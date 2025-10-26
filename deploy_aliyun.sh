#!/bin/bash
# ================================================
# HydroNet 阿里云一键部署脚本
# ================================================

set -e  # 遇到错误立即退出

echo "================================================"
echo "🌊 HydroNet 阿里云一键部署脚本"
echo "================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}提示: 建议使用sudo运行此脚本${NC}"
    echo "sudo $0"
    echo ""
fi

# 步骤1: 系统更新
echo -e "${GREEN}[1/8] 更新系统软件包...${NC}"
sudo apt update && sudo apt upgrade -y

# 步骤2: 安装Python和依赖
echo -e "${GREEN}[2/8] 安装Python 3.8+...${NC}"
sudo apt install -y python3 python3-pip python3-venv python3-dev

# 安装系统依赖
sudo apt install -y build-essential libssl-dev libffi-dev

# 步骤3: 安装Nginx
echo -e "${GREEN}[3/8] 安装Nginx...${NC}"
sudo apt install -y nginx

# 步骤4: 创建部署目录
echo -e "${GREEN}[4/8] 创建部署目录...${NC}"
DEPLOY_DIR="/opt/hydronet"
sudo mkdir -p $DEPLOY_DIR

# 如果当前目录是git仓库，复制文件
if [ -d ".git" ]; then
    echo "检测到Git仓库，复制文件..."
    sudo cp -r * $DEPLOY_DIR/
else
    echo "请将HydroNet代码放到 $DEPLOY_DIR 目录"
fi

cd $DEPLOY_DIR

# 步骤5: 创建虚拟环境并安装依赖
echo -e "${GREEN}[5/8] 创建Python虚拟环境...${NC}"
sudo python3 -m venv venv
source venv/bin/activate

echo "安装Python依赖包..."
pip install --upgrade pip
pip install -r requirements.txt

# 步骤6: 配置环境变量
echo -e "${GREEN}[6/8] 配置环境变量...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo -e "${YELLOW}⚠️  请编辑 $DEPLOY_DIR/.env 文件并填写您的配置${NC}"
    echo ""
    echo "必需配置项："
    echo "  ALIYUN_API_KEY=你的阿里云API密钥"
    echo ""
    echo "获取地址: https://dashscope.console.aliyun.com/apiKey"
    echo ""
    read -p "按Enter继续配置环境变量..." 
    nano $DEPLOY_DIR/.env
fi

# 步骤7: 配置Nginx
echo -e "${GREEN}[7/8] 配置Nginx反向代理...${NC}"

# 获取服务器IP或域名
read -p "请输入您的域名或服务器IP (例: example.com 或 123.456.789.123): " DOMAIN

cat > /tmp/hydronet_nginx << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

sudo mv /tmp/hydronet_nginx /etc/nginx/sites-available/hydronet
sudo ln -sf /etc/nginx/sites-available/hydronet /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 测试Nginx配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

echo -e "${GREEN}Nginx配置完成！${NC}"

# 步骤8: 配置systemd服务
echo -e "${GREEN}[8/8] 配置系统服务...${NC}"

cat > /tmp/hydronet.service << EOF
[Unit]
Description=HydroNet Water Network Intelligence System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$DEPLOY_DIR
Environment="PATH=$DEPLOY_DIR/venv/bin"
ExecStart=$DEPLOY_DIR/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app --timeout 120
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/hydronet.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hydronet
sudo systemctl start hydronet

# 检查服务状态
sleep 2
if sudo systemctl is-active --quiet hydronet; then
    echo -e "${GREEN}✅ 服务启动成功！${NC}"
else
    echo -e "${RED}❌ 服务启动失败，查看日志：${NC}"
    sudo journalctl -u hydronet -n 50
    exit 1
fi

# 配置防火墙（如果使用ufw）
if command -v ufw &> /dev/null; then
    echo "配置防火墙..."
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    echo -e "${GREEN}防火墙配置完成${NC}"
fi

echo ""
echo "================================================"
echo -e "${GREEN}🎉 部署完成！${NC}"
echo "================================================"
echo ""
echo "📋 部署信息："
echo "  - 部署目录: $DEPLOY_DIR"
echo "  - 配置文件: $DEPLOY_DIR/.env"
echo "  - 日志文件: $DEPLOY_DIR/hydronet.log"
echo ""
echo "🌐 访问地址："
echo "  - HTTP: http://$DOMAIN"
echo "  - 健康检查: http://$DOMAIN/api/health"
echo ""
echo "🔧 管理命令："
echo "  - 查看状态: sudo systemctl status hydronet"
echo "  - 重启服务: sudo systemctl restart hydronet"
echo "  - 查看日志: sudo journalctl -u hydronet -f"
echo "  - 编辑配置: nano $DEPLOY_DIR/.env"
echo ""
echo "📚 下一步："
echo "  1. 测试访问: curl http://$DOMAIN/api/health"
echo "  2. 配置HTTPS (推荐): sudo certbot --nginx -d $DOMAIN"
echo "  3. 开发MCP服务"
echo ""
echo "================================================"
echo "让每一滴水，都被智能而高效地调控！💧"
echo "================================================"
