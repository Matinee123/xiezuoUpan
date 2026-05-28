@echo off
chcp 65001 >nul
title AI 写作工作台 - 安装依赖
echo ========================================
echo   AI 写作工作台 - 安装依赖库
echo ========================================
echo.
echo 正在检查 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

echo 正在安装 PDF/DOCX 导出所需库...
"%~dp0_env\Scripts\python.exe" -m pip install reportlab python-docx -q
if %errorlevel% neq 0 (
    echo [警告] 部分库安装失败，导出 PDF/DOCX 功能不可用
    echo 但 Markdown/HTML 导出不受影响
) else (
    echo [成功] 依赖库安装完成
)

echo.
echo 安装完成！您可以双击 start.bat 启动写作工作台
echo.
pause
