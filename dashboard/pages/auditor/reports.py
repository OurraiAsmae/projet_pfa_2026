"""Auditor — Compliance Reports Generator"""
import streamlit as st
import httpx
import json
from datetime import datetime
from utils.api_client import API_URL

TIMEOUT = 15

def _generate_report(report_type: str, period: str) -> dict:
    """Generate and pin report to IPFS"""
    try:
        r = httpx.post(
            f"{API_URL}/ipfs/pin-json",
            json={
                "content": {
                    "report_type":   report_type,
                    "period":        period,
                    "generated_at":  datetime.utcnow().isoformat(),
                    "generated_by":  "Internal Auditor",
                    "status":        "PENDING_EXTERNAL_CERTIFICATION",
                },
                "name": f"report-{report_type}-{period}"
            },
            timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def _get_drift() -> dict:
    try:
        r = httpx.get(f"{API_URL}/drift/latest", timeout=TIMEOUT)
        return r.json()
    except:
        return {}

def _get_stats() -> dict:
    try:
        r = httpx.get(f"{API_URL}/stats", timeout=TIMEOUT)
        return r.json()
    except:
        return {}

def _get_all_models() -> list:
    try:
        r = httpx.get(f"{API_URL}/governance/all-models", timeout=TIMEOUT)
        return r.json().get("models", [])
    except:
        return []

def show(user: dict):
    st.title("📄 Compliance Reports")
    st.caption("Internal Auditor — Generate & Submit Reports to CNDP")

    # ── Report Generator ──────────────────────────────
    st.subheader("📋 Generate New Report")

    col1, col2 = st.columns(2)
    with col1:
        report_type = st.selectbox(
            "Report Type",
            ["Monthly Activity Report",
             "Model Governance Report",
             "Drift Alert Report",
             "CNDP Compliance Report",
             "Full Audit Report"])
    with col2:
        period = st.text_input(
            "Period",
            datetime.utcnow().strftime("%Y-%m"))

    if st.button("📄 Generate & Pin to IPFS",
                 type="primary",
                 use_container_width=True):

        with st.spinner("Generating report..."):
            # Collect data
            stats  = _get_stats()
            models = _get_all_models()
            drift  = _get_drift()

            total    = stats.get("total", 0)
            fraude   = stats.get("FRAUDE", 0)
            ambigu   = stats.get("AMBIGU", 0)
            legitime = stats.get("LEGITIME", 0)
            total    = fraude + ambigu + legitime if total == 0 else total

            statuses = [m.get("status") for m in models]

            report = {
                "report_type":    report_type,
                "period":         period,
                "generated_at":   datetime.utcnow().isoformat(),
                "generated_by":   user.get("username", "auditor"),
                "status":         "PENDING_EXTERNAL_CERTIFICATION",
                "transaction_stats": {
                    "total":    total,
                    "fraud":    fraude,
                    "amber":    ambigu,
                    "legit":    legitime,
                    "fraud_rate": round(fraude/total*100, 2) if total > 0 else 0,
                },
                "model_governance": {
                    "total_models":  len(models),
                    "deployed":      statuses.count("DEPLOYED"),
                    "rejected":      statuses.count("REJECTED"),
                    "revoked":       statuses.count("REVOKED"),
                    "submitted":     statuses.count("SUBMITTED"),
                },
                "drift_status": {
                    "drift_detected": drift.get("drift_detected", False),
                    "severity":       drift.get("severity", "unknown"),
                    "auc_current":    drift.get("model_auc_current", 0),
                },
                "cndp_compliance": {
                    "blockchain_audit": True,
                    "four_eyes":        True,
                    "ipfs_versioning":  True,
                    "shap_explainability": True,
                    "regulatory_thresholds": True,
                },
            }

            # Pin to IPFS
            r = httpx.post(
                f"{API_URL}/ipfs/pin-json",
                json={
                    "data": report,
                    "name": f"report-{report_type.replace(' ','-')}-{period}"
                },
                timeout=30)

            if r.status_code == 200:
                cid = r.json().get("cid", "")
                st.success(f"✅ Report generated and pinned to IPFS!")
                st.code(f"CID: {cid}")

                # Display report summary
                st.markdown("---")
                st.subheader("📊 Report Summary")

                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Total TX",   f"{total:,}")
                c2.metric("Fraud Rate", f"{round(fraude/total*100,2) if total>0 else 0}%")
                c3.metric("Models",     len(models))
                c4.metric("Deployed",   statuses.count("DEPLOYED"))

                st.info(f"""
                **Report:** {report_type}
                **Period:** {period}
                **IPFS CID:** `{cid}`
                **Status:** ⏳ Pending External Auditor Certification
                **Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
                """)

                st.warning("""
                ⚠️ **Next Step:** External Auditor must verify and 
                certify this report with cryptographic signature 
                before submission to Regulator.
                """)
            else:
                st.error(f"❌ Failed to pin report: {r.text[:100]}")

    # ── Pinned Reports List ───────────────────────────
    st.markdown("---")
    st.subheader("📁 Pinned Reports on IPFS")

    if st.button("🔄 Load Reports"):
        try:
            r = httpx.get(f"{API_URL}/ipfs/list", timeout=TIMEOUT)
            if r.status_code == 200:
                files = r.json().get("files", [])
                reports = [f for f in files 
                          if "report" in f.get("name","").lower()
                          or "certified" in f.get("name","").lower()]
                if reports:
                    for rep in reports:
                        cid  = rep.get("cid","")
                        name = rep.get("name","")
                        is_local = cid.startswith("LOCAL-")
                        storage  = "📦 Redis" if is_local else "📌 IPFS"
                        st.markdown(f"""
                        📄 **{name}**
                        — {storage} CID: `{cid[:30]}...`
                        """)
                else:
                    st.info("No reports pinned yet.")
        except Exception as e:
            st.error(f"❌ {e}")
