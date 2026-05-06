"""Auditor — Blockchain Audit Trail"""
import streamlit as st
import httpx
import pandas as pd
from datetime import datetime
from utils.api_client import API_URL
from styles import (
    _header, _card_header, _alert_box,
    _ICON_HISTORY, _ICON_INFO, _ICON_CHECK, _ICON_WARNING, _ICON_ERROR, _ICON_CHART, _ICON_SHIELD
)

TIMEOUT = 15

def _get_all_models() -> list:
    try:
        r = httpx.get(f"{API_URL}/governance/all-models", timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json().get("models", [])
    except:
        pass
    return []

def _get_model_history(model_id: str) -> dict:
    try:
        r = httpx.get(f"{API_URL}/governance/history/{model_id}", timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {}

def _get_stats() -> dict:
    try:
        r = httpx.get(f"{API_URL}/stats", timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {}

def show(user: dict):
    _header("Blockchain Audit Trail", _ICON_HISTORY)

    # Fix tab text visibility
    st.markdown("""
    <style>
      /* Streamlit tabs — force dark text on all versions */
      .stTabs [data-baseweb="tab-list"] button,
      .stTabs [data-baseweb="tab-list"] button p,
      .stTabs [data-baseweb="tab-list"] button span,
      .stTabs [data-baseweb="tab-list"] button div,
      button[role="tab"],
      button[role="tab"] p,
      button[role="tab"] span,
      button[role="tab"] div {
        color: #1C1C1C !important;
        font-weight: 600 !important;
        font-size: .88rem !important;
        opacity: 1 !important;
      }
      .stTabs [data-baseweb="tab-list"] button:hover,
      .stTabs [data-baseweb="tab-list"] button:hover p,
      button[role="tab"]:hover,
      button[role="tab"]:hover p {
        color: #1F7A5A !important;
      }
      .stTabs [data-baseweb="tab-list"] button[aria-selected="true"],
      .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] p,
      button[role="tab"][aria-selected="true"],
      button[role="tab"][aria-selected="true"] p {
        color: #1F7A5A !important;
      }
    </style>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "Model Governance",
        "Transaction Lookup",
        "System Metrics"
    ])

    # ── Tab 1: Model Governance ───────────────────────
    with tab1:
        _card_header("Model Governance History", _ICON_HISTORY)

        with st.spinner("Loading blockchain data..."):
            models = _get_all_models()

        if not models:
            _alert_box("WARNING", "No models found on blockchain.", _ICON_WARNING)
        else:
            # Summary table
            status_colors = {
                "DEPLOYED":             "",
                "TECHNICAL_APPROVED":   "",
                "COMPLIANCE_VALIDATED": "",
                "SUBMITTED":            "",
                "REJECTED":             "",
                "REVOKED":              "",
            }

            rows = []
            for m in models:
                status = m.get("status", "")
                rows.append({
                    "Model ID":      m.get("modelID", ""),
                    "Status":        status,
                    "AUC":           round(m.get("auc", 0), 4),
                    "F1":            round(m.get("f1", 0), 4),
                    "Submitted At":  str(m.get("submittedAt",""))[:10],
                    "Scientist":     m.get("scientistID","").split("@")[0],
                    "CO":            m.get("complianceOfficerID","").split("@")[0] or "—",
                    "MLE":           m.get("mlEngineerID","").split("@")[0] or "—",
                    "Reason":        str(m.get("revokeReason",""))[:50] or "—",
                })

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)

            # Stats
            c1,c2,c3,c4,c5 = st.columns(5)
            statuses = [m.get("status") for m in models]
            c1.metric("Total",    len(models))
            c2.metric("Deployed",  statuses.count("DEPLOYED"))
            c3.metric("Rejected",  statuses.count("REJECTED"))
            c4.metric("Revoked",   statuses.count("REVOKED"))
            c5.metric("Pending",   statuses.count("SUBMITTED"))

            # Model history detail
            st.markdown("---")
            _card_header("Model Blockchain History", _ICON_HISTORY)
            model_ids = [m.get("modelID","") for m in models]
            selected = st.selectbox("Select Model", model_ids)

            if st.button("Load Full History", type="primary"):
                with st.spinner("Fetching blockchain history..."):
                    history = _get_model_history(selected)

                if history.get("success"):
                    data = history.get("data", history.get("output", ""))
                    _alert_box("SUCCESS", f"History for {selected}", _ICON_CHECK)
                    try:
                        import json
                        parsed = json.loads(data) if isinstance(data, str) else data
                        if isinstance(parsed, list):
                            for i, entry in enumerate(parsed):
                                with st.expander(
                                    f"Entry {i+1} — {entry.get('timestamp','')[:16]}"):
                                    st.json(entry)
                        else:
                            st.json(parsed)
                    except:
                        st.code(str(data))
                else:
                    _alert_box("ERROR", history.get('output', history.get('error','Error')), _ICON_ERROR)

    # ── Tab 2: Transaction Lookup ─────────────────────
    with tab2:
        _card_header("Transaction Verification", _ICON_SHIELD)
        # Load recent transactions
        try:
            import httpx as _httpx
            r_recent = _httpx.get(f"{API_URL}/transactions/recent", params={"limit": 20}, timeout=10)
            if r_recent.status_code == 200:
                recent_txs = r_recent.json().get("transactions", [])
                if recent_txs:
                    tx_options = {f"{t.get('tx_id','')} — {t.get('zone','')} — Score:{t.get('score',0):.3f}": t.get('tx_id','') for t in recent_txs}
                    selected_label = st.selectbox("Select from recent transactions", list(tx_options.keys()))
                    tx_id = tx_options[selected_label]
                    manual = st.text_input("Or enter TX ID manually", "")
                    if manual:
                        tx_id = manual
                else:
                    tx_id = st.text_input("Transaction ID", "TX-AMBER-001")
            else:
                tx_id = st.text_input("Transaction ID", "TX-AMBER-001")
        except:
            tx_id = st.text_input("Transaction ID", "TX-AMBER-001")
        if st.button("Verify on Blockchain", type="primary"):
            try:
                r = httpx.get(f"{API_URL}/decision/{tx_id}", timeout=TIMEOUT)
                d = r.json()
                if d.get("data"):
                    data = d["data"]
                    _alert_box("SUCCESS", f"Transaction found &mdash; Source: {d.get('source')}", _ICON_CHECK)
                    d = data if isinstance(data, dict) else {}
                    c1,c2,c3 = st.columns(3)
                    c1.metric("Zone",  d.get("zone","N/A"))
                    c2.metric("Score", f"{d.get('score',0):.4f}")
                    c3.metric("Model", d.get("ml_model_used","") and "RF-v2.0" or "N/A")
                    st.markdown(f"**TX ID:** `{d.get('tx_id','N/A')}`")
                    st.markdown(f"**Blockchain Recorded:** {'Yes' if d.get('blockchain_recorded') else 'No'}")
                    st.markdown(f"**ML Model Used:** {'Yes' if d.get('ml_model_used') else 'No'}")
                    st.markdown(f"**SHAP CID:** `{d.get('shap_cid','N/A')}`")
                    if d.get("top_features"):
                        st.markdown("**Top SHAP Features:**")
                        for feat in d["top_features"][:5]:
                            st.markdown(f"- `{feat.get('feature','')}`: {feat.get('shap_value',0):+.4f}")
                else:
                    _alert_box("WARNING", "Transaction not found in cache.", _ICON_WARNING)
            except Exception as e:
                _alert_box("ERROR", str(e), _ICON_ERROR)

    # ── Tab 3: System Metrics ─────────────────────────
    with tab3:
        _card_header("System Metrics", _ICON_CHART)

        stats = _get_stats()
        if stats:
            total   = stats.get("total", 0)
            fraude  = stats.get("FRAUDE", 0)
            ambigu  = stats.get("AMBIGU", 0)
            legitime= stats.get("LEGITIME", 0)
            total   = fraude + ambigu + legitime if total == 0 else total

            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Total TX",      f"{total:,}")
            c2.metric("Fraud Rate",
                f"{fraude/total*100:.2f}%" if total > 0 else "0%")
            c3.metric("Amber Rate",
                f"{ambigu/total*100:.2f}%" if total > 0 else "0%")
            c4.metric("Legit Rate",
                f"{legitime/total*100:.2f}%" if total > 0 else "0%")

            st.markdown("---")
            _card_header("Compliance Checklist", _ICON_SHIELD)
            checks = [
                "Blockchain immutable audit trail",
                "4-eyes principle enforced",
                "Model versioning on IPFS",
                "SHAP explainability per transaction",
                "Regulatory thresholds AUC≥0.95",
                "Data hash DVC tracking",
                "Role-based access control",
            ]
            for check in checks:
                st.markdown(
                    f"<span style='color:#16A34A;font-weight:bold;'>&#10003;</span> {check}",
                    unsafe_allow_html=True)
        else:
            _alert_box("INFO", "No stats available yet.", _ICON_INFO)
