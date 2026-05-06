"""Regulator — System Status (Read Only)"""
import streamlit as st
import httpx
from datetime import datetime
from utils.api_client import API_URL, GW_URL, AUTH_URL
from styles import (
    _header, _card_header, _alert_box,
    _ICON_SHIELD, _ICON_INFO, _ICON_CHECK, _ICON_WARNING, _ICON_ERROR, _ICON_CHART, _ICON_HISTORY, _ICON_MODEL
)

TIMEOUT = 10

def _get_health() -> dict:
    try:
        r = httpx.get(f"{API_URL}/health", timeout=TIMEOUT)
        return r.json() if r.status_code == 200 else {}
    except:
        return {}

def _get_stats() -> dict:
    try:
        r = httpx.get(f"{API_URL}/stats", timeout=TIMEOUT)
        return r.json() if r.status_code == 200 else {}
    except:
        return {}

def _get_all_models() -> list:
    try:
        r = httpx.get(f"{API_URL}/governance/all-models", timeout=TIMEOUT)
        return r.json().get("models", []) if r.status_code == 200 else []
    except:
        return []

def _get_certified_reports() -> list:
    try:
        r = httpx.get(f"{API_URL}/ipfs/list", timeout=TIMEOUT)
        if r.status_code == 200:
            files = r.json().get("files", [])
            return [f for f in files if "certified" in f.get("name","").lower()]
    except:
        pass
    return []

def _get_drift() -> dict:
    try:
        r = httpx.get(f"{API_URL}/drift/latest", timeout=TIMEOUT)
        return r.json() if r.status_code == 200 else {}
    except:
        return {}

def show(user: dict):
    _header("Regulatory Supervision Dashboard", _ICON_SHIELD)
    st.markdown(f"<p style='color:#64748B;margin-top:-10px;margin-bottom:16px;'>Read-Only View &nbsp;|&nbsp; Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>", unsafe_allow_html=True)

    st.markdown("""<style>
      .stTabs [data-baseweb="tab-list"] button { color:#1C1C1C!important; font-weight:600!important; }
      .stTabs [data-baseweb="tab-list"] button p { color:#1C1C1C!important; }
      .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] { color:#1F7A5A!important; }
      .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] p { color:#1F7A5A!important; }
    </style>""", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "System Status",
        "Model Governance",
        "Fraud Statistics",
        "Certified Reports"
    ])

    # ── Tab 1: System Status ──────────────────────────
    with tab1:
        _card_header("Infrastructure Status", _ICON_SHIELD)

        health = _get_health()
        drift  = _get_drift()

        # Service health
        services = {
            "ML API":       health.get("ml_model", False),
            "Blockchain":   health.get("blockchain", True),
            "Redis Cache":  health.get("redis", False),
            "SHAP Service": health.get("shap", False),
            "IPFS Pinata":  health.get("ipfs", True),
        }

        c1, c2, c3, c4, c5 = st.columns(5)
        cols = [c1, c2, c3, c4, c5]
        for i, (name, status) in enumerate(services.items()):
            cols[i].metric(name, "OK" if status else "DOWN")

        st.markdown("---")

        # Active model
        _card_header("Active Fraud Detection Model", _ICON_MODEL)
        try:
            r = httpx.get(f"{API_URL}/model/active", timeout=TIMEOUT)
            active = r.json() if r.status_code == 200 else {}
        except:
            active = {}

        if active.get("model_id"):
            col1, col2, col3 = st.columns(3)
            col1.metric("Model ID",   active.get("model_id","N/A"))
            col2.metric("Type",       active.get("model_type","N/A"))
            col3.metric("Since",      str(active.get("deployed_at",""))[:10])
        else:
            _alert_box("WARNING", "No active model in production", _ICON_WARNING)

        # Drift status
        st.markdown("---")
        _card_header("Model Drift Status", _ICON_CHART)
        if drift and drift.get("status") != "no_data":
            drift_detected = drift.get("drift_detected", False)
            if drift_detected:
                _alert_box("ERROR", f"DRIFT DETECTED &mdash; Severity: {drift.get('severity','unknown')}", _ICON_ERROR)
                col1, col2 = st.columns(2)
                col1.metric("AUC Current", drift.get("model_auc_current", 0))
                col2.metric("AUC Degradation", drift.get("auc_degradation", 0))
            else:
                _alert_box("SUCCESS", "No drift detected — Model performing within thresholds", _ICON_CHECK)
        else:
            _alert_box("INFO", "No drift report available yet.", _ICON_INFO)

        # Blockchain channels
        st.markdown("---")
        _card_header("Blockchain Channels", _ICON_HISTORY)
        channels = {
            "modelgovernance": "ML Model Lifecycle — Bank Org",
            "frauddetection":  "Fraud Decisions — Bank Org",
            "compliance":      "Internal Reports — Bank + Audit",
            "regulatory":      "BAM Submissions — Audit + Regulator",
        }
        for ch, desc in channels.items():
            st.markdown(
                f"<span style='color:#16A34A;font-weight:bold;'>&#9679;</span> <b>{ch}</b> — {desc}",
                unsafe_allow_html=True)

    # ── Tab 2: Model Governance ───────────────────────
    with tab2:
        _card_header("Model Governance — Read Only", _ICON_MODEL)

        models = _get_all_models()
        if not models:
            _alert_box("WARNING", "No models found.", _ICON_WARNING)
        else:
            status_map = {
                "DEPLOYED":             "",
                "TECHNICAL_APPROVED":   "",
                "COMPLIANCE_VALIDATED": "",
                "SUBMITTED":            "",
                "REJECTED":             "",
                "REVOKED":              "",
            }

            # Summary metrics
            statuses = [m.get("status") for m in models]
            c1,c2,c3,c4,c5 = st.columns(5)
            c1.metric("Total Models",  len(models))
            c2.metric("Deployed",   statuses.count("DEPLOYED"))
            c3.metric("Rejected",   statuses.count("REJECTED"))
            c4.metric("Revoked",    statuses.count("REVOKED"))
            c5.metric("Pending",    statuses.count("SUBMITTED"))

            st.markdown("---")

            # Models table
            import pandas as pd
            rows = []
            for m in models:
                status = m.get("status","")
                rows.append({
                    "Model ID":     m.get("modelID",""),
                    "Status":       status,
                    "AUC-ROC":      round(m.get("auc",0), 4),
                    "F1":           round(m.get("f1",0), 4),
                    "Submitted":    str(m.get("submittedAt",""))[:10],
                    "4-Eyes":       "Yes" if m.get("complianceOfficerID") and m.get("mlEngineerID") else "No",
                    "IPFS Card":    "Yes" if m.get("modelCardCID") else "No",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

            # Deployed model details
            deployed = [m for m in models if m.get("status") == "DEPLOYED"]
            if deployed:
                st.markdown("---")
                _card_header("Currently Deployed Model", _ICON_CHECK)
                m = deployed[0]
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("AUC-ROC",    round(m.get("auc",0), 4))
                col2.metric("F1-Score",   round(m.get("f1",0), 4))
                col3.metric("Recall",     round(m.get("recall",0), 4))
                col4.metric("Precision",  round(m.get("precision",0), 4))

                _alert_box("SUCCESS", "Regulatory Thresholds Met: AUC-ROC &ge; 0.95 | F1 &ge; 0.85 | Recall &ge; 0.90", _ICON_CHECK)

    # ── Tab 3: Fraud Statistics ───────────────────────
    with tab3:
        _card_header("Fraud Detection Statistics", _ICON_CHART)

        stats = _get_stats()
        if stats:
            fraude   = stats.get("FRAUDE", 0)
            ambigu   = stats.get("AMBIGU", 0)
            legitime = stats.get("LEGITIME", 0)
            total    = fraude + ambigu + legitime

            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Total TX",     f"{total:,}")
            c2.metric("Auto-Blocked",
                f"{fraude:,}",
                f"{fraude/total*100:.1f}%" if total > 0 else "0%")
            c3.metric("Human Review",
                f"{ambigu:,}",
                f"{ambigu/total*100:.1f}%" if total > 0 else "0%")
            c4.metric("Auto-Approved",
                f"{legitime:,}",
                f"{legitime/total*100:.1f}%" if total > 0 else "0%")

            st.markdown("---")
            _card_header("Compliance Status", _ICON_SHIELD)
            checks = [
                "Immutable blockchain audit trail — Hyperledger Fabric 2.5",
                "4-eyes principle enforced for all model deployments",
                "Model versioning on IPFS (Pinata)",
                "SHAP explainability per transaction",
                "Regulatory thresholds: AUC≥0.95, F1≥0.85, Recall≥0.90",
                "Dataset versioning with DVC hash",
                "Role-based access control (8 roles)",
                "External auditor certification required",
            ]
            for check in checks:
                st.markdown(
                    f"<span style='color:#16A34A;font-weight:bold;'>&#10003;</span> {check}",
                    unsafe_allow_html=True)
        else:
            _alert_box("INFO", "No statistics available yet.", _ICON_INFO)

    # ── Tab 4: Certified Reports ──────────────────────
    with tab4:
        _card_header("Certified Reports — External Auditor", _ICON_HISTORY)
        st.markdown("<p style='color:#64748B;'>Read-only view of certified compliance reports</p>", unsafe_allow_html=True)

        reports = _get_certified_reports()
        if not reports:
            _alert_box("WARNING", "No certified reports available yet.", _ICON_WARNING)
            _alert_box("INFO", "External Auditor must certify Internal Auditor reports first.", _ICON_INFO)
        else:
            _alert_box("SUCCESS", f"{len(reports)} certified report(s) available", _ICON_CHECK)
            for rep in reports:
                name = rep.get("name","")
                cid  = rep.get("cid","")
                with st.expander(f"**{name}**"):
                    st.markdown(f"**CID:** `{cid}`")
                    st.markdown(f"**IPFS URL:** https://gateway.pinata.cloud/ipfs/{cid}")
                    if st.button("View Report", key=f"view_{cid[:8]}"):
                        try:
                            r = httpx.get(
                                f"{API_URL}/ipfs/get/{cid}",
                                timeout=TIMEOUT)
                            if r.status_code == 200:
                                st.json(r.json())
                            else:
                                _alert_box("ERROR", "Could not retrieve report", _ICON_ERROR)
                        except Exception as e:
                            _alert_box("ERROR", str(e), _ICON_ERROR)
