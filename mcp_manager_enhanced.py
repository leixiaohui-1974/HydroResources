# -*- coding: utf-8 -*-
"""
增强版MCP服务管理器
符合标准MCP协议，支持工具注册、调用、结果序列化
参考HydroSIS云服务架构方案
"""

import os
import json
import logging
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# 尝试导入HydroSIS客户端
try:
    from hydrosis_mcp_client import HydroSISMCPClient
    HYDROSIS_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ HydroSIS MCP客户端未安装")
    HYDROSIS_AVAILABLE = False


class MCPServiceManager:
    """
    MCP服务管理器（增强版）
    
    功能：
    1. 工具注册和管理
    2. 标准MCP协议
    3. 异步工具调用
    4. 结果序列化
    5. 错误处理
    """
    
    def __init__(self):
        """初始化MCP服务管理器"""
        self.services = {}
        self._initialize_hydronet_services()
        
        # 初始化HydroSIS客户端
        self.hydrosis_client = None
        self.hydrosis_tools_cache = []
        
        if HYDROSIS_AVAILABLE and os.environ.get('HYDROSIS_MCP_ENABLED', '').lower() == 'true':
            hydrosis_url = os.environ.get('HYDROSIS_MCP_URL', 'http://localhost:8080')
            hydrosis_timeout = int(os.environ.get('HYDROSIS_MCP_TIMEOUT', '300'))
            
            try:
                self.hydrosis_client = HydroSISMCPClient(hydrosis_url, hydrosis_timeout)
                logger.info(f"✅ 已连接HydroSIS MCP服务器: {hydrosis_url}")
                logger.info(f"   HydroSIS提供18个专业水文工具")
            except Exception as e:
                logger.error(f"❌ 连接HydroSIS服务器失败: {e}")
                self.hydrosis_client = None
        else:
            if not HYDROSIS_AVAILABLE:
                logger.info("ℹ️ HydroSIS MCP客户端未安装，仅使用HydroNet工具")
            else:
                logger.info("ℹ️ HydroSIS MCP未启用（设置HYDROSIS_MCP_ENABLED=true启用）")
        
        logger.info("✅ MCP服务管理器初始化完成")
    
    def _initialize_hydronet_services(self):
        """初始化HydroNet专业服务"""
        
        # 1. 水网仿真服务
        self.services['simulation'] = {
            'name': 'simulation',
            'description': '水网仿真模拟 - 预测流量、水位、压力等运行参数',
            'url': None,  # 可配置远程服务URL
            'parameters': {
                'type': 'object',
                'properties': {
                    'network_config': {
                        'type': 'object',
                        'description': '水网配置（节点、管道拓扑）'
                    },
                    'boundary_conditions': {
                        'type': 'object',
                        'description': '边界条件（入流、出流、水位等）',
                        'properties': {
                            'inflow': {'type': 'number', 'description': '入流量 (m³/h)'},
                            'pressure': {'type': 'number', 'description': '压力 (MPa)'}
                        }
                    },
                    'duration': {
                        'type': 'number',
                        'description': '模拟时长（小时）',
                        'minimum': 1,
                        'maximum': 168
                    }
                },
                'required': ['boundary_conditions', 'duration']
            },
            'examples': [
                {
                    'description': '基础仿真示例',
                    'parameters': {
                        'boundary_conditions': {'inflow': 150, 'pressure': 0.5},
                        'duration': 24
                    }
                }
            ]
        }
        
        # 2. 系统辨识服务
        self.services['identification'] = {
            'name': 'identification',
            'description': '系统辨识 - 识别管网参数、校准模型',
            'url': None,
            'parameters': {
                'type': 'object',
                'properties': {
                    'observed_data': {
                        'type': 'array',
                        'description': '观测数据（时间序列）',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'time': {'type': 'string'},
                                'flow': {'type': 'number'},
                                'pressure': {'type': 'number'}
                            }
                        }
                    },
                    'model_type': {
                        'type': 'string',
                        'enum': ['linear', 'nonlinear', 'hybrid'],
                        'description': '模型类型'
                    },
                    'parameters_to_identify': {
                        'type': 'array',
                        'description': '需要辨识的参数',
                        'items': {'type': 'string'}
                    }
                },
                'required': ['observed_data']
            }
        }
        
        # 3. 优化调度服务
        self.services['scheduling'] = {
            'name': 'scheduling',
            'description': '优化调度 - 生成最优水资源调度方案',
            'url': None,
            'parameters': {
                'type': 'object',
                'properties': {
                    'objective': {
                        'type': 'string',
                        'enum': ['minimize_cost', 'minimize_energy', 'maximize_efficiency', 'balance'],
                        'description': '优化目标'
                    },
                    'constraints': {
                        'type': 'object',
                        'description': '约束条件',
                        'properties': {
                            'max_flow': {'type': 'number'},
                            'min_pressure': {'type': 'number'},
                            'max_power': {'type': 'number'}
                        }
                    },
                    'time_horizon': {
                        'type': 'number',
                        'description': '调度时间范围（小时）',
                        'minimum': 1,
                        'maximum': 168
                    }
                },
                'required': ['objective', 'time_horizon']
            }
        }
        
        # 4. 控制策略服务
        self.services['control'] = {
            'name': 'control',
            'description': '控制策略设计 - 设计和优化控制器（PID、MPC等）',
            'url': None,
            'parameters': {
                'type': 'object',
                'properties': {
                    'controller_type': {
                        'type': 'string',
                        'enum': ['PID', 'MPC', 'fuzzy', 'adaptive'],
                        'description': '控制器类型'
                    },
                    'setpoint': {
                        'type': 'number',
                        'description': '设定值'
                    },
                    'process_model': {
                        'type': 'object',
                        'description': '过程模型参数'
                    },
                    'performance_spec': {
                        'type': 'object',
                        'description': '性能指标要求',
                        'properties': {
                            'settling_time': {'type': 'number', 'description': '调节时间(s)'},
                            'overshoot': {'type': 'number', 'description': '超调量(%)'}
                        }
                    }
                },
                'required': ['controller_type', 'setpoint']
            }
        }
        
        # 5. 性能测试服务
        self.services['testing'] = {
            'name': 'testing',
            'description': '性能测试 - 测试和评估系统性能',
            'url': None,
            'parameters': {
                'type': 'object',
                'properties': {
                    'test_type': {
                        'type': 'string',
                        'enum': ['stress', 'reliability', 'efficiency', 'stability'],
                        'description': '测试类型'
                    },
                    'test_duration': {
                        'type': 'number',
                        'description': '测试时长（小时）'
                    },
                    'test_scenario': {
                        'type': 'string',
                        'description': '测试场景描述'
                    }
                },
                'required': ['test_type']
            }
        }
        
        logger.info(f"📦 注册了 {len(self.services)} 个HydroNet专业服务")
    
    def get_tools_list(self) -> List[Dict]:
        """
        获取工具列表（供LLM使用）
        返回格式符合通义千问Function Calling要求
        包括HydroNet工具 + HydroSIS工具
        """
        tools = []
        
        # 1. HydroNet自己的5个工具
        for service in self.services.values():
            tool = {
                'name': service['name'],
                'description': f"[HydroNet] {service['description']}",
                'parameters': service['parameters']
            }
            tools.append(tool)
        
        # 2. HydroSIS的18个工具（如果已连接）
        if self.hydrosis_client and self.hydrosis_tools_cache:
            for hydrosis_tool in self.hydrosis_tools_cache:
                tool = {
                    'name': f"hydrosis_{hydrosis_tool['name']}",
                    'description': f"[HydroSIS] {hydrosis_tool['description']}",
                    'parameters': hydrosis_tool.get('inputSchema', {})
                }
                tools.append(tool)
        
        return tools
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_id: str = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        调用MCP工具（异步）
        支持HydroNet工具和HydroSIS工具
        
        Args:
            tool_name: 工具名称（hydrosis_开头的是HydroSIS工具）
            arguments: 参数字典
            user_id: 用户ID
            timeout: 超时时间（秒）
            
        Returns:
            工具执行结果
        """
        logger.info(f"🔧 调用工具: {tool_name}")
        logger.debug(f"参数: {json.dumps(arguments, ensure_ascii=False)}")
        
        # 检查是否是HydroSIS工具
        if tool_name.startswith('hydrosis_'):
            return await self._call_hydrosis_tool(tool_name, arguments, user_id, timeout)
        
        # HydroNet自己的工具
        if tool_name not in self.services:
            raise ValueError(f"❌ 工具不存在: {tool_name}")
        
        service = self.services[tool_name]
        
        # 如果配置了远程服务URL，调用远程服务
        if service.get('url'):
            try:
                result = await self._call_remote_service(
                    service['url'],
                    tool_name,
                    arguments,
                    user_id,
                    timeout
                )
                logger.info(f"✅ 远程服务调用成功: {tool_name}")
                return result
            except Exception as e:
                logger.error(f"❌ 远程服务调用失败: {e}")
                raise
        else:
            # 返回Mock数据（开发测试用）
            logger.warning(f"⚠️ {tool_name} 未配置远程服务，返回Mock数据")
            return self._get_mock_response(tool_name, arguments, user_id)
    
    async def _call_remote_service(
        self,
        url: str,
        tool_name: str,
        arguments: Dict,
        user_id: str,
        timeout: int
    ) -> Dict:
        """调用远程MCP服务"""
        async with aiohttp.ClientSession() as session:
            payload = {
                'tool_name': tool_name,
                'arguments': arguments,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
            
            async with session.post(
                f"{url}/execute",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"服务返回错误 {response.status}: {error_text}")
                
                return await response.json()
    
    def _get_mock_response(
        self,
        tool_name: str,
        arguments: Dict,
        user_id: str = None
    ) -> Dict[str, Any]:
        """生成Mock响应（用于开发测试）"""
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        mock_responses = {
            'simulation': {
                'status': 'success',
                'tool': 'simulation',
                'message': '✅ 仿真完成（Mock数据）',
                'results': {
                    'simulation_time': timestamp,
                    'duration': arguments.get('duration', 24),
                    'metrics': {
                        'average_flow': 145.8,
                        'max_flow': 178.2,
                        'average_pressure': 0.52,
                        'max_pressure': 0.68,
                        'energy_consumption': 1234.5,
                        'efficiency': 0.89
                    },
                    'time_series': [
                        {'hour': 0, 'flow': 120, 'pressure': 0.45},
                        {'hour': 6, 'flow': 145, 'pressure': 0.50},
                        {'hour': 12, 'flow': 175, 'pressure': 0.62},
                        {'hour': 18, 'flow': 138, 'pressure': 0.48},
                        {'hour': 24, 'flow': 125, 'pressure': 0.46}
                    ],
                    'warnings': [],
                    'note': '⚠️ 这是Mock数据，请配置实际MCP服务URL'
                }
            },
            
            'identification': {
                'status': 'success',
                'tool': 'identification',
                'message': '✅ 辨识完成（Mock数据）',
                'results': {
                    'identified_parameters': {
                        'roughness': 0.013,
                        'time_constant': 150.2,
                        'gain': 1.25,
                        'dead_time': 5.3
                    },
                    'model_fit': {
                        'R2': 0.94,
                        'RMSE': 2.34,
                        'MAE': 1.87
                    },
                    'confidence_intervals': {
                        'roughness': [0.011, 0.015],
                        'time_constant': [140, 160]
                    },
                    'validation': {
                        'cross_validation_score': 0.91,
                        'residual_analysis': 'passed'
                    },
                    'note': '⚠️ 这是Mock数据，请配置实际MCP服务URL'
                }
            },
            
            'scheduling': {
                'status': 'success',
                'tool': 'scheduling',
                'message': '✅ 调度优化完成（Mock数据）',
                'results': {
                    'objective_value': 15832.50,
                    'improvement': '18.5%',
                    'schedule': [
                        {'time': '00:00', 'flow': 95, 'power': 45, 'cost': 580},
                        {'time': '04:00', 'flow': 110, 'power': 52, 'cost': 620},
                        {'time': '08:00', 'flow': 160, 'power': 78, 'cost': 890},
                        {'time': '12:00', 'flow': 185, 'power': 92, 'cost': 1050},
                        {'time': '16:00', 'flow': 145, 'power': 68, 'cost': 780},
                        {'time': '20:00', 'flow': 120, 'power': 56, 'cost': 670}
                    ],
                    'constraints_satisfied': True,
                    'kpis': {
                        'total_cost': 15832.50,
                        'total_energy': 1847.3,
                        'avg_efficiency': 0.88,
                        'peak_demand_reduction': '15%'
                    },
                    'note': '⚠️ 这是Mock数据，请配置实际MCP服务URL'
                }
            },
            
            'control': {
                'status': 'success',
                'tool': 'control',
                'message': '✅ 控制器设计完成（Mock数据）',
                'results': {
                    'controller_type': arguments.get('controller_type', 'PID'),
                    'parameters': {
                        'Kp': 1.45,
                        'Ki': 0.32,
                        'Kd': 0.08,
                        'Tf': 0.05
                    },
                    'performance': {
                        'rise_time': 12.5,
                        'settling_time': 45.2,
                        'overshoot': 8.3,
                        'steady_state_error': 0.5
                    },
                    'stability': {
                        'gain_margin': 12.5,
                        'phase_margin': 48.2,
                        'stable': True
                    },
                    'robustness': {
                        'sensitivity': 0.73,
                        'complementary_sensitivity': 0.68
                    },
                    'note': '⚠️ 这是Mock数据，请配置实际MCP服务URL'
                }
            },
            
            'testing': {
                'status': 'success',
                'tool': 'testing',
                'message': '✅ 性能测试完成（Mock数据）',
                'results': {
                    'test_type': arguments.get('test_type', 'stress'),
                    'test_duration': arguments.get('test_duration', 24),
                    'summary': {
                        'total_tests': 15,
                        'passed': 13,
                        'failed': 0,
                        'warnings': 2,
                        'success_rate': 86.7
                    },
                    'performance_metrics': {
                        'reliability': 0.987,
                        'mtbf': 2580.5,
                        'availability': 0.995,
                        'response_time': 125.3
                    },
                    'stress_test': {
                        'max_load_handled': '150%',
                        'failure_point': '185%',
                        'recovery_time': 5.2
                    },
                    'recommendations': [
                        '建议增加缓冲容量以应对峰值负载',
                        '考虑优化控制器参数以提高响应速度'
                    ],
                    'note': '⚠️ 这是Mock数据，请配置实际MCP服务URL'
                }
            }
        }
        
        response = mock_responses.get(tool_name, {
            'status': 'error',
            'tool': tool_name,
            'message': f'❌ 未知工具: {tool_name}'
        })
        
        # 添加元数据
        response['metadata'] = {
            'user_id': user_id,
            'timestamp': timestamp,
            'execution_time': 0.5,
            'is_mock': True
        }
        
        return response
    
    def register_service(
        self,
        name: str,
        description: str,
        url: str,
        parameters: Dict,
        examples: List[Dict] = None
    ):
        """
        注册新的MCP服务
        
        Args:
            name: 服务名称
            description: 服务描述
            url: 服务URL
            parameters: 参数Schema（JSON Schema格式）
            examples: 示例列表
        """
        self.services[name] = {
            'name': name,
            'description': description,
            'url': url,
            'parameters': parameters,
            'examples': examples or [],
            'registered_at': datetime.now().isoformat()
        }
        logger.info(f"✅ 注册MCP服务: {name} -> {url}")
    
    def get_service_info(self, name: str) -> Optional[Dict]:
        """获取服务详细信息"""
        return self.services.get(name)
    
    def list_services(self) -> List[Dict]:
        """列出所有服务"""
        return list(self.services.values())
    
    def get_health_status(self) -> Dict:
        """获取所有服务的健康状态"""
        status = {
            'total': len(self.services),
            'services': {
                name: {
                    'available': service.get('url') is not None,
                    'type': 'remote' if service.get('url') else 'mock'
                }
                for name, service in self.services.items()
            }
        }
        
        # 添加HydroSIS状态
        if self.hydrosis_client:
            status['hydrosis'] = {
                'enabled': True,
                'tools_count': len(self.hydrosis_tools_cache),
                'url': os.environ.get('HYDROSIS_MCP_URL', 'http://localhost:8080')
            }
        else:
            status['hydrosis'] = {
                'enabled': False,
                'reason': 'Not configured or unavailable'
            }
        
        return status
    
    async def load_hydrosis_tools(self):
        """
        异步加载HydroSIS工具列表
        在应用启动时调用
        """
        if not self.hydrosis_client:
            logger.info("ℹ️ HydroSIS客户端未初始化，跳过工具加载")
            return
        
        try:
            # 健康检查
            health = await self.hydrosis_client.health_check()
            if health.get('status') != 'healthy':
                logger.warning(f"⚠️ HydroSIS服务不健康: {health}")
                return
            
            # 加载工具列表
            tools = await self.hydrosis_client.list_tools()
            self.hydrosis_tools_cache = tools
            
            logger.info(f"✅ 已加载 {len(tools)} 个HydroSIS工具")
            
            # 按分类统计
            by_category = await self.hydrosis_client.get_tools_by_category()
            for category, category_tools in by_category.items():
                logger.info(f"   - {category}: {len(category_tools)} 个")
        
        except Exception as e:
            logger.error(f"❌ 加载HydroSIS工具失败: {e}")
            self.hydrosis_tools_cache = []
    
    async def _call_hydrosis_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_id: str,
        timeout: int
    ) -> Dict[str, Any]:
        """
        调用HydroSIS MCP工具
        
        Args:
            tool_name: 工具名称（带hydrosis_前缀）
            arguments: 参数
            user_id: 用户ID
            timeout: 超时时间
            
        Returns:
            工具执行结果
        """
        if not self.hydrosis_client:
            raise Exception("❌ HydroSIS MCP客户端未初始化")
        
        # 移除hydrosis_前缀
        actual_tool_name = tool_name.replace('hydrosis_', '', 1)
        
        logger.info(f"🌊 调用HydroSIS工具: {actual_tool_name}")
        
        try:
            # 检查是否需要异步执行（某些工具耗时较长）
            async_tools = ['run_simulation', 'calibrate_parameters', 'delineate_watershed']
            
            if actual_tool_name in async_tools:
                # 提交异步任务
                logger.info(f"   ⏳ 提交异步任务...")
                task_info = await self.hydrosis_client.submit_async_task(
                    actual_tool_name,
                    arguments,
                    user_id or 'default'
                )
                
                task_id = task_info.get('task_id')
                logger.info(f"   📋 任务ID: {task_id}")
                
                # 等待任务完成（带进度反馈）
                result = await self.hydrosis_client.wait_for_task(
                    task_id,
                    poll_interval=2.0,
                    max_wait=min(timeout, 600)  # 最多等待10分钟
                )
                
                # 转换为统一格式
                if result.get('status') == 'completed':
                    return {
                        'status': 'success',
                        'tool': tool_name,
                        'message': f'✅ {actual_tool_name} 执行完成',
                        'results': result.get('results', {}),
                        'metadata': {
                            'task_id': task_id,
                            'execution_time': result.get('execution_time'),
                            'is_hydrosis': True,
                            'is_async': True
                        }
                    }
                else:
                    raise Exception(f"任务失败: {result.get('error', '未知错误')}")
            
            else:
                # 同步调用
                result = await self.hydrosis_client.call_tool(
                    actual_tool_name,
                    arguments,
                    user_id or 'default'
                )
                
                # 转换为统一格式
                return {
                    'status': result.get('status', 'success'),
                    'tool': tool_name,
                    'message': f'✅ {actual_tool_name} 执行完成',
                    'results': result.get('data', {}),
                    'metadata': {
                        **result.get('metadata', {}),
                        'is_hydrosis': True,
                        'is_async': False
                    }
                }
        
        except Exception as e:
            logger.error(f"❌ HydroSIS工具调用失败: {e}")
            raise Exception(f"HydroSIS工具调用失败: {str(e)}")
