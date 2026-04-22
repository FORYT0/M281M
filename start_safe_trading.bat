@echo off
echo ============================================================
echo M281M AI Trading System - SAFE Adaptive Paper Trading
echo ============================================================
echo.
echo SAFETY FEATURES ENABLED:
echo.
echo 1. HARD RISK KILL SWITCH
echo    - Stops if drawdown ^> 10%%
echo    - Stops after 5 consecutive losses
echo    - Stops if daily loss ^> 3%%
echo    - Stops if confidence drops ^< 60%%
echo.
echo 2. FIXED RISK PER TRADE
echo    - Risk only 1%% per trade ($100)
echo    - Position size calculated from stop loss
echo    - Stop loss: 0.5%% per trade
echo.
echo 3. CONTROLLED LEARNING
echo    - OBSERVE MODE for first 2 weeks
echo    - Collects experiences but does NOT update models
echo    - Models stay stable during validation
echo.
echo Initial Capital: $10,000 (simulated)
echo.
echo Press Ctrl+C to stop and save results
echo.
echo Press any key to start SAFE trading...
pause ^> nul

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting SAFE adaptive paper trading...
echo.

python scripts/safe_adaptive_trading.py

pause
