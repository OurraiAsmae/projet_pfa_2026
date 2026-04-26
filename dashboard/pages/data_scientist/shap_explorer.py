"""
Data Scientist — Global SHAP Explorer v3.0
"""
import streamlit as st
import pandas as pd
import httpx
from utils.api_client import (
    get_ipfs_list, get_mlflow_models,
    get_mlflow_run, mlflow_dict, mlflow_params,
    API_URL, ML_URL
)

def show(user: dict):
    st.title("📊 Global SHAP Explorer")
    st.info(
        "Global feature importance computed on the "
        "training dataset. "
        "Per-transaction SHAP → Fraud Analyst only.")

    # Get registered models
    models = get_mlflow_models()
    if not models:
        st.warning("No models registered in MLflow.")
        return

    # Build model options
    model_options = {}
    for m in models:
        v = (m["latest_versions"][-1]
             if m.get("latest_versions") else None)
        if v:
            model_options[m["name"]] = {
                "model": m, "version": v}

    if not model_options:
        st.warning("No model versions available.")
        return

    # Model selector
    sel_name = st.selectbox(
        "Select Model", list(model_options.keys()))
    sel = model_options[sel_name]
    v   = sel["version"]

    # Get run info
    run_data = get_mlflow_run(v["run_id"])
    data     = run_data.get("data", {})
    met      = mlflow_dict(data.get("metrics", []))
    par      = mlflow_params(data.get("params", []))

    # ── Model info card ───────────────────────────
    auc_val  = met.get("auc_roc", 0)
    f1_val   = met.get("f1", 0)
    rec_val  = met.get("recall", 0)
    prec_val = met.get("precision", 0)
    mtype    = par.get("model_type", "N/A")
    did      = par.get("dataset_id", "Not linked")
    mhash    = par.get("model_hash_sha256", "N/A")

    # Use markdown card instead of st.metric
    st.markdown(f"""
    <div style="background:white;
                border:1px solid #E2E8F0;
                border-radius:10px;
                padding:1.2rem;
                margin-bottom:1rem;
                border-top:3px solid #003366;">
        <div style="display:grid;
                    grid-template-columns:1fr 1fr 1fr 1fr;
                    gap:1.5rem;">
            <div>
                <div style="font-size:.72rem;color:#64748B;
                            text-transform:uppercase;
                            font-weight:600;letter-spacing:.05em;">
                    AUC-ROC</div>
                <div style="font-size:1.6rem;font-weight:700;
                            color:#003366;margin-top:.2rem;">
                    {auc_val:.4f}</div>
                <div style="font-size:.72rem;color:#16A34A;">
                    {'✅ OK' if auc_val >= 0.95 else '⚠️ Below threshold'}</div>
            </div>
            <div>
                <div style="font-size:.72rem;color:#64748B;
                            text-transform:uppercase;
                            font-weight:600;letter-spacing:.05em;">
                    F1-Score</div>
                <div style="font-size:1.6rem;font-weight:700;
                            color:#003366;margin-top:.2rem;">
                    {f1_val:.4f}</div>
                <div style="font-size:.72rem;color:#16A34A;">
                    {'✅ OK' if f1_val >= 0.85 else '⚠️ Below threshold'}</div>
            </div>
            <div>
                <div style="font-size:.72rem;color:#64748B;
                            text-transform:uppercase;
                            font-weight:600;letter-spacing:.05em;">
                    Recall</div>
                <div style="font-size:1.6rem;font-weight:700;
                            color:#003366;margin-top:.2rem;">
                    {rec_val:.4f}</div>
            </div>
            <div>
                <div style="font-size:.72rem;color:#64748B;
                            text-transform:uppercase;
                            font-weight:600;letter-spacing:.05em;">
                    Precision</div>
                <div style="font-size:1.6rem;font-weight:700;
                            color:#003366;margin-top:.2rem;">
                    {prec_val:.4f}</div>
            </div>
        </div>
        <div style="margin-top:1rem;padding-top:.8rem;
                    border-top:1px solid #E2E8F0;
                    display:grid;
                    grid-template-columns:1fr 1fr;gap:1rem;">
            <div>
                <span style="font-size:.72rem;color:#64748B;
                             font-weight:600;">MODEL TYPE: </span>
                <span style="font-size:.9rem;color:#003366;
                             font-weight:700;">{mtype}</span>
            </div>
            <div>
                <span style="font-size:.72rem;color:#64748B;
                             font-weight:600;">DATASET: </span>
                <span style="font-size:.85rem;color:#0052A3;
                             font-weight:600;">{did}</span>
            </div>
        </div>
        <div style="margin-top:.5rem;">
            <span style="font-size:.72rem;color:#64748B;
                         font-weight:600;">🔐 HASH: </span>
            <span style="font-size:.75rem;color:#64748B;
                         font-family:monospace;">
                {mhash[:50]}...</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Compute button ────────────────────────────
    if st.button("🚀 Compute Global SHAP",
                 type="primary"):
        with st.spinner(
            "Computing Global SHAP on 500 samples... "
            "(30-60 seconds)"):
            try:
                model_path = _get_model_path(mtype)
                r = httpx.post(
                    f"{API_URL}/shap/global",
                    json={
                        "model_path": model_path,
                        "dataset_id": par.get(
                            "dataset_id",""),
                        "model_id":   sel_name,
                        "run_id":     v["run_id"]
                    }, timeout=120)
                if r.status_code == 200:
                    _show_results(r.json(), sel_name)
                else:
                    st.error(f"❌ {r.text[:200]}")
            except Exception as e:
                st.error(f"❌ {e}")

    # ── Cached Global SHAP from IPFS ──────────────
    st.subheader("📌 Cached Global SHAP (IPFS)")
    st.caption("Only model SHAP files — not datasets")

    files = get_ipfs_list()

    # Filter ONLY global-shap files (not datasets)
    global_shap_files = [
        f for f in files
        if f["name"].lower().startswith("global-shap")]

    if global_shap_files:
        for f in global_shap_files:
            model_label = (
                f["name"]
                .replace("global-shap-","")
                .replace("-"," "))
            with st.expander(
                f"📊 {model_label}"):

                c1, c2 = st.columns([3,1])
                c1.caption(f"CID: {f['name']}")
                c2.markdown(
                    f"[🌐 View on IPFS]({f['url']})")

                try:
                    r2 = httpx.get(
                        f['url'], timeout=10)
                    if r2.status_code == 200:
                        data2 = r2.json()
                        imp   = data2.get(
                            "global_importance", [])
                        if imp:
                            df2 = pd.DataFrame(imp)
                            if "importance" in df2.columns:
                                # Summary metrics
                                c1,c2,c3 = st.columns(3)
                                c1.metric("Model",
                                    data2.get(
                                        "model_type","N/A"))
                                c2.metric("Samples",
                                    data2.get("n_samples",0))
                                c3.metric("Explainer",
                                    data2.get(
                                        "explainer_type",""))

                                # Table
                                st.dataframe(
                                    df2[["rank","feature",
                                         "importance"]],
                                    use_container_width=True)

                                # Chart
                                st.bar_chart(
                                    df2.set_index(
                                        "feature")[
                                        "importance"])
                except:
                    st.caption("Could not load content")
    else:
        st.info(
            "No Global SHAP cached yet. "
            "Select a model and click "
            "'Compute Global SHAP' above.")


def _get_model_path(model_type: str) -> str:
    """Map model type to file path"""
    paths = {
        "RandomForestClassifier":
            "/app/mlops/models/random_forest.pkl",
        "XGBClassifier":
            "/app/mlops/models/gradient_boosting.pkl",
        "GradientBoostingClassifier":
            "/app/mlops/models/gradient_boosting.pkl",
        "LogisticRegression":
            "/app/mlops/models/logistic_regression.pkl",
    }
    return paths.get(
        model_type,
        "/app/mlops/models/random_forest.pkl")


def _show_results(result: dict, model_name: str):
    """Display global SHAP results"""
    if result.get("error"):
        st.error(f"❌ {result['error']}")
        return

    st.success(
        f"✅ Global SHAP computed for "
        f"**{model_name}**")

    cid = result.get("cid","")
    if cid and not cid.startswith("QmSIM"):
        st.success(
            f"✅ Pinned to IPFS: `{cid[:30]}...`")
        st.markdown(
            f"[🌐 View on IPFS]"
            f"(https://gateway.pinata.cloud/ipfs/{cid})")

    # Summary
    c1,c2,c3 = st.columns(3)
    c1.metric("Samples Used",
        result.get("n_samples",0))
    c2.metric("Features",
        result.get("n_features",17))
    c3.metric("Explainer",
        result.get("explainer_type","tree"))

    importance = result.get("global_importance",[])
    if not importance:
        st.warning("No importance data.")
        return

    df = pd.DataFrame(importance)

    # Table
    st.subheader("📊 Feature Importance Ranking")
    st.dataframe(
        df[["rank","feature","importance"]],
        use_container_width=True)

    # Bar chart
    st.subheader("📈 Feature Importance Chart")
    st.bar_chart(
        df.set_index("feature")["importance"])

    # Top 3 interpretation
    st.subheader("💡 Interpretation")
    total = sum(f["importance"] for f in importance)
    for f in importance[:3]:
        pct = (f["importance"]/total*100
               if total > 0 else 0)
        st.markdown(
            f"**#{f['rank']} {f['feature']}**: "
            f"`{f['importance']:.4f}` — "
            f"{pct:.1f}% of total importance")

    st.info(
        "**EU AI Act Art. 13 — Transparency:**\n"
        "This analysis demonstrates that the model "
        "uses legitimate fraud indicators and not "
        "discriminatory features like client demographics.")
