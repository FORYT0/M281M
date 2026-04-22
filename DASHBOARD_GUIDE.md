# 📊 Paper Trading Dashboard Guide

**Real-Time Monitoring of Your AI Trading System**

---

## Overview

The Paper Trading Dashboard provides real-time visualization and monitoring of your trading system's performance with:

- 📈 Live portfolio value tracking
- 💰 Real-time trade history
- 📊 Advanced analytics and metrics
- 🛡️ Risk monitoring
- 🔄 Auto-refresh every 10 seconds

---

## Starting the Dashboard

### Quick Start
```bash
start_paper_dashboard.bat
```

### Manual Start
```bash
streamlit run scripts/paper_trading_dashboard.py
```

### What Happens
1. Virtual environment activates
2. Streamlit server starts
3. Browser opens automatically to `http://localhost:8501`
4. Dashboard loads with real-time data

---

## Dashboard Layout

### Top Metrics Bar
```
┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ Portfolio   │ Total       │ Total       │ Win Rate    │ Max         │
│ Value       │ Return      │ Trades      │             │ Drawdown    │
│ $10,234.56  │ +2.35%      │ 15          │ 66.7%       │ -1.23%      │
│ +$234.56    │             │ 10W / 5L    │             │             │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
```

**Metrics:**
- **Portfolio Value:** Current total value with change from initial
- **Total Return:** Percentage gain/loss
- **Total Trades:** Number of completed trades (Wins/Losses)
- **Win Rate:** Percentage of profitable trades
- **Max Drawdown:** Largest peak-to-trough decline

---

## Tabs

### 1️⃣ Overview Tab

#### Equity Curve Chart
- **Top Panel:** Portfolio value over time
  - Green line: Current value
  - Gray dashed line: Initial capital
  - Green fill: Profit area
  
- **Bottom Panel:** Drawdown over time
  - Red line: Drawdown percentage
  - Red fill: Loss area
  - Shows risk exposure

#### Live Market Section
- **Current BTC Price:** Real-time price from Binance
- **Live Price Chart:** Last 5 minutes of price action
- **Updates:** Every second

#### Current Signal Section
- **Signal:** 🟢 BUY / 🟡 HOLD / 🔴 SELL
- **Confidence:** Model confidence percentage
- **Position:** Current open position value (if any)

---

### 2️⃣ Trades Tab

**Recent Trades Table**

Columns:
- **Timestamp:** When trade executed
- **Action:** BUY / SELL / FORCE_CLOSE
- **Price:** Execution price
- **Amount:** BTC amount
- **PnL:** Profit/Loss in dollars
- **PnL %:** Profit/Loss percentage
- **Confidence:** Model confidence at trade time

**Features:**
- Shows last 20 trades
- Sortable columns
- Color-coded PnL (green=profit, red=loss)
- Scrollable for full history

---

### 3️⃣ Analytics Tab

#### PnL Distribution Chart
- **Histogram:** Distribution of trade profits/losses
- **Yellow Line:** Mean PnL
- **Shows:** Trading consistency and outliers

#### Cumulative PnL Chart
- **Line Chart:** Running total of profits/losses
- **Trend:** Shows if system is profitable over time
- **Markers:** Individual trade points

#### Performance Metrics Grid

**Column 1:**
- **Profit Factor:** Total wins / Total losses (>1 is good)
- **Sharpe Ratio:** Risk-adjusted returns (>1 is excellent)

**Column 2:**
- **Avg Win:** Average profit per winning trade
- **Avg Loss:** Average loss per losing trade

**Column 3:**
- **Total PnL:** Sum of all profits and losses
- **Volatility:** Portfolio value volatility

**Column 4:**
- **Current DD:** Current drawdown from peak
- **Max DD:** Maximum drawdown experienced

---

### 4️⃣ Advanced Tab

#### Summary JSON
- Complete system state
- All configuration parameters
- Detailed statistics

#### Model Performance Table
```
┌──────────────────┬─────────┬───────┬──────────┐
│ Model            │ Correct │ Total │ Accuracy │
├──────────────────┼─────────┼───────┼──────────┤
│ Momentum         │ 8       │ 10    │ 80.0%    │
│ Mean Reversion   │ 6       │ 10    │ 60.0%    │
│ Order Flow       │ 9       │ 10    │ 90.0%    │
└──────────────────┴─────────┴───────┴──────────┘
```

**Shows:**
- Individual model accuracy
- Which models are performing best
- Helps identify weak models

#### Kill Switch Status
- **Status:** Armed / Triggered
- **Consecutive Losses:** Current count
- **Avg Confidence:** Recent average
- **Kill Reason:** If triggered, shows why

---

## Sidebar

### Settings
- **Auto-refresh:** Toggle automatic updates
- **Refresh Rate:** Adjust update frequency (5-60 seconds)

### System Status
- **Status:** Active / Killed
- **Uptime:** How long system has been running
- **Kill Switch:** Current state

### Quick Links
- Direct links to documentation
- Results folder access

---

## Understanding the Charts

### Equity Curve
```
Good Pattern:
  ↗️ Steady upward trend
  📈 Smooth growth
  ✅ Above initial capital line

Warning Pattern:
  ↘️ Downward trend
  📉 High volatility
  ⚠️ Below initial capital line
```

### Drawdown Chart
```
Good Pattern:
  📊 Small drawdowns (<5%)
  ⏱️ Quick recovery
  ✅ Mostly near zero

Warning Pattern:
  📊 Large drawdowns (>10%)
  ⏱️ Slow recovery
  ⚠️ Approaching kill switch limit
```

### PnL Distribution
```
Good Pattern:
  📊 More wins than losses
  📈 Mean PnL positive
  ✅ Tight distribution

Warning Pattern:
  📊 More losses than wins
  📉 Mean PnL negative
  ⚠️ Wide distribution (inconsistent)
```

---

## Key Metrics Explained

### Profit Factor
```
Formula: Total Wins / Total Losses

Interpretation:
  > 2.0: Excellent
  1.5-2.0: Good
  1.0-1.5: Acceptable
  < 1.0: Losing system
```

### Sharpe Ratio
```
Formula: Return / Volatility

Interpretation:
  > 2.0: Excellent
  1.0-2.0: Good
  0.5-1.0: Acceptable
  < 0.5: Poor risk-adjusted returns
```

### Win Rate
```
Formula: Winning Trades / Total Trades

Interpretation:
  > 60%: Excellent
  50-60%: Good
  40-50%: Acceptable (if profit factor > 1.5)
  < 40%: Needs improvement
```

### Max Drawdown
```
Formula: (Peak - Trough) / Peak

Interpretation:
  < 5%: Excellent
  5-10%: Good
  10-15%: Acceptable
  > 15%: High risk
```

---

## Real-Time Updates

### What Updates Automatically
✅ Portfolio value
✅ Trade history
✅ All charts
✅ Performance metrics
✅ Kill switch status
✅ Model performance

### Update Frequency
- **Default:** Every 10 seconds
- **Adjustable:** 5-60 seconds
- **Manual:** Disable auto-refresh

### Data Sources
- **Equity:** `paper_trading_results/equity_*.csv`
- **Trades:** `paper_trading_results/trades_*.csv`
- **Summary:** `paper_trading_results/summary_*.json`
- **Status:** `paper_trading_status.json`

---

## Usage Scenarios

### Daily Monitoring
1. Start dashboard in morning
2. Check overnight performance
3. Review any new trades
4. Monitor kill switch status
5. Leave running all day

### Performance Review
1. Go to Analytics tab
2. Check profit factor and Sharpe ratio
3. Review PnL distribution
4. Analyze cumulative PnL trend
5. Identify areas for improvement

### Troubleshooting
1. Go to Advanced tab
2. Check model performance
3. Review kill switch status
4. Examine summary JSON
5. Identify issues

---

## Tips & Best Practices

### 1. Keep Dashboard Running
- Run alongside paper trading
- Monitor in real-time
- Catch issues early

### 2. Check Multiple Times Daily
- Morning: Review overnight
- Midday: Check progress
- Evening: Daily summary

### 3. Watch Key Metrics
- **Priority 1:** Kill switch status
- **Priority 2:** Drawdown
- **Priority 3:** Win rate
- **Priority 4:** Profit factor

### 4. Use Auto-Refresh
- Enable for live monitoring
- Set to 10-30 seconds
- Disable when analyzing details

### 5. Review Analytics Weekly
- Check cumulative PnL trend
- Analyze model performance
- Identify patterns
- Plan optimizations

---

## Troubleshooting

### Dashboard Won't Start
```
Error: streamlit not found
Solution: pip install streamlit
```

### No Data Showing
```
Issue: "No trading data found"
Solution: Start paper trading first
Command: start_safe_trading.bat
```

### Charts Not Updating
```
Issue: Auto-refresh disabled
Solution: Enable in sidebar
```

### Browser Doesn't Open
```
Issue: Manual navigation needed
Solution: Open http://localhost:8501
```

### Port Already in Use
```
Error: Port 8501 is already in use
Solution: Stop other Streamlit instances
Or: streamlit run --server.port 8502 scripts/paper_trading_dashboard.py
```

---

## Advanced Features

### Custom Refresh Rate
```python
# In sidebar
refresh_rate = st.slider("Refresh rate (seconds)", 5, 60, 10)
```

### Export Data
- All charts have download buttons
- Export as PNG or SVG
- Save for reports

### Full Screen Mode
- Click expand icon on charts
- Better for presentations
- Detailed analysis

---

## Performance Optimization

### For Smooth Operation
- Close unused browser tabs
- Use modern browser (Chrome/Firefox)
- Adequate RAM (4GB+ recommended)
- SSD for faster file access

### If Dashboard is Slow
- Increase refresh rate (30-60 seconds)
- Close other applications
- Reduce chart complexity
- Clear browser cache

---

## Integration with Trading System

### Data Flow
```
Paper Trading System
    ↓
Writes CSV files every minute
    ↓
Dashboard reads files
    ↓
Updates visualizations
    ↓
You see real-time results
```

### Status Updates
```
Trading System
    ↓
Writes status.json every minute
    ↓
Dashboard reads status
    ↓
Shows in sidebar
```

---

## Keyboard Shortcuts

- **R:** Refresh dashboard manually
- **Ctrl+C:** Stop dashboard (in terminal)
- **F11:** Full screen browser
- **Ctrl+Shift+R:** Hard refresh

---

## Summary

The dashboard provides:
- ✅ Real-time monitoring
- ✅ Comprehensive analytics
- ✅ Risk tracking
- ✅ Model performance
- ✅ Beautiful visualizations
- ✅ Auto-refresh
- ✅ Easy to use

**Start monitoring your trading system now:**
```bash
start_paper_dashboard.bat
```

---

**Happy monitoring! 📊📈**