"""Admin — User Management"""
import streamlit as st
import httpx
import os
from utils.api_client import (get_users, create_user,
                               update_user, delete_user,
                               AUTH_URL, auth_headers)

ROLES = ["Data Scientist","Compliance Officer",
         "ML Engineer","Fraud Analyst",
         "Internal Auditor","External Auditor",
         "Regulator","Admin"]

def show(user: dict):
    st.title("👥 User Management")
    token = st.session_state.get("token","")

    # ── Add New User ──────────────────────────────
    with st.expander("➕ Add New User", expanded=False):
        with st.form("create_user"):
            c1,c2,c3 = st.columns(3)
            username  = c1.text_input("Username*")
            password  = c2.text_input("Password*",
                type="password")
            full_name = c3.text_input("Full Name*")
            c1,c2,c3 = st.columns(3)
            email     = c1.text_input("Email*")
            dept      = c2.text_input("Department*")
            role_new  = c3.selectbox("Role*", ROLES)

            if st.form_submit_button(
                "✅ Create User", type="primary"):
                if all([username, password,
                        full_name, email, dept]):
                    result, code = create_user({
                        "username":   username,
                        "password":   password,
                        "role":       role_new,
                        "full_name":  full_name,
                        "email":      email,
                        "department": dept
                    }, token=token)
                    if code == 200:
                        st.success(
                            f"✅ User **{username}** "
                            f"created ({role_new})")
                        st.rerun()
                    else:
                        st.error(
                            f"❌ {result.get('detail',result)}")
                else:
                    st.warning(
                        "Please fill all required fields")

    # ── User List ─────────────────────────────────
    st.subheader("Current Users")
    users = get_users(token=token)

    if not users:
        st.warning("No users found or auth service unavailable")
        return

    for u in users:
        status = "🟢 Active" if u["is_active"] else "🔴 Disabled"
        last   = str(u.get("last_login") or "Never")[:16]

        with st.expander(
            f"{status} · **{u['username']}** "
            f"— {u['role']} — {u['full_name']}"):

            c1,c2,c3,c4 = st.columns(4)
            c1.markdown(f"**Email:** {u['email']}")
            c2.markdown(f"**Dept:** {u['department']}")
            c3.markdown(f"**Last login:** {last}")
            c4.markdown(
                f"**Created:** "
                f"{str(u.get('created_at',''))[:10]}")

            if u["username"] != "admin":
                col1,col2,col3,col4 = st.columns(4)

                # Disable / Enable
                btn = ("🔴 Disable" if u["is_active"]
                       else "🟢 Enable")
                if col1.button(btn,
                    key=f"tog_{u['id']}"):
                    try:
                        r = httpx.put(
                            f"{AUTH_URL}/users/{u['id']}",
                            headers=auth_headers(),
                            json={"is_active":
                                  not bool(u["is_active"])},
                            timeout=8)
                        if r.status_code == 200:
                            action = ("disabled"
                                if u["is_active"]
                                else "enabled")
                            st.success(
                                f"✅ {u['username']} {action}")
                            st.rerun()
                        else:
                            st.error(
                                f"❌ {r.json().get('detail')}")
                    except Exception as e:
                        st.error(f"❌ {e}")



                # Delete
                if col4.button("🗑️ Delete",
                    key=f"del_{u['id']}"):
                    result, code = delete_user(u["id"], token=token)
                    if code == 200:
                        st.success(
                            f"✅ {u['username']} deleted")
                        st.rerun()
                    else:
                        st.error(
                            f"❌ {result.get('detail',result)}")
