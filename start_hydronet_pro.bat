@echo off
REM HydroNet Pro 启动脚本 (Windows)

echo ================================
echo 🌊 HydroNet Pro 启动脚本
echo ================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python
    echo 请先安装Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python已安装

REM 检查虚拟环境
if not exist "venv\" (
    echo.
    echo 📦 创建Python虚拟环境...
    python -m venv venv
    
    if errorlevel 1 (
        echo ❌ 创建虚拟环境失败
        pause
        exit /b 1
    )
    
    echo ✅ 虚拟环境创建成功
)

REM 激活虚拟环境
echo.
echo 🔌 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
if not exist "venv\.dependencies_installed" (
    echo.
    echo 📥 安装Python依赖...
    python -m pip install --upgrade pip
    pip install -r requirements_pro.txt
    
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
    
    type nul > venv\.dependencies_installed
    echo ✅ 依赖安装成功
) else (
    echo ✅ 依赖已安装
)

REM 检查环境变量文件
if not exist ".env" (
    echo.
    echo ⚠️  警告: 未找到.env文件
    echo 📝 创建默认.env文件...
    
    (
        echo # HydroNet Pro 配置文件
        echo.
        echo # Flask配置
        echo FLASK_APP=app_hydronet_pro.py
        echo FLASK_ENV=development
        echo SECRET_KEY=your-secret-key-change-this
        echo.
        echo # 服务器配置
        echo HOST=0.0.0.0
        echo PORT=5000
        echo DEBUG=True
        echo.
        echo # 阿里云API密钥
        echo ALIYUN_API_KEY=your-api-key-here
        echo QWEN_MODEL=qwen-plus
        echo.
        echo # 数据库（SQLite）
        echo DATABASE_PATH=hydronet_pro.db
    ) > .env
    
    echo ✅ .env文件已创建
    echo.
    echo ⚠️  重要: 请编辑.env文件，配置您的阿里云API密钥！
    echo    编辑命令: notepad .env
    echo.
    pause
)

REM 启动应用
echo.
echo ================================
echo 🚀 启动HydroNet Pro...
echo ================================
echo.
echo 💡 访问地址: http://localhost:5000
echo 💡 按Ctrl+C停止服务
echo.
echo ================================
echo.

REM 运行Flask应用
python app_hydronet_pro.py

pause
