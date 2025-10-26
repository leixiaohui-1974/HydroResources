# HydroNet 水网智能体系统 - 微信公众号Web应用

<div align="center">

## 💧 让每一滴水，都被智能而高效地调控

基于腾讯元宝大模型和MCP服务的水网智能管理系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📋 目录

- [系统简介](#系统简介)
- [主要功能](#主要功能)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [MCP服务接入](#mcp服务接入)
- [微信公众号配置](#微信公众号配置)
- [API接口文档](#api接口文档)
- [部署指南](#部署指南)
- [常见问题](#常见问题)

---

## 🌟 系统简介

HydroNet是一个集成了大语言模型和专业水网服务的智能管理系统，通过微信公众号和Web界面提供：

- 🤖 **智能对话**：基于腾讯元宝大模型的自然语言交互
- 🌊 **水网仿真**：模拟水网运行情况和预测分析
- 🔍 **系统辨识**：识别水网系统特性和参数
- 📊 **智能调度**：优化水资源调度方案
- 🎮 **控制优化**：设计和优化水网控制策略
- ✅ **性能测试**：全面的系统性能评估

---

## 🚀 主要功能

### 1. 自然语言交互
- 通过微信公众号或Web界面与AI助手对话
- 智能识别用户意图并调用相应的专业服务
- 上下文感知的多轮对话能力

### 2. MCP服务集成
支持以下五大类水网专业服务：

| 服务类型 | 功能描述 | 典型应用 |
|---------|---------|---------|
| 🌊 仿真服务 | 水网运行模拟与预测 | 洪水预报、调度预演 |
| 🔍 辨识服务 | 系统参数识别与验证 | 模型校准、特性分析 |
| 📊 调度服务 | 优化调度方案生成 | 水资源配置、发电优化 |
| 🎮 控制服务 | 控制策略设计优化 | PID调参、MPC设计 |
| ✅ 测试服务 | 性能测试与评估 | 可靠性分析、压力测试 |

### 3. 多端访问
- **微信公众号**：移动端随时随地访问
- **Web界面**：桌面端功能完整体验
- **API接口**：第三方系统集成

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                     用户界面层                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 微信公众号    │  │  Web界面      │  │  第三方应用   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓ ↑
┌─────────────────────────────────────────────────────────┐
│                    应用服务层                             │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Flask Web应用 (app.py)                  │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 微信消息处理  │  │  会话管理     │  │  API路由      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓ ↑
┌─────────────────────────────────────────────────────────┐
│                    AI服务层                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │      腾讯元宝大模型 (HunyuanClient)                │  │
│  │  - 自然语言理解                                     │  │
│  │  - 意图识别                                        │  │
│  │  - 对话生成                                        │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓ ↑
┌─────────────────────────────────────────────────────────┐
│                   MCP服务层                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │         MCP服务管理器 (MCPServiceManager)         │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐         │
│  │仿真  │  │辨识  │  │调度  │  │控制  │  │测试  │         │
│  │服务  │  │服务  │  │服务  │  │服务  │  │服务  │         │
│  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘         │
└─────────────────────────────────────────────────────────┘
```

### 核心组件

| 组件 | 文件 | 功能描述 |
|-----|------|---------|
| 主应用 | `app.py` | Flask应用主程序，路由管理 |
| 配置管理 | `config.py` | 系统配置和环境变量管理 |
| AI客户端 | `hunyuan_client.py` | 腾讯元宝大模型接口封装 |
| MCP管理器 | `mcp_manager.py` | MCP服务注册、调用和管理 |
| 微信处理器 | `wechat_handler.py` | 微信公众号消息处理 |
| 前端界面 | `templates/`, `static/` | Web用户界面 |

---

## ⚡ 快速开始

### 环境要求
- Python 3.8+
- pip 包管理器
- 腾讯云账号（用于元宝大模型）
- 微信公众号（可选，用于公众号接入）

### 安装步骤

1. **克隆项目**
```bash
cd /workspace
# 项目文件已存在
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
# 复制配置文件模板
cp .env.example .env

# 编辑 .env 文件，填写实际配置
nano .env  # 或使用其他编辑器
```

5. **启动应用**
```bash
# 开发模式
python app.py

# 生产模式（使用gunicorn）
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

6. **访问应用**
- Web界面: http://localhost:5000
- 健康检查: http://localhost:5000/api/health

---

## ⚙️ 配置说明

### 必需配置

#### 1. 腾讯云配置
在 [腾讯云控制台](https://console.cloud.tencent.com/cam/capi) 获取密钥：

```env
TENCENT_SECRET_ID=your-secret-id
TENCENT_SECRET_KEY=your-secret-key
TENCENT_REGION=ap-guangzhou
```

#### 2. 元宝大模型配置
```env
HUNYUAN_MODEL=hunyuan-lite  # 可选: hunyuan-lite, hunyuan-standard, hunyuan-pro
HUNYUAN_TEMPERATURE=0.7     # 温度参数 0-1
HUNYUAN_MAX_TOKENS=2000     # 最大输出token数
```

### 可选配置

#### 微信公众号配置
在 [微信公众平台](https://mp.weixin.qq.com) 配置：

```env
WECHAT_TOKEN=your-wechat-token
WECHAT_APP_ID=your-app-id
WECHAT_APP_SECRET=your-app-secret
```

#### 系统配置
```env
SECRET_KEY=your-secret-key
DEBUG=False  # 生产环境设为False
PORT=5000
MAX_CONVERSATION_HISTORY=10
```

---

## 🔌 MCP服务接入

### 服务注册

MCP服务可以通过API动态注册：

```python
# Python示例
import requests

service_data = {
    "name": "my_simulation_service",
    "url": "http://localhost:8080/api",
    "description": "自定义仿真服务",
    "type": "simulation"
}

response = requests.post(
    "http://localhost:5000/api/mcp/register",
    json=service_data
)
```

### 服务开发规范

MCP服务需要实现以下REST API接口：

```
POST /execute
Content-Type: application/json

{
    "query": "用户查询文本",
    "params": {
        // 服务特定参数
    }
}

Response:
{
    "status": "success",
    "message": "执行成功",
    "data": {
        // 服务返回数据
    }
}
```

### 内置服务类型

系统预定义了五种服务类型，您可以为每种类型注册实际的服务实现：

| 服务名称 | 类型标识 | 关键词 |
|---------|---------|--------|
| 仿真服务 | simulation | 仿真, 模拟, simulation, 预测 |
| 辨识服务 | identification | 辨识, 识别, 参数 |
| 调度服务 | scheduling | 调度, 优化, scheduling, 方案 |
| 控制服务 | control | 控制, control, PID, MPC |
| 测试服务 | testing | 测试, test, 评估, 性能 |

### 调用MCP服务

```bash
# 直接调用特定服务
curl -X POST http://localhost:5000/api/mcp/services/simulation \
  -H "Content-Type: application/json" \
  -d '{
    "params": {
      "flow_rate": 100,
      "duration": 3600
    }
  }'

# 通过对话自动调用（包含关键词）
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我做一个水网仿真分析"
  }'
```

---

## 📱 微信公众号配置

### 1. 配置服务器
在微信公众平台 -> 开发 -> 基本配置中：

- **服务器地址(URL)**: `https://your-domain.com/wechat`
- **Token**: 与`.env`中的`WECHAT_TOKEN`一致
- **消息加解密方式**: 明文模式（简单）或安全模式（推荐）

### 2. 验证配置
点击"提交"，系统会向您的服务器发送GET请求进行验证。

### 3. 启用服务器配置
验证通过后，启用服务器配置，微信用户的消息将转发到您的服务器。

### 4. 测试
- 关注您的公众号
- 发送消息测试对话功能

---

## 📚 API接口文档

### 对话接口

#### POST /api/chat
发送聊天消息

**请求体**:
```json
{
    "message": "帮我做一个水网仿真",
    "conversation_id": "optional-conversation-id"
}
```

**响应**:
```json
{
    "success": true,
    "message": "AI回复内容",
    "conversation_id": "uuid",
    "mcp_data": {...},
    "timestamp": "2025-10-26T10:00:00"
}
```

### MCP服务接口

#### GET /api/mcp/services
获取所有MCP服务列表

**响应**:
```json
{
    "success": true,
    "services": [
        {
            "name": "simulation",
            "description": "水网仿真服务",
            "type": "simulation",
            "status": "active",
            "url": "http://..."
        }
    ]
}
```

#### POST /api/mcp/services/{service_name}
调用指定MCP服务

**请求体**:
```json
{
    "params": {
        "key": "value"
    }
}
```

#### POST /api/mcp/register
注册新的MCP服务

**请求体**:
```json
{
    "name": "service_name",
    "url": "http://service-url",
    "description": "服务描述",
    "type": "service_type"
}
```

### 系统接口

#### GET /api/health
健康检查

**响应**:
```json
{
    "status": "healthy",
    "timestamp": "2025-10-26T10:00:00",
    "services": {
        "hunyuan": true,
        "mcp": {...}
    }
}
```

#### GET /api/system/info
系统信息

**响应**:
```json
{
    "name": "HydroNet 水网智能体系统",
    "version": "1.0.0",
    "description": "...",
    "capabilities": [...],
    "mcp_services_count": 5
}
```

---

## 🚢 部署指南

### Docker部署（推荐）

创建 `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

构建和运行:
```bash
docker build -t hydronet .
docker run -d -p 5000:5000 --env-file .env hydronet
```

### 云服务器部署

#### 1. 使用Nginx反向代理
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 2. 使用systemd管理服务
创建 `/etc/systemd/system/hydronet.service`:
```ini
[Unit]
Description=HydroNet Service
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/hydronet
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl enable hydronet
sudo systemctl start hydronet
```

### HTTPS配置
使用Let's Encrypt免费证书:
```bash
sudo certbot --nginx -d your-domain.com
```

---

## ❓ 常见问题

### Q: 如何获取腾讯云API密钥？
A: 登录[腾讯云控制台](https://console.cloud.tencent.com/cam/capi)，在"访问管理 -> 访问密钥"中创建新密钥。

### Q: 元宝大模型调用失败怎么办？
A: 
1. 检查API密钥是否正确
2. 确认账户余额充足
3. 检查网络连接
4. 查看日志文件 `hydronet.log`

### Q: 如何添加自定义MCP服务？
A: 
1. 开发符合规范的REST API服务
2. 通过 `/api/mcp/register` 接口注册
3. 或直接修改 `mcp_manager.py` 添加服务定义

### Q: 微信公众号验证失败？
A: 
1. 确认Token配置正确
2. 检查服务器URL可访问
3. 查看服务器日志
4. 确保使用HTTPS（认证后需要）

### Q: 如何清除对话历史？
A: Web界面点击"清空对话"按钮，或通过API调用清除指定会话。

### Q: 性能优化建议？
A:
1. 使用gunicorn多进程部署
2. 配置Redis缓存会话数据
3. 使用CDN加速静态资源
4. 数据库连接池优化
5. MCP服务异步调用

---

## 📞 技术支持

- **项目地址**: [GitHub仓库链接]
- **问题反馈**: [Issues页面]
- **技术文档**: [Wiki链接]
- **团队**: 河北工程大学 · 智慧水网创新团队

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- 腾讯云提供元宝大模型服务
- Flask Web框架
- 微信公众平台
- 所有贡献者和用户

---

<div align="center">

**让每一滴水，都被智能而高效地调控** 💧

Made with ❤️ by HydroNet Team

</div>
