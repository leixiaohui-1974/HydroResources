#!/bin/bash

# HydroNet Pro 启动脚本

echo "================================"
echo "🌊 HydroNet Pro 启动脚本"
echo "================================"
echo ""

# 检查Python版本
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
echo "📌 Python版本: $python_version"

if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3"
    echo "请先安装Python 3.8+"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
    
    if [ $? -ne 0 ]; then
        echo "❌ 创建虚拟环境失败"
        exit 1
    fi
    
    echo "✅ 虚拟环境创建成功"
fi

# 激活虚拟环境
echo ""
echo "🔌 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
if [ ! -f "venv/.dependencies_installed" ]; then
    echo ""
    echo "📥 安装Python依赖..."
    pip install --upgrade pip
    pip install -r requirements_pro.txt
    
    if [ $? -eq 0 ]; then
        touch venv/.dependencies_installed
        echo "✅ 依赖安装成功"
    else
        echo "❌ 依赖安装失败"
        exit 1
    fi
else
    echo "✅ 依赖已安装"
fi

# 检查环境变量
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  警告: 未找到.env文件"
    echo "📝 创建默认.env文件..."
    
    cat > .env << EOF
# HydroNet Pro 配置文件

# Flask配置
FLASK_APP=app_hydronet_pro.py
FLASK_ENV=development
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

# 服务器配置
HOST=0.0.0.0
PORT=5000
DEBUG=True

# 阿里云API密钥
ALIYUN_API_KEY=your-api-key-here
QWEN_MODEL=qwen-plus

# 数据库（SQLite）
DATABASE_PATH=hydronet_pro.db
EOF
    
    echo "✅ .env文件已创建"
    echo ""
    echo "⚠️  重要: 请编辑.env文件，配置您的阿里云API密钥！"
    echo "   编辑命令: nano .env"
    echo ""
    read -p "按Enter键继续..."
fi

# 检查API密钥
source .env
if [ "$ALIYUN_API_KEY" = "your-api-key-here" ]; then
    echo ""
    echo "❌ 错误: 请先配置阿里云API密钥"
    echo "   1. 编辑.env文件: nano .env"
    echo "   2. 设置ALIYUN_API_KEY=你的密钥"
    echo "   3. 重新运行此脚本"
    echo ""
    exit 1
fi

# 启动应用
echo ""
echo "================================"
echo "🚀 启动HydroNet Pro..."
echo "================================"
echo ""
echo "💡 访问地址: http://localhost:5000"
echo "💡 按Ctrl+C停止服务"
echo ""
echo "================================"
echo ""

# 运行Flask应用
python3 app_hydronet_pro.py
