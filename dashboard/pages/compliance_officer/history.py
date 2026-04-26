"""Compliance Officer — Validation History"""
import streamlit as st
import pandas as pd
from utils.api_client import get_audit_logs

def show(user: dict):
    st.title("📋 Validation History")
    logs = get_audit_logs(200)
    filtered = [l for l in logs
                if l.get("action") in
                ("VALIDATE_COMPLIANCE","REJECT_MODEL")]
    if filtered:
        st.metric("Total Actions", len(filtered))
        st.dataframe(
            pd.DataFrame(filtered),
            use_container_width=True)
    else:
        st.info("No validation history yet.")
