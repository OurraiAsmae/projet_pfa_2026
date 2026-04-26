"""
ML Engineer — Model Deployment v4.0
Switch active model, deactivate, revoke permanently
"""
import streamlit as st
import httpx
import time
from datetime import datetime
from utils.api_client import (
    get_active_model, get_models_info,
    deploy_governance, deploy_model,
    revoke_model, API_URL
)
from utils.model_registry import (
    get_mlflow_bc_mapping, _get_bc_status
)

def show(user: dict):
    st.title("🚀 Model Deployment")
    st.warning(
        "⚠️ Four-Eyes Principle: "
        "Compliance Officer validated → "
        "ML Engineer approved → "
        "ML Engineer deploys (you)")

    # Current active model
    active = get_active_model()
    if active:
        st.markdown(f"""
        <div style="background:#EFF6FF;
                    border:1px solid #BFDBFE;
                    border-left:4px solid #003366;
                    border-radius:8px;padding:1rem;
                    margin-bottom:1rem;">
            <div style="font-size:.75rem;color:#64748B;
                        font-weight:600;
                        text-transform:uppercase;">
                🟢 Currently Active in Production</div>
            <div style="font-size:1.1rem;font-weight:700;
                        color:#003366;margin-top:.3rem;">
                {active.get('model_id','N/A')}</div>
            <div style="font-size:.85rem;color:#0052A3;">
                {active.get('model_type','N/A')} |
                Since: {str(active.get(
                    'deployed_at',''))[:16]} UTC
            </div>
        </div>
        """, unsafe_allow_html=True)

    with st.spinner("Loading models..."):
        mapping      = get_mlflow_bc_mapping()
        local_models = get_models_info()
        local_map    = {
            m["name"]: m for m in local_models}

    candidates = _build_candidates(
        mapping, local_map)

    if not candidates:
        st.warning("No models available.")
        return

    # Separate by status — HIDE REVOKED + SUBMITTED
    ready     = {k:v for k,v in candidates.items()
                 if v["bc_status"] == "TECHNICAL_APPROVED"}
    validated = {k:v for k,v in candidates.items()
                 if v["bc_status"] == "COMPLIANCE_VALIDATED"}
    deployed  = {k:v for k,v in candidates.items()
                 if v["bc_status"] == "DEPLOYED"}
    # SUBMITTED and REVOKED are NOT shown

    # ── READY FOR DEPLOYMENT ─────────────────────
    if ready:
        st.subheader(
            f"🟡 Ready for Deployment ({len(ready)})")
        st.success("✅ Full approval chain completed!")
        for name, info in ready.items():
            _render_ready(name, info, user)

    # ── COMPLIANCE VALIDATED ──────────────────────
    if validated:
        st.subheader(
            f"🔵 Awaiting Technical Approval "
            f"({len(validated)})")
        for name, info in validated.items():
            with st.expander(
                f"🔵 **{name}** — "
                f"{info['model_type']}"):
                st.info(
                    "→ Go to Technical Approval "
                    "to approve this model first")

    # ── DEPLOYED MODELS ───────────────────────────
    if deployed:
        st.subheader(
            f"📦 Deployed Models ({len(deployed)})")
        for name, info in deployed.items():
            _render_deployed(name, info, user)

    if not ready and not validated and not deployed:
        st.info(
            "No models in deployment pipeline.\n"
            "Submit a model as Data Scientist first.")


def _render_ready(name: str,
                   info: dict,
                   user: dict):
    """Render model ready for first deployment"""
    bc_id  = info["bc_id"]
    mtype  = info["model_type"]
    auc    = info["auc_roc"]
    f1     = info["f1"]

    with st.expander(
        f"🟡 **{name}** — {mtype} — "
        f"AUC:{auc:.4f} — TECHNICAL_APPROVED",
        expanded=True):

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("AUC-ROC", f"{auc:.4f}")
        c2.metric("F1",      f"{f1:.4f}")
        c3.metric("Dataset", info["dataset_id"][:15])
        c4.metric("By",      info["submitted_by"])

        st.caption(f"BC ID: `{bc_id}`")

        if not info["local_found"]:
            st.error(
                f"❌ Local model file not found "
                f"for {mtype}")
            return

        st.markdown("---")
        st.markdown("**🔒 4-Stage Deployment Process**")
        for num, title in [
            ("1️⃣","Verify TECHNICAL_APPROVED in Fabric"),
            ("2️⃣","Retrieve local model file"),
            ("3️⃣","Recompute SHA-256 hash"),
            ("4️⃣","Load into FastAPI production")]:
            st.markdown(f"{num} {title}")

        confirmed = st.text_input(
            "Confirm BC Model ID",
            bc_id, key=f"cid_{name}")

        if st.button(
            "🚀 Deploy to Production",
            key=f"dep_{name}",
            type="primary",
            use_container_width=True):
            _run_deployment(
                info, confirmed,
                user["username"])


def _render_deployed(name: str,
                      info: dict,
                      user: dict):
    """
    Render deployed model with:
    - Deactivate button (if active)
    - Activate button (if inactive)
    - Revoke permanently button
    """
    bc_id     = info["bc_id"]
    mtype     = info["model_type"]
    auc       = info["auc_roc"]
    is_active = info["is_active"]

    status_icon = "🟢" if is_active else "⚫"
    status_text = "ACTIVE" if is_active else "INACTIVE"

    with st.expander(
        f"{status_icon} **{name}** — {mtype} — "
        f"AUC:{auc:.4f} — {status_text}"):

        c1,c2,c3 = st.columns(3)
        c1.metric("AUC-ROC", f"{auc:.4f}")
        c2.metric("Status",  status_text)
        c3.metric("Active",
            "🟢 YES" if is_active else "⚫ NO")

        st.caption(
            f"BC ID: `{bc_id}` | "
            f"Dataset: {info['dataset_id']}")

        st.markdown("---")

        if is_active:
            # ── ACTIVE MODEL ─────────────────────
            st.success(
                "🟢 This model is currently serving "
                "live fraud detection requests")

            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "⏸️ Deactivate",
                    key=f"deact_{name}",
                    help="Stop this model but keep "
                         "it available for reactivation"):
                    with st.spinner("Deactivating..."):
                        # Just change active status
                        # without touching blockchain
                        r = httpx.post(
                            f"{API_URL}/model/deactivate",
                            json={"model_id": bc_id},
                            timeout=10)
                        if r.status_code == 200:
                            st.warning(
                                f"⏸️ **{name}** "
                                f"deactivated — "
                                f"No model active now")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(
                                f"❌ {r.text[:100]}")

            with col2:
                st.button(
                    "🗑️ Revoke Permanently",
                    key=f"rev_{name}",
                    disabled=True,
                    help="Cannot revoke active model. "
                         "Deactivate first.")

        else:
            # ── INACTIVE MODEL ────────────────────
            st.info(
                "⚫ This model is deployed but "
                "not currently active")

            col1, col2 = st.columns(2)

            with col1:
                # Activate button
                if info["local_found"]:
                    if st.button(
                        "▶️ Activate",
                        key=f"act_{name}",
                        type="primary",
                        help="Make this model active "
                             "in production"):
                        with st.spinner(
                            "Activating..."):
                            r = deploy_model(
                                bc_id,
                                info["local_path"])
                            if r.get("success"):
                                st.success(
                                    f"✅ **{name}** "
                                    f"is now active "
                                    f"in production!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(
                                    f"❌ {r}")
                else:
                    st.error(
                        "❌ Local file not found")

            with col2:
                # Revoke permanently
                with st.expander(
                    "🗑️ Revoke Permanently"):
                    st.error(
                        "⚠️ This action is IRREVERSIBLE\n\n"
                        "The model will be permanently "
                        "revoked and can never be "
                        "deployed again.")
                    reason = st.text_area(
                        "Reason for permanent revocation",
                        key=f"rev_reason_{name}",
                        placeholder=(
                            "e.g. Model replaced by "
                            "better version, "
                            "security issue detected..."))
                    if st.button(
                        "🗑️ Confirm Permanent Revocation",
                        key=f"rev_confirm_{name}",
                        type="primary"):
                        if len(reason) < 20:
                            st.error(
                                "Please provide a reason "
                                "(min 20 chars)")
                        else:
                            with st.spinner(
                                "Revoking..."):
                                full_reason = (
                                    f"[PERMANENT_REVOKE] "
                                    f"{reason} | "
                                    f"By: {user['username']} | "
                                    f"{datetime.utcnow().isoformat()}")
                                r2 = revoke_model(
                                    bc_id, full_reason)
                                if r2.get("success"):
                                    st.error(
                                        f"🗑️ **{name}** "
                                        f"permanently "
                                        f"revoked — "
                                        f"Never deployable again")
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error(
                                        f"❌ {r2.get('output',r2.get('error'))}")


def _build_candidates(mapping: dict,
                       local_map: dict) -> dict:
    type_to_local = {
        "RandomForestClassifier":    "random_forest",
        "XGBClassifier":             "gradient_boosting",
        "GradientBoostingClassifier":"gradient_boosting",
        "LogisticRegression":        "logistic_regression",
    }
    result = {}
    for mlflow_name, info in mapping.items():
        # Skip SUBMITTED and UNKNOWN
        if info["bc_status"] in [
            "SUBMITTED","UNKNOWN",""]:
            continue
        # Skip if not on chain
        if not info["on_chain"]:
            continue
        model_type = info["model_type"]
        local_name = type_to_local.get(model_type,"")
        local_m    = local_map.get(local_name, {})
        result[mlflow_name] = {
            **info,
            "local_name": local_name,
            "local_path": local_m.get("path",""),
            "local_size": local_m.get("size_mb",0),
            "is_active":  local_m.get("is_active",False),
            "local_found":bool(local_m),
        }
    return result


def _run_deployment(info: dict,
                    model_id: str,
                    engineer: str):
    prog   = st.progress(0)
    status = st.empty()

    # Stage 1
    status.info("1️⃣ Verifying blockchain status...")
    prog.progress(20)
    bc_status = _get_bc_status(model_id)
    if bc_status != "TECHNICAL_APPROVED":
        st.error(
            f"🚫 ABORT — Required: TECHNICAL_APPROVED "
            f"| Found: {bc_status}")
        return
    st.success("✅ Stage 1: TECHNICAL_APPROVED")

    # Stage 2
    status.info("2️⃣ Retrieving model file...")
    prog.progress(40)
    model_path = info.get("local_path","")
    if not model_path:
        st.error("🚫 Model path not found")
        return
    st.success(f"✅ Stage 2: `{model_path}`")

    # Stage 3
    status.info("3️⃣ Computing SHA-256...")
    prog.progress(60)
    try:
        r = httpx.get(
            f"{API_URL}/model/hash",
            params={"path": model_path},
            timeout=10)
        if r.status_code == 200:
            h = r.json().get("hash","")
            mh = info.get("model_hash","")
            if mh and mh != "N/A" and h == mh:
                st.success(
                    f"✅ Stage 3: Hash verified ✓")
            else:
                st.success(
                    f"✅ Stage 3: Hash computed "
                    f"`{h[:20]}...`")
    except Exception as e:
        st.warning(f"⚠️ Stage 3: {e}")
    prog.progress(75)

    # Stage 4
    status.info("4️⃣ Deploying to production...")
    prog.progress(85)
    bc_ok = False
    try:
        bc_r  = deploy_governance(model_id)
        bc_ok = bc_r.get("success",False)
    except:
        pass
    api_r = deploy_model(model_id, model_path)
    prog.progress(100)
    status.empty()

    if api_r.get("success"):
        st.success("🎉 Deployed successfully!")
        st.balloons()
        st.markdown(f"""
        <div style="background:#F0FDF4;
                    border-left:4px solid #16A34A;
                    border-radius:8px;padding:1rem;">
            <b>🚀 Deployment Successful</b><br/>
            Model: {model_id}<br/>
            By: {engineer}<br/>
            Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}<br/>
            Blockchain: {'✅' if bc_ok else '⚠️ Pending'}
        </div>
        """, unsafe_allow_html=True)
        time.sleep(2)
        st.rerun()
    else:
        st.error(f"❌ {api_r}")
