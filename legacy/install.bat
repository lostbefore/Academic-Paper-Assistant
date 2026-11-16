@echo off
chcp 65001 >nul
title Academic Paper Assistant - 安装
color 0B

echo ==========================================
echo   Academic Paper Assistant - 安装向导
echo ==========================================
echo.

cd /d "%~dp0"

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 未安装，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python 已安装

:: 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js 未安装，请先安装 Node.js 18+
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js 已安装

:: 创建虚拟环境
if not exist ".venv" (
    echo [INFO] 创建 Python 虚拟环境...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] 创建虚拟环境失败
        pause
        exit /b 1
    )
)
echo [OK] 虚拟环境已就绪

:: 激活虚拟环境并安装依赖
echo [INFO] 安装 Python 依赖...
call .venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Python 依赖安装失败
    pause
    exit /b 1
)
echo [OK] Python 依赖安装完成

:: 安装前端依赖
echo [INFO] 安装前端依赖...
cd frontend
call npm install
if errorlevel 1 (
    echo [ERROR] 前端依赖安装失败
    pause
    exit /b 1
)
cd ..
echo [OK] 前端依赖安装完成

:: 检查 .env 文件
if not exist ".env" (
    echo.
    echo [WARNING] 未找到 .env 配置文件
    echo [INFO] 正在创建 .env 模板...
    (
        echo # Anthropic API 配置（必需）
        echo ANTHROPIC_API_KEY=your_claude_api_key_here
        echo ANTHROPIC_API_BASE=
        echo ANTHROPIC_MODEL=claude-sonnet-4-6-20251001
        echo.
        echo # Semantic Scholar API（可选）
        echo SEMANTIC_SCHOLAR_API_KEY=
        echo.
        echo # 图片搜索 API（可选）
        echo SERPER_API_KEY=
        echo UNSPLASH_ACCESS_KEY=
        echo UNSPLASH_SECRET_KEY=
        echo BING_IMAGE_API_KEY=
        echo.
        echo # 应用配置
        echo DEFAULT_CITATION_STYLE=apa
        echo ENABLE_IMAGES=true
        echo MAX_IMAGES_PER_PAPER=3
        echo.
        echo # CORS 配置（部署时使用）
        echo CORS_ORIGINS=http://localhost:5173,http://localhost:3000
    ) > .env
    echo [OK] 已创建 .env 模板文件
    echo [ACTION] 请编辑 .env 文件，填入你的 API 密钥
    echo.
    start notepad .env
) else (
    echo [OK] .env 配置文件已存在
)

echo.
echo ==========================================
echo   安装完成！
echo ==========================================
echo.
echo 使用方法:
echo   1. 双击 start.bat 启动前后端
echo   2. 浏览器访问 http://localhost:5173
echo.
pause
