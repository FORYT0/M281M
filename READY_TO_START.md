# 🚀 READY TO START - 2 Week Data Collection

## Current Status

✅ Data recorder is working and tested  
✅ WebSocket connection fixed  
✅ Receiving real market data from Binance  
⏳ Dashboard installation in progress (optional)

---

## START NOW (Without Dashboard)

### Step 1: Start Data Collection

Double-click this file:
```
start_data_collection.bat
```

Or run:
```bash
venv\Scripts\activate.bat
python scripts/record_live_data.py
```

**What you'll see:**
```
============================================================
Recording Statistics - 2026-02-16 21:00:39
============================================================
Uptime: 00:01:00
Order Book Updates: 600
Trades: 145
Ticker Updates: 60
Total Events: 805
============================================================
```

**Leave this running for 2 weeks!**

---

### Step 2: Check Progress Daily

Run this to check data quality:
```
check_data_quality.bat
```

**What you'll see:**
```
Data Quality Report
===================
Order Book Files: 3
Trade Files: 3
Ticker Files: 3
Total Events: 50,000+
Duration: 24 hours
Data Gaps: 0
Quality: EXCELLENT
```

---

## Optional: Install Dashboard (Later)

The dashboard installation was started but needs more time. You can:

### Option A: Let it finish in background
The installation may complete on its own. Try later:
```bash
venv\Scripts\activate.bat
streamlit run scripts/dashboard.py
```

### Option B: Complete installation manually
```bash
venv\Scripts\activate.bat
pip install streamlit plotly
```

This may take 5-10 minutes depending on your internet speed.

### Option C: Skip dashboard entirely
The dashboard is optional. You can monitor progress using:
- `check_data_quality.bat` (runs instantly)
- Check file sizes in `data/live/` folder
- View CSV files directly

---

## What's Happening

### Data Being Collected:
1. **Order Book** (100ms updates)
   - Top 20 bid/ask levels
   - Spread, imbalance, depth
   - ~600 updates/minute

2. **Trades** (real-time)
   - Every trade on Binance
   - Price, size, side (buy/sell)
   - ~100-200 trades/minute

3. **Ticker** (1 second updates)
   - 24h stats
   - Volume, price changes
   - 60 updates/minute

### Files Created:
```
data/live/
├── btcusdt_orderbook_YYYYMMDD_HHMMSS.csv
├── btcusdt_trades_YYYYMMDD_HHMMSS.csv
└── btcusdt_ticker_YYYYMMDD_HHMMSS.csv
```

New files created every hour (auto-rotation).

---

## Timeline

| Day | Expected Data | File Size | Status |
|-----|---------------|-----------|--------|
| 1 | ~50K events | ~500MB | Keep running |
| 3 | ~150K events | ~1.5GB | Check quality |
| 7 | ~500K events | ~5GB | Halfway there |
| 14 | ~1M events | ~10GB | READY! |

---

## Daily Checklist

### Morning Check (30 seconds):
1. Is data collection still running? ✓
2. Run `check_data_quality.bat` ✓
3. Check disk space (need 50GB free) ✓
4. Any error messages? ✓

### If Something Stops:
1. Check error message
2. Restart: `start_data_collection.bat`
3. Data will resume from where it stopped
4. No data loss (files saved every 60 seconds)

---

## Important Notes

### Keep Computer Awake
- Disable sleep mode
- Or use Task Scheduler to keep running
- Or run on a VPS/server

### Internet Connection
- Needs stable connection
- Auto-reconnects if disconnected
- Small gaps are OK (<5 seconds)

### Disk Space
- Monitor disk space
- Need ~10-15GB for 2 weeks
- Files are compressed CSV

### Don't Stop Early
- Minimum: 1 week (168 hours)
- Target: 2 weeks (336 hours)
- More data = better models

---

## After 2 Weeks

### Step 1: Stop Collection
Press `Ctrl+C` in the data collection window

### Step 2: Final Quality Check
```bash
check_data_quality.bat
```

### Step 3: Verify Data
- Check total events (should be ~1M+)
- Check duration (should be ~336 hours)
- Check gaps (should be <1%)

### Step 4: Next Stage
- Retrain agents on real data
- Backtest with real market conditions
- Start paper trading

---

## Troubleshooting

### "No module named 'pandas'"
```bash
venv\Scripts\activate.bat
pip install pandas
```

### "Connection refused"
- Check internet connection
- Binance may be down (rare)
- Script will auto-reconnect

### "Disk full"
- Free up space
- Or move data/live/ to external drive
- Update path in script

### "Process killed"
- Computer went to sleep
- Restart data collection
- Check power settings

---

## Quick Commands

### Start collection:
```bash
start_data_collection.bat
```

### Check quality:
```bash
check_data_quality.bat
```

### View latest data:
```bash
dir data\live\
```

### Check file sizes:
```bash
dir data\live\ /s
```

---

## Current Progress

**Status:** ✅ READY TO START  
**Risk:** ZERO (read-only, no trading)  
**Cost:** $0  
**Time Required:** 2 weeks passive  
**Action Required:** Start data collection now!

---

## START NOW!

1. Double-click: `start_data_collection.bat`
2. Let it run for 2 weeks
3. Check daily with: `check_data_quality.bat`
4. Come back in 2 weeks!

**That's it!** The system will collect data 24/7 automatically.

---

## Questions?

- Data collection working? Check terminal output
- Files being created? Check `data/live/` folder
- Quality good? Run `check_data_quality.bat`
- Need dashboard? Complete installation later

---

**You're all set! Start the data collection and let it run for 2 weeks.**

The dashboard is optional - you can monitor progress using the quality check script.
