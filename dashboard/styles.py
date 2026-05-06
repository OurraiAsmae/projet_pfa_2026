"""BlockML-Gov — Styles centralisés v6.0"""
import streamlit as st

CORPORATE_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
  * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; }
  @keyframes fadeUp { from { opacity:0;transform:translateY(12px); } to { opacity:1;transform:translateY(0); } }
  @keyframes fadeIn { from { opacity:0; } to { opacity:1; } }
  @keyframes pulse-green { 0%,100% { box-shadow:0 4px 6px rgba(31,122,90,0.15); } 50% { box-shadow:0 4px 20px rgba(31,122,90,0.35); } }
  @keyframes bounceIn { 0% { transform:scale(.95);opacity:0; } 60% { transform:scale(1.02);opacity:1; } 100% { transform:scale(1); } }
  .stApp { background:#F4F6F5 !important; }
  .main .block-container { background:#F4F6F5 !important; padding:1.5rem 2.2rem !important; max-width:1400px !important; animation:fadeIn .35s ease !important; }
  .main .block-container::before { content:'' !important; display:block !important; height:3px !important; background:linear-gradient(90deg,#1F7A5A,#4CAF82,#A8E6C8) !important; margin-bottom:1.5rem !important; margin-left:-2.2rem !important; margin-right:-2.2rem !important; margin-top:-1.5rem !important; }
  .stApp p,.stApp li { color:#6B7280 !important; }
  *:focus { outline:none !important; }
  input:focus,textarea:focus { border-color:#1F7A5A !important; box-shadow:0 0 0 3px rgba(31,122,90,.15) !important; }
  div[data-testid="stTabs"] button[role="tab"] { color:#374151 !important; font-weight:600 !important; font-size:.88rem !important; background:transparent !important; border:none !important; padding:.55rem 1.2rem !important; }
  div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color:#1F7A5A !important; border-bottom:2px solid #1F7A5A !important; }
  div[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color:#1F7A5A !important; height:3px !important; }
  section[data-testid="stSidebar"] { background:#FFFFFF !important; border-right:1px solid #E8E8E8 !important; }
  h1 { color:#1C1C1C !important; font-weight:800 !important; font-size:1.75rem !important; animation:fadeUp .3s ease !important; }
  h2 { color:#1C1C1C !important; font-weight:700 !important; font-size:1.1rem !important; }
  h3 { color:#374151 !important; font-weight:600 !important; font-size:.92rem !important; }
  div[data-testid="stMetric"] { border-radius:16px !important; padding:1.4rem 1.5rem !important; border:none !important; transition:transform .22s ease !important; animation:fadeUp .35s ease both !important; }
  div[data-testid="stMetric"]:hover { transform:translateY(-4px) !important; }
  div[data-testid="column"]:nth-of-type(1) div[data-testid="stMetric"] { background:linear-gradient(135deg,#1A6B4E,#1F7A5A) !important; box-shadow:0 6px 20px rgba(31,122,90,.35) !important; animation:pulse-green 3s ease-in-out infinite !important; }
  div[data-testid="column"]:nth-of-type(2) div[data-testid="stMetric"] { background:linear-gradient(135deg,#2A9D6F,#4CAF82) !important; }
  div[data-testid="column"]:nth-of-type(3) div[data-testid="stMetric"] { background:linear-gradient(135deg,#4CAF82,#6ECFA0) !important; }
  div[data-testid="column"]:nth-of-type(4) div[data-testid="stMetric"] { background:linear-gradient(135deg,#A8E6C8,#C8F5E0) !important; }
  div[data-testid="column"]:nth-of-type(1) div[data-testid="stMetric"] div[data-testid="stMetricValue"] * { color:#FFFFFF !important; font-weight:800 !important; font-size:2rem !important; }
  div[data-testid="column"]:nth-of-type(2) div[data-testid="stMetric"] div[data-testid="stMetricValue"] * { color:#FFFFFF !important; font-weight:800 !important; font-size:2rem !important; }
  div[data-testid="column"]:nth-of-type(3) div[data-testid="stMetric"] div[data-testid="stMetricValue"] * { color:#FFFFFF !important; font-weight:800 !important; font-size:2rem !important; }
  div[data-testid="column"]:nth-of-type(4) div[data-testid="stMetric"] div[data-testid="stMetricValue"] * { color:#1A6B4E !important; font-weight:800 !important; font-size:2rem !important; }
  div[data-testid="column"]:nth-of-type(5) div[data-testid="stMetric"] { background:linear-gradient(135deg,#6ECFA0,#A8E6C8) !important; box-shadow:0 4px 14px rgba(110,207,160,.3) !important; }
  div[data-testid="column"]:nth-of-type(5) div[data-testid="stMetric"] div[data-testid="stMetricLabel"] p { color:rgba(255,255,255,.8) !important; font-weight:600 !important; font-size:.8rem !important; text-transform:uppercase !important; }
  div[data-testid="column"]:nth-of-type(5) div[data-testid="stMetric"] div[data-testid="stMetricValue"] * { color:#FFFFFF !important; font-weight:800 !important; font-size:2rem !important; }
  div[data-testid="column"]:nth-of-type(1) div[data-testid="stMetric"] div[data-testid="stMetricLabel"] p { color:rgba(255,255,255,.8) !important; font-weight:600 !important; font-size:.8rem !important; text-transform:uppercase !important; }
  div[data-testid="column"]:nth-of-type(2) div[data-testid="stMetric"] div[data-testid="stMetricLabel"] p { color:rgba(255,255,255,.8) !important; font-weight:600 !important; font-size:.8rem !important; text-transform:uppercase !important; }
  div[data-testid="column"]:nth-of-type(3) div[data-testid="stMetric"] div[data-testid="stMetricLabel"] p { color:rgba(255,255,255,.8) !important; font-weight:600 !important; font-size:.8rem !important; text-transform:uppercase !important; }
  div[data-testid="column"]:nth-of-type(4) div[data-testid="stMetric"] div[data-testid="stMetricLabel"] p { color:#1A6B4E !important; font-weight:700 !important; font-size:.8rem !important; text-transform:uppercase !important; }
  .main .stButton > button { background:linear-gradient(135deg,#1F7A5A,#4CAF82) !important; color:#FFFFFF !important; border:none !important; border-radius:12px !important; font-weight:600 !important; padding:.55rem 1.3rem !important; transition:all .2s ease !important; box-shadow:0 2px 8px rgba(31,122,90,.25) !important; }
  .main .stButton > button * { color:#FFFFFF !important; }
  .main .stButton > button:hover { transform:translateY(-2px) scale(1.02) !important; box-shadow:0 8px 20px rgba(31,122,90,.35) !important; }
  div[data-testid="stExpander"] { background:#FFFFFF !important; border:1px solid #EFEFEF !important; border-radius:14px !important; box-shadow:0 1px 3px rgba(0,0,0,.04) !important; overflow:hidden !important; margin-bottom:.75rem !important; transition:box-shadow .2s ease !important; }
  div[data-testid="stExpander"]:hover { box-shadow:0 6px 20px rgba(0,0,0,.08) !important; border-color:#D1FAE5 !important; }
  div[data-testid="stExpander"] summary { color:#1C1C1C !important; font-weight:600 !important; padding:.95rem 1.2rem !important; }
  .stTextInput input,.stTextArea textarea,.stNumberInput input { border:1.5px solid #E5E7EB !important; border-radius:10px !important; background:#FAFAFA !important; color:#111827 !important; }
  .stTextInput input:focus,.stTextArea textarea:focus { border-color:#1F7A5A !important; background:#FFFFFF !important; box-shadow:0 0 0 3px rgba(31,122,90,.15) !important; }
  div[data-testid="stDataFrame"] { border-radius:14px !important; overflow:hidden !important; box-shadow:0 2px 8px rgba(0,0,0,.06) !important; border:1px solid #E8EDE9 !important; background:#FFFFFF !important; }
  div[data-testid="stDataFrame"] thead tr th { background:linear-gradient(135deg,#F0FAF6,#E8F5EE) !important; color:#1F7A5A !important; font-weight:700 !important; font-size:.78rem !important; text-transform:uppercase !important; }
  div[data-testid="stSuccess"] { background:#ECFDF5 !important; border-left:4px solid #1F7A5A !important; border-radius:12px !important; }
  div[data-testid="stSuccess"] * { color:#065F46 !important; }
  div[data-testid="stError"] { background:#FEF2F2 !important; border-left:4px solid #EF4444 !important; border-radius:12px !important; }
  div[data-testid="stError"] * { color:#991B1B !important; }
  div[data-testid="stWarning"] { background:#FFFBEB !important; border-left:4px solid #F59E0B !important; border-radius:12px !important; }
  div[data-testid="stWarning"] * { color:#92400E !important; }
  div[data-testid="stInfo"] { background:#EFF6FF !important; border-left:4px solid #3B82F6 !important; border-radius:12px !important; }
  div[data-testid="stInfo"] * { color:#1E40AF !important; }
  hr { border:none !important; border-top:1px solid #F3F4F6 !important; margin:1.5rem 0 !important; }
  .stCaption { color:#9CA3AF !important; font-size:.78rem !important; }
  #MainMenu,footer,header { visibility:hidden; }
  ::-webkit-scrollbar { width:5px; height:5px; }
  ::-webkit-scrollbar-thumb { background:#D1D5DB; border-radius:10px; }
</style>
"""

def inject_css():
    st.markdown(CORPORATE_CSS, unsafe_allow_html=True)

_ICON_SHIELD     = '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#1F7A5A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>'
_ICON_HISTORY    = '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#1F7A5A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>'
_ICON_DB         = '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#1F7A5A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>'
_ICON_SUCCESS    = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'
_ICON_CHECK      = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>'
_ICON_WARNING    = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
_ICON_ERROR      = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>'
_ICON_INFO       = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'
_ICON_IPFS       = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>'
_ICON_BLOCKCHAIN = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M3 15h18"/><path d="M9 3v18"/><path d="M15 3v18"/></svg>'
_ICON_CHART      = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1F7A5A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
_ICON_PENDING    = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>'
_ICON_DATASET    = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#047857" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>'
_ICON_USER       = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#4B5563" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>'
_ICON_MODEL      = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>'
_ICON_LINK       = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>'


def _header(title: str, icon_svg: str, subtitle: str = ""):
    st.markdown(f"""
        <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.5rem;padding-bottom:1rem;border-bottom:1px solid #E5E7EB;">
            <div style="width:48px;height:48px;background:#F0FAF6;border-radius:12px;display:flex;align-items:center;justify-content:center;">{icon_svg}</div>
            <div>
                <h1 style="margin:0;padding:0;font-size:1.6rem;color:#111827;font-weight:700;">{title}</h1>
                <p style="margin:0;padding:0;color:#6B7280;font-size:0.9rem;">{subtitle}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)


def _card_header(title: str, icon_svg: str):
    st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.5rem;margin:1.5rem 0 0.8rem 0;">
            <div style="display:flex;align-items:center;justify-content:center;">{icon_svg}</div>
            <h3 style="margin:0;padding:0;font-size:1.1rem;color:#111827;font-weight:600;">{title}</h3>
        </div>
    """, unsafe_allow_html=True)


def _alert_box(alert_type: str, content: str, icon_svg: str = None):
    colors = {
        "SUCCESS": ("#F0FDF4", "#16A34A", "#14532D"),
        "WARNING": ("#FFFBEB", "#F59E0B", "#92400E"),
        "ERROR":   ("#FEF2F2", "#EF4444", "#991B1B"),
        "INFO":    ("#EFF6FF", "#3B82F6", "#1E3A8A"),
    }
    default_icons = {
        "SUCCESS": _ICON_CHECK,
        "WARNING": _ICON_WARNING,
        "ERROR":   _ICON_ERROR,
        "INFO":    _ICON_INFO,
    }
    bg, border, text = colors.get(alert_type.upper(), colors["INFO"])
    icon = icon_svg or default_icons.get(alert_type.upper(), _ICON_INFO)
    st.markdown(f"""
        <div style="padding:1rem;background-color:{bg};border-left:4px solid {border};
                    border-radius:0.5rem;display:flex;align-items:flex-start;
                    gap:0.75rem;margin-bottom:1rem;">
            <div style="margin-top:2px;flex-shrink:0;">{icon}</div>
            <div style="color:{text};font-weight:500;font-size:0.95rem;">{content}</div>
        </div>
    """, unsafe_allow_html=True)
