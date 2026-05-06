"""ML Engineer — Drift Monitoring"""
import streamlit as st
import pandas as pd
from utils.api_client import get_drift_latest
from styles import (
    _header, _card_header, _alert_box,
    _ICON_CHART, _ICON_WARNING, _ICON_ERROR, _ICON_SUCCESS, _ICON_INFO
)

def show(user: dict):
    _header("Drift Monitoring — Evidently AI", _ICON_CHART)

    c1,c2 = st.columns([3,1])
    with c2:
        if st.button("Refresh"):
            st.rerun()

    d = get_drift_latest()
    if not d or d.get("status") == "no_data":
        _alert_box("WARNING", "No drift report available yet.", _ICON_WARNING)
        return

    sh = d.get("drift_share",0)
    if sh > 0.30:
        _alert_box("ERROR", "CRITICAL DRIFT — Immediate retraining required!", _ICON_ERROR)
    elif sh > 0.15:
        _alert_box("WARNING", "DRIFT DETECTED — Close monitoring required", _ICON_WARNING)
    else:
        _alert_box("SUCCESS", "No significant drift detected", _ICON_SUCCESS)

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
        _card_header("Drifted Features", _ICON_INFO)
        st.dataframe(
            pd.DataFrame(d["drifted_features"]),
            use_container_width=True)

    st.caption(
        f"Last check: {d.get('timestamp','N/A')}")
