"""Auditor — Compliance Reports"""
import streamlit as st

def show(user: dict):
    st.title("📄 Compliance Reports")
    st.metric("Reports Pending", "0")
    if st.button("📄 Generate Monthly Report",
                 type="primary"):
        st.success(
            "✅ Report initiated on blockchain "
            "(channel: compliance)")
