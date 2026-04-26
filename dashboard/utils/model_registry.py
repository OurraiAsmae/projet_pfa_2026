"""
Shared utility — MLflow to Blockchain ID mapping
Uses run_name from MLflow as blockchain model ID
"""
import httpx
from utils.api_client import ML_URL, API_URL

def get_mlflow_bc_mapping() -> dict:
    """
    Returns mapping:
    {mlflow_name: {bc_id, run_id, run_name, model_type, metrics, params}}
    Uses run_name as blockchain ID
    """
    result = {}
    try:
        r = httpx.get(
            f"{ML_URL}/api/2.0/mlflow/"
            "registered-models/search",
            params={"max_results": 50},
            timeout=5)
        models = r.json().get(
            "registered_models", [])

        for m in models:
            v = (m["latest_versions"][-1]
                 if m.get("latest_versions") else None)
            if not v:
                continue

            rr = httpx.get(
                f"{ML_URL}/api/2.0/mlflow/runs/get",
                params={"run_id": v["run_id"]},
                timeout=5)
            run_info = rr.json().get(
                "run", {})
            run_name = run_info.get(
                "info", {}).get("run_name", "")
            data     = run_info.get("data", {})

            metrics = {
                i["key"]: float(i["value"])
                for i in data.get("metrics", [])
                if "key" in i and
                isinstance(i.get("value"), (int,float))
                or _is_float(str(i.get("value","")))
            }
            params = {
                i["key"]: i["value"]
                for i in data.get("params", [])
                if "key" in i
            }

            # Check if blockchain ID exists
            bc_id     = run_name
            bc_status = _get_bc_status(bc_id)

            result[m["name"]] = {
                "bc_id":      bc_id,
                "bc_status":  bc_status,
                "run_id":     v["run_id"],
                "run_name":   run_name,
                "version":    v["version"],
                "model_type": params.get(
                    "model_type", "Unknown"),
                "dataset_id": params.get(
                    "dataset_id", "N/A"),
                "submitted_by": params.get(
                    "submitted_by", "Unknown"),
                "model_hash": params.get(
                    "model_hash_sha256", "N/A"),
                "auc_roc":    metrics.get("auc_roc", 0),
                "f1":         metrics.get("f1", 0),
                "recall":     metrics.get("recall", 0),
                "precision":  metrics.get("precision",0),
                "n_train":    int(metrics.get(
                    "n_train", 0)),
                "metrics":    metrics,
                "params":     params,
                "on_chain":   bc_status != "UNKNOWN"
            }
    except Exception as e:
        print(f"get_mlflow_bc_mapping error: {e}")
    return result


def _get_bc_status(model_id: str) -> str:
    """Get blockchain status"""
    try:
        r = httpx.get(
            f"{API_URL}/governance/model/{model_id}",
            timeout=8)
        if r.status_code == 200:
            d = r.json()
            if isinstance(d, dict):
                return d.get("status", "UNKNOWN")
    except:
        pass
    return "UNKNOWN"


def _is_float(s: str) -> bool:
    """Check if string is a float"""
    try:
        float(s)
        return True
    except:
        return False
