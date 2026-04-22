@echo off
REM ============================================================
REM Remove Data Collection from Windows Startup
REM ============================================================

echo.
echo This will remove the automatic data collection startup task.
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause > nul

echo.
echo Removing startup task...
echo.

schtasks /delete /tn "M281M_DataCollection" /f

if %errorlevel% equ 0 (
    echo.
    echo ============================================================
    echo SUCCESS! Data collection removed from startup.
    echo ============================================================
    echo.
) else (
    echo.
    echo ERROR: Task not found or could not be removed.
    echo.
)

pause
