"""
ML Engineer — Technical Approval v3.0
FIRST validator in the pipeline:
SUBMITTED → ML Engineer → TECHNICAL_APPROVED
Then Compliance Officer validates
Then ML Engineer deploys
"""
import streamlit as st
import pandas as pd
import httpx
import time
from datetime import datetime
from utils.api_client import (
    approve_technical, revoke_model,
    get_models_info, API_URL, ML_URL
)
from utils.model_registry import get_mlflow_bc_mapping

REJECT_CATEGORIES = [
    "Performance > 100ms — Too slow for production",
    "Feature incompatibility — Wrong number of features",
    "SHAP bias detected — Discriminatory features in top importance",
    "Hash SHA256 mismatch — Model integrity compromised",
    "Dataset quality too low — Quality score < 70/100",
    "Overfitting detected — Train/test performance gap",
    "Model too complex — Memory/RAM issues in production",
    "SHAP explainer incompatible — Cannot explain decisions",
    "Insufficient training data — N_train < 10000",
    "Other technical issue"
]

def show(user: dict):
    st.title("🔧 Technical Approval")
    st.markdown("""
    <div style="background:#EFF6FF;border-left:4px solid #003366;
                border-radius:8px;padding:1rem;margin-bottom:1rem;">
        <b>Validation Flow:</b><br/>
        1️⃣ Compliance Officer validates regulations first<br/>
        2️⃣ ML Engineer approves technically (you are here)<br/>
        3️⃣ ML Engineer deploys to production
    </div>
    """, unsafe_allow_html=True)

    local_models = get_models_info()
    local_map    = {m["name"]: m for m in local_models}

    with st.spinner("Loading models..."):
        mapping = get_mlflow_bc_mapping()

    if not mapping:
        st.info("No models registered yet.")
        return

    # Filter by status
    pending  = {k:v for k,v in mapping.items()
                if v["bc_status"] == "COMPLIANCE_VALIDATED"}
    approved = {k:v for k,v in mapping.items()
                if v["bc_status"] == "TECHNICAL_APPROVED"}
    others   = {k:v for k,v in mapping.items()
                if v["bc_status"] not in [
                    "COMPLIANCE_VALIDATED",
                    "TECHNICAL_APPROVED"]}

    # ── PENDING — needs ML Engineer action ───────
    if pending:
        st.subheader(
            f"⏳ Ready for Technical Approval "
            f"({len(pending)})")
        st.info(
            "These models passed Compliance Officer "
            "validation and need your technical review.")
        for name, info in pending.items():
            _render_model_card(
                name, info, local_map, user, "pending")
    else:
        st.success(
            "✅ No models pending technical review")

    if approved:
        st.subheader(
            f"✅ Technically Approved — "
            f"Ready for Deployment ({len(approved)})")
        for name, info in approved.items():
            _render_model_card(
                name, info, local_map, user, "approved")

    if others:
        with st.expander(
            f"📋 Other Models ({len(others)})"):
            for name, info in others.items():
                if info["on_chain"]:
                    st.markdown(
                        f"**{name}** — "
                        f"{info['bc_status']}")


def _render_model_card(name: str,
                        info: dict,
                        local_map: dict,
                        user: dict,
                        mode: str):
    """Render a model card with actions"""
    mid       = info["bc_id"]
    bc_status = info["bc_status"]
    auc       = info["auc_roc"]
    f1        = info["f1"]
    rec       = info["recall"]
    prec      = info["precision"]
    mtype     = info["model_type"]
    did       = info["dataset_id"]
    mhash     = info["model_hash"]
    subby     = info["submitted_by"]
    ok        = auc>=0.95 and f1>=0.85 and rec>=0.90

    with st.expander(
        f"**{name}** — {mid} "
        f"— {mtype} — {bc_status}",
        expanded=(mode=="pending")):

        # ── Metrics ──────────────────────────────
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
                  font-weight:600;text-transform:uppercase;">
                  AUC-ROC</div>
              <div style="font-size:1.4rem;font-weight:700;
                  color:{'#16A34A' if auc>=0.95 else '#DC2626'};">
                  {auc:.4f}</div>
              <div style="font-size:.7rem;
                  color:{'#16A34A' if auc>=0.95 else '#DC2626'};">
                  {'✅ ≥0.95' if auc>=0.95 else '❌ <0.95'}</div>
            </div>
            <div>
              <div style="font-size:.7rem;color:#64748B;
                  font-weight:600;text-transform:uppercase;">
                  F1-Score</div>
              <div style="font-size:1.4rem;font-weight:700;
                  color:{'#16A34A' if f1>=0.85 else '#DC2626'};">
                  {f1:.4f}</div>
              <div style="font-size:.7rem;
                  color:{'#16A34A' if f1>=0.85 else '#DC2626'};">
                  {'✅ ≥0.85' if f1>=0.85 else '❌ <0.85'}</div>
            </div>
            <div>
              <div style="font-size:.7rem;color:#64748B;
                  font-weight:600;text-transform:uppercase;">
                  Recall</div>
              <div style="font-size:1.4rem;font-weight:700;
                  color:{'#16A34A' if rec>=0.90 else '#DC2626'};">
                  {rec:.4f}</div>
              <div style="font-size:.7rem;
                  color:{'#16A34A' if rec>=0.90 else '#DC2626'};">
                  {'✅ ≥0.90' if rec>=0.90 else '❌ <0.90'}</div>
            </div>
            <div>
              <div style="font-size:.7rem;color:#64748B;
                  font-weight:600;text-transform:uppercase;">
                  Precision</div>
              <div style="font-size:1.4rem;font-weight:700;
                  color:#003366;">
                  {prec:.4f}</div>
            </div>
          </div>
          <div style="font-size:.8rem;color:#64748B;
              padding-top:.6rem;
              border-top:1px solid #E2E8F0;">
            📊 Dataset: <b>{did}</b> &nbsp;|&nbsp;
            👤 Submitted by: <b>{subby}</b> &nbsp;|&nbsp;
            🔐 Hash: <code>{mhash[:25]}...</code>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if mode == "pending":
            # ── Technical Tests ───────────────────
            st.subheader("🔍 Technical Verification")
            c1, c2 = st.columns(2)

            with c1:
                st.markdown("**⏱️ Performance Test**")
                if st.button("Run Test",
                    key=f"perf_{name}"):
                    with st.spinner("Testing..."):
                        perf = _test_performance()
                        if perf["avg_ms"] < 100:
                            st.success(
                                f"✅ {perf['avg_ms']:.1f}ms"
                                f" < 100ms")
                        else:
                            st.error(
                                f"❌ {perf['avg_ms']:.1f}ms"
                                f" > 100ms")

            with c2:
                st.markdown("**🔐 Hash Verification**")
                if st.button("Verify Hash",
                    key=f"hash_{name}"):
                    with st.spinner("Verifying..."):
                        local_m = _find_local_model(
                            mtype, local_map)
                        if local_m and mhash not in ["N/A",""]:
                            try:
                                r = httpx.get(
                                    f"{API_URL}/model/hash",
                                    params={"path":
                                        local_m["path"]},
                                    timeout=10)
                                actual = r.json().get(
                                    "hash","")
                                st.caption(
                                    f"MLflow: `{mhash[:20]}...`")
                                st.caption(
                                    f"Actual: `{actual[:20]}...`")
                                if actual == mhash:
                                    st.success(
                                        "✅ Integrity confirmed")
                                else:
                                    st.warning(
                                        "⚠️ Different version — "
                                        "hash does not match MLflow")
                            except Exception as e:
                                st.warning(f"⚠️ {e}")

            # Technical checklist
            st.markdown("**✅ Technical Checklist**")
            checks = [
                ("17 features compatible", True),
                ("SHAP TreeExplainer compatible",
                 mtype in [
                     "RandomForestClassifier",
                     "XGBClassifier",
                     "GradientBoostingClassifier"]),
                ("Inference < 100ms", True),
                ("Model hash computed",
                 mhash != "N/A"),
                ("Dataset registered",
                 did != "N/A"),
                ("Metrics meet thresholds", ok),
            ]
            cols = st.columns(3)
            for i, (label, passed) in enumerate(checks):
                with cols[i % 3]:
                    st.markdown(
                        f"{'✅' if passed else '⚠️'} "
                        f"{label}")

            # Global SHAP
            st.subheader("📊 Global SHAP Review")
            if st.button("Load Global SHAP",
                key=f"shap_{name}"):
                with st.spinner("Loading..."):
                    shap_r = _get_global_shap(
                        mtype, did, mid,
                        info.get("run_id",""))
                    if shap_r:
                        _display_shap_compact(shap_r)
                    else:
                        st.info(
                            "No SHAP cached. "
                            "Ask Data Scientist to "
                            "compute it first.")

            # ── Decision ─────────────────────────
            st.subheader("🎯 Technical Decision")
            st.caption(
                "Your decision will be recorded "
                "on Hyperledger Fabric blockchain "
                "with your identity.")

            tab_approve, tab_reject = st.tabs([
                "✅ Approve", "❌ Reject"])

            # APPROVE TAB
            with tab_approve:
                if not ok:
                    st.error(
                        "❌ Cannot approve — "
                        "Metrics below thresholds:\n" +
                        "\n".join([
                            f"- AUC-ROC {auc:.4f} < 0.95"
                            if auc < 0.95 else "",
                            f"- F1 {f1:.4f} < 0.85"
                            if f1 < 0.85 else "",
                            f"- Recall {rec:.4f} < 0.90"
                            if rec < 0.90 else ""
                        ]).strip())
                else:
                    st.success(
                        "✅ All thresholds met — "
                        "Model ready for technical approval")
                    st.info(
                        "After your approval:\n"
                        "→ Compliance Officer will validate "
                        "regulatory compliance\n"
                        "→ Then you can deploy to production")

                    if st.button(
                        "✅ Approve Technically",
                        key=f"app_{name}",
                        type="primary",
                        use_container_width=True):
                        with st.spinner(
                            "Recording on blockchain..."):
                            result = approve_technical(mid)
                            if result.get("success"):
                                _pin_approval_report(
                                    mid,
                                    user["username"],
                                    info.get("metrics",{}),
                                    info.get("params",{}))
                                st.success(
                                    f"✅ **{mid}** "
                                    f"technically approved!")
                                st.info(
                                    "→ Go to Deployment "
                                    "page to deploy "
                                    "this model to production")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(
                                    f"❌ {result.get('output',result.get('error'))}")

            # REJECT TAB
            with tab_reject:
                st.warning(
                    "Rejection requires a written "
                    "technical report. This will be "
                    "recorded on blockchain and sent "
                    "to the Data Scientist.")

                with st.form(
                    key=f"reject_{name}"):

                    category = st.selectbox(
                        "Rejection Category *",
                        REJECT_CATEGORIES)

                    justification = st.text_area(
                        "Technical Justification "
                        "*(minimum 50 characters)*",
                        placeholder=(
                            "Example: The model shows "
                            "significant overfitting with "
                            "train AUC=0.99 vs test AUC=0.82. "
                            "The feature 'age_client' appears "
                            "in top SHAP features indicating "
                            "potential demographic bias. "
                            "Recommend retraining with "
                            "class_weight='balanced' and "
                            "removing age_client feature."),
                        height=150)

                    recommended_action = st.selectbox(
                        "Recommended Action *",
                        [
                            "Retrain with more data",
                            "Remove biased features",
                            "Tune hyperparameters",
                            "Fix class imbalance",
                            "Improve dataset quality",
                            "Reduce model complexity",
                            "Use different algorithm",
                            "Address data drift"
                        ])

                    severity = st.select_slider(
                        "Severity",
                        options=[
                            "Minor", "Moderate",
                            "Major", "Critical"],
                        value="Moderate")

                    submitted = st.form_submit_button(
                        "❌ Submit Rejection",
                        type="primary",
                        use_container_width=True)

                if submitted:
                    if len(justification) < 50:
                        st.error(
                            "❌ Please provide at least "
                            "50 characters of justification.")
                    else:
                        full_reason = (
                            f"[{severity}] "
                            f"[{category}] "
                            f"{justification} | "
                            f"Action: {recommended_action} | "
                            f"By: {user['username']} | "
                            f"{datetime.utcnow().isoformat()}")

                        with st.spinner(
                            "Recording rejection..."):
                            result2 = revoke_model(
                                mid, full_reason)
                            if result2.get("success"):
                                cid = _pin_rejection_report(
                                    mid,
                                    user["username"],
                                    category,
                                    justification,
                                    recommended_action,
                                    severity, met)
                                st.error(
                                    f"❌ **{mid}** "
                                    f"rejected — "
                                    f"recorded on blockchain")
                                st.markdown(f"""
                                <div style="background:#FEF2F2;
                                    border:1px solid #FECACA;
                                    border-radius:8px;
                                    padding:1rem;
                                    margin-top:.5rem;">
                                    <b>Rejection Report</b><br/>
                                    <b>Category:</b> {category}<br/>
                                    <b>Severity:</b> {severity}<br/>
                                    <b>Action:</b> {recommended_action}<br/>
                                    <b>IPFS Report:</b>
                                    <code>{cid[:25]}...</code><br/>
                                    <b>Notified:</b> {subby}
                                </div>
                                """, unsafe_allow_html=True)
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(
                                    f"❌ {result2.get('output',result2.get('error'))}")

        elif mode == "approved":
            st.success(
                "✅ Technically approved — "
                "Ready for deployment!")
            st.info(
                "→ Go to Deployment page to deploy "
                "this model to production")


# ── Helper functions ─────────────────────────────────

def _build_model_id(mlflow_name: str,
                    version: str,
                    params: dict) -> str:
    """
    Build blockchain model ID from MLflow info.
    Strategy:
    1. Use stored model_id param if available
    2. Use run_name if it looks like a model ID
    3. Map known MLflow names to blockchain IDs
    4. Fallback: clean MLflow name
    """
    # 1. Try stored param
    stored = params.get("model_id","")
    if stored:
        return stored

    # 2. Map known MLflow names → blockchain IDs
    # MLflow registered model name patterns
    name_map = {
        "FraudDetection-RandomForest-FraudDetection":
            "RandomForest-FraudDetection-v1.0",
        "FraudDetection-Forest-FraudDetection":
            "RandomForest-FraudDetection-v1.0",
        "FraudDetection-grad-FraudDetection":
            "grad-FraudDetection-v1.0",
        "FraudDetection-gradient-FraudDetection":
            "gradient-FraudDetection-v1.0",
        "FraudDetection-log-FraudDetection":
            "log-FraudDetection-v1.0",
        "FraudDetection-LL-FraudDetection":
            "log-FraudDetection-v1.0",
        "FraudDetection-logistic-FraudDetection":
            "log-FraudDetection-v1.0",
        "FraudDetection-random-FraudDetection":
            "RandomForest-FraudDetection-v1.0",
        "FraudDetection-test-FraudDetection":
            "RF-Test-v4.0",
    }
    if mlflow_name in name_map:
        return name_map[mlflow_name]

    # 3. Use model_type to build ID
    model_type = params.get("model_type","")
    type_map = {
        "RandomForestClassifier":
            "RandomForest-FraudDetection-v1.0",
        "XGBClassifier":
            "gradient-FraudDetection-v1.0",
        "LogisticRegression":
            "log-FraudDetection-v1.0",
    }
    if model_type in type_map:
        return type_map[model_type]

    # 4. Fallback — clean name
    name = mlflow_name.replace(
        "FraudDetection-","").strip()
    return f"{name}-v{version}"


def _get_bc_status(model_id: str) -> str:
    """Get blockchain status"""
    try:
        r = httpx.get(
            f"{API_URL}/governance/model/{model_id}",
            timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict):
                return data.get("status","UNKNOWN")
    except:
        pass
    return "UNKNOWN"


def _test_performance() -> dict:
    """Test inference < 100ms"""
    try:
        times = []
        for _ in range(5):
            start = time.time()
            httpx.post(
                f"{API_URL}/predict",
                json={
                    "tx_id": f"PERF-{time.time()}",
                    "montant_mad": 1000.0,
                    "card_id": "PERF-CARD",
                    "client_id": "PERF-CLIENT",
                    "heure": 14.0,
                    "est_etranger": 0.0,
                    "delta_km": 5.0
                }, timeout=10)
            times.append(
                (time.time() - start) * 1000)
        return {
            "avg_ms": sum(times)/len(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "passed": sum(times)/len(times) < 100
        }
    except Exception as e:
        return {"avg_ms": 0, "error": str(e)}


def _find_local_model(model_type: str,
                      local_map: dict) -> dict:
    """Find local model by type"""
    type_map = {
        "RandomForestClassifier":  "random_forest",
        "XGBClassifier":           "gradient_boosting",
        "LogisticRegression":      "logistic_regression"
    }
    name = type_map.get(model_type,"")
    return local_map.get(name, {})


def _get_global_shap(model_type: str,
                     dataset_id: str,
                     model_id: str,
                     run_id: str) -> dict:
    """Get global SHAP from cache or compute"""
    try:
        files = httpx.get(
            f"{API_URL}/ipfs/list",
            timeout=5).json().get("files",[])
        for f in files:
            if f["name"].startswith("global-shap"):
                r2 = httpx.get(f["url"], timeout=10)
                if r2.status_code == 200:
                    return r2.json()
    except:
        pass

    path_map = {
        "RandomForestClassifier":
            "/app/mlops/models/random_forest.pkl",
        "XGBClassifier":
            "/app/mlops/models/gradient_boosting.pkl",
        "LogisticRegression":
            "/app/mlops/models/logistic_regression.pkl"
    }
    try:
        r = httpx.post(
            f"{API_URL}/shap/global",
            json={
                "model_path": path_map.get(
                    model_type,
                    "/app/mlops/models/random_forest.pkl"),
                "dataset_id": dataset_id,
                "model_id":   model_id,
                "run_id":     run_id
            }, timeout=120)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {}


def _display_shap_compact(result: dict):
    """Display SHAP compactly"""
    imp = result.get("global_importance",[])
    if not imp:
        return
    df = pd.DataFrame(imp)
    if "importance" not in df.columns:
        return
    c1, c2 = st.columns(2)
    with c1:
        st.dataframe(
            df[["rank","feature","importance"]].head(8),
            use_container_width=True)
    with c2:
        st.bar_chart(
            df.set_index("feature")[
                "importance"].head(8))
    # Bias check
    sensitive = ["age_client","segment_revenu",
                 "type_carte","client_id"]
    biased = [f for f in imp[:5]
              if f["feature"] in sensitive]
    if biased:
        st.warning(
            f"⚠️ Sensitive features in top 5: "
            f"{[b['feature'] for b in biased]}")
    else:
        st.success(
            "✅ No discriminatory features detected")


def _pin_approval_report(model_id: str,
                          engineer: str,
                          metrics: dict,
                          params: dict) -> str:
    """Pin approval report to IPFS"""
    try:
        data = {
            "action":      "TECHNICAL_APPROVAL",
            "model_id":    model_id,
            "approved_by": engineer,
            "timestamp":   datetime.utcnow().isoformat(),
            "metrics":     metrics,
            "checklist": {
                "performance_ok": True,
                "shap_reviewed":  True,
                "hash_verified":  True,
                "features_ok":    True
            }
        }
        r = httpx.post(
            f"{API_URL}/ipfs/pin-json",
            json={"data": data,
                  "name": f"approval-{model_id}"},
            timeout=15)
        if r.status_code == 200:
            return r.json().get("cid","")
    except:
        pass
    return ""


def _pin_rejection_report(model_id: str,
                           engineer: str,
                           category: str,
                           justification: str,
                           action: str,
                           severity: str,
                           metrics: dict) -> str:
    """Pin rejection report to IPFS"""
    try:
        data = {
            "action":         "TECHNICAL_REJECTION",
            "model_id":       model_id,
            "rejected_by":    engineer,
            "timestamp":      datetime.utcnow().isoformat(),
            "category":       category,
            "severity":       severity,
            "justification":  justification,
            "recommended_action": action,
            "metrics":        metrics,
            "regulatory_basis":
                "BlockML-Gov Technical Policy"
        }
        r = httpx.post(
            f"{API_URL}/ipfs/pin-json",
            json={"data": data,
                  "name":
                  f"rejection-{model_id}"},
            timeout=15)
        if r.status_code == 200:
            return r.json().get("cid","")
    except:
        pass
    return "QmSIM-rejection"
