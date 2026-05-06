"""Data Scientist — MLflow Experiments"""
import streamlit as st
from utils.api_client import (get_mlflow_experiments,
                               get_mlflow_runs,
                               get_mlflow_run,
                               mlflow_dict,
                               ML_URL)

# --- SVG Icons ---
_ICON_FLASK = '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#1F7A5A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3h6v3l-3 3-3-3V3z"/><path d="M8.5 9L4 18a2 2 0 0 0 1.7 3h12.6A2 2 0 0 0 20 18l-4.5-9"/></svg>'

def _header(title: str, subtitle: str, icon_svg: str):
    st.markdown(f"""
        <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.5rem;padding-bottom:1rem;border-bottom:1px solid #E5E7EB;">
            <div style="width:48px;height:48px;background:#F0FAF6;border-radius:12px;display:flex;align-items:center;justify-content:center;">
                {icon_svg}
            </div>
            <div>
                <h1 style="margin:0;padding:0;font-size:1.6rem;color:#111827;font-weight:700;">{title}</h1>
                <p style="margin:0;padding:0;color:#6B7280;font-size:0.9rem;">{subtitle}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)


def show(user: dict):
    _header(
        "MLflow Experiment Tracking",
        "Track hyperparameter tuning and model performance metrics centrally.",
        _ICON_FLASK
    )

    experiments = get_mlflow_experiments()
    nms = {e["experiment_id"]: e["name"]
           for e in experiments
           if e["name"] != "Default"}

    if not nms:
        st.info("No experiments yet. Upload a model first.")
        st.markdown(
            f"[Open MLflow UI](http://localhost:5000)")
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
            f"[RUN] {info.get('run_name',info['run_id'][:8])} "
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
        f"[Open MLflow UI](http://localhost:5000)")
