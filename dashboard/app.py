"""
BlockML-Gov Dashboard v5.0
Entry point — Login + Routing only
"""
import streamlit as st
import sys
import os

# Add dashboard to path
sys.path.insert(0, "/app")

st.set_page_config(
    page_title="BlockML-Gov | Banking AI Governance",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import modules
from styles import inject_css
from auth import show_login_page, handle_logout
from components.sidebar import render_sidebar
from components.topbar import render_topbar

# Pages imports
from pages.admin.user_management import show as admin_users
from pages.admin.audit_logs import show as admin_logs
from pages.data_scientist.upload_model import show as ds_upload
from pages.data_scientist.notifications import show as ds_notifications, show_popup_if_notifications
from pages.data_scientist.upload_dataset import show as ds_upload_dataset
from pages.data_scientist.mlflow_experiments import show as ds_mlflow
from pages.data_scientist.shap_explorer import show as ds_shap
from pages.compliance_officer.validation import show as co_validation
from pages.compliance_officer.history import show as co_history
from pages.ml_engineer.approval import show as mle_approval
from pages.ml_engineer.deployment import show as mle_deployment
from pages.ml_engineer.drift_monitoring import show as mle_drift
from pages.ml_engineer.history import show as mle_history
from pages.fraud_analyst.live_dashboard import show as fa_dashboard
from pages.fraud_analyst.alerts import show as fa_alerts
from pages.auditor.audit_trail import show as aud_trail
from pages.auditor.reports import show as aud_reports
from pages.auditor.certify_reports import show as aud_certify
from pages.regulator.system_status import show as reg_status

# Inject CSS
inject_css()

# ── Route map ────────────────────────────────────────
ROUTES = {
    "👥 User Management":       admin_users,
    "📋 Audit Logs":            admin_logs,
    "📬 Notifications":         ds_notifications,
    "📤 Upload Model":          ds_upload,
    "📊 Upload Dataset":        ds_upload_dataset,
    "🔬 MLflow Experiments":    ds_mlflow,
    "🔍 SHAP Explorer":         ds_shap,
    "✅ Compliance Validation":  co_validation,
    "📋 Validation History":    co_history,
    "🔧 Technical Approval":    mle_approval,
    "🚀 Model Deployment":      mle_deployment,
    "📜 Model History":         mle_history,
    "📉 Drift Monitoring":      mle_drift,
    "📊 Live Dashboard":        fa_dashboard,
    "🚨 Alerts":                fa_alerts,
    "📋 Audit Trail":           aud_trail,
    "📄 Compliance Reports":    aud_reports,
    "🔐 Integrity Check":       aud_certify,
    "📋 Certified Reports":     aud_certify,
    "🏛️ System Status":         reg_status,
    "🔍 Inspection":            reg_status,
    "📨 BAM Submissions":       reg_status,
}

# ── Main ─────────────────────────────────────────────
def main():
    if not st.session_state.get("logged_in", False):
        show_login_page()
        return

    user = st.session_state["user"]

    # Render sidebar + get selected page
    page = render_sidebar(user, handle_logout)

    # Popup notifications pour Data Scientist
    if user.get("role") == "Data Scientist":
        show_popup_if_notifications()


    # Render top bar
    render_topbar(page, user)

    # Route to page
    page_fn = ROUTES.get(page)
    if page_fn:
        page_fn(user)
    else:
        st.error(f"Page '{page}' not found")

main()
