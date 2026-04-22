# 🚀 Auto-Start Data Collection on Windows

This guide shows you how to make data collection start automatically when Windows boots up.

---

## Quick Setup (2 minutes)

### Step 1: Run Setup Script

1. Right-click `setup_startup.bat`
2. Select "Run as administrator"
3. Press any key to confirm
4. Done!

The data collection will now start automatically every time Windows boots.

---

## What Happens?

When Windows starts:
1. Waits 30 seconds for network to be ready
2. Activates Python virtual environment
3. Starts data collection in background
4. Logs output to `logs/data_collection.log`

---

## Managing Auto-Start

### Check Status
Run: `check_startup_status.bat`

Shows if auto-start is enabled and task details.

### Remove Auto-Start
Run: `remove_startup.bat`

Disables automatic startup (you can still run manually).

### View Logs
Check: `logs/data_collection.log`

See what's happening with data collection.

---

## Manual Control

### Start Manually (with console)
Run: `start_data_collection.bat`

Shows live output in console window.

### Stop Data Collection

**Option 1: Task Manager**
1. Press `Ctrl+Shift+Esc`
2. Find "Python" process
3. Right-click → End task

**Option 2: Command Line**
```cmd
taskkill /f /im python.exe
```

---

## Troubleshooting

### Data Collection Not Starting?

**Check the log file:**
```cmd
type logs\data_collection.log
```

**Common issues:**

1. **Virtual environment not found**
   - Make sure `venv` folder exists
   - Run: `python -m venv venv`

2. **Network not ready**
   - Script waits 30 seconds after boot
   - Increase wait time in `start_data_collection_silent.bat`

3. **Python not in PATH**
   - Virtual environment should handle this
   - Check: `venv\Scripts\python.exe` exists

### Task Not Created?

**Run as Administrator:**
- Right-click `setup_startup.bat`
- Select "Run as administrator"

**Check Task Scheduler:**
1. Press `Win+R`
2. Type: `taskschd.msc`
3. Look for "M281M_DataCollection"

### Want to See Console Output?

Edit `start_data_collection_silent.bat`:
- Remove the `>> logs/data_collection.log 2>&1` part
- Or run `start_data_collection.bat` manually

---

## Advanced Configuration

### Change Wait Time

Edit `start_data_collection_silent.bat`:
```bat
REM Change 30 to desired seconds
timeout /t 30 /nobreak > nul
```

### Run as Different User

Edit task in Task Scheduler:
1. Open `taskschd.msc`
2. Find "M281M_DataCollection"
3. Right-click → Properties
4. Change user account

### Run on Schedule Instead of Startup

Use Task Scheduler to set custom schedule:
1. Open `taskschd.msc`
2. Find "M281M_DataCollection"
3. Right-click → Properties
4. Go to "Triggers" tab
5. Edit or add new trigger

---

## Files Created

- `setup_startup.bat` - Configures auto-start
- `remove_startup.bat` - Removes auto-start
- `check_startup_status.bat` - Check if enabled
- `start_data_collection_silent.bat` - Background version
- `logs/data_collection.log` - Output log

---

## Security Notes

- Task runs with your user account
- No admin privileges required after setup
- Data collection only connects to Binance API
- No incoming network connections

---

## Testing

### Test Without Rebooting

1. Open Task Scheduler (`taskschd.msc`)
2. Find "M281M_DataCollection"
3. Right-click → Run
4. Check `logs/data_collection.log`

### Test After Reboot

1. Restart Windows
2. Wait 1-2 minutes
3. Check Task Manager for Python process
4. Check `logs/data_collection.log`
5. Check `data/live/` for new files

---

## Uninstall

To completely remove:

1. Run `remove_startup.bat`
2. Delete these files:
   - `setup_startup.bat`
   - `remove_startup.bat`
   - `check_startup_status.bat`
   - `start_data_collection_silent.bat`
   - `logs/data_collection.log`

---

## Summary

**Enable:** Run `setup_startup.bat` as admin
**Disable:** Run `remove_startup.bat`
**Check:** Run `check_startup_status.bat`
**Logs:** Check `logs/data_collection.log`

Data collection will run silently in the background, collecting market data 24/7!
