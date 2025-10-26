# -*- coding: utf-8 -*-
"""
增强版通义千问客户端 - 支持Function Calling和流式响应
参考HydroSIS云服务架构方案中的ChatService设计
"""

import json
import logging
from typing import Dict, List, Optional, AsyncGenerator, Callable
import dashscope
from dashscope import Generation
from http import HTTPStatus

logger = logging.getLogger(__name__)


class QwenChatService:
    """
    增强版通义千问对话服务
    支持：
    1. Function Calling (工具调用)
    2. 流式响应
    3. MCP工具集成
    4. 对话历史管理
    """
    
    def __init__(self, api_key: str, model: str = "qwen-plus", mcp_manager=None):
        """
        初始化对话服务
        
        Args:
            api_key: 阿里云API密钥
            model: 模型名称 (qwen-turbo/qwen-plus/qwen-max)
            mcp_manager: MCP服务管理器实例
        """
        if not api_key or api_key == "your-api-key":
            raise ValueError("请配置有效的阿里云API密钥")
        
        dashscope.api_key = api_key
        self.model = model
        self.mcp_manager = mcp_manager
        
        # 对话历史存储 {conversation_id: messages}
        self.conversations: Dict[str, List[Dict]] = {}
        
        logger.info(f"✅ 通义千问对话服务初始化成功 - 模型: {model}")
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是HydroNet水网智能助手，专门帮助用户进行水网分析和管理。

你可以使用以下专业工具：
- simulation: 水网仿真模拟（预测流量、水位、压力等）
- identification: 系统辨识（识别管网参数、校准模型）
- scheduling: 优化调度（生成最优调度方案，降低能耗）
- control: 控制策略（设计PID、MPC等控制器）
- testing: 性能测试（评估系统可靠性和效率）

**重要指导原则**：
1. 当用户询问具体的计算、分析任务时，主动调用相应工具
2. 解释清楚每个工具的用途和所需参数
3. 对工具返回的结果进行专业解读
4. 用简洁、专业、友好的中文回答

**示例场景**：
- 用户说"帮我模拟一下水网运行"→ 调用simulation工具
- 用户说"优化调度方案"→ 调用scheduling工具
- 用户说"设计一个PID控制器"→ 调用control工具"""
    
    def _get_mcp_tools(self) -> List[Dict]:
        """获取MCP工具列表（转换为通义千问格式）"""
        if not self.mcp_manager:
            return []
        
        mcp_services = self.mcp_manager.get_tools_list()
        
        # 转换为通义千问Function格式
        tools = []
        for service in mcp_services:
            tool = {
                "type": "function",
                "function": {
                    "name": service['name'],
                    "description": service['description'],
                    "parameters": service.get('parameters', {
                        "type": "object",
                        "properties": {},
                        "required": []
                    })
                }
            }
            tools.append(tool)
        
        logger.info(f"📦 加载了 {len(tools)} 个MCP工具")
        return tools
    
    async def chat_stream(
        self,
        user_id: str,
        conversation_id: str,
        message: str,
        on_chunk: Optional[Callable] = None
    ) -> AsyncGenerator[Dict, None]:
        """
        流式对话（支持工具调用）
        
        Args:
            user_id: 用户ID
            conversation_id: 对话ID
            message: 用户消息
            on_chunk: 回调函数（处理每个chunk）
            
        Yields:
            消息chunk字典:
            - type: 'text' | 'tool_call' | 'tool_result' | 'complete'
            - content: 内容
            - tool_name: 工具名称（仅tool_call/tool_result）
            - status: running | completed | failed
        """
        try:
            # 1. 初始化对话历史
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = [
                    {"role": "system", "content": self._build_system_prompt()}
                ]
            
            # 2. 添加用户消息
            self.conversations[conversation_id].append({
                "role": "user",
                "content": message
            })
            
            # 3. 获取MCP工具列表
            tools = self._get_mcp_tools()
            
            # 4. 调用通义千问（流式 + Function Calling）
            logger.info(f"💬 用户 {user_id} 发送消息: {message[:50]}...")
            
            responses = Generation.call(
                model=self.model,
                messages=self.conversations[conversation_id],
                tools=tools if tools else None,
                result_format='message',
                stream=True,
                incremental_output=True
            )
            
            # 5. 处理响应流
            assistant_content = ""
            tool_calls = []
            
            for response in responses:
                if response.status_code == HTTPStatus.OK:
                    choice = response.output.choices[0]
                    message_obj = choice.message
                    
                    # 处理工具调用
                    if hasattr(message_obj, 'tool_calls') and message_obj.tool_calls:
                        for tool_call in message_obj.tool_calls:
                            tool_name = tool_call.function.name
                            tool_args = json.loads(tool_call.function.arguments)
                            
                            logger.info(f"🔧 调用工具: {tool_name}")
                            
                            # 通知前端工具调用开始
                            chunk = {
                                'type': 'tool_call',
                                'tool_name': tool_name,
                                'status': 'running',
                                'arguments': tool_args
                            }
                            
                            if on_chunk:
                                on_chunk(chunk)
                            yield chunk
                            
                            # 执行MCP工具
                            try:
                                result = await self.mcp_manager.call_tool(
                                    tool_name,
                                    tool_args,
                                    user_id=user_id
                                )
                                
                                logger.info(f"✅ 工具 {tool_name} 执行成功")
                                
                                # 通知前端工具执行完成
                                result_chunk = {
                                    'type': 'tool_result',
                                    'tool_name': tool_name,
                                    'status': 'completed',
                                    'result': result
                                }
                                
                                if on_chunk:
                                    on_chunk(result_chunk)
                                yield result_chunk
                                
                                # 保存工具调用结果
                                tool_calls.append({
                                    "tool_call_id": tool_call.id,
                                    "role": "tool",
                                    "name": tool_name,
                                    "content": json.dumps(result, ensure_ascii=False)
                                })
                                
                            except Exception as e:
                                logger.error(f"❌ 工具 {tool_name} 执行失败: {e}")
                                error_chunk = {
                                    'type': 'tool_result',
                                    'tool_name': tool_name,
                                    'status': 'failed',
                                    'error': str(e)
                                }
                                if on_chunk:
                                    on_chunk(error_chunk)
                                yield error_chunk
                    
                    # 处理文本内容（流式输出）
                    if hasattr(message_obj, 'content') and message_obj.content:
                        delta_content = message_obj.content
                        if delta_content:
                            assistant_content += delta_content
                            
                            text_chunk = {
                                'type': 'text',
                                'content': delta_content
                            }
                            
                            if on_chunk:
                                on_chunk(text_chunk)
                            yield text_chunk
                else:
                    logger.error(f"API调用失败: {response.code} - {response.message}")
                    raise Exception(f"API调用失败: {response.message}")
            
            # 6. 如果有工具调用，需要再次调用LLM生成最终回答
            if tool_calls:
                logger.info(f"🔄 基于工具结果生成最终回答...")
                
                # 将工具调用和结果添加到历史
                messages_with_tools = self.conversations[conversation_id].copy()
                messages_with_tools.append({
                    "role": "assistant",
                    "content": "",
                    "tool_calls": tool_calls
                })
                messages_with_tools.extend(tool_calls)
                
                # 再次调用LLM
                final_responses = Generation.call(
                    model=self.model,
                    messages=messages_with_tools,
                    result_format='message',
                    stream=True,
                    incremental_output=True
                )
                
                final_content = ""
                for response in final_responses:
                    if response.status_code == HTTPStatus.OK:
                        choice = response.output.choices[0]
                        if hasattr(choice.message, 'content') and choice.message.content:
                            delta = choice.message.content
                            final_content += delta
                            
                            text_chunk = {
                                'type': 'text',
                                'content': delta
                            }
                            
                            if on_chunk:
                                on_chunk(text_chunk)
                            yield text_chunk
                
                assistant_content = final_content
            
            # 7. 保存助手回复到历史
            self.conversations[conversation_id].append({
                "role": "assistant",
                "content": assistant_content
            })
            
            # 8. 限制历史长度
            self._trim_history(conversation_id, max_messages=30)
            
            # 9. 发送完成信号
            complete_chunk = {
                'type': 'complete',
                'conversation_id': conversation_id
            }
            if on_chunk:
                on_chunk(complete_chunk)
            yield complete_chunk
            
            logger.info(f"✅ 对话完成: {conversation_id}")
            
        except Exception as e:
            logger.error(f"❌ 对话处理失败: {e}", exc_info=True)
            error_chunk = {
                'type': 'error',
                'error': str(e)
            }
            if on_chunk:
                on_chunk(error_chunk)
            yield error_chunk
    
    def _trim_history(self, conversation_id: str, max_messages: int = 30):
        """限制对话历史长度"""
        if conversation_id in self.conversations:
            messages = self.conversations[conversation_id]
            if len(messages) > max_messages:
                # 保留系统消息和最近的对话
                system_msgs = [m for m in messages if m.get("role") == "system"]
                recent_msgs = messages[-max_messages:]
                self.conversations[conversation_id] = system_msgs + recent_msgs
                logger.info(f"📝 对话历史已裁剪至 {max_messages} 条")
    
    def clear_conversation(self, conversation_id: str):
        """清除对话历史"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"🗑️ 已清除对话历史: {conversation_id}")
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """获取对话历史"""
        return self.conversations.get(conversation_id, [])
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return bool(dashscope.api_key and dashscope.api_key != "your-api-key")


# 兼容旧版本的简单客户端类
class QwenClient:
    """简单版通义千问客户端（向后兼容）"""
    
    def __init__(self, api_key: str, model: str = "qwen-turbo"):
        self.service = QwenChatService(api_key, model)
        self.model = model
        self.api_key = api_key
    
    def is_available(self) -> bool:
        return self.service.is_available()
    
    def chat(self, message: str, conversation_id: Optional[str] = None, 
             system_prompt: Optional[str] = None, **kwargs) -> Dict:
        """同步chat方法（为了兼容）"""
        import asyncio
        import uuid
        
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # 简单实现：收集所有流式响应
        content = ""
        
        async def collect_stream():
            nonlocal content
            user_id = kwargs.get('user_id', 'default')
            async for chunk in self.service.chat_stream(user_id, conversation_id, message):
                if chunk['type'] == 'text':
                    content += chunk['content']
        
        # 运行异步函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(collect_stream())
        
        return {
            'content': content,
            'conversation_id': conversation_id,
            'model': self.model
        }
