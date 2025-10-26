# -*- coding: utf-8 -*-
"""
HydroNet 水网智能体系统 - 本地单机版
适合本地部署，使用SQLite + 阿里云通义千问
"""

from flask import Flask, request, jsonify, render_template, g
from flask_cors import CORS
import json
import sqlite3
from datetime import datetime
import logging
import uuid
import os

from config import Config
from qwen_client import QwenClient
from mcp_manager import MCPServiceManager

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
CORS(app)

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'hydronet_local.db')

# 初始化服务
qwen_client = QwenClient(
    api_key=Config.ALIYUN_API_KEY,
    model=Config.QWEN_MODEL
)

mcp_manager = MCPServiceManager()


# ==================== 数据库工具函数 ====================

def get_db():
    """获取数据库连接"""
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 对话表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 消息表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tokens_used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    ''')
    
    # 创建索引
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_messages_conversation 
        ON messages(conversation_id)
    ''')
    
    conn.commit()
    conn.close()
    logger.info("数据库初始化完成")


@app.teardown_appcontext
def close_db(error):
    """关闭数据库连接"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


# ==================== 主页路由 ====================

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


# ==================== 对话API ====================

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """获取对话列表"""
    try:
        db = get_db()
        cursor = db.execute('''
            SELECT c.*, COUNT(m.id) as message_count
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            LIMIT 50
        ''')
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                'id': row['id'],
                'title': row['title'],
                'message_count': row['message_count'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        return jsonify({
            'success': True,
            'conversations': conversations
        })
        
    except Exception as e:
        logger.error(f"获取对话列表失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """获取对话详情"""
    try:
        db = get_db()
        
        # 获取对话信息
        cursor = db.execute(
            'SELECT * FROM conversations WHERE id = ?',
            (conversation_id,)
        )
        conversation = cursor.fetchone()
        
        if not conversation:
            return jsonify({'error': '对话不存在'}), 404
        
        # 获取消息列表
        cursor = db.execute('''
            SELECT * FROM messages 
            WHERE conversation_id = ? 
            ORDER BY created_at ASC
        ''', (conversation_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'id': row['id'],
                'role': row['role'],
                'content': row['content'],
                'tokens_used': row['tokens_used'],
                'created_at': row['created_at']
            })
        
        return jsonify({
            'success': True,
            'conversation': {
                'id': conversation['id'],
                'title': conversation['title'],
                'created_at': conversation['created_at']
            },
            'messages': messages
        })
        
    except Exception as e:
        logger.error(f"获取对话详情失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/conversations', methods=['POST'])
def create_conversation():
    """创建新对话"""
    try:
        data = request.json
        title = data.get('title', '新对话')
        
        conversation_id = str(uuid.uuid4())
        
        db = get_db()
        db.execute('''
            INSERT INTO conversations (id, title)
            VALUES (?, ?)
        ''', (conversation_id, title))
        db.commit()
        
        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'title': title
        }), 201
        
    except Exception as e:
        logger.error(f"创建对话失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/conversations/<conversation_id>/messages', methods=['POST'])
def send_message(conversation_id):
    """发送消息"""
    try:
        data = request.json
        user_message = data.get('message')
        
        if not user_message:
            return jsonify({'error': '消息不能为空'}), 400
        
        db = get_db()
        
        # 检查对话是否存在
        cursor = db.execute(
            'SELECT * FROM conversations WHERE id = ?',
            (conversation_id,)
        )
        if not cursor.fetchone():
            return jsonify({'error': '对话不存在'}), 404
        
        # 保存用户消息
        user_msg_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO messages (id, conversation_id, role, content)
            VALUES (?, ?, ?, ?)
        ''', (user_msg_id, conversation_id, 'user', user_message))
        
        # 检查是否需要调用MCP服务
        mcp_response = mcp_manager.process_user_query(user_message)
        
        # 调用AI模型
        if mcp_response:
            system_prompt = f"基于以下水网系统数据回答用户问题：\n{json.dumps(mcp_response, ensure_ascii=False)}"
            response = qwen_client.chat(
                user_message,
                conversation_id=conversation_id,
                system_prompt=system_prompt
            )
        else:
            response = qwen_client.chat(
                user_message,
                conversation_id=conversation_id
            )
        
        # 保存AI回复
        assistant_msg_id = str(uuid.uuid4())
        tokens_used = response.get('usage', {}).get('total_tokens', 0)
        
        db.execute('''
            INSERT INTO messages (id, conversation_id, role, content, tokens_used)
            VALUES (?, ?, ?, ?, ?)
        ''', (assistant_msg_id, conversation_id, 'assistant', response['content'], tokens_used))
        
        # 更新对话时间
        db.execute('''
            UPDATE conversations 
            SET updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (conversation_id,))
        
        # 自动生成标题（如果是第一条消息）
        cursor = db.execute(
            'SELECT COUNT(*) as cnt FROM messages WHERE conversation_id = ?',
            (conversation_id,)
        )
        if cursor.fetchone()['cnt'] == 2:  # 第一对对话
            # 使用用户消息的前20个字符作为标题
            title = user_message[:20] + ('...' if len(user_message) > 20 else '')
            db.execute(
                'UPDATE conversations SET title = ? WHERE id = ?',
                (title, conversation_id)
            )
        
        db.commit()
        
        return jsonify({
            'success': True,
            'user_message': {
                'id': user_msg_id,
                'role': 'user',
                'content': user_message
            },
            'assistant_message': {
                'id': assistant_msg_id,
                'role': 'assistant',
                'content': response['content'],
                'tokens_used': tokens_used
            },
            'mcp_data': mcp_response
        })
        
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """删除对话"""
    try:
        db = get_db()
        
        # 删除消息
        db.execute('DELETE FROM messages WHERE conversation_id = ?', (conversation_id,))
        
        # 删除对话
        db.execute('DELETE FROM conversations WHERE id = ?', (conversation_id,))
        
        db.commit()
        
        return jsonify({'success': True, 'message': '对话已删除'})
        
    except Exception as e:
        logger.error(f"删除对话失败: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== MCP服务API ====================

@app.route('/api/mcp/services', methods=['GET'])
def get_mcp_services():
    """获取MCP服务列表"""
    try:
        services = mcp_manager.list_services()
        return jsonify({
            'success': True,
            'services': services
        })
    except Exception as e:
        logger.error(f"获取MCP服务列表失败: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== 系统API ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': 'local',
        'database': 'sqlite',
        'ai_model': {
            'provider': '阿里云',
            'model': Config.QWEN_MODEL,
            'available': qwen_client.is_available()
        }
    })


@app.route('/api/system/info', methods=['GET'])
def system_info():
    """系统信息"""
    # 统计数据
    db = get_db()
    cursor = db.execute('SELECT COUNT(*) as cnt FROM conversations')
    conversation_count = cursor.fetchone()['cnt']
    
    cursor = db.execute('SELECT COUNT(*) as cnt FROM messages')
    message_count = cursor.fetchone()['cnt']
    
    return jsonify({
        'name': 'HydroNet 水网智能体系统',
        'version': '2.0.0',
        'edition': 'Local (本地版)',
        'platform': 'Aliyun + Local',
        'description': '本地部署版本，使用SQLite数据库和阿里云通义千问',
        'features': [
            '本地部署',
            '无需云服务器',
            '阿里云通义千问',
            'MCP服务集成',
            '智能对话',
            'SQLite数据库'
        ],
        'ai_model': {
            'provider': '阿里云',
            'model': Config.QWEN_MODEL,
            'available': qwen_client.is_available()
        },
        'statistics': {
            'conversations': conversation_count,
            'messages': message_count,
            'mcp_services': len(mcp_manager.list_services())
        },
        'database': {
            'type': 'SQLite',
            'path': DB_PATH,
            'size_mb': round(os.path.getsize(DB_PATH) / 1024 / 1024, 2) if os.path.exists(DB_PATH) else 0
        }
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    try:
        db = get_db()
        
        # 总对话数
        cursor = db.execute('SELECT COUNT(*) as cnt FROM conversations')
        total_conversations = cursor.fetchone()['cnt']
        
        # 总消息数
        cursor = db.execute('SELECT COUNT(*) as cnt FROM messages')
        total_messages = cursor.fetchone()['cnt']
        
        # 总Token使用量
        cursor = db.execute('SELECT SUM(tokens_used) as total FROM messages')
        total_tokens = cursor.fetchone()['total'] or 0
        
        # 今天的对话数
        cursor = db.execute('''
            SELECT COUNT(*) as cnt FROM conversations 
            WHERE DATE(created_at) = DATE('now')
        ''')
        today_conversations = cursor.fetchone()['cnt']
        
        # 今天的消息数
        cursor = db.execute('''
            SELECT COUNT(*) as cnt FROM messages 
            WHERE DATE(created_at) = DATE('now')
        ''')
        today_messages = cursor.fetchone()['cnt']
        
        return jsonify({
            'success': True,
            'stats': {
                'total': {
                    'conversations': total_conversations,
                    'messages': total_messages,
                    'tokens': total_tokens
                },
                'today': {
                    'conversations': today_conversations,
                    'messages': today_messages
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'not_found', 'message': '资源不存在'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'internal_error', 'message': '服务器内部错误'}), 500


# ==================== 启动应用 ====================

if __name__ == '__main__':
    # 初始化数据库
    if not os.path.exists(DB_PATH):
        logger.info("首次运行，初始化数据库...")
        init_db()
    
    logger.info("=" * 70)
    logger.info("🌊 HydroNet 水网智能体系统 - 本地版")
    logger.info("=" * 70)
    logger.info(f"📦 版本: 本地单机版 (SQLite)")
    logger.info(f"🤖 AI模型: 阿里云通义千问 ({Config.QWEN_MODEL})")
    logger.info(f"💾 数据库: {DB_PATH}")
    logger.info(f"🔌 MCP服务: {len(mcp_manager.list_services())} 个")
    logger.info(f"🌐 访问地址: http://{Config.HOST}:{Config.PORT}")
    logger.info("=" * 70)
    logger.info("")
    logger.info("💡 特点:")
    logger.info("   ✓ 无需云服务器，本地运行")
    logger.info("   ✓ 使用SQLite，免配置数据库")
    logger.info("   ✓ 集成阿里云通义千问")
    logger.info("   ✓ 支持MCP服务扩展")
    logger.info("   ✓ 简单易用，快速启动")
    logger.info("")
    logger.info("=" * 70)
    
    # 开发环境使用debug模式
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
