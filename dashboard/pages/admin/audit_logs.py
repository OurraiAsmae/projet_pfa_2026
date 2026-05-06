"""Admin — Audit Logs — Light Theme"""
import streamlit as st
import pandas as pd
from utils.api_client import get_audit_logs

ACTION_COLORS = {
    "LOGIN_SUCCESS":  "#1F7A5A",
    "LOGIN_FAILED":   "#E05252",
    "LOGOUT":         "#8A8A8A",
    "CREATE_USER":    "#2563EB",
    "DELETE_USER":    "#E05252",
    "UPDATE_USER":    "#D97706",
    "SUBMIT_MODEL":   "#7C3AED",
    "VALIDATE":       "#1F7A5A",
    "DEPLOY":         "#2563EB",
    "APPROVE":        "#1F7A5A",
    "REJECT":         "#E05252",
}

PLOTLY_CONFIG = {"displayModeBar": False}


def _page_header(user: dict):
    from datetime import datetime
    hour = datetime.utcnow().hour + 1
    salut = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")

    st.markdown(f"""
    <style>
      #aud-header, #aud-header * {{ box-sizing: border-box; }}
    </style>
    <div id="aud-header" style="
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 1.8rem;
    ">
      <div>
        <h1 style="
          font-size: 1.75rem !important;
          font-weight: 800 !important;
          color: #1C1C1C !important;
          margin: 0 0 .25rem 0 !important;
          letter-spacing: -.03em !important;
          border: none !important;
          padding: 0 !important;
        ">Audit Logs</h1>
        <p style="
          font-size: .88rem;
          color: #8A8A8A;
          margin: 0;
          font-weight: 400;
        ">Track and monitor all system activity in real time.</p>
      </div>
      <div style="
        display: flex;
        align-items: center;
        gap: .75rem;
      ">
        <div style="
          background: #F5F7F6;
          border: 1px solid #E0E0E0;
          border-radius: 12px;
          padding: .55rem 1rem;
          font-size: .8rem;
          color: #2B2B2B;
          font-weight: 500;
        ">{salut}, <strong>{user['full_name']}</strong></div>
        <div style="
          width: 38px; height: 38px;
          border-radius: 50%;
          background: linear-gradient(135deg, #1F7A5A, #4CAF82);
          display: flex; align-items: center; justify-content: center;
          font-size: .9rem; font-weight: 800; color: white;
        ">{(user.get('full_name') or 'U')[0].upper()}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def show(user: dict):
    _page_header(user)
    token = st.session_state.get("token", "")

    logs = get_audit_logs(200, token=token)
    if not logs:
        st.info("No audit records available.")
        return

    df = pd.DataFrame(logs)

    total   = len(df)
    success = int(df["success"].sum()) if "success" in df.columns else 0
    failed  = total - success
    n_act   = df["action"].nunique() if "action" in df.columns else 0
    n_users = df["username"].nunique() if "username" in df.columns else 0

    # ── Métriques style Donezo ──────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Events",    total)
    c2.metric("Successful",      success)
    c3.metric("Failed",          failed)
    c4.metric("Active Users",    n_users)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # ── Graphes ─────────────────────────────────────
    try:
        import plotly.graph_objects as go

        g1, g2 = st.columns([3, 2])

        with g1:
            # Timeline ou répartition par action
            ts_col = next((c for c in ["timestamp","created_at","date","time"] if c in df.columns), None)

            if ts_col:
                dft = df.copy()
                dft[ts_col] = pd.to_datetime(dft[ts_col], errors="coerce")
                dft = dft.dropna(subset=[ts_col]).sort_values(ts_col)
                dft["heure"] = dft[ts_col].dt.floor("H")
                grouped = dft.groupby(["heure","action"]).size().reset_index(name="n")

                fig = go.Figure()
                for action in grouped["action"].unique():
                    sub   = grouped[grouped["action"] == action]
                    color = ACTION_COLORS.get(action, "#1F7A5A")
                    fig.add_trace(go.Scatter(
                        x=sub["heure"], y=sub["n"],
                        mode="lines+markers", name=action,
                        line=dict(color=color, width=2.5),
                        marker=dict(size=7, color=color,
                                    line=dict(color="white", width=2)),
                        hovertemplate="%{x|%H:%M} — %{y} event(s)<extra></extra>",
                    ))
                title_text = "Activity Timeline"
            else:
                action_counts = df["action"].value_counts()
                fig = go.Figure(go.Bar(
                    x=action_counts.index,
                    y=action_counts.values,
                    marker=dict(
                        color=[ACTION_COLORS.get(a, "#1F7A5A") for a in action_counts.index],
                        line_width=0,
                    ),
                    hovertemplate="%{x}: %{y}<extra></extra>",
                ))
                title_text = "Event Distribution"

            fig.update_layout(
                title=dict(text=title_text,
                           font=dict(size=14, color="#1C1C1C", family="Inter"),
                           x=0),
                plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=0, r=0, t=42, b=0),
                font=dict(family="Inter", size=11, color="#8A8A8A"),
                height=360, showlegend=True,
                legend=dict(orientation="h", y=-0.18, x=0,
                            font=dict(size=10)),
                xaxis=dict(gridcolor="#F0F0F0", linecolor="#E0E0E0",
                           showgrid=True, zeroline=False),
                yaxis=dict(gridcolor="#F0F0F0", linecolor="#E0E0E0",
                           showgrid=True, zeroline=False, rangemode="tozero"),
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

        with g2:
            if "success" in df.columns and total > 0:
                pct = int(success / total * 100)
                vals   = [success, failed] if failed > 0 else [success]
                labels = ["Success", "Failed"] if failed > 0 else ["Success"]
                colors = ["#1F7A5A", "#E05252"] if failed > 0 else ["#1F7A5A"]

                fig2 = go.Figure(go.Pie(
                    labels=labels, values=vals, hole=.62,
                    marker=dict(colors=colors,
                                line=dict(color="white", width=2.5)),
                    textinfo="label+percent" if failed > 0 else "none",
                    textfont=dict(size=11, family="Inter"),
                    textposition="outside" if failed > 0 else "none",
                    hovertemplate="%{label}: %{value}<extra></extra>",
                ))
                fig2.update_layout(
                    title=dict(text="Success Rate",
                               font=dict(size=14, color="#1C1C1C", family="Inter"),
                               x=0),
                    showlegend=False,
                    paper_bgcolor="white",
                    margin=dict(l=10, r=10, t=42, b=30),
                    height=360,
                    annotations=[dict(
                        text=f"<b>{pct}%</b>",
                        x=.5, y=.5,
                        font=dict(size=32, color="#1C1C1C", family="Inter"),
                        showarrow=False,
                    )],
                )
                st.plotly_chart(fig2, use_container_width=True, config=PLOTLY_CONFIG)

    except ImportError:
        st.warning("Plotly not available.")

    # ── Tableau ─────────────────────────────────────
    st.subheader("Event Log")
    st.dataframe(df, use_container_width=True, hide_index=True)
