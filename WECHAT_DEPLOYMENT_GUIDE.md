# 📱 微信公众号部署完整指南

## 🎯 核心概念理解

### ❌ 常见误解
"把程序部署在微信公众号平台上"

### ✅ 正确理解
```
┌─────────────────────────────────────────────────────────────┐
│                      正确的架构                              │
└─────────────────────────────────────────────────────────────┘

    用户微信客户端
         ↓ ↑
    [1] 发送消息 / 接收回复
         ↓ ↑
    微信公众号平台
    (腾讯服务器)
         ↓ ↑
    [2] 消息转发 / 响应转发
         ↓ ↑
    您的服务器
    (运行HydroNet程序)
         ↓ ↑
    [3] 调用AI模型 / MCP服务
         ↓ ↑
    腾讯云元宝 / MCP服务
```

**关键点**：
1. **微信公众号** = 消息中转站（腾讯提供）
2. **您的服务器** = 程序实际运行的地方（需要自己准备）
3. **HydroNet程序** = 部署在您的服务器上

---

## 🏗️ 完整部署方案

### 方案1：云服务器部署 ⭐ 推荐

#### 适用场景
- 需要微信公众号接入
- 需要稳定运行
- 有一定技术能力

#### 服务器选择
任选一家云服务商：

| 服务商 | 最低配置 | 价格参考 | 备注 |
|--------|---------|---------|------|
| 阿里云ECS | 1核2G | ~100元/月 | 学生优惠更便宜 |
| 腾讯云CVM | 1核2G | ~100元/月 | 新用户有优惠 |
| 华为云ECS | 1核2G | ~100元/月 | 企业用户优惠 |
| AWS/Azure | 1核2G | ~150元/月 | 国际化需求 |

**推荐配置**：
- CPU: 2核
- 内存: 4GB
- 硬盘: 40GB
- 带宽: 5Mbps
- 系统: Ubuntu 20.04 / CentOS 7+

#### 部署步骤

**第1步：购买服务器**
```bash
# 选择云服务商，购买服务器
# 获得：
# - 公网IP地址（例如：123.456.789.123）
# - SSH登录权限
```

**第2步：连接服务器**
```bash
# 使用SSH连接
ssh root@123.456.789.123

# 或使用云服务商的Web控制台
```

**第3步：安装环境**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# 或
sudo yum update -y  # CentOS

# 安装Python 3.8+
sudo apt install python3.8 python3-pip python3-venv -y

# 安装Git
sudo apt install git -y

# 安装Nginx（用于反向代理）
sudo apt install nginx -y
```

**第4步：上传代码**
```bash
# 方法1：使用Git（推荐）
cd /opt
sudo git clone <您的代码仓库地址>
cd HydroNet

# 方法2：使用SCP上传
# 在本地执行：
scp -r /workspace/* root@123.456.789.123:/opt/HydroNet/
```

**第5步：配置环境**
```bash
cd /opt/HydroNet

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
nano .env  # 填写配置
```

**第6步：配置Nginx反向代理**
```bash
sudo nano /etc/nginx/sites-available/hydronet
```

写入以下配置：
```nginx
server {
    listen 80;
    server_name your-domain.com;  # 改成您的域名或IP

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
sudo nginx -t
sudo systemctl reload nginx
```

**第7步：配置systemd服务**
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
WorkingDirectory=/opt/HydroNet
Environment="PATH=/opt/HydroNet/venv/bin"
ExecStart=/opt/HydroNet/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable hydronet
sudo systemctl start hydronet
sudo systemctl status hydronet  # 查看状态
```

**第8步：配置HTTPS（重要！）**
```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取免费SSL证书
sudo certbot --nginx -d your-domain.com

# 证书会自动续期
```

**第9步：开放防火墙端口**
```bash
# Ubuntu UFW
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 或在云服务商控制台配置安全组
# 开放端口：80, 443
```

**第10步：验证部署**
```bash
# 测试应用
curl http://your-domain.com/api/health

# 应该返回：
# {"status":"healthy",...}
```

---

### 方案2：内网穿透 🏠 适合开发测试

#### 适用场景
- 没有云服务器
- 仅用于开发测试
- 不推荐用于生产环境

#### 使用工具
- **ngrok** (国外)
- **花生壳** (国内)
- **frp** (开源)
- **natapp** (国内)

#### 示例：使用ngrok

**第1步：安装ngrok**
```bash
# 访问 https://ngrok.com
# 注册并下载ngrok

# 或使用命令安装
wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip
unzip ngrok-stable-linux-amd64.zip
sudo mv ngrok /usr/local/bin/
```

**第2步：启动HydroNet**
```bash
cd /workspace
python app.py
# 应用运行在 http://localhost:5000
```

**第3步：启动ngrok**
```bash
ngrok http 5000

# 会显示：
# Forwarding  https://xxxx-xx-xx-xxx.ngrok.io -> http://localhost:5000
```

**第4步：使用临时域名**
```
临时公网地址：https://xxxx-xx-xx-xxx.ngrok.io
用这个地址配置微信公众号
```

⚠️ **限制**：
- 免费版域名会变化
- 有流量和速度限制
- 不稳定，不适合生产环境

---

### 方案3：Serverless部署 ☁️ 弹性扩展

#### 适用平台
- 腾讯云Serverless
- 阿里云函数计算
- AWS Lambda

#### 优点
- 按需付费，成本低
- 自动扩展
- 免运维

#### 缺点
- 冷启动延迟
- 需要改造代码
- 状态管理复杂

（需要单独教程，这里不展开）

---

## 🔧 微信公众号配置

### 前提条件
1. ✅ 已有微信公众号（订阅号或服务号）
2. ✅ 服务器已部署并可通过HTTPS访问
3. ✅ 已获得公网域名（必须HTTPS）

### 配置步骤

**第1步：登录微信公众平台**
```
访问：https://mp.weixin.qq.com
使用管理员微信扫码登录
```

**第2步：获取开发信息**
```
导航：设置与开发 -> 基本配置

记录：
- AppID: wxxxxxxxxxxxxxxxxxxx
- AppSecret: [点击重置后获取]
```

**第3步：配置服务器**
```
设置与开发 -> 基本配置 -> 服务器配置

填写：
┌─────────────────────────────────────────────┐
│ 服务器地址(URL)                             │
│ https://your-domain.com/wechat              │
├─────────────────────────────────────────────┤
│ Token (自定义，例如)                        │
│ hydronet_token_2025                         │
├─────────────────────────────────────────────┤
│ EncodingAESKey                              │
│ [点击随机生成]                              │
├─────────────────────────────────────────────┤
│ 消息加解密方式                              │
│ ○ 明文模式                                  │
│ ● 兼容模式 (推荐)                           │
│ ○ 安全模式                                  │
└─────────────────────────────────────────────┘
```

**第4步：更新.env配置**
```env
# 在服务器上编辑 /opt/HydroNet/.env
WECHAT_TOKEN=hydronet_token_2025
WECHAT_APP_ID=wxxxxxxxxxxxxxxxxxxx
WECHAT_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**第5步：重启应用**
```bash
sudo systemctl restart hydronet
```

**第6步：提交验证**
```
在微信公众平台点击"提交"按钮
等待验证通过（绿色√）
```

**第7步：启用服务器配置**
```
验证通过后，点击"启用"
```

**第8步：测试**
```
1. 用手机关注您的公众号
2. 发送消息："你好"
3. 应该收到AI助手的回复
```

---

## 📊 完整部署检查清单

### 服务器部署
- [ ] ✅ 购买云服务器
- [ ] ✅ 安装Python 3.8+
- [ ] ✅ 上传代码到服务器
- [ ] ✅ 安装依赖包
- [ ] ✅ 配置环境变量（.env）
- [ ] ✅ 配置Nginx反向代理
- [ ] ✅ 配置systemd服务
- [ ] ✅ 获取SSL证书（HTTPS）
- [ ] ✅ 开放防火墙端口
- [ ] ✅ 验证应用运行

### 微信公众号配置
- [ ] ✅ 登录微信公众平台
- [ ] ✅ 获取AppID和AppSecret
- [ ] ✅ 配置服务器地址
- [ ] ✅ 设置Token
- [ ] ✅ 验证服务器
- [ ] ✅ 启用服务器配置
- [ ] ✅ 测试消息收发

### 功能测试
- [ ] ✅ Web界面访问正常
- [ ] ✅ API接口调用正常
- [ ] ✅ 微信消息响应正常
- [ ] ✅ AI对话功能正常
- [ ] ✅ MCP服务调用正常
- [ ] ✅ 日志记录正常

---

## 💰 成本估算

### 云服务器方案（推荐）

| 项目 | 费用 | 说明 |
|------|------|------|
| 云服务器 | ~100元/月 | 1核2G基础配置 |
| 域名 | ~50元/年 | .com域名 |
| SSL证书 | 免费 | Let's Encrypt |
| 带宽 | 包含 | 5Mbps通常够用 |
| **总计** | **~120元/月** | 约1500元/年 |

### 腾讯云AI调用（按需）

| 项目 | 免费额度 | 超出后价格 |
|------|---------|-----------|
| 混元大模型 | 通常有试用 | ~0.01-0.05元/千tokens |
| 每月对话100次 | - | ~1-5元 |
| 每月对话1000次 | - | ~10-50元 |

### 成本优化建议
1. 使用学生优惠（阿里云/腾讯云）
2. 选择年付（通常有折扣）
3. 使用轻量应用服务器（更便宜）
4. 合理设置AI模型参数（降低token消耗）

---

## 🚨 常见问题与解决

### Q1: 微信验证一直失败
**可能原因**：
1. 服务器URL不可访问
2. Token配置不一致
3. 未使用HTTPS
4. 防火墙阻止

**解决方法**：
```bash
# 1. 检查应用是否运行
sudo systemctl status hydronet

# 2. 检查Nginx配置
sudo nginx -t
curl http://localhost:5000/api/health

# 3. 检查防火墙
sudo ufw status

# 4. 查看日志
sudo journalctl -u hydronet -f
tail -f /opt/HydroNet/hydronet.log
```

### Q2: 微信验证通过，但消息没响应
**检查步骤**：
```bash
# 1. 查看实时日志
sudo journalctl -u hydronet -f

# 2. 检查Token是否一致
cat /opt/HydroNet/.env | grep WECHAT_TOKEN

# 3. 手动测试接口
curl https://your-domain.com/wechat

# 4. 检查腾讯云密钥配置
cat /opt/HydroNet/.env | grep TENCENT
```

### Q3: AI响应很慢或超时
**优化方法**：
```env
# 调整.env配置
HUNYUAN_MODEL=hunyuan-lite  # 使用更快的模型
HUNYUAN_MAX_TOKENS=1000     # 减少最大输出
HUNYUAN_TEMPERATURE=0.5     # 降低随机性
```

### Q4: 服务器资源不足
**监控命令**：
```bash
# 查看CPU和内存
top
htop

# 查看磁盘
df -h

# 查看进程
ps aux | grep gunicorn
```

**优化方案**：
```bash
# 减少gunicorn工作进程
# 编辑 /etc/systemd/system/hydronet.service
# 将 -w 4 改为 -w 2
ExecStart=/opt/HydroNet/venv/bin/gunicorn -w 2 -b 127.0.0.1:5000 app:app

# 重启服务
sudo systemctl daemon-reload
sudo systemctl restart hydronet
```

### Q5: HTTPS证书过期
```bash
# certbot会自动续期，但如果失败：
sudo certbot renew
sudo systemctl reload nginx
```

---

## 🎯 推荐部署方案总结

### 🏆 最佳方案：云服务器 + 域名 + HTTPS

**适用于**：
- ✅ 正式使用微信公众号
- ✅ 需要稳定可靠
- ✅ 长期运行

**步骤**：
1. 购买云服务器（阿里云/腾讯云）
2. 注册域名并备案
3. 按本文档完整部署
4. 配置微信公众号
5. 开始使用

**成本**：~1500元/年

---

### 🧪 开发测试：本地 + ngrok

**适用于**：
- ✅ 快速测试
- ✅ 开发调试
- ❌ 不适合生产

**步骤**：
1. 本地运行HydroNet
2. 使用ngrok创建临时域名
3. 配置微信公众号（测试号）
4. 开发完成后切换到云服务器

**成本**：免费（或ngrok付费版~$5/月）

---

## 📞 需要帮助？

如果部署过程中遇到问题：

1. 查看日志文件
2. 检查配置是否正确
3. 参考本文档的"常见问题"部分
4. 联系技术支持

---

## 🎉 部署成功后

恭喜！您的HydroNet系统现在已经：
- ✅ 部署在云服务器上
- ✅ 可通过微信公众号访问
- ✅ 可通过Web界面访问
- ✅ 已接入腾讯元宝AI
- ✅ 可扩展MCP服务

**下一步**：
1. 开发实际的MCP服务
2. 优化AI提示词
3. 添加更多功能
4. 推广您的公众号

**让每一滴水，都被智能而高效地调控！** 💧

---

更新日期：2025-10-26
版本：1.0.0
