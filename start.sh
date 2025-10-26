#!/bin/bash
# HydroNet 启动脚本

echo "🌊 HydroNet 水网智能体系统 - 启动中..."
echo "================================================"

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python版本: $python_version"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 安装依赖包..."
pip install -r requirements.txt -q

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "⚠️  警告: .env 配置文件不存在"
    echo "📝 正在从模板创建配置文件..."
    cp .env.example .env
    echo ""
    echo "⚙️  请编辑 .env 文件并填写您的配置："
    echo "   - TENCENT_SECRET_ID: 腾讯云密钥ID"
    echo "   - TENCENT_SECRET_KEY: 腾讯云密钥Key"
    echo "   - WECHAT_TOKEN: 微信公众号Token（可选）"
    echo ""
    read -p "是否现在编辑配置文件? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    else
        echo "❌ 跳过配置，您可以稍后手动编辑 .env 文件"
        echo ""
    fi
fi

# 创建必要的目录
mkdir -p logs
mkdir -p mcp_services

echo ""
echo "================================================"
echo "✅ 准备完成！"
echo ""
echo "🚀 启动方式："
echo "   开发模式: python app.py"
echo "   生产模式: gunicorn -w 4 -b 0.0.0.0:5000 app:app"
echo ""
echo "🌐 访问地址:"
echo "   Web界面: http://localhost:5000"
echo "   API文档: http://localhost:5000/api/health"
echo ""
echo "📚 详细文档请查看: HYDRONET_README.md"
echo "================================================"
echo ""

# 询问是否立即启动
read -p "是否立即启动应用? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 启动HydroNet..."
    python app.py
fi
