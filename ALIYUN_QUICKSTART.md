# 🚀 阿里云 5分钟快速部署

最快速度部署HydroNet到阿里云！

---

## 📋 准备（2分钟）

### 1. 购买阿里云服务器

访问：https://swas.console.aliyun.com

**选择配置**：
- 镜像：Ubuntu 20.04
- 规格：2核2GB
- 价格：99元/年（新用户）

### 2. 获取API密钥

访问：https://dashscope.console.aliyun.com/apiKey

点击"创建API-KEY"并复制

---

## ⚡ 快速部署（3分钟）

### 方式1：一键脚本（最快）

```bash
# 1. 连接服务器（在阿里云控制台点击"远程连接"）

# 2. 下载部署脚本
wget https://你的地址/deploy_aliyun.sh
chmod +x deploy_aliyun.sh

# 3. 运行部署
sudo ./deploy_aliyun.sh

# 4. 按提示配置API密钥
# 在编辑器中填写：ALIYUN_API_KEY=sk-xxxxxxxxx

# 完成！
```

### 方式2：手动部署

```bash
# 1. 安装依赖
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx git

# 2. 下载代码
git clone <您的仓库> /opt/hydronet
cd /opt/hydronet

# 3. 安装Python依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. 配置
cp .env.example .env
nano .env  # 填写ALIYUN_API_KEY

# 5. 启动
gunicorn -w 4 -b 0.0.0.0:5000 app:app --daemon
```

---

## ✅ 验证部署

```bash
# 测试API
curl http://localhost:5000/api/health

# 应该返回：{"status":"healthy"}
```

---

## 🌐 配置访问

### 1. 开放端口

在阿里云控制台：
- 进入"安全组"
- 添加规则：端口80，0.0.0.0/0

### 2. 访问系统

```
http://您的服务器IP
```

---

## 🎉 完成！

现在可以：
- 📱 通过浏览器访问
- 🤖 与AI助手对话
- 🔧 开发MCP服务

**详细文档**：查看 `ALIYUN_DEPLOYMENT.md`

---

## 🐛 遇到问题？

### 无法访问
```bash
# 检查服务
sudo systemctl status hydronet

# 查看日志
sudo journalctl -u hydronet -f
```

### AI不响应
```bash
# 检查API密钥
cat /opt/hydronet/.env | grep ALIYUN_API_KEY

# 应该有正确的密钥，不是 "your-api-key"
```

### 更多帮助
查看完整文档：`ALIYUN_DEPLOYMENT.md`

---

**让每一滴水，都被智能而高效地调控！** 💧
