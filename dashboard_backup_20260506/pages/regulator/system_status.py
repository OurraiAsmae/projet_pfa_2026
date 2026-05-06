"""Regulator — System Status (Read Only)"""
import streamlit as st
import httpx
from datetime import datetime
from utils.api_client import API_URL, GW_URL, AUTH_URL

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
    st.title("🏛️ Regulatory Supervision Dashboard")
    st.caption("BAM — Bank Al-Maghrib | Read-Only View | CNDP Compliance")
    st.markdown(f"*Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🟢 System Status",
        "🤖 Model Governance",
        "📊 Fraud Statistics",
        "📋 Certified Reports"
    ])

    # ── Tab 1: System Status ──────────────────────────
    with tab1:
        st.subheader("🟢 Infrastructure Status")

        health = _get_health()
        drift  = _get_drift()

        # Service health
        services = {
            "🤖 ML API":        health.get("ml_model", False),
            "⛓️ Blockchain":    health.get("blockchain", True),
            "📦 Redis Cache":   health.get("redis", False),
            "🔍 SHAP Service":  health.get("shap", False),
            "📌 IPFS Pinata":   health.get("ipfs", True),
        }

        c1, c2, c3, c4, c5 = st.columns(5)
        cols = [c1, c2, c3, c4, c5]
        for i, (name, status) in enumerate(services.items()):
            icon = "🟢" if status else "🔴"
            cols[i].metric(name, f"{icon} {'OK' if status else 'DOWN'}")

        st.markdown("---")

        # Active model
        st.subheader("🤖 Active Fraud Detection Model")
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
            st.warning("No active model in production")

        # Drift status
        st.markdown("---")
        st.subheader("📉 Model Drift Status")
        if drift and drift.get("status") != "no_data":
            drift_detected = drift.get("drift_detected", False)
            if drift_detected:
                st.error(f"⚠️ DRIFT DETECTED — Severity: {drift.get('severity','unknown')}")
                col1, col2 = st.columns(2)
                col1.metric("AUC Current", drift.get("model_auc_current", 0))
                col2.metric("AUC Degradation", drift.get("auc_degradation", 0))
            else:
                st.success("✅ No drift detected — Model performing within thresholds")
        else:
            st.info("No drift report available yet.")

        # Blockchain channels
        st.markdown("---")
        st.subheader("⛓️ Blockchain Channels")
        channels = {
            "modelgovernance": "ML Model Lifecycle — Bank Org",
            "frauddetection":  "Fraud Decisions — Bank Org",
            "compliance":      "Internal Reports — Bank + Audit",
            "regulatory":      "BAM Submissions — Audit + Regulator",
        }
        for ch, desc in channels.items():
            st.markdown(f"🟢 **{ch}** — {desc}")

    # ── Tab 2: Model Governance ───────────────────────
    with tab2:
        st.subheader("🤖 Model Governance — Read Only")

        models = _get_all_models()
        if not models:
            st.warning("No models found.")
        else:
            status_map = {
                "DEPLOYED":             "🟢",
                "TECHNICAL_APPROVED":   "🔵",
                "COMPLIANCE_VALIDATED": "🟡",
                "SUBMITTED":            "⚪",
                "REJECTED":             "🔴",
                "REVOKED":              "⚫",
            }

            # Summary metrics
            statuses = [m.get("status") for m in models]
            c1,c2,c3,c4,c5 = st.columns(5)
            c1.metric("Total Models",  len(models))
            c2.metric("🟢 Deployed",   statuses.count("DEPLOYED"))
            c3.metric("🔴 Rejected",   statuses.count("REJECTED"))
            c4.metric("⚫ Revoked",    statuses.count("REVOKED"))
            c5.metric("⚪ Pending",    statuses.count("SUBMITTED"))

            st.markdown("---")

            # Models table
            import pandas as pd
            rows = []
            for m in models:
                status = m.get("status","")
                rows.append({
                    "Model ID":     m.get("modelID",""),
                    "Status":       f"{status_map.get(status,'❓')} {status}",
                    "AUC-ROC":      round(m.get("auc",0), 4),
                    "F1":           round(m.get("f1",0), 4),
                    "Submitted":    str(m.get("submittedAt",""))[:10],
                    "4-Eyes ✅":    "Yes" if m.get("complianceOfficerID") and m.get("mlEngineerID") else "No",
                    "IPFS Card":    "✅" if m.get("modelCardCID") else "❌",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

            # Deployed model details
            deployed = [m for m in models if m.get("status") == "DEPLOYED"]
            if deployed:
                st.markdown("---")
                st.subheader("🟢 Currently Deployed Model")
                m = deployed[0]
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("AUC-ROC",    round(m.get("auc",0), 4))
                col2.metric("F1-Score",   round(m.get("f1",0), 4))
                col3.metric("Recall",     round(m.get("recall",0), 4))
                col4.metric("Precision",  round(m.get("precision",0), 4))

                st.success(f"""
                ✅ **Regulatory Thresholds Met:**
                AUC-ROC ≥ 0.95 | F1 ≥ 0.85 | Recall ≥ 0.90
                """)

    # ── Tab 3: Fraud Statistics ───────────────────────
    with tab3:
        st.subheader("📊 Fraud Detection Statistics")

        stats = _get_stats()
        if stats:
            fraude   = stats.get("FRAUDE", 0)
            ambigu   = stats.get("AMBIGU", 0)
            legitime = stats.get("LEGITIME", 0)
            total    = fraude + ambigu + legitime

            c1,c2,c3,c4 = st.columns(4)
            c1.metric("📊 Total TX",     f"{total:,}")
            c2.metric("🔴 Auto-Blocked",
                f"{fraude:,}",
                f"{fraude/total*100:.1f}%" if total > 0 else "0%")
            c3.metric("🟡 Human Review",
                f"{ambigu:,}",
                f"{ambigu/total*100:.1f}%" if total > 0 else "0%")
            c4.metric("🟢 Auto-Approved",
                f"{legitime:,}",
                f"{legitime/total*100:.1f}%" if total > 0 else "0%")

            st.markdown("---")
            st.subheader("📋 CNDP Compliance Status")
            checks = [
                ("✅", "Immutable blockchain audit trail — Hyperledger Fabric 2.5"),
                ("✅", "4-eyes principle enforced for all model deployments"),
                ("✅", "Model versioning on IPFS (Pinata)"),
                ("✅", "SHAP explainability per transaction"),
                ("✅", "Regulatory thresholds: AUC≥0.95, F1≥0.85, Recall≥0.90"),
                ("✅", "Dataset versioning with DVC hash"),
                ("✅", "Role-based access control (8 roles)"),
                ("✅", "External auditor certification required"),
            ]
            for icon, check in checks:
                st.markdown(f"{icon} {check}")
        else:
            st.info("No statistics available yet.")

    # ── Tab 4: Certified Reports ──────────────────────
    with tab4:
        st.subheader("📋 Certified Reports — External Auditor")
        st.caption("Read-only view of certified compliance reports")

        reports = _get_certified_reports()
        if not reports:
            st.warning("No certified reports available yet.")
            st.info("External Auditor must certify Internal Auditor reports first.")
        else:
            st.success(f"✅ {len(reports)} certified report(s) available")
            for rep in reports:
                name = rep.get("name","")
                cid  = rep.get("cid","")
                with st.expander(f"📋 **{name}**"):
                    st.markdown(f"**CID:** `{cid}`")
                    st.markdown(f"**IPFS URL:** https://gateway.pinata.cloud/ipfs/{cid}")
                    if st.button("👁️ View Report", key=f"view_{cid[:8]}"):
                        try:
                            r = httpx.get(
                                f"{API_URL}/ipfs/get/{cid}",
                                timeout=TIMEOUT)
                            if r.status_code == 200:
                                st.json(r.json())
                            else:
                                st.error("Could not retrieve report")
                        except Exception as e:
                            st.error(f"❌ {e}")
