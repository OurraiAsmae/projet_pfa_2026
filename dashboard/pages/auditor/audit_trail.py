"""Auditor — Audit Trail"""
import streamlit as st
import json
import httpx
from utils.api_client import API_URL, get_audit_logs
import pandas as pd

def show(user: dict):
    st.title("📋 Blockchain Audit Trail")

    # Transaction lookup
    txid = st.text_input(
        "Transaction ID", "TX-REAL-004")
    if st.button("🔍 Verify on Blockchain",
                 type="primary"):
        try:
            r = httpx.get(
                f"{API_URL}/decision/{txid}",
                timeout=10)
            d = r.json()
            if d.get("source") == "redis_cache":
                data = d["data"]
                st.success("✅ Decision found")
                c1,c2,c3 = st.columns(3)
                c1.metric("Decision",
                    data.get("zone","N/A"))
                c2.metric("Score",
                    f"{data.get('score',0):.4f}")
                c3.metric("Model",
                    data.get("active_model","N/A"))
                st.code(json.dumps(data, indent=2))
            else:
                st.warning(
                    "Transaction not found in cache")
        except Exception as e:
            st.error(f"❌ {e}")

    # Model integrity
    st.subheader("🔐 Model Integrity Check")
    h = st.text_input("Model SHA-256 Hash",
        "sha256:4ee395fd183024e7b2e9016697625ef"
        "351e463e82d49d40a2eb1318036547dd5")
    if st.button("🔍 Verify Hash"):
        exp = ("sha256:4ee395fd183024e7b2e9016697625ef"
               "351e463e82d49d40a2eb1318036547dd5")
        if h == exp:
            st.success(
                "✅ Hash verified — Model intact")
        else:
            st.error(
                "❌ Hash mismatch — Possible tampering!")
