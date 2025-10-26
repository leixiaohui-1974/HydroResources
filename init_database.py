# -*- coding: utf-8 -*-
"""
数据库初始化脚本
创建所有表和初始数据
"""

from app_saas import app, db
from models import Tenant, User, Conversation, Message, MCPService, UsageStats, AuditLog
import sys

def init_database():
    """初始化数据库"""
    with app.app_context():
        print("=" * 60)
        print("🌊 HydroNet 数据库初始化")
        print("=" * 60)
        
        # 删除所有表（警告：将删除所有数据！）
        response = input("⚠️  这将删除所有现有数据！是否继续？(yes/no): ")
        if response.lower() != 'yes':
            print("已取消")
            return
        
        print("\n1. 删除现有表...")
        db.drop_all()
        print("   ✅ 完成")
        
        print("\n2. 创建新表...")
        db.create_all()
        print("   ✅ 完成")
        
        print("\n3. 创建默认租户和管理员...")
        
        # 创建系统租户
        system_tenant = Tenant(
            name='System Admin',
            subdomain='admin',
            plan='enterprise',
            status='active',
            quota_api_calls=-1,  # 无限制
            quota_storage_mb=-1,
            quota_users=-1,
            quota_mcp_services=-1
        )
        db.session.add(system_tenant)
        db.session.flush()
        
        # 创建系统管理员
        admin_user = User(
            tenant_id=system_tenant.id,
            email='admin@hydronet.com',
            username='admin',
            full_name='系统管理员',
            role='admin',
            is_active=True,
            is_verified=True
        )
        admin_user.set_password('HydroNet@2025')  # 请立即修改！
        db.session.add(admin_user)
        
        # 创建演示租户
        demo_tenant = Tenant(
            name='Demo Company',
            subdomain='demo',
            plan='pro',
            status='active'
        )
        db.session.add(demo_tenant)
        db.session.flush()
        
        # 创建演示用户
        demo_user = User(
            tenant_id=demo_tenant.id,
            email='demo@example.com',
            username='demo',
            full_name='演示用户',
            role='admin',
            is_active=True,
            is_verified=True
        )
        demo_user.set_password('demo123')
        db.session.add(demo_user)
        
        db.session.commit()
        
        print(f"   ✅ 系统管理员: admin@hydronet.com / HydroNet@2025")
        print(f"   ✅ 演示账号: demo@example.com / demo123")
        
        print("\n4. 数据库初始化完成！")
        print("\n" + "=" * 60)
        print("⚠️  安全提示:")
        print("   1. 立即修改管理员默认密码")
        print("   2. 配置.env文件中的SECRET_KEY和JWT_SECRET_KEY")
        print("   3. 生产环境使用强密码")
        print("=" * 60)

if __name__ == '__main__':
    init_database()
