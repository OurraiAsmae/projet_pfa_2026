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
    validate_compliance, revoke_model, reject_model,
    API_URL
)
from utils.model_registry import get_mlflow_bc_mapping
from styles import (
    _header, _card_header, _alert_box,
    _ICON_SHIELD, _ICON_BLOCKCHAIN, _ICON_CHECK, _ICON_WARNING, _ICON_ERROR,
    _ICON_PENDING, _ICON_INFO, _ICON_DATASET, _ICON_USER, _ICON_MODEL, _ICON_LINK
)

REJECT_CATEGORIES = [
    "AUC-ROC below threshold (< 0.80)",
    "F1-Score below threshold (< 0.55)",
    "Recall below threshold (< 0.40)",
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
    _header("Compliance Validation", _ICON_SHIELD)


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
        _card_header(f"Pending Compliance Review ({len(pending)})", _ICON_PENDING)
        for name, info in pending.items():
            _render_card(name, info, user, "pending")
    else:
        _alert_box("SUCCESS", "No models pending compliance review", _ICON_CHECK)

    # ── ALREADY PROCESSED ────────────────────────
    if others:
        _card_header(f"Already Processed ({len(others)})", _ICON_BLOCKCHAIN)
        for name, info in others.items():
            with st.expander(f"{name} — {info['bc_status']}"):
                c1,c2,c3 = st.columns(3)
                c1.metric("AUC-ROC",
                    f"{info['auc_roc']:.4f}")
                c2.metric("Status",
                    info["bc_status"])
                c3.metric("BC ID",
                    info["bc_id"][:20]+"...")

    # ── NOT ON BLOCKCHAIN ─────────────────────────
    if no_chain:
        with st.expander(f"Not on Blockchain ({len(no_chain)}) — Need to be submitted first"):
            for name, info in no_chain.items():
                st.markdown(
                    f"**{name}** — "
                    f"run_name: `{info['run_name']}` "
                    f"— Not found on blockchain")
            _alert_box("WARNING", "These models were registered in MLflow but not submitted to blockchain. Ask Data Scientist to re-submit.", _ICON_WARNING)


def _render_card(name: str, info: dict,
                  user: dict, mode: str):
    """Render compliance validation card"""
    auc  = info["auc_roc"]
    f1   = info["f1"]
    rec  = info["recall"]
    prec = info["precision"]
    ok   = auc>=0.80 and f1>=0.55 and rec>=0.40 and prec>=0.75

    with st.expander(
        f"{name} — {info['model_type']} — {info['bc_id']}",
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
                   color:{'#16A34A' if auc>=0.80 else '#DC2626'};">
                   {auc:.4f}</div>
               <div style="font-size:.7rem;
                   color:{'#16A34A' if auc>=0.80 else '#DC2626'};">
                   {'Target ≥0.80 met' if auc>=0.80 else f'Requires +{0.80-auc:.4f}'}</div>
            </div>
            <div>
              <div style="font-size:.7rem;color:#64748B;
                  font-weight:600;
                  text-transform:uppercase;">F1-Score</div>
              <div style="font-size:1.4rem;font-weight:700;
                   color:{'#16A34A' if f1>=0.55 else '#DC2626'};">
                   {f1:.4f}</div>
               <div style="font-size:.7rem;
                   color:{'#16A34A' if f1>=0.55 else '#DC2626'};">
                   {'Target ≥0.55 met' if f1>=0.55 else f'Requires +{0.55-f1:.4f}'}</div>
            </div>
            <div>
              <div style="font-size:.7rem;color:#64748B;
                  font-weight:600;
                  text-transform:uppercase;">Recall</div>
              <div style="font-size:1.4rem;font-weight:700;
                   color:{'#16A34A' if rec>=0.40 else '#DC2626'};">
                   {rec:.4f}</div>
               <div style="font-size:.7rem;
                   color:{'#16A34A' if rec>=0.40 else '#DC2626'};">
                   {'Target ≥0.40 met' if rec>=0.40 else f'Requires +{0.40-rec:.4f}'}</div>
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
            Dataset: <b>{info['dataset_id']}</b>
            &nbsp;|&nbsp;
            By: <b>{info['submitted_by']}</b>
            &nbsp;|&nbsp;
            BC: <code>{info['bc_id']}</code>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Regulatory checklist
        _card_header("Regulatory Checklist", _ICON_SHIELD)
        checks = [
            ("AUC-ROC ≥ 0.80 (BAM threshold)",
             auc >= 0.80),
            ("F1-Score ≥ 0.55 (BAM threshold)",
             f1 >= 0.55),
            ("Recall ≥ 0.40 (BAM threshold)",
             rec >= 0.40),
            ("Precision ≥ 0.75",
             prec >= 0.75),
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
                    f"<span style='color:{'#16A34A' if passed else '#DC2626'};font-weight:bold;'>"
                    f"{'✓' if passed else '✗'}</span> "
                    f"{label}", unsafe_allow_html=True)

        # Decision
        _card_header("Compliance Decision", _ICON_CHECK)
        tab_validate, tab_reject = st.tabs([
            "Validate", "Reject"])

        with tab_validate:
            if not ok:
                _alert_box("ERROR", "Cannot validate — Metrics below BAM thresholds", _ICON_ERROR)
            else:
                _alert_box("SUCCESS", "All thresholds met — Ready for compliance validation", _ICON_CHECK)
                _alert_box("INFO", "After validation:<br/>&rarr; ML Engineer will approve technically<br/>&rarr; Then deploy to production", _ICON_INFO)

                if st.button(
                    "Validate Compliance",
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
                            _alert_box("SUCCESS", f"**{info['bc_id']}** compliance validated!", _ICON_CHECK)
                            _alert_box("INFO", "→ ML Engineer can now approve technically", _ICON_INFO)
                            time.sleep(2)
                            st.rerun()
                        else:
                            _alert_box("ERROR", result.get('output',result.get('error','Error')), _ICON_ERROR)

        with tab_reject:
            _alert_box("WARNING", "Rejection requires a written regulatory report — recorded on blockchain.", _ICON_WARNING)

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
                    "Submit Rejection",
                    type="primary",
                    use_container_width=True)

            if submitted:
                if len(justification) < 50:
                    _alert_box("ERROR", "Minimum 50 characters required for justification.", _ICON_ERROR)
                else:
                    full = (
                        f"[CO_REJECT] [{category}] "
                        f"{justification} | "
                        f"Action: {recommended} | "
                        f"By: {user['username']} | "
                        f"{datetime.utcnow().isoformat()}")
                    with st.spinner("Recording..."):
                        r2 = reject_model(
                            info["bc_id"], full, category)
                        if r2.get("success"):
                            cid = _pin_rejection(
                                info["bc_id"],
                                user["username"],
                                category,
                                justification,
                                recommended,
                                info)
                            _alert_box("ERROR", f"**{info['bc_id']}** rejected", _ICON_ERROR)
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
                            _alert_box("ERROR", r2.get('output',r2.get('error', 'Error')), _ICON_ERROR)


def _status_icon(status: str) -> str:
    from styles import _ICON_PENDING, _ICON_CHECK, _ICON_SHIELD, _ICON_BLOCKCHAIN, _ICON_ERROR, _ICON_WARNING
    return {
        "SUBMITTED":            _ICON_PENDING,
        "COMPLIANCE_VALIDATED": _ICON_CHECK,
        "TECHNICAL_APPROVED":   _ICON_SHIELD,
        "DEPLOYED":             _ICON_BLOCKCHAIN,
        "REVOKED":              _ICON_ERROR,
    }.get(status, _ICON_WARNING)


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
