@echo off
echo ============================================================
echo M281M AI Trading System - Data Collection
echo ============================================================
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.
echo Starting live data recorder...
echo This will collect real market data from Binance.
echo.
echo Press Ctrl+C to stop recording
echo Data will be saved to: data/live/
echo.
echo ============================================================
echo.

python scripts/record_live_data.py

pause
