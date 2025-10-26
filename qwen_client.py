# -*- coding: utf-8 -*-
"""
阿里云通义千问大模型客户端
"""

import json
import logging
from typing import Dict, List, Optional
import requests
from http import HTTPStatus

logger = logging.getLogger(__name__)


class QwenClient:
    """阿里云通义千问大模型客户端"""
    
    def __init__(self, api_key: str, model: str = "qwen-turbo"):
        """
        初始化客户端
        
        Args:
            api_key: 阿里云API密钥
            model: 模型名称，可选：qwen-turbo, qwen-plus, qwen-max
        """
        self.api_key = api_key
        self.model = model
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        
        # 对话历史存储 {conversation_id: [messages]}
        self.conversations: Dict[str, List[Dict]] = {}
        
        logger.info(f"阿里云通义千问客户端初始化成功 - 模型: {model}")
    
    def is_available(self) -> bool:
        """检查客户端是否可用"""
        return bool(self.api_key and self.api_key != "your-api-key")
    
    def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict:
        """
        发送聊天消息
        
        Args:
            message: 用户消息
            conversation_id: 对话ID，用于保持上下文
            system_prompt: 系统提示词
            temperature: 温度参数 0-2
            max_tokens: 最大token数
            
        Returns:
            包含模型响应的字典
        """
        if not self.is_available():
            raise Exception("阿里云通义千问客户端未配置，请设置ALIYUN_API_KEY")
        
        try:
            # 生成或获取对话ID
            if conversation_id is None:
                import uuid
                conversation_id = str(uuid.uuid4())
            
            # 获取对话历史
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []
                
                # 添加系统提示词
                if system_prompt:
                    self.conversations[conversation_id].append({
                        "role": "system",
                        "content": system_prompt
                    })
                else:
                    # 默认系统提示词
                    default_prompt = """你是HydroNet水网智能体系统的AI助手。你具备以下能力：

1. 💧 水网仿真：可以模拟水网运行情况，预测水位、流量等参数
2. 🔍 系统辨识：识别水网系统特性和参数，进行模型校准
3. 📊 智能调度：优化水资源调度方案，提高效率降低能耗
4. 🎮 控制优化：设计和优化水网控制策略，如PID、MPC等
5. ✅ 性能测试：测试和评估系统性能，提供改进建议

请用专业、友好、简洁的方式回答用户关于水网管理的问题。当用户需要执行具体任务时：
- 先确认需求和参数
- 说明将调用的服务
- 给出操作建议
- 提供结果解读

保持回答的专业性和实用性。"""
                    self.conversations[conversation_id].append({
                        "role": "system",
                        "content": default_prompt
                    })
            
            # 添加用户消息
            self.conversations[conversation_id].append({
                "role": "user",
                "content": message
            })
            
            # 构建请求
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "input": {
                    "messages": self.conversations[conversation_id]
                },
                "parameters": {
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": 0.9
                }
            }
            
            # 调用API
            logger.info(f"发送消息到通义千问: {message[:50]}...")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # 检查响应
            if response.status_code != HTTPStatus.OK:
                error_msg = f"API调用失败: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # 解析响应
            result = response.json()
            
            if result.get('output') and result['output'].get('choices'):
                assistant_message = result['output']['choices'][0]['message']['content']
                
                # 保存助手回复到历史
                self.conversations[conversation_id].append({
                    "role": "assistant",
                    "content": assistant_message
                })
                
                # 限制历史长度
                max_history = 20  # 保留最近20条消息
                if len(self.conversations[conversation_id]) > max_history:
                    # 保留系统消息和最近的对话
                    system_msgs = [m for m in self.conversations[conversation_id] if m["role"] == "system"]
                    recent_msgs = self.conversations[conversation_id][-max_history:]
                    self.conversations[conversation_id] = system_msgs + recent_msgs
                
                logger.info(f"收到模型响应: {assistant_message[:50]}...")
                
                return {
                    'content': assistant_message,
                    'conversation_id': conversation_id,
                    'model': self.model,
                    'usage': result.get('usage', {}),
                    'finish_reason': result['output']['choices'][0].get('finish_reason', 'stop')
                }
            else:
                raise Exception(f"模型响应格式异常: {result}")
            
        except requests.exceptions.Timeout:
            logger.error("调用通义千问超时")
            raise Exception("模型调用超时，请稍后重试")
        except requests.exceptions.RequestException as e:
            logger.error(f"调用通义千问失败: {str(e)}", exc_info=True)
            raise Exception(f"模型调用失败: {str(e)}")
        except Exception as e:
            logger.error(f"处理消息失败: {str(e)}", exc_info=True)
            raise
    
    def clear_conversation(self, conversation_id: str):
        """清除对话历史"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"已清除对话历史: {conversation_id}")
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """获取对话历史"""
        return self.conversations.get(conversation_id, [])
    
    def get_models_info(self) -> Dict:
        """获取可用模型信息"""
        return {
            "qwen-turbo": {
                "name": "通义千问-Turbo",
                "description": "快速响应，适合日常对话",
                "max_tokens": 6000,
                "free_quota": "每天100万tokens"
            },
            "qwen-plus": {
                "name": "通义千问-Plus",
                "description": "平衡性能，适合复杂任务",
                "max_tokens": 30000,
                "pricing": "按量付费"
            },
            "qwen-max": {
                "name": "通义千问-Max",
                "description": "最强性能，适合专业场景",
                "max_tokens": 30000,
                "pricing": "按量付费"
            }
        }
