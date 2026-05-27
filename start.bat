@echo off
chcp 65001 >nul
title AI 写作工作台

echo.
echo    AI 写作工作台 v1.0.0
echo    正在启动...
echo.

"%~dp0_env\Scripts\python.exe" -B "%~dp0launcher.py"
if errorlevel 1 (
    echo.
    echo [错误] 启动失败
    echo 请确认 _env 目录存在且完整
    echo.
)
pause
