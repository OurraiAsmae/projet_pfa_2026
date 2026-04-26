"""Data Scientist — MLflow Experiments"""
import streamlit as st
from utils.api_client import (get_mlflow_experiments,
                               get_mlflow_runs,
                               get_mlflow_run,
                               mlflow_dict,
                               ML_URL)

def show(user: dict):
    st.title("🔬 MLflow Experiment Tracking")

    experiments = get_mlflow_experiments()
    nms = {e["experiment_id"]: e["name"]
           for e in experiments
           if e["name"] != "Default"}

    if not nms:
        st.info("No experiments yet. Upload a model first.")
        st.markdown(
            f"[🔗 Open MLflow UI](http://localhost:5000)")
        return

    sel = st.selectbox("Experiment", list(nms.values()))
    eid = [k for k,v in nms.items() if v==sel]

    if not eid:
        return

    runs = get_mlflow_runs(eid[0])
    if not runs:
        st.info("No runs in this experiment.")
        return

    for run in runs:
        info = run["info"]
        data = run.get("data",{})
        m    = mlflow_dict(data.get("metrics",{}))
        p    = mlflow_dict(data.get("params",{}))

        with st.expander(
            f"🏃 {info.get('run_name',info['run_id'][:8])} "
            f"— AUC: {m.get('auc_roc',0):.4f}"):

            c1,c2,c3,c4 = st.columns(4)
            c1.metric("AUC-ROC",
                f"{m.get('auc_roc',0):.4f}")
            c2.metric("F1",
                f"{m.get('f1',0):.4f}")
            c3.metric("Recall",
                f"{m.get('recall',0):.4f}")
            c4.metric("Type",
                p.get("model_type","N/A"))

            st.caption(
                f"Dataset: "
                f"{p.get('dataset_id','N/A')} "
                f"| Submitted by: "
                f"{p.get('submitted_by','N/A')}")

            st.code(
                f"Run ID     : {info['run_id']}\n"
                f"Model Hash : "
                f"{p.get('model_hash_sha256','N/A')}\n"
                f"Dataset ID : "
                f"{p.get('dataset_id','N/A')}\n"
                f"Dataset DVC: "
                f"{p.get('dataset_hash_dvc','N/A')}")

    st.markdown(
        f"[🔗 Open MLflow UI](http://localhost:5000)")
