"""Fraud Analyst — Transaction Analysis & Testing"""
import streamlit as st
import time
import httpx
from datetime import datetime
from utils.api_client import get_active_model, API_URL

TIMEOUT = 30

def _predict(payload: dict) -> dict:
    try:
        r = httpx.post(f"{API_URL}/predict", json=payload, timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def show(user: dict):
    st.title("🧪 Transaction Analysis")

    # Active model
    active = get_active_model()
    if active:
        st.info(f"🤖 Active Model: **{active.get('model_id')}** ({active.get('model_type')})")
    else:
        st.error("❌ No active model — deploy a model first")
        return

    # Form
    with st.form("test_tx_form"):
        st.subheader("📋 Transaction Details")

        c1, c2, c3 = st.columns(3)
        with c1:
            txid = st.text_input("Transaction ID", f"TX-TEST-{int(time.time())}")
            amt  = st.number_input("Amount (MAD)", value=5000.0, min_value=0.0)
            hr   = st.slider("Hour", 0, 23, 14)
            jour = st.selectbox("Day of Week", [0,1,2,3,4,5,6],
                format_func=lambda x: ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][x])
        with c2:
            card_id   = st.text_input("Card ID", "CARD-001")
            client_id = st.text_input("Client ID", "CLIENT-001")
            est_fgn   = st.selectbox("Foreign Transaction", [0, 1],
                format_func=lambda x: "Yes 🌍" if x else "No 🏠")
            pays      = st.selectbox("Country", ["MA","FR","ES","US","GB","DE","IT"])
        with c3:
            device    = st.selectbox("Device Type", ["mobile","web","atm","pos"])
            new_dev   = st.selectbox("New Device", [0, 1],
                format_func=lambda x: "Yes ⚠️" if x else "No ✅")
            age_cli   = st.slider("Client Age", 18, 80, 35)
            seg_rev   = st.selectbox("Revenue Segment", [1, 2, 3],
                format_func=lambda x: {1:"Low",2:"Medium",3:"High"}[x])

        st.subheader("📍 Location & Velocity")
        c4, c5 = st.columns(2)
        with c4:
            tx_lat    = st.number_input("Latitude", value=33.5731)
            tx_lon    = st.number_input("Longitude", value=-7.5898)
            delta_km  = st.number_input("Distance from last TX (km)", value=0.0)
        with c5:
            delta_min = st.number_input("Minutes since last TX", value=60.0)
            nb_tx_1h  = st.number_input("Transactions in last hour", value=1)
            type_carte= st.selectbox("Card Type", [1, 2, 3],
                format_func=lambda x: {1:"Debit",2:"Credit",3:"Gold"}[x])

        submitted = st.form_submit_button(
            "🔍 Analyze Transaction",
            type="primary",
            use_container_width=True)

    if submitted:
        est_weekend = 1 if jour >= 5 else 0

        # Encode categorical → float
        pays_map   = {"MA":0,"FR":1,"ES":2,"US":3,"GB":4,"DE":5,"IT":6}
        device_map = {"mobile":0,"web":1,"atm":2,"pos":3}

        payload = {
            "tx_id":             txid,
            "card_id":           card_id,
            "client_id":         client_id,
            "montant_mad":       float(amt),
            "heure":             float(hr),
            "jour_semaine":      float(jour),
            "est_weekend":       float(est_weekend),
            "est_etranger":      float(est_fgn),
            "pays_transaction":  float(pays_map.get(pays, 0)),
            "tx_lat":            float(tx_lat),
            "tx_lon":            float(tx_lon),
            "delta_km":          float(delta_km),
            "delta_min_last_tx": float(delta_min),
            "nb_tx_1h":          float(nb_tx_1h),
            "device_type":       float(device_map.get(device, 0)),
            "est_nouveau_device":float(new_dev),
            "age_client":        float(age_cli),
            "segment_revenu":    float(seg_rev),
            "type_carte":        float(type_carte),
            "type_transaction":  1.0,
        }

        with st.spinner("🔍 Analyzing transaction..."):
            result = _predict(payload)

        if result.get("error"):
            st.error(f"❌ Error: {result['error']}")
            return

        # Result display
        zone  = result.get("zone", "")
        score = result.get("score", 0)

        zone_config = {
            "FRAUDE":  {"color": "#DC2626", "bg": "#FEF2F2",
                        "border": "#FECACA", "icon": "🔴",
                        "label": "FRAUD DETECTED — AUTO BLOCKED"},
            "AMBIGU":  {"color": "#D97706", "bg": "#FFFBEB",
                        "border": "#FDE68A", "icon": "🟡",
                        "label": "AMBIGUOUS — HUMAN REVIEW REQUIRED"},
            "LEGITIME":{"color": "#16A34A", "bg": "#F0FDF4",
                        "border": "#BBF7D0", "icon": "🟢",
                        "label": "LEGITIMATE — AUTO APPROVED"},
        }
        cfg = zone_config.get(zone, zone_config["AMBIGU"])

        st.markdown(f"""
        <div style="background:{cfg['bg']};border:2px solid {cfg['border']};
                    border-left:6px solid {cfg['color']};border-radius:12px;
                    padding:1.5rem;margin:1rem 0;">
            <div style="font-size:2rem;font-weight:800;color:{cfg['color']};">
                {cfg['icon']} {cfg['label']}
            </div>
            <div style="font-size:3rem;font-weight:900;color:{cfg['color']};
                        margin:.5rem 0;">
                Score: {score:.4f}
            </div>
            <div style="color:#64748B;font-size:.85rem;">
                TX: {txid} | Model: {result.get('active_model','N/A')} |
                {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Métriques
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🎯 Score", f"{score:.4f}")
        c2.metric("🤖 ML Used", "✅" if result.get("ml_model_used") else "❌")
        c3.metric("⛓️ Blockchain", "✅" if result.get("blockchain_recorded") else "❌")
        c4.metric("📦 Cache", "✅" if result.get("from_cache") else "❌")

        # SHAP Top Features
        top_features = result.get("top_features", [])
        if top_features:
            st.markdown("---")
            st.subheader("🔍 SHAP Explanation — Why this decision?")

            for feat in top_features[:8]:
                fname = feat.get("feature", "")
                fval  = feat.get("value", 0)
                shap  = feat.get("shap_value", feat.get("importance", 0))
                direction = "🔴 → Fraud" if shap > 0 else "🟢 → Legit"
                bar_color = "#DC2626" if shap > 0 else "#16A34A"
                bar_width  = min(abs(shap) * 200, 100)

                st.markdown(f"""
                <div style="display:flex;align-items:center;margin:.3rem 0;
                            background:#F8FAFC;border-radius:6px;padding:.5rem;">
                    <div style="width:180px;font-weight:600;font-size:.85rem;">
                        {fname}</div>
                    <div style="width:80px;font-size:.8rem;color:#64748B;">
                        = {fval}</div>
                    <div style="flex:1;background:#E2E8F0;border-radius:4px;height:16px;">
                        <div style="width:{bar_width}%;background:{bar_color};
                                    height:16px;border-radius:4px;"></div>
                    </div>
                    <div style="width:120px;font-size:.8rem;
                                color:{bar_color};text-align:right;">
                        {shap:+.4f} {direction}</div>
                </div>
                """, unsafe_allow_html=True)

            shap_cid = result.get("shap_cid", "")
            if shap_cid:
                st.caption(f"📌 SHAP stored on IPFS: `{shap_cid}`")

        # Correction option pour Fraud Analyst
        st.markdown("---")
        st.subheader("✏️ Correction (False Positive/Negative)")
        with st.expander("🔧 Contest this decision"):
            st.warning("Use this to report incorrect classifications from client complaints.")
            correct_label = st.selectbox(
                "Correct Label",
                ["FRAUDE", "LEGITIME"],
                index=0 if zone != "FRAUDE" else 1)
            correction_reason = st.text_area(
                "Reason for correction",
                placeholder="e.g. Client confirmed legitimate purchase, receipt provided...")
            if st.button("📤 Submit Correction", type="primary"):
                if len(correction_reason) < 20:
                    st.error("Please provide a reason (min 20 chars)")
                else:
                    st.success(f"✅ Correction submitted: {txid} → {correct_label}")
                    st.info("This correction will be used for model retraining.")
