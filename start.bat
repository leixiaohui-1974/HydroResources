@echo off
REM HydroNet 启动脚本 (Windows)

echo ========================================
echo 🌊 HydroNet 水网智能体系统 - 启动中...
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo ✓ Python已安装

REM 检查虚拟环境
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 🔧 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 📥 安装依赖包...
pip install -r requirements.txt -q

REM 检查配置文件
if not exist ".env" (
    echo ⚠️  警告: .env 配置文件不存在
    echo 📝 正在从模板创建配置文件...
    copy .env.example .env
    echo.
    echo ⚙️  请编辑 .env 文件并填写您的配置：
    echo    - TENCENT_SECRET_ID: 腾讯云密钥ID
    echo    - TENCENT_SECRET_KEY: 腾讯云密钥Key
    echo    - WECHAT_TOKEN: 微信公众号Token（可选）
    echo.
    notepad .env
)

REM 创建必要的目录
if not exist "logs" mkdir logs
if not exist "mcp_services" mkdir mcp_services

echo.
echo ========================================
echo ✅ 准备完成！
echo.
echo 🚀 启动方式：
echo    开发模式: python app.py
echo    生产模式: gunicorn -w 4 -b 0.0.0.0:5000 app:app
echo.
echo 🌐 访问地址:
echo    Web界面: http://localhost:5000
echo    API文档: http://localhost:5000/api/health
echo.
echo 📚 详细文档请查看: HYDRONET_README.md
echo ========================================
echo.

REM 启动应用
set /p answer="是否立即启动应用? (y/n): "
if /i "%answer%"=="y" (
    echo 🚀 启动HydroNet...
    python app.py
)

pause
