# -*- coding: utf-8 -*-
"""
HydroNet 水网智能体系统 - 多租户SaaS版本
阿里云 + Web应用 + 微信公众号 + 多租户架构
"""

from flask import Flask, request, jsonify, render_template, g
from flask_cors import CORS
from flask_migrate import Migrate
import json
import xmltodict
from datetime import datetime
import logging

# 导入配置和模块
from config import Config
from models import db
from auth import jwt, require_auth, require_api_key
from quota import limiter, require_quota
from qwen_client import QwenClient
from wechat_handler import WechatMessageHandler

# 导入API路由
from api_routes import auth_bp, admin_bp, chat_bp, tenant_bp

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# 初始化扩展
db.init_app(app)
jwt.init_app(app)
limiter.init_app(app)
migrate = Migrate(app, db)

# 初始化服务
qwen_client = QwenClient(
    api_key=Config.ALIYUN_API_KEY,
    model=Config.QWEN_MODEL
)

# 初始化微信处理器（如果启用）
wechat_handler = None
if Config.WECHAT_ENABLED:
    from mcp_manager import MCPServiceManager
    mcp_manager = MCPServiceManager()
    wechat_handler = WechatMessageHandler(
        token=Config.WECHAT_TOKEN,
        qwen_client=qwen_client,
        mcp_manager=mcp_manager
    )
    logger.info("微信公众号功能已启用")

# 注册蓝图
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(tenant_bp)


# ==================== 主页路由 ====================

@app.route('/')
def index():
    """主页 - 展示聊天界面"""
    return render_template('index.html')


# ==================== 微信公众号路由 ====================

@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    """微信公众号接入点（可选）"""
    if not Config.WECHAT_ENABLED or not wechat_handler:
        return jsonify({
            'error': '微信公众号功能未启用',
            'tip': '请在.env中设置 WECHAT_ENABLED=true 并配置相关参数'
        }), 404
    
    if request.method == 'GET':
        # 微信服务器验证
        signature = request.args.get('signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        echostr = request.args.get('echostr', '')
        
        if wechat_handler.verify_signature(signature, timestamp, nonce):
            logger.info("微信验证成功")
            return echostr
        else:
            logger.warning("微信验证失败")
            return 'Invalid signature', 403
    
    elif request.method == 'POST':
        try:
            xml_data = request.data
            msg_dict = xmltodict.parse(xml_data)['xml']
            
            logger.info(f"收到微信消息")
            
            response_xml = wechat_handler.handle_message(msg_dict)
            return response_xml
            
        except Exception as e:
            logger.error(f"处理微信消息失败: {str(e)}", exc_info=True)
            return 'success'


# ==================== 系统路由 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        # 检查数据库连接
        from models import Tenant
        db.session.execute(db.select(Tenant).limit(1))
        db_status = True
    except:
        db_status = False
    
    return jsonify({
        'status': 'healthy' if db_status else 'degraded',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'database': db_status,
            'qwen': qwen_client.is_available(),
            'wechat': Config.WECHAT_ENABLED
        }
    })


@app.route('/api/system/info', methods=['GET'])
def system_info():
    """获取系统信息"""
    from models import Tenant, User
    
    return jsonify({
        'name': 'HydroNet 水网智能体系统',
        'version': '2.0.0',
        'edition': 'SaaS Multi-Tenant',
        'platform': 'Aliyun',
        'description': '基于阿里云通义千问的多租户水网智能管理系统',
        'features': [
            '多租户隔离',
            '用户认证授权',
            '配额管理',
            '审计日志',
            '智能对话',
            'MCP服务集成'
        ],
        'access_methods': {
            'web': True,
            'wechat': Config.WECHAT_ENABLED,
            'api': True
        },
        'ai_model': {
            'provider': '阿里云',
            'model': Config.QWEN_MODEL,
            'available': qwen_client.is_available()
        },
        'statistics': {
            'tenants': Tenant.query.count(),
            'users': User.query.count()
        }
    })


@app.route('/api/plans', methods=['GET'])
def get_plans():
    """获取可用套餐"""
    from quota import PLAN_LIMITS
    
    plans = {}
    for plan_name, limits in PLAN_LIMITS.items():
        plans[plan_name] = {
            'name': plan_name.capitalize(),
            'limits': limits,
            'price': {
                'free': 0,
                'basic': 99,
                'pro': 499,
                'enterprise': '联系销售'
            }.get(plan_name)
        }
    
    return jsonify({'plans': plans})


# ==================== 错误处理 ====================

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'bad_request', 'message': str(error)}), 400


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'unauthorized', 'message': '需要认证'}), 401


@app.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'forbidden', 'message': '权限不足'}), 403


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'not_found', 'message': '资源不存在'}), 404


@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({'error': 'rate_limit_exceeded', 'message': '请求过于频繁'}), 429


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'internal_error', 'message': '服务器内部错误'}), 500


# ==================== 数据库初始化命令 ====================

@app.cli.command()
def init_db():
    """初始化数据库"""
    db.create_all()
    logger.info("数据库初始化完成")


@app.cli.command()
def create_admin():
    """创建系统管理员"""
    from models import Tenant, User
    
    # 创建系统租户
    tenant = Tenant(
        name='System',
        plan='enterprise',
        status='active'
    )
    db.session.add(tenant)
    db.session.flush()
    
    # 创建管理员用户
    admin = User(
        tenant_id=tenant.id,
        email='admin@hydronet.com',
        username='admin',
        role='admin',
        is_active=True
    )
    admin.set_password('admin123')  # 请修改默认密码
    db.session.add(admin)
    
    db.session.commit()
    
    logger.info(f"系统管理员创建成功: admin@hydronet.com / admin123")
    logger.info("请立即修改默认密码！")


# ==================== 启动应用 ====================

if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("🌊 HydroNet 水网智能体系统 - 多租户SaaS版")
    logger.info("=" * 70)
    logger.info(f"🔐 认证: JWT + RBAC")
    logger.info(f"🏢 架构: 多租户隔离")
    logger.info(f"🤖 AI模型: 阿里云通义千问 ({Config.QWEN_MODEL})")
    logger.info(f"🌐 Web访问: http://{Config.HOST}:{Config.PORT}")
    if Config.WECHAT_ENABLED:
        logger.info(f"📱 微信接入: http://{Config.HOST}:{Config.PORT}/wechat ✅")
    logger.info(f"📊 数据库: {Config.SQLALCHEMY_DATABASE_URI}")
    logger.info("=" * 70)
    logger.info("")
    logger.info("💡 首次运行请执行:")
    logger.info("   flask init-db      # 初始化数据库")
    logger.info("   flask create-admin # 创建管理员")
    logger.info("")
    logger.info("=" * 70)
    
    # 开发环境使用debug模式，生产环境请使用gunicorn
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
