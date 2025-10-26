#!/bin/bash
# HydroNet Pro + HydroSIS 一键启动脚本

set -e

echo "================================================================"
echo "🚀 HydroNet Pro + HydroSIS MCP 一键启动"
echo "================================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker未安装${NC}"
        echo "请先安装Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose未安装${NC}"
        echo "请先安装Docker Compose"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker已安装${NC}"
}

# 克隆HydroSIS项目
clone_hydrosis() {
    if [ -d "HydroSIS" ]; then
        echo -e "${YELLOW}⚠️  HydroSIS目录已存在，跳过克隆${NC}"
    else
        echo -e "${BLUE}📥 克隆HydroSIS项目...${NC}"
        git clone -b codex/main-0919 https://github.com/leixiaohui-1974/HydroSIS.git
        echo -e "${GREEN}✅ HydroSIS项目克隆完成${NC}"
    fi
}

# 启动HydroSIS MCP服务器
start_hydrosis() {
    echo ""
    echo -e "${BLUE}🌊 启动HydroSIS MCP服务器...${NC}"
    
    cd HydroSIS/mcp_server
    
    # 创建.env文件
    if [ ! -f .env ]; then
        cat > .env << EOF
DATA_ROOT=/data
HOST=0.0.0.0
PORT=8080
WORKERS=4
LOG_LEVEL=INFO
EOF
        echo -e "${GREEN}✅ 已创建HydroSIS .env配置${NC}"
    fi
    
    # 启动服务
    docker-compose up -d
    
    cd ../..
    
    # 等待服务启动
    echo -e "${YELLOW}⏳ 等待HydroSIS服务启动...${NC}"
    sleep 10
    
    # 健康检查
    if curl -s http://localhost:8080/health > /dev/null; then
        echo -e "${GREEN}✅ HydroSIS MCP服务器已启动 (端口: 8080)${NC}"
    else
        echo -e "${RED}❌ HydroSIS服务启动失败${NC}"
        echo "查看日志: cd HydroSIS/mcp_server && docker-compose logs"
        exit 1
    fi
}

# 配置HydroNet Pro
configure_hydronet() {
    echo ""
    echo -e "${BLUE}🔧 配置HydroNet Pro...${NC}"
    
    # 检查.env文件
    if [ ! -f .env ]; then
        echo -e "${YELLOW}⚠️  未找到.env文件，创建默认配置${NC}"
        cat > .env << 'EOF'
# Flask配置
FLASK_APP=app_hydronet_pro.py
FLASK_ENV=production
SECRET_KEY=your-secret-key-change-this
HOST=0.0.0.0
PORT=5000
DEBUG=False

# 阿里云通义千问
ALIYUN_API_KEY=your-api-key-here
QWEN_MODEL=qwen-plus

# 数据库
DATABASE_PATH=hydronet_pro.db

# HydroSIS MCP集成
HYDROSIS_MCP_ENABLED=true
HYDROSIS_MCP_URL=http://localhost:8080
HYDROSIS_MCP_TIMEOUT=300
EOF
        echo -e "${YELLOW}⚠️  请编辑.env文件，设置ALIYUN_API_KEY${NC}"
    else
        # 确保HydroSIS配置存在
        if ! grep -q "HYDROSIS_MCP_ENABLED" .env; then
            cat >> .env << 'EOF'

# HydroSIS MCP集成
HYDROSIS_MCP_ENABLED=true
HYDROSIS_MCP_URL=http://localhost:8080
HYDROSIS_MCP_TIMEOUT=300
EOF
            echo -e "${GREEN}✅ 已添加HydroSIS配置到.env${NC}"
        else
            # 确保启用
            sed -i 's/HYDROSIS_MCP_ENABLED=false/HYDROSIS_MCP_ENABLED=true/' .env 2>/dev/null || true
            echo -e "${GREEN}✅ HydroSIS集成已启用${NC}"
        fi
    fi
}

# 安装Python依赖
install_dependencies() {
    echo ""
    echo -e "${BLUE}📦 安装Python依赖...${NC}"
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3未安装${NC}"
        exit 1
    fi
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        echo "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装依赖
    if [ -f requirements_pro.txt ]; then
        pip install -q --upgrade pip
        pip install -q -r requirements_pro.txt
        echo -e "${GREEN}✅ Python依赖已安装${NC}"
    else
        echo -e "${RED}❌ requirements_pro.txt不存在${NC}"
        exit 1
    fi
}

# 启动HydroNet Pro
start_hydronet() {
    echo ""
    echo -e "${BLUE}🚀 启动HydroNet Pro...${NC}"
    
    # 检查API Key
    if grep -q "your-api-key-here" .env; then
        echo -e "${RED}❌ 请先在.env中设置ALIYUN_API_KEY！${NC}"
        exit 1
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 启动应用
    python3 app_hydronet_pro.py &
    HYDRONET_PID=$!
    
    echo -e "${GREEN}✅ HydroNet Pro已启动 (PID: $HYDRONET_PID)${NC}"
    
    # 保存PID
    echo $HYDRONET_PID > .hydronet.pid
}

# 显示状态
show_status() {
    echo ""
    echo "================================================================"
    echo -e "${GREEN}🎉 启动完成！${NC}"
    echo "================================================================"
    echo ""
    echo "📊 服务状态:"
    echo ""
    echo "  🌊 HydroSIS MCP Server:"
    echo "     地址: http://localhost:8080"
    echo "     健康检查: http://localhost:8080/health"
    echo "     工具列表: http://localhost:8080/mcp/tools"
    echo ""
    echo "  🚀 HydroNet Pro:"
    echo "     地址: http://localhost:5000"
    echo "     状态: 正在启动..."
    echo ""
    echo "================================================================"
    echo ""
    echo "💡 使用提示:"
    echo "  - 在浏览器访问 http://localhost:5000 开始使用"
    echo "  - AI可以调用23个工具（5个HydroNet + 18个HydroSIS）"
    echo "  - 查看HydroSIS日志: cd HydroSIS/mcp_server && docker-compose logs -f"
    echo "  - 停止服务: ./stop_all.sh"
    echo ""
    echo "================================================================"
}

# 主函数
main() {
    echo "步骤1: 检查Docker..."
    check_docker
    
    echo ""
    echo "步骤2: 克隆HydroSIS项目..."
    clone_hydrosis
    
    echo ""
    echo "步骤3: 启动HydroSIS MCP服务器..."
    start_hydrosis
    
    echo ""
    echo "步骤4: 配置HydroNet Pro..."
    configure_hydronet
    
    echo ""
    echo "步骤5: 安装Python依赖..."
    install_dependencies
    
    echo ""
    echo "步骤6: 启动HydroNet Pro..."
    start_hydronet
    
    echo ""
    show_status
    
    # 等待HydroNet启动
    sleep 5
    
    # 测试连接
    if curl -s http://localhost:5000 > /dev/null; then
        echo -e "${GREEN}✅ 所有服务已就绪！${NC}"
        echo ""
        echo "🌐 现在可以访问: http://localhost:5000"
    else
        echo -e "${YELLOW}⚠️  HydroNet Pro可能还在启动中...${NC}"
        echo "请稍等片刻后访问 http://localhost:5000"
    fi
}

# 运行主函数
main
