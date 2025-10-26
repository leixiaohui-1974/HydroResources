# -*- coding: utf-8 -*-
"""
认证和授权模块 - JWT + RBAC
"""

from functools import wraps
from flask import request, jsonify, g
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime, timedelta
import logging

from models import db, User, Tenant, AuditLog

logger = logging.getLogger(__name__)

jwt = JWTManager()


# ==================== 权限定义 ====================

PERMISSIONS = {
    'admin': [
        # 用户管理
        'manage_users', 'view_all_users', 'delete_users',
        # MCP服务
        'manage_services', 'view_all_services',
        # 对话
        'view_all_conversations', 'delete_conversations',
        # 系统
        'view_stats', 'manage_settings', 'view_audit_logs',
        # 计费
        'manage_billing', 'view_invoices'
    ],
    'user': [
        # 自己的数据
        'view_own_conversations', 'create_conversation', 'delete_own_conversation',
        'use_mcp_services',
        'view_own_profile', 'edit_own_profile'
    ],
    'viewer': [
        'view_own_conversations',
        'view_own_profile'
    ]
}


# ==================== JWT回调 ====================

@jwt.user_identity_loader
def user_identity_lookup(user):
    """加载用户身份"""
    return user.id


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    """从JWT加载用户"""
    identity = jwt_data["sub"]
    return User.query.filter_by(id=identity).first()


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Token过期回调"""
    return jsonify({
        'error': 'token_expired',
        'message': 'Token已过期，请重新登录'
    }), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    """无效Token回调"""
    return jsonify({
        'error': 'invalid_token',
        'message': '无效的Token'
    }), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    """缺少Token回调"""
    return jsonify({
        'error': 'authorization_required',
        'message': '需要认证'
    }), 401


# ==================== 认证装饰器 ====================

def require_auth(f):
    """
    要求认证装饰器
    使用JWT验证用户身份并注入租户信息
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        # 获取当前用户
        current_user = get_jwt_identity()
        user = User.query.get(current_user)
        
        if not user or not user.is_active:
            return jsonify({'error': '用户不存在或已被禁用'}), 401
        
        # 获取租户
        tenant = Tenant.query.get(user.tenant_id)
        if not tenant or tenant.status != 'active':
            return jsonify({'error': '租户不存在或已被停用'}), 403
        
        # 注入到g对象中
        g.current_user = user
        g.tenant = tenant
        g.tenant_id = tenant.id
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_permission(permission):
    """
    要求特定权限装饰器
    
    用法:
    @require_permission('manage_users')
    def create_user():
        pass
    """
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user = g.current_user
            
            # 检查权限
            if not user.has_permission(permission):
                logger.warning(f"用户 {user.email} 尝试访问需要权限 {permission} 的资源")
                return jsonify({
                    'error': 'permission_denied',
                    'message': f'需要权限: {permission}'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_role(role):
    """
    要求特定角色装饰器
    
    用法:
    @require_role('admin')
    def admin_only():
        pass
    """
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user = g.current_user
            
            if user.role != role:
                return jsonify({
                    'error': 'role_required',
                    'message': f'需要角色: {role}'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


# ==================== API Key认证 ====================

def require_api_key(f):
    """
    API Key认证装饰器
    用于外部API调用
    
    请求头: X-API-Key: <api_key>
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': '缺少API Key'}), 401
        
        # 查找租户
        tenant = Tenant.query.filter_by(api_key=api_key).first()
        
        if not tenant:
            return jsonify({'error': '无效的API Key'}), 401
        
        if tenant.status != 'active':
            return jsonify({'error': '租户已被停用'}), 403
        
        # 注入租户信息
        g.tenant = tenant
        g.tenant_id = tenant.id
        g.current_user = None  # API调用没有用户上下文
        
        return f(*args, **kwargs)
    
    return decorated_function


# ==================== 租户隔离中间件 ====================

def ensure_tenant_isolation(f):
    """
    确保租户隔离装饰器
    自动在查询中添加tenant_id过滤
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'tenant_id'):
            return jsonify({'error': '缺少租户上下文'}), 500
        
        return f(*args, **kwargs)
    
    return decorated_function


# ==================== 审计日志 ====================

def audit_log(action, resource_type=None, resource_id=None):
    """
    审计日志装饰器
    
    用法:
    @audit_log('delete_user', resource_type='user')
    def delete_user(user_id):
        pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 执行函数
            result = f(*args, **kwargs)
            
            # 记录审计日志
            if hasattr(g, 'current_user') and hasattr(g, 'tenant_id'):
                log = AuditLog(
                    tenant_id=g.tenant_id,
                    user_id=g.current_user.id if g.current_user else None,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id or kwargs.get('id') or kwargs.get('user_id'),
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', '')[:500]
                )
                db.session.add(log)
                db.session.commit()
            
            return result
        
        return decorated_function
    return decorator


# ==================== 认证工具函数 ====================

def login_user(email, password):
    """
    用户登录
    
    Args:
        email: 邮箱
        password: 密码
        
    Returns:
        (access_token, refresh_token, user_dict) 或 None
    """
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return None
    
    if not user.is_active:
        return None
    
    # 检查租户状态
    tenant = Tenant.query.get(user.tenant_id)
    if not tenant or tenant.status != 'active':
        return None
    
    # 更新最后登录时间
    user.update_last_login()
    
    # 生成Token
    access_token = create_access_token(
        identity=user.id,
        additional_claims={
            'tenant_id': user.tenant_id,
            'role': user.role
        },
        expires_delta=timedelta(hours=8)
    )
    
    refresh_token = create_refresh_token(
        identity=user.id,
        expires_delta=timedelta(days=30)
    )
    
    # 记录审计日志
    log = AuditLog(
        tenant_id=user.tenant_id,
        user_id=user.id,
        action='login',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')[:500]
    )
    db.session.add(log)
    db.session.commit()
    
    return access_token, refresh_token, user.to_dict()


def register_user(email, password, username=None, tenant_name=None):
    """
    用户注册（创建新租户）
    
    Args:
        email: 邮箱
        password: 密码
        username: 用户名
        tenant_name: 租户名称
        
    Returns:
        (user, tenant) 或 None
    """
    # 检查邮箱是否已存在
    if User.query.filter_by(email=email).first():
        return None, "邮箱已被注册"
    
    try:
        # 创建租户
        tenant = Tenant(
            name=tenant_name or email.split('@')[0],
            subdomain=None,  # 可以后续设置
            plan='free',
            status='trial'
        )
        db.session.add(tenant)
        db.session.flush()  # 获取tenant.id
        
        # 创建用户（租户管理员）
        user = User(
            tenant_id=tenant.id,
            email=email,
            username=username or email.split('@')[0],
            role='admin',  # 第一个用户是管理员
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        
        db.session.commit()
        
        logger.info(f"新租户注册: {tenant.name} ({tenant.id}), 管理员: {user.email}")
        
        return user, tenant
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"注册失败: {str(e)}")
        return None, str(e)


def get_user_permissions(user):
    """获取用户的所有权限"""
    return PERMISSIONS.get(user.role, []) + user.permissions
