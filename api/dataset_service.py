"""
BlockML-Gov Dataset Service v1.0
Complete Data Governance:
Step 1 → Hash + Versioning
Step 2 → Dataset Card → IPFS
Step 3 → Feature Analysis + Quality Score
Step 4 → Local Storage
Step 5 → Blockchain + Lineage
"""
import os, json, hashlib, pickle
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional

DATASETS_DIR = "/app/mlops/datasets"
MODELS_DIR   = "/app/mlops/models"
os.makedirs(DATASETS_DIR, exist_ok=True)

REQUIRED_FEATURES = [
    "heure","jour_semaine","est_weekend","montant_mad",
    "type_transaction","pays_transaction","est_etranger",
    "tx_lat","tx_lon","delta_km","delta_min_last_tx",
    "nb_tx_1h","device_type","est_nouveau_device",
    "age_client","segment_revenu","type_carte"
]
TARGET_VARIABLE = "fraude"

class DatasetService:

    # ════════════════════════════════════════════════
    # STEP 1 — Hash + Versioning
    # ════════════════════════════════════════════════
    def compute_hash(self, content: bytes) -> str:
        """Compute SHA256 hash of dataset"""
        return "sha256:" + hashlib.sha256(content).hexdigest()

    def get_next_version(self, dataset_name: str) -> str:
        """Get next version number for dataset"""
        existing = []
        for f in os.listdir(DATASETS_DIR):
            if f.startswith(dataset_name) and f.endswith("_meta.json"):
                try:
                    meta = json.load(open(f"{DATASETS_DIR}/{f}"))
                    v = int(meta.get("version","v0").replace("v",""))
                    existing.append(v)
                except:
                    pass
        next_v = max(existing) + 1 if existing else 1
        return f"v{next_v}"

    def check_duplicate(self, hash_val: str) -> Optional[dict]:
        """Check if dataset already exists by hash"""
        for f in os.listdir(DATASETS_DIR):
            if f.endswith("_meta.json"):
                try:
                    meta = json.load(open(f"{DATASETS_DIR}/{f}"))
                    if meta.get("hash") == hash_val:
                        return meta
                except:
                    pass
        return None

    # ════════════════════════════════════════════════
    # STEP 2 — Dataset Card → IPFS
    # ════════════════════════════════════════════════
    def create_dataset_card(self,
                            dataset_name: str,
                            version: str,
                            hash_val: str,
                            df: pd.DataFrame,
                            uploaded_by: str) -> dict:
        """Create Dataset Card for IPFS"""

        # Detect features and target
        cols = list(df.columns)
        has_target = TARGET_VARIABLE in cols
        input_features = [c for c in cols
                         if c != TARGET_VARIABLE
                         and c not in ["tx_id","client_id","card_id","timestamp"]]

        # Basic stats
        n_rows = len(df)
        fraud_rate = 0.0
        n_fraud = 0
        n_legit = n_rows
        if has_target:
            n_fraud = int(df[TARGET_VARIABLE].sum())
            n_legit = n_rows - n_fraud
            fraud_rate = round(n_fraud / n_rows, 4)

        dataset_id = f"DS-{dataset_name}-{version}"

        card = {
            "schema": "BlockML-Gov-Dataset-Card-v1",
            "identity": {
                "dataset_id":  dataset_id,
                "name":        dataset_name,
                "version":     version,
                "hash_sha256": hash_val,
            },
            "features": {
                "input_features":  input_features,
                "target_variable": TARGET_VARIABLE
                                   if has_target else "unknown",
                "n_features":      len(input_features),
                "n_total_columns": len(cols),
                "required_features_present": [
                    f for f in REQUIRED_FEATURES
                    if f in input_features
                ],
                "required_features_missing": [
                    f for f in REQUIRED_FEATURES
                    if f not in input_features
                ]
            },
            "statistics": {
                "n_rows":      n_rows,
                "n_fraud":     n_fraud,
                "n_legitimate":n_legit,
                "fraud_rate":  fraud_rate,
                "n_columns":   len(cols)
            },
            "provenance": {
                "uploaded_by":    uploaded_by,
                "uploaded_at":    datetime.utcnow().isoformat(),
                "source":         "Banking Core System",
                "regulatory_basis":"EU AI Act Art.10"
            }
        }
        return card

    def pin_dataset_card(self, card: dict,
                         dataset_id: str) -> str:
        """Pin Dataset Card to IPFS Pinata"""
        try:
            from ipfs_client import IPFSClient
            client = IPFSClient()
            cid = client.pin_json(
                card, f"dataset-card-{dataset_id}")
            if cid:
                print(f"✅ Dataset Card pinned: {cid}")
                return cid
        except Exception as e:
            print(f"⚠️ IPFS dataset card: {e}")
        return self._simulate_cid(card)

    # ════════════════════════════════════════════════
    # STEP 3 — Feature Analysis + Quality Score
    # ════════════════════════════════════════════════
    def analyze_features(self, df: pd.DataFrame,
                         dataset_id: str) -> dict:
        """Complete feature analysis"""
        cols = list(df.columns)
        has_target = TARGET_VARIABLE in cols
        feature_cols = [c for c in cols
                       if c != TARGET_VARIABLE
                       and df[c].dtype in [np.float64,
                           np.float32, np.int64, np.int32]]

        analysis = {
            "dataset_id":        dataset_id,
            "timestamp":         datetime.utcnow().isoformat(),
            "feature_importance":[],
            "correlations":      [],
            "statistics":        [],
            "quality":           {},
            "comparison":        None
        }

        # 3a. Statistics per feature
        for col in feature_cols[:17]:
            try:
                stats = {
                    "feature": col,
                    "mean":    round(float(df[col].mean()), 4),
                    "std":     round(float(df[col].std()),  4),
                    "min":     round(float(df[col].min()),  4),
                    "max":     round(float(df[col].max()),  4),
                    "missing": round(float(
                        df[col].isnull().sum() / len(df)), 4),
                    "zeros":   round(float(
                        (df[col]==0).sum() / len(df)), 4)
                }
                analysis["statistics"].append(stats)
            except:
                pass

        # 3b. Correlation with target
        if has_target:
            for col in feature_cols[:17]:
                try:
                    corr = float(df[col].corr(df[TARGET_VARIABLE]))
                    if not np.isnan(corr):
                        analysis["correlations"].append({
                            "feature":     col,
                            "correlation": round(corr, 4),
                            "abs_corr":    round(abs(corr), 4),
                            "direction":   "→ FRAUD" if corr > 0
                                          else "→ LEGITIMATE"
                        })
                except:
                    pass
            analysis["correlations"].sort(
                key=lambda x: x["abs_corr"], reverse=True)

        # 3c. Feature Importance (quick RF)
        if has_target and len(feature_cols) >= 3:
            try:
                from sklearn.ensemble import RandomForestClassifier
                from sklearn.preprocessing import StandardScaler

                X = df[feature_cols].fillna(0).values
                y = df[TARGET_VARIABLE].values

                # Quick RF (small for speed)
                rf = RandomForestClassifier(
                    n_estimators=50,
                    max_depth=5,
                    random_state=42,
                    n_jobs=-1)
                rf.fit(X, y)

                importances = rf.feature_importances_
                for i, col in enumerate(feature_cols):
                    analysis["feature_importance"].append({
                        "feature":    col,
                        "importance": round(float(importances[i]),4),
                        "rank":       0
                    })
                analysis["feature_importance"].sort(
                    key=lambda x: x["importance"], reverse=True)
                for i, f in enumerate(
                        analysis["feature_importance"]):
                    f["rank"] = i + 1

                print(f"✅ Feature importance computed "
                      f"({len(feature_cols)} features)")
            except Exception as e:
                print(f"⚠️ Feature importance: {e}")

        # 3d. Quality Score
        analysis["quality"] = self._compute_quality(df, feature_cols)

        return analysis

    def _compute_quality(self, df: pd.DataFrame,
                         feature_cols: list) -> dict:
        """Compute data quality score 0-100"""
        scores = {}
        total  = 0

        # 1. Sufficient rows (20 pts)
        n = len(df)
        if n >= 10000:   s = 20
        elif n >= 5000:  s = 15
        elif n >= 1000:  s = 10
        else:            s = 0
        scores["sufficient_rows"] = {
            "score": s, "max": 20,
            "value": n,
            "status": "✅" if s==20 else "⚠️" if s>0 else "❌"
        }
        total += s

        # 2. Fraud rate acceptable (20 pts)
        has_target = TARGET_VARIABLE in df.columns
        if has_target:
            fr = df[TARGET_VARIABLE].mean()
            if 0.01 <= fr <= 0.10: s = 20
            elif 0.001 <= fr <= 0.20: s = 10
            else: s = 0
            scores["fraud_rate"] = {
                "score": s, "max": 20,
                "value": round(float(fr), 4),
                "status": "✅" if s==20 else "⚠️" if s>0 else "❌"
            }
            total += s
        else:
            scores["fraud_rate"] = {
                "score": 0, "max": 20,
                "value": "N/A",
                "status": "⚠️ No target"
            }

        # 3. Required features present (20 pts)
        present = [f for f in REQUIRED_FEATURES
                  if f in df.columns]
        ratio = len(present) / len(REQUIRED_FEATURES)
        s = int(20 * ratio)
        scores["required_features"] = {
            "score": s, "max": 20,
            "value": f"{len(present)}/{len(REQUIRED_FEATURES)}",
            "status": "✅" if s==20 else "⚠️" if s>=10 else "❌"
        }
        total += s

        # 4. Missing values < 5% (15 pts)
        if feature_cols:
            miss = df[feature_cols].isnull().mean().mean()
            if miss < 0.01:   s = 15
            elif miss < 0.05: s = 10
            elif miss < 0.10: s = 5
            else:             s = 0
            scores["missing_values"] = {
                "score": s, "max": 15,
                "value": f"{miss:.2%}",
                "status": "✅" if s==15 else "⚠️" if s>0 else "❌"
            }
            total += s

        # 5. No duplicates (10 pts)
        dups = df.duplicated().sum()
        dup_ratio = dups / len(df)
        if dup_ratio < 0.001:  s = 10
        elif dup_ratio < 0.01: s = 5
        else:                  s = 0
        scores["no_duplicates"] = {
            "score": s, "max": 10,
            "value": f"{dups} duplicates",
            "status": "✅" if s==10 else "⚠️" if s>0 else "❌"
        }
        total += s

        # 6. Correct types (10 pts)
        numeric_cols = df[feature_cols].select_dtypes(
            include=[np.number]).columns
        ratio = len(numeric_cols) / max(len(feature_cols), 1)
        s = int(10 * ratio)
        scores["correct_types"] = {
            "score": s, "max": 10,
            "value": f"{len(numeric_cols)}/{len(feature_cols)} numeric",
            "status": "✅" if s==10 else "⚠️" if s>=5 else "❌"
        }
        total += s

        # 7. Outliers < 1% (5 pts)
        outlier_count = 0
        for col in feature_cols[:10]:
            try:
                q1 = df[col].quantile(0.01)
                q3 = df[col].quantile(0.99)
                outlier_count += ((df[col] < q1) |
                                  (df[col] > q3)).sum()
            except:
                pass
        outlier_ratio = outlier_count / max(len(df) * 10, 1)
        s = 5 if outlier_ratio < 0.02 else 0
        scores["outliers"] = {
            "score": s, "max": 5,
            "value": f"{outlier_count} outliers",
            "status": "✅" if s==5 else "⚠️"
        }
        total += s

        # Global rating
        if total >= 90:   rating = "Excellent ✅"
        elif total >= 70: rating = "Good ✅"
        elif total >= 50: rating = "Acceptable ⚠️"
        else:             rating = "Poor ❌"

        return {
            "total_score":  total,
            "max_score":    100,
            "rating":       rating,
            "breakdown":    scores
        }

    def pin_analysis(self, analysis: dict,
                     dataset_id: str) -> str:
        """Pin feature analysis to IPFS"""
        try:
            from ipfs_client import IPFSClient
            client = IPFSClient()
            # Pin only summary (not full data)
            summary = {
                "dataset_id":   dataset_id,
                "timestamp":    analysis["timestamp"],
                "quality_score":analysis["quality"]["total_score"],
                "quality_rating":analysis["quality"]["rating"],
                "top_features": analysis["feature_importance"][:5],
                "top_correlations": analysis["correlations"][:5],
                "n_features_analyzed": len(
                    analysis["feature_importance"])
            }
            cid = client.pin_json(
                summary, f"dataset-analysis-{dataset_id}")
            if cid:
                print(f"✅ Analysis pinned: {cid}")
                return cid
        except Exception as e:
            print(f"⚠️ IPFS analysis: {e}")
        return self._simulate_cid(analysis)

    # ════════════════════════════════════════════════
    # STEP 4 — Local Storage
    # ════════════════════════════════════════════════
    def save_locally(self, content: bytes,
                     df: pd.DataFrame,
                     dataset_name: str,
                     version: str,
                     hash_val: str,
                     card: dict,
                     analysis: dict,
                     card_cid: str,
                     analysis_cid: str) -> dict:
        """Save all dataset artifacts locally"""
        safe_name = dataset_name.replace(" ","_").replace(".csv","")
        h_short   = hash_val.replace("sha256:","")[:8]
        base      = f"{DATASETS_DIR}/{safe_name}_{version}_{h_short}"

        # Save CSV
        csv_path = f"{base}.csv"
        with open(csv_path, "wb") as f:
            f.write(content)

        # Save metadata
        meta = {
            "dataset_id":   card["identity"]["dataset_id"],
            "name":         dataset_name,
            "version":      version,
            "hash":         hash_val,
            "card_cid":     card_cid,
            "analysis_cid": analysis_cid,
            "csv_path":     csv_path,
            "n_rows":       card["statistics"]["n_rows"],
            "n_cols":       card["statistics"]["n_columns"],
            "fraud_rate":   card["statistics"]["fraud_rate"],
            "quality_score":analysis["quality"]["total_score"],
            "quality_rating":analysis["quality"]["rating"],
            "uploaded_by":  card["provenance"]["uploaded_by"],
            "uploaded_at":  card["provenance"]["uploaded_at"],
            "features":     card["features"]["input_features"],
            "blockchain_registered": False
        }
        meta_path = f"{base}_meta.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        # Save full analysis
        analysis_path = f"{base}_analysis.json"
        with open(analysis_path, "w") as f:
            json.dump(analysis, f, indent=2)

        print(f"✅ Saved locally: {csv_path}")
        return {
            "csv_path":      csv_path,
            "meta_path":     meta_path,
            "analysis_path": analysis_path,
            "base_name":     base
        }

    def get_all_datasets(self) -> list:
        """List all datasets with metadata"""
        datasets = []
        for f in os.listdir(DATASETS_DIR):
            if f.endswith("_meta.json"):
                try:
                    meta = json.load(
                        open(f"{DATASETS_DIR}/{f}"))
                    # Add file size
                    csv_p = meta.get("csv_path","")
                    if os.path.exists(csv_p):
                        meta["size_mb"] = round(
                            os.path.getsize(csv_p)/1024/1024, 2)
                    else:
                        meta["size_mb"] = 0
                    datasets.append(meta)
                except:
                    pass
        datasets.sort(key=lambda x: x.get("uploaded_at",""),
                      reverse=True)
        return datasets

    def get_dataset_analysis(self, dataset_id: str) -> dict:
        """Get analysis for a specific dataset"""
        for f in os.listdir(DATASETS_DIR):
            if f.endswith("_analysis.json"):
                try:
                    data = json.load(
                        open(f"{DATASETS_DIR}/{f}"))
                    if data.get("dataset_id") == dataset_id:
                        return data
                except:
                    pass
        return {}

    # ════════════════════════════════════════════════
    # STEP 5 — Blockchain + Lineage
    # ════════════════════════════════════════════════
    def register_on_blockchain(self,
                               dataset_id: str,
                               hash_val: str,
                               card_cid: str,
                               version: str,
                               n_rows: int,
                               fraud_rate: float,
                               quality_score: int,
                               uploaded_by: str) -> bool:
        """Register dataset on Hyperledger Fabric"""
        try:
            import httpx
            gw_url = os.getenv("GATEWAY_URL",
                               "http://gateway:9999")
            r = httpx.post(
                f"{gw_url}/submit-dataset",
                json={
                    "dataset_id":    dataset_id,
                    "hash":          hash_val,
                    "cid":           card_cid,
                    "version":       version,
                    "n_rows":        str(n_rows),
                    "fraud_rate":    str(round(fraud_rate,4)),
                    "quality_score": str(quality_score),
                    "uploaded_by":   uploaded_by
                },
                timeout=15)
            result = r.json()
            if result.get("success"):
                print(f"✅ Dataset registered on blockchain: "
                      f"{dataset_id}")
                return True
            else:
                print(f"⚠️ Blockchain: {result.get('message')}")
                return False
        except Exception as e:
            print(f"⚠️ Blockchain register: {e}")
            return False

    def link_model_to_dataset(self,
                              model_id: str,
                              dataset_id: str,
                              dataset_hash: str) -> bool:
        """Link a model to its training dataset"""
        try:
            # Update local metadata
            for f in os.listdir(DATASETS_DIR):
                if f.endswith("_meta.json"):
                    path = f"{DATASETS_DIR}/{f}"
                    meta = json.load(open(path))
                    if meta.get("dataset_id") == dataset_id:
                        models = meta.get("models_trained",[])
                        if model_id not in models:
                            models.append(model_id)
                        meta["models_trained"] = models
                        json.dump(meta, open(path,"w"), indent=2)
                        print(f"✅ Lineage: {model_id} → "
                              f"{dataset_id}")
                        return True
        except Exception as e:
            print(f"⚠️ Lineage: {e}")
        return False

    def get_lineage(self, dataset_id: str) -> dict:
        """Get complete lineage for a dataset"""
        for f in os.listdir(DATASETS_DIR):
            if f.endswith("_meta.json"):
                try:
                    meta = json.load(
                        open(f"{DATASETS_DIR}/{f}"))
                    if meta.get("dataset_id") == dataset_id:
                        return {
                            "dataset_id":    dataset_id,
                            "version":       meta.get("version"),
                            "hash":          meta.get("hash"),
                            "card_cid":      meta.get("card_cid"),
                            "models_trained":meta.get(
                                "models_trained",[]),
                            "uploaded_by":   meta.get("uploaded_by"),
                            "uploaded_at":   meta.get("uploaded_at"),
                            "quality_score": meta.get("quality_score")
                        }
                except:
                    pass
        return {"error": f"Dataset {dataset_id} not found"}

    def compare_versions(self,
                         dataset_id_v1: str,
                         dataset_id_v2: str) -> dict:
        """Compare two dataset versions"""
        meta1 = self._get_meta(dataset_id_v1)
        meta2 = self._get_meta(dataset_id_v2)
        if not meta1 or not meta2:
            return {"error": "One or both datasets not found"}

        an1 = self.get_dataset_analysis(dataset_id_v1)
        an2 = self.get_dataset_analysis(dataset_id_v2)

        comparison = {
            "v1": dataset_id_v1,
            "v2": dataset_id_v2,
            "timestamp": datetime.utcnow().isoformat(),
            "differences": {
                "n_rows": {
                    "v1": meta1.get("n_rows",0),
                    "v2": meta2.get("n_rows",0),
                    "change": meta2.get("n_rows",0) -
                              meta1.get("n_rows",0)
                },
                "fraud_rate": {
                    "v1": meta1.get("fraud_rate",0),
                    "v2": meta2.get("fraud_rate",0),
                    "change": round(
                        meta2.get("fraud_rate",0) -
                        meta1.get("fraud_rate",0), 4)
                },
                "quality_score": {
                    "v1": meta1.get("quality_score",0),
                    "v2": meta2.get("quality_score",0),
                    "change": meta2.get("quality_score",0) -
                              meta1.get("quality_score",0)
                }
            },
            "feature_drift": []
        }

        # Compare correlations
        if an1.get("correlations") and an2.get("correlations"):
            corr1 = {c["feature"]: c["correlation"]
                     for c in an1["correlations"]}
            corr2 = {c["feature"]: c["correlation"]
                     for c in an2["correlations"]}
            for feat in set(list(corr1.keys()) +
                            list(corr2.keys())):
                c1 = corr1.get(feat, 0)
                c2 = corr2.get(feat, 0)
                drift = round(abs(c2 - c1), 4)
                if drift > 0.05:
                    comparison["feature_drift"].append({
                        "feature": feat,
                        "corr_v1": c1,
                        "corr_v2": c2,
                        "drift":   drift,
                        "status":  "⚠️ Drifted" if drift > 0.1
                                  else "⚡ Changed"
                    })

        return comparison

    # ── Utils ─────────────────────────────────────────
    def _get_meta(self, dataset_id: str) -> Optional[dict]:
        for f in os.listdir(DATASETS_DIR):
            if f.endswith("_meta.json"):
                try:
                    meta = json.load(
                        open(f"{DATASETS_DIR}/{f}"))
                    if meta.get("dataset_id") == dataset_id:
                        return meta
                except:
                    pass
        return None

    def _simulate_cid(self, data: dict) -> str:
        h = hashlib.sha256(
            json.dumps(data, sort_keys=True,
                       default=str).encode()
        ).hexdigest()
        return f"QmSIM{h[:38]}"

# Singleton
dataset_svc = DatasetService()
