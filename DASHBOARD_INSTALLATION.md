# Dashboard Installation Guide

## Status

The dashboard installation was started but needs more time to complete. The installation is downloading pandas (11.1 MB) and other dependencies.

---

## Complete Installation

### Option 1: Wait and Retry

The installation may have completed in the background. Try running:

```bash
venv\Scripts\activate.bat
streamlit run scripts/dashboard.py
```

If you see "command not found", proceed to Option 2.

---

### Option 2: Manual Installation

Run this command and wait 5-10 minutes:

```bash
venv\Scripts\activate.bat
pip install streamlit plotly
```

**Expected output:**
```
Collecting streamlit
Collecting plotly
...
Successfully installed streamlit-1.54.0 plotly-6.5.2 ...
```

Then start the dashboard:
```bash
streamlit run scripts/dashboard.py
```

---

### Option 3: Install in Smaller Steps

If the full installation times out, install packages one at a time:

```bash
venv\Scripts\activate.bat
pip install plotly
pip install streamlit
```

---

## After Installation

### Start Dashboard

**Option A: Batch file**
```
start_dashboard.bat
```

**Option B: Command line**
```bash
venv\Scripts\activate.bat
streamlit run scripts/dashboard.py
```

### Access Dashboard

Open your browser to:
```
http://localhost:8501
```

---

## Dashboard Features

Once installed, you'll see:

1. **Status Indicator**
   - 🔴 NOT COLLECTING
   - 🟡 STARTING
   - 🟢 COLLECTING
   - ✅ READY

2. **Key Metrics**
   - Total Events
   - Duration (hours/days)
   - Data Size (MB)
   - Data Gaps

3. **Progress Bar**
   - Target: 2 weeks (336 hours)
   - Current progress %

4. **Live Charts**
   - Spread over time
   - Order book imbalance
   - Trade distribution

5. **Auto-refresh**
   - Updates every 30 seconds
   - Real-time monitoring

---

## Is Dashboard Required?

**No!** The dashboard is optional. You can monitor progress using:

### Alternative 1: Quality Check Script
```bash
check_data_quality.bat
```

Shows:
- File counts
- Total events
- Duration
- Data gaps
- Quality assessment

### Alternative 2: File Explorer
Check `data/live/` folder:
- File sizes growing?
- New files created?
- Timestamps recent?

### Alternative 3: View CSV Files
Open CSV files in Excel or text editor:
- See actual data
- Check timestamps
- Verify format

---

## Troubleshooting

### Installation Fails

**Error: "Timeout"**
- Your internet may be slow
- Try installing overnight
- Or use smaller steps (Option 3)

**Error: "Permission denied"**
```bash
venv\Scripts\activate.bat
python -m pip install --user streamlit plotly
```

**Error: "No module named 'pip'"**
```bash
python -m ensurepip --upgrade
```

### Dashboard Won't Start

**Error: "streamlit: command not found"**
- Installation incomplete
- Retry installation
- Check virtual environment activated

**Error: "Port 8501 already in use"**
```bash
streamlit run scripts/dashboard.py --server.port 8502
```

**Error: "No data files found"**
- Start data collection first
- Wait a few minutes for files
- Check `data/live/` folder exists

---

## Installation Time

Typical installation times:

- **Fast internet (100+ Mbps):** 2-3 minutes
- **Medium internet (10-50 Mbps):** 5-10 minutes
- **Slow internet (<10 Mbps):** 10-20 minutes

Total download size: ~50-60 MB

---

## Do I Need This Now?

**No!** You can:

1. **Start data collection now** (no dashboard needed)
2. **Install dashboard later** (anytime during 2 weeks)
3. **Skip dashboard entirely** (use quality check script)

The most important thing is to start collecting data. The dashboard is just a nice-to-have visualization tool.

---

## Quick Decision Guide

### Install Dashboard If:
- ✓ You want real-time visualization
- ✓ You like seeing charts and graphs
- ✓ You have 10 minutes to spare
- ✓ You have stable internet

### Skip Dashboard If:
- ✓ You want to start collecting NOW
- ✓ You're OK with text-based monitoring
- ✓ You have slow internet
- ✓ You prefer simple tools

---

## Recommendation

**Start data collection first, install dashboard later.**

1. Run: `start_data_collection.bat`
2. Let it collect for a few hours
3. Then install dashboard when convenient
4. Or just use `check_data_quality.bat` daily

The data collection is the critical part. The dashboard is optional.

---

## Summary

- Dashboard installation: **In Progress**
- Required for data collection: **No**
- Can install later: **Yes**
- Alternative monitoring: **check_data_quality.bat**
- Recommendation: **Start collecting data now, install dashboard later**

---

**Focus on starting the data collection. The dashboard can wait!**
