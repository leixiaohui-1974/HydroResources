# 🚀 HydroNet 快速入门指南

5分钟快速启动HydroNet水网智能体系统！

## 📋 前提条件

- ✅ Python 3.8 或更高版本
- ✅ pip 包管理器
- ✅ 腾讯云账号（用于元宝大模型）
- ⚪ 微信公众号（可选）

## ⚡ 三步启动

### 第1步：配置环境

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
nano .env  # 或使用其他编辑器
```

**最少需要配置这两项**：
```env
TENCENT_SECRET_ID=你的腾讯云密钥ID
TENCENT_SECRET_KEY=你的腾讯云密钥Key
```

💡 在这里获取密钥：https://console.cloud.tencent.com/cam/capi

### 第2步：安装依赖

```bash
# Linux/Mac
./start.sh

# 或手动安装
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 第3步：启动应用

```bash
# 开发模式
python app.py

# 生产模式
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 🎉 完成！

现在可以访问：
- 🌐 Web界面：http://localhost:5000
- 🔍 健康检查：http://localhost:5000/api/health

## 💬 测试对话

### 通过Web界面
1. 打开浏览器访问 http://localhost:5000
2. 在聊天框输入："你好，帮我介绍一下系统功能"
3. 点击发送或按 Ctrl+Enter

### 通过API
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我做一个水网仿真分析"
  }'
```

## 🔌 启动MCP服务（可选）

```bash
# 新开一个终端
cd mcp_services
python example_service.py

# 注册服务
curl -X POST http://localhost:5000/api/mcp/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "example_simulation",
    "url": "http://localhost:8080",
    "description": "示例仿真服务",
    "type": "simulation"
  }'
```

## 📱 配置微信公众号（可选）

### 1. 修改配置
```env
WECHAT_TOKEN=你设置的Token
WECHAT_APP_ID=你的AppID
WECHAT_APP_SECRET=你的AppSecret
```

### 2. 公众号后台配置
- 服务器URL：`https://你的域名/wechat`
- Token：与配置文件一致
- 消息加解密：明文模式

### 3. 提交验证
点击提交，等待验证通过

### 4. 测试
关注你的公众号，发送消息测试

## 🧪 快速测试清单

- [ ] ✅ Web界面打开正常
- [ ] ✅ 发送消息有响应
- [ ] ✅ 系统信息显示正常
- [ ] ✅ MCP服务列表显示正常
- [ ] ⚪ 快捷按钮功能正常
- [ ] ⚪ MCP服务调用成功
- [ ] ⚪ 微信公众号响应正常

## 🛠️ 常见问题

### Q: 提示"腾讯元宝客户端未初始化"
**A**: 检查`.env`文件中的`TENCENT_SECRET_ID`和`TENCENT_SECRET_KEY`是否配置正确

### Q: 端口5000被占用
**A**: 修改`.env`中的`PORT=5000`为其他端口，如`PORT=8000`

### Q: 安装依赖失败
**A**: 
```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: Web界面无法打开
**A**: 检查防火墙设置，确保端口开放

### Q: AI响应很慢
**A**: 
- 检查网络连接
- 考虑更换更快的模型（如hunyuan-lite）
- 减小`HUNYUAN_MAX_TOKENS`的值

## 📚 下一步

✅ **基础使用**
- 阅读 [HYDRONET_README.md](HYDRONET_README.md) 了解完整功能
- 查看 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) 了解项目结构

🔧 **开发MCP服务**
- 阅读 [mcp_services/README.md](mcp_services/README.md)
- 参考 [example_service.py](mcp_services/example_service.py)
- 开发你自己的专业服务

🚀 **部署生产环境**
- 配置HTTPS证书
- 使用Nginx反向代理
- 配置systemd服务
- 添加监控和日志

🎨 **定制界面**
- 修改 `templates/index.html`
- 调整 `static/css/style.css`
- 扩展 `static/js/main.js`

## 🎓 学习资源

### 官方文档
- [Flask文档](https://flask.palletsprojects.com/)
- [腾讯云混元大模型](https://cloud.tencent.com/product/hunyuan)
- [微信公众平台](https://mp.weixin.qq.com/wiki)

### 视频教程
- 待补充

### 示例项目
- 查看`mcp_services/example_service.py`

## 💡 快捷命令

```bash
# 启动应用
python app.py

# 启动MCP示例服务
python mcp_services/example_service.py

# 查看日志
tail -f hydronet.log

# 测试健康检查
curl http://localhost:5000/api/health

# 查看系统信息
curl http://localhost:5000/api/system/info

# 列出MCP服务
curl http://localhost:5000/api/mcp/services
```

## 🎯 使用场景示例

### 场景1: 水网仿真分析
```
用户: "帮我做一个流量为150m³/s、持续2小时的水网仿真"
AI: [自动调用仿真MCP服务]
    返回仿真结果、水位变化、流速等数据
```

### 场景2: 系统参数辨识
```
用户: "识别当前水网系统的粗糙系数和时间常数"
AI: [自动调用辨识MCP服务]
    返回识别的参数值和置信度
```

### 场景3: 智能调度优化
```
用户: "生成明天的最优调度方案，目标是降低能耗"
AI: [自动调用调度MCP服务]
    返回优化后的调度方案
```

## 🆘 需要帮助？

- 📖 查看完整文档：[HYDRONET_README.md](HYDRONET_README.md)
- 🐛 报告问题：提交Issue
- 💬 技术交流：联系团队

---

**开始你的HydroNet之旅吧！** 🚀💧

河北工程大学·智慧水网创新团队
