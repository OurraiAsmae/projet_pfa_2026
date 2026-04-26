"""
SHAP Service v3 — IPFS Pinata réel
"""
import os, json, hashlib, pickle
import numpy as np
from datetime import datetime

MODELS_DIR = "/app/mlops/models"
SHAP_DIR   = "/app/mlops/shap"
os.makedirs(SHAP_DIR, exist_ok=True)

FEATURE_NAMES = [
    "heure","jour_semaine","est_weekend","montant_mad",
    "type_transaction","pays_transaction","est_etranger",
    "tx_lat","tx_lon","delta_km","delta_min_last_tx",
    "nb_tx_1h","device_type","est_nouveau_device",
    "age_client","segment_revenu","type_carte"
]

TREE_MODELS = [
    "RandomForestClassifier","GradientBoostingClassifier",
    "XGBClassifier","LGBMClassifier",
    "DecisionTreeClassifier","ExtraTreesClassifier"
]

class SHAPService:
    def __init__(self):
        self.scaler    = None
        self.explainer = None
        self.rf_model  = None
        self._load()

    def _load(self):
        try:
            import shap
            with open(f"{MODELS_DIR}/scaler.pkl","rb") as f:
                self.scaler = pickle.load(f)
            with open(f"{MODELS_DIR}/random_forest.pkl","rb") as f:
                self.rf_model = pickle.load(f)
            self.explainer = shap.TreeExplainer(self.rf_model)
            print(f"✅ SHAP Service prêt — {len(FEATURE_NAMES)} features")
        except Exception as e:
            print(f"⚠️ SHAP: {e}")

    def compute_shap(self, features: dict, tx_id: str,
                     active_model=None) -> dict:
        """Compute SHAP + pin to IPFS"""
        # Si modèle actif est TreeModel → utiliser son explainer
        if active_model is not None:
            mtype = type(active_model).__name__
            if mtype in TREE_MODELS and mtype != "RandomForestClassifier":
                try:
                    import shap
                    self.explainer = shap.TreeExplainer(active_model)
                except:
                    pass

        if not self.explainer or not self.scaler:
            return self._fallback(tx_id)

        try:
            X = np.array([[
                float(features.get(f, 0))
                for f in FEATURE_NAMES
            ]])
            X_scaled = self.scaler.transform(X)
            sv = self.explainer.shap_values(X_scaled)
            vals = sv[1][0] if isinstance(sv, list) else sv[0]

            ev = self.explainer.expected_value
            base = float(ev[1] if isinstance(ev, np.ndarray) else ev)

            top = sorted([{
                "feature":       fn,
                "shap_value":    round(float(v), 4),
                "abs_value":     round(abs(float(v)), 4),
                "feature_value": round(float(X[0][i]), 4)
            } for i,(fn,v) in enumerate(zip(FEATURE_NAMES,vals))],
            key=lambda x: x["abs_value"], reverse=True)

            result = {
                "tx_id":        tx_id,
                "timestamp":    datetime.utcnow().isoformat(),
                "model_type":   "RandomForestClassifier",
                "base_value":   base,
                "n_features":   len(FEATURE_NAMES),
                "shap_values":  [round(float(v),4) for v in vals],
                "top_features": top[:5],
                "all_features": top
            }

            # Save locally
            local = f"{SHAP_DIR}/shap_{tx_id}.json"
            with open(local,"w") as f:
                json.dump(result, f, indent=2)

            # Pin to IPFS
            cid = self._pin(result, tx_id)
            pinned = not cid.startswith("QmSIM")

            result.update({
                "cid":      cid,
                "ipfs_url": f"https://gateway.pinata.cloud/ipfs/{cid}"
                            if pinned else "",
                "storage":  {
                    "local":  local,
                    "ipfs":   cid,
                    "pinned": pinned
                }
            })
            return result

        except Exception as e:
            print(f"⚠️ SHAP: {e}")
            return self._fallback(tx_id)

    def _pin(self, data: dict, tx_id: str) -> str:
        try:
            from ipfs_client import IPFSClient
            cid = IPFSClient().pin_shap_summary(tx_id, data)
            if cid:
                return cid
        except Exception as e:
            print(f"⚠️ IPFS: {e}")
        return self._sim(data)

    def get_shap_from_cid(self, cid: str, tx_id: str) -> dict:
        local = f"{SHAP_DIR}/shap_{tx_id}.json"
        if os.path.exists(local):
            with open(local) as f:
                d = json.load(f)
            d["source"] = "local_cache"
            return d
        if cid and not cid.startswith("QmSIM"):
            try:
                from ipfs_client import IPFSClient
                c = IPFSClient().get_from_ipfs(cid)
                if c:
                    c["source"] = "ipfs"
                    return c
            except:
                pass
        return {"error": f"SHAP not found for {tx_id}"}

    def _sim(self, data: dict) -> str:
        h = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
        return f"QmSIM{h[:38]}"

    def _fallback(self, tx_id: str) -> dict:
        return {
            "tx_id": tx_id,
            "cid":   self._sim({"tx_id": tx_id}),
            "error": "SHAP not available"
        }
