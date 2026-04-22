@echo off
echo ============================================================
echo M281M AI Trading System - Data Quality Check
echo ============================================================
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

python scripts/monitor_data_quality.py

echo.
echo ============================================================
pause
