"""Fraud Analyst — Live Dashboard"""
import streamlit as st
import time
from utils.api_client import get_stats, get_active_model

def show(user: dict):
    st.title("📊 Live Fraud Dashboard")

    c1,c2 = st.columns([3,1])
    with c2:
        auto = st.checkbox("🔄 Auto-refresh (5s)")

    stats = get_stats()
    if not stats:
        st.error("API unavailable")
        return

    tot = sum([stats.get("FRAUDE",0),
               stats.get("AMBIGU",0),
               stats.get("LEGITIME",0)])

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("🔴 FRAUD",
        stats.get("FRAUDE",0),
        delta=f"{stats.get('FRAUDE',0)/tot*100:.1f}%"
        if tot else "0%")
    c2.metric("🟡 AMBIGUOUS",
        stats.get("AMBIGU",0))
    c3.metric("🟢 LEGITIMATE",
        stats.get("LEGITIME",0))
    c4.metric("📦 Total", tot)

    st.subheader("📬 Blockchain Outbox")
    ob = stats.get("outbox",{})
    c1,c2,c3 = st.columns(3)
    c1.metric("Pending",    ob.get("pending",0))
    c2.metric("✅ Success", ob.get("total_success",0))
    c3.metric("❌ Failed",  ob.get("total_failed",0))

    active = get_active_model()
    if active:
        st.info(
            f"🤖 **Active Model:** "
            f"{active.get('model_id')} "
            f"({active.get('model_type')})")

    if auto:
        time.sleep(5)
        st.rerun()
