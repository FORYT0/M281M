@echo off
echo ============================================================
echo M281M AI Trading System - Agent Retraining
echo ============================================================
echo.
echo This will retrain all agents on your collected live data.
echo.
echo Data collected: 1.12 GB (20+ days)
echo Agents to train: 4 (Momentum, Mean Reversion, Order Flow, Regime)
echo.
echo This may take 30-60 minutes depending on your hardware.
echo.
echo Press any key to start training or Ctrl+C to cancel...
pause > nul

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting training...
echo.

python scripts/retrain_on_live_data.py

echo.
echo ============================================================
echo Training complete!
echo ============================================================
echo.
echo Check the models/ folder for trained models.
echo.
pause
