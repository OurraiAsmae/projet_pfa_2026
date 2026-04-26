"""Fraud Analyst — Test Transaction"""
import streamlit as st
import time
from utils.api_client import predict, get_active_model

def show(user: dict):
    st.title("🧪 Transaction Analysis")

    active = get_active_model()
    if active:
        st.info(
            f"🤖 Active Model: "
            f"**{active.get('model_id')}** "
            f"({active.get('model_type')})")

    with st.form("test_tx"):
        c1,c2,c3 = st.columns(3)
        with c1:
            txid = st.text_input(
                "Transaction ID",
                f"TX-{int(time.time())}")
            amt  = st.number_input(
                "Amount (MAD)", value=5000.0)
            hr   = st.slider("Hour", 0, 23, 14)
        with c2:
            cid2 = st.text_input("Card ID","CARD-001")
            cli  = st.text_input("Client ID","CLIENT-001")
            fgn  = st.selectbox(
                "Foreign Transaction",[0,1])
        with c3:
            dist = st.number_input(
                "Distance (km)", value=5.0)
            ntx  = st.number_input(
                "Tx/hour", value=1.0)
            ndev = st.selectbox("New Device",[0,1])

        sub = st.form_submit_button(
            "🔍 Analyze", type="primary")

    if sub:
        with st.spinner("Analyzing..."):
            result = predict({
                "tx_id":            txid,
                "montant_mad":      amt,
                "card_id":          cid2,
                "client_id":        cli,
                "heure":            float(hr),
                "est_etranger":     float(fgn),
                "delta_km":         float(dist),
                "nb_tx_1h":         float(ntx),
                "est_nouveau_device": float(ndev)
            })

            if result.get("error"):
                st.error(f"❌ {result['error']}")
                return

            zone   = result["zone"]
            labels = {
                "FRAUDE":  "🔴 FRAUD",
                "AMBIGU":  "🟡 AMBIGUOUS",
                "LEGITIME":"🟢 LEGITIMATE"
            }
            st.subheader(
                f"Decision: **{labels.get(zone,zone)}**")

            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Risk Score",
                f"{result['score']:.4f}")
            c2.metric("ML Model",
                "✅" if result["ml_model_used"]
                else "❌")
            c3.metric("Blockchain",
                "✅" if result["blockchain_recorded"]
                else "⚠️")
            c4.metric("Model",
                result.get("active_model","N/A"))

            # SHAP
            if result.get("top_features"):
                st.subheader("🔍 SHAP Explanation")
                for f2 in result["top_features"][:5]:
                    d2 = ("🔴 → FRAUD"
                          if f2["shap_value"]>0
                          else "🟢 → LEGITIMATE")
                    st.write(
                        f"**{f2['feature']}**: "
                        f"{f2['shap_value']:+.4f} {d2}")

            # IPFS
            cid = result.get("shap_cid","")
            url = result.get("shap_ipfs_url","")
            if url:
                st.markdown(
                    f"[🌐 SHAP on IPFS]({url})")
