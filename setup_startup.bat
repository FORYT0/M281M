@echo off
REM ============================================================
REM Setup Data Collection to Run on Windows Startup
REM ============================================================

echo.
echo This will configure data collection to start automatically
echo when Windows boots up.
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause > nul

REM Get the current directory (project root)
set "PROJECT_DIR=%~dp0"
set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

echo.
echo Creating startup task...
echo.

REM Create scheduled task to run on startup
schtasks /create /tn "M281M_DataCollection" /tr "\"%PROJECT_DIR%\start_data_collection_silent.bat\"" /sc onstart /ru "%USERNAME%" /rl highest /f

if %errorlevel% equ 0 (
    echo.
    echo ============================================================
    echo SUCCESS! Data collection will now start on Windows boot.
    echo ============================================================
    echo.
    echo Task Name: M281M_DataCollection
    echo Script: %PROJECT_DIR%\start_data_collection_silent.bat
    echo.
    echo To manage this task:
    echo   - View: taskschd.msc ^(Task Scheduler^)
    echo   - Remove: remove_startup.bat
    echo   - Test: Run "Task Scheduler" and manually run the task
    echo.
    pause
) else (
    echo.
    echo ERROR: Failed to create startup task.
    echo Please run this script as Administrator.
    echo.
    pause
)
