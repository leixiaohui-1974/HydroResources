# -*- coding: utf-8 -*-
"""
HydroSIS MCP客户端
用于连接和调用HydroSIS MCP服务器的18个专业水文工具
"""

import aiohttp
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class HydroSISMCPClient:
    """
    HydroSIS MCP服务客户端
    
    连接到HydroSIS MCP服务器：
    - GitHub: https://github.com/leixiaohui-1974/HydroSIS
    - 18个专业水文建模工具
    - 完整的流域建模流程
    """
    
    def __init__(self, base_url: str = "http://localhost:8080", timeout: int = 300):
        """
        初始化客户端
        
        Args:
            base_url: MCP服务器地址（默认: http://localhost:8080）
            timeout: 请求超时时间（秒），默认5分钟
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.tools_cache = None
        
        logger.info(f"✅ HydroSIS MCP客户端初始化: {base_url}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            服务器状态信息
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ HydroSIS MCP服务健康: {data.get('tools_count')} 个工具")
                        return data
                    else:
                        logger.error(f"❌ 健康检查失败: {response.status}")
                        return {"status": "unhealthy", "code": response.status}
        except Exception as e:
            logger.error(f"❌ 连接HydroSIS服务失败: {e}")
            return {"status": "unreachable", "error": str(e)}
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        获取所有可用工具列表
        
        Returns:
            工具列表，每个工具包含name, description, category, inputSchema
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/mcp/tools") as response:
                    if response.status == 200:
                        data = await response.json()
                        tools = data.get('tools', [])
                        self.tools_cache = tools  # 缓存工具列表
                        logger.info(f"📦 获取到 {len(tools)} 个HydroSIS工具")
                        return tools
                    else:
                        error_text = await response.text()
                        raise Exception(f"获取工具列表失败 ({response.status}): {error_text}")
        except Exception as e:
            logger.error(f"❌ 获取工具列表失败: {e}")
            return []
    
    async def get_tools_by_category(self) -> Dict[str, List[Dict]]:
        """
        按分类获取工具
        
        Returns:
            {category: [tools]} 格式的字典
        """
        tools = await self.list_tools()
        
        categories = {}
        for tool in tools:
            category = tool.get('category', 'general')
            if category not in categories:
                categories[category] = []
            categories[category].append(tool)
        
        return categories
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        调用MCP工具（同步方式）
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            user_id: 用户ID
            
        Returns:
            工具执行结果
        """
        try:
            logger.info(f"🔧 调用HydroSIS工具: {tool_name}")
            
            # 添加user_id到参数中
            if 'user_id' not in arguments:
                arguments['user_id'] = user_id
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/mcp/tools/{tool_name}",
                    json=arguments,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ 工具 {tool_name} 执行成功")
                        return self._parse_mcp_result(result)
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ 工具执行失败 ({response.status}): {error_text}")
                        raise Exception(f"工具执行失败: {error_text}")
        
        except asyncio.TimeoutError:
            logger.error(f"⏰ 工具 {tool_name} 执行超时")
            raise Exception(f"工具执行超时（>{self.timeout.total}秒）")
        except Exception as e:
            logger.error(f"❌ 调用工具失败: {e}")
            raise
    
    async def submit_async_task(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_id: str = "default",
        callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        提交异步任务（适合长时间运行的操作）
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            user_id: 用户ID
            callback_url: 回调URL（可选）
            
        Returns:
            任务信息 {"task_id": "...", "status": "submitted"}
        """
        try:
            logger.info(f"📤 提交异步任务: {tool_name}")
            
            payload = {
                "tool_name": tool_name,
                "arguments": arguments,
                "user_id": user_id,
                "callback_url": callback_url
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/tasks/submit",
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        task_id = result.get('task_id')
                        logger.info(f"✅ 任务已提交: {task_id}")
                        return result
                    else:
                        error_text = await response.text()
                        raise Exception(f"提交任务失败: {error_text}")
        
        except Exception as e:
            logger.error(f"❌ 提交任务失败: {e}")
            raise
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        查询任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息，包括进度、状态、结果等
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/tasks/{task_id}") as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        raise KeyError(f"任务不存在: {task_id}")
                    else:
                        error_text = await response.text()
                        raise Exception(f"查询任务失败: {error_text}")
        
        except KeyError:
            raise
        except Exception as e:
            logger.error(f"❌ 查询任务状态失败: {e}")
            raise
    
    async def wait_for_task(
        self,
        task_id: str,
        poll_interval: float = 2.0,
        max_wait: float = 600.0
    ) -> Dict[str, Any]:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            poll_interval: 轮询间隔（秒）
            max_wait: 最大等待时间（秒）
            
        Returns:
            任务最终状态和结果
        """
        start_time = datetime.now()
        
        while True:
            # 检查超时
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > max_wait:
                raise TimeoutError(f"等待任务超时（>{max_wait}秒）")
            
            # 查询状态
            status = await self.get_task_status(task_id)
            current_status = status.get('status')
            progress = status.get('progress', 0)
            
            logger.info(f"⏳ 任务 {task_id}: {current_status} ({progress:.1f}%)")
            
            # 检查是否完成
            if current_status in ['completed', 'failed', 'cancelled']:
                if current_status == 'completed':
                    logger.info(f"✅ 任务完成: {task_id}")
                else:
                    logger.error(f"❌ 任务失败/取消: {task_id}")
                return status
            
            # 等待
            await asyncio.sleep(poll_interval)
    
    def _parse_mcp_result(self, mcp_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析MCP标准响应格式
        
        MCP响应格式:
        {
            "content": [{"type": "text", "text": "..."}],
            "isError": false,
            "metadata": {...}
        }
        
        Returns:
            解析后的结果字典
        """
        content_blocks = mcp_response.get('content', [])
        is_error = mcp_response.get('isError', False)
        metadata = mcp_response.get('metadata', {})
        
        # 提取文本内容
        result_text = ""
        for block in content_blocks:
            if block.get('type') == 'text':
                result_text += block.get('text', '')
        
        # 尝试解析JSON
        try:
            import json
            result_data = json.loads(result_text) if result_text else {}
        except:
            result_data = {"raw_text": result_text}
        
        return {
            "status": "error" if is_error else "success",
            "data": result_data,
            "metadata": metadata,
            "raw_response": mcp_response
        }


# 工具分类常量
HYDROSIS_TOOL_CATEGORIES = {
    "project_management": "项目管理",
    "gis_processing": "GIS处理",
    "data_management": "数据管理",
    "model_configuration": "模型配置",
    "simulation": "水文模拟",
    "calibration": "参数校准",
    "analysis": "结果分析",
    "visualization": "可视化"
}


# HydroSIS 18个工具列表（参考）
HYDROSIS_TOOLS_REFERENCE = [
    # 项目管理 (3个)
    {"name": "create_project", "description": "创建新的水文模拟项目", "category": "project_management"},
    {"name": "list_projects", "description": "列出用户的所有项目", "category": "project_management"},
    {"name": "get_project", "description": "获取项目详细信息", "category": "project_management"},
    
    # GIS处理 (2个)
    {"name": "delineate_watershed", "description": "流域划分（基于DEM和汇水点）", "category": "gis_processing"},
    {"name": "generate_gis_report", "description": "生成GIS分析报告", "category": "visualization"},
    
    # 数据管理 (1个)
    {"name": "upload_forcing_data", "description": "上传气象驱动数据", "category": "data_management"},
    
    # 模型配置 (2个)
    {"name": "configure_runoff_model", "description": "配置产流模型（SCS/XinAnJiang/HBV等）", "category": "model_configuration"},
    {"name": "configure_routing", "description": "配置汇流方法", "category": "model_configuration"},
    
    # 模拟 (1个)
    {"name": "run_simulation", "description": "运行水文模拟", "category": "simulation"},
    
    # 校准 (1个)
    {"name": "calibrate_parameters", "description": "参数自动校准", "category": "calibration"},
    
    # 分析 (1个)
    {"name": "analyze_results", "description": "模拟结果分析", "category": "analysis"},
    
    # 还有其他工具...
]


# 便捷函数
async def create_hydrosis_client(
    server_url: str = "http://localhost:8080"
) -> HydroSISMCPClient:
    """
    创建并测试HydroSIS MCP客户端
    
    Args:
        server_url: MCP服务器地址
        
    Returns:
        已初始化的客户端
    """
    client = HydroSISMCPClient(server_url)
    
    # 健康检查
    health = await client.health_check()
    if health.get('status') != 'healthy':
        logger.warning(f"⚠️ HydroSIS服务可能不可用: {health}")
    
    return client


# 使用示例
async def example_usage():
    """使用示例"""
    
    # 1. 创建客户端
    client = await create_hydrosis_client("http://localhost:8080")
    
    # 2. 列出所有工具
    tools = await client.list_tools()
    print(f"可用工具: {len(tools)} 个")
    
    # 3. 按分类查看
    by_category = await client.get_tools_by_category()
    for category, category_tools in by_category.items():
        print(f"\n{category}: {len(category_tools)} 个工具")
        for tool in category_tools:
            print(f"  - {tool['name']}: {tool['description']}")
    
    # 4. 调用工具（同步）
    try:
        result = await client.call_tool(
            "create_project",
            {
                "project_name": "我的测试项目",
                "description": "HydroNet集成测试",
                "template": "basic"
            },
            user_id="hydronet_user"
        )
        print(f"\n项目创建结果: {result}")
    except Exception as e:
        print(f"调用失败: {e}")
    
    # 5. 提交异步任务
    task = await client.submit_async_task(
        "run_simulation",
        {
            "project_id": "project-123",
            "generate_report": True
        },
        user_id="hydronet_user"
    )
    print(f"\n任务ID: {task['task_id']}")
    
    # 6. 等待任务完成
    result = await client.wait_for_task(task['task_id'], poll_interval=2.0, max_wait=300.0)
    print(f"任务结果: {result}")


if __name__ == "__main__":
    asyncio.run(example_usage())
