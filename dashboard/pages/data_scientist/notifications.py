"""Data Scientist — Rejection Notifications"""
import streamlit as st
import pika
import json
import httpx
from datetime import datetime
from utils.api_client import API_URL

RABBIT_HOST = "rabbitmq"

# --- SVG Icons ---
_ICON_BELL = '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#1F7A5A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>'
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
        pass
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
            _alert_box(
                f"You have {count} rejection notification(s)!\n"
                f"Go to **Notifications** to see the details.", "warning")
            return count
    except:
        pass
    return 0


def show(user: dict):
    _header(
        "Rejection Notifications",
        "View feedback from Compliance Officers and ML Engineers.",
        _ICON_BELL
    )

    # Get read notifications from session state
    if "read_notifications" not in st.session_state:
        st.session_state.read_notifications = set()

    messages = _get_notifications()

    if not messages:
        _alert_box("No pending notifications — all models are on track!", "success")
        return

    unread = [m for m in messages 
              if m[1].get("model_id") not in st.session_state.read_notifications]
    read   = [m for m in messages 
              if m[1].get("model_id") in st.session_state.read_notifications]

    if unread:
        _alert_box(f"**{len(unread)}** unread notification(s)", "error")
    if read:
        _alert_box(f"**{len(read)}** read notification(s)", "info")

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

            icon_label  = "[READ]" if is_read else "[UNREAD]"

            with st.expander(
                f"{icon_label} {model_id} — {category} — {timestamp}",
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
                            f"Mark as Read",
                            key=f"ack_{delivery_tag}"):
                            st.session_state.read_notifications.add(model_id)
                            channel.basic_ack(delivery_tag)
                            channel.close()
                            connection.close()
                            st.rerun()
                else:
                    _alert_box("You have read this notification", "success")

        try:
            connection.close()
        except:
            pass

    except Exception as e:
        _alert_box(f"Error: {e}", "error")
