"""Fraud Analyst — Alerts"""
import streamlit as st
from utils.api_client import get_alerts

def show(user: dict):
    st.title("🚨 Rate Limiting Alerts")

    if st.button("🔄 Refresh"):
        st.rerun()

    alerts = get_alerts()
    if alerts:
        st.error(f"⚠️ {len(alerts)} active alerts!")
        for a in alerts:
            st.warning(
                f"**{a['card_id']}** — "
                f"{a['count']} tx in {a['window']}s "
                f"— {a['detected_at']}")
    else:
        st.success("✅ No active alerts")
