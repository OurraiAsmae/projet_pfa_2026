"""
BlockML-Gov API Client
Centralized API calls for all pages
"""
import httpx
import streamlit as st
import os

API_URL  = os.getenv("API_URL",  "http://api:8000")
GW_URL   = os.getenv("GATEWAY_URL", "http://gateway:9999")
ML_URL   = os.getenv("MLFLOW_URL",  "http://mlflow:5000")
AUTH_URL = os.getenv("AUTH_URL",    "http://auth-service:8001")

TIMEOUT_SHORT  = 5
TIMEOUT_MEDIUM = 15
TIMEOUT_LONG   = 120

def auth_headers(token: str = None) -> dict:
    if token is None:
        try:
            token = st.session_state.get("token","")
        except:
            token = ""
    return {"Authorization": f"Bearer {token}"}

# ── Auth ─────────────────────────────────────────────
def login(username: str, password: str) -> dict:
    try:
        r = httpx.post(f"{AUTH_URL}/auth/login",
            json={"username": username,
                  "password": password},
            timeout=10)
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def logout(token: str):
    try:
        httpx.post(f"{AUTH_URL}/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5)
    except:
        pass

# ── Users ─────────────────────────────────────────────
def get_users(token: str = None) -> list:
    try:
        r = httpx.get(f"{AUTH_URL}/users",
            headers=auth_headers(token),
            timeout=TIMEOUT_SHORT)
        return r.json().get("users", [])
    except Exception as e:
        print(f"get_users error: {e}")
        return []

def create_user(data: dict,
                token: str = None) -> tuple:
    try:
        r = httpx.post(f"{AUTH_URL}/users",
            headers=auth_headers(token),
            json=data, timeout=TIMEOUT_SHORT)
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def update_user(user_id: int, data: dict,
                token: str = None) -> tuple:
    try:
        r = httpx.put(f"{AUTH_URL}/users/{user_id}",
            headers=auth_headers(token),
            json=data, timeout=TIMEOUT_SHORT)
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def delete_user(user_id: int,
                token: str = None) -> tuple:
    try:
        r = httpx.delete(f"{AUTH_URL}/users/{user_id}",
            headers=auth_headers(token),
            timeout=TIMEOUT_SHORT)
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def get_audit_logs(limit: int = 100,
                    token: str = None) -> list:
    try:
        r = httpx.get(f"{AUTH_URL}/audit-logs",
            params={"limit": limit},
            headers=auth_headers(token),
            timeout=TIMEOUT_SHORT)
        return r.json().get("logs", [])
    except Exception as e:
        print(f"get_audit_logs error: {e}")
        return []

# ── Models ────────────────────────────────────────────
def get_active_model() -> dict:
    try:
        return httpx.get(f"{API_URL}/model/active",
            timeout=TIMEOUT_SHORT).json()
    except:
        return {}

def get_models_info() -> list:
    try:
        r = httpx.get(f"{API_URL}/models/info",
            timeout=TIMEOUT_SHORT)
        return r.json().get("models", [])
    except:
        return []

def deploy_model(model_id: str,
                 model_path: str) -> dict:
    try:
        r = httpx.post(
            f"{API_URL}/model/deploy/{model_id}",
            params={"model_path": model_path},
            timeout=TIMEOUT_MEDIUM)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ── Governance ────────────────────────────────────────
def validate_compliance(model_id: str) -> dict:
    try:
        r = httpx.post(
            f"{API_URL}/governance/validate-compliance/{model_id}",
            timeout=TIMEOUT_MEDIUM)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def approve_technical(model_id: str) -> dict:
    try:
        r = httpx.post(
            f"{API_URL}/governance/approve-technical/{model_id}",
            timeout=TIMEOUT_MEDIUM)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def deploy_governance(model_id: str) -> dict:
    try:
        r = httpx.post(
            f"{API_URL}/governance/deploy/{model_id}",
            timeout=TIMEOUT_MEDIUM)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def revoke_model(model_id: str,
                 reason: str) -> dict:
    try:
        r = httpx.post(
            f"{API_URL}/governance/revoke/{model_id}",
            params={"reason": reason},
            timeout=TIMEOUT_MEDIUM)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def reject_model(model_id: str, reason: str, category: str, signer: str = "User2@bank.fraud-governance.com") -> dict:
    try:
        r = httpx.post(
            f"{API_URL}/governance/reject/{model_id}",
            params={"reason": reason, "category": category, "signer": signer},
            timeout=TIMEOUT_MEDIUM)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def reject_model(model_id: str, reason: str, category: str, signer: str = "User2@bank.fraud-governance.com") -> dict:
    try:
        r = httpx.post(
            f"{API_URL}/governance/reject/{model_id}",
            params={"reason": reason, "category": category, "signer": signer},
            timeout=TIMEOUT_MEDIUM)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_model_governance(model_id: str) -> dict:
    try:
        r = httpx.get(
            f"{API_URL}/governance/model/{model_id}",
            timeout=TIMEOUT_MEDIUM)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ── Datasets ──────────────────────────────────────────
def upload_dataset(file_content: bytes,
                   filename: str,
                   dataset_name: str,
                   uploaded_by: str) -> dict:
    try:
        r = httpx.post(
            f"{API_URL}/datasets/upload",
            files={"file": (filename, file_content, "text/csv")},
            data={"dataset_name": dataset_name,
                  "uploaded_by": uploaded_by},
            timeout=TIMEOUT_LONG)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_datasets() -> list:
    try:
        r = httpx.get(f"{API_URL}/datasets/list",
            timeout=TIMEOUT_SHORT)
        return r.json().get("datasets", [])
    except:
        return []

def get_dataset_analysis(dataset_id: str) -> dict:
    try:
        r = httpx.get(
            f"{API_URL}/datasets/{dataset_id}/analysis",
            timeout=TIMEOUT_MEDIUM)
        return r.json()
    except:
        return {}

def get_dataset_lineage(dataset_id: str) -> dict:
    try:
        r = httpx.get(
            f"{API_URL}/datasets/{dataset_id}/lineage",
            timeout=TIMEOUT_SHORT)
        return r.json()
    except:
        return {}

def compare_datasets(id1: str, id2: str) -> dict:
    try:
        r = httpx.get(
            f"{API_URL}/datasets/compare/{id1}/{id2}",
            timeout=TIMEOUT_MEDIUM)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ── Predictions ───────────────────────────────────────
def predict(tx_data: dict) -> dict:
    try:
        r = httpx.post(f"{API_URL}/predict",
            json=tx_data, timeout=TIMEOUT_MEDIUM)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_stats() -> dict:
    try:
        return httpx.get(f"{API_URL}/stats",
            timeout=TIMEOUT_SHORT).json()
    except:
        return {}

def get_alerts() -> list:
    try:
        return httpx.get(f"{API_URL}/alerts",
            timeout=TIMEOUT_SHORT).json()
    except:
        return []

# ── SHAP ──────────────────────────────────────────────
def get_shap(tx_id: str) -> dict:
    try:
        r = httpx.get(f"{API_URL}/shap/{tx_id}",
            timeout=TIMEOUT_MEDIUM)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ── IPFS ──────────────────────────────────────────────
def get_ipfs_list() -> list:
    try:
        r = httpx.get(f"{API_URL}/ipfs/list",
            timeout=TIMEOUT_SHORT)
        return r.json().get("files", [])
    except:
        return []

# ── Drift ─────────────────────────────────────────────
def get_drift_latest() -> dict:
    try:
        return httpx.get(f"{API_URL}/drift/latest",
            timeout=TIMEOUT_SHORT).json()
    except:
        return {}

# ── MLflow ────────────────────────────────────────────
def mlflow_dict(lst) -> dict:
    if isinstance(lst, list):
        return {i["key"]: i["value"]
                for i in lst if "key" in i}
    return lst if isinstance(lst, dict) else {}

def get_mlflow_experiments() -> list:
    try:
        r = httpx.get(
            f"{ML_URL}/api/2.0/mlflow/experiments/search",
            params={"max_results": 20},
            timeout=TIMEOUT_SHORT)
        return r.json().get("experiments", [])
    except:
        return []

def get_mlflow_runs(experiment_id: str) -> list:
    try:
        r = httpx.post(
            f"{ML_URL}/api/2.0/mlflow/runs/search",
            json={"experiment_ids": [experiment_id],
                  "max_results": 10},
            timeout=TIMEOUT_SHORT)
        return r.json().get("runs", [])
    except:
        return []

def get_mlflow_models() -> list:
    try:
        r = httpx.get(
            f"{ML_URL}/api/2.0/mlflow/"
            "registered-models/search",
            timeout=TIMEOUT_SHORT)
        d = r.json()
        return d.get("registered_models", []) \
               if isinstance(d, dict) else []
    except:
        return []

def get_mlflow_run(run_id: str) -> dict:
    try:
        r = httpx.get(
            f"{ML_URL}/api/2.0/mlflow/runs/get",
            params={"run_id": run_id},
            timeout=TIMEOUT_SHORT)
        return r.json().get("run", {})
    except:
        return {}

# ── Health ────────────────────────────────────────────
def get_health() -> dict:
    try:
        return httpx.get(f"{API_URL}/health",
            timeout=TIMEOUT_SHORT).json()
    except:
        return {"status": "error"}

def get_gateway_health() -> dict:
    try:
        return httpx.get(f"{GW_URL}/health",
            timeout=TIMEOUT_SHORT).json()
    except:
        return {"status": "error"}

def get_auth_health() -> dict:
    try:
        return httpx.get(f"{AUTH_URL}/health",
            timeout=TIMEOUT_SHORT).json()
    except:
        return {"status": "error"}

def mlflow_params(lst) -> dict:
    if isinstance(lst, list):
        return {i["key"]: i["value"]
                for i in lst if "key" in i}
    return lst if isinstance(lst, dict) else {}

def get_all_models_governance() -> list:
    """Récupère tous les modèles depuis la blockchain via endpoint dynamique"""
    try:
        r = httpx.get(
            f"{API_URL}/governance/all-models",
            timeout=30)
        if r.status_code == 200:
            return r.json().get("models", [])
    except Exception as e:
        print(f"get_all_models_governance error: {e}")
    return []

def get_all_models_governance_old() -> list:
    """Legacy — liste fixe"""
    model_ids = [
        "RandomForest-FraudDetection-v1.0",
        "grad-FraudDetection-v1.0",
        "log-FraudDetection-v1.0",
        "gradient-FraudDetection-v1.0",
        "Forest-FraudDetection-v1.0",
        "logistic-v1.0",
        "RF-Test-v4.0",
        "random-FraudDetection-v2.0",
        "test-FraudDetection-v2.0",
        "LL-FraudDetection-v2.0",
    ]
    results = []
    for mid in model_ids:
        try:
            r = httpx.get(
                f"{API_URL}/governance/model/{mid}",
                timeout=TIMEOUT_SHORT)
            if r.status_code == 200:
                data = r.json()
                if data.get("modelID"):
                    results.append(data)
                elif data.get("success") and data.get("data"):
                    results.append(data["data"])
        except Exception:
            pass
    return results

def evaluate_model_metrics(model_path: str, dataset_id: str = "") -> dict:
    """Evaluate model by uploading pkl file to API"""
    try:
        with open(model_path, "rb") as f:
            files = {"file": ("model.pkl", f, "application/octet-stream")}
            params = {}
            if dataset_id:
                params["dataset_id"] = dataset_id
            r = httpx.post(
                f"{API_URL}/model/evaluate-upload",
                files=files,
                params=params,
                timeout=120)
        return r.json()
    except Exception as e:
        return {"error": str(e)}
