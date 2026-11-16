@echo off
chcp 65001 >nul
title Academic Paper Assistant - 一键启动
color 0A

echo ==========================================
echo   Academic Paper Assistant - 一键启动
echo ==========================================
echo.

:: 检查是否以管理员权限运行
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] 以管理员权限运行
) else (
    echo [WARNING] 建议以管理员权限运行，某些功能可能受限
    echo.
)

:: 设置工作目录
cd /d "%~dp0"
echo [INFO] 工作目录: %CD%
echo.

:: 检查虚拟环境
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] 虚拟环境不存在，请先运行安装脚本
    pause
    exit /b 1
)

:: 激活虚拟环境
call .venv\Scripts\activate.bat
echo [OK] 虚拟环境已激活

:: 检查前端依赖
if not exist "frontend\node_modules" (
    echo [WARNING] 前端依赖不存在，请先运行 install.bat
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   正在启动服务...
echo ==========================================
echo.

:: 启动后端（在新窗口）
echo [INFO] 启动后端服务 (http://localhost:8000)...
start "后端服务" cmd /k "cd /d %CD% && call .venv\Scripts\activate.bat && python backend/api.py"

:: 等待后端启动
timeout /t 3 /nobreak >nul

:: 启动前端（在新窗口）
echo [INFO] 启动前端服务 (http://localhost:5173)...
start "前端服务" cmd /k "cd /d %CD%\frontend && npm run dev"

echo.
echo ==========================================
echo   服务启动完成！
echo ==========================================
echo.
echo  后端地址: http://localhost:8000
echo  前端地址: http://localhost:5173
echo.
echo  按任意键关闭所有服务...
echo.
pause >nul

:: 关闭服务
echo [INFO] 正在关闭服务...
taskkill /FI "WINDOWTITLE eq 后端服务*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq 前端服务*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq 后端*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq 前端*" /F >nul 2>&1

echo [OK] 服务已关闭
timeout /t 2 /nobreak >nul
