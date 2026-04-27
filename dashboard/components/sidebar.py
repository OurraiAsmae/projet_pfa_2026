"""
BlockML-Gov Sidebar Component
"""
import streamlit as st
import httpx
import os
from datetime import datetime

API_URL  = os.getenv("API_URL", "http://api:8000")

PAGES_MAP = {
    "Admin": [
        "👥 User Management",
        "📋 Audit Logs"
    ],
    "Data Scientist": [
        "📤 Upload Model",
        "📊 Upload Dataset",
        "🔬 MLflow Experiments",
        "🔍 SHAP Explorer"
    ],
    "Compliance Officer": [
        "✅ Compliance Validation",
        "📋 Validation History"
    ],
    "ML Engineer": [
        "🔧 Technical Approval",
        "🚀 Model Deployment",
        "📜 Model History",
        "📉 Drift Monitoring"
    ],
    "Fraud Analyst": [
        "📊 Live Dashboard",
        "🧪 Test Transaction",
        "🚨 Alerts"
    ],
    "Internal Auditor": [
        "📋 Audit Trail",
        "📄 Compliance Reports"
    ],
    "External Auditor": [
        "🔐 Integrity Check",
        "📋 Certified Reports"
    ],
    "Regulator": [
        "🏛️ System Status",
        "🔍 Inspection",
        "📨 BAM Submissions"
    ],
}

ROLE_ICONS = {
    "Admin":              "⚙️",
    "Data Scientist":     "🔬",
    "Compliance Officer": "✅",
    "ML Engineer":        "🔧",
    "Fraud Analyst":      "🔍",
    "Internal Auditor":   "📋",
    "External Auditor":   "🔐",
    "Regulator":          "🏛️"
}

def render_sidebar(user: dict,
                   on_logout) -> str:
    """Render sidebar and return selected page"""
    role = user["role"]

    with st.sidebar:
        # Logo
        st.markdown(f"""
        <div style="text-align:center;padding:1.2rem 0 1rem;
                    border-bottom:1px solid rgba(201,168,76,.3);
                    margin-bottom:1rem;">
          <div style="font-size:2.8rem;">🏦</div>
          <div style="font-size:1.15rem;font-weight:800;
                      color:#C9A84C;letter-spacing:.05em;">
            BlockML-Gov
          </div>
          <div style="font-size:.65rem;
                      color:rgba(255,255,255,.6);
                      letter-spacing:.1em;
                      text-transform:uppercase;">
            AI Governance Platform
          </div>
        </div>
        """, unsafe_allow_html=True)

        # User card
        icon = ROLE_ICONS.get(role, "👤")
        st.markdown(f"""
        <div style="background:rgba(255,255,255,.08);
                    border:1px solid rgba(201,168,76,.25);
                    border-radius:10px;padding:.9rem;
                    margin-bottom:1rem;">
          <div style="font-size:.65rem;color:#C9A84C;
                      text-transform:uppercase;
                      letter-spacing:.1em;
                      margin-bottom:.3rem;">
            Logged in as
          </div>
          <div style="font-size:.95rem;font-weight:700;
                      color:white;">
            {icon} {user['full_name']}
          </div>
          <div style="font-size:.72rem;
                      color:rgba(255,255,255,.55);
                      margin:.15rem 0;">
            {user.get('department','')}
          </div>
          <div style="margin-top:.4rem;">
            <span style="background:#C9A84C;color:#003366;
                         padding:.15rem .6rem;
                         border-radius:20px;
                         font-size:.68rem;font-weight:800;">
              {role}
            </span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Active model
        try:
            active = httpx.get(
                f"{API_URL}/model/active",
                timeout=3).json()
            mid   = active.get("model_id","N/A")
            mtype = active.get("model_type","N/A")
            st.markdown(f"""
            <div style="background:rgba(0,82,163,.25);
                        border-left:3px solid #4A9EFF;
                        border-radius:8px;
                        padding:.65rem .9rem;
                        margin-bottom:1rem;">
              <div style="font-size:.62rem;color:#4A9EFF;
                          text-transform:uppercase;
                          letter-spacing:.08em;">
                Active Model
              </div>
              <div style="font-size:.82rem;font-weight:700;
                          color:white;margin-top:.15rem;">
                {mid}
              </div>
              <div style="font-size:.68rem;
                          color:rgba(255,255,255,.5);">
                {mtype}
              </div>
            </div>
            """, unsafe_allow_html=True)
        except:
            pass

        # Navigation label
        st.markdown("""
        <div style="font-size:.68rem;color:#C9A84C;
                    text-transform:uppercase;
                    letter-spacing:.1em;
                    margin-bottom:.4rem;
                    font-weight:700;">
          Navigation
        </div>
        """, unsafe_allow_html=True)

        # Page selector
        pages = PAGES_MAP.get(role, ["📊 Dashboard"])
        page  = st.selectbox("Navigation", pages,
                             label_visibility="collapsed")

        st.markdown("---")

        # System health
        try:
            h = httpx.get(
                f"{API_URL}/health", timeout=3).json()
            st.markdown(f"""
            <div style="font-size:.68rem;
                        color:rgba(255,255,255,.5);
                        line-height:1.8;">
              <span style="color:#4ADE80;">●</span>
              API v{h.get('version','?')}<br/>
              <span style="color:#4ADE80;">●</span>
              ML: {h.get('ml_model')}<br/>
              <span style="color:#4ADE80;">●</span>
              SHAP: {h.get('shap')}<br/>
              <span style="color:#4ADE80;">●</span>
              Redis: {h.get('redis')}
            </div>
            """, unsafe_allow_html=True)
        except:
            pass

        st.markdown("---")

        # Logout
        if st.button("🚪 Logout",
                     use_container_width=True):
            on_logout()

        # Session info
        login_t = st.session_state.get(
            "login_time","")[:16]
        st.markdown(f"""
        <div style="font-size:.6rem;
                    color:rgba(255,255,255,.3);
                    text-align:center;
                    margin-top:.5rem;">
          Session since {login_t} UTC<br/>
          BlockML-Gov v4.0
        </div>
        """, unsafe_allow_html=True)

    return page
