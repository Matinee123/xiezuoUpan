@echo off
chcp 65001 >nul
title AI 写作工作台 - 通用版
echo ========================================
echo   AI 写作工作台 v1.0.0 - 通用版
echo   正在启动...
echo ========================================
echo.

set "ROOT=%~dp0.."
cd /d "%ROOT%"

python -m 通用写作.server
if %errorlevel% neq 0 (
    echo.
    echo [错误] Python 未找到或启动失败
    echo 请确保已安装 Python 3.10+
    echo.
    pause
)
