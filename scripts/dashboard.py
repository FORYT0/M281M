"""
M281M Data Collection Monitor — IMPROVED UI v2
Modern dark-themed dashboard with real-time stats and charts.
Run: streamlit run scripts/dashboard.py
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime
import time, json

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="M281M · Data Monitor",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    background-color: #0d1117;
    color: #e6edf3;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 2rem; max-width: 1600px; }

/* ── Top banner ── */
.top-banner {
    background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 1.2rem 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.5rem;
}
.top-banner h1 { margin: 0; font-size: 1.6rem; font-weight: 700;
    background: linear-gradient(90deg, #58a6ff, #3fb950);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.top-banner .ts { color: #8b949e; font-size: 0.8rem; }

/* ── KPI cards ── */
.kpi-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 1rem; margin-bottom: 1.5rem; }
.kpi {
    background: #161b22; border: 1px solid #30363d; border-radius: 10px;
    padding: 1.1rem 1.3rem; position: relative; overflow: hidden;
}
.kpi::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 3px; border-radius: 10px 10px 0 0;
}
.kpi.blue::before  { background: #58a6ff; }
.kpi.green::before { background: #3fb950; }
.kpi.amber::before { background: #d29922; }
.kpi.red::before   { background: #f85149; }
.kpi .label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: .08em; color: #8b949e; margin-bottom: .4rem; }
.kpi .value { font-size: 1.8rem; font-weight: 700; color: #e6edf3; line-height: 1; }
.kpi .sub   { font-size: 0.78rem; color: #8b949e; margin-top: .3rem; }

/* ── Status badge ── */
.badge {
    display: inline-flex; align-items: center; gap: .4rem;
    padding: .25rem .75rem; border-radius: 20px; font-size: .78rem; font-weight: 600;
}
.badge.ok   { background: #1a3a2a; color: #3fb950; border: 1px solid #3fb950; }
.badge.warn { background: #3a2e10; color: #d29922; border: 1px solid #d29922; }
.badge.err  { background: #3a1a1a; color: #f85149; border: 1px solid #f85149; }

/* ── Progress bar container ── */
.prog-wrap { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 1.2rem 1.5rem; margin-bottom: 1.5rem; }
.prog-label { display: flex; justify-content: space-between; margin-bottom: .6rem; font-size: .82rem; color: #8b949e; }
.prog-bar-bg { background: #21262d; border-radius: 4px; height: 8px; }
.prog-bar-fill { height: 8px; border-radius: 4px; background: linear-gradient(90deg, #58a6ff, #3fb950); transition: width .5s; }

/* ── Section headers ── */
.sec-header { font-size: 1rem; font-weight: 600; color: #8b949e;
    text-transform: uppercase; letter-spacing: .08em; margin: 1.5rem 0 .8rem; border-bottom: 1px solid #21262d; padding-bottom: .4rem; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: #161b22 !important; border-right: 1px solid #30363d; }
[data-testid="stSidebar"] .stButton > button { width: 100%; }

/* ── Plotly chart borders ── */
.js-plotly-plot { border: 1px solid #30363d; border-radius: 10px; }

/* ── Alert boxes ── */
.alert { padding: .85rem 1.2rem; border-radius: 8px; margin-bottom: 1rem; font-size: .88rem; }
.alert.info   { background: #0d2a4a; border-left: 3px solid #58a6ff; color: #a0c4ff; }
.alert.success{ background: #0d2e18; border-left: 3px solid #3fb950; color: #7ee787; }
.alert.warn   { background: #2e2008; border-left: 3px solid #d29922; color: #e3b341; }
.alert.error  { background: #2e0d0d; border-left: 3px solid #f85149; color: #ffa198; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────────────────────────
DATA_DIR = Path("data/live")
TARGET_HOURS = 336  # 2 weeks

def get_files():
    if not DATA_DIR.exists():
        return [], [], []
    return (sorted(DATA_DIR.glob("*_orderbook_*.csv")),
            sorted(DATA_DIR.glob("*_trades_*.csv")),
            sorted(DATA_DIR.glob("*_ticker_*.csv")))

def analyze_file(fp):
    try:
        df = pd.read_csv(fp)
        if df.empty: return None
        df["dt"] = pd.to_datetime(df.get("datetime", df.get("timestamp")), format="mixed", errors="coerce")
        df = df.dropna(subset=["dt"])
        if df.empty: return None
        gaps = int((df["dt"].diff().dt.total_seconds() > 5).sum())
        return {"rows": len(df), "start": df["dt"].iloc[0], "end": df["dt"].iloc[-1],
                "hours": (df["dt"].iloc[-1] - df["dt"].iloc[0]).total_seconds()/3600,
                "mb": fp.stat().st_size/1024/1024, "gaps": gaps}
    except:
        return None

@st.cache_data(ttl=30)
def get_stats():
    ob, tr, ti = get_files()
    s = {"ob": len(ob), "tr": len(tr), "ti": len(ti), "rows": 0,
         "mb": 0.0, "hours": 0.0, "gaps": 0, "oldest": None, "newest": None}
    for f in ob + tr + ti:
        r = analyze_file(f)
        if not r: continue
        s["rows"] += r["rows"]; s["mb"] += r["mb"]
        s["hours"] = max(s["hours"], r["hours"]); s["gaps"] += r["gaps"]
        s["oldest"] = r["start"] if s["oldest"] is None else min(s["oldest"], r["start"])
        s["newest"] = r["end"]   if s["newest"] is None else max(s["newest"], r["end"])
    return s

@st.cache_data(ttl=30)
def get_spread_df():
    _, _, ob_files = [], [], []
    ob_files, _, _ = get_files()
    if not ob_files: return pd.DataFrame()
    df = pd.read_csv(ob_files[-1])
    if df.empty: return pd.DataFrame()
    df["dt"] = pd.to_datetime(df.get("datetime", df.get("timestamp")), format="mixed", errors="coerce")
    return df.dropna(subset=["dt"]).iloc[::50]

@st.cache_data(ttl=30)
def get_trade_df():
    _, tr, _ = get_files()
    if not tr: return pd.DataFrame()
    df = pd.read_csv(tr[-1])
    df["dt"] = pd.to_datetime(df.get("datetime", df.get("timestamp")), format="mixed", errors="coerce")
    return df.dropna(subset=["dt"])

CHART_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(22,27,34,1)",
    font=dict(family="Inter, sans-serif", color="#8b949e", size=11),
    margin=dict(l=50, r=20, t=40, b=40),
    xaxis=dict(gridcolor="#21262d", zeroline=False),
    yaxis=dict(gridcolor="#21262d", zeroline=False),
)

def make_spread_chart(df):
    if "spread_bps" not in df.columns: return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["dt"], y=df["spread_bps"],
        mode="lines", name="Spread (bps)", line=dict(color="#58a6ff", width=1.5),
        fill="tozeroy", fillcolor="rgba(88,166,255,0.08)"))
    fig.update_layout(**CHART_LAYOUT, title="Bid-Ask Spread (bps)", height=280)
    return fig

def make_imbalance_chart(df):
    if "imbalance" not in df.columns: return None
    fig = go.Figure()
    colors = ["#f85149" if v < 0 else "#3fb950" for v in df["imbalance"]]
    fig.add_trace(go.Bar(x=df["dt"], y=df["imbalance"], name="Imbalance",
        marker_color=colors, marker_line_width=0))
    fig.update_layout(**CHART_LAYOUT, title="Order Book Imbalance", height=280)
    return fig

def make_trade_pie(df):
    if "side" not in df.columns: return None
    vc = df["side"].value_counts()
    fig = go.Figure(go.Pie(labels=vc.index, values=vc.values,
        marker=dict(colors=["#3fb950","#f85149"], line=dict(color="#0d1117", width=2)),
        textinfo="label+percent", hole=0.45))
    fig.update_layout(**CHART_LAYOUT, title="Buy vs Sell Distribution", height=280,
        showlegend=False, margin=dict(l=20,r=20,t=40,b=20))
    return fig

def make_volume_chart(df):
    if "quantity" not in df.columns: return None
    df2 = df.set_index("dt").resample("5min")["quantity"].sum().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df2["dt"], y=df2["quantity"], name="Volume",
        marker_color="#3fb950", marker_line_width=0))
    fig.update_layout(**CHART_LAYOUT, title="5-Min Volume Profile", height=280)
    return fig

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛰️ M281M Monitor")
    st.markdown("---")
    auto_refresh = st.toggle("Auto-refresh (30s)", value=True)
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    st.markdown("**Target:** 2 weeks (336h)")
    st.markdown("**Symbol:** BTC/USDT · Binance")
    st.markdown("---")
    st.markdown("**Quick Actions**")
    st.markdown("▶ `start_data_collection.bat`")
    st.markdown("▶ `check_data_quality.bat`")
    st.markdown("▶ `retrain_v2.py`")

# ── Banner ─────────────────────────────────────────────────────────────────────
stats = get_stats()
now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

pct = min(stats["hours"] / TARGET_HOURS, 1.0)
if stats["hours"] == 0:
    badge_cls, badge_txt = "err",  "● No Data"
elif stats["hours"] < 24:
    badge_cls, badge_txt = "warn", "● Starting"
elif pct >= 1.0:
    badge_cls, badge_txt = "ok",   "● Ready"
else:
    badge_cls, badge_txt = "ok",   "● Collecting"

st.markdown(f"""
<div class="top-banner">
  <h1>🛰️ M281M — Data Collection Monitor</h1>
  <div style="display:flex;align-items:center;gap:1rem;">
    <span class="badge {badge_cls}">{badge_txt}</span>
    <span class="ts">Updated: {now_str}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPI row ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="kpi-grid">
  <div class="kpi blue">
    <div class="label">Total Events</div>
    <div class="value">{stats["rows"]:,}</div>
    <div class="sub">{stats["ob"]+stats["tr"]+stats["ti"]} files</div>
  </div>
  <div class="kpi green">
    <div class="label">Duration</div>
    <div class="value">{stats["hours"]:.1f}h</div>
    <div class="sub">{stats["hours"]/24:.1f} days collected</div>
  </div>
  <div class="kpi amber">
    <div class="label">Data Size</div>
    <div class="value">{stats["mb"]:.1f}<span style="font-size:1rem;"> MB</span></div>
    <div class="sub">{stats["mb"]/1024:.2f} GB</div>
  </div>
  <div class="kpi {'red' if stats['gaps'] > 10 else 'green'}">
    <div class="label">Data Gaps</div>
    <div class="value">{stats["gaps"]}</div>
    <div class="sub">{'⚠ Check quality' if stats["gaps"] > 10 else '✓ Good quality'}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Progress ───────────────────────────────────────────────────────────────────
bar_pct = round(pct * 100, 1)
st.markdown(f"""
<div class="prog-wrap">
  <div class="prog-label">
    <span>📊 Collection Progress to 2-Week Target</span>
    <span><b>{stats["hours"]:.1f}h</b> / {TARGET_HOURS}h &nbsp;·&nbsp; <b>{bar_pct}%</b></span>
  </div>
  <div class="prog-bar-bg">
    <div class="prog-bar-fill" style="width:{bar_pct}%"></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Timeline ───────────────────────────────────────────────────────────────────
if stats["oldest"] and stats["newest"]:
    c1, c2 = st.columns(2)
    c1.markdown(f"""<div class="alert info">📅 <b>Data Start:</b> {stats["oldest"].strftime("%Y-%m-%d %H:%M:%S")}</div>""", unsafe_allow_html=True)
    c2.markdown(f"""<div class="alert success">🕒 <b>Latest Tick:</b> {stats["newest"].strftime("%Y-%m-%d %H:%M:%S")}</div>""", unsafe_allow_html=True)

# ── Charts ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-header">📊 Live Market Data</div>', unsafe_allow_html=True)

ob_df = get_spread_df()
tr_df = get_trade_df()

c1, c2 = st.columns(2)
with c1:
    f = make_spread_chart(ob_df)
    st.plotly_chart(f, use_container_width=True) if f else st.info("Spread chart — no data yet")
with c2:
    f = make_imbalance_chart(ob_df)
    st.plotly_chart(f, use_container_width=True) if f else st.info("Imbalance chart — no data yet")

c1, c2 = st.columns(2)
with c1:
    f = make_trade_pie(tr_df)
    st.plotly_chart(f, use_container_width=True) if f else st.info("Trade distribution — no data yet")
with c2:
    f = make_volume_chart(tr_df)
    st.plotly_chart(f, use_container_width=True) if f else st.info("Volume profile — no data yet")

# ── Recommendations ────────────────────────────────────────────────────────────
st.markdown('<div class="sec-header">💡 Recommendations</div>', unsafe_allow_html=True)

if pct < 0.25:
    st.markdown('<div class="alert warn">Keep collecting. Target 2 weeks for robust model training.</div>', unsafe_allow_html=True)
elif pct < 0.75:
    days_left = (TARGET_HOURS - stats["hours"]) / 24
    st.markdown(f'<div class="alert info">Good progress! Continue for <b>{days_left:.1f}</b> more days.</div>', unsafe_allow_html=True)
elif pct < 1.0:
    st.markdown('<div class="alert info">Almost there! Let it run to the 2-week mark for best results.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="alert success">✅ Sufficient data collected! Run <code>python scripts/retrain_v2.py</code> to train LightGBM models, then launch <code>start_safe_trading_v2.bat</code>.</div>', unsafe_allow_html=True)

# ── File breakdown ─────────────────────────────────────────────────────────────
with st.expander("📁 File breakdown"):
    st.markdown(f"- **Order Book files:** {stats['ob']}")
    st.markdown(f"- **Trade files:** {stats['tr']}")
    st.markdown(f"- **Ticker files:** {stats['ti']}")
    st.markdown(f"- **Total size:** {stats['mb']:.2f} MB")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(f"<div style='text-align:center;color:#30363d;font-size:.75rem;margin-top:2rem;'>M281M Data Monitor · {now_str}</div>", unsafe_allow_html=True)

if auto_refresh:
    time.sleep(30)
    st.cache_data.clear()
    st.rerun()
