"""Admin — Audit Logs"""
import streamlit as st
import pandas as pd
from utils.api_client import get_audit_logs

def show(user: dict):
    st.title("📋 System Audit Logs")
    token = st.session_state.get("token","")

    c1,c2,c3 = st.columns([2,2,1])
    limit = c3.number_input("Limit", 10, 500, 100)

    logs = get_audit_logs(limit, token=token)
    if not logs:
        st.info("No audit logs yet.")
        return

    df = pd.DataFrame(logs)
    c1,c2 = st.columns(2)
    actions = ["All"] + sorted(df["action"].unique().tolist())
    users_f = ["All"] + sorted(
        df["username"].dropna().unique().tolist())
    sel_action = c1.selectbox("Filter by Action", actions)
    sel_user   = c2.selectbox("Filter by User", users_f)

    if sel_action != "All":
        df = df[df["action"] == sel_action]
    if sel_user != "All":
        df = df[df["username"] == sel_user]

    st.metric("Total Records", len(df))
    st.dataframe(df, use_container_width=True)
