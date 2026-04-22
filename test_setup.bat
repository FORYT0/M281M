@echo off
echo ============================================================
echo M281M System Setup Test
echo ============================================================
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

echo Testing Python version...
python --version
echo.

echo Testing pandas...
python -c "import pandas; print('pandas:', pandas.__version__)"
echo.

echo Testing websockets...
python -c "import websockets; print('websockets:', websockets.__version__)"
echo.

echo Testing ccxt...
python -c "import ccxt; print('ccxt:', ccxt.__version__)"
echo.

echo Testing numpy...
python -c "import numpy; print('numpy:', numpy.__version__)"
echo.

echo Checking data directory...
if exist "data\live" (
    echo data/live directory: EXISTS
) else (
    echo data/live directory: MISSING - Creating...
    mkdir data\live
)
echo.

echo ============================================================
echo Setup Test Complete!
echo.
echo If all tests passed, you're ready to start data collection.
echo Run: start_data_collection.bat
echo ============================================================
echo.

pause
