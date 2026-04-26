"""
Compliance Officer — Compliance Validation v3.0
FIRST validator in the pipeline:
SUBMITTED → ValidateCompliance() → COMPLIANCE_VALIDATED
Then ML Engineer approves technically
"""
import streamlit as st
import httpx
import time
from datetime import datetime
from utils.api_client import (
    validate_compliance, revoke_model,
    API_URL
)
from utils.model_registry import get_mlflow_bc_mapping

REJECT_CATEGORIES = [
    "AUC-ROC below threshold (< 0.95)",
    "F1-Score below threshold (< 0.85)",
    "Recall below threshold (< 0.90)",
    "Dataset too old (> 12 months)",
    "Biased dataset — non-representative data",
    "Sensitive features used (age, nationality...)",
    "Fraud rate abnormal in dataset (< 0.1% or > 20%)",
    "Model Card incomplete — missing documentation",
    "Training period insufficient",
    "Violation of EU AI Act regulations",
    "Violation of BAM Morocco requirements",
    "Violation of SR 11-7 model risk guidelines",
    "Other regulatory issue"
]

def show(user: dict):
    st.title("✅ Compliance Validation")
    st.markdown("""
    <div style="background:#EFF6FF;
                border-left:4px solid #003366;
                border-radius:8px;
                padding:1rem;margin-bottom:1rem;">
        <b>Compliance Officer is the FIRST validator</b><br/>
        1️⃣ You validate regulatory compliance (here)<br/>
        2️⃣ ML Engineer approves technically<br/>
        3️⃣ ML Engineer deploys to production<br/><br/>
        <b>Regulations:</b>
        EU AI Act | SR 11-7 | Basel III | BAM Morocco
    </div>
    """, unsafe_allow_html=True)

    st.warning(
        "Thresholds (BAM): "
        "AUC-ROC ≥ 0.95 | F1 ≥ 0.85 | Recall ≥ 0.90")

    # Get all models with blockchain status
    with st.spinner("Loading models..."):
        mapping = get_mlflow_bc_mapping()

    if not mapping:
        st.info("No models registered in MLflow.")
        return

    # Separate by status
    pending  = {k:v for k,v in mapping.items()
                if v["bc_status"] == "SUBMITTED"}
    others   = {k:v for k,v in mapping.items()
                if v["bc_status"] != "SUBMITTED"
                and v["on_chain"]}
    no_chain = {k:v for k,v in mapping.items()
                if not v["on_chain"]}

    # ── PENDING ──────────────────────────────────
    if pending:
        st.subheader(
            f"⏳ Pending Compliance Review "
            f"({len(pending)})")
        for name, info in pending.items():
            _render_card(name, info, user, "pending")
    else:
        st.success(
            "✅ No models pending compliance review")

    # ── ALREADY PROCESSED ────────────────────────
    if others:
        st.subheader(
            f"📋 Already Processed ({len(others)})")
        for name, info in others.items():
            with st.expander(
                f"{_status_icon(info['bc_status'])} "
                f"**{name}** — {info['bc_status']}"):
                c1,c2,c3 = st.columns(3)
                c1.metric("AUC-ROC",
                    f"{info['auc_roc']:.4f}")
                c2.metric("Status",
                    info["bc_status"])
                c3.metric("BC ID",
                    info["bc_id"][:20]+"...")

    # ── NOT ON BLOCKCHAIN ─────────────────────────
    if no_chain:
        with st.expander(
            f"⚠️ Not on Blockchain ({len(no_chain)})"
            " — Need to be submitted first"):
            for name, info in no_chain.items():
                st.markdown(
                    f"❓ **{name}** — "
                    f"run_name: `{info['run_name']}` "
                    f"— Not found on blockchain")
            st.info(
                "These models were registered in MLflow "
                "but not submitted to blockchain. "
                "Ask Data Scientist to re-submit.")


def _render_card(name: str, info: dict,
                  user: dict, mode: str):
    """Render compliance validation card"""
    auc  = info["auc_roc"]
    f1   = info["f1"]
    rec  = info["recall"]
    prec = info["precision"]
    ok   = auc>=0.95 and f1>=0.85 and rec>=0.90

    with st.expander(
        f"{'✅' if ok else '❌'} **{name}** "
        f"— {info['model_type']} "
        f"— {info['bc_id']}",
        expanded=True):

        # Metrics card
        st.markdown(f"""
        <div style="background:white;
                    border:1px solid #E2E8F0;
                    border-radius:10px;padding:1rem;
                    border-top:3px solid
                    {'#16A34A' if ok else '#DC2626'};">
          <div style="display:grid;
              grid-template-columns:repeat(4,1fr);
              gap:1rem;margin-bottom:.8rem;">
            <div>
              <div style="font-size:.7rem;color:#64748B;
                  font-weight:600;
                  text-transform:uppercase;">AUC-ROC</div>
              <div style="font-size:1.4rem;font-weight:700;
                  color:{'#16A34A' if auc>=0.95 else '#DC2626'};">
                  {auc:.4f}</div>
              <div style="font-size:.7rem;
                  color:{'#16A34A' if auc>=0.95 else '#DC2626'};">
                  {'✅ ≥0.95' if auc>=0.95 else f'❌ Need +{0.95-auc:.4f}'}</div>
            </div>
            <div>
              <div style="font-size:.7rem;color:#64748B;
                  font-weight:600;
                  text-transform:uppercase;">F1-Score</div>
              <div style="font-size:1.4rem;font-weight:700;
                  color:{'#16A34A' if f1>=0.85 else '#DC2626'};">
                  {f1:.4f}</div>
              <div style="font-size:.7rem;
                  color:{'#16A34A' if f1>=0.85 else '#DC2626'};">
                  {'✅ ≥0.85' if f1>=0.85 else f'❌ Need +{0.85-f1:.4f}'}</div>
            </div>
            <div>
              <div style="font-size:.7rem;color:#64748B;
                  font-weight:600;
                  text-transform:uppercase;">Recall</div>
              <div style="font-size:1.4rem;font-weight:700;
                  color:{'#16A34A' if rec>=0.90 else '#DC2626'};">
                  {rec:.4f}</div>
              <div style="font-size:.7rem;
                  color:{'#16A34A' if rec>=0.90 else '#DC2626'};">
                  {'✅ ≥0.90' if rec>=0.90 else f'❌ Need +{0.90-rec:.4f}'}</div>
            </div>
            <div>
              <div style="font-size:.7rem;color:#64748B;
                  font-weight:600;
                  text-transform:uppercase;">Precision</div>
              <div style="font-size:1.4rem;font-weight:700;
                  color:#003366;">{prec:.4f}</div>
            </div>
          </div>
          <div style="font-size:.8rem;color:#64748B;
              padding-top:.6rem;
              border-top:1px solid #E2E8F0;">
            📊 Dataset: <b>{info['dataset_id']}</b>
            &nbsp;|&nbsp;
            👤 By: <b>{info['submitted_by']}</b>
            &nbsp;|&nbsp;
            🔗 BC: <code>{info['bc_id']}</code>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Regulatory checklist
        st.subheader("📋 Regulatory Checklist")
        checks = [
            ("AUC-ROC ≥ 0.95 (BAM threshold)",
             auc >= 0.95),
            ("F1-Score ≥ 0.85 (BAM threshold)",
             f1 >= 0.85),
            ("Recall ≥ 0.90 (BAM threshold)",
             rec >= 0.90),
            ("Precision ≥ 0.80",
             prec >= 0.80),
            ("Dataset registered",
             info["dataset_id"] != "N/A"),
            ("Model hash computed",
             info["model_hash"] != "N/A"),
            ("MLflow run linked",
             bool(info["run_id"])),
        ]
        cols = st.columns(3)
        for i, (label, passed) in enumerate(checks):
            with cols[i % 3]:
                st.markdown(
                    f"{'✅' if passed else '❌'} "
                    f"{label}")

        # Decision
        st.subheader("🎯 Compliance Decision")
        tab_validate, tab_reject = st.tabs([
            "✅ Validate", "❌ Reject"])

        with tab_validate:
            if not ok:
                st.error(
                    "❌ Cannot validate — "
                    "Metrics below BAM thresholds")
            else:
                st.success(
                    "✅ All thresholds met — "
                    "Ready for compliance validation")
                st.info(
                    "After validation:\n"
                    "→ ML Engineer will approve technically\n"
                    "→ Then deploy to production")

                if st.button(
                    "✅ Validate Compliance",
                    key=f"val_{name}",
                    type="primary",
                    disabled=not ok,
                    use_container_width=True):
                    with st.spinner(
                        "Recording on blockchain..."):
                        result = validate_compliance(
                            info["bc_id"])
                        if result.get("success"):
                            _pin_validation_report(
                                info["bc_id"],
                                user["username"],
                                info)
                            st.success(
                                f"✅ **{info['bc_id']}** "
                                f"compliance validated!")
                            st.info(
                                "→ ML Engineer can now "
                                "approve technically")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(
                                f"❌ {result.get('output',result.get('error','Error'))}")

        with tab_reject:
            st.warning(
                "Rejection requires a written "
                "regulatory report — "
                "recorded on blockchain.")

            with st.form(key=f"reject_{name}"):
                category = st.selectbox(
                    "Rejection Category *",
                    REJECT_CATEGORIES,
                    key=f"cat_{name}")

                justification = st.text_area(
                    "Regulatory Justification "
                    "*(min 50 chars)*",
                    placeholder=(
                        "Example: The model's recall "
                        "of 0.87 is below the BAM "
                        "minimum threshold of 0.90. "
                        "A recall below 0.90 means "
                        "10%+ of fraud transactions "
                        "are not detected, creating "
                        "unacceptable financial risk "
                        "for the bank and violating "
                        "SR 11-7 Section 4.2."),
                    height=150,
                    key=f"just_{name}")

                recommended = st.selectbox(
                    "Recommended Action *",
                    [
                        "Retrain with better recall",
                        "Use class_weight='balanced'",
                        "Lower decision threshold",
                        "Improve dataset quality",
                        "Add more fraud samples",
                        "Use different algorithm",
                        "Review feature selection"
                    ],
                    key=f"rec_{name}")

                submitted = st.form_submit_button(
                    "❌ Submit Rejection",
                    type="primary",
                    use_container_width=True)

            if submitted:
                if len(justification) < 50:
                    st.error(
                        "❌ Minimum 50 characters "
                        "required for justification.")
                else:
                    full = (
                        f"[CO_REJECT] [{category}] "
                        f"{justification} | "
                        f"Action: {recommended} | "
                        f"By: {user['username']} | "
                        f"{datetime.utcnow().isoformat()}")
                    with st.spinner("Recording..."):
                        r2 = revoke_model(
                            info["bc_id"], full)
                        if r2.get("success"):
                            cid = _pin_rejection(
                                info["bc_id"],
                                user["username"],
                                category,
                                justification,
                                recommended,
                                info)
                            st.error(
                                f"❌ **{info['bc_id']}** "
                                f"rejected")
                            st.markdown(f"""
                            <div style="background:#FEF2F2;
                                border:1px solid #FECACA;
                                border-radius:8px;
                                padding:1rem;">
                                <b>Rejection Report</b><br/>
                                Category: {category}<br/>
                                Action: {recommended}<br/>
                                IPFS: <code>{cid[:25]}...</code>
                            </div>
                            """, unsafe_allow_html=True)
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(
                                f"❌ {r2.get('output',r2.get('error'))}")


def _status_icon(status: str) -> str:
    return {
        "SUBMITTED":            "📋",
        "COMPLIANCE_VALIDATED": "✅",
        "TECHNICAL_APPROVED":   "🔧",
        "DEPLOYED":             "🚀",
        "REVOKED":              "❌",
    }.get(status, "❓")


def _pin_validation_report(model_id, officer,
                            info) -> str:
    try:
        data = {
            "action":       "COMPLIANCE_VALIDATION",
            "model_id":     model_id,
            "validated_by": officer,
            "timestamp":    datetime.utcnow().isoformat(),
            "metrics": {
                "auc_roc":   info["auc_roc"],
                "f1":        info["f1"],
                "recall":    info["recall"],
                "precision": info["precision"]
            },
            "regulatory_basis": [
                "EU AI Act 2024",
                "SR 11-7",
                "Basel III",
                "BAM Morocco"
            ]
        }
        r = httpx.post(
            f"{API_URL}/ipfs/pin-json",
            json={"data": data,
                  "name": f"compliance-{model_id}"},
            timeout=15)
        if r.status_code == 200:
            return r.json().get("cid","")
    except:
        pass
    return ""


def _pin_rejection(model_id, officer,
                   category, justification,
                   action, info) -> str:
    try:
        data = {
            "action":         "COMPLIANCE_REJECTION",
            "model_id":       model_id,
            "rejected_by":    officer,
            "timestamp":      datetime.utcnow().isoformat(),
            "category":       category,
            "justification":  justification,
            "recommended_action": action,
            "metrics": {
                "auc_roc":   info["auc_roc"],
                "f1":        info["f1"],
                "recall":    info["recall"]
            }
        }
        r = httpx.post(
            f"{API_URL}/ipfs/pin-json",
            json={"data": data,
                  "name": f"co-rejection-{model_id}"},
            timeout=15)
        if r.status_code == 200:
            return r.json().get("cid","")
    except:
        pass
    return ""
