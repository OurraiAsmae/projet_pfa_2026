"""Data Scientist — Upload Dataset"""
import streamlit as st
import pandas as pd
from utils.api_client import (upload_dataset,
                               get_datasets,
                               get_dataset_analysis,
                               get_dataset_lineage,
                               API_URL)
import httpx

def show(user: dict):
    st.title("📊 Dataset Governance")
    st.info(
        "Complete Data Governance: "
        "Hash → Dataset Card IPFS → "
        "Feature Analysis → Blockchain")

    # ── Upload form ───────────────────────────────
    with st.form("up_ds"):
        c1,c2 = st.columns(2)
        f  = c1.file_uploader(
            "Upload CSV Dataset", type=["csv"])
        nm = c2.text_input(
            "Dataset Name",
            "transactions_bancaires")
        sub = st.form_submit_button(
            "🚀 Upload & Analyze",
            type="primary")

    if sub and f:
        with st.spinner(
            "Step 1: Hash → "
            "Step 2: IPFS Card → "
            "Step 3: Analysis → "
            "Step 4: Storage → "
            "Step 5: Blockchain..."):
            result = upload_dataset(
                f.getvalue(), f.name,
                nm, user["username"])

            if result.get("success"):
                st.success(
                    f"✅ Dataset registered: "
                    f"**{result['dataset_id']}**")
                st.balloons()

                # Metrics
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Version",
                    result["version"])
                c2.metric("Quality",
                    f"{result['quality_score']}/100 "
                    f"{result['quality_rating']}")
                c3.metric("Fraud Rate",
                    f"{result['fraud_rate']:.2%}")
                c4.metric("Rows",
                    f"{result['n_rows']:,}")

                # IPFS
                st.subheader("🌐 IPFS Storage")
                c1,c2 = st.columns(2)
                with c1:
                    st.markdown("**Dataset Card CID:**")
                    st.code(result["card_cid"])
                    st.markdown(
                        f"[🔗 View on IPFS]"
                        f"({result['card_ipfs_url']})")
                with c2:
                    st.markdown("**Analysis CID:**")
                    st.code(result.get(
                        "analysis_cid","N/A"))
                    st.markdown(
                        f"**Blockchain:** "
                        f"{result['blockchain']}")

                # Feature Importance
                if result.get("top_features"):
                    st.subheader(
                        "📊 Top Feature Importance")
                    df_fi = pd.DataFrame(
                        result["top_features"])
                    st.dataframe(
                        df_fi[["rank","feature",
                               "importance"]],
                        use_container_width=True)

                # Correlations
                if result.get("top_correlations"):
                    st.subheader(
                        "🔗 Top Correlations with Fraud")
                    df_c = pd.DataFrame(
                        result["top_correlations"])
                    st.dataframe(
                        df_c[["feature","correlation",
                              "direction"]],
                        use_container_width=True)

                # Traceability
                st.subheader("🔐 Traceability")
                st.code(
                    f"Dataset ID  : {result['dataset_id']}\n"
                    f"Hash DVC    : {result['hash']}\n"
                    f"Card CID    : {result['card_cid']}\n"
                    f"Version     : {result['version']}\n"
                    f"Uploaded by : {user['username']}\n"
                    f"Blockchain  : {result['blockchain']}")

            elif "already exists" in str(result):
                st.warning(
                    "⚠️ Dataset already exists "
                    "(same hash detected)")
                ex = result.get("existing",{})
                if ex:
                    st.info(
                        f"Existing: {ex.get('dataset_id')} "
                        f"v{ex.get('version')}")
            else:
                st.error(f"❌ {result}")

    elif sub:
        st.warning("Please upload a CSV file")

    # ── Registered Datasets ───────────────────────
    st.subheader("📦 Registered Datasets")
    datasets = get_datasets()

    if not datasets:
        st.info("No datasets registered yet. "
                "Upload your first dataset above.")
        return

    for ds in datasets:
        q    = ds.get("quality_score", 0)
        q_ic = ("✅" if q>=90 else
                "⚠️" if q>=70 else "❌")

        with st.expander(
            f"{q_ic} **{ds['dataset_id']}** "
            f"— {ds['version']} "
            f"— {ds.get('n_rows',0):,} rows "
            f"— Quality: {q}/100"):

            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Rows",
                f"{ds.get('n_rows',0):,}")
            c2.metric("Fraud Rate",
                f"{ds.get('fraud_rate',0):.2%}")
            c3.metric("Quality", f"{q}/100")
            c4.metric("Version",
                ds.get("version","v1"))

            st.caption(
                f"Uploaded by: "
                f"{ds.get('uploaded_by','N/A')} "
                f"| Date: "
                f"{str(ds.get('uploaded_at',''))[:10]}")

            # IPFS link
            cid = ds.get("card_cid","")
            if cid and not cid.startswith("QmSIM"):
                st.markdown(
                    f"🌐 **IPFS:** "
                    f"[{cid[:25]}...]"
                    f"(https://gateway.pinata.cloud"
                    f"/ipfs/{cid})")

            st.code(
                f"Hash: {ds.get('hash','N/A')}")

            col1, col2, col3 = st.columns(3)

            # Full Analysis
            if col1.button(
                "📊 Analysis",
                key=f"an_{ds['dataset_id']}"):
                an = get_dataset_analysis(
                    ds["dataset_id"])
                if an.get("feature_importance"):
                    st.subheader("Feature Importance")
                    df2 = pd.DataFrame(
                        an["feature_importance"])
                    st.dataframe(
                        df2[["rank","feature",
                             "importance"]],
                        use_container_width=True)
                if an.get("correlations"):
                    st.subheader(
                        "Correlations with Fraud")
                    df3 = pd.DataFrame(
                        an["correlations"])
                    st.dataframe(
                        df3[["feature","correlation",
                             "direction"]],
                        use_container_width=True)
                if an.get("quality"):
                    st.subheader("Quality Breakdown")
                    for k,v in an["quality"][
                            "breakdown"].items():
                        st.write(
                            f"{v['status']} **{k}**: "
                            f"{v['value']} "
                            f"({v['score']}/{v['max']})")

            # Lineage
            if col2.button(
                "🔗 Lineage",
                key=f"lin_{ds['dataset_id']}"):
                lin = get_dataset_lineage(
                    ds["dataset_id"])
                models = lin.get("models_trained",[])
                if models:
                    st.success(
                        f"Models trained on this dataset:\n"
                        + "\n".join(
                            f"  → {m}" for m in models))
                else:
                    st.info(
                        "No models trained on this "
                        "dataset yet")

            # Compare versions
            if col3.button(
                "⚖️ Compare",
                key=f"cmp_{ds['dataset_id']}"):
                all_ds = get_datasets()
                other  = [d["dataset_id"]
                          for d in all_ds
                          if d["dataset_id"] !=
                          ds["dataset_id"]]
                if other:
                    sel = st.selectbox(
                        "Compare with:",
                        other,
                        key=f"sel_{ds['dataset_id']}")
                    if st.button(
                        "Run Comparison",
                        key=f"run_{ds['dataset_id']}"):
                        try:
                            cmp = httpx.get(
                                f"{API_URL}/datasets/"
                                f"compare/"
                                f"{ds['dataset_id']}/"
                                f"{sel}",
                                timeout=10).json()
                            st.json(cmp)
                        except Exception as e:
                            st.error(f"❌ {e}")
                else:
                    st.info(
                        "Need at least 2 datasets "
                        "to compare")
