# 🏗️ HydroNet 技术架构方案

**基于HydroSIS云服务架构的商业化实施**

**版本**: 1.0  
**日期**: 2025-10-26  
**目标**: 快速用户增长 + 低成本运营 + 技术领先

---

## 📋 目录

1. [架构设计理念](#1-架构设计理念)
2. [方案一：大模型入口程序（核心）](#2-方案一大模型入口程序核心)
3. [两阶段技术演进](#3-两阶段技术演进)
4. [用户增长技术支撑](#4-用户增长技术支撑)
5. [快速实施路线](#5-快速实施路线)

---

## 1. 架构设计理念

### 1.1 设计原则

基于HydroSIS云服务架构方案，结合我们的**用户增长优先**策略：

```
✅ 快速启动 > 完美架构
✅ 用户体验 > 技术复杂度  
✅ 成本控制 > 功能完备性
✅ 增长黑客 > 传统营销
```

### 1.2 核心架构（参考HydroSIS方案1）

```
┌─────────────────────────────────────────────────────────────┐
│                   用户终端（Web/微信）                         │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         阶段一：学校服务器 (自有100万设备)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │        前端应用 (React/Vue)                          │   │
│  │   - 对话界面  - 项目管理  - 结果展示                  │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │     Flask应用 (app_local.py 增强版)                  │   │
│  │   - 用户认证  - 会话管理  - 任务调度                  │   │
│  │   - 免费版限制  - 推荐系统  - 数据分析                │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │     通义千问 API（阿里云）                            │   │
│  │   - AI对话  - 工具调用  - 流式响应                    │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │     MCP服务管理器                                     │   │
│  │   - 仿真  - 辨识  - 调度  - 控制  - 测试             │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │     数据存储 (PostgreSQL + SQLite)                   │   │
│  │   - 用户数据  - 对话历史  - 项目文件  - 统计数据      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 方案一：大模型入口程序（核心）

### 2.1 前端设计（类Claude界面）

参考HydroSIS方案，但简化启动：

#### 技术栈选择

**MVP版本（1-3个月）**：
```
前端: 现有 HTML + JavaScript + Bootstrap
      ↓ 快速改造成类Claude界面
优势: 零学习成本，立即可用
```

**增长版本（3-6个月）**：
```typescript
// 升级到现代框架
前端: Vue 3 + TypeScript + Element Plus
理由: 
  - Vue学习曲线平缓
  - Element Plus中文文档完善
  - 适合快速开发
  - 国内生态好
```

#### 对话界面设计

```html
<!-- MVP版本：改造现有index.html -->
<div class="chat-container">
  <!-- 侧边栏 -->
  <div class="sidebar">
    <button class="new-chat-btn">+ 新对话</button>
    <div class="conversation-list">
      <!-- 对话历史列表 -->
    </div>
    <div class="user-info">
      <div class="usage-stats">
        <p>本月已用: <span id="usage-count">15</span>/100次</p>
        <p class="upgrade-tip">
          升级专业版解锁无限次数 
          <a href="/pricing">立即升级</a>
        </p>
      </div>
    </div>
  </div>
  
  <!-- 主对话区 -->
  <div class="main-chat">
    <div class="messages" id="message-container">
      <!-- 消息列表 -->
    </div>
    <div class="input-area">
      <textarea id="user-input" placeholder="问我任何水网问题..."></textarea>
      <button id="send-btn">发送</button>
      <button id="upload-btn">📎 上传文件</button>
    </div>
  </div>
</div>

<style>
/* Claude风格UI */
.chat-container {
  display: flex;
  height: 100vh;
  background: #fff;
}

.sidebar {
  width: 260px;
  background: #f7f7f8;
  border-right: 1px solid #e5e5e5;
}

.main-chat {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.message {
  margin-bottom: 20px;
  animation: fadeIn 0.3s;
}

.message.user {
  text-align: right;
}

.message.assistant .content {
  background: #f0f0f0;
  padding: 12px 16px;
  border-radius: 12px;
  display: inline-block;
  max-width: 80%;
}

/* 工具调用展示 */
.tool-call {
  background: #e8f4fd;
  border-left: 3px solid #1890ff;
  padding: 10px;
  margin: 10px 0;
  border-radius: 4px;
}

.tool-call-status {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.tool-call-status.running {
  background: #ffe58f;
  color: #ad6800;
}

.tool-call-status.completed {
  background: #b7eb8f;
  color: #52c41a;
}
</style>

<script>
// 核心JavaScript
class ChatInterface {
  constructor() {
    this.ws = null;
    this.conversationId = null;
    this.init();
  }
  
  init() {
    // 建立WebSocket连接（流式响应）
    this.connectWebSocket();
    
    // 绑定事件
    document.getElementById('send-btn').onclick = () => this.sendMessage();
    document.getElementById('user-input').onkeydown = (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    };
  }
  
  connectWebSocket() {
    this.ws = new WebSocket('ws://localhost:5000/ws');
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'text') {
        this.appendAssistantMessage(data.content);
      } else if (data.type === 'tool_call') {
        this.showToolCall(data.tool_name, data.status, data.result);
      }
    };
  }
  
  async sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    if (!message) return;
    
    // 显示用户消息
    this.appendUserMessage(message);
    input.value = '';
    
    // 发送到后端
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation_id: this.conversationId,
        message: message
      })
    });
    
    // 处理流式响应
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      this.appendAssistantMessage(chunk, true); // 追加模式
    }
  }
  
  appendUserMessage(content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';
    messageDiv.innerHTML = `
      <div class="content">${this.escapeHtml(content)}</div>
    `;
    document.getElementById('message-container').appendChild(messageDiv);
    this.scrollToBottom();
  }
  
  appendAssistantMessage(content, append = false) {
    let messageDiv;
    if (append) {
      // 追加到最后一条助手消息
      const messages = document.querySelectorAll('.message.assistant');
      messageDiv = messages[messages.length - 1];
      messageDiv.querySelector('.content').innerHTML += content;
    } else {
      messageDiv = document.createElement('div');
      messageDiv.className = 'message assistant';
      messageDiv.innerHTML = `
        <div class="avatar">🤖</div>
        <div class="content">${content}</div>
      `;
      document.getElementById('message-container').appendChild(messageDiv);
    }
    this.scrollToBottom();
  }
  
  showToolCall(toolName, status, result) {
    const toolDiv = document.createElement('div');
    toolDiv.className = 'tool-call';
    toolDiv.innerHTML = `
      <div class="tool-call-header">
        <span class="tool-call-name">⚙️ ${toolName}</span>
        <span class="tool-call-status ${status}">${status}</span>
      </div>
      ${result ? `<div class="tool-call-result">${JSON.stringify(result, null, 2)}</div>` : ''}
    `;
    document.getElementById('message-container').appendChild(toolDiv);
    this.scrollToBottom();
  }
  
  scrollToBottom() {
    const container = document.getElementById('message-container');
    container.scrollTop = container.scrollHeight;
  }
  
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// 初始化
const chat = new ChatInterface();
</script>
```

### 2.2 后端设计（Flask增强版）

基于HydroSIS的ChatService设计，改造我们的`app_local.py`：

```python
# app_hydronet.py - HydroNet商业版主程序

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import asyncio
from typing import AsyncGenerator
import dashscope  # 阿里云通义千问SDK
from dashscope import Generation

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ============================================
# 1. 通义千问客户端（参考HydroSIS ChatService）
# ============================================

class QwenChatService:
    """通义千问对话服务（支持工具调用）"""
    
    def __init__(self, api_key: str, mcp_manager):
        dashscope.api_key = api_key
        self.mcp_manager = mcp_manager
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是HydroNet水网智能助手，专门帮助用户进行水网仿真、辨识、调度、控制和测试。

你可以使用以下MCP工具：
- simulation: 水网仿真模拟
- identification: 系统辨识
- scheduling: 优化调度
- control: 控制策略设计
- testing: 系统测试

请用简洁、专业的中文回答。当需要计算时，主动调用工具。对于免费用户，提醒他们每月只有100次调用额度。
"""
    
    async def chat_stream(
        self,
        user_id: str,
        conversation_id: str,
        message: str,
        history: list
    ) -> AsyncGenerator[dict, None]:
        """流式对话（支持工具调用）"""
        
        # 1. 获取MCP工具列表
        mcp_tools = self.mcp_manager.get_tools_list()
        tools = self._convert_to_qwen_tools(mcp_tools)
        
        # 2. 构建消息
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + history + [
            {"role": "user", "content": message}
        ]
        
        # 3. 调用通义千问（流式 + 工具调用）
        responses = Generation.call(
            model='qwen-plus',  # 或 qwen-max（更强但更贵）
            messages=messages,
            tools=tools,
            result_format='message',
            stream=True,
            incremental_output=True
        )
        
        # 4. 处理响应
        tool_calls = []
        
        for response in responses:
            if response.status_code == 200:
                output = response.output
                
                # 处理工具调用
                if output.get('choices') and output['choices'][0].get('message'):
                    msg = output['choices'][0]['message']
                    
                    # 有工具调用
                    if msg.get('tool_calls'):
                        for tool_call in msg['tool_calls']:
                            tool_name = tool_call['function']['name']
                            tool_args = json.loads(tool_call['function']['arguments'])
                            
                            # 通知前端工具调用开始
                            yield {
                                'type': 'tool_call',
                                'tool_name': tool_name,
                                'status': 'running',
                                'arguments': tool_args
                            }
                            
                            # 执行MCP工具
                            try:
                                result = await self.mcp_manager.call_tool(
                                    tool_name,
                                    tool_args,
                                    user_id=user_id
                                )
                                
                                # 通知前端工具调用完成
                                yield {
                                    'type': 'tool_call',
                                    'tool_name': tool_name,
                                    'status': 'completed',
                                    'result': result
                                }
                                
                                tool_calls.append({
                                    'tool_call_id': tool_call['id'],
                                    'role': 'tool',
                                    'name': tool_name,
                                    'content': json.dumps(result)
                                })
                                
                            except Exception as e:
                                yield {
                                    'type': 'tool_call',
                                    'tool_name': tool_name,
                                    'status': 'failed',
                                    'error': str(e)
                                }
                    
                    # 文本内容
                    if msg.get('content'):
                        yield {
                            'type': 'text',
                            'content': msg['content']
                        }
        
        # 5. 如果有工具调用，需要再次调用LLM生成最终回答
        if tool_calls:
            messages_with_tools = messages + [
                {"role": "assistant", "content": "", "tool_calls": tool_calls}
            ] + tool_calls
            
            final_responses = Generation.call(
                model='qwen-plus',
                messages=messages_with_tools,
                result_format='message',
                stream=True
            )
            
            for response in final_responses:
                if response.status_code == 200:
                    content = response.output.choices[0].message.content
                    if content:
                        yield {
                            'type': 'text',
                            'content': content
                        }
    
    def _convert_to_qwen_tools(self, mcp_tools: list) -> list:
        """将MCP工具转换为通义千问格式"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool['name'],
                    "description": tool['description'],
                    "parameters": tool.get('parameters', {})
                }
            }
            for tool in mcp_tools
        ]


# ============================================
# 2. 用户管理（支持免费/付费分级）
# ============================================

class UserManager:
    """用户管理（含免费版限制）"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_user(self, user_id: str) -> dict:
        """获取用户信息"""
        user = await self.db.execute(
            "SELECT * FROM users WHERE id = $1", user_id
        )
        return user
    
    async def check_quota(self, user_id: str) -> dict:
        """检查用户配额"""
        user = await self.get_user(user_id)
        
        # 获取本月使用量
        usage = await self.db.execute("""
            SELECT COUNT(*) as count
            FROM api_calls
            WHERE user_id = $1
              AND created_at >= date_trunc('month', CURRENT_DATE)
        """, user_id)
        
        tier = user['tier']  # 'free', 'pro', 'enterprise'
        limits = {
            'free': 100,
            'pro': 10000,
            'enterprise': -1  # 无限
        }
        
        limit = limits.get(tier, 100)
        used = usage['count']
        
        return {
            'tier': tier,
            'limit': limit,
            'used': used,
            'remaining': limit - used if limit != -1 else -1,
            'can_use': used < limit or limit == -1
        }
    
    async def record_api_call(self, user_id: str, endpoint: str):
        """记录API调用"""
        await self.db.execute("""
            INSERT INTO api_calls (user_id, endpoint, created_at)
            VALUES ($1, $2, NOW())
        """, user_id, endpoint)


# ============================================
# 3. Flask路由（参考HydroSIS API设计）
# ============================================

qwen_service = QwenChatService(
    api_key=os.environ.get('ALIYUN_API_KEY'),
    mcp_manager=mcp_manager
)

user_manager = UserManager(db)

@app.route('/api/chat', methods=['POST'])
async def chat():
    """对话API（流式响应）"""
    data = request.json
    user_id = data.get('user_id')
    conversation_id = data.get('conversation_id')
    message = data.get('message')
    
    # 1. 检查配额
    quota = await user_manager.check_quota(user_id)
    if not quota['can_use']:
        return jsonify({
            'error': 'quota_exceeded',
            'message': f'您已用完本月{quota["limit"]}次免费额度',
            'upgrade_url': '/pricing'
        }), 429
    
    # 2. 加载对话历史
    history = await load_conversation_history(conversation_id)
    
    # 3. 流式响应
    async def generate():
        async for chunk in qwen_service.chat_stream(
            user_id, conversation_id, message, history
        ):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    # 4. 记录API调用
    await user_manager.record_api_call(user_id, '/api/chat')
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream'
    )


@app.route('/api/user/quota', methods=['GET'])
async def get_quota():
    """获取用户配额"""
    user_id = request.args.get('user_id')
    quota = await user_manager.check_quota(user_id)
    return jsonify(quota)


@app.route('/api/user/upgrade', methods=['POST'])
async def upgrade():
    """用户升级（付费）"""
    data = request.json
    user_id = data['user_id']
    tier = data['tier']  # 'pro' or 'enterprise'
    
    # TODO: 集成支付宝/微信支付
    # 1. 生成订单
    # 2. 调用支付接口
    # 3. 支付成功后更新用户等级
    
    return jsonify({'status': 'pending', 'payment_url': '...'})


# ============================================
# 4. WebSocket支持（实时通信）
# ============================================

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('chat_message')
async def handle_chat_message(data):
    """WebSocket消息处理"""
    user_id = data['user_id']
    message = data['message']
    conversation_id = data['conversation_id']
    
    # 检查配额
    quota = await user_manager.check_quota(user_id)
    if not quota['can_use']:
        emit('error', {
            'type': 'quota_exceeded',
            'message': '配额已用完'
        })
        return
    
    # 流式响应
    history = await load_conversation_history(conversation_id)
    
    async for chunk in qwen_service.chat_stream(
        user_id, conversation_id, message, history
    ):
        emit('chat_chunk', chunk)
    
    emit('chat_complete', {})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
```

### 2.3 MCP服务管理器（集成水网专业功能）

```python
# mcp_manager_enhanced.py - 增强版MCP管理器

class MCPServiceManager:
    """MCP服务管理器（水网专业功能）"""
    
    def __init__(self):
        self.services = {
            'simulation': {
                'name': 'simulation',
                'description': '水网仿真模拟',
                'url': 'http://localhost:8001',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'network_config': {
                            'type': 'object',
                            'description': '水网配置（节点、管道）'
                        },
                        'boundary_conditions': {
                            'type': 'object',
                            'description': '边界条件（流量、水位）'
                        },
                        'simulation_duration': {
                            'type': 'number',
                            'description': '模拟时长（秒）'
                        }
                    },
                    'required': ['network_config', 'boundary_conditions']
                }
            },
            'identification': {
                'name': 'identification',
                'description': '系统辨识（参数估计）',
                'url': 'http://localhost:8002',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'observed_data': {
                            'type': 'array',
                            'description': '观测数据'
                        },
                        'model_structure': {
                            'type': 'string',
                            'description': '模型结构'
                        }
                    },
                    'required': ['observed_data']
                }
            },
            'scheduling': {
                'name': 'scheduling',
                'description': '优化调度',
                'url': 'http://localhost:8003',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'objective': {
                            'type': 'string',
                            'enum': ['minimize_cost', 'maximize_efficiency'],
                            'description': '优化目标'
                        },
                        'constraints': {
                            'type': 'object',
                            'description': '约束条件'
                        }
                    },
                    'required': ['objective']
                }
            },
            'control': {
                'name': 'control',
                'description': '控制策略设计',
                'url': 'http://localhost:8004',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'control_type': {
                            'type': 'string',
                            'enum': ['PID', 'MPC', 'optimal'],
                            'description': '控制类型'
                        },
                        'setpoint': {
                            'type': 'number',
                            'description': '设定值'
                        }
                    },
                    'required': ['control_type']
                }
            },
            'testing': {
                'name': 'testing',
                'description': '系统测试',
                'url': 'http://localhost:8005',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'test_scenario': {
                            'type': 'string',
                            'description': '测试场景'
                        }
                    },
                    'required': ['test_scenario']
                }
            }
        }
    
    def get_tools_list(self) -> list:
        """获取工具列表（供LLM使用）"""
        return [
            {
                'name': svc['name'],
                'description': svc['description'],
                'parameters': svc['parameters']
            }
            for svc in self.services.values()
        ]
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: dict,
        user_id: str = None
    ) -> dict:
        """调用MCP工具"""
        
        if tool_name not in self.services:
            raise ValueError(f'Unknown tool: {tool_name}')
        
        service = self.services[tool_name]
        
        # 如果有URL，调用远程服务
        if service.get('url'):
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{service['url']}/execute",
                    json={'parameters': arguments, 'user_id': user_id}
                ) as response:
                    return await response.json()
        else:
            # 本地Mock实现
            return self._mock_tool_execution(tool_name, arguments)
    
    def _mock_tool_execution(self, tool_name: str, args: dict) -> dict:
        """Mock工具执行（用于演示）"""
        
        if tool_name == 'simulation':
            return {
                'status': 'completed',
                'results': {
                    'max_flow': 125.3,
                    'max_pressure': 45.2,
                    'energy_consumption': 1234.5,
                    'plot_url': '/results/simulation_plot.png'
                },
                'message': '仿真完成！最大流量125.3 m³/h'
            }
        
        elif tool_name == 'identification':
            return {
                'status': 'completed',
                'parameters': {
                    'roughness': 0.012,
                    'leakage_rate': 0.03,
                    'confidence': 0.95
                },
                'message': '辨识完成！管道粗糙度0.012'
            }
        
        # ... 其他工具的mock实现
        
        return {'status': 'completed', 'message': f'{tool_name} 执行完成'}
```

---

## 3. 两阶段技术演进

### 3.1 阶段一：学校服务器（0-12月）

**目标**：500-1000个用户

**技术栈**：
```
前端: HTML/JS/Bootstrap → Vue 3
后端: Flask + PostgreSQL
AI: 通义千问API
MCP: 本地Mock服务
存储: 服务器本地磁盘
```

**部署架构**：
```
学校100万服务器
├── Nginx (反向代理 + 静态文件)
├── Gunicorn (Flask应用 × 4实例)
├── PostgreSQL (用户数据 + 对话历史)
├── Redis (会话缓存 + 限流)
└── 通义千问API (阿里云)
```

**成本**：
- 服务器：0元（学校提供）
- 通义千问：0-500元/月（免费额度+少量付费）
- 运维人员：8000元/月
- **总计**：≈10万元/年

### 3.2 阶段二：混合云部署（12-24月）

**目标**：2000-3000个用户

**技术栈演进**：
```
前端: Vue 3 + CDN加速
后端: Flask → FastAPI (异步)
数据库: PostgreSQL主从复制
缓存: Redis集群
消息队列: RabbitMQ
MCP: Docker容器化
```

**架构调整**：
```
┌─────────────────────────┐     ┌─────────────────────────┐
│  阿里云（新客户）        │     │ 学校服务器（老客户）      │
│  - ECS × 2              │     │  - 继续服务              │
│  - RDS PostgreSQL       │     │  - 逐步迁移              │
│  - Redis                │     └─────────────────────────┘
│  - OSS                  │
└─────────────────────────┘
        ↓
  通义千问API（共用）
```

---

## 4. 用户增长技术支撑

### 4.1 免费增值功能实现

```python
# 功能分级表
TIER_FEATURES = {
    'free': {
        'api_calls_per_month': 100,
        'max_conversations': 10,
        'max_file_size_mb': 10,
        'mcp_services': ['simulation'],  # 仅仿真
        'support': 'community',
        'branding': True,  # 显示"由HydroNet提供"
    },
    'pro': {
        'api_calls_per_month': 10000,
        'max_conversations': 100,
        'max_file_size_mb': 100,
        'mcp_services': ['simulation', 'identification', 'scheduling'],
        'support': 'email',
        'branding': False,
        'priority': True,
    },
    'enterprise': {
        'api_calls_per_month': -1,  # 无限
        'max_conversations': -1,
        'max_file_size_mb': 500,
        'mcp_services': 'all',
        'support': '24x7',
        'branding': False,
        'priority': True,
        'custom_deployment': True,
    }
}

# 功能检查装饰器
def require_feature(feature_name: str, tier_required: str = 'pro'):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id')
            user = await get_user(user_id)
            
            tier_level = {'free': 1, 'pro': 2, 'enterprise': 3}
            if tier_level[user.tier] < tier_level[tier_required]:
                return {
                    'error': 'feature_locked',
                    'message': f'此功能需要{tier_required}版本',
                    'upgrade_url': '/pricing'
                }
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 使用示例
@app.route('/api/mcp/scheduling', methods=['POST'])
@require_feature('scheduling', 'pro')
async def run_scheduling(user_id: str, params: dict):
    # ... 执行调度 ...
    pass
```

### 4.2 推荐系统实现

```python
# referral_system.py - 推荐裂变系统

class ReferralSystem:
    """推荐系统"""
    
    def __init__(self, db):
        self.db = db
    
    async def generate_referral_code(self, user_id: str) -> str:
        """生成推荐码"""
        code = hashlib.md5(f"{user_id}{time.time()}".encode()).hexdigest()[:8]
        
        await self.db.execute("""
            INSERT INTO referral_codes (user_id, code, created_at)
            VALUES ($1, $2, NOW())
        """, user_id, code)
        
        return code
    
    async def register_with_referral(
        self,
        username: str,
        email: str,
        password: str,
        referral_code: str = None
    ) -> dict:
        """通过推荐码注册"""
        
        # 1. 创建用户
        user_id = await self.create_user(username, email, password)
        
        # 2. 如果有推荐码，处理奖励
        if referral_code:
            referrer = await self.db.execute("""
                SELECT user_id FROM referral_codes WHERE code = $1
            """, referral_code)
            
            if referrer:
                # 记录推荐关系
                await self.db.execute("""
                    INSERT INTO referrals (referrer_id, referee_id, created_at)
                    VALUES ($1, $2, NOW())
                """, referrer['user_id'], user_id)
                
                # 奖励推荐人（延长试用期）
                await self.reward_referrer(referrer['user_id'], 'trial_extension', 30)
                
                # 奖励被推荐人（延长试用期）
                await self.reward_referee(user_id, 'trial_extension', 30)
        
        return {'user_id': user_id, 'referral_applied': bool(referral_code)}
    
    async def reward_referrer(self, user_id: str, reward_type: str, value: int):
        """奖励推荐人"""
        if reward_type == 'trial_extension':
            # 延长试用期
            await self.db.execute("""
                UPDATE users
                SET trial_end_date = trial_end_date + INTERVAL '$1 days'
                WHERE id = $2
            """, value, user_id)
        
        elif reward_type == 'cash':
            # 现金奖励
            await self.db.execute("""
                INSERT INTO rewards (user_id, type, amount, status)
                VALUES ($1, 'cash', $2, 'pending')
            """, user_id, value)
    
    async def get_referral_stats(self, user_id: str) -> dict:
        """获取推荐统计"""
        stats = await self.db.execute("""
            SELECT 
                COUNT(*) as total_referrals,
                COUNT(CASE WHEN r.status = 'converted' THEN 1 END) as paid_referrals,
                SUM(rw.amount) as total_rewards
            FROM referrals r
            LEFT JOIN rewards rw ON rw.user_id = r.referrer_id
            WHERE r.referrer_id = $1
        """, user_id)
        
        return stats
```

### 4.3 数据分析和增长监控

```python
# analytics.py - 增长数据分析

class GrowthAnalytics:
    """增长数据分析"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_growth_metrics(self, date_range: tuple) -> dict:
        """获取增长指标"""
        
        # 1. 新用户注册
        new_users = await self.db.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM users
            WHERE created_at BETWEEN $1 AND $2
            GROUP BY DATE(created_at)
            ORDER BY date
        """, date_range[0], date_range[1])
        
        # 2. 活跃用户(MAU)
        mau = await self.db.execute("""
            SELECT COUNT(DISTINCT user_id) as mau
            FROM api_calls
            WHERE created_at >= NOW() - INTERVAL '30 days'
        """)
        
        # 3. 付费转化率
        conversion = await self.db.execute("""
            SELECT 
                COUNT(CASE WHEN tier = 'free' THEN 1 END) as free_users,
                COUNT(CASE WHEN tier != 'free' THEN 1 END) as paid_users,
                COUNT(CASE WHEN tier != 'free' THEN 1 END)::float / COUNT(*)::float as conversion_rate
            FROM users
            WHERE created_at <= $1
        """, date_range[1])
        
        # 4. 留存率
        retention = await self.db.execute("""
            WITH cohort AS (
                SELECT 
                    DATE_TRUNC('month', created_at) as cohort_month,
                    user_id
                FROM users
            ),
            activity AS (
                SELECT 
                    c.cohort_month,
                    c.user_id,
                    DATE_TRUNC('month', a.created_at) as activity_month,
                    EXTRACT(MONTH FROM AGE(a.created_at, c.cohort_month)) as month_number
                FROM cohort c
                LEFT JOIN api_calls a ON c.user_id = a.user_id
            )
            SELECT 
                cohort_month,
                month_number,
                COUNT(DISTINCT user_id) as active_users
            FROM activity
            GROUP BY cohort_month, month_number
            ORDER BY cohort_month, month_number
        """)
        
        # 5. 推荐效果
        referral_effect = await self.db.execute("""
            SELECT 
                COUNT(*) as total_referrals,
                COUNT(CASE WHEN ref.status = 'converted' THEN 1 END) as converted,
                AVG(EXTRACT(DAY FROM ref.converted_at - ref.created_at)) as avg_conversion_days
            FROM referrals ref
            WHERE ref.created_at BETWEEN $1 AND $2
        """, date_range[0], date_range[1])
        
        return {
            'new_users': new_users,
            'mau': mau['mau'],
            'conversion_rate': conversion['conversion_rate'],
            'retention_cohort': retention,
            'referral_effect': referral_effect
        }
    
    async def generate_growth_report(self) -> dict:
        """生成增长报告"""
        # ... 生成详细报告 ...
        pass
```

---

## 5. 快速实施路线

### 5.1 第一个月（MVP）

**Week 1-2: 前端改造**
```bash
□ 基于现有index.html改造成Claude风格
□ 添加对话历史侧边栏
□ 实现流式消息展示
□ 添加工具调用可视化
□ 配额显示和升级提示
```

**Week 3: 后端集成**
```bash
□ 集成通义千问API
□ 实现流式响应
□ 添加工具调用功能
□ MCP服务Mock实现
□ WebSocket支持
```

**Week 4: 用户系统**
```bash
□ 用户注册/登录
□ 免费版配额限制
□ 推荐码生成
□ 数据库设计和迁移
□ 部署到学校服务器
```

### 5.2 第2-3个月（增长功能）

```bash
□ 完善推荐裂变系统
□ 集成支付接口（支付宝/微信）
□ 添加数据分析仪表盘
□ 实现真实MCP服务（Docker化）
□ 性能优化和压力测试
□ 增长实验（AB测试）
```

### 5.3 第4-6个月（规模化准备）

```bash
□ 升级到Vue 3前端
□ FastAPI异步后端
□ Redis集群
□ PostgreSQL主从复制
□ CDN加速
□ 监控告警系统
□ 准备阿里云迁移方案
```

---

## 📊 预期效果

### 技术指标

```
性能目标:
  - 响应时间: <200ms (不含AI推理)
  - 并发用户: 500+ (阶段一)
  - 可用性: 99.5%
  - AI响应: <3s (流式首字节)

增长指标:
  - 第1个月: 50-100个用户
  - 第3个月: 300-500个用户
  - 第6个月: 800-1000个用户
  - 免费转付费: >15%
  - 推荐K因子: >1.5
```

### 成本优势

```
对比传统SaaS:
  传统: 需要30-50万/年云服务器成本
  我们: 仅需10万/年（学校支持）
  
节省: 40万/年
节省率: 80%

这就是我们的核心竞争力！🚀
```

---

## 🎯 总结

基于HydroSIS云服务架构方案，我们为HydroNet设计了：

1. **MVP快速启动**：1个月内上线类Claude对话界面
2. **用户增长驱动**：免费增值 + 推荐裂变
3. **成本极低**：学校支持 + 通义千问免费额度
4. **技术先进**：流式响应 + 工具调用 + MCP协议
5. **可扩展性**：平滑过渡到阿里云

**下一步行动**：立即开始Week 1开发！🚀
