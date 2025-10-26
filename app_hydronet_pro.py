# -*- coding: utf-8 -*-
"""
HydroNet Pro - 增强版水网智能体系统
集成通义千问Function Calling + MCP服务 + 用户系统
参考HydroSIS云服务架构方案实现
"""

from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import sqlite3
from datetime import datetime, timedelta
import logging
import uuid
import os
import asyncio
from functools import wraps

from config import Config
from qwen_client_enhanced import QwenChatService
from mcp_manager_enhanced import MCPServiceManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY
CORS(app, resources={r"/api/*": {"origins": "*"}})

# SocketIO for WebSocket
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'hydronet_pro.db')

# 初始化MCP管理器
mcp_manager = MCPServiceManager()

# 初始化通义千问服务
qwen_service = QwenChatService(
    api_key=Config.ALIYUN_API_KEY,
    model=Config.QWEN_MODEL,
    mcp_manager=mcp_manager
)

logger.info("=" * 70)
logger.info("🌊 HydroNet Pro - 增强版水网智能体系统")
logger.info("=" * 70)
logger.info(f"✅ 通义千问服务已初始化 - 模型: {Config.QWEN_MODEL}")
logger.info(f"✅ MCP服务管理器已初始化 - {len(mcp_manager.list_services())} 个服务")
logger.info("=" * 70)


# ==================== 数据库初始化 ====================

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            tier TEXT DEFAULT 'free',
            referral_code TEXT UNIQUE,
            referred_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            trial_end_date TIMESTAMP,
            FOREIGN KEY (referred_by) REFERENCES users(id)
        )
    ''')
    
    # 对话表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # 消息表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tool_calls TEXT,
            tokens_used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    ''')
    
    # API调用记录表（用于配额管理）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_calls (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            tokens_used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # 推荐记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id TEXT PRIMARY KEY,
            referrer_id TEXT NOT NULL,
            referee_id TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            reward_amount REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            converted_at TIMESTAMP,
            FOREIGN KEY (referrer_id) REFERENCES users(id),
            FOREIGN KEY (referee_id) REFERENCES users(id)
        )
    ''')
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_calls_user_time ON api_calls(user_id, created_at)')
    
    conn.commit()
    conn.close()
    logger.info("✅ 数据库初始化完成")


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==================== 配额管理 ====================

TIER_LIMITS = {
    'free': {
        'api_calls_per_month': 100,
        'max_conversations': 10,
        'features': ['simulation']
    },
    'pro': {
        'api_calls_per_month': 10000,
        'max_conversations': 100,
        'features': ['simulation', 'identification', 'scheduling']
    },
    'enterprise': {
        'api_calls_per_month': -1,  # 无限
        'max_conversations': -1,
        'features': 'all'
    }
}


def check_quota(user_id: str) -> dict:
    """检查用户配额"""
    conn = get_db()
    
    # 获取用户信息
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return {'can_use': False, 'error': '用户不存在'}
    
    tier = user['tier']
    limit = TIER_LIMITS[tier]['api_calls_per_month']
    
    # 获取本月使用量
    first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    usage = conn.execute('''
        SELECT COUNT(*) as count 
        FROM api_calls 
        WHERE user_id = ? AND created_at >= ?
    ''', (user_id, first_day_of_month.isoformat())).fetchone()
    
    used = usage['count']
    conn.close()
    
    return {
        'can_use': used < limit or limit == -1,
        'tier': tier,
        'limit': limit,
        'used': used,
        'remaining': limit - used if limit != -1 else -1
    }


def record_api_call(user_id: str, endpoint: str, tokens: int = 0):
    """记录API调用"""
    conn = get_db()
    conn.execute('''
        INSERT INTO api_calls (id, user_id, endpoint, tokens_used, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (str(uuid.uuid4()), user_id, endpoint, tokens, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 简单实现：从请求头获取user_id
        # 生产环境应使用JWT token
        user_id = request.headers.get('X-User-ID', 'default_user')
        return f(user_id=user_id, *args, **kwargs)
    return decorated_function


# ==================== 主页路由 ====================

@app.route('/')
def index():
    """主页 - Claude风格对话界面"""
    return render_template('index_pro.html')


# ==================== 对话API（流式响应）====================

@app.route('/api/chat/stream', methods=['POST'])
@require_auth
def chat_stream(user_id):
    """流式对话API（SSE - Server-Sent Events）"""
    try:
        data = request.json
        conversation_id = data.get('conversation_id')
        message = data.get('message')
        
        if not message:
            return jsonify({'error': '消息不能为空'}), 400
        
        # 检查配额
        quota = check_quota(user_id)
        if not quota['can_use']:
            return jsonify({
                'error': 'quota_exceeded',
                'message': f'您已用完本月{quota["limit"]}次免费额度',
                'quota': quota
            }), 429
        
        # 如果没有conversation_id，创建新对话
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            conn = get_db()
            conn.execute('''
                INSERT INTO conversations (id, user_id, title)
                VALUES (?, ?, ?)
            ''', (conversation_id, user_id, message[:30] + '...'))
            conn.commit()
            conn.close()
        
        # 保存用户消息
        conn = get_db()
        conn.execute('''
            INSERT INTO messages (id, conversation_id, role, content)
            VALUES (?, ?, ?, ?)
        ''', (str(uuid.uuid4()), conversation_id, 'user', message))
        conn.commit()
        conn.close()
        
        # 记录API调用
        record_api_call(user_id, '/api/chat/stream')
        
        # 流式响应函数
        def generate():
            """生成SSE流"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            assistant_content = ""
            tool_calls_data = []
            
            async def stream_chat():
                nonlocal assistant_content, tool_calls_data
                
                async for chunk in qwen_service.chat_stream(
                    user_id,
                    conversation_id,
                    message
                ):
                    # 发送chunk到前端
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                    
                    # 收集内容用于保存
                    if chunk['type'] == 'text':
                        assistant_content += chunk.get('content', '')
                    elif chunk['type'] in ['tool_call', 'tool_result']:
                        tool_calls_data.append(chunk)
            
            # 运行异步生成器
            try:
                for item in loop.run_until_complete(
                    asyncio.gather(*(stream_chat(),))
                )[0]:
                    yield item
                
                # 保存助手回复
                conn = get_db()
                conn.execute('''
                    INSERT INTO messages (id, conversation_id, role, content, tool_calls)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    str(uuid.uuid4()),
                    conversation_id,
                    'assistant',
                    assistant_content,
                    json.dumps(tool_calls_data, ensure_ascii=False)
                ))
                
                # 更新对话时间
                conn.execute('''
                    UPDATE conversations 
                    SET updated_at = ? 
                    WHERE id = ?
                ''', (datetime.now().isoformat(), conversation_id))
                
                conn.commit()
                conn.close()
                
            except Exception as e:
                logger.error(f"流式响应错误: {e}", exc_info=True)
                error_data = {
                    'type': 'error',
                    'error': str(e)
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            finally:
                loop.close()
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        logger.error(f"对话失败: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ==================== WebSocket支持 ====================

@socketio.on('connect')
def handle_connect():
    """WebSocket连接"""
    logger.info(f"🔌 客户端连接: {request.sid}")
    emit('connected', {'status': 'ok'})


@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket断开"""
    logger.info(f"🔌 客户端断开: {request.sid}")


@socketio.on('chat_message')
def handle_chat_message(data):
    """处理WebSocket消息"""
    try:
        user_id = data.get('user_id', 'default_user')
        message = data.get('message')
        conversation_id = data.get('conversation_id')
        
        logger.info(f"💬 WS消息: {message[:50]}...")
        
        # 检查配额
        quota = check_quota(user_id)
        if not quota['can_use']:
            emit('error', {
                'type': 'quota_exceeded',
                'message': '配额已用完',
                'quota': quota
            })
            return
        
        # 创建新对话（如果需要）
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            conn = get_db()
            conn.execute('''
                INSERT INTO conversations (id, user_id, title)
                VALUES (?, ?, ?)
            ''', (conversation_id, user_id, message[:30]))
            conn.commit()
            conn.close()
            
            emit('conversation_created', {'conversation_id': conversation_id})
        
        # 保存用户消息
        conn = get_db()
        conn.execute('''
            INSERT INTO messages (id, conversation_id, role, content)
            VALUES (?, ?, ?, ?)
        ''', (str(uuid.uuid4()), conversation_id, 'user', message))
        conn.commit()
        conn.close()
        
        # 记录API调用
        record_api_call(user_id, '/ws/chat')
        
        # 异步处理对话
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        assistant_content = ""
        tool_calls_data = []
        
        async def process_chat():
            nonlocal assistant_content, tool_calls_data
            
            async for chunk in qwen_service.chat_stream(
                user_id,
                conversation_id,
                message,
                on_chunk=lambda c: emit('chat_chunk', c)
            ):
                if chunk['type'] == 'text':
                    assistant_content += chunk.get('content', '')
                elif chunk['type'] in ['tool_call', 'tool_result']:
                    tool_calls_data.append(chunk)
        
        loop.run_until_complete(process_chat())
        loop.close()
        
        # 保存助手回复
        conn = get_db()
        conn.execute('''
            INSERT INTO messages (id, conversation_id, role, content, tool_calls)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            conversation_id,
            'assistant',
            assistant_content,
            json.dumps(tool_calls_data, ensure_ascii=False)
        ))
        conn.execute('''
            UPDATE conversations SET updated_at = ? WHERE id = ?
        ''', (datetime.now().isoformat(), conversation_id))
        conn.commit()
        conn.close()
        
        emit('chat_complete', {
            'conversation_id': conversation_id,
            'message': '对话完成'
        })
        
    except Exception as e:
        logger.error(f"WS处理失败: {e}", exc_info=True)
        emit('error', {'type': 'internal_error', 'message': str(e)})


# ==================== 对话管理API ====================

@app.route('/api/conversations', methods=['GET'])
@require_auth
def get_conversations(user_id):
    """获取用户的对话列表"""
    try:
        conn = get_db()
        cursor = conn.execute('''
            SELECT c.*, COUNT(m.id) as message_count
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE c.user_id = ?
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            LIMIT 50
        ''', (user_id,))
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                'id': row['id'],
                'title': row['title'],
                'message_count': row['message_count'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        conn.close()
        return jsonify({'success': True, 'conversations': conversations})
        
    except Exception as e:
        logger.error(f"获取对话列表失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/conversations/<conversation_id>', methods=['GET'])
@require_auth
def get_conversation(user_id, conversation_id):
    """获取对话详情"""
    try:
        conn = get_db()
        
        # 验证对话属于该用户
        conv = conn.execute('''
            SELECT * FROM conversations WHERE id = ? AND user_id = ?
        ''', (conversation_id, user_id)).fetchone()
        
        if not conv:
            return jsonify({'error': '对话不存在或无权访问'}), 404
        
        # 获取消息
        messages = conn.execute('''
            SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC
        ''', (conversation_id,)).fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'conversation': dict(conv),
            'messages': [dict(m) for m in messages]
        })
        
    except Exception as e:
        logger.error(f"获取对话失败: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== 用户API ====================

@app.route('/api/user/quota', methods=['GET'])
@require_auth
def get_user_quota(user_id):
    """获取用户配额信息"""
    try:
        quota = check_quota(user_id)
        return jsonify({'success': True, 'quota': quota})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/referral', methods=['GET'])
@require_auth
def get_referral_code(user_id):
    """获取推荐码"""
    try:
        conn = get_db()
        user = conn.execute('SELECT referral_code FROM users WHERE id = ?', (user_id,)).fetchone()
        
        if not user['referral_code']:
            # 生成推荐码
            import hashlib
            code = hashlib.md5(f"{user_id}{datetime.now()}".encode()).hexdigest()[:8].upper()
            conn.execute('UPDATE users SET referral_code = ? WHERE id = ?', (code, user_id))
            conn.commit()
        else:
            code = user['referral_code']
        
        # 获取推荐统计
        stats = conn.execute('''
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'converted' THEN 1 END) as converted
            FROM referrals WHERE referrer_id = ?
        ''', (user_id,)).fetchone()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'referral_code': code,
            'stats': dict(stats)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== MCP服务API ====================

@app.route('/api/mcp/services', methods=['GET'])
def get_mcp_services():
    """获取MCP服务列表"""
    try:
        services = mcp_manager.list_services()
        return jsonify({'success': True, 'services': services})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== 系统API ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': 'pro',
        'ai_model': {
            'provider': '阿里云',
            'model': Config.QWEN_MODEL,
            'available': qwen_service.is_available()
        },
        'mcp_services': len(mcp_manager.list_services())
    })


@app.route('/api/system/info', methods=['GET'])
def system_info():
    """系统信息"""
    conn = get_db()
    
    user_count = conn.execute('SELECT COUNT(*) as cnt FROM users').fetchone()['cnt']
    conv_count = conn.execute('SELECT COUNT(*) as cnt FROM conversations').fetchone()['cnt']
    msg_count = conn.execute('SELECT COUNT(*) as cnt FROM messages').fetchone()['cnt']
    
    conn.close()
    
    return jsonify({
        'name': 'HydroNet Pro',
        'version': '3.0.0',
        'edition': 'Professional',
        'features': [
            '通义千问Function Calling',
            '流式响应',
            'MCP服务集成',
            'WebSocket实时通信',
            '用户系统',
            '配额管理',
            '推荐系统'
        ],
        'statistics': {
            'users': user_count,
            'conversations': conv_count,
            'messages': msg_count,
            'mcp_services': len(mcp_manager.list_services())
        }
    })


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'not_found'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'internal_error'}), 500


# ==================== 启动应用 ====================

if __name__ == '__main__':
    # 初始化数据库
    if not os.path.exists(DB_PATH):
        logger.info("首次运行，初始化数据库...")
        init_db()
        
        # 创建默认用户
        conn = get_db()
        default_user_id = 'default_user'
        conn.execute('''
            INSERT OR IGNORE INTO users (id, username, email, password_hash, tier)
            VALUES (?, ?, ?, ?, ?)
        ''', (default_user_id, 'demo', 'demo@hydronet.com', 'demo_hash', 'free'))
        conn.commit()
        conn.close()
        logger.info("✅ 已创建默认用户: demo")
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("🚀 HydroNet Pro 启动完成！")
    logger.info("=" * 70)
    logger.info(f"🌐 访问地址: http://{Config.HOST}:{Config.PORT}")
    logger.info(f"🤖 AI模型: {Config.QWEN_MODEL}")
    logger.info(f"🔌 MCP服务: {len(mcp_manager.list_services())} 个")
    logger.info(f"💾 数据库: {DB_PATH}")
    logger.info("=" * 70)
    logger.info("")
    logger.info("💡 新功能:")
    logger.info("   ✅ Function Calling - 智能工具调用")
    logger.info("   ✅ 流式响应 - 实时对话体验")
    logger.info("   ✅ WebSocket - 双向实时通信")
    logger.info("   ✅ 用户系统 - 认证和配额管理")
    logger.info("   ✅ MCP服务 - 5个专业水网工具")
    logger.info("")
    logger.info("=" * 70)
    
    # 使用SocketIO运行
    socketio.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        allow_unsafe_werkzeug=True
    )
