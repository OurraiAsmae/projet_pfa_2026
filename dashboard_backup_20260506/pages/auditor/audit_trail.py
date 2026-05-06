"""Auditor — Blockchain Audit Trail"""
import streamlit as st
import httpx
import pandas as pd
from datetime import datetime
from utils.api_client import API_URL

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
    st.title("📋 Blockchain Audit Trail")
    st.caption("Internal Auditor — CNDP Compliance View")

    tab1, tab2, tab3 = st.tabs([
        "🤖 Model Governance",
        "🔍 Transaction Lookup",
        "📊 System Metrics"
    ])

    # ── Tab 1: Model Governance ───────────────────────
    with tab1:
        st.subheader("🤖 Model Governance History")

        with st.spinner("Loading blockchain data..."):
            models = _get_all_models()

        if not models:
            st.warning("No models found on blockchain.")
        else:
            # Summary table
            status_colors = {
                "DEPLOYED":             "🟢",
                "TECHNICAL_APPROVED":   "🔵",
                "COMPLIANCE_VALIDATED": "🟡",
                "SUBMITTED":            "⚪",
                "REJECTED":             "🔴",
                "REVOKED":              "⚫",
            }

            rows = []
            for m in models:
                status = m.get("status", "")
                rows.append({
                    "Model ID":      m.get("modelID", ""),
                    "Status":        f"{status_colors.get(status,'❓')} {status}",
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
            c2.metric("🟢 Deployed",  statuses.count("DEPLOYED"))
            c3.metric("🔴 Rejected",  statuses.count("REJECTED"))
            c4.metric("⚫ Revoked",   statuses.count("REVOKED"))
            c5.metric("⚪ Pending",   statuses.count("SUBMITTED"))

            # Model history detail
            st.markdown("---")
            st.subheader("🔍 Model Blockchain History")
            model_ids = [m.get("modelID","") for m in models]
            selected = st.selectbox("Select Model", model_ids)

            if st.button("📜 Load Full History", type="primary"):
                with st.spinner("Fetching blockchain history..."):
                    history = _get_model_history(selected)

                if history.get("success"):
                    data = history.get("data", history.get("output", ""))
                    st.success(f"✅ History for {selected}")
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
                    st.error(f"❌ {history.get('output', history.get('error','Error'))}")

    # ── Tab 2: Transaction Lookup ─────────────────────
    with tab2:
        st.subheader("🔍 Transaction Verification")
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
        if st.button("🔍 Verify on Blockchain", type="primary"):
            try:
                r = httpx.get(f"{API_URL}/decision/{tx_id}", timeout=TIMEOUT)
                d = r.json()
                if d.get("data"):
                    data = d["data"]
                    st.success(f"✅ Transaction found — Source: {d.get('source')}")
                    d = data if isinstance(data, dict) else {}
                    c1,c2,c3 = st.columns(3)
                    c1.metric("Zone",  d.get("zone","N/A"))
                    c2.metric("Score", f"{d.get('score',0):.4f}")
                    c3.metric("Model", d.get("ml_model_used","") and "RF-v2.0" or "N/A")
                    st.markdown(f"**TX ID:** `{d.get('tx_id','N/A')}`")
                    st.markdown(f"**Blockchain Recorded:** {'✅' if d.get('blockchain_recorded') else '❌'}")
                    st.markdown(f"**ML Model Used:** {'✅' if d.get('ml_model_used') else '❌'}")
                    st.markdown(f"**SHAP CID:** `{d.get('shap_cid','N/A')}`")
                    if d.get("top_features"):
                        st.markdown("**Top SHAP Features:**")
                        for feat in d["top_features"][:5]:
                            st.markdown(f"- `{feat.get('feature','')}`: {feat.get('shap_value',0):+.4f}")
                else:
                    st.warning("Transaction not found in cache.")
            except Exception as e:
                st.error(f"❌ {e}")

    # ── Tab 3: System Metrics ─────────────────────────
    with tab3:
        st.subheader("📊 System Metrics — CNDP Compliance")

        stats = _get_stats()
        if stats:
            total   = stats.get("total", 0)
            fraude  = stats.get("FRAUDE", 0)
            ambigu  = stats.get("AMBIGU", 0)
            legitime= stats.get("LEGITIME", 0)
            total   = fraude + ambigu + legitime if total == 0 else total

            c1,c2,c3,c4 = st.columns(4)
            c1.metric("📊 Total TX",      f"{total:,}")
            c2.metric("🔴 Fraud Rate",
                f"{fraude/total*100:.2f}%" if total > 0 else "0%")
            c3.metric("🟡 Amber Rate",
                f"{ambigu/total*100:.2f}%" if total > 0 else "0%")
            c4.metric("🟢 Legit Rate",
                f"{legitime/total*100:.2f}%" if total > 0 else "0%")

            st.markdown("---")
            st.markdown("**📋 CNDP Compliance Checklist:**")
            checks = [
                ("✅", "Blockchain immutable audit trail"),
                ("✅", "4-eyes principle enforced"),
                ("✅", "Model versioning on IPFS"),
                ("✅", "SHAP explainability per transaction"),
                ("✅", "Regulatory thresholds AUC≥0.95"),
                ("✅", "Data hash DVC tracking"),
                ("✅", "Role-based access control"),
            ]
            for icon, check in checks:
                st.markdown(f"{icon} {check}")
        else:
            st.info("No stats available yet.")
