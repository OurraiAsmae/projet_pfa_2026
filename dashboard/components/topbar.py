"""
BlockML-Gov Top Bar Component
"""
import streamlit as st
from datetime import datetime

def render_topbar(page: str, user: dict):
    """Render top navigation bar"""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    st.markdown(f"""
    <div class="topbar">
      <div>
        <span style="font-size:1.05rem;font-weight:700;">
          {page}
        </span>
        <span style="margin-left:1rem;opacity:.65;
                     font-size:.82rem;">
          BlockML-Gov · Banking AI Governance
        </span>
      </div>
      <div style="font-size:.78rem;opacity:.8;">
        {user['full_name']} · {user['role']} · {now}
      </div>
    </div>
    """, unsafe_allow_html=True)
