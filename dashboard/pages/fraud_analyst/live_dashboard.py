"""Fraud Analyst — Live Dashboard"""
import streamlit as st
import pandas as pd
import time
from datetime import datetime
from utils.api_client import get_active_model, API_URL
import httpx

TIMEOUT = 10

def _get_recent_transactions(limit: int = 50) -> list:
    """Get recent transactions from Redis via API"""
    try:
        r = httpx.get(f"{API_URL}/transactions/recent",
                      params={"limit": limit}, timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json().get("transactions", [])
    except:
        pass
    return []

def _get_stats() -> dict:
    """Get fraud stats from API"""
    try:
        r = httpx.get(f"{API_URL}/stats", timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {}

def show(user: dict):
    st.title("📊 Live Fraud Dashboard")

    # Auto-refresh
    col_title, col_refresh = st.columns([3, 1])
    with col_refresh:
        auto = st.checkbox("🔄 Auto-refresh (10s)")
        if st.button("🔄 Refresh Now"):
            st.rerun()

    # Active model
    active = get_active_model()
    if active:
        st.markdown(f"""
        <div style="background:#EFF6FF;border-left:4px solid #003366;
                    border-radius:8px;padding:.8rem;margin-bottom:1rem;">
            <span style="font-size:.75rem;color:#64748B;font-weight:600;">
            🟢 ACTIVE MODEL</span><br/>
            <span style="font-weight:700;color:#003366;">
            {active.get('model_id','N/A')}</span>
            <span style="color:#0052A3;font-size:.85rem;">
            — {active.get('model_type','N/A')}</span>
        </div>
        """, unsafe_allow_html=True)

    # Stats
    stats = _get_stats()
    total    = stats.get("total", 0)
    fraude   = stats.get("FRAUDE", stats.get("fraude", 0))
    ambigu   = stats.get("AMBIGU", stats.get("ambigu", 0))
    legitime = stats.get("LEGITIME", stats.get("legitime", 0))
    total    = fraude + ambigu + legitime if total == 0 else total

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📊 Total Transactions", f"{total:,}")
    c2.metric("🔴 Fraud (Auto-blocked)",
              f"{fraude:,}",
              f"{fraude/total*100:.1f}%" if total > 0 else "0%")
    c3.metric("🟡 Amber (Human Review)",
              f"{ambigu:,}",
              f"{ambigu/total*100:.1f}%" if total > 0 else "0%")
    c4.metric("🟢 Legitimate (Auto-approved)",
              f"{legitime:,}",
              f"{legitime/total*100:.1f}%" if total > 0 else "0%")

    st.markdown("---")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        zone_filter = st.multiselect(
            "Filter by Zone",
            ["🔴 FRAUDE", "🟡 AMBIGU", "🟢 LEGITIME"],
            default=["🔴 FRAUDE", "🟡 AMBIGU"])
    with col2:
        limit = st.slider("Max transactions", 10, 100, 50)
    with col3:
        min_score = st.slider("Min score", 0.0, 1.0, 0.0)

    # Recent transactions
    st.subheader("🔴 Recent Flagged Transactions")
    txs = _get_recent_transactions(limit)

    if not txs:
        st.info("No recent transactions found. Transactions will appear here as they are processed.")
        # Show demo data
        _show_demo_table()
    else:
        _show_transactions_table(txs, zone_filter, min_score)

    # Auto-refresh
    if auto:
        time.sleep(10)
        st.rerun()


def _show_transactions_table(txs: list, zone_filter: list, min_score: float):
    """Display transactions table"""
    zone_map = {
        "🔴 FRAUDE": "FRAUDE",
        "🟡 AMBIGU": "AMBIGU",
        "🟢 LEGITIME": "LEGITIME"
    }
    allowed_zones = [zone_map[z] for z in zone_filter]

    rows = []
    for tx in txs:
        zone  = tx.get("zone", tx.get("decision", ""))
        score = tx.get("score", 0)
        if zone not in allowed_zones:
            continue
        if score < min_score:
            continue

        zone_icon = {"FRAUDE": "🔴", "AMBIGU": "🟡", "LEGITIME": "🟢"}.get(zone, "⚪")
        rows.append({
            "Zone":       f"{zone_icon} {zone}",
            "TX ID":      tx.get("tx_id", "")[:20],
            "Score":      f"{score:.4f}",
            "Amount":     f"{tx.get('montant_mad', 0):,.0f} MAD",
            "Country":    tx.get("pays_transaction", ""),
            "Device":     tx.get("device_type", ""),
            "Hour":       tx.get("heure", ""),
            "Timestamp":  str(tx.get("timestamp", ""))[:16],
        })

    if not rows:
        st.info("No transactions match the filter.")
        return

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)
    st.caption(f"Showing {len(rows)} transactions")


def _show_demo_table():
    """Show demo data when no real transactions"""
    st.caption("📌 Demo data — connect your transaction stream")
    import random, hashlib
    random.seed(42)
    rows = []
    zones = ["FRAUDE", "FRAUDE", "AMBIGU", "AMBIGU", "LEGITIME"]
    for i in range(10):
        zone  = random.choice(zones)
        score = random.uniform(0.85, 0.99) if zone == "FRAUDE" else \
                random.uniform(0.40, 0.85) if zone == "AMBIGU" else \
                random.uniform(0.01, 0.39)
        zone_icon = {"FRAUDE": "🔴", "AMBIGU": "🟡", "LEGITIME": "🟢"}[zone]
        rows.append({
            "Zone":    f"{zone_icon} {zone}",
            "TX ID":   f"TX-DEMO-{i+1:03d}",
            "Score":   f"{score:.4f}",
            "Amount":  f"{random.randint(500,50000):,} MAD",
            "Country": random.choice(["MA", "FR", "ES", "US"]),
            "Device":  random.choice(["mobile", "web", "atm"]),
            "Hour":    random.randint(0, 23),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
