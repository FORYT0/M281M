# Troubleshooting Guide

## Common Issues and Solutions

### Issue: "ModuleNotFoundError: No module named 'pandas'"

**Problem:** Virtual environment not activated

**Solution:**
```bash
# Activate virtual environment first
.\venv\Scripts\Activate.ps1

# Then run the script
python scripts/record_live_data.py
```

**Or use the batch file (auto-activates):**
```bash
start_data_collection.bat
```

---

### Issue: "Connection refused" or "Cannot connect to Binance"

**Problem:** Network issue or Binance is down

**Solutions:**
1. Check your internet connection
2. Try again in a few minutes
3. Check Binance status: https://www.binance.com/en/support/announcement
4. Try using a VPN if Binance is blocked in your region

---

### Issue: "Disk full" or "No space left"

**Problem:** Not enough disk space

**Solutions:**
1. Free up space (need 50GB minimum)
2. Delete old files
3. Move data to external drive
4. Clean up temporary files

**Check disk space:**
```bash
# Windows
dir data\live
```

---

### Issue: Script stops unexpectedly

**Problem:** Various reasons (network, system sleep, etc.)

**Solutions:**
1. Check logs for error messages
2. Restart the script
3. Ensure computer doesn't sleep
4. Use Task Scheduler for auto-restart

**Prevent sleep:**
- Windows Settings > System > Power & Sleep
- Set "When plugged in, PC goes to sleep after" to "Never"

---

### Issue: "Permission denied" when saving files

**Problem:** File permissions or antivirus blocking

**Solutions:**
1. Run as administrator
2. Check antivirus settings
3. Add exception for M281M folder
4. Check folder permissions

---

### Issue: Data has gaps

**Problem:** Connection drops or script stopped

**Solutions:**
1. Check if script is still running
2. Review logs for disconnections
3. Ensure stable internet connection
4. Use wired connection instead of WiFi

**Check data quality:**
```bash
check_data_quality.bat
```

---

### Issue: High CPU usage

**Problem:** Normal for real-time data processing

**Solutions:**
1. This is expected behavior
2. Close other applications
3. Upgrade hardware if needed
4. Reduce update frequency (advanced)

---

### Issue: "Import error" or "Module not found"

**Problem:** Missing dependencies

**Solution:**
```bash
# Activate venv
.\venv\Scripts\Activate.ps1

# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

---

### Issue: Batch file doesn't work

**Problem:** Execution policy or path issues

**Solutions:**

**Option 1: Use PowerShell directly**
```powershell
.\venv\Scripts\Activate.ps1
python scripts/record_live_data.py
```

**Option 2: Change execution policy**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Option 3: Use Command Prompt**
```cmd
venv\Scripts\activate.bat
python scripts\record_live_data.py
```

---

### Issue: "WebSocket connection failed"

**Problem:** Firewall or network blocking WebSocket

**Solutions:**
1. Check firewall settings
2. Allow Python through firewall
3. Try different network
4. Use VPN if needed

**Test connection:**
```bash
python -c "import websockets; print('websockets installed')"
```

---

### Issue: Data files are empty or very small

**Problem:** Script not running long enough or connection issues

**Solutions:**
1. Let script run for at least 1 hour
2. Check if WebSocket connected successfully
3. Look for "WebSocket connected successfully" message
4. Check logs for errors

---

### Issue: "Rate limit exceeded"

**Problem:** Too many requests to Binance

**Solutions:**
1. This shouldn't happen with our setup
2. Wait a few minutes
3. Restart the script
4. Check if you're running multiple instances

---

## Verification Steps

### 1. Check Virtual Environment
```bash
# Should show (venv) in prompt
.\venv\Scripts\Activate.ps1

# Should print pandas version
python -c "import pandas; print(pandas.__version__)"
```

### 2. Check Dependencies
```bash
pip list | findstr /C:"pandas" /C:"websockets" /C:"ccxt"
```

Should show:
- pandas 3.0.0 (or similar)
- websockets 16.0 (or similar)
- ccxt 4.5.38 (or similar)

### 3. Check Data Directory
```bash
dir data\live
```

Should show CSV files after running for a while.

### 4. Check Connection
```bash
python scripts/record_live_data.py
```

Should see:
- "Connecting to wss://stream.binance.com..."
- "WebSocket connected successfully"
- Statistics every 60 seconds

---

## Getting Help

### Check Logs
```bash
# View recent logs
type logs\m281m.log
```

### Check Documentation
- `START_HERE.md` - Getting started
- `DEPLOYMENT_CHECKLIST.md` - Step-by-step guide
- `QUICK_START.md` - Quick reference
- `docs/DEPLOYMENT_GUIDE.md` - Complete guide

### Common Commands
```bash
# Activate venv
.\venv\Scripts\Activate.ps1

# Start data collection
python scripts/record_live_data.py

# Check data quality
python scripts/monitor_data_quality.py

# Test system
python scripts/test_risk_management.py
```

---

## Prevention Tips

1. **Keep computer awake:** Disable sleep mode
2. **Stable internet:** Use wired connection
3. **Enough space:** Monitor disk usage
4. **Regular checks:** Run quality check daily
5. **Backup data:** Copy data folder regularly

---

## Emergency Recovery

### If everything fails:

1. **Restart fresh:**
```bash
# Deactivate venv
deactivate

# Reactivate
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt

# Try again
python scripts/record_live_data.py
```

2. **Check system:**
- Python version: `python --version` (should be 3.11+)
- Disk space: `dir`
- Internet: Open browser, check connection

3. **Start over:**
- Delete `data/live/*` if corrupted
- Restart data collection
- Monitor closely for first hour

---

## Still Having Issues?

1. Check all documentation in `docs/`
2. Review error messages carefully
3. Search error message online
4. Check Binance API status
5. Verify system requirements

---

**Most Common Fix:** Just activate the virtual environment!

```bash
.\venv\Scripts\Activate.ps1
```

Then run your command again.
