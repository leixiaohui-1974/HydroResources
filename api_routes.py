# -*- coding: utf-8 -*-
"""
管理后台和业务API路由
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
import json

from models import db, Tenant, User, Conversation, Message, MCPService, UsageStats, AuditLog
from auth import (
    require_auth, require_permission, require_role, audit_log,
    login_user, register_user, get_user_permissions
)
from quota import require_quota, QuotaManager, check_quota_alerts, recommend_upgrade
from qwen_client import QwenClient
from mcp_manager import MCPServiceManager
from config import Config

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')
tenant_bp = Blueprint('tenant', __name__, url_prefix='/api/tenant')


# ==================== 认证路由 ====================

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册（创建新租户）"""
    data = request.json
    
    email = data.get('email')
    password = data.get('password')
    username = data.get('username')
    tenant_name = data.get('tenant_name')
    
    if not email or not password:
        return jsonify({'error': '邮箱和密码不能为空'}), 400
    
    user, tenant = register_user(email, password, username, tenant_name)
    
    if not user:
        return jsonify({'error': tenant}), 400  # tenant包含错误信息
    
    # 自动登录
    access_token, refresh_token, user_dict = login_user(email, password)
    
    return jsonify({
        'success': True,
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user_dict,
        'tenant': tenant.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.json
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': '邮箱和密码不能为空'}), 400
    
    result = login_user(email, password)
    
    if not result:
        return jsonify({'error': '邮箱或密码错误'}), 401
    
    access_token, refresh_token, user_dict = result
    
    return jsonify({
        'success': True,
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user_dict
    })


@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """获取当前用户信息"""
    user = g.current_user
    tenant = g.tenant
    
    return jsonify({
        'user': user.to_dict(include_sensitive=True),
        'tenant': tenant.to_dict(),
        'permissions': get_user_permissions(user)
    })


@auth_bp.route('/logout', methods=['POST'])
@require_auth
@audit_log('logout')
def logout():
    """用户登出"""
    # JWT是无状态的，客户端删除token即可
    # 这里可以记录审计日志
    return jsonify({'success': True, 'message': '登出成功'})


# ==================== 对话路由 ====================

@chat_bp.route('/conversations', methods=['GET'])
@require_auth
def get_conversations():
    """获取用户的对话列表"""
    user = g.current_user
    
    # 查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 查询对话
    query = Conversation.query.filter_by(
        tenant_id=g.tenant_id,
        user_id=user.id,
        is_archived=False
    ).order_by(Conversation.updated_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'conversations': [conv.to_dict() for conv in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@chat_bp.route('/conversations/<conversation_id>', methods=['GET'])
@require_auth
def get_conversation(conversation_id):
    """获取对话详情"""
    conversation = Conversation.query.filter_by(
        id=conversation_id,
        tenant_id=g.tenant_id,
        user_id=g.current_user.id
    ).first()
    
    if not conversation:
        return jsonify({'error': '对话不存在'}), 404
    
    return jsonify(conversation.to_dict(include_messages=True))


@chat_bp.route('/conversations', methods=['POST'])
@require_auth
@require_quota('api_calls')
def create_conversation():
    """创建新对话"""
    data = request.json
    title = data.get('title', '新对话')
    
    conversation = Conversation(
        tenant_id=g.tenant_id,
        user_id=g.current_user.id,
        title=title
    )
    
    db.session.add(conversation)
    db.session.commit()
    
    return jsonify(conversation.to_dict()), 201


@chat_bp.route('/conversations/<conversation_id>/messages', methods=['POST'])
@require_auth
@require_quota('api_calls')
def send_message(conversation_id):
    """发送消息"""
    conversation = Conversation.query.filter_by(
        id=conversation_id,
        tenant_id=g.tenant_id,
        user_id=g.current_user.id
    ).first()
    
    if not conversation:
        return jsonify({'error': '对话不存在'}), 404
    
    data = request.json
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({'error': '消息不能为空'}), 400
    
    # 保存用户消息
    msg_user = Message(
        conversation_id=conversation_id,
        tenant_id=g.tenant_id,
        role='user',
        content=user_message
    )
    db.session.add(msg_user)
    
    # 调用AI（这里需要实例化或使用全局的qwen_client）
    qwen_client = QwenClient(Config.ALIYUN_API_KEY, Config.QWEN_MODEL)
    
    try:
        response = qwen_client.chat(
            user_message,
            conversation_id=conversation_id
        )
        
        # 保存AI回复
        msg_assistant = Message(
            conversation_id=conversation_id,
            tenant_id=g.tenant_id,
            role='assistant',
            content=response['content'],
            tokens_used=response.get('usage', {}).get('total_tokens', 0)
        )
        db.session.add(msg_assistant)
        
        # 更新对话时间
        conversation.updated_at = datetime.utcnow()
        
        # 记录使用量
        UsageStats.track_api_call(
            tenant_id=g.tenant_id,
            user_id=g.current_user.id,
            tokens_used=msg_assistant.tokens_used
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user_message': msg_user.to_dict(),
            'assistant_message': msg_assistant.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== 租户管理路由 ====================

@tenant_bp.route('/info', methods=['GET'])
@require_auth
def get_tenant_info():
    """获取租户信息"""
    tenant = g.tenant
    
    return jsonify({
        'tenant': tenant.to_dict(),
        'alerts': check_quota_alerts(tenant.id),
        'upgrade_recommendation': recommend_upgrade(tenant.id)
    })


@tenant_bp.route('/usage', methods=['GET'])
@require_auth
def get_tenant_usage():
    """获取租户使用量统计"""
    tenant = g.tenant
    
    # 获取时间范围
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    
    # 查询统计数据
    stats = UsageStats.query.filter(
        UsageStats.tenant_id=tenant.id,
        UsageStats.date >= start_date,
        UsageStats.date <= end_date
    ).order_by(UsageStats.date).all()
    
    return jsonify({
        'usage': [stat.to_dict() for stat in stats],
        'summary': tenant.get_usage_this_month()
    })


@tenant_bp.route('/users', methods=['GET'])
@require_auth
@require_permission('view_all_users')
def list_tenant_users():
    """列出租户所有用户"""
    users = User.query.filter_by(tenant_id=g.tenant_id).all()
    
    return jsonify({
        'users': [user.to_dict() for user in users],
        'total': len(users),
        'quota': g.tenant.quota_users
    })


@tenant_bp.route('/users', methods=['POST'])
@require_auth
@require_permission('manage_users')
@require_quota('users')
@audit_log('create_user', resource_type='user')
def create_tenant_user():
    """创建租户用户"""
    data = request.json
    
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')
    
    if not email or not password:
        return jsonify({'error': '邮箱和密码不能为空'}), 400
    
    # 检查邮箱是否已存在
    if User.query.filter_by(email=email).first():
        return jsonify({'error': '邮箱已存在'}), 400
    
    # 创建用户
    user = User(
        tenant_id=g.tenant_id,
        email=email,
        username=data.get('username'),
        role=role,
        full_name=data.get('full_name')
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'success': True, 'user': user.to_dict()}), 201


# ==================== 管理员路由 ====================

@admin_bp.route('/tenants', methods=['GET'])
@require_role('admin')
def list_all_tenants():
    """列出所有租户（仅系统管理员）"""
    # 这个API只对系统级管理员开放
    # 需要额外的系统管理员认证机制
    tenants = Tenant.query.all()
    
    return jsonify({
        'tenants': [tenant.to_dict() for tenant in tenants],
        'total': len(tenants)
    })


@admin_bp.route('/audit-logs', methods=['GET'])
@require_auth
@require_permission('view_audit_logs')
def get_audit_logs():
    """获取审计日志"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    query = AuditLog.query.filter_by(
        tenant_id=g.tenant_id
    ).order_by(AuditLog.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'logs': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    })


@admin_bp.route('/mcp-services', methods=['GET'])
@require_auth
@require_permission('view_all_services')
def list_mcp_services():
    """列出租户的MCP服务"""
    services = MCPService.query.filter_by(tenant_id=g.tenant_id).all()
    
    return jsonify({
        'services': [service.to_dict() for service in services],
        'total': len(services),
        'quota': g.tenant.quota_mcp_services
    })


@admin_bp.route('/mcp-services', methods=['POST'])
@require_auth
@require_permission('manage_services')
@require_quota('mcp_services')
@audit_log('create_mcp_service', resource_type='mcp_service')
def create_mcp_service():
    """创建MCP服务"""
    data = request.json
    
    service = MCPService(
        tenant_id=g.tenant_id,
        name=data.get('name'),
        service_type=data.get('type'),
        url=data.get('url'),
        description=data.get('description'),
        config=data.get('config', {})
    )
    
    db.session.add(service)
    db.session.commit()
    
    return jsonify({'success': True, 'service': service.to_dict()}), 201


@admin_bp.route('/stats', methods=['GET'])
@require_auth
@require_permission('view_stats')
def get_admin_stats():
    """获取管理统计数据"""
    tenant = g.tenant
    
    # 统计数据
    stats = {
        'users': {
            'total': User.query.filter_by(tenant_id=tenant.id).count(),
            'active': User.query.filter_by(tenant_id=tenant.id, is_active=True).count()
        },
        'conversations': {
            'total': Conversation.query.filter_by(tenant_id=tenant.id).count(),
            'this_month': Conversation.query.filter(
                Conversation.tenant_id == tenant.id,
                Conversation.created_at >= datetime.utcnow().replace(day=1)
            ).count()
        },
        'messages': {
            'total': Message.query.filter_by(tenant_id=tenant.id).count()
        },
        'usage': tenant.get_usage_this_month(),
        'quota': {
            'api_calls': tenant.quota_api_calls,
            'users': tenant.quota_users,
            'mcp_services': tenant.quota_mcp_services
        }
    }
    
    return jsonify(stats)
