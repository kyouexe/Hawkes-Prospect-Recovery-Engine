"""Hawkes-Prospect Recovery Engine — Streamlit UI."""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
import uuid

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from data.database import (
    init_db, get_all_events, get_recovery_stats,
    get_audit_log, get_hawkes_metrics, create_p2p_contract
)
from engine.pipeline import run_recovery_pipeline
from engine.p2p_parser import parse_promise
from engine.hawkes import HawkesScheduler
from engine.prospect import ProspectFramer

# ── page config ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="Hawkes-Prospect Recovery Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── custom CSS & animations ──────────────────────────────────────────

st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Dark Theme App Background */
    .stApp {
        background: radial-gradient(circle at 50% 10%, #171d42 0%, #0a0e27 60%, #050816 100%);
        color: #e2e8f0;
    }

    /* Keyframe Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes dotPulse {
        0% { transform: scale(0.95); opacity: 0.6; box-shadow: 0 0 0 0 rgba(0, 230, 118, 0.7); }
        70% { transform: scale(1.15); opacity: 1; box-shadow: 0 0 0 8px rgba(0, 230, 118, 0); }
        100% { transform: scale(0.95); opacity: 0.6; box-shadow: 0 0 0 0 rgba(0, 230, 118, 0); }
    }

    /* Top Hero Header */
    .hero-header {
        background: linear-gradient(135deg, rgba(25, 33, 68, 0.75), rgba(15, 20, 45, 0.85));
        border: 1px solid rgba(56, 97, 251, 0.25);
        border-radius: 20px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(16px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.37);
        display: flex;
        align-items: center;
        justify-content: space-between;
        animation: fadeIn 0.5s ease-out;
    }

    .hero-title-group {
        display: flex;
        align-items: center;
        gap: 1.2rem;
    }

    .hero-icon {
        font-size: 2.8rem;
        background: linear-gradient(135deg, #3861fb, #61dafb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 12px rgba(56, 97, 251, 0.5));
    }

    .hero-title {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #ffffff 0%, #61dafb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.2;
    }

    .hero-subtitle {
        font-size: 0.88rem;
        color: #94a3b8;
        margin-top: 0.25rem;
        margin-bottom: 0;
        font-weight: 400;
    }

    .status-badge {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        background: rgba(13, 25, 48, 0.6);
        border: 1px solid rgba(0, 230, 118, 0.3);
        padding: 0.5rem 1rem;
        border-radius: 30px;
        font-size: 0.8rem;
        color: #00e676;
        font-weight: 600;
    }

    .status-dot {
        width: 9px;
        height: 9px;
        background-color: #00e676;
        border-radius: 50%;
        animation: dotPulse 2s infinite ease-in-out;
    }

    /* KPI Glassmorphism Cards */
    .kpi-card {
        background: linear-gradient(135deg, rgba(30, 42, 82, 0.7), rgba(18, 24, 52, 0.85));
        border: 1px solid rgba(56, 97, 251, 0.2);
        border-radius: 16px;
        padding: 1.25rem 1.4rem;
        text-align: left;
        backdrop-filter: blur(12px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
        overflow: hidden;
    }

    .kpi-card:hover {
        transform: translateY(-4px);
        border-color: rgba(97, 218, 251, 0.5);
        box-shadow: 0 12px 30px rgba(56, 97, 251, 0.25);
    }

    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, #3861fb, #61dafb);
    }

    .kpi-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }

    .kpi-label {
        font-size: 0.78rem;
        color: #94a3b8;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .kpi-icon {
        font-size: 1.2rem;
        opacity: 0.8;
    }

    .kpi-value {
        font-size: 1.85rem;
        font-weight: 800;
        background: linear-gradient(90deg, #ffffff 30%, #61dafb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.1;
    }

    /* Custom Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background: rgba(15, 20, 45, 0.5);
        padding: 6px;
        border-radius: 14px;
        border: 1px solid rgba(56, 97, 251, 0.15);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        color: #94a3b8;
        padding: 10px 22px;
        font-weight: 600;
        font-size: 0.9rem;
        border: none !important;
        transition: all 0.2s ease;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(56, 97, 251, 0.3), rgba(97, 218, 251, 0.15)) !important;
        color: #61dafb !important;
        box-shadow: 0 4px 15px rgba(56, 97, 251, 0.2);
    }

    /* Sticky Footer */
    .app-footer {
        margin-top: 3rem;
        padding: 1.5rem;
        border-top: 1px solid rgba(56, 97, 251, 0.15);
        background: rgba(10, 14, 39, 0.6);
        border-radius: 16px 16px 0 0;
        text-align: center;
        color: #64748b;
        font-size: 0.82rem;
        backdrop-filter: blur(10px);
    }

    .app-footer span {
        color: #3861fb;
        font-weight: 600;
    }

    /* Buttons & Controls */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    /* Hide default Streamlit padding at top */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ── init DB ──────────────────────────────────────────────────────────

init_db()

# ── Hero Header Banner ───────────────────────────────────────────────

st.markdown("""
<div class="hero-header">
    <div class="hero-title-group">
        <div class="hero-icon">⚡</div>
        <div>
            <h1 class="hero-title">Hawkes-Prospect Recovery Engine</h1>
            <p class="hero-subtitle">Autonomous AI Revenue Recovery • Behavioral Framing & Policy Guardrails • Razorpay Track 03</p>
        </div>
    </div>
    <div class="status-badge">
        <span class="status-dot"></span>
        <span>ENGINE LIVE • OFFLINE MOCK MODE</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Top Control Bar ──────────────────────────────────────────────────

col_ctrl1, col_ctrl2 = st.columns([4, 1])

with col_ctrl2:
    if st.button("🔄 Regenerate Seed Data", use_container_width=True):
        init_db(force_reseed=True)
        st.toast("Database re-seeded successfully!", icon="✅")
        time.sleep(0.5)
        st.rerun()

# ── KPI Cards Section ────────────────────────────────────────────────

stats = get_recovery_stats()

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">
            <span class="kpi-label">Total At-Risk</span>
            <span class="kpi-icon">💰</span>
        </div>
        <div class="kpi-value">₹{stats['total_at_risk']:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">
            <span class="kpi-label">Total Recovered</span>
            <span class="kpi-icon">🎯</span>
        </div>
        <div class="kpi-value">₹{stats['total_recovered']:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">
            <span class="kpi-label">Recovery Rate</span>
            <span class="kpi-icon">⚡</span>
        </div>
        <div class="kpi-value">{stats['recovery_rate']}%</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">
            <span class="kpi-label">Guardrail Interventions</span>
            <span class="kpi-icon">🛡️</span>
        </div>
        <div class="kpi-value">{stats['guardrail_interventions']}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Main Content Tabs ────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    "🚀 Recovery Pipeline",
    "🧪 P2P Sandbox",
    "📊 Analytics & Math Models",
    "📋 Immutable Audit Log",
])

# ── Tab 1: Recovery Pipeline ─────────────────────────────────────────

with tab1:
    st.subheader("Batch Recovery Orchestrator")
    st.caption("Triggers the Hawkes self-exciting retry process, Prospect Theory framing, and Guardrail checks.")

    if st.button("▶ Run Batch Recovery Pipeline", type="primary", use_container_width=True):
        events = get_all_events()
        pending = [e for e in events if e["status"] == "PENDING"]

        if not pending:
            st.info("No pending payment failure events to process.")
        else:
            progress = st.progress(0, text="Initializing recovery engine…")
            results = []

            for i, evt in enumerate(pending):
                progress.progress(
                    (i + 1) / len(pending),
                    text=f"Processing {evt['event_id']} ({evt['customer_name']}) via Hawkes & Prospect Engine…",
                )
                res = run_recovery_pipeline(evt["event_id"])
                res["event_id"] = evt["event_id"]
                res["customer_name"] = evt["customer_name"]
                res["amount"] = evt["amount"]
                results.append(res)
                time.sleep(0.12)

            progress.progress(1.0, text="✅ Batch recovery pipeline execution complete!")
            st.success(f"Successfully processed {len(results)} failed payment events.")

            # Pipeline Funnel Visualization
            statuses = pd.Series([r["status"] for r in results])
            funnel_data = {
                "Stage": ["Failed Input", "Retried", "Recovered", "Escalated", "Retry Pending"],
                "Count": [
                    len(results),
                    len([r for r in results if r["status"] != "SKIPPED"]),
                    int((statuses == "RECOVERED").sum()),
                    int((statuses == "ESCALATED").sum()),
                    int((statuses == "RETRY_PENDING").sum()),
                ],
            }
            fig = go.Figure(go.Funnel(
                y=funnel_data["Stage"],
                x=funnel_data["Count"],
                textinfo="value+percent initial",
                marker=dict(color=["#3861fb", "#5b7fff", "#00e676", "#ffb300", "#94a3b8"]),
            ))
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#c8d6e5", family="Inter"),
                title="Recovery Pipeline Funnel Conversion",
                height=350,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Live Payment Events Queue")
    all_events = get_all_events()
    if all_events:
        df_events = pd.DataFrame(all_events)
        display_cols = ["event_id", "customer_name", "amount", "bank", "error_code", "category", "status"]

        st.dataframe(
            df_events[display_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "amount": st.column_config.NumberColumn("Amount (₹)", format="₹%d"),
                "event_id": "Event ID",
                "customer_name": "Customer",
                "error_code": "Error Code",
                "status": "Current Status"
            }
        )

# ── Tab 2: P2P Sandbox ──────────────────────────────────────────────

with tab2:
    st.subheader("Promise-to-Pay (P2P) Natural Language Sandbox")
    st.caption("Tests the rule-based intent parser that extracts promised dates from customer messages.")

    col_input, col_output = st.columns([1, 1], gap="medium")

    with col_input:
        user_text = st.text_area(
            "Customer Reply Message",
            value=st.session_state.get("p2p_input", "I will pay on Friday"),
            height=120,
            placeholder="e.g. 'will pay Friday', 'in 3 days', 'by the 5th'",
        )

        st.markdown("**Quick Preset Examples:**")
        sample_msgs = [
            "I will pay on Friday",
            "Can pay by the 5th",
            "Will transfer tomorrow morning",
            "Payment in 3 days",
            "Sending on 15/09",
        ]

        btn_cols = st.columns(2)
        for idx, msg in enumerate(sample_msgs):
            col = btn_cols[idx % 2]
            if col.button(msg, key=f"sample_{msg}", use_container_width=True):
                st.session_state["p2p_input"] = msg
                st.rerun()

    with col_output:
        text_to_parse = user_text
        if text_to_parse:
            result = parse_promise(text_to_parse)
            if result["parsed"]:
                st.success(f"✅ Date Extracted — Confidence Score: {result['confidence']:.0%}")
                st.metric("Promised Date", result["promised_date"])
                st.json(result)

                events = get_all_events()
                pending_ids = [e["event_id"] for e in events if e["status"] == "PENDING"]
                if pending_ids:
                    st.markdown("---")
                    selected = st.selectbox("Link Contract to Event ID", pending_ids)
                    if st.button("📝 Register P2P Contract", type="primary", use_container_width=True):
                        contract = {
                            "contract_id": f"P2P-{uuid.uuid4().hex[:10].upper()}",
                            "event_id": selected,
                            "promised_date": result["promised_date"],
                            "raw_customer_text": text_to_parse,
                            "confidence": result["confidence"],
                            "status": "ACTIVE",
                        }
                        create_p2p_contract(contract)
                        st.toast(f"Contract {contract['contract_id']} created!", icon="📝")
            else:
                st.warning("⚠ Could not extract a valid promised payment date.")
                st.json(result)

# ── Tab 3: Analytics ─────────────────────────────────────────────────

with tab3:
    st.subheader("Mathematical Model Analytics")

    # Hawkes Decay Curve
    st.markdown("#### Hawkes Process Hazard Rate $h(t)$ Decay by Bank Switch")
    scheduler = HawkesScheduler()
    events = get_all_events()
    banks = sorted(set(e["bank"] for e in events))

    decay_frames = []
    for bank in banks:
        bank_events = [e for e in events if e["bank"] == bank]
        if bank_events:
            t_fail = datetime.fromisoformat(bank_events[0]["failed_at"])
            curve = scheduler.decay_curve(t_fail, hours=72, steps=80)
            for pt in curve:
                pt["bank"] = bank
            decay_frames.extend(curve)

    if decay_frames:
        df_decay = pd.DataFrame(decay_frames)
        fig_decay = px.line(
            df_decay, x="hour", y="hazard_rate", color="bank",
            labels={"hour": "Hours Elapsed Since Failure (t)", "hazard_rate": "Hazard Rate h(t)"},
            color_discrete_sequence=["#3861fb", "#ff1744", "#00e676", "#ffb300"],
        )
        fig_decay.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c8d6e5", family="Inter"),
            height=380,
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_decay, use_container_width=True)

    # Prospect Theory Scatter Plot
    st.markdown("#### Prospect Theory Framing & Discount Distribution")
    framer = ProspectFramer()
    scatter_data = []
    for e in events:
        frame = framer.frame(e["category"], e["amount"], e["customer_name"])
        scatter_data.append({
            "event_id": e["event_id"],
            "category": e["category"],
            "amount": e["amount"],
            "frame_type": frame.frame_type,
            "discount_pct": frame.discount_pct,
        })

    if scatter_data:
        df_scatter = pd.DataFrame(scatter_data)
        fig_scatter = px.scatter(
            df_scatter, x="amount", y="discount_pct",
            color="frame_type", symbol="category",
            size="amount", size_max=18,
            labels={
                "amount": "Transaction Value (₹)",
                "discount_pct": "Pre-Guardrail Discount %",
                "frame_type": "Psychological Frame",
            },
            color_discrete_map={"LOSS": "#ff1744", "GAIN": "#00e676"},
        )
        fig_scatter.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c8d6e5", family="Inter"),
            height=380,
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

# ── Tab 4: Audit Log ────────────────────────────────────────────────

with tab4:
    st.subheader("Immutable Audit Ledger")
    st.caption("Cryptographically verifiable execution log recording every recovery decision and guardrail check.")

    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        filter_event = st.text_input("Filter by Event ID", placeholder="e.g. EVT001")
    with col_f2:
        guardrail_only = st.checkbox("Show Guardrail Interventions Only")

    logs = get_audit_log(
        event_id=filter_event if filter_event else None,
        guardrail_only=guardrail_only,
    )

    if logs:
        df_logs = pd.DataFrame(logs)
        st.dataframe(
            df_logs,
            use_container_width=True,
            hide_index=True,
            column_config={
                "log_id": "Log ID",
                "event_id": "Event ID",
                "timestamp": "Timestamp",
                "action": "Action Taken",
                "reason": "Reason / Context",
                "guardrail_triggered": "Guardrail Flag"
            }
        )
        st.caption(f"Showing {len(logs)} immutable audit log entries.")
    else:
        st.info("No matching audit log entries found.")

# ── Footer ───────────────────────────────────────────────────────────

st.markdown("""
<div class="app-footer">
    <div>⚡ <b>Hawkes-Prospect Recovery Engine v1.0</b> | Razorpay Internship Track 03 Submission</div>
    <div style="margin-top:0.3rem;">Powered by <span>Hawkes Self-Exciting Point Process</span> & <span>Prospect Theory Framing</span></div>
</div>
""", unsafe_allow_html=True)