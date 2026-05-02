"""Fraud Analyst — Amber Zone Alerts"""
import streamlit as st
import pika
import json
import httpx
from utils.api_client import API_URL

RABBIT_HOST = "rabbitmq"

def _get_alerts(limit=5) -> list:
    messages = []
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBIT_HOST,
                credentials=pika.PlainCredentials("guest", "guest"),
                connection_attempts=2, retry_delay=1))
        channel = connection.channel()
        channel.queue_declare(queue="amber_alerts", durable=True)
        while len(messages) < limit:
            method, props, body = channel.basic_get(
                queue="amber_alerts", auto_ack=True)
            if method is None:
                break
            try:
                msg = json.loads(body)
                messages.append(msg)
            except:
                pass
        connection.close()
    except Exception as e:
        st.warning(f"⚠️ RabbitMQ: {e}")
    return messages

def _get_count() -> int:
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBIT_HOST,
                credentials=pika.PlainCredentials("guest", "guest"),
                connection_attempts=2))
        channel = connection.channel()
        q = channel.queue_declare(queue="amber_alerts", durable=True, passive=True)
        count = q.method.message_count
        connection.close()
        return count
    except:
        return 0

def _validate(tx_id: str, decision: str, reason: str) -> bool:
    try:
        r = httpx.post(
            f"{API_URL}/transactions/{tx_id}/validate",
            json={"decision": decision, "reason": reason},
            timeout=10)
        return r.status_code == 200
    except:
        return False

def show(user: dict):
    st.title("🚨 Amber Zone Alerts")
    st.caption("Transactions requiring human review — score between 0.40 and 0.80")

    # Track validated tx in session
    if "validated_txs" not in st.session_state:
        st.session_state.validated_txs = set()

    count = _get_count()
    if count == 0 and not st.session_state.get("current_alerts"):
        st.success("✅ No pending amber alerts!")
        return

    st.error(f"⚠️ **{count} transaction(s)** remaining in queue")

    # Load new alerts if needed
    if "current_alerts" not in st.session_state or st.button("🔄 Load Next Alerts"):
        alerts = _get_alerts(limit=5)
        st.session_state.current_alerts = [
            a for a in alerts 
            if a.get("tx_id") not in st.session_state.validated_txs
        ]

    alerts = st.session_state.get("current_alerts", [])
    pending = [a for a in alerts if a.get("tx_id") not in st.session_state.validated_txs]

    if not pending:
        st.info("All loaded alerts processed. Click 'Load Next Alerts' for more.")
        st.session_state.current_alerts = []
        return

    for alert in pending:
        tx_id    = alert.get("tx_id", "")
        score    = alert.get("score", 0)
        amount   = alert.get("montant_mad", 0)
        top_feat = alert.get("top_features", [])
        ts       = alert.get("timestamp", "")[:16]

        with st.expander(
            f"🟡 **{tx_id}** — Score: {score:.4f} — {amount:,.0f} MAD — {ts}",
            expanded=True):

            c1, c2 = st.columns(2)
            c1.metric("🎯 Score", f"{score:.4f}")
            c2.metric("💰 Amount", f"{amount:,.0f} MAD")

            if top_feat:
                st.markdown("**🔍 Why flagged (SHAP):**")
                for feat in top_feat[:5]:
                    fname = feat.get("feature", "")
                    shap  = feat.get("shap_value", feat.get("importance", 0))
                    color = "#DC2626" if shap > 0 else "#16A34A"
                    st.markdown(
                        f"- `{fname}`: <span style='color:{color};font-weight:700;'>{shap:+.4f}</span>",
                        unsafe_allow_html=True)

            st.markdown("---")
            reason = st.text_area(
                "Justification (required)",
                placeholder="Explain your decision...",
                key=f"reason_{tx_id}",
                height=80)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔴 Confirm FRAUD",
                    key=f"fraud_{tx_id}",
                    type="primary",
                    use_container_width=True):
                    if len(reason) < 10:
                        st.error("⚠️ Min 10 chars required")
                    else:
                        if _validate(tx_id, "FRAUDE", reason):
                            st.session_state.validated_txs.add(tx_id)
                            st.error(f"🔴 **{tx_id}** → FRAUD confirmed!")
                            import time; time.sleep(1)
                            st.rerun()
            with col2:
                if st.button("🟢 Mark LEGITIMATE",
                    key=f"legit_{tx_id}",
                    use_container_width=True):
                    if len(reason) < 10:
                        st.error("⚠️ Min 10 chars required")
                    else:
                        if _validate(tx_id, "LEGITIME", reason):
                            st.session_state.validated_txs.add(tx_id)
                            st.success(f"🟢 **{tx_id}** → LEGITIMATE confirmed!")
                            import time; time.sleep(1)
                            st.rerun()
