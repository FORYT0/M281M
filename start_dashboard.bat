@echo off
echo ============================================================
echo M281M Data Collection Dashboard
echo ============================================================
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.
echo Starting dashboard...
echo Dashboard will open in your browser automatically.
echo.
echo Press Ctrl+C to stop the dashboard
echo ============================================================
echo.

streamlit run scripts/dashboard.py

pause
