@echo off
REM ================================================
REM HydroNet 本地版一键启动脚本 (Windows)
REM ================================================

echo ================================================
echo 🌊 HydroNet 本地版 - 一键启动
echo ================================================
echo.

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Python
    echo 请先安装Python 3.8+
    pause
    exit /b 1
)

echo ✓ Python已安装
python --version

REM 检查虚拟环境
if not exist "venv" (
    echo.
    echo [1/4] 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo [2/4] 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo [3/4] 安装依赖包...
pip install --upgrade pip -q
pip install -r requirements_local.txt -q

REM 检查配置
if not exist ".env" (
    echo.
    echo ⚠️  配置文件不存在
    echo 正在创建配置文件...
    copy .env.example .env
    
    echo.
    echo 请编辑 .env 文件并填写您的阿里云API密钥：
    echo   ALIYUN_API_KEY=sk-xxxxxxxxxxxxxxxx
    echo.
    echo 获取地址: https://dashscope.console.aliyun.com/apiKey
    echo.
    notepad .env
)

echo.
echo ================================================
echo [4/4] 启动HydroNet本地版...
echo ================================================
echo.
echo 💡 提示:
echo   - 无需数据库配置（自动使用SQLite）
echo   - 数据保存在：hydronet_local.db
echo   - 访问地址：http://localhost:5000
echo   - 停止服务：按 Ctrl+C
echo.
echo ================================================
echo.

REM 启动应用
python app_local.py

pause
