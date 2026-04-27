"""Fraud Analyst — Amber Zone Alerts"""
import streamlit as st
import pika
import json
import httpx
from datetime import datetime
from utils.api_client import API_URL

RABBIT_HOST = "rabbitmq"
TIMEOUT = 10

def _get_amber_alerts() -> list:
    """Get Amber Zone alerts from RabbitMQ"""
    messages = []
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBIT_HOST,
                credentials=pika.PlainCredentials("guest", "guest"),
                connection_attempts=2,
                retry_delay=1))
        channel = connection.channel()
        channel.queue_declare(queue="amber_alerts", durable=True)

        while True:
            method, props, body = channel.basic_get(
                queue="amber_alerts", auto_ack=False)
            if method is None:
                break
            try:
                msg = json.loads(body)
                messages.append((method.delivery_tag, msg))
            except:
                channel.basic_ack(method.delivery_tag)

        connection.close()
    except Exception as e:
        st.warning(f"⚠️ RabbitMQ: {e}")
    return messages


def _get_amber_count() -> int:
    """Get count of pending amber alerts"""
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBIT_HOST,
                credentials=pika.PlainCredentials("guest", "guest"),
                connection_attempts=2))
        channel = connection.channel()
        q = channel.queue_declare(
            queue="amber_alerts", durable=True, passive=True)
        count = q.method.message_count
        connection.close()
        return count
    except:
        return 0


def _validate_transaction(tx_id: str, decision: str, reason: str) -> bool:
    """Submit manual decision for amber transaction"""
    try:
        r = httpx.post(
            f"{API_URL}/transactions/{tx_id}/validate",
            json={"decision": decision, "reason": reason},
            timeout=TIMEOUT)
        return r.status_code == 200
    except:
        return False


def show(user: dict):
    st.title("🚨 Amber Zone Alerts")
    st.caption("Transactions requiring human review — score between 0.40 and 0.85")

    # Count
    count = _get_amber_count()

    if count == 0:
        st.success("✅ No pending amber alerts — all transactions processed!")
        return

    st.error(f"⚠️ **{count} transaction(s)** require your review")

    # Get alerts
    alerts = _get_amber_alerts()

    if not alerts:
        st.info("Alerts are being processed...")
        return

    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBIT_HOST,
                credentials=pika.PlainCredentials("guest", "guest"),
                connection_attempts=2))
        channel = connection.channel()

        for delivery_tag, alert in alerts:
            tx_id    = alert.get("tx_id", "")
            score    = alert.get("score", 0)
            amount   = alert.get("montant_mad", 0)
            country  = alert.get("pays_transaction", "")
            device   = alert.get("device_type", "")
            hour     = alert.get("heure", 0)
            ts       = alert.get("timestamp", "")[:16]
            top_feat = alert.get("top_features", [])

            with st.expander(
                f"🟡 **{tx_id}** — Score: {score:.4f} — {amount:,.0f} MAD — {ts}",
                expanded=True):

                # Transaction details
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("🎯 Score",   f"{score:.4f}")
                c2.metric("💰 Amount",  f"{amount:,.0f} MAD")
                c3.metric("🌍 Country", str(country))
                c4.metric("📱 Device",  str(device))

                # SHAP features
                if top_feat:
                    st.markdown("**🔍 Why flagged (SHAP):**")
                    for feat in top_feat[:5]:
                        fname = feat.get("feature", "")
                        shap  = feat.get("shap_value",
                                feat.get("importance", 0))
                        color = "#DC2626" if shap > 0 else "#16A34A"
                        st.markdown(
                            f"- `{fname}`: "
                            f"<span style='color:{color};font-weight:700;'>"
                            f"{shap:+.4f}</span>",
                            unsafe_allow_html=True)

                st.markdown("---")
                st.markdown("**📋 Your Decision:**")

                col1, col2 = st.columns(2)
                reason = st.text_area(
                    "Justification",
                    placeholder="Explain your decision...",
                    key=f"reason_{delivery_tag}")

                with col1:
                    if st.button(
                        "🔴 Confirm FRAUD",
                        key=f"fraud_{delivery_tag}",
                        type="primary",
                        use_container_width=True):
                        if len(reason) < 10:
                            st.error("Please provide a justification")
                        else:
                            channel.basic_ack(delivery_tag)
                            st.error(f"🔴 **{tx_id}** confirmed as FRAUD")
                            st.rerun()

                with col2:
                    if st.button(
                        "🟢 Mark LEGITIMATE",
                        key=f"legit_{delivery_tag}",
                        use_container_width=True):
                        if len(reason) < 10:
                            st.error("Please provide a justification")
                        else:
                            channel.basic_ack(delivery_tag)
                            st.success(f"🟢 **{tx_id}** marked as LEGITIMATE")
                            st.rerun()

        connection.close()

    except Exception as e:
        st.error(f"❌ Error: {e}")
