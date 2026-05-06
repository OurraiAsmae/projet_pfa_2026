"""Data Scientist — Upload Dataset"""
import streamlit as st
import pandas as pd
from utils.api_client import (upload_dataset,
                               get_datasets,
                               get_dataset_analysis,
                               get_dataset_lineage,
                               API_URL)
import httpx

# --- SVG Icons ---
_ICON_DB = '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#1F7A5A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>'
_ICON_SUCCESS = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'
_ICON_WARNING = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
_ICON_ERROR = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>'
_ICON_IPFS = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>'
_ICON_BLOCKCHAIN = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M3 15h18"/><path d="M9 3v18"/><path d="M15 3v18"/></svg>'
_ICON_LINK = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>'
_ICON_CHART = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1F7A5A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'

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

def show(user: dict):
    _header(
        "Dataset Governance",
        "Complete Data Governance: Hash → Dataset Card IPFS → Feature Analysis → Blockchain",
        _ICON_DB
    )

    # ── Upload form ───────────────────────────────
    with st.form("up_ds"):
        c1,c2 = st.columns(2)
        f  = c1.file_uploader(
            "Upload CSV Dataset", type=["csv"])
        nm = c2.text_input(
            "Dataset Name",
            "transactions_bancaires")
        sub = st.form_submit_button(
            "Upload & Analyze",
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
                st.markdown(f"""
                    <div style="padding:1rem;background-color:#ECFDF5;border-left:4px solid #10B981;border-radius:0.5rem;display:flex;align-items:center;gap:0.75rem;margin-bottom:1rem;">
                        {_ICON_SUCCESS}
                        <div style="color:#065F46;font-weight:500;">Dataset registered: <strong>{result['dataset_id']}</strong></div>
                    </div>
                """, unsafe_allow_html=True)

                # Metrics
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Version",
                    result["version"])
                c2.metric("Quality",
                    f"{result['quality_score']}/100 "
                    f"{result['quality_rating'].replace('✅', '').replace('⚠️', '').replace('❌', '')}")
                c3.metric("Fraud Rate",
                    f"{result['fraud_rate']:.2%}")
                c4.metric("Rows",
                    f"{result['n_rows']:,}")

                # IPFS
                _card_header("Distributed Storage", _ICON_IPFS)
                c1,c2 = st.columns(2)
                with c1:
                    st.markdown("**Dataset Card CID:**")
                    st.code(result["card_cid"])
                    st.markdown(
                        f"[View on IPFS]({result['card_ipfs_url']})")
                with c2:
                    st.markdown("**Analysis CID:**")
                    st.code(result.get("analysis_cid","N/A"))
                    st.markdown(f"**Blockchain tx:** {result['blockchain']}")

                # Feature Importance
                if result.get("top_features"):
                    _card_header("Top Feature Importance", _ICON_CHART)
                    df_fi = pd.DataFrame(
                        result["top_features"])
                    st.dataframe(
                        df_fi[["rank","feature","importance"]],
                        use_container_width=True)

                # Correlations
                if result.get("top_correlations"):
                    _card_header("Top Correlations with Fraud", _ICON_LINK)
                    df_c = pd.DataFrame(
                        result["top_correlations"])
                    st.dataframe(
                        df_c[["feature","correlation","direction"]],
                        use_container_width=True)

                # Traceability
                _card_header("Traceability Record", _ICON_BLOCKCHAIN)
                st.code(
                    f"Dataset ID  : {result['dataset_id']}\n"
                    f"Hash DVC    : {result['hash']}\n"
                    f"Card CID    : {result['card_cid']}\n"
                    f"Version     : {result['version']}\n"
                    f"Uploaded by : {user['username']}\n"
                    f"Blockchain  : {result['blockchain']}")

            elif "already exists" in str(result):
                st.markdown(f"""
                    <div style="padding:1rem;background-color:#FFFBEB;border-left:4px solid #F59E0B;border-radius:0.5rem;display:flex;align-items:center;gap:0.75rem;margin-bottom:1rem;">
                        {_ICON_WARNING}
                        <div style="color:#92400E;font-weight:500;">Dataset already exists (same hash detected)</div>
                    </div>
                """, unsafe_allow_html=True)
                ex = result.get("existing",{})
                if ex:
                    st.info(
                        f"Existing record: {ex.get('dataset_id')} "
                        f"v{ex.get('version')}")
            else:
                st.markdown(f"""
                    <div style="padding:1rem;background-color:#FEF2F2;border-left:4px solid #EF4444;border-radius:0.5rem;display:flex;align-items:center;gap:0.75rem;margin-bottom:1rem;">
                        {_ICON_ERROR}
                        <div style="color:#991B1B;font-weight:500;">Error: {result}</div>
                    </div>
                """, unsafe_allow_html=True)

    elif sub:
        st.markdown(f"""
            <div style="padding:1rem;background-color:#FFFBEB;border-left:4px solid #F59E0B;border-radius:0.5rem;display:flex;align-items:center;gap:0.75rem;margin-bottom:1rem;">
                {_ICON_WARNING}
                <div style="color:#92400E;font-weight:500;">Please upload a CSV file</div>
            </div>
        """, unsafe_allow_html=True)


    # ── Registered Datasets ───────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    _card_header("Registered Datasets", _ICON_DB)
    datasets = get_datasets()

    if not datasets:
        st.info("No datasets registered yet. Upload your first dataset above.")
        return

    for ds in datasets:
        q    = ds.get("quality_score", 0)
        q_label = ("[SUCCESS]" if q>=90 else "[WARNING]" if q>=70 else "[ERROR]")

        with st.expander(
            f"{q_label} {ds['dataset_id']} "
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
                    f"**IPFS Record:** "
                    f"[{cid[:25]}...]"
                    f"(https://gateway.pinata.cloud/ipfs/{cid})")

            st.code(
                f"Hash: {ds.get('hash','N/A')}")

            col1, col2, col3 = st.columns(3)

            # Full Analysis
            if col1.button("Run Analysis", key=f"an_{ds['dataset_id']}"):
                an = get_dataset_analysis(
                    ds["dataset_id"])
                if an.get("feature_importance"):
                    _card_header("Feature Importance", _ICON_CHART)
                    df2 = pd.DataFrame(
                        an["feature_importance"])
                    st.dataframe(
                        df2[["rank","feature","importance"]],
                        use_container_width=True)
                if an.get("correlations"):
                    _card_header("Correlations with Fraud", _ICON_LINK)
                    df3 = pd.DataFrame(
                        an["correlations"])
                    st.dataframe(
                        df3[["feature","correlation","direction"]],
                        use_container_width=True)
                if an.get("quality"):
                    _card_header("Quality Breakdown", _ICON_DB)
                    for k,v in an["quality"]["breakdown"].items():
                        st.write(
                            f"[{v['status'].replace('✅', 'OK').replace('⚠️', 'WARN').replace('❌', 'FAIL')}] "
                            f"**{k}**: {v['value']} ({v['score']}/{v['max']})")

            # Lineage
            if col2.button("View Lineage", key=f"lin_{ds['dataset_id']}"):
                lin = get_dataset_lineage(
                    ds["dataset_id"])
                models = lin.get("models_trained",[])
                if models:
                    st.markdown(f"""
                        <div style="padding:1rem;background-color:#ECFDF5;border-left:4px solid #10B981;border-radius:0.5rem;margin-bottom:1rem;">
                            <div style="color:#065F46;font-weight:600;margin-bottom:0.5rem;">Models trained on this dataset:</div>
                            <ul style="color:#065F46;margin:0;">
                                {"".join(f"<li>{m}</li>" for m in models)}
                            </ul>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("No models trained on this dataset yet")

            # Compare versions
            if col3.button("Compare Versions", key=f"cmp_{ds['dataset_id']}"):
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
                                f"{API_URL}/datasets/compare/{ds['dataset_id']}/{sel}",
                                timeout=10).json()
                            st.json(cmp)
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.info("Need at least 2 datasets to compare")
