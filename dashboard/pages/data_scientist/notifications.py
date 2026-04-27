"""Data Scientist — Rejection Notifications"""
import streamlit as st
import pika
import json
from datetime import datetime

RABBIT_HOST = "rabbitmq"

def _get_notifications() -> list:
    """Consume all messages from ds_notifications queue"""
    messages = []
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBIT_HOST,
                credentials=pika.PlainCredentials("guest", "guest"),
                connection_attempts=2,
                retry_delay=1))
        channel = connection.channel()
        channel.queue_declare(queue="ds_notifications", durable=True)

        while True:
            method, props, body = channel.basic_get(
                queue="ds_notifications", auto_ack=False)
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

def _ack_message(delivery_tag: int, connection):
    """Acknowledge message"""
    pass

def show_popup_if_notifications():
    """Show popup alert if there are pending notifications — called at login"""
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBIT_HOST,
                credentials=pika.PlainCredentials("guest", "guest"),
                connection_attempts=2,
                retry_delay=1))
        channel = connection.channel()
        q = channel.queue_declare(
            queue="ds_notifications", durable=True, passive=True)
        count = q.method.message_count
        connection.close()

        if count > 0:
            st.warning(f"""
            ⚠️ **You have {count} rejection notification(s)!**
            Go to **📬 Notifications** to see the details and rejection reasons.
            """)
            return count
    except:
        pass
    return 0

def show(user: dict):
    st.title("📬 Rejection Notifications")

    messages = _get_notifications()

    if not messages:
        st.success("✅ No pending notifications — all models are on track!")
        return

    st.error(f"⚠️ You have **{len(messages)}** rejection notification(s)")

    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBIT_HOST,
                credentials=pika.PlainCredentials("guest", "guest"),
                connection_attempts=2))
        channel = connection.channel()

        for delivery_tag, msg in messages:
            model_id   = msg.get("model_id", "")
            category   = msg.get("category", "")
            reason     = msg.get("reason", "")
            rejected_by = msg.get("rejected_by", "")
            role       = msg.get("role", "")
            timestamp  = msg.get("timestamp", "")[:16]

            with st.expander(
                f"❌ **{model_id}** — {category} — {timestamp}",
                expanded=True):

                col1, col2 = st.columns(2)
                col1.error(f"**Model:** {model_id}")
                col2.warning(f"**Rejected by:** {rejected_by} ({role})")

                st.markdown(f"**Category:** `{category}`")
                st.markdown("**Rejection Reason:**")
                st.info(reason[:500])

                st.markdown("**What to do:**")
                st.markdown("""
                - Review the rejection reason carefully
                - Fix the identified issues
                - Retrain your model if needed
                - Re-submit with improved metrics
                """)

                if st.button(
                    f"✅ Mark as Read",
                    key=f"ack_{delivery_tag}"):
                    channel.basic_ack(delivery_tag)
                    st.success("✅ Marked as read!")
                    st.rerun()

        connection.close()

    except Exception as e:
        st.error(f"❌ Error: {e}")
