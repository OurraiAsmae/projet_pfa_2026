"""
Drift Monitor — Phase 6
Evidently AI + RecordDrift() sur blockchain
"""
import os
import sys
import json
import time
import hashlib
import logging
import schedule
import pickle
import httpx
import redis
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, DataQualityPreset
from evidently.metrics import (
    DatasetDriftMetric,
    ColumnDriftMetric
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [DRIFT] %(message)s"
)
log = logging.getLogger(__name__)

# Config
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://gateway:9999")
REDIS_HOST  = os.getenv("REDIS_HOST", "redis")
API_URL     = os.getenv("API_URL", "http://api:8000")
DATASET_PATH = "/app/mlops/datasets/transactions_bancaires.csv"
MODEL_PATH   = "/app/mlops/models/random_forest.pkl"
SCALER_PATH  = "/app/mlops/models/scaler.pkl"
REPORTS_DIR  = "/app/mlops/reports/drift"

# 17 features exactes du modèle
FEATURE_NAMES = [
    "heure", "jour_semaine", "est_weekend", "montant_mad",
    "est_etranger", "delta_km", "delta_min_last_tx", "nb_tx_1h",
    "est_nouveau_device", "age_client", "age_compte_jours",
    "ratio_montant_moy", "risque_horaire",
    "type_transaction", "device_type",
    "segment_revenu", "type_carte"
]

# Seuils de drift (configurables)
DRIFT_THRESHOLD        = float(os.getenv("DRIFT_THRESHOLD", "0.15"))
CRITICAL_THRESHOLD     = float(os.getenv("CRITICAL_THRESHOLD", "0.30"))
FEATURES_DRIFT_MAX     = int(os.getenv("FEATURES_DRIFT_MAX", "3"))
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL", "60"))

os.makedirs(REPORTS_DIR, exist_ok=True)


class DriftMonitor:
    def __init__(self):
        self.redis_client = None
        self.model = None
        self.scaler = None
        self.reference_data = None
        self._init()

    def _init(self):
        # Redis
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST, port=6379,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            log.info("✅ Redis connecté")
        except Exception as e:
            log.warning(f"⚠️ Redis: {e}")

        # Modèle RF
        try:
            with open(MODEL_PATH, "rb") as f:
                self.model = pickle.load(f)
            with open(SCALER_PATH, "rb") as f:
                self.scaler = pickle.load(f)
            log.info(f"✅ Modèle RF chargé — {self.model.n_features_in_} features")
        except Exception as e:
            log.warning(f"⚠️ Modèle: {e}")

        # Dataset de référence
        try:
            df = pd.read_csv(DATASET_PATH)
            # Encoder colonnes catégorielles
            from sklearn.preprocessing import LabelEncoder
            le = LabelEncoder()
            cat_cols = ["type_transaction", "device_type", "segment_revenu", "type_carte"]
            for col in cat_cols:
                if col in df.columns:
                    df[col] = le.fit_transform(df[col].astype(str))

            # Garder seulement les features du modèle
            available = [f for f in FEATURE_NAMES if f in df.columns]
            self.reference_data = df[available + ["fraude"]].copy()
            log.info(f"✅ Dataset référence chargé — {len(self.reference_data)} lignes")
        except Exception as e:
            log.warning(f"⚠️ Dataset: {e}")

    def get_current_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """
        Simule les données de production récentes.
        En production réelle → lire depuis Kafka/base de données.
        """
        if self.reference_data is None:
            return pd.DataFrame()

        # Simuler du drift progressif
        current = self.reference_data.sample(
            n=min(n_samples, len(self.reference_data)),
            random_state=int(datetime.now().timestamp()) % 1000
        ).copy()

        # Simuler drift sur certaines features
        drift_hour = datetime.now().hour
        if drift_hour >= 22 or drift_hour <= 6:
            # Nuit → plus de transactions suspectes
            current["montant_mad"] *= np.random.uniform(1.3, 1.8,
                len(current))
            current["est_etranger"] = np.random.choice([0, 1],
                len(current), p=[0.3, 0.7])
            current["nb_tx_1h"] *= np.random.uniform(1.5, 2.5,
                len(current))
            log.info("🌙 Simulation drift nocturne activée")

        return current

    def compute_drift_report(self, current_data: pd.DataFrame) -> dict:
        """Calcule le rapport de drift avec Evidently"""
        if self.reference_data is None or current_data.empty:
            return {"error": "Données non disponibles"}

        features = [f for f in FEATURE_NAMES
                    if f in self.reference_data.columns
                    and f in current_data.columns]

        ref = self.reference_data[features].copy()
        cur = current_data[features].copy()

        # Rapport Evidently
        report = Report(metrics=[
            DatasetDriftMetric(),
                ] + [ColumnDriftMetric(column_name=f) for f in features[:5]])

        report.run(reference_data=ref, current_data=cur)
        report_dict = report.as_dict()

        # Extraire les métriques clés
        dataset_drift = report_dict["metrics"][0]["result"]
        drift_detected = dataset_drift.get("dataset_drift", False)
        drift_share    = dataset_drift.get("share_of_drifted_columns", 0)
        n_drifted      = dataset_drift.get("number_of_drifted_columns", 0)

        # Features avec drift
        drifted_features = []
        for metric in report_dict["metrics"][2:]:
            col = metric.get("result", {}).get("column_name", "")
            drift_score = metric.get("result", {}).get("drift_score", 0)
            detected = metric.get("result", {}).get("drift_detected", False)
            if detected:
                drifted_features.append({
                    "feature": col,
                    "drift_score": round(drift_score, 4),
                    "severity": "CRITICAL" if drift_score > CRITICAL_THRESHOLD
                                else "WARNING"
                })

        # Calculer performance si modèle disponible
        model_auc = None
        if self.model and self.scaler and "fraude" in current_data.columns:
            try:
                from sklearn.metrics import roc_auc_score
                X = current_data[features].values
                y = current_data["fraude"].values
                X_scaled = self.scaler.transform(X)
                y_proba = self.model.predict_proba(X_scaled)[:, 1]
                model_auc = round(float(roc_auc_score(y, y_proba)), 4)
            except Exception as e:
                log.warning(f"⚠️ AUC calc: {e}")

        # Sauvegarder le rapport HTML
        report_path = os.path.join(
            REPORTS_DIR,
            f"drift_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.html"
        )
        report.save_html(report_path)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "drift_detected": drift_detected,
            "drift_share": round(drift_share, 4),
            "n_drifted_features": n_drifted,
            "drifted_features": drifted_features,
            "model_auc_current": model_auc,
            "model_auc_reference": 0.9503,
            "auc_degradation": round(0.9503 - model_auc, 4) if model_auc else None,
            "report_path": report_path,
            "n_reference": len(ref),
            "n_current": len(cur)
        }

    def record_drift_on_blockchain(self, drift_report: dict) -> bool:
        """Enregistre le drift sur blockchain via Gateway"""
        severity = "NORMAL"
        if drift_report.get("drift_share", 0) > CRITICAL_THRESHOLD:
            severity = "CRITICAL"
        elif drift_report.get("drift_detected"):
            severity = "WARNING"

        auc_deg = drift_report.get("auc_degradation")

        payload = {
            "model_id": "RandomForest-FraudDetection-v1.0",
            "drift_score": str(round(drift_report.get("drift_share", 0), 4)),
            "affected_features": json.dumps(
                [f["feature"] for f in drift_report.get("drifted_features", [])]
            ),
            "severity": severity,
            "auc_degradation": str(round(auc_deg, 4)) if auc_deg else "0.0",
            "recommendation": self._get_recommendation(severity, auc_deg)
        }

        try:
            resp = httpx.post(
                f"{GATEWAY_URL}/record-drift",
                json=payload,
                timeout=15.0
            )
            result = resp.json()
            log.info(f"✅ Drift enregistré sur blockchain: {result}")
            return result.get("success", False)
        except Exception as e:
            log.error(f"⚠️ Gateway drift: {e}")
            return False

    def _get_recommendation(self, severity: str, auc_deg: float) -> str:
        if severity == "CRITICAL":
            return "RETRAIN_URGENT"
        elif severity == "WARNING" and auc_deg and auc_deg > 0.05:
            return "RETRAIN_SCHEDULED"
        elif severity == "WARNING":
            return "MONITOR_CLOSELY"
        return "NO_ACTION"

    def store_drift_redis(self, drift_report: dict):
        """Stocke le rapport drift dans Redis pour le dashboard"""
        if not self.redis_client:
            return
        try:
            key = f"drift:{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            self.redis_client.setex(key, 86400 * 7, json.dumps(drift_report))
            self.redis_client.lpush("drift:history", json.dumps({
                "timestamp": drift_report["timestamp"],
                "drift_detected": drift_report["drift_detected"],
                "drift_share": drift_report["drift_share"],
                "severity": "CRITICAL" if drift_report.get("drift_share", 0) > CRITICAL_THRESHOLD
                            else ("WARNING" if drift_report["drift_detected"] else "NORMAL"),
                "model_auc": drift_report.get("model_auc_current")
            }))
            self.redis_client.ltrim("drift:history", 0, 99)
            self.redis_client.set("drift:latest", json.dumps(drift_report))
            log.info("✅ Drift stocké dans Redis")
        except Exception as e:
            log.error(f"⚠️ Redis drift: {e}")

    def send_alert_rabbitmq(self, drift_report: dict):
        """Envoie une alerte si drift critique"""
        if drift_report.get("drift_share", 0) > DRIFT_THRESHOLD:
            try:
                alert = {
                    "type": "DRIFT_ALERT",
                    "severity": "CRITICAL" if drift_report.get("drift_share", 0) > CRITICAL_THRESHOLD
                                else "WARNING",
                    "message": f"Drift détecté: {drift_report['n_drifted_features']} features affectées",
                    "drift_share": drift_report["drift_share"],
                    "timestamp": drift_report["timestamp"],
                    "model_id": "RandomForest-FraudDetection-v1.0"
                }
                if self.redis_client:
                    self.redis_client.lpush("alerts:drift", json.dumps(alert))
                    self.redis_client.ltrim("alerts:drift", 0, 49)
                log.warning(f"🚨 ALERTE DRIFT: {alert['severity']} — {alert['message']}")
            except Exception as e:
                log.error(f"⚠️ Alert: {e}")

    def run_check(self):
        """Exécute un cycle complet de vérification drift"""
        log.info("=" * 50)
        log.info("🔍 Vérification drift démarrée...")

        # 1. Obtenir données courantes
        current_data = self.get_current_data(n_samples=2000)
        if current_data.empty:
            log.warning("⚠️ Pas de données courantes")
            return

        # 2. Calculer drift avec Evidently
        drift_report = self.compute_drift_report(current_data)
        if "error" in drift_report:
            log.error(f"❌ Erreur drift: {drift_report['error']}")
            return

        # 3. Logger les résultats
        log.info(f"📊 Drift détecté: {drift_report['drift_detected']}")
        log.info(f"📊 Share drifted: {drift_report['drift_share']:.2%}")
        log.info(f"📊 Features driftées: {drift_report['n_drifted_features']}")
        if drift_report.get("model_auc_current"):
            log.info(f"📊 AUC courant: {drift_report['model_auc_current']}")
            log.info(f"📊 Dégradation AUC: {drift_report.get('auc_degradation', 0):.4f}")

        # 4. Stocker dans Redis
        self.store_drift_redis(drift_report)

        # 5. Si drift → blockchain + alerte
        if drift_report["drift_detected"] or \
           drift_report["drift_share"] > DRIFT_THRESHOLD:
            log.warning("🚨 DRIFT DÉTECTÉ — Enregistrement blockchain...")
            self.record_drift_on_blockchain(drift_report)
            self.send_alert_rabbitmq(drift_report)
        else:
            log.info("✅ Pas de drift significatif")

        log.info("=" * 50)
        return drift_report


def main():
    log.info("🚀 Drift Monitor démarré")
    log.info(f"   Gateway: {GATEWAY_URL}")
    log.info(f"   Seuil drift: {DRIFT_THRESHOLD}")
    log.info(f"   Intervalle: {CHECK_INTERVAL_MINUTES} minutes")

    monitor = DriftMonitor()

    # Premier check immédiat
    monitor.run_check()

    # Scheduler
    schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(monitor.run_check)

    log.info(f"⏰ Prochain check dans {CHECK_INTERVAL_MINUTES} minutes")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
