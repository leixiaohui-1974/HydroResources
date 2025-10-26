# HydroNet 项目结构说明

## 📁 项目目录结构

```
/workspace/
│
├── 📄 核心应用文件
│   ├── app.py                      # Flask主应用，路由和API接口
│   ├── config.py                   # 配置管理，环境变量
│   ├── hunyuan_client.py          # 腾讯元宝大模型客户端
│   ├── mcp_manager.py             # MCP服务管理器
│   └── wechat_handler.py          # 微信公众号消息处理器
│
├── 🎨 前端文件
│   ├── templates/
│   │   └── index.html             # Web界面HTML模板
│   │
│   └── static/
│       ├── css/
│       │   └── style.css          # 样式文件
│       └── js/
│           └── main.js            # JavaScript交互逻辑
│
├── 🔧 MCP服务目录
│   └── mcp_services/
│       ├── README.md              # MCP服务开发指南
│       ├── example_service.py     # MCP服务示例代码
│       ├── simulation/            # 仿真服务（待开发）
│       ├── identification/        # 辨识服务（待开发）
│       ├── scheduling/            # 调度服务（待开发）
│       ├── control/               # 控制服务（待开发）
│       └── testing/               # 测试服务（待开发）
│
├── 📝 配置文件
│   ├── .env.example               # 环境变量配置模板
│   ├── .gitignore                 # Git忽略文件
│   └── requirements.txt           # Python依赖包列表
│
├── 🚀 启动脚本
│   ├── start.sh                   # Linux/Mac启动脚本
│   └── start.bat                  # Windows启动脚本
│
├── 📚 文档
│   ├── README.md                  # 原项目README（PPT生成）
│   ├── HYDRONET_README.md         # HydroNet系统完整文档
│   ├── PROJECT_STRUCTURE.md       # 本文件
│   └── build_hydronet_ppt.py      # PPT生成脚本（原有）
│
└── 📦 运行时文件（自动生成）
    ├── venv/                      # Python虚拟环境
    ├── logs/                      # 日志文件
    ├── .env                       # 实际配置（需手动创建）
    └── *.db                       # 数据库文件（可选）
```

## 📄 核心文件说明

### 1. app.py - 主应用程序
**功能**: Flask Web应用的入口文件
**主要路由**:
- `/` - Web界面首页
- `/wechat` - 微信公众号接入点
- `/api/chat` - 聊天对话API
- `/api/mcp/*` - MCP服务管理API
- `/api/health` - 健康检查
- `/api/system/info` - 系统信息

**依赖模块**:
- `config` - 配置管理
- `hunyuan_client` - AI模型
- `mcp_manager` - MCP服务
- `wechat_handler` - 微信处理

### 2. config.py - 配置管理
**功能**: 集中管理应用配置
**配置项**:
- Flask基础配置（端口、调试模式等）
- 微信公众号配置（Token、AppID等）
- 腾讯云API配置（密钥、区域等）
- 元宝大模型配置（模型、温度等）
- MCP服务配置（目录、超时等）

### 3. hunyuan_client.py - AI客户端
**功能**: 腾讯元宝大模型接口封装
**主要方法**:
- `chat()` - 发送对话消息
- `clear_conversation()` - 清除对话历史
- `get_conversation_history()` - 获取对话历史
- `is_available()` - 检查客户端状态

**特性**:
- 自动管理对话上下文
- 支持自定义系统提示词
- 对话历史限制和清理

### 4. mcp_manager.py - MCP服务管理
**功能**: 管理和调用MCP服务
**主要方法**:
- `register_service()` - 注册新服务
- `call_service()` - 调用服务
- `list_services()` - 列出所有服务
- `process_user_query()` - 处理用户查询

**内置服务类型**:
- simulation - 仿真服务
- identification - 辨识服务
- scheduling - 调度服务
- control - 控制服务
- testing - 测试服务

### 5. wechat_handler.py - 微信处理器
**功能**: 处理微信公众号消息
**主要方法**:
- `verify_signature()` - 验证微信签名
- `handle_message()` - 处理消息
- `_process_text_message()` - 处理文本
- `_create_text_response()` - 创建响应

**支持消息类型**:
- 文本消息
- 关注/取消关注事件

## 🎨 前端文件说明

### templates/index.html
**功能**: Web界面主页
**组件**:
- 聊天消息区域
- 输入框和发送按钮
- 快捷操作按钮
- 系统信息模态框
- MCP服务侧边栏

### static/css/style.css
**功能**: 页面样式
**特性**:
- 渐变背景
- 动画效果
- 响应式设计
- 现代化UI

### static/js/main.js
**功能**: 前端交互逻辑
**主要函数**:
- `sendMessage()` - 发送消息
- `addMessage()` - 添加消息到界面
- `showSystemInfo()` - 显示系统信息
- `showServices()` - 显示MCP服务
- `quickQuery()` - 快捷查询

## 🔧 配置文件说明

### .env.example
**功能**: 环境变量配置模板
**使用方法**:
```bash
cp .env.example .env
# 编辑.env文件填写实际配置
```

### requirements.txt
**功能**: Python依赖包列表
**安装方法**:
```bash
pip install -r requirements.txt
```

### .gitignore
**功能**: Git版本控制忽略文件
**包含**:
- Python缓存文件
- 虚拟环境
- 日志文件
- 配置文件（.env）
- 数据库文件

## 🚀 启动脚本说明

### start.sh (Linux/Mac)
**功能**: 自动化启动流程
**步骤**:
1. 检查Python环境
2. 创建/激活虚拟环境
3. 安装依赖
4. 检查配置文件
5. 启动应用

**使用方法**:
```bash
chmod +x start.sh
./start.sh
```

### start.bat (Windows)
**功能**: Windows启动脚本
**使用方法**:
```cmd
start.bat
```

## 🔌 MCP服务说明

### mcp_services/example_service.py
**功能**: MCP服务示例实现
**接口**:
- `POST /execute` - 执行服务
- `GET /health` - 健康检查
- `GET /info` - 服务信息

**运行方法**:
```bash
python mcp_services/example_service.py
```

### mcp_services/README.md
**功能**: MCP服务开发指南
**内容**:
- 服务规范
- 开发教程
- API接口说明
- 示例代码

## 📊 数据流程

```
用户输入
    ↓
微信公众号 / Web界面
    ↓
app.py (Flask路由)
    ↓
wechat_handler / API处理
    ↓
mcp_manager (检查是否需要MCP服务)
    ↓
[如需] 调用MCP服务 → 获取专业数据
    ↓
hunyuan_client (调用AI模型)
    ↓
生成响应
    ↓
返回给用户
```

## 🔒 安全考虑

### 敏感信息
- `.env` 文件包含密钥，**不要**提交到Git
- 生产环境设置 `DEBUG=False`
- 使用强密钥作为 `SECRET_KEY`

### 访问控制
- 微信公众号使用Token验证
- API可添加认证中间件
- MCP服务应实现访问控制

### HTTPS
- 生产环境必须使用HTTPS
- 微信公众号需要HTTPS

## 📈 性能优化建议

### 应用层
- 使用 `gunicorn` 多进程部署
- 添加 Redis 缓存对话历史
- 异步处理长时间MCP服务调用

### 前端
- 压缩CSS/JS文件
- 使用CDN加速静态资源
- 实现消息分页加载

### MCP服务
- 服务结果缓存
- 数据库连接池
- 批量处理请求

## 🧪 测试

### 单元测试
```bash
pytest tests/
```

### API测试
```bash
# 健康检查
curl http://localhost:5000/api/health

# 对话测试
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
```

### MCP服务测试
```bash
# 测试示例服务
python mcp_services/example_service.py &
curl http://localhost:8080/health
```

## 📦 部署

### Docker
```bash
docker build -t hydronet .
docker run -d -p 5000:5000 --env-file .env hydronet
```

### 云服务器
```bash
# 使用systemd管理
sudo systemctl enable hydronet
sudo systemctl start hydronet

# 使用Nginx反向代理
sudo nginx -s reload
```

## 🔄 更新和维护

### 更新依赖
```bash
pip install --upgrade -r requirements.txt
```

### 查看日志
```bash
tail -f logs/hydronet.log
```

### 备份
- 定期备份 `.env` 配置
- 备份数据库文件
- 备份对话历史

## 📞 技术支持

- **文档**: HYDRONET_README.md
- **MCP开发**: mcp_services/README.md
- **问题反馈**: 提交Issue
- **团队**: 河北工程大学·智慧水网创新团队

---

更新日期: 2025-10-26
版本: 1.0.0
