"""
BlockML-Gov IPFS Service — Pinata
Hybrid storage: Local files + IPFS CIDs on blockchain
"""
import os
import json
import hashlib
import requests
from datetime import datetime
from typing import Optional

PINATA_JWT = os.getenv("PINATA_JWT", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiIzYjk5ZTAwNy1kNWQwLTRmMzUtYjcyNS0wZWJkZjVhZDE3NzIiLCJlbWFpbCI6InNlbWFzZW1hYWFuZUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicGluX3BvbGljeSI6eyJyZWdpb25zIjpbeyJkZXNpcmVkUmVwbGljYXRpb25Db3VudCI6MSwiaWQiOiJGUkExIn0seyJkZXNpcmVkUmVwbGljYXRpb25Db3VudCI6MSwiaWQiOiJOWUMxIn1dLCJ2ZXJzaW9uIjoxfSwibWZhX2VuYWJsZWQiOmZhbHNlLCJzdGF0dXMiOiJBQ1RJVkUifSwiYXV0aGVudGljYXRpb25UeXBlIjoic2NvcGVkS2V5Iiwic2NvcGVkS2V5S2V5IjoiYTg1YmQ0ZTU1MmFiYzk4NTI3YTYiLCJzY29wZWRLZXlTZWNyZXQiOiI1YWE3OTgxMjZiNTA1NjdlYWI1NjBiNGY5NzQxZjdkOGE2NWQ0MmYzYWJmNTk0NzFjMDA0MDhjZTg2OGRkZTE4IiwiZXhwIjoxODA4Mzk1NjM2fQ.MZR5KOc93sqgNp8p72WpYhl6iPtTa89M4R-tWri3Tko")

PINATA_BASE  = "https://api.pinata.cloud"
GATEWAY_BASE = "https://gateway.pinata.cloud/ipfs"

HEADERS = {
    "Authorization": f"Bearer {PINATA_JWT}"
}

class IPFSClient:
    """
    Hybrid IPFS client:
    - Files stored locally (models, datasets)
    - Metadata/summaries pinned to IPFS via Pinata
    - CIDs recorded on Hyperledger Fabric blockchain
    """

    def test_connection(self) -> bool:
        try:
            r = requests.get(
                f"{PINATA_BASE}/data/testAuthentication",
                headers=HEADERS, timeout=10)
            return r.status_code == 200
        except:
            return False

    # ── Pin JSON to IPFS ─────────────────────────────
    def pin_json(self, data: dict, name: str) -> Optional[str]:
        """Pin JSON metadata to IPFS → returns CID"""
        try:
            payload = {
                "pinataMetadata": {
                    "name": name,
                    "keyvalues": {
                        "project": "BlockML-Gov",
                        "timestamp": datetime.utcnow().isoformat(),
                        "type": "metadata"
                    }
                },
                "pinataContent": data
            }
            r = requests.post(
                f"{PINATA_BASE}/pinning/pinJSONToIPFS",
                json=payload, headers=HEADERS, timeout=30)
            if r.status_code == 200:
                cid = r.json()["IpfsHash"]
                print(f"✅ IPFS JSON pinned: {cid} ({name})")
                return cid
            else:
                print(f"❌ Pinata JSON error: {r.text}")
                return None
        except Exception as e:
            print(f"❌ IPFS pin_json error: {e}")
            return None

    # ── Pin File to IPFS ─────────────────────────────
    def pin_file(self, file_path: str,
                 name: str, file_type: str = "file") -> Optional[str]:
        """Pin a local file to IPFS → returns CID"""
        try:
            with open(file_path, "rb") as f:
                files = {"file": (name, f)}
                metadata = json.dumps({
                    "name": name,
                    "keyvalues": {
                        "project": "BlockML-Gov",
                        "type": file_type,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
                data = {"pinataMetadata": metadata}
                r = requests.post(
                    f"{PINATA_BASE}/pinning/pinFileToIPFS",
                    files=files, data=data,
                    headers=HEADERS, timeout=60)
            if r.status_code == 200:
                cid = r.json()["IpfsHash"]
                print(f"✅ IPFS file pinned: {cid} ({name})")
                return cid
            else:
                print(f"❌ Pinata file error: {r.text}")
                return None
        except Exception as e:
            print(f"❌ IPFS pin_file error: {e}")
            return None

    # ── Model Card ───────────────────────────────────
    def create_model_card(self,
                          model_id: str,
                          model_type: str,
                          metrics: dict,
                          dataset_info: dict,
                          feature_names: list,
                          submitted_by: str,
                          local_path: str = None) -> dict:
        """
        Create and pin a complete Model Card to IPFS.
        Returns both local hash and IPFS CID.
        """
        model_card = {
            "schema_version": "1.0",
            "model_id": model_id,
            "model_type": model_type,
            "framework": "scikit-learn / xgboost",
            "governance": {
                "framework": "BlockML-Gov",
                "regulatory": [
                    "EU AI Act 2024",
                    "SR 11-7 (Federal Reserve)",
                    "Basel III",
                    "BAM Morocco"
                ],
                "explainability": "SHAP TreeExplainer",
                "blockchain": "Hyperledger Fabric 2.5"
            },
            "performance": {
                "auc_roc":   metrics.get("auc_roc", 0),
                "auc_pr":    metrics.get("auc_pr", 0),
                "f1_score":  metrics.get("f1", 0),
                "precision": metrics.get("precision", 0),
                "recall":    metrics.get("recall", 0),
                "n_train":   metrics.get("n_train", 0),
                "n_test":    metrics.get("n_test", 0)
            },
            "thresholds": {
                "fraud_threshold":      0.85,
                "legitimate_threshold": 0.40,
                "auc_min":    0.95,
                "f1_min":     0.85,
                "recall_min": 0.80
            },
            "data": {
                "dataset_name": dataset_info.get("name", ""),
                "dataset_hash": dataset_info.get("hash", ""),
                "n_features":   len(feature_names),
                "features":     feature_names,
                "fraud_rate":   dataset_info.get("fraud_rate", 0)
            },
            "model_file": {
                "local_path":  local_path or "",
                "hash_sha256": self._hash_file(local_path)
                               if local_path else ""
            },
            "metadata": {
                "submitted_by":  submitted_by,
                "created_at":    datetime.utcnow().isoformat(),
                "project":       "BlockML-Gov",
                "use_case":      "Banking Fraud Detection",
                "language":      "Python 3.11",
                "docker_image":  "asmaeourrai/blockmlgov-api:v1"
            }
        }

        # Pin to IPFS
        cid = self.pin_json(
            model_card,
            f"model-card-{model_id}")

        # Save locally too
        local_save = (f"/app/mlops/model_cards/"
                      f"model_card_{model_id}.json")
        os.makedirs(os.path.dirname(local_save), exist_ok=True)
        with open(local_save, "w") as f:
            json.dump(model_card, f, indent=2)

        return {
            "cid":        cid or self._simulate_cid(model_card),
            "ipfs_url":   f"{GATEWAY_BASE}/{cid}" if cid else "",
            "local_path": local_save,
            "model_card": model_card,
            "pinned":     cid is not None
        }

    # ── SHAP Summary ─────────────────────────────────
    def pin_shap_summary(self,
                         tx_id: str,
                         shap_data: dict) -> str:
        """Pin SHAP explanation to IPFS"""
        summary = {
            "tx_id":        tx_id,
            "timestamp":    datetime.utcnow().isoformat(),
            "model_id":     shap_data.get("model_type","RF"),
            "base_value":   shap_data.get("base_value", 0),
            "top_features": shap_data.get("top_features", []),
            "n_features":   shap_data.get("n_features", 17),
            "project":      "BlockML-Gov"
        }
        cid = self.pin_json(summary, f"shap-{tx_id}")
        return cid or self._simulate_cid(summary)

    # ── Drift Report ─────────────────────────────────
    def pin_drift_report(self, drift_data: dict) -> str:
        """Pin drift report summary to IPFS"""
        summary = {
            "timestamp":        drift_data.get("timestamp",""),
            "drift_detected":   drift_data.get("drift_detected",False),
            "drift_share":      drift_data.get("drift_share", 0),
            "n_drifted":        drift_data.get("n_drifted_features",0),
            "drifted_features": drift_data.get("drifted_features",[]),
            "model_auc":        drift_data.get("model_auc_current",0),
            "auc_degradation":  drift_data.get("auc_degradation", 0),
            "project":          "BlockML-Gov"
        }
        cid = self.pin_json(
            summary,
            f"drift-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
        return cid or self._simulate_cid(summary)

    # ── Dataset Hash ─────────────────────────────────
    def pin_dataset_info(self,
                         dataset_name: str,
                         data_hash: str,
                         stats: dict) -> str:
        """Pin dataset metadata to IPFS"""
        info = {
            "dataset_name": dataset_name,
            "data_hash_dvc": data_hash,
            "statistics": stats,
            "pinned_at": datetime.utcnow().isoformat(),
            "project": "BlockML-Gov"
        }
        cid = self.pin_json(info, f"dataset-{dataset_name}")
        return cid or self._simulate_cid(info)

    # ── List pinned files ────────────────────────────
    def list_pinned(self, limit: int = 20) -> list:
        """List all files pinned on Pinata"""
        try:
            r = requests.get(
                f"{PINATA_BASE}/data/pinList"
                f"?status=pinned&pageLimit={limit}"
                f"&metadata[keyvalues][project]"
                f"[value]=BlockML-Gov"
                f"&metadata[keyvalues][project][op]=eq",
                headers=HEADERS, timeout=10)
            if r.status_code == 200:
                rows = r.json().get("rows", [])
                return [{
                    "cid":      row["ipfs_pin_hash"],
                    "name":     row["metadata"]["name"],
                    "size":     row["size"],
                    "date":     row["date_pinned"][:10],
                    "url":      f"{GATEWAY_BASE}/{row['ipfs_pin_hash']}"
                } for row in rows]
        except Exception as e:
            print(f"❌ list_pinned error: {e}")
        return []

    # ── Retrieve from IPFS ───────────────────────────
    def get_from_ipfs(self, cid: str) -> Optional[dict]:
        """Retrieve JSON content from IPFS via Pinata API"""
        try:
            # Use Pinata dedicated gateway
            r = requests.get(
                f"https://aquamarine-binding-narwhal-353.mypinata.cloud/ipfs/{cid}",
                headers=HEADERS,
                timeout=15)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"❌ Pinata gateway: {e}")

        # Fallback: search in pinList and reconstruct
        try:
            rows = self.list_pinned(100)
            for row in rows:
                if row.get("cid") == cid:
                    # Found metadata, try public gateway
                    for gw in [
                        f"https://ipfs.io/ipfs/{cid}",
                        f"https://gateway.pinata.cloud/ipfs/{cid}",
                    ]:
                        try:
                            r2 = requests.get(gw, timeout=10)
                            if r2.status_code == 200:
                                return r2.json()
                        except:
                            continue
        except Exception as e:
            print(f"❌ get_from_ipfs fallback: {e}")
        return None

    # ── Utils ─────────────────────────────────────────
    def _hash_file(self, path: str) -> str:
        if not path or not os.path.exists(path):
            return ""
        sha = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)
        return f"sha256:{sha.hexdigest()}"

    def _simulate_cid(self, data: dict) -> str:
        """Fallback CID if IPFS unavailable"""
        content = json.dumps(data, sort_keys=True)
        h = hashlib.sha256(content.encode()).hexdigest()
        return f"QmSIM{h[:38]}"

    def get_gateway_url(self, cid: str) -> str:
        return f"{GATEWAY_BASE}/{cid}"


# Singleton
ipfs = IPFSClient()
