import os, json, hashlib, pickle
import numpy as np
import warnings
warnings.filterwarnings("ignore")

SHAP_DIR = "/app/mlops/shap"
MODEL_PATH = "/app/mlops/models/random_forest.pkl"
SCALER_PATH = "/app/mlops/models/scaler.pkl"

FEATURE_NAMES = [
    "heure", "jour_semaine", "est_weekend", "montant_mad",
    "type_transaction", "pays_transaction", "est_etranger",
    "tx_lat", "tx_lon", "delta_km", "delta_min_last_tx",
    "nb_tx_1h", "device_type", "est_nouveau_device",
    "age_client", "segment_revenu", "type_carte"
]

class SHAPService:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.explainer = None
        self.feature_names = FEATURE_NAMES
        self._load()

    def _load(self):
        import shap
        try:
            with open(MODEL_PATH, "rb") as f:
                self.model = pickle.load(f)
            with open(SCALER_PATH, "rb") as f:
                self.scaler = pickle.load(f)
            self.explainer = shap.TreeExplainer(self.model)
            print(f"SHAP Service — {self.model.n_features_in_} features")
        except Exception as e:
            print(f"SHAP Service error: {e}")

    def compute_shap(self, features_dict: dict, tx_id: str) -> dict:
        if not self.model or not self.explainer:
            cid = "QmSHAP" + hashlib.sha256(tx_id.encode()).hexdigest()[:38]
            return {"cid": cid, "top_features": [], "error": "Model not loaded"}
        try:
            X = np.zeros((1, len(self.feature_names)))
            for i, name in enumerate(self.feature_names):
                X[0, i] = float(features_dict.get(name, 0))
            X_scaled = self.scaler.transform(X)
            shap_values = self.explainer.shap_values(X_scaled)
            if isinstance(shap_values, list):
                sv = shap_values[1][0]
                base_value = float(self.explainer.expected_value[1])
            else:
                sv = shap_values[0]
                base_value = float(self.explainer.expected_value)
            feature_importance = [
                {
                    "feature": name,
                    "shap_value": float(sv[i]),
                    "abs_importance": float(abs(sv[i])),
                    "feature_value": float(X[0, i])
                }
                for i, name in enumerate(self.feature_names)
            ]
            top_features = sorted(
                feature_importance,
                key=lambda x: x["abs_importance"],
                reverse=True
            )[:5]
            shap_data = {
                "tx_id": tx_id,
                "feature_names": self.feature_names,
                "shap_values": sv.tolist(),
                "base_value": base_value,
                "top_features": top_features,
                "model_type": "RandomForestClassifier",
                "n_features": len(self.feature_names)
            }
            shap_json = json.dumps(shap_data, sort_keys=True)
            cid = "QmSHAP" + hashlib.sha256(shap_json.encode()).hexdigest()[:38]
            os.makedirs(SHAP_DIR, exist_ok=True)
            with open(os.path.join(SHAP_DIR, f"shap_{tx_id}.json"), "w") as f:
                json.dump(shap_data, f, indent=2)
            return {"cid": cid, "top_features": top_features, "base_value": base_value}
        except Exception as e:
            print(f"SHAP compute error: {e}")
            cid = "QmSHAP" + hashlib.sha256(tx_id.encode()).hexdigest()[:38]
            return {"cid": cid, "top_features": [], "error": str(e)}

    def get_shap_from_cid(self, cid: str, tx_id: str) -> dict:
        path = os.path.join(SHAP_DIR, f"shap_{tx_id}.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return {"error": f"SHAP not found for {tx_id}"}
