# 🏢 HydroNet 多租户SaaS部署完整指南

## 🎯 概述

本指南将帮助您部署**完整的多租户SaaS版本** HydroNet系统。

**新增功能**：
- ✅ 多租户数据隔离
- ✅ 用户认证和授权（JWT）
- ✅ RBAC权限控制
- ✅ 配额管理和限流
- ✅ 审计日志
- ✅ 管理后台API

---

## 📋 系统要求

### 必需服务
1. **PostgreSQL** 13+ （数据库）
2. **Redis** 6+ （缓存和限流）
3. **Python** 3.8+
4. **阿里云账号** （通义千问API）

### 推荐配置
- **CPU**: 4核
- **内存**: 8GB
- **硬盘**: 50GB SSD
- **带宽**: 10Mbps

---

## 🚀 快速部署（阿里云）

### 步骤1：购买和配置服务器

```bash
# 1. 购买ECS（推荐配置）
# - 地域：华东1（杭州）
# - 规格：ecs.c6.xlarge (4核8G)
# - 系统：Ubuntu 22.04 LTS
# - 价格：约300-400元/月

# 2. 购买RDS PostgreSQL
# - 规格：2核4GB
# - 存储：20GB
# - 价格：约200元/月

# 3. 购买Redis实例
# - 规格：1GB
# - 价格：约100元/月
```

### 步骤2：连接服务器并安装依赖

```bash
# SSH连接
ssh root@your-server-ip

# 更新系统
apt update && apt upgrade -y

# 安装Python和依赖
apt install -y python3.10 python3-pip python3-venv nginx git

# 安装PostgreSQL客户端
apt install -y postgresql-client

# 验证安装
python3 --version  # 应该 >= 3.8
```

### 步骤3：部署应用

```bash
# 创建部署目录
mkdir -p /opt/hydronet-saas
cd /opt/hydronet-saas

# 克隆或上传代码
# git clone <your-repo> .
# 或使用scp上传

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements_saas.txt
```

### 步骤4：配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置
nano .env
```

**必须配置**：
```env
# 基础配置
SECRET_KEY=<生成随机字符串>
JWT_SECRET_KEY=<另一个随机字符串>
DEBUG=False

# 阿里云API
ALIYUN_API_KEY=sk-xxxxxxxxxxxxxxxx

# 数据库（使用RDS地址）
DATABASE_URL=postgresql://hydronet:your_password@rm-xxxxxxx.pg.rds.aliyuncs.com:5432/hydronet

# Redis（使用Redis实例地址）
REDIS_URL=redis://:your_password@r-xxxxxxx.redis.rds.aliyuncs.com:6379/0

# 微信公众号（可选）
WECHAT_ENABLED=true
WECHAT_TOKEN=your-token
WECHAT_APP_ID=your-app-id
WECHAT_APP_SECRET=your-app-secret
```

**生成密钥**：
```bash
# 生成SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 生成JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 步骤5：初始化数据库

```bash
# 激活虚拟环境
source venv/bin/activate

# 初始化数据库
python3 init_database.py

# 应该看到：
# ✅ 系统管理员: admin@hydronet.com / HydroNet@2025
# ✅ 演示账号: demo@example.com / demo123
```

### 步骤6：测试运行

```bash
# 测试运行
python3 app_saas.py

# 访问测试
curl http://localhost:5000/api/health

# 应该返回：
# {"status":"healthy",...}

# 停止测试（Ctrl+C）
```

### 步骤7：配置Gunicorn

```bash
# 创建Gunicorn配置
cat > gunicorn_config.py << 'EOF'
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
accesslog = "/opt/hydronet-saas/logs/gunicorn_access.log"
errorlog = "/opt/hydronet-saas/logs/gunicorn_error.log"
loglevel = "info"
EOF

# 创建日志目录
mkdir -p logs
```

### 步骤8：配置Nginx

```bash
# 创建Nginx配置
cat > /etc/nginx/sites-available/hydronet-saas << 'EOF'
upstream hydronet {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    client_max_body_size 20M;
    
    # 访问日志
    access_log /var/log/nginx/hydronet_access.log;
    error_log /var/log/nginx/hydronet_error.log;
    
    # 静态文件
    location /static {
        alias /opt/hydronet-saas/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # API和应用
    location / {
        proxy_pass http://hydronet;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
EOF

# 启用配置
ln -s /etc/nginx/sites-available/hydronet-saas /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

### 步骤9：配置systemd服务

```bash
# 创建systemd服务
cat > /etc/systemd/system/hydronet-saas.service << 'EOF'
[Unit]
Description=HydroNet SaaS Multi-Tenant System
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=root
WorkingDirectory=/opt/hydronet-saas
Environment="PATH=/opt/hydronet-saas/venv/bin"
ExecStart=/opt/hydronet-saas/venv/bin/gunicorn -c gunicorn_config.py app_saas:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd
systemctl daemon-reload

# 启动服务
systemctl enable hydronet-saas
systemctl start hydronet-saas

# 查看状态
systemctl status hydronet-saas
```

### 步骤10：配置HTTPS

```bash
# 安装certbot
apt install -y certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d your-domain.com

# 自动续期
systemctl enable certbot.timer
```

### 步骤11：配置防火墙

```bash
# 开放端口
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw enable

# 或在阿里云控制台配置安全组
```

---

## 🧪 功能测试

### 1. 测试注册新租户

```bash
curl -X POST http://your-domain.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@company.com",
    "password": "Test@123",
    "tenant_name": "Test Company"
  }'

# 应该返回：
# {
#   "success": true,
#   "access_token": "eyJ...",
#   "user": {...},
#   "tenant": {...}
# }
```

### 2. 测试登录

```bash
curl -X POST http://your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@hydronet.com",
    "password": "HydroNet@2025"
  }'

# 保存返回的 access_token
TOKEN="eyJ..."
```

### 3. 测试创建对话

```bash
curl -X POST http://your-domain.com/api/chat/conversations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试对话"
  }'
```

### 4. 测试发送消息

```bash
curl -X POST http://your-domain.com/api/chat/conversations/<conversation_id>/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，帮我分析一下水网系统"
  }'
```

### 5. 测试管理后台

```bash
# 获取租户信息
curl -X GET http://your-domain.com/api/tenant/info \
  -H "Authorization: Bearer $TOKEN"

# 获取使用统计
curl -X GET http://your-domain.com/api/tenant/usage \
  -H "Authorization: Bearer $TOKEN"

# 获取审计日志
curl -X GET http://your-domain.com/api/admin/audit-logs \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📊 监控和运维

### 日志位置
```bash
# 应用日志
tail -f /opt/hydronet-saas/hydronet.log

# Gunicorn日志
tail -f /opt/hydronet-saas/logs/gunicorn_error.log

# Nginx日志
tail -f /var/log/nginx/hydronet_error.log

# Systemd日志
journalctl -u hydronet-saas -f
```

### 性能监控

```bash
# 安装监控工具
pip install flask-monitoring-dashboard

# 查看数据库连接
psql -h <rds-host> -U hydronet -d hydronet -c "SELECT count(*) FROM pg_stat_activity;"

# 查看Redis状态
redis-cli -h <redis-host> -a <password> INFO
```

### 备份数据

```bash
# 创建备份脚本
cat > /opt/backup/backup_hydronet.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backup/hydronet"

mkdir -p $BACKUP_DIR

# 备份数据库
pg_dump -h <rds-host> -U hydronet -d hydronet > $BACKUP_DIR/db_$DATE.sql

# 压缩
gzip $BACKUP_DIR/db_$DATE.sql

# 保留最近30天
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: db_$DATE.sql.gz"
EOF

chmod +x /opt/backup/backup_hydronet.sh

# 添加定时任务
crontab -e
# 添加: 0 2 * * * /opt/backup/backup_hydronet.sh
```

---

## 🔒 安全加固

### 1. 修改默认密码
```bash
# 登录后立即修改
curl -X PUT http://your-domain.com/api/auth/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "HydroNet@2025",
    "new_password": "YourStrongPassword@2025"
  }'
```

### 2. 配置防火墙规则
```bash
# 限制SSH访问
ufw limit 22/tcp

# 限制数据库访问（仅允许应用服务器）
# 在RDS安全组中配置白名单
```

### 3. 启用审计日志
已默认启用，所有敏感操作都会记录。

### 4. 定期更新
```bash
# 更新系统
apt update && apt upgrade -y

# 更新Python包
source /opt/hydronet-saas/venv/bin/activate
pip install --upgrade -r requirements_saas.txt
```

---

## 💰 成本估算

### 阿里云资源（月度）

| 资源 | 规格 | 价格 |
|------|------|------|
| ECS服务器 | 4核8G | 300-400元 |
| RDS PostgreSQL | 2核4G | 200元 |
| Redis | 1GB | 100元 |
| 带宽 | 10Mbps | 100元 |
| 对象存储OSS | 50GB | 10元 |
| **总计** | - | **约710-810元/月** |

### 通义千问API
- qwen-turbo: 免费（每天100万tokens）
- 足够中小型SaaS使用

### 节省成本建议
1. 使用包年付费（约7.5折）
2. 使用预留实例（约6折）
3. 合理规划资源规格

---

## 📈 扩展和优化

### 水平扩展

```bash
# 增加应用服务器
# 1. 部署多个应用实例
# 2. 使用SLB负载均衡

# Nginx配置负载均衡
upstream hydronet {
    server 10.0.0.1:5000;
    server 10.0.0.2:5000;
    server 10.0.0.3:5000;
    least_conn;  # 最少连接
}
```

### 数据库优化

```sql
-- 创建索引
CREATE INDEX idx_conversations_tenant_user ON conversations(tenant_id, user_id);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- 分区表（大数据量）
-- 按租户分区
```

### Redis缓存

```python
# 缓存热点数据
# - 租户信息
# - 用户权限
# - 配额使用量
```

---

## 🆘 故障排查

### 问题1: 数据库连接失败
```bash
# 检查RDS连接
psql -h <rds-host> -U hydronet -d hydronet

# 检查安全组
# 在阿里云控制台确认白名单配置
```

### 问题2: Redis连接失败
```bash
# 测试连接
redis-cli -h <redis-host> -a <password> ping

# 应该返回：PONG
```

### 问题3: 服务无法启动
```bash
# 查看详细日志
journalctl -u hydronet-saas -n 100 --no-pager

# 检查端口占用
netstat -tlnp | grep 5000
```

### 问题4: API响应慢
```bash
# 检查数据库慢查询
# 查看Redis命中率
# 增加Gunicorn worker数量
```

---

## 🎉 部署完成检查清单

- [ ] ✅ ECS服务器已购买并配置
- [ ] ✅ RDS PostgreSQL已创建
- [ ] ✅ Redis实例已创建
- [ ] ✅ 代码已部署
- [ ] ✅ 环境变量已配置
- [ ] ✅ 数据库已初始化
- [ ] ✅ Gunicorn已配置
- [ ] ✅ Nginx已配置
- [ ] ✅ Systemd服务已启动
- [ ] ✅ HTTPS证书已配置
- [ ] ✅ 防火墙已配置
- [ ] ✅ 监控已设置
- [ ] ✅ 备份已配置
- [ ] ✅ 默认密码已修改
- [ ] ✅ 功能测试通过

---

## 📞 技术支持

- 文档：查看项目文档
- 问题：提交GitHub Issue
- 团队：河北工程大学·智慧水网创新团队

---

**恭喜！您的多租户SaaS系统已成功部署！** 🎉

现在可以：
1. 注册租户账号
2. 创建用户
3. 开始使用AI对话
4. 配置MCP服务
5. 查看使用统计

**让每一滴水，都被智能而高效地调控！** 💧
