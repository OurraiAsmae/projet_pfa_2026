"""Compliance Officer — Validation History"""
import streamlit as st
import pandas as pd
from utils.api_client import get_all_models_governance

def show(user: dict):
    st.title("📋 Validation History")

    models = get_all_models_governance()
    if not models:
        st.info("No validation history yet.")
        return

    # Filtrer les modèles traités par CO
    statuses = ["COMPLIANCE_VALIDATED", "REJECTED",
                "TECHNICAL_APPROVED", "DEPLOYED", "REVOKED"]
    filtered = [m for m in models if m.get("status") in statuses]

    if not filtered:
        st.info("No validation history yet.")
        return

    st.metric("Total Actions", len(filtered))

    # Colonnes utiles
    rows = []
    for m in filtered:
        rows.append({
            "Model ID":    m.get("modelID", m.get("model_id", "")),
            "Status":      m.get("status", ""),
            "CO ID":       m.get("complianceOfficerID", "—"),
            "Validated At":m.get("complianceAt", "—"),
            "Reject Reason": m.get("revokeReason", "—"),
            "AUC":         m.get("auc", "—"),
        })

    df = pd.DataFrame(rows)

    # Colorer par statut
    def color_status(val):
        colors = {
            "COMPLIANCE_VALIDATED": "background-color:#D1FAE5;color:#065F46",
            "REJECTED":             "background-color:#FEE2E2;color:#991B1B",
            "TECHNICAL_APPROVED":   "background-color:#DBEAFE;color:#1E40AF",
            "DEPLOYED":             "background-color:#D1FAE5;color:#065F46",
            "REVOKED":              "background-color:#F3F4F6;color:#374151",
        }
        return colors.get(val, "")

    st.dataframe(
        df.style.applymap(color_status, subset=["Status"]),
        use_container_width=True)
