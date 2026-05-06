"""
BlockML-Gov Authentication
"""
import streamlit as st
import httpx
import os
import urllib.parse
from datetime import datetime

AUTH_URL = os.getenv("AUTH_URL", "http://auth-service:8001")


def _svg_uri(svg: str) -> str:
    """Encode SVG as a data URI for use in <img> tags."""
    return "data:image/svg+xml," + urllib.parse.quote(svg)


# ── SVG Icons ────────────────────────────────────────
_SHIELD_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#1F7A5A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 12 15 16 10" stroke="#4CAF82" stroke-width="2"/></svg>'
_CHAIN_SVG  = '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M3 15h18"/><path d="M9 3v18"/><path d="M15 3v18"/></svg>'
_SCALE_SVG  = '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 3h5v5"/><path d="M8 3H3v5"/><path d="M12 22V8"/><path d="M20 3l-8 5-8-5"/></svg>'
_BANK_SVG   = '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>'
_LOCK_SVG   = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>'

# ── Login page CSS ───────────────────────────────────
_LOGIN_CSS = """
<style>
/* Hide sidebar on login */
section[data-testid="stSidebar"] { display: none !important; }

/* Login page background */
.login-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 1rem;
    padding-top: 2rem;
    animation: loginFadeIn .5s ease;
}
@keyframes loginFadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes loginShimmer {
    0%   { background-position: -200% center; }
    100% { background-position: 200% center; }
}
@keyframes pulse-dot {
    0%, 100% { opacity: .4; transform: scale(.8); }
    50%      { opacity: 1;  transform: scale(1); }
}

.login-card {
    background: #FFFFFF;
    border-radius: 24px;
    padding: 2.8rem 2.4rem 2.2rem;
    box-shadow: 0 4px 6px rgba(0,0,0,.04), 0 20px 50px rgba(31,122,90,.08);
    border: 1px solid #E8EDE9;
    max-width: 550px;
    width: 100%;
    position: relative;
    overflow: hidden;
}
.login-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #1F7A5A, #4CAF82, #A8E6C8, #4CAF82, #1F7A5A);
    background-size: 200% auto;
    animation: loginShimmer 3s linear infinite;
}

.login-logo {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: .6rem;
}
.login-logo-box {
    width: 80px; height: 80px;
    border-radius: 20px;
    background: linear-gradient(135deg, #F0FAF6, #E0F4ED);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(31,122,90,.12);
}
.login-logo-box img {
    width: 50px; height: 50px;
}

.login-title {
    font-size: 1.9rem;
    font-weight: 900;
    color: #1C1C1C;
    letter-spacing: -.03em;
    text-align: center;
    margin: .8rem 0 .2rem;
    line-height: 1.2;
}
.login-title span { color: #1F7A5A; }

.login-subtitle {
    font-size: .95rem;
    color: #9CA3AF;
    text-align: center;
    margin: 0 0 1.5rem;
    font-weight: 500;
}



.login-divider {
    display: flex;
    align-items: center;
    gap: .75rem;
    margin: 0 0 .4rem;
}
.login-divider::before,
.login-divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #E5E7EB;
}
.login-divider img { width: 14px; height: 14px; }
.login-divider-text {
    display: flex;
    align-items: center;
    gap: .4rem;
    font-size: .72rem;
    font-weight: 600;
    color: #9CA3AF;
    text-transform: uppercase;
    letter-spacing: .08em;
    white-space: nowrap;
}

.login-footer {
    text-align: center;
    margin-top: 1rem;
    padding-top: .7rem;
    border-top: 1px solid #F3F4F6;
}
.login-footer-text {
    font-size: .7rem;
    color: #9CA3AF;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: .4rem;
}
.login-footer-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #1F7A5A;
    display: inline-block;
    animation: pulse-dot 2s ease-in-out infinite;
}
</style>
"""


def show_login_page():
    """Rendu de la page de connexion — design professionnel"""
    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    # Pre-encode SVGs as data URIs
    shield_uri = _svg_uri(_SHIELD_SVG)
    chain_uri  = _svg_uri(_CHAIN_SVG)
    scale_uri  = _svg_uri(_SCALE_SVG)
    bank_uri   = _svg_uri(_BANK_SVG)
    lock_uri   = _svg_uri(_LOCK_SVG)

    c1, c2, c3 = st.columns([1, 2.5, 1])
    with c2:
        st.markdown(
            f'<div class="login-wrapper">'
            f'<div class="login-card">'
            f'<div class="login-logo">'
            f'<div class="login-logo-box"><img src="{shield_uri}" alt="logo"></div>'
            f'</div>'
            f'<div class="login-title">BlockML<span>.</span>Gov</div>'
            f'<p class="login-subtitle">AI Governance Platform for Banking</p>'
            f'<div class="login-divider">'
            f'<span class="login-divider-text"><img src="{lock_uri}" alt=""> Secure Authentication</span>'
            f'</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        with st.form("login_form"):
            username = st.text_input(
                "Username",
                placeholder="Enter your username")
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password")
            submitted = st.form_submit_button(
                "Sign In",
                type="primary",
                use_container_width=True)

        st.markdown(
            f'<div class="login-footer">'
            f'<div class="login-footer-text">'
            f'<span class="login-footer-dot"></span> Protected by Blockchain-backed Audit Trail'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        if submitted:
            if not username or not password:
                st.error(
                    "Please enter your username and password.")
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
                        st.error(r.json().get(
                            'detail', 'Account locked.'))
                    else:
                        st.error(
                            "Invalid credentials. Please try again.")
                except Exception as e:
                    st.error(
                        f"Authentication service unavailable: {e}")


def handle_logout():
    """Handle logout — used as on_click callback, no st.rerun() needed"""
    try:
        token = st.session_state.get("token", "")
        httpx.post(f"{AUTH_URL}/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5)
    except:
        pass
    for k in list(st.session_state.keys()):
        del st.session_state[k]
