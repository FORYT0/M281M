@echo off
REM ============================================================
REM Check Data Collection Startup Status
REM ============================================================

echo.
echo Checking if data collection is configured to run on startup...
echo.

schtasks /query /tn "M281M_DataCollection" /fo list /v

if %errorlevel% equ 0 (
    echo.
    echo ============================================================
    echo Data collection IS configured to run on startup.
    echo ============================================================
    echo.
    echo To remove: run remove_startup.bat
    echo.
) else (
    echo.
    echo ============================================================
    echo Data collection is NOT configured to run on startup.
    echo ============================================================
    echo.
    echo To enable: run setup_startup.bat
    echo.
)

pause
