"""
BlockML-Gov Corporate Banking Styles
"""

CORPORATE_CSS = """
<style>
  /* ── Base ───────────────────────────────────── */
  .stApp { background:#F0F4F8 !important; }

  .main .block-container {
    background:#F8FAFC !important;
    padding:2rem !important;
  }

  /* ── Text colors ────────────────────────────── */
  .stApp p, .stApp div, .stApp span,
  .stApp li, .stApp label {
    color:#1A202C !important;
  }
  .stMarkdown p  { color:#1A202C !important; }
  .stMarkdown li { color:#1A202C !important; }

  /* ── Sidebar ────────────────────────────────── */
  section[data-testid="stSidebar"] {
    background:linear-gradient(
      180deg,#003366 0%,#001a33 100%) !important;
    border-right:3px solid #C9A84C !important;
  }
  section[data-testid="stSidebar"] * {
    color:white !important;
  }

  /* ── Headers ────────────────────────────────── */
  h1 {
    color:#003366 !important;
    font-weight:700 !important;
    border-bottom:3px solid #C9A84C;
    padding-bottom:.5rem;
  }
  h2 { color:#003366 !important; font-weight:600 !important; }
  h3 { color:#0052A3 !important; font-weight:600 !important; }

  /* ── Metrics ────────────────────────────────── */
  div[data-testid="stMetric"] {
    background:white !important;
    border:1px solid #E2E8F0 !important;
    border-radius:10px !important;
    padding:1.2rem !important;
    box-shadow:0 2px 8px rgba(0,51,102,0.08) !important;
    border-top:3px solid #003366 !important;
  }
  div[data-testid="stMetricLabel"] {
    color:#64748B !important;
    font-weight:600 !important;
    font-size:0.75rem !important;
    text-transform:uppercase !important;
    letter-spacing:0.05em !important;
  }
  div[data-testid="stMetricValue"] {
    color:#003366 !important;
    font-weight:700 !important;
  }

  /* ── Buttons ────────────────────────────────── */
  .stButton>button {
    background:#003366 !important;
    color:white !important;
    border:none !important;
    border-radius:8px !important;
    font-weight:600 !important;
    transition:all 0.2s !important;
  }
  .stButton>button:hover {
    background:#0052A3 !important;
    box-shadow:0 4px 15px rgba(0,51,102,0.3) !important;
    transform:translateY(-1px) !important;
  }
  .stButton>button[kind="primary"] {
    background:#0052A3 !important;
  }

  /* ── Cards / Expanders ──────────────────────── */
  div[data-testid="stExpander"] {
    background:white !important;
    border:1px solid #E2E8F0 !important;
    border-radius:10px !important;
    box-shadow:0 2px 8px rgba(0,0,0,0.06) !important;
  }
  div[data-testid="stExpander"] p,
  div[data-testid="stExpander"] span,
  div[data-testid="stExpander"] li {
    color:#1A202C !important;
  }
  div[data-testid="stExpander"] summary {
    color:#003366 !important;
    font-weight:600 !important;
  }

  /* ── Alert boxes ────────────────────────────── */
  div[data-testid="stInfo"] {
    background:#EFF6FF !important;
    border-left:4px solid #003366 !important;
  }
  div[data-testid="stInfo"] * {
    color:#1E40AF !important;
  }
  div[data-testid="stSuccess"] {
    background:#F0FDF4 !important;
    border-left:4px solid #16A34A !important;
  }
  div[data-testid="stSuccess"] * {
    color:#166534 !important;
  }
  div[data-testid="stWarning"] {
    background:#FFFBEB !important;
    border-left:4px solid #D97706 !important;
  }
  div[data-testid="stWarning"] * {
    color:#92400E !important;
  }
  div[data-testid="stError"] {
    background:#FEF2F2 !important;
    border-left:4px solid #DC2626 !important;
  }
  div[data-testid="stError"] * {
    color:#991B1B !important;
  }

  /* ── Form inputs ────────────────────────────── */
  .stTextInput label, .stSelectbox label,
  .stNumberInput label, .stTextArea label,
  .stFileUploader label, .stSlider label,
  .stCheckbox label {
    color:#003366 !important;
    font-weight:600 !important;
    font-size:0.85rem !important;
  }
  .stTextInput input,
  .stTextArea textarea,
  .stNumberInput input {
    border:1.5px solid #CBD5E1 !important;
    border-radius:8px !important;
    background:white !important;
    color:#1A202C !important;
  }
  .stTextInput input:focus,
  .stTextArea textarea:focus {
    border-color:#003366 !important;
    box-shadow:0 0 0 3px rgba(0,51,102,0.1) !important;
  }

  /* ── Selectbox ──────────────────────────────── */
  .stSelectbox div[data-baseweb="select"] span {
    color:#1A202C !important;
  }
  div[data-baseweb="select"] * {
    color:#1A202C !important;
  }

  /* ── Tables ─────────────────────────────────── */
  .dataframe td {
    color:#1A202C !important;
    font-size:0.85rem !important;
  }
  .dataframe th {
    color:#003366 !important;
    font-weight:700 !important;
    background:#EFF6FF !important;
  }

  /* ── Top bar ────────────────────────────────── */
  .topbar {
    background:linear-gradient(90deg,#003366,#0052A3);
    color:white;
    padding:.85rem 1.5rem;
    border-radius:10px;
    margin-bottom:1.5rem;
    display:flex;
    align-items:center;
    justify-content:space-between;
    box-shadow:0 4px 15px rgba(0,51,102,0.2);
  }
  .topbar * { color:white !important; }

  /* ── Badges ─────────────────────────────────── */
  .badge {
    display:inline-block;
    padding:.25rem .75rem;
    border-radius:20px;
    font-size:.72rem;
    font-weight:700;
  }
  .badge-blue   { background:#DBEAFE; color:#1E40AF; }
  .badge-green  { background:#DCFCE7; color:#166534; }
  .badge-red    { background:#FEE2E2; color:#991B1B; }
  .badge-yellow { background:#FEF9C3; color:#854D0E; }
  .badge-gold   { background:#FEF3C7; color:#92400E; }

  /* ── Login box ──────────────────────────────── */
  .login-box {
    max-width:440px;
    margin:3rem auto;
    background:white;
    border-radius:16px;
    padding:2.5rem;
    box-shadow:0 20px 60px rgba(0,51,102,0.15);
    border-top:5px solid #003366;
  }

  /* ── Code ───────────────────────────────────── */
  .stCodeBlock code { color:#E2E8F0 !important; }

  /* ── Caption ────────────────────────────────── */
  .stCaption {
    color:#64748B !important;
    font-size:0.78rem !important;
  }

  /* ── Checkbox ───────────────────────────────── */
  .stCheckbox span { color:#1A202C !important; }

  /* ── Hide Streamlit UI ──────────────────────── */
  #MainMenu, footer, header { visibility:hidden; }
</style>
"""

def inject_css():
    """Inject Corporate Banking CSS"""
    import streamlit as st
    st.markdown(CORPORATE_CSS, unsafe_allow_html=True)
