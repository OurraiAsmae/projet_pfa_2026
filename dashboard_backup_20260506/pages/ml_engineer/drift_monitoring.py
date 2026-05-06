"""ML Engineer — Drift Monitoring"""
import streamlit as st
import pandas as pd
from utils.api_client import get_drift_latest

def show(user: dict):
    st.title("📉 Drift Monitoring — Evidently AI")

    c1,c2 = st.columns([3,1])
    with c2:
        if st.button("🔄 Refresh"):
            st.rerun()

    d = get_drift_latest()
    if not d or d.get("status") == "no_data":
        st.warning("No drift report available yet.")
        return

    sh = d.get("drift_share",0)
    if sh > 0.30:
        st.error(
            "🔴 CRITICAL DRIFT — "
            "Immediate retraining required!")
    elif sh > 0.15:
        st.warning(
            "🟡 DRIFT DETECTED — "
            "Close monitoring required")
    else:
        st.success("🟢 No significant drift detected")

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Drift Share", f"{sh:.2%}")
    c2.metric("Drifted Features",
        d.get("n_drifted_features",0))
    a  = d.get("model_auc_current",0)
    rf = d.get("model_auc_reference",0.9503)
    c3.metric("Production AUC",
        f"{a:.4f}", delta=f"{a-rf:.4f}")
    c4.metric("AUC Degradation",
        f"{d.get('auc_degradation',0):.4f}")

    if d.get("drifted_features"):
        st.subheader("Drifted Features")
        st.dataframe(
            pd.DataFrame(d["drifted_features"]),
            use_container_width=True)

    st.caption(
        f"Last check: {d.get('timestamp','N/A')}")
