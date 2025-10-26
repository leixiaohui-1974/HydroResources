# ☁️ HydroNet 阿里云部署完整指南

## 🎯 概述

本指南将帮助您在阿里云上部署HydroNet水网智能体系统。
完成后，您将拥有一个完整可用的Web应用，集成阿里云通义千问大模型。

---

## 📋 准备工作

### 1. 注册阿里云账号
访问：https://www.aliyun.com
- 新用户有优惠券
- 学生认证可享9.5元/月优惠

### 2. 实名认证
在阿里云控制台完成实名认证（必需）

### 3. 准备预算
- 服务器：~99元/年（新用户首年）
- 或学生价：9.5元/月
- AI调用：免费（每天100万tokens）

---

## 🖥️ 方案一：一键自动部署 ⭐推荐

### 适用场景
- 已有阿里云服务器
- 希望快速部署
- 熟悉Linux命令

### 部署步骤

#### 1. 购买服务器

登录阿里云控制台：https://ecs.console.aliyun.com

**推荐配置**：
```
产品：轻量应用服务器（性价比高）
地域：华东1（杭州）或离您最近的地域
镜像：Ubuntu 20.04 LTS
规格：2核2GB
带宽：3Mbps
价格：99元/年（新用户）或 9.5元/月（学生）
```

**购买地址**：
- 轻量服务器：https://swas.console.aliyun.com
- 云服务器ECS：https://ecs-buy.aliyun.com

#### 2. 连接服务器

```bash
# 方式1：使用阿里云控制台的Web终端（最简单）
# 在服务器列表中点击"远程连接"

# 方式2：使用SSH客户端
ssh root@您的服务器IP
# 首次登录需要输入密码（购买时设置）
```

#### 3. 上传代码

```bash
# 方式1：使用Git（推荐）
cd /opt
git clone <您的代码仓库地址>
cd HydroNet

# 方式2：使用SCP上传
# 在本地执行：
scp -r /workspace/* root@您的服务器IP:/opt/HydroNet/
```

#### 4. 运行一键部署脚本

```bash
cd /opt/HydroNet
chmod +x deploy_aliyun.sh
sudo ./deploy_aliyun.sh
```

脚本会自动完成：
- ✅ 系统更新
- ✅ 安装Python和依赖
- ✅ 安装Nginx
- ✅ 创建虚拟环境
- ✅ 安装项目依赖
- ✅ 配置Nginx反向代理
- ✅ 配置systemd服务
- ✅ 启动应用

#### 5. 配置环境变量

脚本会提示您编辑`.env`文件：

```bash
nano /opt/HydroNet/.env
```

**必需配置**：
```env
# 阿里云API密钥（必需）
ALIYUN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# 其他配置使用默认值即可
QWEN_MODEL=qwen-turbo
SECRET_KEY=your-random-secret-key
```

**获取API密钥**：
1. 访问：https://dashscope.console.aliyun.com/apiKey
2. 登录后点击"创建API Key"
3. 复制密钥并粘贴到`.env`文件

#### 6. 重启服务

```bash
sudo systemctl restart hydronet
sudo systemctl status hydronet
```

#### 7. 测试访问

```bash
# 测试健康检查
curl http://localhost:5000/api/health

# 应该返回：
# {"status":"healthy",...}
```

#### 8. 配置安全组（重要！）

在阿里云控制台：
1. 进入服务器管理页面
2. 点击"安全组"
3. 添加规则：
   - 端口范围：80/80
   - 授权对象：0.0.0.0/0
   - 协议：TCP

#### 9. 访问应用

在浏览器打开：
```
http://您的服务器IP
```

🎉 **部署完成！**

---

## 🏗️ 方案二：手动部署

### 适用场景
- 需要自定义配置
- 学习部署过程
- 已有特殊需求

### 详细步骤

#### 1. 系统准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y git curl wget vim
```

#### 2. 安装Python 3.8+

```bash
# 安装Python
sudo apt install -y python3 python3-pip python3-venv

# 验证版本
python3 --version  # 应该 >= 3.8
```

#### 3. 安装Nginx

```bash
sudo apt install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

#### 4. 部署应用

```bash
# 创建目录
sudo mkdir -p /opt/hydronet
cd /opt/hydronet

# 上传代码（使用Git或SCP）
# git clone <仓库地址> .

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
nano .env  # 填写配置
```

#### 5. 配置Nginx

```bash
sudo nano /etc/nginx/sites-available/hydronet
```

写入配置：
```nginx
server {
    listen 80;
    server_name your-domain.com;  # 改为您的域名或IP

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/hydronet /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

#### 6. 配置systemd服务

```bash
sudo nano /etc/systemd/system/hydronet.service
```

写入：
```ini
[Unit]
Description=HydroNet Water Network Intelligence System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/hydronet
Environment="PATH=/opt/hydronet/venv/bin"
ExecStart=/opt/hydronet/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable hydronet
sudo systemctl start hydronet
sudo systemctl status hydronet
```

---

## 🔒 配置HTTPS（推荐）

### 前提条件
- 已有域名并解析到服务器IP
- 端口80和443已开放

### 使用Let's Encrypt免费证书

```bash
# 安装certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书并自动配置Nginx
sudo certbot --nginx -d your-domain.com

# 测试自动续期
sudo certbot renew --dry-run
```

证书将自动每90天续期。

---

## 🔧 日常管理

### 服务管理命令

```bash
# 查看状态
sudo systemctl status hydronet

# 启动服务
sudo systemctl start hydronet

# 停止服务
sudo systemctl stop hydronet

# 重启服务
sudo systemctl restart hydronet

# 查看日志
sudo journalctl -u hydronet -f

# 查看应用日志
tail -f /opt/hydronet/hydronet.log
```

### 更新应用

```bash
cd /opt/hydronet

# 停止服务
sudo systemctl stop hydronet

# 拉取最新代码
git pull

# 更新依赖（如有变化）
source venv/bin/activate
pip install -r requirements.txt

# 重启服务
sudo systemctl start hydronet
```

### 修改配置

```bash
# 编辑环境变量
nano /opt/hydronet/.env

# 重启服务使配置生效
sudo systemctl restart hydronet
```

---

## 📊 监控与优化

### 查看资源使用

```bash
# CPU和内存
top
htop  # 需要安装: sudo apt install htop

# 磁盘使用
df -h

# 网络流量
iftop  # 需要安装: sudo apt install iftop
```

### 性能优化

#### 1. 调整Gunicorn工作进程

```bash
# 编辑服务文件
sudo nano /etc/systemd/system/hydronet.service

# 修改 ExecStart 行，调整 -w 参数
# 推荐设置为：CPU核心数 * 2 + 1
# 例如2核CPU：-w 5
ExecStart=/opt/hydronet/venv/bin/gunicorn -w 5 -b 127.0.0.1:5000 app:app

# 重载配置
sudo systemctl daemon-reload
sudo systemctl restart hydronet
```

#### 2. 配置Nginx缓存

```nginx
# 在 /etc/nginx/sites-available/hydronet 中添加
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g inactive=60m;

server {
    # ... 其他配置 ...
    
    location /static {
        proxy_cache my_cache;
        proxy_cache_valid 200 60m;
        # ... proxy_pass配置 ...
    }
}
```

### 设置监控告警（阿里云云监控）

1. 登录阿里云控制台
2. 搜索"云监控"
3. 添加监控项：
   - CPU使用率 > 80%
   - 内存使用率 > 80%
   - 磁盘使用率 > 85%
4. 配置告警通知（短信/邮件）

---

## 🐛 故障排查

### 问题1：服务无法启动

```bash
# 查看详细日志
sudo journalctl -u hydronet -n 50 --no-pager

# 常见原因：
# 1. 端口被占用
sudo lsof -i:5000

# 2. 配置文件错误
cat /opt/hydronet/.env

# 3. 依赖未安装
source /opt/hydronet/venv/bin/activate
pip list
```

### 问题2：无法访问网站

```bash
# 检查Nginx状态
sudo systemctl status nginx

# 检查Nginx配置
sudo nginx -t

# 检查安全组
# 在阿里云控制台确认80端口已开放

# 检查防火墙（如果使用）
sudo ufw status
```

### 问题3：AI响应错误

```bash
# 检查API密钥
cat /opt/hydronet/.env | grep ALIYUN_API_KEY

# 测试API
curl -X POST https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation \
  -H "Authorization: Bearer 您的API密钥" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-turbo","input":{"messages":[{"role":"user","content":"你好"}]}}'
```

### 问题4：磁盘空间不足

```bash
# 查看磁盘使用
df -h

# 清理日志
sudo journalctl --vacuum-time=7d

# 清理包缓存
sudo apt clean
```

---

## 💰 成本优化

### 1. 选择合适的服务器规格

| 应用规模 | 推荐配置 | 月访问量 | 成本 |
|---------|---------|---------|------|
| 个人/测试 | 1核2G | <1万 | ~10元/月 |
| 小型团队 | 2核4G | <10万 | ~50元/月 |
| 中型企业 | 4核8G | <100万 | ~200元/月 |

### 2. 使用轻量应用服务器

相比ECS更便宜，适合轻量级应用。

### 3. 按量付费vs包年包月

- 测试/开发：按量付费
- 生产环境：包年包月（更便宜）

### 4. 使用学生优惠

如果是学生，认证后可享9.5元/月优惠。

---

## 🎓 最佳实践

### 1. 定期备份

```bash
# 备份配置和数据
tar -czf hydronet-backup-$(date +%Y%m%d).tar.gz \
    /opt/hydronet/.env \
    /opt/hydronet/*.db \
    /opt/hydronet/logs/

# 上传到阿里云OSS（可选）
```

### 2. 使用Git管理代码

```bash
cd /opt/hydronet
git init
git remote add origin <您的仓库地址>
git push -u origin main
```

### 3. 配置日志轮转

```bash
sudo nano /etc/logrotate.d/hydronet
```

写入：
```
/opt/hydronet/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

### 4. 设置定时任务

```bash
# 编辑crontab
crontab -e

# 添加定时重启（可选）
0 3 * * * systemctl restart hydronet

# 添加定时备份
0 2 * * * /path/to/backup_script.sh
```

---

## 📞 获取帮助

### 阿里云官方资源
- 官方文档：https://help.aliyun.com
- 工单系统：https://selfservice.console.aliyun.com
- 社区论坛：https://developer.aliyun.com/ask

### HydroNet项目
- 项目文档：查看 `HYDRONET_README.md`
- 快速开始：查看 `QUICKSTART.md`
- MCP开发：查看 `mcp_services/README.md`

---

## ✅ 部署检查清单

在完成部署后，请确认：

- [ ] ✅ 服务器已购买并可访问
- [ ] ✅ 系统已更新
- [ ] ✅ Python 3.8+已安装
- [ ] ✅ Nginx已安装并运行
- [ ] ✅ 代码已上传到服务器
- [ ] ✅ 虚拟环境已创建
- [ ] ✅ 依赖包已安装
- [ ] ✅ .env配置已填写
- [ ] ✅ Nginx配置已完成
- [ ] ✅ systemd服务已配置
- [ ] ✅ 服务已启动并运行
- [ ] ✅ 安全组已配置（80端口）
- [ ] ✅ 可通过浏览器访问
- [ ] ✅ AI对话功能正常
- [ ] ✅ （可选）HTTPS已配置

---

## 🎉 部署完成

恭喜！您的HydroNet系统已成功部署在阿里云上。

**现在您可以**：
1. 通过浏览器访问系统
2. 与AI助手对话
3. 开发自己的MCP服务
4. 邀请团队成员使用

**让每一滴水，都被智能而高效地调控！** 💧

---

更新日期：2025-10-26
版本：2.0.0 (阿里云版)
