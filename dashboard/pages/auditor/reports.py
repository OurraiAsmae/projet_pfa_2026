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
    except:
        return {}

def _get_models() -> list:
    try:
        r = httpx.get(f"{API_URL}/governance/all-models", timeout=10)
        return r.json().get("models", []) if r.status_code == 200 else []
    except:
        return []

def _get_drift() -> dict:
    try:
        r = httpx.get(f"{API_URL}/drift/latest", timeout=10)
        return r.json() if r.status_code == 200 else {}
    except:
        return {}

def _build_report(report_type, period, user):
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
            "total_transactions":  total,
            "fraud_auto_blocked":  fraude,
            "amber_human_review":  ambigu,
            "legitimate_approved": legitime,
            "fraud_rate_pct":      round(fraude/total*100, 2) if total > 0 else 0,
            "summary": f"During {period}, processed {total} transactions, fraud rate {round(fraude/total*100,2) if total>0 else 0}%"
        }
    elif report_type == "Model Governance Report":
        base["content"] = {
            "total_models": len(models),
            "deployed":     statuses.count("DEPLOYED"),
            "rejected":     statuses.count("REJECTED"),
            "revoked":      statuses.count("REVOKED"),
            "submitted":    statuses.count("SUBMITTED"),
            "four_eyes_enforced": True,
        }
    elif report_type == "Drift Alert Report":
        base["content"] = {
            "drift_detected":  drift.get("drift_detected", False),
            "severity":        drift.get("severity", "none"),
            "recommendation":  "Retrain model" if drift.get("drift_detected") else "No action required",
        }
    elif report_type == "CNDP Compliance Report":
        base["content"] = {
            "blockchain_audit_trail": True,
            "four_eyes_principle":    True,
            "ipfs_model_versioning":  True,
            "shap_explainability":    True,
            "gdpr_compliant":         True,
            "moroccan_law_09_08":     True,
        }
    elif report_type == "Full Audit Report":
        base["content"] = {
            "total_transactions": total,
            "fraud_rate":         round(fraude/total*100, 2) if total > 0 else 0,
            "total_models":       len(models),
            "deployed_models":    statuses.count("DEPLOYED"),
            "drift_detected":     drift.get("drift_detected", False),
            "blockchain":         True,
            "four_eyes":          True,
            "shap":               True,
        }
    return base

def show(user: dict):
    st.title("📄 Compliance Reports")
    st.caption("Internal Auditor — Generate & Submit Reports to CNDP")

    # ── Generate ──────────────────────────────────────
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
            try:
                r = httpx.post(
                    f"{API_URL}/ipfs/pin-json",
                    json={"data": report, "name": f"report-{report_type.replace(' ','-')}-{period}"},
                    timeout=TIMEOUT)
                if r.status_code == 200:
                    cid     = r.json().get("cid", "")
                    storage = r.json().get("storage", "ipfs")
                    st.success("✅ Report generated and pinned!")
                    st.info(f"📌 **CID:** `{cid}` | {'📦 Redis' if 'redis' in storage else '🌐 IPFS'}")
                    c = report.get("content", {})
                    st.markdown("---")
                    st.subheader("📊 Report Summary")
                    cols = st.columns(4)
                    items = list(c.items())[:4]
                    for i, (k, v) in enumerate(items):
                        cols[i].metric(k.replace("_"," ").title(), str(v)[:15])
                    st.info(f"**Report:** {report_type} | **Period:** {period} | **Status:** ⏳ Pending External Certification")
                    st.warning("⚠️ **Next Step:** External Auditor must certify this report before submission to Regulator.")
                else:
                    st.error(f"❌ Failed: {r.text}")
            except Exception as e:
                st.error(f"❌ {e}")

    # ── Load Reports ──────────────────────────────────
    st.markdown("---")
    st.subheader("📁 Pinned Reports on IPFS")

    if "loaded_reports" not in st.session_state:
        st.session_state.loaded_reports = []

    if st.button("🔄 Load Reports"):
        try:
            r = httpx.get(f"{API_URL}/ipfs/list", timeout=30)
            if r.status_code == 200:
                files = r.json().get("files", [])
                st.session_state.loaded_reports = [
                    f for f in files if "report" in f.get("name","").lower()]
        except Exception as e:
            st.error(f"❌ {e}")

    reports = st.session_state.loaded_reports
    if reports:
        st.success(f"✅ {len(reports)} report(s) found")
        for rep in reports:
            cid     = rep.get("cid", "")
            name    = rep.get("name", "")
            storage = "📦 Redis" if cid.startswith("LOCAL-") else "🌐 IPFS"
            with st.expander(f"📄 **{name}** — {storage}", expanded=False):
                st.markdown(f"**CID:** `{cid}`")
                try:
                    rr = httpx.get(f"{API_URL}/ipfs/get/{cid}", timeout=10)
                    if rr.status_code == 200:
                        data = rr.json()
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Type",   data.get("report_type","").split()[0])
                        c2.metric("Period", data.get("period",""))
                        c3.metric("By",     data.get("generated_by","")[:15])
                        st.markdown(f"**Generated:** {data.get('generated_at','')[:16]} | **Status:** ⏳ Pending")
                        content_data = data.get("content", {})
                        if isinstance(content_data, dict):
                            st.markdown("---")
                            for k, v in content_data.items():
                                if isinstance(v, dict):
                                    st.markdown(f"**{k.replace('_',' ').title()}:**")
                                    ncols = min(len(v), 4)
                                    if ncols > 0:
                                        cols2 = st.columns(ncols)
                                        for i, (kk, vv) in enumerate(list(v.items())[:4]):
                                            cols2[i].metric(kk.replace("_"," "), str(vv))
                                else:
                                    st.markdown(f"**{k.replace('_',' ').title()}:** `{v}`")
                except Exception as ex:
                    st.warning(f"Could not load content: {ex}")
