@echo off
chcp 65001 >nul
title AI Writing Workstation

echo.
echo    AI Writing Workstation v1.0.0
echo    Starting...
echo.

"%~dp0_env\Scripts\python.exe" "%~dp0launcher.py"
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start
    echo Please make sure _env directory exists
    echo.
)
pause
