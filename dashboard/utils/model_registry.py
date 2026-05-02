"""
Shared utility — MLflow to Blockchain ID mapping
Uses run_name from MLflow as blockchain model ID
"""
import httpx
from utils.api_client import ML_URL, API_URL

def get_mlflow_bc_mapping() -> dict:
    """
    Returns mapping of all MLflow runs → blockchain status
    Uses run_name as blockchain ID
    """
    result = {}
    try:
        # Get all experiments
        r = httpx.get(
            f"{ML_URL}/api/2.0/mlflow/experiments/search",
            params={"max_results": 50},
            timeout=5)
        experiments = r.json().get("experiments", [])

        for exp in experiments:
            if exp["name"] == "Default":
                continue
            # Get all runs for this experiment
            rr = httpx.post(
                f"{ML_URL}/api/2.0/mlflow/runs/search",
                json={"experiment_ids": [exp["experiment_id"]],
                      "max_results": 20},
                timeout=5)
            runs = rr.json().get("runs", [])

            for run in runs:
                info     = run.get("info", {})
                data     = run.get("data", {})
                run_name = info.get("run_name", "")

                if not run_name:
                    continue

                metrics = {m["key"]: float(m["value"])
                          for m in data.get("metrics", [])
                          if _is_float(str(m.get("value","")))}
                params  = {p["key"]: p["value"]
                          for p in data.get("params", [])}

                # Skip if AUC is 0 (bad run)
                if metrics.get("auc_roc", 0) == 0:
                    continue

                bc_id     = run_name
                bc_status = _get_bc_status(bc_id)

                # Only add if on blockchain OR has good metrics
                if bc_status != "UNKNOWN" or metrics.get("auc_roc", 0) > 0:
                    # Keep best AUC if duplicate run_name
                    if bc_id in result:
                        if metrics.get("auc_roc", 0) <= result[bc_id].get("auc_roc", 0):
                            continue

                    mlflow_name = f"{exp['name'].replace('fraud-','FraudDetection-')}"

                    result[bc_id] = {
                        "bc_id":        bc_id,
                        "bc_status":    bc_status,
                        "run_id":       info.get("run_id",""),
                        "run_name":     run_name,
                        "version":      params.get("version","1.0"),
                        "model_type":   params.get("model_type","Unknown"),
                        "dataset_id":   params.get("dataset","N/A"),
                        "submitted_by": params.get("submitted_by","Unknown"),
                        "model_hash":   params.get("model_hash_sha256","N/A"),
                        "auc_roc":      metrics.get("auc_roc", 0),
                        "f1":           metrics.get("f1", 0),
                        "recall":       metrics.get("recall", 0),
                        "precision":    metrics.get("precision", 0),
                        "n_train":      int(metrics.get("n_train", 0)),
                        "metrics":      metrics,
                        "params":       params,
                        "on_chain":     bc_status != "UNKNOWN",
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
    try:
        float(s)
        return True
    except:
        return False
