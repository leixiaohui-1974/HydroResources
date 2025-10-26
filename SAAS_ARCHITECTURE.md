# 🏢 HydroNet SaaS多租户架构设计

## 📊 当前状态 vs SaaS目标

### ❌ 当前版本（单租户）
```
特点：
- 所有用户共享同一个系统实例
- 没有用户认证和权限管理
- 对话历史混在一起
- 无法区分不同组织/客户
- 适合：个人使用、内部系统
```

### ✅ SaaS版本（多租户）
```
特点：
- 数据隔离：每个租户数据独立
- 用户管理：注册、登录、权限控制
- 资源限额：API调用次数、存储配额
- 计费系统：按使用量计费
- 适合：商业化SaaS服务
```

---

## 🏗️ 多租户架构设计

### 架构层次

```
┌─────────────────────────────────────────────────────┐
│                   访问层                             │
│  Web界面 / 微信 / API / 移动APP                      │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│                  认证授权层                          │
│  • 用户注册/登录                                     │
│  • JWT Token                                         │
│  • 租户识别                                          │
│  • 权限验证 (RBAC)                                   │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│                  租户隔离层                          │
│  • 租户ID注入                                        │
│  • 数据过滤                                          │
│  • 资源配额检查                                      │
│  • 请求限流                                          │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│                  业务逻辑层                          │
│  • AI对话服务                                        │
│  • MCP服务管理                                       │
│  • 数据分析                                          │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│                   数据存储层                         │
│  • 租户数据隔离（共享表 + tenant_id）                │
│  • 或独立数据库（更强隔离）                          │
└─────────────────────────────────────────────────────┘
```

---

## 💾 数据库设计

### 核心表结构

#### 1. 租户表 (tenants)
```sql
CREATE TABLE tenants (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    subdomain VARCHAR(50) UNIQUE,  -- 例如：customer1.hydronet.com
    plan VARCHAR(20),              -- basic/pro/enterprise
    status VARCHAR(20),            -- active/suspended/trial
    quota_api_calls INT,           -- API调用配额
    quota_storage_mb INT,          -- 存储配额
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### 2. 用户表 (users)
```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,  -- 关联租户
    email VARCHAR(100) UNIQUE NOT NULL,
    username VARCHAR(50),
    password_hash VARCHAR(255),
    role VARCHAR(20),                 -- admin/user/viewer
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
```

#### 3. 对话历史表 (conversations)
```sql
CREATE TABLE conversations (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,  -- 数据隔离！
    user_id VARCHAR(36) NOT NULL,
    title VARCHAR(200),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_tenant_user (tenant_id, user_id)
);
```

#### 4. 消息表 (messages)
```sql
CREATE TABLE messages (
    id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,  -- 双重保险
    role VARCHAR(20),                 -- user/assistant/system
    content TEXT,
    tokens_used INT,
    created_at TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    INDEX idx_conversation (conversation_id)
);
```

#### 5. MCP服务配置表 (mcp_services)
```sql
CREATE TABLE mcp_services (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,  -- 每个租户可配置自己的服务
    name VARCHAR(100),
    url VARCHAR(500),
    type VARCHAR(50),
    config JSON,                      -- 服务特定配置
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
```

#### 6. 使用量统计表 (usage_stats)
```sql
CREATE TABLE usage_stats (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36),
    date DATE,
    api_calls INT DEFAULT 0,
    tokens_used INT DEFAULT 0,
    storage_used_mb INT DEFAULT 0,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    INDEX idx_tenant_date (tenant_id, date)
);
```

---

## 🔒 租户隔离策略

### 策略1：共享数据库 + tenant_id（推荐）

**优点**：
- ✅ 成本低，易于维护
- ✅ 资源利用率高
- ✅ 便于跨租户分析

**实现**：
```python
# 装饰器自动注入tenant_id
@require_tenant
def get_conversations(tenant_id, user_id):
    return Conversation.query.filter_by(
        tenant_id=tenant_id,
        user_id=user_id
    ).all()
```

**注意**：
- ⚠️ 必须在所有查询中加入tenant_id过滤
- ⚠️ 需要严格的代码审查防止数据泄露

### 策略2：独立数据库

**优点**：
- ✅ 最强隔离性
- ✅ 适合大客户
- ✅ 易于迁移

**实现**：
```python
# 根据租户路由到不同数据库
def get_db_connection(tenant_id):
    db_config = TENANT_DBS[tenant_id]
    return create_connection(db_config)
```

### 策略3：混合模式（推荐大型SaaS）

```
小租户 → 共享数据库
大租户 → 独立数据库
超大客户 → 独立部署
```

---

## 🔐 认证授权方案

### JWT Token认证

```python
# 登录获取Token
POST /api/auth/login
{
    "email": "user@example.com",
    "password": "xxx"
}

# 响应
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "xxx",
    "user": {
        "id": "user-123",
        "tenant_id": "tenant-456",
        "role": "admin"
    }
}

# 后续请求携带Token
GET /api/conversations
Headers: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### RBAC权限控制

```python
# 角色定义
ROLES = {
    'admin': [
        'manage_users',
        'manage_services',
        'view_stats',
        'all_conversations'
    ],
    'user': [
        'create_conversation',
        'view_own_conversations',
        'use_mcp_services'
    ],
    'viewer': [
        'view_own_conversations'
    ]
}

# 权限装饰器
@require_permission('manage_users')
def create_user(tenant_id, user_data):
    # 只有admin可以创建用户
    pass
```

---

## 📊 资源配额与限流

### 配额检查

```python
class QuotaManager:
    def check_api_quota(self, tenant_id):
        """检查API调用配额"""
        tenant = Tenant.get(tenant_id)
        usage = get_monthly_usage(tenant_id)
        
        if usage.api_calls >= tenant.quota_api_calls:
            raise QuotaExceededError("API调用次数已达上限")
    
    def check_storage_quota(self, tenant_id, size_mb):
        """检查存储配额"""
        tenant = Tenant.get(tenant_id)
        current = get_storage_usage(tenant_id)
        
        if current + size_mb > tenant.quota_storage_mb:
            raise QuotaExceededError("存储空间不足")
```

### 请求限流

```python
from flask_limiter import Limiter

# 根据租户限流
limiter = Limiter(
    key_func=lambda: get_tenant_id(),
    default_limits=["100 per minute"]
)

# 不同套餐不同限额
@limiter.limit("1000/minute", key_func=lambda: get_tenant_plan())
@app.route('/api/chat')
def chat():
    pass
```

---

## 💰 计费系统设计

### 套餐定义

```python
PLANS = {
    'free': {
        'price': 0,
        'api_calls': 1000,      # 月
        'storage_mb': 100,
        'users': 1,
        'mcp_services': 1
    },
    'basic': {
        'price': 99,            # 元/月
        'api_calls': 10000,
        'storage_mb': 1000,
        'users': 5,
        'mcp_services': 5
    },
    'pro': {
        'price': 499,
        'api_calls': 100000,
        'storage_mb': 10000,
        'users': 20,
        'mcp_services': 20
    },
    'enterprise': {
        'price': 'custom',
        'api_calls': 'unlimited',
        'storage_mb': 'unlimited',
        'users': 'unlimited',
        'mcp_services': 'unlimited'
    }
}
```

### 使用量统计

```python
class UsageTracker:
    def track_api_call(self, tenant_id, tokens_used):
        """记录API调用"""
        today = date.today()
        usage = UsageStats.get_or_create(tenant_id, today)
        usage.api_calls += 1
        usage.tokens_used += tokens_used
        usage.save()
    
    def generate_invoice(self, tenant_id, month):
        """生成账单"""
        usage = UsageStats.get_monthly(tenant_id, month)
        plan = Tenant.get(tenant_id).plan
        
        # 计算超额费用
        overage = calculate_overage(usage, plan)
        
        return {
            'base_fee': PLANS[plan]['price'],
            'overage_fee': overage,
            'total': PLANS[plan]['price'] + overage
        }
```

---

## 🚀 实施路线图

### 阶段1：基础多租户（1-2周）✅ 必需

**功能**：
- [x] 用户注册/登录
- [x] JWT认证
- [x] 租户识别
- [x] 数据隔离（tenant_id）
- [x] 基础权限控制

**数据库**：
- 创建租户、用户表
- 所有业务表添加tenant_id

### 阶段2：资源管理（1周）⚠️ 重要

**功能**：
- [x] 配额管理
- [x] 请求限流
- [x] 使用量统计
- [x] 告警通知

### 阶段3：计费系统（2-3周）💰 商业化必需

**功能**：
- [x] 套餐管理
- [x] 账单生成
- [x] 支付集成（支付宝/微信支付）
- [x] 发票开具

### 阶段4：高级功能（2-4周）🎯 增值功能

**功能**：
- [x] 团队协作
- [x] 审计日志
- [x] 数据导出
- [x] API密钥管理
- [x] Webhook通知
- [x] 白标定制

---

## 💻 技术栈推荐

### 后端增强
```python
# 当前：Flask
# 需要添加：
- Flask-JWT-Extended     # JWT认证
- Flask-SQLAlchemy       # ORM
- Flask-Migrate          # 数据库迁移
- Flask-Limiter          # 限流
- Flask-CORS             # 跨域
- Celery                 # 异步任务
- Redis                  # 缓存、会话、限流
```

### 数据库
```
主数据库：PostgreSQL（推荐）/ MySQL
缓存：Redis
搜索：Elasticsearch（可选）
```

### 前端增强
```javascript
// 需要添加：
- 用户登录/注册界面
- 租户管理后台
- 用量统计仪表板
- 计费中心
- 团队管理
```

---

## 📈 性能优化

### 缓存策略
```python
# Redis缓存租户信息
@cache.memoize(timeout=3600)
def get_tenant(tenant_id):
    return Tenant.query.get(tenant_id)

# 缓存用户权限
@cache.memoize(timeout=600)
def get_user_permissions(user_id):
    return User.query.get(user_id).get_permissions()
```

### 数据库优化
```sql
-- 关键索引
CREATE INDEX idx_tenant_id ON conversations(tenant_id);
CREATE INDEX idx_tenant_user ON conversations(tenant_id, user_id);
CREATE INDEX idx_created_at ON messages(created_at);

-- 分区表（大数据量）
CREATE TABLE messages_2025_01 PARTITION OF messages
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

### 读写分离
```python
# 主库写入
primary_db.execute(insert_query)

# 从库读取
replica_db.execute(select_query)
```

---

## 🔒 安全加固

### 1. SQL注入防护
```python
# ✅ 使用ORM
User.query.filter_by(email=email).first()

# ❌ 不要拼接SQL
db.execute(f"SELECT * FROM users WHERE email='{email}'")
```

### 2. XSS防护
```python
from markupsafe import escape
content = escape(user_input)
```

### 3. CSRF防护
```python
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)
```

### 4. 密码加密
```python
from werkzeug.security import generate_password_hash, check_password_hash

# 存储
password_hash = generate_password_hash(password)

# 验证
check_password_hash(password_hash, password)
```

### 5. API密钥管理
```python
# 为每个租户生成API Key
api_key = secrets.token_urlsafe(32)

# 使用时验证
@require_api_key
def api_endpoint():
    pass
```

---

## 📊 监控与运维

### 关键指标

```python
# 业务指标
- 活跃租户数
- 日活用户数（DAU）
- API调用量
- 平均响应时间
- 错误率

# 资源指标
- CPU使用率
- 内存使用率
- 数据库连接数
- Redis命中率
- 磁盘使用率

# 收入指标
- MRR (月度经常性收入)
- ARR (年度经常性收入)
- 客户流失率
- ARPU (每用户平均收入)
```

### 告警配置
```python
# 阿里云云监控
- API错误率 > 5%
- 响应时间 > 3s
- 配额使用率 > 90%
- 数据库连接数 > 80%
```

---

## 💡 最佳实践

### 1. 租户数据完全隔离
```python
# 在所有查询中强制添加tenant_id
class TenantQuery:
    def filter(self, **kwargs):
        kwargs['tenant_id'] = g.tenant_id
        return super().filter(**kwargs)
```

### 2. 优雅降级
```python
# 当某个租户超配额时，只影响该租户
if is_quota_exceeded(tenant_id):
    return throttle_response()
else:
    return normal_response()
```

### 3. 审计日志
```python
# 记录所有敏感操作
@audit_log
def delete_user(user_id):
    log_event('user_deleted', {
        'user_id': user_id,
        'operator': current_user.id,
        'tenant_id': g.tenant_id
    })
```

### 4. 数据备份
```bash
# 每日备份
0 2 * * * /backup/backup_tenant_data.sh

# 支持租户级别恢复
./restore_tenant.sh tenant-123 2025-01-20
```

---

## 🎯 总结

### 当前版本 → SaaS版本

| 特性 | 当前 | SaaS版本 |
|------|------|----------|
| **多租户** | ❌ 不支持 | ✅ 完整支持 |
| **用户认证** | ❌ 无 | ✅ JWT + 多种登录方式 |
| **权限管理** | ❌ 无 | ✅ RBAC |
| **数据隔离** | ❌ 无 | ✅ tenant_id隔离 |
| **配额管理** | ❌ 无 | ✅ 多级配额 |
| **计费系统** | ❌ 无 | ✅ 自动计费 |
| **使用统计** | ❌ 无 | ✅ 详细统计 |
| **API管理** | ❌ 无 | ✅ API Key |

### 实施成本估算

**开发成本**：
- 基础多租户：1-2人周
- 完整SaaS：4-8人周
- 高级功能：另加2-4人周

**运维成本**：
- 服务器：根据租户数量
- 数据库：PostgreSQL + Redis
- 监控：阿里云云监控（免费）

### 下一步行动

**立即可做**：
1. 设计数据库表结构
2. 实现用户认证
3. 添加租户识别

**需要您决策**：
1. 是否需要SaaS化？
2. 目标客户是谁？
3. 预算和时间？

---

**我可以帮您实现完整的多租户SaaS版本！** 💪

需要我开始实现吗？我可以：
1. 创建数据库模型
2. 实现用户认证
3. 添加租户管理
4. 配置资源配额
5. 创建管理后台

告诉我您的需求，我立即开始！🚀
