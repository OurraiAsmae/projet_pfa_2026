"""Data Scientist — Rejection Notifications"""
import streamlit as st
import pika
import json
import httpx
from datetime import datetime
from utils.api_client import API_URL

RABBIT_HOST = "rabbitmq"

def _get_notifications() -> list:
    messages = []
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBIT_HOST,
                credentials=pika.PlainCredentials("guest", "guest"),
                connection_attempts=2, retry_delay=1))
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

def show_popup_if_notifications():
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBIT_HOST,
                credentials=pika.PlainCredentials("guest", "guest"),
                connection_attempts=2, retry_delay=1))
        channel = connection.channel()
        q = channel.queue_declare(
            queue="ds_notifications", durable=True, passive=True)
        count = q.method.message_count
        connection.close()
        if count > 0:
            st.warning(f"""
            ⚠️ **You have {count} rejection notification(s)!**
            Go to **📬 Notifications** to see the details.
            """)
            return count
    except:
        pass
    return 0

def show(user: dict):
    st.title("📬 Rejection Notifications")

    # Get read notifications from session state
    if "read_notifications" not in st.session_state:
        st.session_state.read_notifications = set()

    messages = _get_notifications()

    if not messages:
        st.success("✅ No pending notifications — all models are on track!")
        return

    unread = [m for m in messages 
              if m[1].get("model_id") not in st.session_state.read_notifications]
    read   = [m for m in messages 
              if m[1].get("model_id") in st.session_state.read_notifications]

    if unread:
        st.error(f"⚠️ **{len(unread)}** unread notification(s)")
    if read:
        st.info(f"✅ **{len(read)}** read notification(s)")

    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBIT_HOST,
                credentials=pika.PlainCredentials("guest", "guest"),
                connection_attempts=2))
        channel = connection.channel()

        for delivery_tag, msg in messages:
            model_id    = msg.get("model_id", "")
            category    = msg.get("category", "")
            reason      = msg.get("reason", "")
            rejected_by = msg.get("rejected_by", "")
            role        = msg.get("role", "")
            timestamp   = msg.get("timestamp", "")[:16]
            is_read     = model_id in st.session_state.read_notifications

            icon  = "✅" if is_read else "❌"
            style = "opacity: 0.6;" if is_read else ""

            with st.expander(
                f"{icon} **{model_id}** — {category} — {timestamp}",
                expanded=not is_read):

                col1, col2 = st.columns(2)
                col1.error(f"**Model:** {model_id}")
                col2.warning(f"**Rejected by:** {rejected_by} ({role})")
                st.markdown(f"**Category:** `{category}`")
                st.markdown("**Rejection Reason:**")
                st.info(reason[:500])

                if not is_read:
                    st.markdown("**What to do:**")
                    st.markdown("""
                    - Review the rejection reason carefully
                    - Fix the identified issues
                    - Retrain your model if needed
                    - Re-submit with improved metrics
                    """)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(
                            f"✅ Mark as Read",
                            key=f"ack_{delivery_tag}"):
                            st.session_state.read_notifications.add(model_id)
                            channel.basic_ack(delivery_tag)
                            channel.close()
                            connection.close()
                            st.rerun()
                else:
                    st.success("✅ You have read this notification")

        try:
            connection.close()
        except:
            pass

    except Exception as e:
        st.error(f"❌ Error: {e}")
