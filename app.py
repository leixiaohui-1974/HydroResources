# -*- coding: utf-8 -*-
"""
HydroNet 微信公众号Web应用 - 主应用文件
集成腾讯元宝大模型和MCP服务
"""

from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import hashlib
import xmltodict
import time
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

from config import Config
from mcp_manager import MCPServiceManager
from hunyuan_client import HunyuanClient
from wechat_handler import WechatMessageHandler

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

# 初始化各个服务
mcp_manager = MCPServiceManager()
hunyuan_client = HunyuanClient(
    secret_id=Config.TENCENT_SECRET_ID,
    secret_key=Config.TENCENT_SECRET_KEY
)
wechat_handler = WechatMessageHandler(
    token=Config.WECHAT_TOKEN,
    hunyuan_client=hunyuan_client,
    mcp_manager=mcp_manager
)


@app.route('/')
def index():
    """主页 - 展示聊天界面"""
    return render_template('index.html')


@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    """
    微信公众号接入点
    GET: 验证服务器地址
    POST: 处理用户消息
    """
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
        # 处理用户消息
        try:
            xml_data = request.data
            msg_dict = xmltodict.parse(xml_data)['xml']
            
            logger.info(f"收到消息: {msg_dict}")
            
            response_xml = wechat_handler.handle_message(msg_dict)
            return response_xml
            
        except Exception as e:
            logger.error(f"处理消息失败: {str(e)}", exc_info=True)
            return 'success'


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Web聊天接口 - 用于网页端直接对话
    """
    try:
        data = request.json
        user_message = data.get('message', '')
        conversation_id = data.get('conversation_id', None)
        
        if not user_message:
            return jsonify({'error': '消息不能为空'}), 400
        
        # 检查是否需要调用MCP服务
        mcp_response = mcp_manager.process_user_query(user_message)
        
        # 调用腾讯元宝大模型
        if mcp_response:
            # 如果有MCP服务响应，将其作为上下文传递给大模型
            system_prompt = f"基于以下水网系统数据回答用户问题：\n{json.dumps(mcp_response, ensure_ascii=False)}"
            response = hunyuan_client.chat(
                user_message,
                conversation_id=conversation_id,
                system_prompt=system_prompt
            )
        else:
            # 直接对话
            response = hunyuan_client.chat(
                user_message,
                conversation_id=conversation_id
            )
        
        return jsonify({
            'success': True,
            'message': response['content'],
            'conversation_id': response['conversation_id'],
            'mcp_data': mcp_response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"聊天接口错误: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/mcp/services', methods=['GET'])
def get_mcp_services():
    """获取所有可用的MCP服务列表"""
    try:
        services = mcp_manager.list_services()
        return jsonify({
            'success': True,
            'services': services
        })
    except Exception as e:
        logger.error(f"获取MCP服务列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/mcp/services/<service_name>', methods=['POST'])
def call_mcp_service(service_name):
    """直接调用指定的MCP服务"""
    try:
        data = request.json
        params = data.get('params', {})
        
        result = mcp_manager.call_service(service_name, params)
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"调用MCP服务 {service_name} 失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/mcp/register', methods=['POST'])
def register_mcp_service():
    """注册新的MCP服务"""
    try:
        data = request.json
        service_name = data.get('name')
        service_url = data.get('url')
        service_description = data.get('description', '')
        service_type = data.get('type', 'general')
        
        if not service_name or not service_url:
            return jsonify({
                'success': False,
                'error': '服务名称和URL不能为空'
            }), 400
        
        mcp_manager.register_service(
            name=service_name,
            url=service_url,
            description=service_description,
            service_type=service_type
        )
        
        return jsonify({
            'success': True,
            'message': f'服务 {service_name} 注册成功'
        })
        
    except Exception as e:
        logger.error(f"注册MCP服务失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'hunyuan': hunyuan_client.is_available(),
            'mcp': mcp_manager.get_health_status()
        }
    })


@app.route('/api/system/info', methods=['GET'])
def system_info():
    """获取系统信息"""
    return jsonify({
        'name': 'HydroNet 水网智能体系统',
        'version': '1.0.0',
        'description': '基于腾讯元宝大模型和MCP服务的水网智能管理系统',
        'capabilities': [
            '自然语言对话',
            '水网仿真',
            '系统辨识',
            '智能调度',
            '控制优化',
            '性能测试'
        ],
        'mcp_services_count': len(mcp_manager.list_services())
    })


if __name__ == '__main__':
    logger.info("启动 HydroNet 微信公众号Web应用...")
    logger.info(f"可用MCP服务: {len(mcp_manager.list_services())} 个")
    
    # 开发环境使用debug模式，生产环境请使用gunicorn等WSGI服务器
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
