# 🚀 HydroNet Pro + HydroSIS 快速开始

**5分钟部署完整的水文智能平台**

---

## 📋 前置条件

确保你已安装：

- ✅ **Docker** & **Docker Compose** (用于HydroSIS服务器)
- ✅ **Python 3.10+** (用于HydroNet Pro)
- ✅ **Git** (用于克隆项目)
- ✅ **阿里云API密钥** (用于通义千问)

---

## ⚡ 一键启动（推荐）

```bash
# 在HydroNet项目根目录执行
./start_with_hydrosis.sh
```

脚本会自动：
1. ✅ 检查Docker环境
2. ✅ 克隆HydroSIS项目
3. ✅ 启动HydroSIS MCP服务器（18个水文工具）
4. ✅ 配置HydroNet Pro
5. ✅ 安装Python依赖
6. ✅ 启动HydroNet Pro

**启动后访问**: http://localhost:5000

---

## 📖 手动部署步骤

### 步骤1：克隆HydroSIS项目

```bash
cd /workspace
git clone -b codex/main-0919 https://github.com/leixiaohui-1974/HydroSIS.git
```

### 步骤2：启动HydroSIS MCP服务器

```bash
cd HydroSIS/mcp_server

# 使用Docker Compose启动
docker-compose up -d

# 查看日志
docker-compose logs -f mcp-server
```

**验证服务**：
```bash
# 健康检查
curl http://localhost:8080/health

# 应返回：
# {
#   "status": "healthy",
#   "timestamp": "...",
#   "tools_count": 18
# }
```

### 步骤3：配置HydroNet Pro

编辑 `.env` 文件，添加HydroSIS配置：

```env
# HydroSIS MCP集成
HYDROSIS_MCP_ENABLED=true
HYDROSIS_MCP_URL=http://localhost:8080
HYDROSIS_MCP_TIMEOUT=300
```

完整的`.env`示例：
```env
# Flask配置
FLASK_APP=app_hydronet_pro.py
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
HOST=0.0.0.0
PORT=5000
DEBUG=False

# 阿里云通义千问
ALIYUN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
QWEN_MODEL=qwen-plus

# 数据库
DATABASE_PATH=hydronet_pro.db

# HydroSIS MCP集成
HYDROSIS_MCP_ENABLED=true
HYDROSIS_MCP_URL=http://localhost:8080
HYDROSIS_MCP_TIMEOUT=300
```

### 步骤4：启动HydroNet Pro

```bash
cd /workspace

# 使用启动脚本
./start_hydronet_pro.sh

# 或手动启动
source venv/bin/activate
python3 app_hydronet_pro.py
```

**启动日志示例**：
```
======================================================================
🌊 HydroNet Pro - 增强版水网智能体系统
======================================================================
✅ 通义千问服务已初始化 - 模型: qwen-plus
✅ MCP服务管理器已初始化 - 5 个HydroNet服务
✅ 已连接HydroSIS MCP服务器: http://localhost:8080
======================================================================

🔄 加载HydroSIS工具...
✅ 已加载 18 个HydroSIS工具
   - project_management: 3 个
   - gis_processing: 2 个
   - data_management: 1 个
   - model_configuration: 2 个
   - simulation: 1 个
   - calibration: 1 个
   - analysis: 1 个
   - visualization: 1 个

======================================================================
🚀 HydroNet Pro 启动完成！
======================================================================
🌐 访问地址: http://0.0.0.0:5000
🤖 AI模型: qwen-plus
🔌 HydroNet服务: 5 个
🌊 HydroSIS工具: 18 个 (http://localhost:8080)
📦 总工具数: 23 个
💾 数据库: hydronet_pro.db
======================================================================
```

---

## 🧪 测试集成

### 测试1：检查工具列表

浏览器访问：http://localhost:5000

在对话框输入：
```
列出所有可用的工具
```

应该看到**23个工具**：
- 5个HydroNet工具（水网仿真、辨识、调度、控制、测试）
- 18个HydroSIS工具（项目管理、流域划分、模型配置、模拟等）

### 测试2：创建水文项目

```
帮我创建一个水文模拟项目，名称叫"测试项目"
```

AI会自动调用`hydrosis_create_project`工具，返回真实结果：
```
✅ 已创建项目！
项目ID: proj-20251026-001
路径: /data/users/default_user/projects/proj-20251026-001
状态: created
```

### 测试3：流域划分

```
基于DEM文件进行流域划分，汇水点位置是东经120.5，北纬30.2
```

AI会调用`hydrosis_delineate_watershed`工具（异步任务）：
```
⏳ 任务已提交...
任务ID: task-xyz123

⏳ 进度: 20% - 加载DEM数据...
⏳ 进度: 40% - 计算流向...
⏳ 进度: 60% - 流域划分...
⏳ 进度: 80% - 生成边界...
✅ 进度: 100% - 完成！

结果：
- 子流域数: 12个
- 总面积: 4,567 km²
- 主河道长度: 89 km
```

---

## 🛑 停止服务

```bash
# 一键停止所有服务
./stop_all.sh

# 或分别停止

# 停止HydroNet Pro
kill $(cat .hydronet.pid)

# 停止HydroSIS MCP服务器
cd HydroSIS/mcp_server
docker-compose down
```

---

## 📊 可用工具一览

### HydroNet工具 (5个)

1. **simulation** - 水网仿真模拟
2. **identification** - 系统辨识
3. **scheduling** - 智能调度
4. **control** - 控制策略
5. **testing** - 性能测试

### HydroSIS工具 (18个)

#### 项目管理 (3个)
- `hydrosis_create_project` - 创建水文项目
- `hydrosis_list_projects` - 列出所有项目
- `hydrosis_get_project` - 获取项目详情

#### GIS处理 (2个)
- `hydrosis_delineate_watershed` - 流域划分（基于DEM）
- `hydrosis_generate_gis_report` - 生成GIS报告

#### 数据管理 (1个)
- `hydrosis_upload_forcing_data` - 上传气象驱动数据

#### 模型配置 (2个)
- `hydrosis_configure_runoff_model` - 配置产流模型（SCS/新安江/HBV等）
- `hydrosis_configure_routing` - 配置汇流方法

#### 模拟运行 (1个)
- `hydrosis_run_simulation` - 运行水文模拟（异步）

#### 参数校准 (1个)
- `hydrosis_calibrate_parameters` - 参数自动校准（异步）

#### 结果分析 (1个)
- `hydrosis_analyze_results` - 模拟结果分析

#### 可视化 (1个)
- `hydrosis_generate_gis_report` - 生成可视化报告

**以及更多工具...**

---

## 💡 使用示例

### 完整建模流程

```
用户: 我想做一个长江流域的水文模拟

AI: 好的！我来帮您进行完整的流程：

【步骤1：创建项目】
[调用 hydrosis_create_project]
✅ 项目已创建
项目ID: proj-202510260001

【步骤2：流域划分】
请提供DEM数据和汇水点位置

用户: DEM文件在/data/dems/yangtze.tif，汇水点：121.5E, 31.2N

AI: 收到！开始流域划分...
[调用 hydrosis_delineate_watershed - 异步]
⏳ 任务处理中...
✅ 完成！
- 子流域: 23个
- 面积: 15,678 km²

【步骤3：配置模型】
建议使用什么产流模型？

用户: 使用SCS方法，CN值75

AI: 好的！
[调用 hydrosis_configure_runoff_model]
✅ 模型配置完成
模型: SCS曲线数法
参数: CN=75

【步骤4：运行模拟】
[调用 hydrosis_run_simulation - 异步]
⏳ 模拟进行中...
⏳ 35% - 计算产流...
⏳ 65% - 河道汇流...
⏳ 85% - 评估指标...
✅ 100% - 完成！

【结果】
- NSE: 0.85 (优秀)
- RMSE: 12.3 m³/s
- 总径流: 780 mm
- 误差: 1.6%

已生成完整报告！
```

---

## 🔧 故障排查

### 问题1：HydroSIS服务无法连接

**检查**：
```bash
# 1. 检查Docker容器状态
docker ps | grep hydrosis

# 2. 检查端口
netstat -tuln | grep 8080

# 3. 测试健康检查
curl http://localhost:8080/health

# 4. 查看日志
cd HydroSIS/mcp_server
docker-compose logs -f mcp-server
```

**解决**：
```bash
# 重启HydroSIS服务
cd HydroSIS/mcp_server
docker-compose restart
```

### 问题2：工具调用失败

**检查HydroNet Pro日志**：
```bash
tail -f hydronet_pro.log
```

**常见错误**：
- `❌ HydroSIS MCP客户端未初始化` → 检查`.env`中`HYDROSIS_MCP_ENABLED=true`
- `❌ 连接HydroSIS服务器失败` → 确保HydroSIS服务正在运行
- `⏰ 工具执行超时` → 增加`HYDROSIS_MCP_TIMEOUT`（如600秒）

### 问题3：异步任务卡住

**调整超时时间**：

编辑`.env`:
```env
HYDROSIS_MCP_TIMEOUT=600  # 增加到10分钟
```

重启HydroNet Pro。

---

## 📈 性能优化

### 单服务器配置

**推荐配置**（学校100万设备）：
```
CPU: 32核+
内存: 64GB+
存储: 500GB SSD

服务分配：
- HydroNet Pro: 8GB内存，4核
- HydroSIS MCP: 32GB内存，16核
- PostgreSQL: 8GB内存，4核
- Redis: 4GB内存，2核
- MinIO: 4GB内存，2核

预计承载：
- 并发用户: 200-500
- 同时建模: 10-20个
- 总用户: 500-1000
```

### 监控和日志

```bash
# HydroSIS日志
cd HydroSIS/mcp_server
docker-compose logs -f

# HydroNet Pro日志
tail -f hydronet_pro.log

# 系统资源
docker stats

# 磁盘使用
df -h
```

---

## 🎯 下一步

### ✅ 部署完成后

1. **邀请首批用户测试**
   - 高校研究人员
   - 水务企业工程师
   - 设计院专业人员

2. **收集反馈**
   - 功能需求
   - 性能表现
   - 用户体验

3. **持续优化**
   - 参数调优
   - 界面改进
   - 功能增强

### 📚 更多文档

- **集成方案详解**: [HYDROSIS_INTEGRATION.md](./HYDROSIS_INTEGRATION.md)
- **HydroNet Pro文档**: [HYDRONET_PRO_README.md](./HYDRONET_PRO_README.md)
- **业务计划**: [BUSINESS_PLAN.md](./BUSINESS_PLAN.md)
- **增长策略**: [GROWTH_STRATEGY.md](./GROWTH_STRATEGY.md)

---

## 🆘 获取帮助

- **GitHub Issues**: https://github.com/leixiaohui-1974/HydroSIS/issues
- **查看文档**: 详细的集成文档在`HYDROSIS_INTEGRATION.md`
- **查看日志**: 大多数问题可以从日志中找到原因

---

<div align="center">

## ✅ 检查清单

```
□ Docker和Docker Compose已安装
□ Python 3.10+已安装
□ 阿里云API密钥已获取
□ HydroSIS已克隆并启动
□ .env文件已配置
□ HydroNet Pro已启动
□ 访问 http://localhost:5000 成功
□ 测试工具调用成功
□ 可以看到23个工具
```

**全部完成？恭喜！🎉**

你现在拥有一个完整的、生产级的水文智能建模平台！

</div>
