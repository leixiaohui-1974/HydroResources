# -*- coding: utf-8 -*-
"""
配额管理和限流模块
"""

from functools import wraps
from flask import request, jsonify, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

from models import Tenant, UsageStats

logger = logging.getLogger(__name__)


# ==================== 限流器 ====================

def get_tenant_id():
    """获取当前租户ID用于限流"""
    if hasattr(g, 'tenant_id'):
        return g.tenant_id
    return get_remote_address()


limiter = Limiter(
    key_func=get_tenant_id,
    default_limits=["1000 per hour"],  # 默认限制
    storage_uri="memory://",  # 生产环境应使用Redis: redis://localhost:6379
)


# ==================== 套餐限制 ====================

PLAN_LIMITS = {
    'free': {
        'api_calls_per_month': 1000,
        'requests_per_minute': 10,
        'storage_mb': 100,
        'users': 1,
        'mcp_services': 1,
        'max_conversation_length': 10  # 对话轮数
    },
    'basic': {
        'api_calls_per_month': 10000,
        'requests_per_minute': 50,
        'storage_mb': 1000,
        'users': 5,
        'mcp_services': 5,
        'max_conversation_length': 50
    },
    'pro': {
        'api_calls_per_month': 100000,
        'requests_per_minute': 200,
        'storage_mb': 10000,
        'users': 20,
        'mcp_services': 20,
        'max_conversation_length': 100
    },
    'enterprise': {
        'api_calls_per_month': -1,  # 无限制
        'requests_per_minute': 1000,
        'storage_mb': -1,
        'users': -1,
        'mcp_services': -1,
        'max_conversation_length': -1
    }
}


# ==================== 配额管理器 ====================

class QuotaManager:
    """配额管理器"""
    
    @staticmethod
    def check_api_quota(tenant_id):
        """
        检查API调用配额
        
        Returns:
            (bool, str) - (是否通过, 错误信息)
        """
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return False, "租户不存在"
        
        # Enterprise计划无限制
        if tenant.plan == 'enterprise':
            return True, None
        
        # 获取本月使用量
        usage = tenant.get_usage_this_month()
        
        if usage['api_calls'] >= tenant.quota_api_calls:
            return False, f"API调用配额已用完 ({usage['api_calls']}/{tenant.quota_api_calls})"
        
        return True, None
    
    @staticmethod
    def check_user_quota(tenant_id):
        """检查用户数配额"""
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return False, "租户不存在"
        
        if tenant.plan == 'enterprise':
            return True, None
        
        current_users = tenant.users.filter_by(is_active=True).count()
        
        if current_users >= tenant.quota_users:
            return False, f"用户数已达上限 ({current_users}/{tenant.quota_users})"
        
        return True, None
    
    @staticmethod
    def check_mcp_service_quota(tenant_id):
        """检查MCP服务配额"""
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return False, "租户不存在"
        
        if tenant.plan == 'enterprise':
            return True, None
        
        from models import MCPService
        current_services = MCPService.query.filter_by(
            tenant_id=tenant_id,
            is_active=True
        ).count()
        
        if current_services >= tenant.quota_mcp_services:
            return False, f"MCP服务数已达上限 ({current_services}/{tenant.quota_mcp_services})"
        
        return True, None
    
    @staticmethod
    def check_storage_quota(tenant_id, size_mb):
        """检查存储配额"""
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return False, "租户不存在"
        
        if tenant.plan == 'enterprise':
            return True, None
        
        # TODO: 计算实际使用的存储
        current_storage = 0
        
        if current_storage + size_mb > tenant.quota_storage_mb:
            return False, f"存储空间不足 ({current_storage + size_mb}/{tenant.quota_storage_mb} MB)"
        
        return True, None
    
    @staticmethod
    def get_plan_limit(tenant, limit_key):
        """获取套餐限制"""
        plan_limits = PLAN_LIMITS.get(tenant.plan, PLAN_LIMITS['free'])
        return plan_limits.get(limit_key)


# ==================== 配额装饰器 ====================

def require_quota(quota_type):
    """
    要求配额装饰器
    
    Args:
        quota_type: 配额类型 (api_calls/users/mcp_services/storage)
    
    用法:
    @require_quota('api_calls')
    def api_endpoint():
        pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'tenant_id'):
                return jsonify({'error': '缺少租户上下文'}), 500
            
            # 检查配额
            if quota_type == 'api_calls':
                passed, error_msg = QuotaManager.check_api_quota(g.tenant_id)
            elif quota_type == 'users':
                passed, error_msg = QuotaManager.check_user_quota(g.tenant_id)
            elif quota_type == 'mcp_services':
                passed, error_msg = QuotaManager.check_mcp_service_quota(g.tenant_id)
            else:
                passed, error_msg = True, None
            
            if not passed:
                logger.warning(f"租户 {g.tenant_id} 配额限制: {error_msg}")
                return jsonify({
                    'error': 'quota_exceeded',
                    'message': error_msg,
                    'quota_type': quota_type
                }), 429  # 429 Too Many Requests
            
            # 记录使用量
            if quota_type == 'api_calls':
                UsageStats.track_api_call(
                    tenant_id=g.tenant_id,
                    user_id=g.current_user.id if hasattr(g, 'current_user') and g.current_user else None
                )
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def rate_limit_by_plan():
    """
    根据套餐动态限流装饰器
    
    用法:
    @rate_limit_by_plan()
    def api_endpoint():
        pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'tenant'):
                # 未认证的请求使用默认限制
                return f(*args, **kwargs)
            
            tenant = g.tenant
            limit = QuotaManager.get_plan_limit(tenant, 'requests_per_minute')
            
            # 使用Flask-Limiter的动态限制
            # 这里简化处理，实际应该集成到limiter中
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


# ==================== 配额告警 ====================

def check_quota_alerts(tenant_id):
    """
    检查配额告警
    当使用量达到80%时发送告警
    
    Returns:
        list of alert messages
    """
    tenant = Tenant.query.get(tenant_id)
    if not tenant or tenant.plan == 'enterprise':
        return []
    
    alerts = []
    usage = tenant.get_usage_this_month()
    
    # API调用告警
    if tenant.quota_api_calls > 0:
        usage_percent = (usage['api_calls'] / tenant.quota_api_calls) * 100
        if usage_percent >= 80:
            alerts.append({
                'type': 'api_calls',
                'usage_percent': usage_percent,
                'current': usage['api_calls'],
                'quota': tenant.quota_api_calls,
                'message': f"API调用量已使用 {usage_percent:.0f}%"
            })
    
    # 用户数告警
    current_users = tenant.users.filter_by(is_active=True).count()
    if tenant.quota_users > 0:
        user_percent = (current_users / tenant.quota_users) * 100
        if user_percent >= 80:
            alerts.append({
                'type': 'users',
                'usage_percent': user_percent,
                'current': current_users,
                'quota': tenant.quota_users,
                'message': f"用户数已使用 {user_percent:.0f}%"
            })
    
    return alerts


# ==================== 升级推荐 ====================

def recommend_upgrade(tenant_id):
    """
    推荐升级套餐
    
    Returns:
        dict with recommendation or None
    """
    tenant = Tenant.query.get(tenant_id)
    if not tenant:
        return None
    
    usage = tenant.get_usage_this_month()
    current_plan = tenant.plan
    
    # 如果已经是最高级别
    if current_plan == 'enterprise':
        return None
    
    # 检查是否经常超配额
    alerts = check_quota_alerts(tenant_id)
    
    if len(alerts) >= 2:  # 多个配额接近上限
        # 推荐下一个级别
        plan_order = ['free', 'basic', 'pro', 'enterprise']
        current_index = plan_order.index(current_plan)
        
        if current_index < len(plan_order) - 1:
            recommended_plan = plan_order[current_index + 1]
            return {
                'current_plan': current_plan,
                'recommended_plan': recommended_plan,
                'reason': '多个配额接近上限',
                'benefits': PLAN_LIMITS[recommended_plan]
            }
    
    return None
