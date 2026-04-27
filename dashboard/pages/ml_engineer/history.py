"""ML Engineer — Model History"""
import streamlit as st
import pandas as pd
from utils.api_client import get_all_models_governance

def show(user: dict):
    st.title("📜 Model History")

    with st.spinner("Loading blockchain history..."):
        all_models = get_all_models_governance()

    if not all_models:
        st.info("No history yet.")
        return

    status_colors = {
        "DEPLOYED":             "🟢",
        "TECHNICAL_APPROVED":   "🔵",
        "COMPLIANCE_VALIDATED": "🟡",
        "SUBMITTED":            "⚪",
        "REJECTED":             "🔴",
        "REVOKED":              "⚫",
    }

    # Filtres
    col1, col2 = st.columns(2)
    with col1:
        filter_status = st.multiselect(
            "Filter by Status",
            options=list(status_colors.keys()),
            default=["DEPLOYED","TECHNICAL_APPROVED",
                     "COMPLIANCE_VALIDATED","REJECTED","REVOKED"])
    with col2:
        st.metric("Total Models", len(all_models))

    filtered = [m for m in all_models
                if m.get("status") in filter_status]

    if not filtered:
        st.info("No models match the filter.")
        return

    rows = []
    for m in filtered:
        status = m.get("status", "")
        # Déterminer qui a traité
        co_id  = m.get("complianceOfficerID", "") or "—"
        mle_id = m.get("mlEngineerID", "") or "—"

        # Simplifier les IDs
        co_short  = "CO: " + co_id.split("@")[0] if "@" in co_id else co_id
        mle_short = "MLE: " + mle_id.split("@")[0] if "@" in mle_id else mle_id

        rows.append({
            "Model ID":      m.get("modelID", ""),
            "Status":        f"{status_colors.get(status,'❓')} {status}",
            "AUC":           round(m.get("auc", 0), 4),
            "F1":            round(m.get("f1", 0), 4),
            "Compliance Officer": co_short,
            "ML Engineer":   mle_short,
            "Submitted At":  str(m.get("submittedAt",""))[:10],
            "Reason":        str(m.get("revokeReason",""))[:80],
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    # Stats
    st.markdown("---")
    st.subheader("📊 Statistics")
    c1, c2, c3, c4 = st.columns(4)
    statuses = [m.get("status") for m in all_models]
    c1.metric("🟢 Deployed",   statuses.count("DEPLOYED"))
    c2.metric("🔴 Rejected",   statuses.count("REJECTED"))
    c3.metric("⚫ Revoked",    statuses.count("REVOKED"))
    c4.metric("⚪ Pending",    statuses.count("SUBMITTED"))
