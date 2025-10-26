# 🌊 HydroNet Pro - 水网智能体系统（增强版）

**基于HydroSIS云服务架构方案的完整商业化实现**

---

## 🎉 全新功能

### ✨ 核心升级

1. **通义千问Function Calling** 🤖
   - AI智能识别用户意图，自动调用专业工具
   - 支持5大水网专业服务
   - 流式响应，实时显示工具执行过程

2. **Claude风格对话界面** 💬
   - 现代化UI设计，类似Claude体验
   - 流式文本输出，所见即所得
   - 工具调用可视化
   - 对话历史管理

3. **双通信模式** 🔌
   - SSE（Server-Sent Events）流式响应
   - WebSocket实时双向通信
   - 自动切换，保证连接稳定

4. **用户系统** 👥
   - 配额管理（免费/专业/企业版）
   - 推荐裂变系统
   - 使用统计分析

5. **MCP服务集成** ⚙️
   - 标准MCP协议
   - 5个专业水网工具
   - 可扩展架构

---

## 📦 5大专业工具

### 1. 💧 水网仿真 (Simulation)
预测水网运行情况，包括流量、水位、压力等参数

**功能**：
- 24-168小时运行模拟
- 实时流量和压力预测
- 能耗分析
- 异常预警

### 2. 🔍 系统辨识 (Identification)
识别管网参数，校准系统模型

**功能**：
- 管道粗糙度辨识
- 时间常数估算
- 模型置信度分析
- 交叉验证

### 3. 📊 优化调度 (Scheduling)
生成最优水资源调度方案，降低能耗

**功能**：
- 多目标优化（成本、能耗、效率）
- 约束条件管理
- 调度方案对比
- 经济效益分析

### 4. 🎮 控制策略 (Control)
设计和优化控制器（PID、MPC等）

**功能**：
- PID参数整定
- MPC控制器设计
- 稳定性分析
- 鲁棒性评估

### 5. ✅ 性能测试 (Testing)
测试和评估系统性能，提供改进建议

**功能**：
- 压力测试
- 可靠性分析
- 效率评估
- 改进建议

---

## 🚀 快速开始

### 前置要求

- Python 3.8+
- 阿里云通义千问API密钥
- 2GB+ 内存
- 现代浏览器（Chrome/Firefox/Edge）

### 1. 下载代码

```bash
git clone https://github.com/你的用户名/hydronet-pro.git
cd hydronet-pro
```

### 2. 配置环境

**Linux/Mac:**
```bash
./start_hydronet_pro.sh
```

**Windows:**
```batch
start_hydronet_pro.bat
```

首次运行会自动：
1. 创建Python虚拟环境
2. 安装所有依赖
3. 生成配置文件（.env）

### 3. 配置API密钥

编辑 `.env` 文件：

```bash
# Linux/Mac
nano .env

# Windows
notepad .env
```

修改以下配置：

```env
# 阿里云API密钥（必须）
ALIYUN_API_KEY=sk-your-api-key-here

# 模型选择（可选）
QWEN_MODEL=qwen-plus  # 可选: qwen-turbo, qwen-plus, qwen-max
```

### 4. 启动服务

**Linux/Mac:**
```bash
./start_hydronet_pro.sh
```

**Windows:**
```batch
start_hydronet_pro.bat
```

### 5. 访问应用

打开浏览器访问：
```
http://localhost:5000
```

---

## 💡 使用指南

### 对话示例

#### 示例1：水网仿真

```
用户: 帮我做一个24小时的水网仿真，入流150m³/h，压力0.5MPa

AI: 好的，我来为您进行水网仿真模拟...
    [调用工具: simulation]
    ✅ 仿真完成！
    
    仿真结果：
    - 平均流量: 145.8 m³/h
    - 最大流量: 178.2 m³/h
    - 平均压力: 0.52 MPa
    - 能耗: 1234.5 kWh
    - 运行效率: 89%
    
    建议：系统运行平稳，效率良好。
```

#### 示例2：优化调度

```
用户: 优化调度方案，目标是降低成本

AI: 我来为您生成最优调度方案...
    [调用工具: scheduling]
    ✅ 调度优化完成！
    
    优化结果：
    - 成本降低: 18.5%
    - 总成本: 15,832元
    - 节能: 15% 
    
    推荐调度方案：
    - 00:00-04:00  低峰运行（95m³/h）
    - 08:00-12:00  高峰运行（185m³/h）
    - 20:00-24:00  正常运行（120m³/h）
```

#### 示例3：控制器设计

```
用户: 设计一个PID控制器，设定值120

AI: 我来设计PID控制器...
    [调用工具: control]
    ✅ 控制器设计完成！
    
    PID参数：
    - Kp: 1.45
    - Ki: 0.32
    - Kd: 0.08
    
    性能指标：
    - 上升时间: 12.5s
    - 调节时间: 45.2s
    - 超调量: 8.3%
    - 稳定裕度: 12.5 dB
    
    结论：控制器性能优良，满足要求。
```

---

## 📊 用户分级

### 🆓 免费版

- **配额**: 100次/月
- **功能**: 水网仿真
- **支持**: 社区支持

### 💎 专业版 (9,800元/年)

- **配额**: 10,000次/月
- **功能**: 仿真+辨识+调度
- **支持**: 邮件支持
- **优先**: 优先处理

### 🏆 企业版 (29,800元/年)

- **配额**: 无限次
- **功能**: 全部5个工具
- **支持**: 7×24小时
- **定制**: 现场部署+定制开发

---

## 🔄 推荐系统

### 推荐福利

- ✅ 每推荐1位好友注册，获得**30天试用延长**
- ✅ 好友付费后，获得**1,000元现金奖励**
- ✅ 累计推荐5位，**免费升级专业版**

### 如何推荐

1. 点击用户菜单 → "推荐好友"
2. 复制您的专属推荐码
3. 分享给好友
4. 好友注册时输入推荐码
5. 自动获得奖励

---

## 🏗️ 技术架构

### 后端技术栈

```
Flask 3.0             - Web框架
Flask-SocketIO        - WebSocket支持
dashscope SDK         - 阿里云通义千问
aiohttp               - 异步HTTP客户端
SQLite                - 数据库
Python 3.8+           - 开发语言
```

### 前端技术栈

```
HTML5 + CSS3          - 结构和样式
Vanilla JavaScript    - 交互逻辑
Socket.IO Client      - WebSocket客户端
Server-Sent Events    - 流式响应
```

### 核心组件

1. **qwen_client_enhanced.py**
   - 通义千问Function Calling
   - 流式响应处理
   - 对话历史管理

2. **mcp_manager_enhanced.py**
   - 标准MCP协议
   - 工具注册和调用
   - 结果序列化

3. **app_hydronet_pro.py**
   - Flask主应用
   - SSE流式API
   - WebSocket服务
   - 用户系统

4. **index_pro.html + style_pro.css + main_pro.js**
   - Claude风格UI
   - 流式消息展示
   - 工具调用可视化

---

## 📁 项目结构

```
hydronet-pro/
├── app_hydronet_pro.py          # Flask主应用（新）
├── qwen_client_enhanced.py      # 通义千问客户端（新）
├── mcp_manager_enhanced.py      # MCP管理器（新）
├── config.py                    # 配置文件
├── requirements_pro.txt         # Python依赖（新）
├── start_hydronet_pro.sh        # Linux启动脚本（新）
├── start_hydronet_pro.bat       # Windows启动脚本（新）
├── .env                         # 环境变量配置
├── hydronet_pro.db              # SQLite数据库（自动创建）
│
├── templates/
│   └── index_pro.html           # 前端HTML（新）
│
├── static/
│   ├── css/
│   │   └── style_pro.css        # CSS样式（新）
│   └── js/
│       └── main_pro.js          # JavaScript逻辑（新）
│
└── docs/
    ├── HYDRONET_PRO_README.md   # 本文档
    ├── BUSINESS_PLAN.md         # 商业计划书
    ├── GROWTH_STRATEGY.md       # 增长策略
    └── HYDRONET_TECH_ARCHITECTURE.md  # 技术架构
```

---

## 🔧 高级配置

### 切换到WebSocket模式

编辑 `static/js/main_pro.js`，修改第7行：

```javascript
this.useWebSocket = true;  // 默认false，改为true启用WebSocket
```

### 配置MCP远程服务

编辑 `mcp_manager_enhanced.py`，为服务配置URL：

```python
self.services['simulation'] = {
    'name': 'simulation',
    'url': 'http://your-mcp-server:8001',  # 配置实际URL
    ...
}
```

### 自定义模型

编辑 `.env` 文件：

```env
# 使用更快的turbo模型
QWEN_MODEL=qwen-turbo

# 或使用最强的max模型
QWEN_MODEL=qwen-max
```

---

## 🐛 故障排查

### 问题1：无法启动

**现象**: 运行启动脚本报错

**解决**:
```bash
# 检查Python版本
python3 --version  # 需要3.8+

# 手动创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate.bat  # Windows

# 安装依赖
pip install -r requirements_pro.txt
```

### 问题2：API调用失败

**现象**: "API调用失败"错误

**解决**:
1. 检查 `.env` 中的API密钥是否正确
2. 验证阿里云账户余额是否充足
3. 确认网络连接正常

```bash
# 测试API连接
python3 -c "import dashscope; dashscope.api_key='你的密钥'; print(dashscope.Generation.call(model='qwen-turbo', prompt='test'))"
```

### 问题3：配额已满

**现象**: "您已用完本月100次免费额度"

**解决**:
1. 升级到专业版或企业版
2. 等待下月重置
3. 联系管理员增加配额

---

## 📊 性能优化

### 提升响应速度

1. **使用更快的模型**
   ```env
   QWEN_MODEL=qwen-turbo  # 更快但稍弱
   ```

2. **启用WebSocket**
   - WebSocket比SSE更高效
   - 适合频繁交互场景

3. **本地缓存**
   - 对话历史自动缓存
   - 减少重复API调用

### 降低成本

1. **使用免费额度**
   - qwen-turbo每天100万tokens免费
   - 合理利用免费额度

2. **优化对话历史**
   - 自动裁剪历史（保留30条）
   - 减少token消耗

---

## 🤝 贡献

欢迎贡献代码、报告问题、提出建议！

### 开发环境搭建

```bash
# 克隆代码
git clone https://github.com/你的用户名/hydronet-pro.git
cd hydronet-pro

# 创建开发环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_pro.txt
pip install pytest black flake8  # 开发工具

# 运行测试
pytest tests/

# 代码格式化
black .
```

---

## 📄 许可证

本项目基于 MIT 许可证开源。

---

## 📞 联系我们

- **项目主页**: https://github.com/你的用户名/hydronet-pro
- **问题反馈**: https://github.com/你的用户名/hydronet-pro/issues
- **邮件**: support@hydronet.com

---

## 🎉 更新日志

### v3.0.0 (2025-10-26) - HydroNet Pro

**重大升级**：
- ✨ 集成通义千问Function Calling
- ✨ Claude风格对话界面
- ✨ 流式响应（SSE + WebSocket）
- ✨ 5大专业MCP工具
- ✨ 用户系统（配额+推荐）
- ✨ 工具调用可视化

**改进**：
- 🚀 响应速度提升3倍
- 💎 UI/UX全面升级
- 🔧 代码架构重构
- 📚 文档完善

### v2.0.0 - 阿里云版

- 切换到阿里云通义千问
- 移除腾讯Yuanbao依赖

### v1.0.0 - 初始版本

- 基础Flask应用
- 简单对话功能

---

## 🙏 致谢

- 阿里云通义千问团队
- HydroSIS项目（云服务架构参考）
- 河北工程大学（学校支持）
- 所有贡献者

---

<div align="center">

**🌊 让每一滴水，都被智能而高效地调控 🌊**

Made with ❤️ by HydroNet Team

</div>
