# -*- coding: utf-8 -*-
"""
微信公众号消息处理器 - 阿里云版本
使用阿里云通义千问大模型
"""

import hashlib
import time
import logging
from typing import Dict, Optional
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


class WechatMessageHandler:
    """微信消息处理器"""
    
    def __init__(self, token: str, qwen_client, mcp_manager):
        """
        初始化消息处理器
        
        Args:
            token: 微信公众号Token
            qwen_client: 阿里云通义千问客户端
            mcp_manager: MCP服务管理器
        """
        self.token = token
        self.qwen_client = qwen_client
        self.mcp_manager = mcp_manager
        
        # 用户会话管理
        self.user_sessions = {}
        
        logger.info("微信消息处理器初始化完成（使用阿里云通义千问）")
    
    def verify_signature(self, signature: str, timestamp: str, nonce: str) -> bool:
        """
        验证微信服务器签名
        
        Args:
            signature: 微信加密签名
            timestamp: 时间戳
            nonce: 随机数
            
        Returns:
            验证是否通过
        """
        try:
            # 将token、timestamp、nonce三个参数进行字典序排序
            tmp_list = [self.token, timestamp, nonce]
            tmp_list.sort()
            tmp_str = ''.join(tmp_list)
            
            # sha1加密
            tmp_str = hashlib.sha1(tmp_str.encode('utf-8')).hexdigest()
            
            # 验证
            return tmp_str == signature
            
        except Exception as e:
            logger.error(f"签名验证失败: {str(e)}")
            return False
    
    def handle_message(self, msg_dict: Dict) -> str:
        """
        处理微信消息
        
        Args:
            msg_dict: 消息字典
            
        Returns:
            XML格式的响应消息
        """
        try:
            msg_type = msg_dict.get('MsgType', '')
            from_user = msg_dict.get('FromUserName', '')
            to_user = msg_dict.get('ToUserName', '')
            
            logger.info(f"收到 {msg_type} 消息来自用户: {from_user}")
            
            if msg_type == 'text':
                # 处理文本消息
                content = msg_dict.get('Content', '')
                response_content = self._process_text_message(from_user, content)
                
                return self._create_text_response(
                    from_user=to_user,
                    to_user=from_user,
                    content=response_content
                )
                
            elif msg_type == 'event':
                # 处理事件消息
                event = msg_dict.get('Event', '')
                
                if event == 'subscribe':
                    # 关注事件
                    welcome_msg = """🌊 欢迎关注HydroNet水网智能体系统！

我是您的智能水网助手，基于阿里云通义千问大模型。

我可以帮您：
✅ 水网仿真与预测
✅ 系统参数辨识
✅ 智能调度优化
✅ 控制策略设计
✅ 性能测试评估

💡 使用方式：
• 直接发送问题，例如："帮我做一个水网仿真"
• 或访问Web系统获得更好的体验

📱 同时支持：
• 微信公众号（移动端）
• Web界面（桌面端）

直接发送消息开始对话吧！😊"""
                    
                    return self._create_text_response(
                        from_user=to_user,
                        to_user=from_user,
                        content=welcome_msg
                    )
                
                elif event == 'unsubscribe':
                    # 取消关注事件
                    logger.info(f"用户取消关注: {from_user}")
                    
            else:
                # 其他类型消息
                return self._create_text_response(
                    from_user=to_user,
                    to_user=from_user,
                    content="抱歉，我暂时只能处理文字消息。请发送文字和我对话！😊"
                )
            
            return 'success'
            
        except Exception as e:
            logger.error(f"处理消息失败: {str(e)}", exc_info=True)
            return 'success'
    
    def _process_text_message(self, user_id: str, content: str) -> str:
        """
        处理文本消息
        
        Args:
            user_id: 用户ID
            content: 消息内容
            
        Returns:
            响应内容
        """
        try:
            # 获取或创建用户会话
            if user_id not in self.user_sessions:
                import uuid
                self.user_sessions[user_id] = {
                    'conversation_id': str(uuid.uuid4()),
                    'created_at': time.time()
                }
            
            session = self.user_sessions[user_id]
            conversation_id = session['conversation_id']
            
            # 检查是否需要调用MCP服务
            mcp_response = self.mcp_manager.process_user_query(content)
            
            # 调用阿里云通义千问大模型
            if mcp_response:
                # 如果有MCP服务响应，将其作为上下文
                import json
                system_prompt = f"基于以下水网系统数据回答用户问题：\n{json.dumps(mcp_response, ensure_ascii=False)}"
                
                response = self.qwen_client.chat(
                    content,
                    conversation_id=conversation_id,
                    system_prompt=system_prompt
                )
            else:
                # 直接对话
                response = self.qwen_client.chat(
                    content,
                    conversation_id=conversation_id
                )
            
            # 微信消息有字数限制，如果回复太长，进行截断
            reply_content = response['content']
            max_length = 2000  # 微信消息最大长度约2048字符
            
            if len(reply_content) > max_length:
                reply_content = reply_content[:max_length] + "\n\n[回复内容较长已截断，建议访问Web系统获得完整回复]"
            
            return reply_content
            
        except Exception as e:
            logger.error(f"处理文本消息失败: {str(e)}", exc_info=True)
            return f"抱歉，处理您的消息时遇到了问题。\n\n💡 建议：\n1. 稍后再试\n2. 访问Web系统获得更稳定的服务\n\n错误信息：{str(e)[:100]}"
    
    def _create_text_response(self, from_user: str, to_user: str, content: str) -> str:
        """
        创建文本响应消息
        
        Args:
            from_user: 发送方（公众号）
            to_user: 接收方（用户）
            content: 消息内容
            
        Returns:
            XML格式的响应
        """
        timestamp = int(time.time())
        
        response_template = f"""<xml>
<ToUserName><![CDATA[{to_user}]]></ToUserName>
<FromUserName><![CDATA[{from_user}]]></FromUserName>
<CreateTime>{timestamp}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>"""
        
        return response_template
    
    def clear_user_session(self, user_id: str):
        """清除用户会话"""
        if user_id in self.user_sessions:
            conversation_id = self.user_sessions[user_id]['conversation_id']
            self.qwen_client.clear_conversation(conversation_id)
            del self.user_sessions[user_id]
            logger.info(f"已清除用户会话: {user_id}")
