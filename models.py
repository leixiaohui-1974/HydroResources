# -*- coding: utf-8 -*-
"""
数据库模型 - 多租户SaaS架构
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import secrets

db = SQLAlchemy()


# ==================== 租户模型 ====================

class Tenant(db.Model):
    """租户/组织模型"""
    __tablename__ = 'tenants'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    subdomain = db.Column(db.String(50), unique=True)  # 子域名
    plan = db.Column(db.String(20), default='free')  # free/basic/pro/enterprise
    status = db.Column(db.String(20), default='active')  # active/suspended/trial/cancelled
    
    # 配额
    quota_api_calls = db.Column(db.Integer, default=1000)  # 月API调用配额
    quota_storage_mb = db.Column(db.Integer, default=100)  # 存储配额(MB)
    quota_users = db.Column(db.Integer, default=1)  # 用户数配额
    quota_mcp_services = db.Column(db.Integer, default=1)  # MCP服务配额
    
    # API密钥
    api_key = db.Column(db.String(64), unique=True)
    api_secret = db.Column(db.String(128))
    
    # 设置
    settings = db.Column(db.JSON, default={})
    
    # 时间戳
    trial_ends_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    users = db.relationship('User', backref='tenant', lazy='dynamic', cascade='all, delete-orphan')
    conversations = db.relationship('Conversation', backref='tenant', lazy='dynamic', cascade='all, delete-orphan')
    mcp_services = db.relationship('MCPService', backref='tenant', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(Tenant, self).__init__(**kwargs)
        if not self.api_key:
            self.generate_api_credentials()
    
    def generate_api_credentials(self):
        """生成API密钥"""
        self.api_key = secrets.token_urlsafe(32)
        self.api_secret = secrets.token_urlsafe(64)
    
    def get_usage_this_month(self):
        """获取本月使用量"""
        from sqlalchemy import func
        today = datetime.utcnow()
        first_day = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        stats = UsageStats.query.filter(
            UsageStats.tenant_id == self.id,
            UsageStats.date >= first_day
        ).with_entities(
            func.sum(UsageStats.api_calls).label('api_calls'),
            func.sum(UsageStats.tokens_used).label('tokens_used')
        ).first()
        
        return {
            'api_calls': stats.api_calls or 0,
            'tokens_used': stats.tokens_used or 0,
            'storage_mb': 0  # TODO: 计算实际存储
        }
    
    def check_quota(self, quota_type):
        """检查配额是否已用完"""
        usage = self.get_usage_this_month()
        
        if quota_type == 'api_calls':
            return usage['api_calls'] < self.quota_api_calls
        elif quota_type == 'users':
            return self.users.count() < self.quota_users
        elif quota_type == 'mcp_services':
            return self.mcp_services.filter_by(is_active=True).count() < self.quota_mcp_services
        
        return True
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subdomain': self.subdomain,
            'plan': self.plan,
            'status': self.status,
            'quota': {
                'api_calls': self.quota_api_calls,
                'storage_mb': self.quota_storage_mb,
                'users': self.quota_users,
                'mcp_services': self.quota_mcp_services
            },
            'usage': self.get_usage_this_month(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ==================== 用户模型 ====================

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    username = db.Column(db.String(50))
    password_hash = db.Column(db.String(255))
    
    # 角色和权限
    role = db.Column(db.String(20), default='user')  # admin/user/viewer
    permissions = db.Column(db.JSON, default=[])
    
    # 状态
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    
    # 个人信息
    full_name = db.Column(db.String(100))
    avatar_url = db.Column(db.String(500))
    phone = db.Column(db.String(20))
    
    # 时间戳
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    conversations = db.relationship('Conversation', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        """检查是否有某个权限"""
        if self.role == 'admin':
            return True  # 管理员有所有权限
        return permission in self.permissions
    
    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'email': self.email,
            'username': self.username,
            'role': self.role,
            'full_name': self.full_name,
            'avatar_url': self.avatar_url,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_sensitive:
            data['permissions'] = self.permissions
        
        return data


# ==================== 对话模型 ====================

class Conversation(db.Model):
    """对话模型"""
    __tablename__ = 'conversations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    title = db.Column(db.String(200))
    is_archived = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('idx_tenant_user', 'tenant_id', 'user_id'),
    )
    
    def to_dict(self, include_messages=False):
        data = {
            'id': self.id,
            'title': self.title or '新对话',
            'is_archived': self.is_archived,
            'message_count': self.messages.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_messages:
            data['messages'] = [msg.to_dict() for msg in self.messages.order_by(Message.created_at).all()]
        
        return data


# ==================== 消息模型 ====================

class Message(db.Model):
    """消息模型"""
    __tablename__ = 'messages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = db.Column(db.String(36), db.ForeignKey('conversations.id'), nullable=False, index=True)
    tenant_id = db.Column(db.String(36), nullable=False, index=True)  # 冗余，便于查询和隔离
    
    role = db.Column(db.String(20), nullable=False)  # user/assistant/system
    content = db.Column(db.Text, nullable=False)
    tokens_used = db.Column(db.Integer, default=0)
    
    # 元数据
    metadata = db.Column(db.JSON, default={})  # 存储MCP服务调用等信息
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'tokens_used': self.tokens_used,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ==================== MCP服务模型 ====================

class MCPService(db.Model):
    """MCP服务配置模型"""
    __tablename__ = 'mcp_services'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    
    name = db.Column(db.String(100), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)  # simulation/identification/scheduling/control/testing
    url = db.Column(db.String(500))
    description = db.Column(db.Text)
    
    # 配置
    config = db.Column(db.JSON, default={})
    is_active = db.Column(db.Boolean, default=True)
    
    # 统计
    call_count = db.Column(db.Integer, default=0)
    last_called_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.service_type,
            'url': self.url,
            'description': self.description,
            'is_active': self.is_active,
            'call_count': self.call_count,
            'last_called_at': self.last_called_at.isoformat() if self.last_called_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ==================== 使用量统计模型 ====================

class UsageStats(db.Model):
    """使用量统计模型"""
    __tablename__ = 'usage_stats'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), index=True)
    
    date = db.Column(db.Date, nullable=False, index=True)
    
    # 使用量
    api_calls = db.Column(db.Integer, default=0)
    tokens_used = db.Column(db.Integer, default=0)
    storage_used_mb = db.Column(db.Integer, default=0)
    
    __table_args__ = (
        db.Index('idx_tenant_date', 'tenant_id', 'date'),
        db.UniqueConstraint('tenant_id', 'user_id', 'date', name='uq_tenant_user_date'),
    )
    
    @staticmethod
    def track_api_call(tenant_id, user_id=None, tokens_used=0):
        """记录API调用"""
        today = datetime.utcnow().date()
        
        stat = UsageStats.query.filter_by(
            tenant_id=tenant_id,
            user_id=user_id,
            date=today
        ).first()
        
        if not stat:
            stat = UsageStats(
                tenant_id=tenant_id,
                user_id=user_id,
                date=today
            )
            db.session.add(stat)
        
        stat.api_calls += 1
        stat.tokens_used += tokens_used
        db.session.commit()
    
    def to_dict(self):
        return {
            'date': self.date.isoformat(),
            'api_calls': self.api_calls,
            'tokens_used': self.tokens_used,
            'storage_used_mb': self.storage_used_mb
        }


# ==================== 审计日志模型 ====================

class AuditLog(db.Model):
    """审计日志模型"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), nullable=False, index=True)
    user_id = db.Column(db.String(36), index=True)
    
    action = db.Column(db.String(50), nullable=False, index=True)  # login/create_user/delete_data等
    resource_type = db.Column(db.String(50))  # user/conversation/service等
    resource_id = db.Column(db.String(36))
    
    details = db.Column(db.JSON, default={})
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
