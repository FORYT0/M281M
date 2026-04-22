@echo off
echo ============================================================
echo M281M Paper Trading Dashboard
echo ============================================================
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.
echo Starting dashboard...
echo Dashboard will open in your browser automatically.
echo.
echo Features:
echo   - Real-time portfolio monitoring
echo   - Live trade history
echo   - Performance analytics
echo   - Risk metrics
echo   - Auto-refresh every 10 seconds
echo.
echo Press Ctrl+C to stop the dashboard
echo ============================================================
echo.

streamlit run scripts/paper_trading_dashboard.py

pause
