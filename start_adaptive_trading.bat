@echo off
echo ============================================================
echo M281M AI Trading System - ADAPTIVE Paper Trading
echo ============================================================
echo.
echo This system includes ONLINE LEARNING:
echo   - Models learn from every trade result
echo   - Performance tracking per model
echo   - Automatic retraining every 100 experiences
echo   - Weighted voting based on recent accuracy
echo.
echo Initial Capital: $10,000 (simulated)
echo Models: 3 AI agents with continuous learning
echo.
echo Press Ctrl+C to stop and save results
echo.
echo Press any key to start adaptive trading...
pause > nul

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting adaptive paper trading...
echo.

python scripts/adaptive_paper_trading.py

pause
