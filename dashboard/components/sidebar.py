"""BlockML-Gov — Sidebar v6 (fixed header/footer + collapse toggle)"""
import streamlit as st
import os
import urllib.parse

API_URL = os.getenv("API_URL", "http://api:8000")

# Normalise les rôles snake_case (DB) → display name (UI)
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

PAGES_MAP = {
    "Admin":              ["User Management", "Audit Logs"],
    "Data Scientist":     ["Notifications", "Upload Model", "Upload Dataset", "MLflow Experiments", "SHAP Explorer"],
    "Compliance Officer": ["Compliance Validation", "Validation History"],
    "ML Engineer":        ["Technical Approval", "Model Deployment", "Model History", "Drift Monitoring"],
    "Fraud Analyst":      ["Live Dashboard", "Alerts"],
    "Internal Auditor":   ["Audit Trail", "Compliance Reports"],
    "External Auditor":   ["Integrity Check", "Certified Reports"],
    "Regulator":          ["System Status"],
}

PAGE_SVG = {
    "User Management":       '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    "Audit Logs":            '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    "Notifications":         '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>',
    "Upload Model":          '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/></svg>',
    "Upload Dataset":        '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',
    "MLflow Experiments":    '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "SHAP Explorer":         '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    "Compliance Validation": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
    "Validation History":    '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "Technical Approval":    '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
    "Model Deployment":      '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    "Model History":         '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>',
    "Drift Monitoring":      '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "Live Dashboard":        '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>',
    "Alerts":                '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "Audit Trail":           '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
    "Compliance Reports":    '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/></svg>',
    "Integrity Check":       '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "Certified Reports":     '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="6"/><path d="M15.477 12.89L17 22l-5-3-5 3 1.523-9.11"/></svg>',
    "System Status":         '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>',
    "Inspection":            '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>',
    "BAM Submissions":       '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
    "Settings":              '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
    "Help":                  '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "Logout":                '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>',
}

# SVGs for collapse button (no curly braces issue — built as plain strings)
_ARROW_LEFT  = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>'
_ARROW_RIGHT = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>'


def _uri(name: str, color: str) -> str:
    svg = PAGE_SVG.get(name, "").replace("COLOR", color)
    return "data:image/svg+xml," + urllib.parse.quote(svg)


def _css(pages: list) -> str:
    base = """
<style>
/* ── Animations ─────────────────────────────── */
@keyframes slideIn {
  from { opacity: 0; transform: translateX(-8px); }
  to   { opacity: 1; transform: translateX(0); }
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 4px 14px rgba(31,122,90,0.25); }
  50%       { box-shadow: 0 4px 22px rgba(31,122,90,0.45); }
}

/* ── Sidebar container ───────────────────────── */
section[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E8E8E8 !important;
    overflow: hidden !important;
}

/* ── FIXED LAYOUT: outer div fills 100vh ─────── */
section[data-testid="stSidebar"] > div:first-child {
    height: 100vh !important;
    overflow: hidden !important;
    padding: 0 !important;
    display: flex !important;
    flex-direction: column !important;
}

/* ── stVerticalBlock = flex column ───────────── */
section[data-testid="stSidebar"] > div:first-child > div[data-testid="stVerticalBlock"] {
    display: flex !important;
    flex-direction: column !important;
    height: 100vh !important;
    overflow: hidden !important;
    flex: 1 !important;
    gap: 0 !important;
    padding: 0 !important;
}

/* ── child(1): CSS injection — zero height ───── */
section[data-testid="stSidebar"] > div:first-child > div[data-testid="stVerticalBlock"] > div:nth-child(1) {
    flex-shrink: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
}

/* ── child(2): Header — fixed at top ─────────── */
section[data-testid="stSidebar"] > div:first-child > div[data-testid="stVerticalBlock"] > div:nth-child(2) {
    flex-shrink: 0 !important;
    background: #FFFFFF !important;
    z-index: 10 !important;
}

/* ── child(3): MENU label — fixed below header ─ */
section[data-testid="stSidebar"] > div:first-child > div[data-testid="stVerticalBlock"] > div:nth-child(3) {
    flex-shrink: 0 !important;
}

/* ── child(4): Radio nav — SCROLLABLE, fills space */
section[data-testid="stSidebar"] > div:first-child > div[data-testid="stVerticalBlock"] > div:nth-child(4) {
    flex: 1 !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    min-height: 0 !important;
    scrollbar-width: thin !important;
    scrollbar-color: #E5E7EB transparent !important;
}

/* ── child(5): GENERAL footer — fixed at bottom ─ */
section[data-testid="stSidebar"] > div:first-child > div[data-testid="stVerticalBlock"] > div:nth-child(5) {
    flex-shrink: 0 !important;
    background: #FFFFFF !important;
    border-top: 1px solid #F0F0F0 !important;
    z-index: 10 !important;
}

/* ── child(6): Logout button — fixed at bottom ── */
section[data-testid="stSidebar"] > div:first-child > div[data-testid="stVerticalBlock"] > div:nth-child(6) {
    flex-shrink: 0 !important;
    background: #FFFFFF !important;
}

/* ── child(7): User card — fixed at bottom ─────── */
section[data-testid="stSidebar"] > div:first-child > div[data-testid="stVerticalBlock"] > div:nth-child(7) {
    flex-shrink: 0 !important;
    background: #FFFFFF !important;
}

/* ── COLLAPSE STATE ──────────────────────────── */
section[data-testid="stSidebar"].sb-collapsed {
    width: 74px !important;
    min-width: 74px !important;
}

/* Hide text in collapsed mode */
section[data-testid="stSidebar"].sb-collapsed .sb-text {
    display: none !important;
}

/* Center nav items when collapsed */
section[data-testid="stSidebar"].sb-collapsed .stRadio > div > label {
    justify-content: center !important;
    padding: .72rem .5rem !important;
}
section[data-testid="stSidebar"].sb-collapsed .stRadio > div > label::before {
    margin-right: 0 !important;
}

/* Center gen-items when collapsed */
section[data-testid="stSidebar"].sb-collapsed .gen-item {
    justify-content: center !important;
    padding: .65rem !important;
    margin: 1px .4rem !important;
}

/* Collapse section label */
section[data-testid="stSidebar"].sb-collapsed .sb-section-label {
    display: none !important;
}

/* User card in collapsed: show only avatar */
section[data-testid="stSidebar"].sb-collapsed .sb-user-card {
    justify-content: center !important;
    padding: .5rem !important;
}

/* Smooth width transition */
section[data-testid="stSidebar"] {
    transition: width 0.25s cubic-bezier(.4,0,.2,1) !important;
}

/* ── Collapse toggle button ──────────────────── */
#sb-toggle {
    background: transparent !important;
    border: 1px solid #E0E0E0 !important;
    border-radius: 8px !important;
    width: 28px !important; height: 28px !important;
    cursor: pointer !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    color: #9CA3AF !important;
    transition: all .2s ease !important;
    padding: 0 !important;
    flex-shrink: 0 !important;
    outline: none !important;
}
#sb-toggle:hover {
    background: #F0FAF6 !important;
    border-color: #1F7A5A !important;
    color: #1F7A5A !important;
}
#sb-toggle:active { transform: scale(.93) !important; }
#sb-toggle:focus  { outline: none !important; box-shadow: none !important; }

/* Arrow rotation via CSS when collapsed (pas de JS) */
#sb-toggle svg {
    transition: transform 0.25s cubic-bezier(.4,0,.2,1) !important;
}
section[data-testid="stSidebar"].sb-collapsed #sb-toggle svg {
    transform: rotate(180deg) !important;
}

/* ── Radio: masquer label ────────────────────── */
section[data-testid="stSidebar"] .stRadio > label { display: none !important; }

/* ── Radio: layout colonne ───────────────────── */
section[data-testid="stSidebar"] .stRadio > div {
    display: flex !important; flex-direction: column !important;
    gap: 3px !important; padding: .4rem .7rem !important;
}

/* ── Item inactif ────────────────────────────── */
section[data-testid="stSidebar"] .stRadio > div > label {
    display: flex !important; align-items: center !important;
    padding: .82rem 1rem !important; border-radius: 11px !important;
    cursor: pointer !important; border: none !important; margin: 0 !important;
    background: transparent !important;
    transition: background .18s ease, transform .18s ease, color .18s ease !important;
    position: relative !important; overflow: hidden !important;
}
section[data-testid="stSidebar"] .stRadio > div > label:hover {
    background: #F0FAF6 !important;
    transform: translateX(3px) !important;
}
section[data-testid="stSidebar"] .stRadio > div > label:hover p {
    color: #1F7A5A !important;
}
section[data-testid="stSidebar"] .stRadio > div > label:active {
    transform: translateX(3px) scale(.98) !important;
    background: #E0F4ED !important;
}

/* Cacher cercle natif */
section[data-testid="stSidebar"] .stRadio > div > label > div:first-child {
    display: none !important;
}

/* Texte inactif */
section[data-testid="stSidebar"] .stRadio > div > label p {
    font-size: .92rem !important; font-weight: 500 !important;
    color: #6B7280 !important; margin: 0 !important; padding: 0 !important;
    transition: color .18s ease !important; white-space: nowrap !important;
    overflow: hidden !important; text-overflow: ellipsis !important;
}

/* ── Item ACTIF ──────────────────────────────── */
section[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {
    background: #1F7A5A !important;
    box-shadow: 0 4px 14px rgba(31,122,90,0.28) !important;
    transform: none !important;
    animation: pulse 2.5s ease-in-out infinite !important;
}
section[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) p {
    color: #FFFFFF !important; font-weight: 700 !important;
}

/* Icône via ::before */
section[data-testid="stSidebar"] .stRadio > div > label::before {
    content: '' !important; display: inline-block !important;
    width: 18px !important; height: 18px !important; min-width: 18px !important;
    background-size: contain !important; background-repeat: no-repeat !important;
    background-position: center !important; margin-right: .7rem !important;
    transition: transform .18s ease !important;
}
section[data-testid="stSidebar"] .stRadio > div > label:hover::before {
    transform: scale(1.1) !important;
}

/* ── Gen-items hover (CSS pur, pas de JS inline) ─ */
.gen-item {
    display: flex !important;
    align-items: center !important;
    gap: .75rem !important;
    padding: .75rem 1rem !important;
    border-radius: 11px !important;
    margin: 2px .6rem !important;
    cursor: pointer !important;
    transition: background .18s ease, transform .18s ease !important;
}
.gen-item:hover {
    background: #F0FAF6 !important;
    transform: translateX(3px) !important;
}
.gen-item:hover .gen-label {
    color: #1F7A5A !important;
}
.gen-item:active {
    transform: translateX(3px) scale(.97) !important;
}
#logout-visual:hover {
    background: #FEF2F2 !important;
    transform: translateX(3px) !important;
}
.gen-label {
    font-size: .92rem !important;
    font-weight: 500 !important;
    color: #6B7280 !important;
    transition: color .18s ease !important;
    white-space: nowrap !important;
}

/* ── Bouton Logout réel — stylé comme gen-item ─ */
section[data-testid="stSidebar"] .stButton {
    padding: 0 .6rem !important;
    margin: 0 !important;
}
section[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    background: transparent !important;
    border: none !important;
    color: #EF4444 !important;
    font-size: .92rem !important;
    font-weight: 500 !important;
    padding: .75rem 1rem !important;
    border-radius: 11px !important;
    cursor: pointer !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    transition: background .18s ease, transform .18s ease !important;
    outline: none !important;
    box-shadow: none !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #FEF2F2 !important;
    transform: translateX(3px) !important;
}
section[data-testid="stSidebar"] .stButton > button:active {
    transform: translateX(3px) scale(.97) !important;
}
section[data-testid="stSidebar"] .stButton > button:focus {
    outline: none !important;
    box-shadow: none !important;
}
section[data-testid="stSidebar"] .stButton > button::before {
    content: '' !important;
    display: inline-block !important;
    width: 18px !important;
    height: 18px !important;
    min-width: 18px !important;
    margin-right: .7rem !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23EF4444' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4'/%3E%3Cpolyline points='16 17 21 12 16 7'/%3E%3Cline x1='21' y1='12' x2='9' y2='12'/%3E%3C/svg%3E") !important;
    background-size: contain !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
}
</style>
"""
    # Per-item icon rules
    icon_css = "<style>"
    for i, page in enumerate(pages, 1):
        g     = _uri(page, "#6B7280")
        w     = _uri(page, "#FFFFFF")
        green = _uri(page, "#1F7A5A")
        icon_css += f"""
section[data-testid="stSidebar"] .stRadio > div > label:nth-child({i})::before {{
    background-image: url("{g}") !important;
}}
section[data-testid="stSidebar"] .stRadio > div > label:nth-child({i}):hover::before {{
    background-image: url("{green}") !important;
}}
section[data-testid="stSidebar"] .stRadio > div > label:nth-child({i}):has(input:checked)::before {{
    background-image: url("{w}") !important;
}}
"""
    icon_css += "</style>"

    return base + icon_css


def render_sidebar(user: dict, on_logout) -> str:
    # Normalise snake_case → display name
    role = ROLE_DISPLAY.get(user["role"], user["role"])
    # Met à jour le user dict pour que le reste du code utilise le bon display name
    user = {**user, "role": role}
    pages = PAGES_MAP.get(role, ["Dashboard"])

    if "current_page" not in st.session_state:
        st.session_state["current_page"] = pages[0]
    if st.session_state["current_page"] not in pages:
        st.session_state["current_page"] = pages[0]

    current = st.session_state["current_page"]

    with st.sidebar:
        # ── [child 1] CSS + JS injection ──────────────────────
        st.markdown(_css(pages), unsafe_allow_html=True)

        # ── [child 2] HEADER (fixed top) ──────────────────────
        st.markdown(
            '<div style="padding:1.3rem 1.1rem 1rem;border-bottom:1px solid #F0F0F0;background:#FFFFFF;">'
            '<div style="display:flex;align-items:center;gap:.75rem;">'
            '<div style="width:38px;height:38px;border-radius:10px;flex-shrink:0;'
            'background:linear-gradient(135deg,#1F7A5A,#4CAF82);'
            'display:flex;align-items:center;justify-content:center;'
            'font-size:1.05rem;font-weight:900;color:#FFF;'
            'box-shadow:0 4px 10px rgba(31,122,90,0.35);">B</div>'
            '<div style="min-width:0;">'
            '<div style="font-size:1.15rem;font-weight:800;color:#1C1C1C;'
            'letter-spacing:-.03em;line-height:1.1;white-space:nowrap;">'
            'BlockML<span style="color:#1F7A5A;">.</span>Gov</div>'
            '<div style="font-size:.65rem;color:#9CA3AF;margin-top:.15rem;'
            'letter-spacing:.03em;white-space:nowrap;">AI Governance Platform</div>'
            '</div></div></div>',
            unsafe_allow_html=True
        )

        # ── [child 3] MENU label ───────────────────────────────
        st.markdown("""
        <div class="sb-section-label" style="
          padding:.9rem 1.1rem .3rem;
          font-size:.67rem;font-weight:700;
          color:#9CA3AF;letter-spacing:.12em;
        ">MENU</div>
        """, unsafe_allow_html=True)

        # ── [child 4] Navigation radio ─────────────────────────
        idx = pages.index(current)
        selected = st.radio("nav", pages, index=idx,
                            label_visibility="collapsed", key="sidebar_nav")
        if selected != current:
            st.session_state["current_page"] = selected
            st.rerun()

        # ── [child 5] GENERAL footer (fixed bottom) ────────────
        svg_settings = PAGE_SVG.get("Settings", "").replace("COLOR", "#9CA3AF")
        svg_help     = PAGE_SVG.get("Help",     "").replace("COLOR", "#9CA3AF")
        svg_logout   = PAGE_SVG.get("Logout",   "").replace("COLOR", "#EF4444")
        initials     = (user.get("full_name") or "U")[0].upper()

        st.markdown(
            f'<div style="padding:.4rem 0 0;">'
            f'<div class="sb-section-label" style="padding:.3rem 1rem .2rem;font-size:.63rem;font-weight:700;color:#9CA3AF;letter-spacing:.12em;">GENERAL</div>'
            f'<div class="gen-item">{svg_settings}<span class="gen-label sb-text">Settings</span></div>'
            f'<div class="gen-item">{svg_help}<span class="gen-label sb-text">Help</span></div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # ── [child 6] Logout button (real, visible, styled via CSS) ────
        st.button("Logout", key="logout_real", on_click=on_logout)

        # ── [child 7] User card ─────────────────────────────────
        st.markdown(
            f'<div style="padding:.6rem .9rem .85rem;">'
            f'<div class="sb-user-card" style="display:flex;align-items:center;gap:.6rem;background:#F9FAFB;border:1px solid #E8EDE9;border-radius:12px;padding:.7rem .9rem;">'
            f'<div style="width:32px;height:32px;border-radius:50%;flex-shrink:0;background:linear-gradient(135deg,#1F7A5A,#4CAF82);display:flex;align-items:center;justify-content:center;font-size:.8rem;font-weight:800;color:white;box-shadow:0 2px 6px rgba(31,122,90,.25);">{initials}</div>'
            f'<div class="sb-text" style="min-width:0;overflow:hidden;">'
            f'<div style="font-size:.8rem;font-weight:700;color:#1C1C1C;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{user["full_name"]}</div>'
            f'<div style="font-size:.67rem;color:#1F7A5A;font-weight:600;white-space:nowrap;">{user["role"]}</div>'
            f'</div></div></div>',
            unsafe_allow_html=True
        )

    return st.session_state["current_page"]
