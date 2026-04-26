"""Regulator — System Status"""
import streamlit as st
from utils.api_client import (get_health,
                               get_gateway_health,
                               get_auth_health,
                               get_active_model,
                               AUTH_URL, GW_URL)

CHANNELS = {
    "modelgovernance": ("BankOrg",
                        "ML Model Lifecycle"),
    "frauddetection":  ("BankOrg",
                        "Fraud Decisions"),
    "compliance":      ("Bank+Audit",
                        "Internal Reports"),
    "regulatory":      ("Audit+Reg",
                        "BAM Submissions"),
}

def show(user: dict):
    st.title("🏛️ System Status")

    # Services
    c1,c2 = st.columns(2)
    with c1:
        st.subheader("🔧 Services")
        for nm, fn in [
            ("ML API",       get_health),
            ("Gateway",      get_gateway_health),
            ("Auth Service", get_auth_health)
        ]:
            h = fn()
            if h.get("status") == "ok":
                st.success(f"✅ {nm} — online")
            else:
                st.error(f"❌ {nm} — unavailable")

    with c2:
        st.subheader("📦 Blockchain Channels")
        for ch,(orgs,desc) in CHANNELS.items():
            st.info(f"**{ch}** ({orgs}): {desc}")

    # Active model
    st.subheader("🤖 Active Production Model")
    active = get_active_model()
    if active:
        c1,c2,c3 = st.columns(3)
        c1.metric("Model ID",
            active.get("model_id","N/A"))
        c2.metric("Type",
            active.get("model_type","N/A"))
        c3.metric("Status",
            active.get("status","N/A"))
        if active.get("deployed_at"):
            st.caption(
                f"Deployed: "
                f"{active['deployed_at'][:19]} UTC")
    else:
        st.warning("No active model")

    # BAM section
    if "BAM" in st.session_state.get(
            "current_page",""):
        st.subheader("📨 BAM Submissions")
        st.metric("Reports This Month", "0")

    if "Inspection" in st.session_state.get(
            "current_page",""):
        st.subheader("🔍 Inspection")
        if st.button("📋 Request Inspection",
                     type="primary"):
            st.success(
                "✅ Inspection request submitted")
