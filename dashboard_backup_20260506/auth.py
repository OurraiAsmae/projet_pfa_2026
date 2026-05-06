"""
BlockML-Gov Authentication
"""
import streamlit as st
import httpx
import os
from datetime import datetime

AUTH_URL = os.getenv("AUTH_URL", "http://auth-service:8001")

def show_login_page():
    """Render login page"""
    c1, c2, c3 = st.columns([1, 1.1, 1])
    with c2:
        st.markdown("""
        <div class="login-box">
          <div style="text-align:center;margin-bottom:2rem;">
            <div style="font-size:3rem;">🏦</div>
            <h2 style="color:#003366;margin:.5rem 0 .2rem;
                       font-size:1.6rem;font-weight:800;
                       border:none;">
              BlockML-Gov
            </h2>
            <p style="color:#64748B;margin:0;
                      font-size:.85rem;">
              AI Governance Platform for Banking
            </p>
            <div style="margin-top:.5rem;">
              <span class="badge badge-blue">
                Hyperledger Fabric 2.5
              </span>&nbsp;
              <span class="badge badge-gold">
                EU AI Act
              </span>&nbsp;
              <span class="badge badge-green">
                Basel III
              </span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            st.markdown("#### 🔐 Secure Authentication")
            username = st.text_input(
                "Username",
                placeholder="Enter your username")
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password")
            submitted = st.form_submit_button(
                "Login →",
                type="primary",
                use_container_width=True)

        if submitted:
            if not username or not password:
                st.error(
                    "Please enter username and password.")
                return
            with st.spinner("Authenticating..."):
                try:
                    r = httpx.post(
                        f"{AUTH_URL}/auth/login",
                        json={"username": username,
                              "password": password},
                        timeout=10)
                    if r.status_code == 200:
                        data = r.json()
                        st.session_state.update({
                            "logged_in":     True,
                            "token":         data["access_token"],
                            "refresh_token": data["refresh_token"],
                            "user":          data["user"],
                            "login_time":    datetime.utcnow().isoformat()
                        })
                        st.rerun()
                    elif r.status_code == 423:
                        st.error(f"🔒 {r.json().get('detail','Account locked')}")
                    else:
                        st.error(
                            "❌ Invalid credentials.")
                except Exception as e:
                    st.error(
                        f"❌ Auth service unavailable: {e}")

def handle_logout():
    """Handle logout"""
    try:
        token = st.session_state.get("token","")
        httpx.post(f"{AUTH_URL}/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5)
    except:
        pass
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()
