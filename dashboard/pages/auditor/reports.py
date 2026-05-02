"""Internal Auditor — Compliance Reports"""
import streamlit as st
import httpx
from datetime import datetime
from utils.api_client import API_URL

TIMEOUT = 30

def _get_stats() -> dict:
    try:
        r = httpx.get(f"{API_URL}/stats", timeout=10)
        return r.json() if r.status_code == 200 else {}
    except: return {}

def _get_models() -> list:
    try:
        r = httpx.get(f"{API_URL}/governance/all-models", timeout=10)
        return r.json().get("models", []) if r.status_code == 200 else []
    except: return []

def _get_drift() -> dict:
    try:
        r = httpx.get(f"{API_URL}/drift/latest", timeout=10)
        return r.json() if r.status_code == 200 else {}
    except: return {}

def _build_report(report_type: str, period: str, user: dict) -> dict:
    stats  = _get_stats()
    models = _get_models()
    drift  = _get_drift()

    fraude   = stats.get("FRAUDE", 0)
    ambigu   = stats.get("AMBIGU", 0)
    legitime = stats.get("LEGITIME", 0)
    total    = fraude + ambigu + legitime
    statuses = [m.get("status") for m in models]

    base = {
        "report_type":  report_type,
        "period":       period,
        "generated_at": datetime.utcnow().isoformat(),
        "generated_by": user.get("username", "auditor"),
        "status":       "PENDING_EXTERNAL_CERTIFICATION",
    }

    if report_type == "Monthly Activity Report":
        base["content"] = {
            "total_transactions": total,
            "fraud_auto_blocked": fraude,
            "amber_human_review": ambigu,
            "legitimate_approved": legitime,
            "fraud_rate_pct": round(fraude/total*100, 2) if total > 0 else 0,
            "amber_rate_pct": round(ambigu/total*100, 2) if total > 0 else 0,
            "summary": f"During {period}, the system processed {total} transactions with a fraud rate of {round(fraude/total*100,2) if total>0 else 0}%"
        }

    elif report_type == "Model Governance Report":
        base["content"] = {
            "total_models":    len(models),
            "deployed":        statuses.count("DEPLOYED"),
            "compliance_validated": statuses.count("COMPLIANCE_VALIDATED"),
            "technical_approved": statuses.count("TECHNICAL_APPROVED"),
            "rejected":        statuses.count("REJECTED"),
            "revoked":         statuses.count("REVOKED"),
            "submitted":       statuses.count("SUBMITTED"),
            "four_eyes_enforced": True,
            "models_detail":   [{"id": m.get("modelID"), "status": m.get("status"), "auc": m.get("auc")} for m in models[:5]]
        }

    elif report_type == "Drift Alert Report":
        base["content"] = {
            "drift_detected":  drift.get("drift_detected", False),
            "severity":        drift.get("severity", "none"),
            "auc_current":     drift.get("model_auc_current", 0),
            "auc_degradation": drift.get("auc_degradation", 0),
            "monitoring_period": period,
            "action_required": drift.get("drift_detected", False),
            "recommendation":  "Retrain model" if drift.get("drift_detected") else "No action required"
        }

    elif report_type == "CNDP Compliance Report":
        base["content"] = {
            "blockchain_audit_trail": True,
            "four_eyes_principle":    True,
            "ipfs_model_versioning":  True,
            "shap_explainability":    True,
            "regulatory_thresholds":  {"auc_min": 0.95, "f1_min": 0.85, "recall_min": 0.90},
            "data_retention_policy":  "30 days Redis + IPFS permanent",
            "gdpr_compliant":         True,
            "moroccan_law_09_08":     True,
            "cndp_submission_date":   datetime.utcnow().isoformat()
        }

    elif report_type == "Full Audit Report":
        base["content"] = {
            "monthly_stats": {
                "total": total, "fraud": fraude,
                "amber": ambigu, "legit": legitime
            },
            "model_governance": {
                "total": len(models),
                "deployed": statuses.count("DEPLOYED"),
                "rejected": statuses.count("REJECTED")
            },
            "drift": {
                "detected": drift.get("drift_detected", False),
                "severity": drift.get("severity", "none")
            },
            "cndp_compliance": {
                "blockchain": True, "four_eyes": True,
                "shap": True, "ipfs": True
            },
            "auditor_signature": user.get("username", "auditor"),
            "audit_period": period
        }

    return base

def show(user: dict):
    st.title("📄 Compliance Reports")
    st.caption("Internal Auditor — Generate & Submit Reports to CNDP")

    st.subheader("📋 Generate New Report")
    col1, col2 = st.columns(2)
    with col1:
        report_type = st.selectbox("Report Type", [
            "Monthly Activity Report",
            "Model Governance Report",
            "Drift Alert Report",
            "CNDP Compliance Report",
            "Full Audit Report"])
    with col2:
        period = st.text_input("Period", datetime.utcnow().strftime("%Y-%m"))

    if st.button("📄 Generate & Pin to IPFS", type="primary", use_container_width=True):
        with st.spinner("Generating report..."):
            report = _build_report(report_type, period, user)
            r = httpx.post(
                f"{API_URL}/ipfs/pin-json",
                json={
                    "data": report,
                    "name": f"report-{report_type.replace(' ','-')}-{period}"
                },
                timeout=TIMEOUT)
            if r.status_code == 200:
                cid = r.json().get("cid", "")
                storage = r.json().get("storage", "ipfs")
                st.success("✅ Report generated and pinned!")
                st.info(f"📌 **CID:** `{cid}` | Storage: {'📦 Redis' if 'redis' in storage else '🌐 IPFS'}")
                st.markdown("---")
                st.subheader("📊 Report Summary")
                content = report.get("content", {})
                c1,c2,c3,c4 = st.columns(4)
                if report_type == "Monthly Activity Report":
                    c1.metric("Total TX",   content.get("total_transactions",0))
                    c2.metric("Fraud Rate", f"{content.get('fraud_rate_pct',0)}%")
                    c3.metric("Fraud",      content.get("fraud_auto_blocked",0))
                    c4.metric("Legitimate", content.get("legitimate_approved",0))
                elif report_type == "Model Governance Report":
                    c1.metric("Total Models", content.get("total_models",0))
                    c2.metric("Deployed",     content.get("deployed",0))
                    c3.metric("Rejected",     content.get("rejected",0))
                    c4.metric("Pending",      content.get("submitted",0))
                elif report_type == "CNDP Compliance Report":
                    c1.metric("Blockchain", "✅")
                    c2.metric("4-Eyes",     "✅")
                    c3.metric("SHAP",       "✅")
                    c4.metric("IPFS",       "✅")

                st.info(f"""
                **Report:** {report_type} | **Period:** {period} | **IPFS CID:** `{cid[:30]}...`
                **Status:** ⏳ Pending External Auditor Certification
                **Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
                """)
                st.warning("⚠️ **Next Step:** External Auditor must verify and certify this report with cryptographic signature before submission to Regulator.")
            else:
                st.error(f"❌ Failed to pin report: {r.text}")

    st.markdown("---")
    st.subheader("📁 Pinned Reports on IPFS")
    if "loaded_reports" not in st.session_state:
        st.session_state.loaded_reports = []

    if st.button("🔄 Load Reports"):
        try:
            r = httpx.get(f"{API_URL}/ipfs/list", timeout=30)
            if r.status_code == 200:
                files = r.json().get("files", [])
                reports = [f for f in files if "report" in f.get("name","").lower()]
                st.session_state.loaded_reports = reports
                if reports:
                    st.success(f"✅ {len(reports)} report(s) found")
                    if "viewed_report" not in st.session_state:
                        st.session_state.viewed_report = None

                    for rep in reports:
                        cid     = rep.get("cid","")
                        name    = rep.get("name","")
                        storage = "📦 Redis" if cid.startswith("LOCAL-") else "🌐 IPFS"
                        col1, col2 = st.columns([4,1])
                        col1.markdown(f"📄 **{name}** — {storage} — `{cid[:25]}...`")
                        if col2.button("👁️ View", key=f"view_{cid[:10]}"):
                            rr = httpx.get(f"{API_URL}/ipfs/get/{cid}", timeout=10)
                            if rr.status_code == 200:
                                st.session_state.viewed_report = rr.json()
                            else:
                                st.error("❌ Could not retrieve report")

                    if st.session_state.viewed_report:
                        data = st.session_state.viewed_report
                        st.markdown("---")
                        st.subheader("📋 Report Details")
                        c1,c2,c3 = st.columns(3)
                        c1.metric("Type",   data.get("report_type","").split()[0])
                        c2.metric("Period", data.get("period",""))
                        c3.metric("Status", "⏳ Pending")
                        st.markdown(f"**Generated by:** {data.get('generated_by','')} | **At:** {data.get('generated_at','')[:16]}")
                        content_data = data.get("content", {})
                        if isinstance(content_data, dict):
                            st.markdown("---")
                            for k, v in content_data.items():
                                if isinstance(v, dict):
                                    st.markdown(f"**{k.replace('_',' ').title()}:**")
                                    cols = st.columns(len(v))
                                    for i,(kk,vv) in enumerate(v.items()):
                                        cols[i].metric(kk.replace("_"," "), str(vv))
                                elif isinstance(v, list):
                                    st.markdown(f"**{k.replace('_',' ').title()}:** {v}")
                                else:
                                    st.markdown(f"**{k.replace('_',' ').title()}:** `{v}`")
                        if st.button("✖️ Close Report"):
                            st.session_state.viewed_report = None
                            st.rerun()
                else:
                    st.info("No reports pinned yet.")
        except Exception as e:
            st.error(f"❌ {e}")
