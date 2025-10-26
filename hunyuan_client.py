# -*- coding: utf-8 -*-
"""
腾讯元宝大模型客户端
支持腾讯混元大模型API调用
"""

import json
import logging
from typing import Dict, List, Optional
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.hunyuan.v20230901 import hunyuan_client, models

logger = logging.getLogger(__name__)


class HunyuanClient:
    """腾讯元宝（混元）大模型客户端"""
    
    def __init__(self, secret_id: str, secret_key: str, region: str = "ap-guangzhou"):
        """
        初始化客户端
        
        Args:
            secret_id: 腾讯云API密钥ID
            secret_key: 腾讯云API密钥Key
            region: 地域，默认广州
        """
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.region = region
        
        # 对话历史存储 {conversation_id: [messages]}
        self.conversations: Dict[str, List[Dict]] = {}
        
        try:
            # 初始化认证对象
            cred = credential.Credential(secret_id, secret_key)
            
            # 配置HTTP选项
            httpProfile = HttpProfile()
            httpProfile.endpoint = "hunyuan.tencentcloudapi.com"
            
            # 配置客户端
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            
            # 创建客户端
            self.client = hunyuan_client.HunyuanClient(cred, region, clientProfile)
            
            logger.info("腾讯元宝大模型客户端初始化成功")
            
        except Exception as e:
            logger.error(f"初始化腾讯元宝客户端失败: {str(e)}")
            self.client = None
    
    def is_available(self) -> bool:
        """检查客户端是否可用"""
        return self.client is not None
    
    def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model: str = "hunyuan-lite",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict:
        """
        发送聊天消息
        
        Args:
            message: 用户消息
            conversation_id: 对话ID，用于保持上下文
            system_prompt: 系统提示词
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            包含模型响应的字典
        """
        if not self.is_available():
            raise Exception("腾讯元宝客户端未初始化")
        
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
                        "Role": "system",
                        "Content": system_prompt
                    })
                else:
                    # 默认系统提示词
                    default_prompt = """你是HydroNet水网智能体系统的AI助手。你具备以下能力：
1. 水网仿真：可以模拟水网运行情况
2. 系统辨识：识别水网系统特性和参数
3. 智能调度：优化水资源调度方案
4. 控制优化：优化水网控制策略
5. 性能测试：测试和评估系统性能

请用专业、友好的方式回答用户关于水网管理的问题。当用户需要执行具体的仿真、辨识、调度等任务时，请识别意图并给出建议。"""
                    self.conversations[conversation_id].append({
                        "Role": "system",
                        "Content": default_prompt
                    })
            
            # 添加用户消息
            self.conversations[conversation_id].append({
                "Role": "user",
                "Content": message
            })
            
            # 构建请求
            req = models.ChatCompletionsRequest()
            params = {
                "Model": model,
                "Messages": self.conversations[conversation_id],
                "Temperature": temperature,
                "TopP": 1.0,
            }
            req.from_json_string(json.dumps(params))
            
            # 调用API
            logger.info(f"发送消息到元宝大模型: {message[:50]}...")
            resp = self.client.ChatCompletions(req)
            
            # 解析响应
            response_dict = json.loads(resp.to_json_string())
            
            if "Choices" in response_dict and len(response_dict["Choices"]) > 0:
                assistant_message = response_dict["Choices"][0]["Message"]["Content"]
                
                # 保存助手回复到历史
                self.conversations[conversation_id].append({
                    "Role": "assistant",
                    "Content": assistant_message
                })
                
                # 限制历史长度
                max_history = 20  # 保留最近20条消息
                if len(self.conversations[conversation_id]) > max_history:
                    # 保留系统消息和最近的对话
                    system_msgs = [m for m in self.conversations[conversation_id] if m["Role"] == "system"]
                    recent_msgs = self.conversations[conversation_id][-max_history:]
                    self.conversations[conversation_id] = system_msgs + recent_msgs
                
                logger.info(f"收到模型响应: {assistant_message[:50]}...")
                
                return {
                    'content': assistant_message,
                    'conversation_id': conversation_id,
                    'model': model,
                    'usage': response_dict.get('Usage', {})
                }
            else:
                raise Exception("模型响应格式异常")
            
        except Exception as e:
            logger.error(f"调用元宝大模型失败: {str(e)}", exc_info=True)
            raise Exception(f"模型调用失败: {str(e)}")
    
    def clear_conversation(self, conversation_id: str):
        """清除对话历史"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"已清除对话历史: {conversation_id}")
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """获取对话历史"""
        return self.conversations.get(conversation_id, [])
