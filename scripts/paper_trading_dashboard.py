"""
M281M Paper Trading Dashboard — IMPROVED UI v2
Professional dark-themed live trading monitor.
Run: streamlit run scripts/paper_trading_dashboard.py
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import glob, time, json
from datetime import datetime

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="M281M · Trading",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    background-color: #0d1117;
    color: #e6edf3;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 2rem; max-width: 1800px; }

/* ── Banner ── */
.top-banner {
    background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
    border: 1px solid #30363d; border-radius: 12px;
    padding: 1.1rem 2rem; display: flex; align-items: center;
    justify-content: space-between; margin-bottom: 1.5rem;
}
.top-banner h1 { margin:0; font-size:1.5rem; font-weight:700;
    background: linear-gradient(90deg,#58a6ff,#3fb950);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.top-banner .meta { display:flex; gap:1.5rem; align-items:center; }

/* ── KPI grid ── */
.kpi-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:.85rem; margin-bottom:1.4rem; }
.kpi {
    background:#161b22; border:1px solid #30363d; border-radius:10px;
    padding:1rem 1.1rem; position:relative; overflow:hidden;
}
.kpi::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; border-radius:10px 10px 0 0; }
.kpi.blue::before   { background:#58a6ff; }
.kpi.green::before  { background:#3fb950; }
.kpi.red::before    { background:#f85149; }
.kpi.amber::before  { background:#d29922; }
.kpi.purple::before { background:#bc8cff; }
.kpi.teal::before   { background:#39d353; }
.kpi .label { font-size:.68rem; text-transform:uppercase; letter-spacing:.08em; color:#8b949e; margin-bottom:.35rem; }
.kpi .value { font-size:1.55rem; font-weight:700; color:#e6edf3; line-height:1; }
.kpi .delta { font-size:.75rem; margin-top:.3rem; }
.delta.pos { color:#3fb950; } .delta.neg { color:#f85149; } .delta.neu { color:#8b949e; }

/* ── Signal box ── */
.signal-box {
    border-radius:10px; padding:1.2rem 1.5rem; text-align:center;
    border:2px solid; margin-bottom:.5rem;
}
.signal-box.long  { background:#0d2e18; border-color:#3fb950; }
.signal-box.short { background:#2e0d0d; border-color:#f85149; }
.signal-box.hold  { background:#1c1f26; border-color:#30363d; }
.signal-box .dir  { font-size:2rem; font-weight:800; letter-spacing:.05em; }
.signal-box .conf { font-size:.85rem; color:#8b949e; margin-top:.3rem; }
.signal-box.long  .dir { color:#3fb950; }
.signal-box.short .dir { color:#f85149; }
.signal-box.hold  .dir { color:#8b949e; }

/* ── Badge ── */
.badge { display:inline-flex; align-items:center; gap:.4rem;
    padding:.22rem .7rem; border-radius:20px; font-size:.75rem; font-weight:600; }
.badge.ok   { background:#1a3a2a; color:#3fb950; border:1px solid #3fb950; }
.badge.warn { background:#3a2e10; color:#d29922; border:1px solid #d29922; }
.badge.err  { background:#3a1a1a; color:#f85149; border:1px solid #f85149; }
.badge.kill { background:#4a0a0a; color:#ff6b6b; border:1px solid #f85149; animation:pulse 1s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.6} }

/* ── Section headers ── */
.sec-header { font-size:.85rem; font-weight:600; color:#8b949e; text-transform:uppercase;
    letter-spacing:.08em; margin:1.3rem 0 .7rem; border-bottom:1px solid #21262d; padding-bottom:.35rem; }

/* ── Table ── */
.trade-table { width:100%; border-collapse:collapse; font-size:.82rem; }
.trade-table th { background:#161b22; color:#8b949e; padding:.55rem .8rem;
    text-align:left; border-bottom:1px solid #30363d; font-weight:500; font-size:.72rem;
    text-transform:uppercase; letter-spacing:.05em; }
.trade-table td { padding:.55rem .8rem; border-bottom:1px solid #21262d; color:#e6edf3; }
.trade-table tr:hover td { background:#161b22; }
.win  { color:#3fb950; font-weight:600; }
.loss { color:#f85149; font-weight:600; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background:#161b22 !important; border-right:1px solid #30363d; }

/* ── Plotly charts ── */
.js-plotly-plot { border:1px solid #30363d; border-radius:10px; }

/* ── Kill switch alert ── */
.ks-alert {
    background:#2e0d0d; border:1px solid #f85149; border-left:4px solid #f85149;
    border-radius:8px; padding:1rem 1.2rem; margin:1rem 0; color:#ffa198;
    font-size:.88rem; font-weight:600;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
RESULTS_DIR = Path("paper_trading_results")
STATUS_FILE  = Path("paper_trading_status.json")

CHART_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(22,27,34,1)",
    font=dict(family="Inter, sans-serif", color="#8b949e", size=11),
    margin=dict(l=50, r=20, t=40, b=40),
    xaxis=dict(gridcolor="#21262d", zeroline=False),
    yaxis=dict(gridcolor="#21262d", zeroline=False),
    hovermode="x unified",
)

# ── Data loading ───────────────────────────────────────────────────────────────
def _latest(pattern):
    files = glob.glob(str(RESULTS_DIR / pattern))
    return max(files, key=os.path.getctime) if files else None

@st.cache_data(ttl=10)
def load_status():
    if STATUS_FILE.exists():
        try:
            with open(STATUS_FILE) as f: return json.load(f)
        except: pass
    return {}

@st.cache_data(ttl=10)
def load_equity():
    fp = _latest("equity_*.csv")
    if fp:
        df = pd.read_csv(fp)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    return pd.DataFrame()

@st.cache_data(ttl=10)
def load_trades():
    fp = _latest("trades_*.csv")
    if fp:
        df = pd.read_csv(fp)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    return pd.DataFrame()

@st.cache_data(ttl=10)
def load_summary():
    fp = _latest("summary_*.json")
    if fp:
        with open(fp) as f: return json.load(f)
    return {}

# ── Metrics ────────────────────────────────────────────────────────────────────
def calc_metrics(eq, tr):
    m = {"equity":0,"initial":0,"ret_pct":0,"dd":0,"cur_dd":0,"volatility":0,
         "trades":0,"wins":0,"losses":0,"wr":0,"pnl":0,"avg_win":0,"avg_loss":0,
         "pf":0,"sharpe":0,"pos_value":0}
    if not eq.empty:
        m["equity"]   = eq["total_value"].iloc[-1]
        m["initial"]  = eq["total_value"].iloc[0]
        m["ret_pct"]  = (m["equity"] - m["initial"]) / m["initial"] * 100
        m["pos_value"] = eq.get("position_value", pd.Series([0])).iloc[-1]
        eq2 = eq.copy()
        eq2["peak"] = eq2["total_value"].cummax()
        eq2["dd"]   = (eq2["total_value"] - eq2["peak"]) / eq2["peak"] * 100
        m["dd"]     = eq2["dd"].min()
        m["cur_dd"] = eq2["dd"].iloc[-1]
        ret = eq2["total_value"].pct_change().dropna()
        m["volatility"] = float(ret.std() * np.sqrt(len(eq2))) if len(ret) > 1 else 0

    if not tr.empty and "pnl" in tr.columns:
        done = tr[tr["pnl"].notna()]
        if not done.empty:
            m["trades"]   = len(done)
            m["wins"]     = int((done["pnl"] > 0).sum())
            m["losses"]   = int((done["pnl"] < 0).sum())
            m["wr"]       = m["wins"] / m["trades"] * 100 if m["trades"] else 0
            m["pnl"]      = float(done["pnl"].sum())
            m["avg_win"]  = float(done[done["pnl"]>0]["pnl"].mean()) if m["wins"]  else 0
            m["avg_loss"] = float(done[done["pnl"]<0]["pnl"].mean()) if m["losses"] else 0
            tw = done[done["pnl"]>0]["pnl"].sum()
            tl = abs(done[done["pnl"]<0]["pnl"].sum())
            m["pf"]     = tw/tl if tl else 0
            m["sharpe"] = m["ret_pct"] / m["volatility"] if m["volatility"] else 0
    return m

# ── Chart builders ─────────────────────────────────────────────────────────────
def chart_equity(eq):
    if eq.empty: return None
    eq = eq.copy()
    eq["peak"] = eq["total_value"].cummax()
    eq["dd"]   = (eq["total_value"] - eq["peak"]) / eq["peak"] * 100

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.7, 0.3], vertical_spacing=0.04,
        subplot_titles=["Portfolio Equity", "Drawdown %"])

    fig.add_trace(go.Scatter(x=eq["timestamp"], y=eq["total_value"],
        mode="lines", name="Equity", line=dict(color="#58a6ff", width=2),
        fill="tozeroy", fillcolor="rgba(88,166,255,0.07)"), row=1, col=1)

    fig.add_hline(y=eq["total_value"].iloc[0], line_dash="dot",
        line_color="#30363d", annotation_text="Start", row=1, col=1)

    fig.add_trace(go.Scatter(x=eq["timestamp"], y=eq["dd"],
        mode="lines", name="Drawdown", line=dict(color="#f85149", width=1.5),
        fill="tozeroy", fillcolor="rgba(248,81,73,0.1)"), row=2, col=1)

    fig.update_layout(**CHART_LAYOUT, height=420, showlegend=False)
    fig.update_yaxes(title_text="USD ($)", row=1, col=1)
    fig.update_yaxes(title_text="DD (%)", row=2, col=1)
    return fig

def chart_pnl_dist(tr):
    if tr.empty or "pnl" not in tr.columns: return None
    done = tr[tr["pnl"].notna()]
    if done.empty: return None
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=done["pnl"], nbinsx=30,
        marker_color=np.where(done["pnl"] >= 0, "#3fb950", "#f85149"),
        marker_line_color="#0d1117", marker_line_width=1, name="PnL"))
    mean = done["pnl"].mean()
    fig.add_vline(x=mean, line_dash="dash", line_color="#d29922",
        annotation_text=f"Mean: ${mean:.2f}", annotation_font_color="#d29922")
    fig.update_layout(**CHART_LAYOUT, title="Trade PnL Distribution", height=300)
    return fig

def chart_cumulative_pnl(tr):
    if tr.empty or "pnl" not in tr.columns: return None
    done = tr[tr["pnl"].notna()].copy()
    if done.empty: return None
    done["cum_pnl"] = done["pnl"].cumsum()
    colors = np.where(done["cum_pnl"] >= 0, "#3fb950", "#f85149")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=done["timestamp"], y=done["cum_pnl"],
        mode="lines+markers", name="Cumulative PnL",
        line=dict(color="#3fb950", width=2),
        marker=dict(size=5, color=colors.tolist())))
    fig.add_hline(y=0, line_dash="dot", line_color="#30363d")
    fig.update_layout(**CHART_LAYOUT, title="Cumulative PnL", height=300)
    return fig

def chart_win_loss(m):
    fig = go.Figure(go.Pie(
        labels=["Wins", "Losses"],
        values=[max(m["wins"],0), max(m["losses"],0)],
        marker=dict(colors=["#3fb950","#f85149"],
            line=dict(color="#0d1117", width=2)),
        textinfo="label+percent", hole=0.5,
        textfont=dict(color="#e6edf3")))
    fig.update_layout(**CHART_LAYOUT, title="Win / Loss Ratio",
        height=280, showlegend=False, margin=dict(l=20,r=20,t=40,b=20))
    return fig

def chart_agent_weights(status):
    aw = status.get("agent_weights") or status.get("model_performance", {})
    if not aw: return None
    names, vals, cols = [], [], []
    for k, v in aw.items():
        names.append(k.replace("_agent","").replace("_"," ").title())
        score = v if isinstance(v, (int,float)) else (v.get("correct",0)/(v.get("total",1) or 1)*100)
        vals.append(score)
        cols.append("#58a6ff" if score > 60 else "#d29922")
    fig = go.Figure(go.Bar(x=names, y=vals, marker_color=cols,
        marker_line_width=0, text=[f"{v:.1f}" for v in vals],
        textposition="outside", textfont=dict(color="#e6edf3")))
    fig.update_layout(**CHART_LAYOUT, title="Agent Performance / Weights",
        height=280, yaxis=dict(gridcolor="#21262d", range=[0, max(vals)*1.2+5]))
    return fig

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 M281M Trading")
    st.markdown("---")
    auto_refresh = st.toggle("Auto-refresh (10s)", value=True)
    refresh_rate = st.slider("Interval (s)", 5, 60, 10)
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.markdown("---")

    status = load_status()
    if status:
        ks = status.get("kill_switch", {})
        if ks.get("is_killed"):
            st.markdown(f'<div class="badge kill">🚨 KILL SWITCH</div>', unsafe_allow_html=True)
            st.caption(ks.get("kill_reason",""))
        else:
            st.markdown('<span class="badge ok">● Active</span>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**Live Signal**")
        sig = status.get("signal","HOLD")
        conf = status.get("confidence", 0)
        sig_cls = "long" if sig=="BUY" else ("short" if sig=="SELL" else "hold")
        st.markdown(f"""<div class="signal-box {sig_cls}">
            <div class="dir">{sig}</div>
            <div class="conf">Confidence: {conf:.1%}</div>
        </div>""", unsafe_allow_html=True)

        if "price" in status:
            st.metric("BTC/USDT", f"${status['price']:,.2f}")
        st.markdown("---")
        if "kill_switch" in status:
            st.metric("Consec. Losses", ks.get("consecutive_losses", 0))
    else:
        st.info("Start trading to see live data")

# ── Load data ──────────────────────────────────────────────────────────────────
eq_df  = load_equity()
tr_df  = load_trades()
summary = load_summary()
m = calc_metrics(eq_df, tr_df)
now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ── Banner ─────────────────────────────────────────────────────────────────────
running = bool(status.get("status") == "ACTIVE")
badge_cls = "ok" if running else "warn"
badge_txt = "● LIVE" if running else "● Offline"

ret_color = "#3fb950" if m["ret_pct"] >= 0 else "#f85149"
ret_sign  = "+" if m["ret_pct"] >= 0 else ""

st.markdown(f"""
<div class="top-banner">
  <h1>📈 M281M Paper Trading Dashboard</h1>
  <div class="meta">
    <span style="font-size:.85rem;color:{ret_color};font-weight:700;">
      {ret_sign}{m['ret_pct']:.2f}% return
    </span>
    <span class="badge {badge_cls}">{badge_txt}</span>
    <span style="color:#8b949e;font-size:.78rem;">{now_str}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Kill switch alert ──────────────────────────────────────────────────────────
ks = status.get("kill_switch", {})
if ks.get("is_killed"):
    st.markdown(f'<div class="ks-alert">🚨 KILL SWITCH TRIGGERED — {ks.get("kill_reason","Unknown reason")} — Trading halted. Review logs before restarting.</div>', unsafe_allow_html=True)

# ── KPI row ────────────────────────────────────────────────────────────────────
pnl_cls   = "green" if m["pnl"] >= 0 else "red"
ret_cls   = "green" if m["ret_pct"] >= 0 else "red"
dd_delta  = f"{m['cur_dd']:.2f}% current"

st.markdown(f"""
<div class="kpi-grid">
  <div class="kpi blue">
    <div class="label">Equity</div>
    <div class="value">${m['equity']:,.0f}</div>
    <div class="delta neu">Start: ${m['initial']:,.0f}</div>
  </div>
  <div class="kpi {ret_cls}">
    <div class="label">Total Return</div>
    <div class="value">{'+' if m['ret_pct']>=0 else ''}{m['ret_pct']:.2f}%</div>
    <div class="delta neu">${m['equity']-m['initial']:+,.2f}</div>
  </div>
  <div class="kpi {pnl_cls}">
    <div class="label">Realised PnL</div>
    <div class="value">${m['pnl']:+,.2f}</div>
    <div class="delta neu">Avg win ${m['avg_win']:.2f}</div>
  </div>
  <div class="kpi amber">
    <div class="label">Trades</div>
    <div class="value">{m['trades']}</div>
    <div class="delta neu">{m['wins']}W · {m['losses']}L</div>
  </div>
  <div class="kpi {'green' if m['wr']>=50 else 'red'}">
    <div class="label">Win Rate</div>
    <div class="value">{m['wr']:.1f}%</div>
    <div class="delta neu">PF {m['pf']:.2f}</div>
  </div>
  <div class="kpi red">
    <div class="label">Max Drawdown</div>
    <div class="value">{m['dd']:.2f}%</div>
    <div class="delta neu">{dd_delta}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📈 Equity & Risk", "💰 Trades", "📊 Analytics", "🤖 Agents"])

with tab1:
    f = chart_equity(eq_df)
    if f: st.plotly_chart(f, use_container_width=True)
    else: st.info("Equity chart will appear once trading starts.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="sec-header">Risk Summary</div>', unsafe_allow_html=True)
        st.metric("Sharpe Ratio",    f"{m['sharpe']:.2f}")
        st.metric("Volatility",      f"{m['volatility']:.2f}%")
        st.metric("Current Drawdown",f"{m['cur_dd']:.2f}%")
    with c2:
        st.markdown('<div class="sec-header">Position</div>', unsafe_allow_html=True)
        if m["pos_value"] > 0:
            st.metric("Open Position", f"${m['pos_value']:,.2f}")
        else:
            st.success("No open position (cash)")
        st.metric("Free Capital", f"${m['equity'] - m['pos_value']:,.2f}")

with tab2:
    st.markdown('<div class="sec-header">Recent Trades</div>', unsafe_allow_html=True)
    if not tr_df.empty:
        show = tr_df.tail(30).copy()
        pnl_col = "pnl" if "pnl" in show.columns else None

        rows_html = ""
        for _, row in show.iterrows():
            pnl_val  = row.get("pnl", None)
            pnl_str  = f'<span class="{"win" if pnl_val and pnl_val>0 else "loss"}">${pnl_val:+.2f}</span>' if pd.notna(pnl_val) else "—"
            action   = str(row.get("action", row.get("side","—")))
            price    = f"${row['price']:,.2f}" if "price" in row and pd.notna(row["price"]) else "—"
            amount   = f"{row['amount']:.5f}" if "amount" in row and pd.notna(row.get("amount")) else (f"{row.get('size',''):.5f}" if "size" in row else "—")
            ts_str   = str(row["timestamp"])[:19]
            reason   = str(row.get("reason", row.get("close_reason","—")))
            conf     = f"{row['confidence']:.2f}" if "confidence" in row and pd.notna(row.get("confidence")) else "—"
            rows_html += f"<tr><td>{ts_str}</td><td><b>{action.upper()}</b></td><td>{price}</td><td>{amount}</td><td>{pnl_str}</td><td>{conf}</td><td>{reason}</td></tr>"

        st.markdown(f"""
        <table class="trade-table">
          <thead><tr>
            <th>Timestamp</th><th>Action</th><th>Price</th><th>Amount</th>
            <th>PnL</th><th>Confidence</th><th>Reason</th>
          </tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""", unsafe_allow_html=True)
    else:
        st.info("No trades recorded yet. System is running — waiting for signals.")

with tab3:
    c1, c2 = st.columns(2)
    with c1:
        f = chart_pnl_dist(tr_df)
        st.plotly_chart(f, use_container_width=True) if f else st.info("PnL distribution — awaiting trades")
        f = chart_win_loss(m)
        st.plotly_chart(f, use_container_width=True) if f else None
    with c2:
        f = chart_cumulative_pnl(tr_df)
        st.plotly_chart(f, use_container_width=True) if f else st.info("Cumulative PnL — awaiting trades")

        st.markdown('<div class="sec-header">Performance Table</div>', unsafe_allow_html=True)
        perf_data = {
            "Metric": ["Total Return","Total PnL","Win Rate","Profit Factor","Sharpe Ratio","Avg Win","Avg Loss","Max Drawdown"],
            "Value":  [f"{m['ret_pct']:+.2f}%", f"${m['pnl']:+.2f}", f"{m['wr']:.1f}%",
                       f"{m['pf']:.2f}", f"{m['sharpe']:.2f}",
                       f"${m['avg_win']:.2f}", f"${m['avg_loss']:.2f}", f"{m['dd']:.2f}%"]
        }
        st.dataframe(pd.DataFrame(perf_data), use_container_width=True, hide_index=True)

with tab4:
    st.markdown('<div class="sec-header">Agent Weights & Performance</div>', unsafe_allow_html=True)
    f = chart_agent_weights(status if status else summary)
    st.plotly_chart(f, use_container_width=True) if f else st.info("Agent weight chart — awaiting live session data")

    st.markdown('<div class="sec-header">Kill Switch Status</div>', unsafe_allow_html=True)
    ks = status.get("kill_switch", summary.get("kill_switch", {}))
    if ks:
        c1, c2, c3 = st.columns(3)
        is_killed = ks.get("is_killed", False)
        c1.metric("Status", "🚨 TRIGGERED" if is_killed else "✅ Armed")
        c2.metric("Consecutive Losses", ks.get("consecutive_losses", 0))
        c3.metric("Kill Reason", ks.get("kill_reason") or "None")
    else:
        st.info("Kill switch status will appear once trading session starts.")

    if summary:
        with st.expander("📋 Full Session Summary JSON"):
            st.json(summary)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(f"<div style='text-align:center;color:#30363d;font-size:.75rem;margin-top:2rem;'>M281M Trading Dashboard · {now_str} · Auto-refresh: {'ON' if auto_refresh else 'OFF'}</div>", unsafe_allow_html=True)

if auto_refresh:
    time.sleep(refresh_rate)
    st.cache_data.clear()
    st.rerun()
