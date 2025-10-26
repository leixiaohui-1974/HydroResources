# 💻 HydroNet 本地版部署指南

## 🎯 适用场景

本地版适合以下场景：
- ✅ 个人学习和研究
- ✅ 团队内部使用
- ✅ 不想配置云服务器
- ✅ 数据保存在本地
- ✅ 快速测试和开发

---

## ⚡ 3步快速开始

### 第1步：获取阿里云API密钥

1. 访问：https://dashscope.console.aliyun.com/apiKey
2. 登录阿里云账号
3. 点击"创建API-KEY"
4. 复制密钥（格式：`sk-xxxxxxxxxxxxxxxx`）

💡 **免费额度**：qwen-turbo模型每天100万tokens免费

### 第2步：配置密钥

```bash
# 1. 复制配置文件
cp .env.example .env

# 2. 编辑配置文件
nano .env  # 或使用其他编辑器

# 3. 填写API密钥
ALIYUN_API_KEY=sk-你的密钥
```

### 第3步：启动应用

**Linux/Mac**:
```bash
./start_local.sh
```

**Windows**:
```cmd
start_local.bat
```

**或手动启动**:
```bash
# 安装依赖
pip install -r requirements_local.txt

# 启动应用
python3 app_local.py
```

🎉 **完成！** 访问 http://localhost:5000

---

## 📋 系统要求

### 最低要求
- Python 3.8+
- 500MB 磁盘空间
- 2GB 内存

### 推荐配置
- Python 3.10+
- 2GB 磁盘空间
- 4GB 内存

### 操作系统
- ✅ Windows 10/11
- ✅ macOS 10.15+
- ✅ Linux (Ubuntu 20.04+, CentOS 7+等)

---

## 🔧 详细安装步骤

### 1. 安装Python

**Windows**:
1. 访问 https://www.python.org/downloads/
2. 下载Python 3.10+安装包
3. 安装时勾选"Add Python to PATH"

**macOS**:
```bash
# 使用Homebrew
brew install python@3.10
```

**Linux**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3-pip python3-venv

# CentOS/RHEL
sudo yum install python3 python3-pip
```

### 2. 下载代码

```bash
# 方式1：Git克隆
git clone <your-repo-url>
cd hydronet

# 方式2：下载ZIP
# 解压后进入目录
```

### 3. 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 4. 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements_local.txt
```

### 5. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置（必需）
nano .env
```

**最少配置**：
```env
ALIYUN_API_KEY=sk-你的密钥
```

**完整配置**（可选）：
```env
# Flask配置
HOST=0.0.0.0
PORT=5000
DEBUG=True

# 阿里云API
ALIYUN_API_KEY=sk-你的密钥
QWEN_MODEL=qwen-turbo

# 其他配置使用默认值即可
```

### 6. 启动应用

```bash
python3 app_local.py
```

看到以下输出表示成功：
```
======================================================================
🌊 HydroNet 水网智能体系统 - 本地版
======================================================================
📦 版本: 本地单机版 (SQLite)
🤖 AI模型: 阿里云通义千问 (qwen-turbo)
💾 数据库: ./hydronet_local.db
🌐 访问地址: http://127.0.0.1:5000
======================================================================
```

---

## 🌐 访问应用

### Web界面

在浏览器访问：http://localhost:5000

**功能**：
- 💬 创建对话
- 🤖 与AI助手聊天
- 📝 查看历史记录
- 🔍 调用MCP服务
- 📊 查看统计信息

### API接口

本地版提供以下API：

```bash
# 健康检查
curl http://localhost:5000/api/health

# 系统信息
curl http://localhost:5000/api/system/info

# 创建对话
curl -X POST http://localhost:5000/api/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "测试对话"}'

# 发送消息
curl -X POST http://localhost:5000/api/conversations/<id>/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
```

---

## 💾 数据存储

### 数据库文件

- **位置**: `./hydronet_local.db`
- **类型**: SQLite
- **大小**: 根据使用量增长
- **备份**: 直接复制文件即可

### 备份数据

```bash
# 备份数据库
cp hydronet_local.db hydronet_local_backup_$(date +%Y%m%d).db

# 恢复数据
cp hydronet_local_backup_20250126.db hydronet_local.db
```

### 清空数据

```bash
# 删除数据库文件
rm hydronet_local.db

# 重新启动应用会自动创建新数据库
python3 app_local.py
```

---

## 🔧 常见问题

### Q1: 提示"ALIYUN_API_KEY未配置"

**解决**：
```bash
# 检查.env文件
cat .env | grep ALIYUN_API_KEY

# 确保格式正确
ALIYUN_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### Q2: 端口5000被占用

**解决**：
```bash
# 修改.env中的端口
PORT=8000

# 或停止占用端口的程序
# Linux/Mac:
lsof -i:5000
kill -9 <PID>

# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Q3: 无法访问http://localhost:5000

**检查**：
1. 应用是否启动成功
2. 防火墙是否阻止
3. 浏览器是否正确

**解决**：
```bash
# 尝试使用127.0.0.1
http://127.0.0.1:5000

# 或使用0.0.0.0允许外部访问
# 修改.env: HOST=0.0.0.0
```

### Q4: AI响应很慢

**原因**：
- 网络连接问题
- 模型选择不当

**优化**：
```env
# 使用更快的模型
QWEN_MODEL=qwen-turbo  # 最快

# 减少输出长度
QWEN_MAX_TOKENS=1000
```

### Q5: SQLite数据库文件过大

**解决**：
```bash
# 清理旧对话
# 删除30天前的对话
sqlite3 hydronet_local.db "DELETE FROM messages WHERE created_at < datetime('now', '-30 days')"
sqlite3 hydronet_local.db "DELETE FROM conversations WHERE id NOT IN (SELECT DISTINCT conversation_id FROM messages)"

# 压缩数据库
sqlite3 hydronet_local.db "VACUUM"
```

---

## 🚀 高级配置

### 修改监听地址

允许局域网访问：
```env
# .env文件
HOST=0.0.0.0  # 允许外部访问
PORT=5000
```

访问地址：`http://<你的IP>:5000`

### 使用不同的AI模型

```env
# qwen-turbo: 最快，免费
QWEN_MODEL=qwen-turbo

# qwen-plus: 平衡性能
QWEN_MODEL=qwen-plus

# qwen-max: 最强性能
QWEN_MODEL=qwen-max
```

### 配置MCP服务

编辑 `mcp_services/` 目录下的服务：
```bash
# 启动示例服务
python3 mcp_services/example_service.py
```

---

## 📊 性能优化

### 1. 使用本地缓存

对话历史缓存在内存中，重启会重新加载。

### 2. 定期清理数据

```bash
# 创建清理脚本
cat > cleanup.sh << 'EOF'
#!/bin/bash
sqlite3 hydronet_local.db << SQL
DELETE FROM messages WHERE created_at < datetime('now', '-90 days');
DELETE FROM conversations WHERE id NOT IN (SELECT DISTINCT conversation_id FROM messages);
VACUUM;
SQL
echo "数据清理完成"
EOF

chmod +x cleanup.sh
./cleanup.sh
```

### 3. 监控资源使用

```bash
# 查看进程
ps aux | grep app_local.py

# 查看数据库大小
ls -lh hydronet_local.db
```

---

## 🔒 安全建议

### 1. 保护API密钥

```bash
# 不要提交.env到Git
# .gitignore已包含.env

# 定期更换密钥
```

### 2. 局域网访问控制

```bash
# 仅本机访问
HOST=127.0.0.1

# 允许局域网但配置防火墙
HOST=0.0.0.0
# 然后在防火墙中限制IP
```

### 3. 数据备份

```bash
# 设置定时备份
crontab -e
# 添加：0 2 * * * cp /path/to/hydronet_local.db /path/to/backup/
```

---

## 🆚 本地版 vs 云端版对比

| 特性 | 本地版 | 云端版 |
|------|--------|--------|
| **部署** | 本机运行 | 阿里云服务器 |
| **数据库** | SQLite | PostgreSQL |
| **成本** | 免费（仅API） | 700+元/月 |
| **适用** | 个人/小团队 | 企业/SaaS |
| **用户管理** | ❌ | ✅ 多租户 |
| **权限控制** | ❌ | ✅ RBAC |
| **可扩展性** | 低 | 高 |
| **维护** | 简单 | 复杂 |
| **数据安全** | 本地存储 | 云端备份 |

---

## 📱 移动端访问

### 1. 局域网访问

```bash
# 1. 查看本机IP
# Linux/Mac:
ifconfig | grep inet

# Windows:
ipconfig

# 2. 设置允许外部访问
# .env: HOST=0.0.0.0

# 3. 手机浏览器访问
http://192.168.1.100:5000
```

### 2. 内网穿透（可选）

使用ngrok或花生壳实现外网访问：
```bash
# 使用ngrok
ngrok http 5000

# 获得临时域名
https://xxxx.ngrok.io
```

---

## 🎓 开发和调试

### 启用调试模式

```env
# .env文件
DEBUG=True
```

### 查看日志

应用日志会输出到控制台。

### 开发新功能

```bash
# 1. 修改代码
# 2. 重启应用
# 3. 测试功能
```

---

## 🔄 更新升级

### 更新代码

```bash
# Git拉取最新代码
git pull

# 更新依赖
pip install -r requirements_local.txt --upgrade

# 重启应用
```

### 迁移到云端版

如果需要升级到多租户SaaS版：
1. 导出SQLite数据
2. 部署云端版（参考SAAS_DEPLOYMENT_GUIDE.md）
3. 导入数据到PostgreSQL

---

## 💡 使用技巧

### 1. 快速测试

```bash
# 测试API
curl http://localhost:5000/api/health

# 查看统计
curl http://localhost:5000/api/stats
```

### 2. 批量导入对话

可以编写脚本批量导入历史对话。

### 3. 自定义提示词

在代码中修改系统提示词（qwen_client.py）。

---

## 📞 获取帮助

### 文档
- **本地版指南**: LOCAL_DEPLOYMENT_GUIDE.md (本文件)
- **系统说明**: HYDRONET_README.md
- **版本对比**: VERSION_COMPARISON.md

### 问题反馈
- GitHub Issues
- 邮件支持

---

## 🎉 开始使用

现在您可以：

1. ✅ 创建对话
2. ✅ 与AI助手交流
3. ✅ 查看历史记录
4. ✅ 使用MCP服务
5. ✅ 查看统计信息

**让每一滴水，都被智能而高效地调控！** 💧

---

**HydroNet本地版 - 简单、快速、免费！** 🚀
