"""Admin — User Management — Edition Premium"""
import streamlit as st
import httpx
from utils.api_client import (get_users, create_user,
                               delete_user, AUTH_URL, auth_headers)

ROLES = ["Data Scientist", "Compliance Officer", "ML Engineer",
         "Fraud Analyst", "Internal Auditor", "External Auditor",
         "Regulator", "Admin"]

# snake_case DB → display name
ROLE_DISPLAY = {
    "admin":              "Admin",
    "data_scientist":     "Data Scientist",
    "compliance_officer": "Compliance Officer",
    "ml_engineer":        "ML Engineer",
    "fraud_analyst":      "Fraud Analyst",
    "internal_auditor":   "Internal Auditor",
    "external_auditor":   "External Auditor",
    "regulator":          "Regulator",
}

# Couleur par rôle : (texte, fond)
ROLE_STYLE = {
    "Admin":              ("#1E40AF", "#DBEAFE"),
    "Data Scientist":     ("#166534", "#DCFCE7"),
    "Compliance Officer": ("#92400E", "#FEF3C7"),
    "ML Engineer":        ("#5B21B6", "#EDE9FE"),
    "Fraud Analyst":      ("#991B1B", "#FEE2E2"),
    "Internal Auditor":   ("#065F46", "#D1FAE5"),
    "External Auditor":   ("#374151", "#F3F4F6"),
    "Regulator":          ("#115E59", "#CCFBF1"),
}

# Bordure gauche par rôle
ROLE_BORDER = {
    "Admin":              "#3B82F6",
    "Data Scientist":     "#10B981",
    "Compliance Officer": "#F59E0B",
    "ML Engineer":        "#8B5CF6",
    "Fraud Analyst":      "#EF4444",
    "Internal Auditor":   "#10B981",
    "External Auditor":   "#6B7280",
    "Regulator":          "#14B8A6",
}


def _badge(text, color, bg):
    return (
        f'<span style="background:{bg};color:{color};'
        f'padding:.22rem .75rem;border-radius:30px;'
        f'font-size:.68rem;font-weight:700;'
        f'letter-spacing:.05em;text-transform:uppercase;">'
        f'{text}</span>'
    )


def _status_badge(is_active):
    if is_active:
        return _badge("Active", "#1F7A5A", "#DFF5EC")
    return _badge("Disabled", "#991B1B", "#FEE2E2")


def _role_badge(role):
    c, bg = ROLE_STYLE.get(role, ("#1E40AF", "#DBEAFE"))
    return _badge(role, c, bg)


def _page_header(user: dict):
    from datetime import datetime
    hour = datetime.utcnow().hour + 1
    salut = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")

    st.markdown(f"""
    <div style="
      display: flex; align-items: center;
      justify-content: space-between;
      margin-bottom: 1.8rem;
    ">
      <div>
        <h1 style="
          font-size: 1.75rem !important; font-weight: 800 !important;
          color: #1C1C1C !important; margin: 0 0 .25rem 0 !important;
          letter-spacing: -.03em !important; border: none !important; padding: 0 !important;
        ">User Management</h1>
        <p style="font-size:.88rem;color:#8A8A8A;margin:0;font-weight:400;">
          Manage accounts, roles and permissions.
        </p>
      </div>
      <div style="display:flex;align-items:center;gap:.75rem;">
        <div style="
          background:#F5F7F6;border:1px solid #E0E0E0;border-radius:12px;
          padding:.55rem 1rem;font-size:.8rem;color:#2B2B2B;font-weight:500;
        ">{salut}, <strong>{user['full_name']}</strong></div>
        <div style="
          width:38px;height:38px;border-radius:50%;
          background:linear-gradient(135deg,#1F7A5A,#4CAF82);
          display:flex;align-items:center;justify-content:center;
          font-size:.9rem;font-weight:800;color:white;
        ">{(user.get('full_name') or 'U')[0].upper()}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def show(user: dict):
    _page_header(user)
    token = st.session_state.get("token", "")

    # ── Récupération des utilisateurs ─────────────
    users = get_users(token=token)

    # Normalise les rôles snake_case → display name
    if users:
        for u in users:
            u["role"] = ROLE_DISPLAY.get(u["role"], u["role"])

    # ── Métriques sommaires ────────────────────────
    if users:
        total    = len(users)
        active   = sum(1 for u in users if u["is_active"])
        inactive = total - active
        n_roles  = len(ROLES)   # toujours 8 — nombre de rôles définis dans le système

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Users", total)
        c2.metric("Active", active)
        c3.metric("Disabled", inactive)
        c4.metric("Roles", n_roles)

    st.markdown("")

    # ── Ajouter un utilisateur ─────────────────────
    with st.expander("Add User", expanded=False):
        with st.form("create_user"):
            st.markdown(
                '<p style="font-size:.72rem;font-weight:700;color:#111827;'
                'text-transform:uppercase;letter-spacing:.09em;'
                'margin-bottom:.6rem;">Account Information</p>',
                unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            username  = c1.text_input("Username")
            password  = c2.text_input("Password", type="password")
            full_name = c3.text_input("Full Name")

            c1, c2, c3 = st.columns(3)
            email    = c1.text_input("Email Address")
            dept     = c2.text_input("Department")
            role_new = c3.selectbox("Role", ROLES)

            if st.form_submit_button("Create Account", type="primary"):
                if all([username, password, full_name, email, dept]):
                    result, code = create_user({
                        "username": username, "password": password,
                        "role": role_new, "full_name": full_name,
                        "email": email, "department": dept
                    }, token=token)
                    if code == 200:
                        st.success(f"Account created: {username} ({role_new})")
                        st.rerun()
                    else:
                        st.error(result.get("detail", str(result)))
                else:
                    st.warning("All fields are required.")

    # ── Liste des utilisateurs ─────────────────────
    st.subheader("Registered Users")

    if not users:
        st.warning("No users found or service unavailable.")
        return

    for u in users:
        last   = str(u.get("last_login") or "—")[:16]
        role   = u["role"]
        border = ROLE_BORDER.get(role, "#042C53")
        header = f"{u['username']}  ·  {role}  ·  {u['full_name']}"

        with st.expander(header):
            # Ligne de badges
            st.markdown(
                f'<div style="display:flex;gap:.5rem;'
                f'flex-wrap:wrap;margin-bottom:.9rem;">'
                f'{_status_badge(u["is_active"])}'
                f'{_role_badge(role)}'
                f'</div>',
                unsafe_allow_html=True)

            # Informations
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"**Email**  \n{u['email']}")
            c2.markdown(f"**Department**  \n{u['department']}")
            c3.markdown(f"**Last Login**  \n{last}")
            c4.markdown(f"**Created At**  \n{str(u.get('created_at',''))[:10]}")

            # Actions (sauf admin)
            if u["username"] != "admin":
                st.markdown("---")
                col1, col2, col3, col4 = st.columns(4)

                btn_label = "Disable" if u["is_active"] else "Enable"
                if col1.button(btn_label, key=f"tog_{u['id']}"):
                    try:
                        r = httpx.put(
                            f"{AUTH_URL}/users/{u['id']}",
                            headers=auth_headers(),
                            json={"is_active": not bool(u["is_active"])},
                            timeout=8)
                        if r.status_code == 200:
                            action = "disabled" if u["is_active"] else "enabled"
                            st.success(f"Account {u['username']} {action}.")
                            st.rerun()
                        else:
                            st.error(r.json().get("detail", "Unknown error"))
                    except Exception as e:
                        st.error(str(e))

                if col4.button("Delete", key=f"del_{u['id']}"):
                    result, code = delete_user(u["id"], token=token)
                    if code == 200:
                        st.success(f"Account {u['username']} deleted.")
                        st.rerun()
                    else:
                        st.error(result.get("detail", str(result)))
