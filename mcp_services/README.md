# MCP服务开发指南

本目录用于存放MCP（Model Context Protocol）服务的实现。

## 📁 目录说明

```
mcp_services/
├── README.md                 # 本文件
├── example_service.py        # MCP服务示例
├── simulation/              # 仿真服务（待实现）
├── identification/          # 辨识服务（待实现）
├── scheduling/              # 调度服务（待实现）
├── control/                 # 控制服务（待实现）
└── testing/                 # 测试服务（待实现）
```

## 🔌 MCP服务规范

### 必需接口

每个MCP服务必须实现以下REST API接口：

#### 1. 执行接口
```
POST /execute
Content-Type: application/json

请求体:
{
    "query": "用户查询文本",
    "params": {
        // 服务特定参数
    }
}

响应:
{
    "status": "success" | "error",
    "message": "执行信息",
    "data": {
        // 服务返回的数据
    },
    "timestamp": "ISO格式时间戳"
}
```

#### 2. 健康检查接口
```
GET /health

响应:
{
    "status": "healthy" | "unhealthy",
    "service": "服务名称",
    "version": "版本号",
    "timestamp": "ISO格式时间戳"
}
```

#### 3. 服务信息接口（推荐）
```
GET /info

响应:
{
    "name": "服务名称",
    "type": "服务类型",
    "description": "服务描述",
    "version": "版本号",
    "capabilities": ["能力列表"],
    "parameters": {
        "参数名": {
            "type": "参数类型",
            "description": "参数描述",
            "default": "默认值"
        }
    }
}
```

## 🚀 快速开始

### 1. 运行示例服务

```bash
# 安装依赖
pip install flask numpy

# 运行示例服务
python mcp_services/example_service.py
```

服务将在 `http://localhost:8080` 启动。

### 2. 注册服务到HydroNet

启动HydroNet主应用后，通过API注册服务：

```bash
curl -X POST http://localhost:5000/api/mcp/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "example_simulation",
    "url": "http://localhost:8080",
    "description": "示例仿真服务",
    "type": "simulation"
  }'
```

### 3. 测试服务

```bash
# 直接调用服务
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{
    "query": "进行水流仿真",
    "params": {
      "flow_rate": 120,
      "duration": 7200,
      "roughness": 0.015
    }
  }'

# 通过HydroNet调用
curl -X POST http://localhost:5000/api/mcp/services/example_simulation \
  -H "Content-Type: application/json" \
  -d '{
    "params": {
      "flow_rate": 120
    }
  }'
```

## 📚 服务类型说明

### 1. 仿真服务 (Simulation)
- **功能**: 水网运行模拟与预测
- **关键词**: 仿真、模拟、simulation、预测
- **典型参数**: 流量、水位、持续时间、边界条件
- **输出**: 时间序列数据、预测结果、警告信息

### 2. 辨识服务 (Identification)
- **功能**: 系统参数识别与验证
- **关键词**: 辨识、识别、参数、identification
- **典型参数**: 观测数据、初始参数估计
- **输出**: 识别的参数、置信度、验证结果

### 3. 调度服务 (Scheduling)
- **功能**: 优化调度方案生成
- **关键词**: 调度、优化、scheduling、方案
- **典型参数**: 目标函数、约束条件、时间窗口
- **输出**: 最优调度方案、目标函数值、可行性分析

### 4. 控制服务 (Control)
- **功能**: 控制策略设计优化
- **关键词**: 控制、control、PID、MPC
- **典型参数**: 系统模型、性能指标、约束
- **输出**: 控制参数、性能分析、稳定性指标

### 5. 测试服务 (Testing)
- **功能**: 性能测试与评估
- **关键词**: 测试、test、评估、性能
- **典型参数**: 测试场景、评估指标
- **输出**: 测试结果、性能指标、建议

## 🛠️ 开发建议

### 1. 错误处理
```python
try:
    # 服务逻辑
    result = perform_task(params)
    return jsonify({
        'status': 'success',
        'data': result
    })
except ValueError as e:
    return jsonify({
        'status': 'error',
        'message': f'参数错误: {str(e)}'
    }), 400
except Exception as e:
    return jsonify({
        'status': 'error',
        'message': f'服务错误: {str(e)}'
    }), 500
```

### 2. 参数验证
```python
def validate_params(params):
    required = ['flow_rate', 'duration']
    for param in required:
        if param not in params:
            raise ValueError(f'缺少必需参数: {param}')
    
    if params['flow_rate'] <= 0:
        raise ValueError('流量必须大于0')
```

### 3. 日志记录
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/execute', methods=['POST'])
def execute():
    logger.info(f"收到执行请求: {request.json}")
    # ...
    logger.info(f"执行完成，耗时: {elapsed_time}秒")
```

### 4. 性能优化
- 使用缓存减少重复计算
- 异步处理长时间任务
- 数据库连接池
- 批量处理请求

### 5. 安全考虑
- 输入验证和清理
- 访问控制和认证
- 数据加密传输（HTTPS）
- 防止注入攻击

## 🔧 常用工具和库

### Python推荐库
```python
# Web框架
Flask==3.0.0
FastAPI==0.104.1

# 科学计算
numpy==1.24.3
scipy==1.11.3
pandas==2.0.3

# 水力学/水文学
swmm-api==0.2.0.17.3  # SWMM模型接口
pyet==1.1.0           # 蒸散发计算

# 优化
cvxpy==1.4.1          # 凸优化
pulp==2.7.0           # 线性规划

# 机器学习
scikit-learn==1.3.2
tensorflow==2.14.0    # 如需深度学习

# 数据可视化
matplotlib==3.8.0
plotly==5.18.0
```

## 📖 参考资源

- [Flask文档](https://flask.palletsprojects.com/)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [MCP协议说明](https://spec.modelcontextprotocol.io/)
- [HydroNet主项目README](../HYDRONET_README.md)

## 💡 示例项目

查看 `example_service.py` 获取完整的服务实现示例。

## 🤝 贡献

欢迎贡献您的MCP服务实现！请确保：
1. 遵循上述接口规范
2. 提供充分的文档和示例
3. 包含单元测试
4. 代码风格一致

---

如有问题或建议，请联系团队或提交Issue。
