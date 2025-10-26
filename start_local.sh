#!/bin/bash
# ================================================
# HydroNet 本地版一键启动脚本
# ================================================

echo "================================================"
echo "🌊 HydroNet 本地版 - 一键启动"
echo "================================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python 3"
    echo "请先安装Python 3.8+"
    exit 1
fi

echo -e "${GREEN}✓ Python已安装${NC}"
python3 --version

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo ""
    echo -e "${GREEN}[1/4] 创建虚拟环境...${NC}"
    python3 -m venv venv
fi

# 激活虚拟环境
echo -e "${GREEN}[2/4] 激活虚拟环境...${NC}"
source venv/bin/activate

# 安装依赖
echo -e "${GREEN}[3/4] 安装依赖包...${NC}"
pip install --upgrade pip -q
pip install -r requirements_local.txt -q

# 检查配置
if [ ! -f ".env" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  配置文件不存在${NC}"
    echo "正在创建配置文件..."
    cp .env.example .env
    
    echo ""
    echo "请编辑 .env 文件并填写您的阿里云API密钥："
    echo "  ALIYUN_API_KEY=sk-xxxxxxxxxxxxxxxx"
    echo ""
    echo "获取地址: https://dashscope.console.aliyun.com/apiKey"
    echo ""
    read -p "按Enter继续编辑配置文件..." 
    ${EDITOR:-nano} .env
fi

echo ""
echo "================================================"
echo -e "${GREEN}[4/4] 启动HydroNet本地版...${NC}"
echo "================================================"
echo ""
echo "💡 提示:"
echo "  - 无需数据库配置（自动使用SQLite）"
echo "  - 数据保存在：hydronet_local.db"
echo "  - 访问地址：http://localhost:5000"
echo "  - 停止服务：按 Ctrl+C"
echo ""
echo "================================================"
echo ""

# 启动应用
python3 app_local.py
