@echo off
REM ============================================================
REM M281M Data Collection - Silent Startup Version
REM Runs in background without console window
REM ============================================================

REM Change to project directory
cd /d "%~dp0"

REM Wait 30 seconds after boot for network to be ready
timeout /t 30 /nobreak > nul

REM Activate virtual environment and start data collection
call venv\Scripts\activate.bat

REM Run in background, redirect output to log file
python scripts/record_live_data.py >> logs/data_collection.log 2>&1
