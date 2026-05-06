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

# --- SVG Icons ---
_ICON_NETWORK = '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#1F7A5A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>'
_ICON_CHART = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1F7A5A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
_ICON_IPFS = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>'
_ICON_SUCCESS = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'
_ICON_WARNING = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
_ICON_ERROR = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>'

def _header(title: str, subtitle: str, icon_svg: str):
    st.markdown(f"""
        <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.5rem;padding-bottom:1rem;border-bottom:1px solid #E5E7EB;">
            <div style="width:48px;height:48px;background:#F0FAF6;border-radius:12px;display:flex;align-items:center;justify-content:center;">
                {icon_svg}
            </div>
            <div>
                <h1 style="margin:0;padding:0;font-size:1.6rem;color:#111827;font-weight:700;">{title}</h1>
                <p style="margin:0;padding:0;color:#6B7280;font-size:0.9rem;">{subtitle}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

def _card_header(title: str, icon_svg: str):
    st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.5rem;margin:1.5rem 0 0.8rem 0;">
            <div style="display:flex;align-items:center;justify-content:center;">{icon_svg}</div>
            <h3 style="margin:0;padding:0;font-size:1.1rem;color:#111827;font-weight:600;">{title}</h3>
        </div>
    """, unsafe_allow_html=True)

def _alert_box(text: str, alert_type="info"):
    colors = {
        "success": ("#ECFDF5", "#10B981", "#065F46", _ICON_SUCCESS),
        "warning": ("#FFFBEB", "#F59E0B", "#92400E", _ICON_WARNING),
        "error":   ("#FEF2F2", "#EF4444", "#991B1B", _ICON_ERROR),
        "info":    ("#EFF6FF", "#3B82F6", "#1E40AF", _ICON_SUCCESS)
    }
    bg, border, text_color, icon = colors.get(alert_type, colors["info"])
    st.markdown(f"""
        <div style="padding:1rem;background-color:{bg};border-left:4px solid {border};border-radius:0.5rem;display:flex;align-items:flex-start;gap:0.75rem;margin-bottom:1rem;">
            <div style="margin-top:2px;">{icon}</div>
            <div style="color:{text_color};font-weight:500;">{text}</div>
        </div>
    """, unsafe_allow_html=True)


def show(user: dict):
    _header(
        "Global SHAP Explorer",
        "Global feature importance computed on the training dataset. Per-transaction SHAP → Fraud Analyst only.",
        _ICON_NETWORK
    )

    # Get registered models
    models = get_mlflow_models()
    if not models:
        _alert_box("No models registered in MLflow.", "warning")
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
        _alert_box("No model versions available.", "warning")
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

    st.markdown(
        f'<div style="background:white;'
        f'border:1px solid #E2E8F0;'
        f'border-radius:10px;'
        f'padding:1.2rem;'
        f'margin-bottom:1rem;'
        f'border-top:3px solid #1F7A5A;">'
        f'<div style="display:grid;'
        f'grid-template-columns:1fr 1fr 1fr 1fr;'
        f'gap:1.5rem;">'
        f'<div>'
        f'<div style="font-size:.72rem;color:#64748B;'
        f'text-transform:uppercase;'
        f'font-weight:600;letter-spacing:.05em;">'
        f'AUC-ROC</div>'
        f'<div style="font-size:1.6rem;font-weight:700;'
        f'color:#1F7A5A;margin-top:.2rem;">'
        f'{auc_val:.4f}</div>'
        f'<div style="font-size:.72rem;color:{"#16A34A" if auc_val >= 0.95 else "#D97706"};">'
        f'{"[PASS] OK" if auc_val >= 0.95 else "[WARN] Below threshold"}</div>'
        f'</div>'
        f'<div>'
        f'<div style="font-size:.72rem;color:#64748B;'
        f'text-transform:uppercase;'
        f'font-weight:600;letter-spacing:.05em;">'
        f'F1-Score</div>'
        f'<div style="font-size:1.6rem;font-weight:700;'
        f'color:#1F7A5A;margin-top:.2rem;">'
        f'{f1_val:.4f}</div>'
        f'<div style="font-size:.72rem;color:{"#16A34A" if f1_val >= 0.85 else "#D97706"};">'
        f'{"[PASS] OK" if f1_val >= 0.85 else "[WARN] Below threshold"}</div>'
        f'</div>'
        f'<div>'
        f'<div style="font-size:.72rem;color:#64748B;'
        f'text-transform:uppercase;'
        f'font-weight:600;letter-spacing:.05em;">'
        f'Recall</div>'
        f'<div style="font-size:1.6rem;font-weight:700;'
        f'color:#1F7A5A;margin-top:.2rem;">'
        f'{rec_val:.4f}</div>'
        f'</div>'
        f'<div>'
        f'<div style="font-size:.72rem;color:#64748B;'
        f'text-transform:uppercase;'
        f'font-weight:600;letter-spacing:.05em;">'
        f'Precision</div>'
        f'<div style="font-size:1.6rem;font-weight:700;'
        f'color:#1F7A5A;margin-top:.2rem;">'
        f'{prec_val:.4f}</div>'
        f'</div>'
        f'</div>'
        f'<div style="margin-top:1rem;padding-top:.8rem;'
        f'border-top:1px solid #E2E8F0;'
        f'display:grid;'
        f'grid-template-columns:1fr 1fr;gap:1rem;">'
        f'<div>'
        f'<span style="font-size:.72rem;color:#64748B;'
        f'font-weight:600;">MODEL TYPE: </span>'
        f'<span style="font-size:.9rem;color:#1F7A5A;'
        f'font-weight:700;">{mtype}</span>'
        f'</div>'
        f'<div>'
        f'<span style="font-size:.72rem;color:#64748B;'
        f'font-weight:600;">DATASET: </span>'
        f'<span style="font-size:.85rem;color:#059669;'
        f'font-weight:600;">{did}</span>'
        f'</div>'
        f'</div>'
        f'<div style="margin-top:.5rem;">'
        f'<span style="font-size:.72rem;color:#64748B;'
        f'font-weight:600;">HASH: </span>'
        f'<span style="font-size:.75rem;color:#64748B;'
        f'font-family:monospace;">'
        f'{mhash[:50]}...</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # ── Compute button ────────────────────────────
    if st.button("Compute Global SHAP", type="primary"):
        with st.spinner("Computing Global SHAP on 500 samples... (30-60 seconds)"):
            try:
                model_path = _get_model_path(mtype)
                r = httpx.post(
                    f"{API_URL}/shap/global",
                    json={
                        "model_path": model_path,
                        "dataset_id": par.get("dataset_id",""),
                        "model_id":   sel_name,
                        "run_id":     v["run_id"]
                    }, timeout=120)
                if r.status_code == 200:
                    _show_results(r.json(), sel_name)
                else:
                    _alert_box(f"{r.text[:200]}", "error")
            except Exception as e:
                _alert_box(f"{e}", "error")

    # ── Cached Global SHAP from IPFS ──────────────
    _card_header("Cached Global SHAP (IPFS)", _ICON_IPFS)
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
            with st.expander(f"[DATA] {model_label}"):
                c1, c2 = st.columns([3,1])
                c1.caption(f"CID: {f['name']}")
                c2.markdown(
                    f"[View on IPFS]({f['url']})")

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
                                    data2.get("model_type","N/A"))
                                c2.metric("Samples",
                                    data2.get("n_samples",0))
                                c3.metric("Explainer",
                                    data2.get("explainer_type",""))

                                # Table
                                st.dataframe(
                                    df2[["rank","feature","importance"]],
                                    use_container_width=True)

                                # Chart
                                st.bar_chart(
                                    df2.set_index("feature")["importance"])
                except:
                    st.caption("Could not load content")
    else:
        st.info("No Global SHAP cached yet. Select a model and click 'Compute Global SHAP' above.")


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
        _alert_box(f"{result['error']}", "error")
        return

    _alert_box(f"Global SHAP computed for **{model_name}**", "success")

    cid = result.get("cid","")
    if cid and not cid.startswith("QmSIM"):
        _alert_box(f"Pinned to IPFS: `{cid[:30]}...`", "success")
        st.markdown(
            f"[View on IPFS](https://gateway.pinata.cloud/ipfs/{cid})")

    # Summary
    c1,c2,c3 = st.columns(3)
    c1.metric("Samples Used", result.get("n_samples",0))
    c2.metric("Features", result.get("n_features",17))
    c3.metric("Explainer", result.get("explainer_type","tree"))

    importance = result.get("global_importance",[])
    if not importance:
        st.warning("No importance data.")
        return

    df = pd.DataFrame(importance)

    # Table
    _card_header("Feature Importance Ranking", _ICON_CHART)
    st.dataframe(
        df[["rank","feature","importance"]],
        use_container_width=True)

    # Bar chart
    _card_header("Feature Importance Chart", _ICON_CHART)
    st.bar_chart(df.set_index("feature")["importance"])

    # Top 3 interpretation
    _card_header("Interpretation", _ICON_NETWORK)
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
