"""
BlockML-Gov — Top Bar (Donezo Style — No icons, no hover effects)
"""
import streamlit as st


def render_topbar(page: str, user: dict):
    """Rendu de la barre de navigation haute"""
    email = user.get('email', 'admin@blockml.gov')
    name  = user.get('full_name', 'User')
    role  = user.get('role', '')
    initial = name[0].upper() if name else "U"

    st.markdown(f"""
    <div style="
      background: #FFFFFF;
      border-radius: 16px;
      padding: .8rem 1.5rem;
      margin-bottom: 1.5rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border: 1px solid #E0E0E0;
      box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    ">

      <!-- Gauche : Barre de recherche -->
      <div style="
        background: #F5F7F6;
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        padding: .55rem 1rem;
        width: 300px;
      ">
        <span style="color:#8A8A8A; font-size:.875rem;">Search task...</span>
      </div>

      <!-- Droite : Profil utilisateur -->
      <div style="display:flex; align-items:center; gap:.75rem;">
        <div style="
          width: 38px; height: 38px; border-radius: 50%;
          background: #DFF5EC;
          border: 2px solid #A7D7C5;
          display: flex; align-items: center; justify-content: center;
          font-weight: 700; font-size: 1rem; color: #1F7A5A;
        ">{initial}</div>
        <div>
          <div style="font-size:.875rem; font-weight:700; color:#1C1C1C; line-height:1.2;">{name}</div>
          <div style="font-size:.75rem; color:#8A8A8A;">{role}</div>
        </div>
      </div>

    </div>
    """, unsafe_allow_html=True)
