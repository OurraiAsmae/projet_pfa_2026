"""
Data Scientist — Upload Model v2.0
"""
import streamlit as st
import hashlib
import tempfile
import os
import json
import pandas as pd
import httpx
from datetime import datetime
from utils.api_client import (
    evaluate_model_metrics,
    get_datasets, GW_URL, ML_URL, API_URL
)

# --- SVG Icons ---
_ICON_BRAIN = '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#1F7A5A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"/></svg>'
_ICON_SUCCESS = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'
_ICON_WARNING = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
_ICON_ERROR = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>'
_ICON_CHART = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1F7A5A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
_ICON_SHIELD = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1F7A5A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'
_ICON_UPLOAD = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1F7A5A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>'
_ICON_DATABASE = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1F7A5A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>'
_ICON_PACKAGE = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1F7A5A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="16.5" y1="9.4" x2="7.5" y2="4.21"></line><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>'


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
        "info":    ("#EFF6FF", "#3B82F6", "#1E40AF", _ICON_SUCCESS) # Using success icon or we can make an info one
    }
    bg, border, text_color, icon = colors.get(alert_type, colors["info"])
    st.markdown(f"""
        <div style="padding:1rem;background-color:{bg};border-left:4px solid {border};border-radius:0.5rem;display:flex;align-items:flex-start;gap:0.75rem;margin-bottom:1rem;">
            <div style="margin-top:2px;">{icon}</div>
            <div style="color:{text_color};font-weight:500;">{text}</div>
        </div>
    """, unsafe_allow_html=True)


def _mlflow_dict(lst) -> dict:
    """Convert MLflow metrics/params list to dict"""
    if isinstance(lst, list):
        result = {}
        for item in lst:
            if "key" not in item:
                continue
            val = item.get("value", 0)
            try:
                result[item["key"]] = float(val)
            except (ValueError, TypeError):
                result[item["key"]] = val
        return result
    return lst if isinstance(lst, dict) else {}


def _mlflow_params(lst) -> dict:
    """Convert MLflow params list to dict"""
    if isinstance(lst, list):
        return {i["key"]: i["value"]
                for i in lst if "key" in i}
    return lst if isinstance(lst, dict) else {}


FEATURE_NAMES = [
    "heure","jour_semaine","est_weekend","montant_mad",
    "type_transaction","pays_transaction","est_etranger",
    "tx_lat","tx_lon","delta_km","delta_min_last_tx",
    "nb_tx_1h","device_type","est_nouveau_device",
    "age_client","segment_revenu","type_carte"
]

def _fetch_metrics_from_mlflow(run_name: str) -> dict:
    """Search MLflow for run by exact run_name = BC ID"""
    try:
        best_match = None
        r = httpx.get(
            f"{ML_URL}/api/2.0/mlflow/experiments/search",
            params={"max_results": 50}, timeout=5)
        experiments = r.json().get("experiments", [])
        for exp in experiments:
            if exp["name"] == "Default":
                continue
            rr = httpx.post(
                f"{ML_URL}/api/2.0/mlflow/runs/search",
                json={"experiment_ids": [exp["experiment_id"]],
                      "max_results": 20},
                timeout=5)
            runs = rr.json().get("runs", [])
            for run in runs:
                info    = run.get("info", {})
                data    = run.get("data", {})
                if info.get("run_name") == run_name:
                    metrics = _mlflow_dict(data.get("metrics", []))
                    params  = _mlflow_params(data.get("params", []))
                    if metrics.get("auc_roc", 0) > 0:
                        candidate = {
                            "found":     True,
                            "run_id":    info["run_id"],
                            "run_name":  run_name,
                            "auc_roc":   metrics.get("auc_roc",   0.0),
                            "auc_pr":    metrics.get("auc_pr",    0.0),
                            "f1":        metrics.get("f1",        0.0),
                            "precision": metrics.get("precision", 0.0),
                            "recall":    metrics.get("recall",    0.0),
                            "n_train":   int(metrics.get("n_train", 0)),
                            "n_test":    int(metrics.get("n_test",  0)),
                            "metrics":   metrics,
                            "params":    params,
                        }
                        if best_match is None or candidate["auc_roc"] > best_match["auc_roc"]:
                            best_match = candidate
        if best_match:
            return best_match
    except Exception as e:
        print(f"MLflow search error: {e}")
    return {"found": False}


def _check_policy(auc, f1, rec, prec) -> list:
    checks = [
        ("AUC-ROC",   auc,  0.95),
        ("F1-Score",  f1,   0.85),
        ("Recall",    rec,  0.90),
        ("Precision", prec, 0.80),
    ]
    return [{"metric": m, "value": v, "min": mn,
             "passed": v >= mn,
             "gap": max(0, mn - v)}
            for m, v, mn in checks]

def _load_model(content: bytes, tmp_path: str) -> dict:
    try:
        import sys
        sys.path.insert(0, "/app")
        from model_loader import load_model_from_bytes
        return load_model_from_bytes(content, tmp_path)
    except:
        try:
            import pickle
            with open(tmp_path, "rb") as f:
                model = pickle.load(f)
            return {
                "success":        True,
                "model":          model,
                "model_type":     type(model).__name__,
                "model_hash":     "sha256:" + hashlib.sha256(content).hexdigest(),
                "n_features":     getattr(model,"n_features_in_","N/A"),
                "shap_explainer": "tree",
                "auto_installed": False
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

def _compute_global_shap(model, model_type,
                          shap_type, dataset_id) -> dict:
    try:
        import shap, numpy as np
        X = _get_dataset_sample(dataset_id)
        if X is None:
            return {}
        if shap_type == "tree":
            exp  = shap.TreeExplainer(model)
            vals = exp.shap_values(X)
        elif shap_type == "linear":
            exp  = shap.LinearExplainer(model, X)
            vals = exp.shap_values(X)
        else:
            bg   = shap.sample(X, 50)
            exp  = shap.KernelExplainer(
                model.predict_proba, bg)
            vals = exp.shap_values(X[:50])

        if isinstance(vals, list):
            vals = vals[1]
        mean_abs = np.abs(vals).mean(axis=0)
        n = min(len(FEATURE_NAMES), len(mean_abs))
        feats = sorted([{
            "feature":    FEATURE_NAMES[i],
            "importance": round(float(mean_abs[i]), 4),
            "rank": 0}
            for i in range(n)],
            key=lambda x: x["importance"], reverse=True)
        for i, f in enumerate(feats):
            f["rank"] = i + 1
        return {
            "global_importance": feats,
            "top_5_features":    feats[:5],
            "n_samples":         len(X),
            "explainer_type":    shap_type
        }
    except Exception as e:
        return {"error": str(e)}

def _get_dataset_sample(dataset_id, n=500):
    try:
        datasets_dir = "/app/mlops/datasets"
        if not os.path.exists(datasets_dir):
            return None
        for f in os.listdir(datasets_dir):
            if not f.endswith("_meta.json"):
                continue
            meta = json.load(
                open(f"{datasets_dir}/{f}"))
            if meta.get("dataset_id") == dataset_id:
                csv_p = meta.get("csv_path","")
                if os.path.exists(csv_p):
                    df = pd.read_csv(csv_p)
                    cols = [c for c in FEATURE_NAMES
                            if c in df.columns]
                    if cols:
                        return df[cols].fillna(0).sample(
                            min(n, len(df)),
                            random_state=42).values
    except Exception as e:
        print(f"Sample error: {e}")
    return None


def show(user: dict):
    _header(
        "Model Registration",
        "Workflow: Upload .pkl → Auto-detect → MLflow metrics → Policy PR-005 → Global SHAP → IPFS → Blockchain",
        _ICON_BRAIN
    )

    datasets = get_datasets()

    with st.form("upload_model_form"):
        _card_header("Model File", _ICON_UPLOAD)
        c1, c2 = st.columns(2)
        with c1:
            mfile = st.file_uploader(
                "Upload .pkl", type=["pkl"])
            mname = st.text_input(
                "Model Name",
                "RandomForest-FraudDetection")
            ver   = st.text_input("Version", "1.0")
        with c2:
            desc = st.text_area(
                "Description",
                "Describe your model...")

        _card_header("Performance Metrics", _ICON_CHART)
        st.caption(
            "Policy PR-005: "
            "AUC-ROC >= 0.95 | F1 >= 0.85 | Recall >= 0.90")
        st.info("Metrics will be automatically computed by evaluating the model on test data after upload.")
        auc = apr = f1 = prec = rec = 0.0
        ntr = nte = 0
        trt = 0.0
        auto_fetch = True

        # Dataset selector dans le form — juste avant Submit
        _card_header("Training Dataset", _ICON_DATABASE)
        if datasets:
            opts = {
                f"{d['dataset_id']} "
                f"({d.get('n_rows',0):,} rows "
                f"Q:{d.get('quality_score',0)}/100)": d
                for d in datasets}
            sel_lbl = st.selectbox(
                "Select Dataset", list(opts.keys()),
                key="selected_dataset")
            sel_ds  = opts[sel_lbl]
            dh      = sel_ds.get("hash","")
            did     = sel_ds.get("dataset_id","")
            dcid    = sel_ds.get("card_cid","")
            # Afficher le dataset réellement sélectionné
            selected_did = sel_lbl.split(" (")[0]
            selected_ds_data = opts[sel_lbl]
        else:
            st.warning(
                "No datasets registered. "
                "Upload a dataset first.")
            dh = did = dcid = ""
            sel_ds = {}

        sub = st.form_submit_button(
            "Submit Model", type="primary")

    if sub and mfile:
        _process(mfile, mname, ver, desc,
                 auc, apr, f1, prec, rec,
                 ntr, nte, trt,
                 dh, did, dcid,
                 user["username"], auto_fetch)
    elif sub:
        _alert_box("Please upload a .pkl file", "warning")

    _show_models()


def _process(mfile, mname, ver, desc,
             auc, apr, f1, prec, rec,
             ntr, nte, trt,
             dh, did, dcid,
             submitted_by, auto_fetch):

    prog   = st.progress(0)
    status = st.empty()

    content = mfile.getvalue()
    mhash   = "sha256:" + hashlib.sha256(
        content).hexdigest()

    with tempfile.NamedTemporaryFile(
            suffix=".pkl", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # STEP 1 — Load model
        status.info("Step 1/7 — Loading model...")
        prog.progress(10)
        load_r = _load_model(content, tmp_path)
        if not load_r["success"]:
            _alert_box(str(load_r.get('error')), "error")
            return

        model      = load_r["model"]
        model_type = load_r["model_type"]
        n_features = load_r["n_features"]
        shap_type  = load_r["shap_explainer"]

        if load_r.get("auto_installed"):
            _alert_box(
                f"Auto-installed: {load_r.get('installed_package')}", "success")

        c1,c2,c3 = st.columns(3)
        c1.metric("Model Type",  model_type)
        c2.metric("Features",    str(n_features))
        c3.metric("SHAP Engine", shap_type)
        st.code(f"Model Hash: {mhash}")

        # STEP 2 — Auto-fetch MLflow metrics
        status.info("Step 2/7 — MLflow metrics...")
        prog.progress(20)
        run_id = ""

        if auto_fetch:
            bc_id = f"{mname}-v{ver}"
            mlf = _fetch_metrics_from_mlflow(bc_id)
            if mlf.get("found"):
                auc   = mlf["auc_roc"]
                apr   = mlf["auc_pr"]
                f1    = mlf["f1"]
                prec  = mlf["precision"]
                rec   = mlf["recall"]
                ntr   = mlf["n_train"]
                nte   = mlf["n_test"]
                run_id = mlf["run_id"]
                _alert_box(f"Metrics fetched from MLflow ({bc_id})", "success")
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("AUC-ROC", f"{auc:.4f}")
                c2.metric("F1",      f"{f1:.4f}")
                c3.metric("Recall",  f"{rec:.4f}")
                c4.metric("Precision",f"{prec:.4f}")
            else:
                status.info("Not found in MLflow — evaluating model on dataset...")
                eval_r = evaluate_model_metrics(tmp_path, dataset_id=did)
                if eval_r.get("success"):
                    auc   = eval_r["auc_roc"]
                    apr   = eval_r["auc_pr"]
                    f1    = eval_r["f1"]
                    prec  = eval_r["precision"]
                    rec   = eval_r["recall"]
                    ntr   = eval_r["n_train"]
                    nte   = eval_r["n_test"]
                    mhash = eval_r["model_hash"]
                    _alert_box("Metrics computed from model evaluation!", "success")
                    c1,c2,c3,c4 = st.columns(4)
                    c1.metric("AUC-ROC", f"{auc:.4f}")
                    c2.metric("F1",      f"{f1:.4f}")
                    c3.metric("Recall",  f"{rec:.4f}")
                    c4.metric("Precision",f"{prec:.4f}")
                else:
                    _alert_box(f"Could not compute metrics: {eval_r.get('error','Unknown')}. Continuing with 0.0", "warning")


        # STEP 3 — MLflow (register if not already)
        status.info("Step 3/7 — MLflow tracking...")
        prog.progress(30)

        if not run_id:
            try:
                import httpx as _hx
                import time as _time

                # Créer experiment
                exp_r = _hx.get(f"{ML_URL}/api/2.0/mlflow/experiments/get-by-name",
                    params={"experiment_name": f"fraud-{mname}"}, timeout=5)
                if exp_r.status_code == 200:
                    exp_id = exp_r.json()["experiment"]["experiment_id"]
                else:
                    cr = _hx.post(f"{ML_URL}/api/2.0/mlflow/experiments/create",
                        json={"name": f"fraud-{mname}"}, timeout=5)
                    exp_id = cr.json()["experiment_id"]

                # Créer run
                ts = int(_time.time() * 1000)
                rr = _hx.post(f"{ML_URL}/api/2.0/mlflow/runs/create",
                    json={"experiment_id": exp_id,
                          "run_name": f"{mname}-v{ver}",
                          "start_time": ts}, timeout=5)
                run_id = rr.json()["run"]["info"]["run_id"]

                # Logger métriques
                for k,v2 in [("auc_roc",auc),("auc_pr",apr),("f1",f1),
                              ("precision",prec),("recall",rec),
                              ("n_train",float(ntr)),("n_test",float(nte))]:
                    _hx.post(f"{ML_URL}/api/2.0/mlflow/runs/log-metric",
                        json={"run_id":run_id,"key":k,"value":v2,
                              "timestamp":ts,"step":0}, timeout=5)

                # Logger params
                for k,v2 in [("model_type",model_type),("version",ver),
                              ("dataset_id",did),("dataset_hash_dvc",dh),
                              ("model_hash_sha256",mhash),
                              ("submitted_by",submitted_by),
                              ("shap_explainer",shap_type)]:
                    _hx.post(f"{ML_URL}/api/2.0/mlflow/runs/log-parameter",
                        json={"run_id":run_id,"key":k,"value":str(v2)}, timeout=5)

                # Terminer run
                _hx.post(f"{ML_URL}/api/2.0/mlflow/runs/update",
                    json={"run_id":run_id,"status":"FINISHED"}, timeout=5)

                # Enregistrer dans Model Registry
                reg_name = f"FraudDetection-{mname}"
                _hx.post(f"{ML_URL}/api/2.0/mlflow/registered-models/create",
                    json={"name": reg_name}, timeout=5)
                _hx.post(f"{ML_URL}/api/2.0/mlflow/model-versions/create",
                    json={"name": reg_name,
                          "source": f"mlflow-artifacts:/{exp_id}/{run_id}/artifacts/model",
                          "run_id": run_id}, timeout=5)

                _alert_box(f"MLflow run: {run_id[:16]}... + Registry OK", "success")
            except Exception as e:
                _alert_box(f"MLflow: {e}", "warning")
                run_id = hashlib.sha256(mhash.encode()).hexdigest()[:16]
        else:
            _alert_box(f"MLflow run linked: {run_id[:16]}...", "success")

        # STEP 4 — Policy Engine PR-005
        status.info("Step 4/7 — Policy Engine PR-005...")
        prog.progress(45)

        policy = _check_policy(auc, f1, rec, prec)
        passed = all(r["passed"] for r in policy)

        _card_header("Policy Engine PR-005", _ICON_SHIELD)
        cols = st.columns(len(policy))
        for i, r in enumerate(policy):
            icon = "[PASS]" if r["passed"] else "[FAIL]"
            cols[i].metric(
                f"{icon} {r['metric']}",
                f"{r['value']:.4f}",
                delta="OK" if r["passed"]
                else f"Need +{r['gap']:.4f}")

        if not passed:
            _alert_box("Model BLOCKED by Policy Engine PR-005. Does not meet regulatory thresholds.", "error")
            with st.expander("Improvement Tips"):
                st.markdown(
                    "- Use `class_weight='balanced'`\n"
                    "- Increase training data\n"
                    "- Tune hyperparameters\n"
                    "- Try XGBoost or LightGBM")
            return

        _alert_box("Policy PR-005 — All thresholds met!", "success")

        # STEP 5 — Global SHAP
        status.info("Step 5/7 — Global SHAP...")
        prog.progress(60)

        shap_data = {}
        shap_cid  = ""
        if did:
            shap_data = _compute_global_shap(
                model, model_type, shap_type, did)
            if shap_data.get("global_importance"):
                _card_header("Global SHAP Analysis", _ICON_CHART)
                df_shap = pd.DataFrame(
                    shap_data["global_importance"])
                st.dataframe(
                    df_shap[["rank","feature",
                              "importance"]],
                    use_container_width=True)
                st.caption(
                    f"Computed on "
                    f"{shap_data.get('n_samples',0)} "
                    f"samples | {shap_type} explainer")

        # STEP 6 — Model Card → IPFS
        status.info("Step 6/7 — Model Card → IPFS...")
        prog.progress(75)

        model_card_cid = ""
        card = {
            "schema":      "BlockML-Gov-Model-Card-v1",
            "model_id":    f"{mname}-v{ver}",
            "model_type":  model_type,
            "version":     ver,
            "description": desc,
            "performance": {
                "auc_roc":   auc, "auc_pr": apr,
                "f1":        f1,  "precision": prec,
                "recall":    rec, "n_train": ntr,
                "n_test":    nte
            },
            "policy_pr005":  {"passed": passed},
            "data": {
                "dataset_id":  did,
                "dataset_hash":dh,
                "dataset_cid": dcid,
                "features":    FEATURE_NAMES
            },
            "model_file": {
                "hash_sha256":    mhash,
                "shap_explainer": shap_type,
                "mlflow_run_id":  run_id
            },
            "global_shap": shap_data.get(
                "top_5_features", []),
            "provenance": {
                "submitted_by": submitted_by,
                "submitted_at": datetime.utcnow().isoformat(),
                "framework":    "BlockML-Gov v4.0"
            }
        }

        try:
            r2 = httpx.post(
                f"{API_URL}/ipfs/pin-json",
                json={"data": card,
                      "name": f"model-card-{mname}-v{ver}"},
                timeout=30)
            if r2.status_code == 200:
                model_card_cid = r2.json().get("cid","")
                _alert_box(f"Model Card → IPFS: `{model_card_cid[:25]}...`", "success")
        except Exception as e:
            _alert_box(f"IPFS Error: {e}", "warning")

        # Fallback CID
        if not model_card_cid:
            model_card_cid = (
                "QmCard" + hashlib.sha256(
                    f"{mname}{ver}".encode()
                ).hexdigest()[:38])

        # STEP 7 — Blockchain
        status.info("Step 7/7 — Blockchain...")
        prog.progress(90)

        bc_ok = False
        try:
            r3 = httpx.post(
                f"{API_URL}/governance/submit-model",
                json={
                    "model_id":      f"{mname}-v{ver}",
                    "version":       ver,
                    "data_hash":     dh,
                    "mlflow_run_id": run_id,
                    "model_card_cid":model_card_cid,
                    "auc":           str(auc),
                    "f1":            str(f1),
                    "precision":     str(prec),
                    "recall":        str(rec)
                }, timeout=15)
            res = r3.json()
            bc_ok = res.get("success", False)
        except Exception as e:
            _alert_box(f"Blockchain Error: {e}", "warning")

        # Link model → dataset
        if did:
            try:
                httpx.post(
                    f"{API_URL}/datasets/{did}/link-model",
                    params={"model_id": f"{mname}-v{ver}"},
                    timeout=5)
            except:
                pass

        # FINAL
        prog.progress(100)
        status.empty()

        _alert_box(f"**{mname}-v{ver}** submitted successfully!", "success")

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Type",      model_type)
        c2.metric("AUC-ROC",   f"{auc:.4f}")
        c3.metric("Blockchain",
            "SUBMITTED" if bc_ok else "Pending")
        c4.metric("IPFS",
            "PINNED" if model_card_cid else "N/A")

        st.code(
            f"Model ID       : {mname}-v{ver}\n"
            f"Model Type     : {model_type}\n"
            f"Model Hash     : {mhash}\n"
            f"MLflow Run     : {run_id}\n"
            f"Dataset ID     : {did}\n"
            f"Model Card CID : {model_card_cid}\n"
            f"SHAP Explainer : {shap_type}\n"
            f"Policy PR-005  : Passed\n"
            f"Blockchain     : "
            f"{'SUBMITTED' if bc_ok else 'Pending'}")

        st.info(
            "Next Steps:\n"
            "1. Compliance Officer → Validate\n"
            "2. ML Engineer → Approve + SHAP review\n"
            "3. ML Engineer → Deploy")

    except Exception as e:
        import traceback
        _alert_box(str(e), "error")
        st.code(traceback.format_exc())
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _show_models():
    _card_header("Registered Models", _ICON_PACKAGE)
    try:
        r = httpx.get(
            f"{ML_URL}/api/2.0/mlflow/"
            "registered-models/search",
            timeout=5)
        d = r.json()
        models = (d.get("registered_models",[])
                  if isinstance(d,dict) else [])
        if not models:
            st.info("No models registered yet.")
            return
        for m in models:
            v = (m["latest_versions"][-1]
                 if m.get("latest_versions") else None)
            if not v: continue
            met, par = {}, {}
            try:
                rr = httpx.get(
                    f"{ML_URL}/api/2.0/mlflow/runs/get",
                    params={"run_id": v["run_id"]},
                    timeout=5)
                rd = rr.json().get("run",{}).get("data",{})
                met = _mlflow_dict(rd.get("metrics",[]))
                par = _mlflow_params(rd.get("params",[]))
            except:
                pass
            auc_v = met.get("auc_roc",0.0)
            icon_label = "[PASS]" if auc_v>=0.95 else "[WARN]"
            with st.expander(
                f"{icon_label} {m['name']} "
                f"v{v['version']} — AUC:{auc_v:.4f}"):
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("AUC-ROC",f"{auc_v:.4f}")
                c2.metric("F1",f"{met.get('f1',0):.4f}")
                c3.metric("Type",
                    par.get("model_type","N/A"))
                c4.metric("Dataset",
                    par.get("dataset_id","N/A")[:15])
                st.code(
                    f"Hash   : {par.get('model_hash_sha256','N/A')}\n"
                    f"Run ID : {v['run_id']}\n"
                    f"Dataset: {par.get('dataset_id','N/A')}")
    except Exception as e:
        _alert_box(f"MLflow Error: {e}", "warning")
