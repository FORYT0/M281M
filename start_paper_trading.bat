@echo off
echo ============================================================
echo M281M AI Trading System - Paper Trading
echo ============================================================
echo.
echo This will start paper trading with your trained models.
echo.
echo Initial Capital: $10,000 (simulated)
echo Models: Momentum, Mean Reversion, Order Flow
echo.
echo The system will:
echo   - Connect to live Binance market data
echo   - Make trading decisions using your trained models
echo   - Execute simulated trades (no real money)
echo   - Track performance in real-time
echo.
echo Press Ctrl+C to stop and save results
echo.
echo Press any key to start paper trading...
pause > nul

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting paper trading...
echo.

python scripts/simple_paper_trading.py

pause
