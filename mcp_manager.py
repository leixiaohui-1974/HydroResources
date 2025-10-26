# -*- coding: utf-8 -*-
"""
MCP服务管理器
管理和调用各种水网MCP服务：仿真、辨识、调度、控制、测试
"""

import json
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class MCPServiceManager:
    """MCP服务管理器"""
    
    def __init__(self):
        """初始化MCP服务管理器"""
        self.services = {}
        self._initialize_default_services()
        logger.info("MCP服务管理器初始化完成")
    
    def _initialize_default_services(self):
        """初始化默认的MCP服务"""
        
        # 水网仿真服务
        self.services['simulation'] = {
            'name': 'simulation',
            'url': None,  # 待配置
            'description': '水网仿真服务 - 模拟水网运行情况',
            'type': 'simulation',
            'methods': ['run_simulation', 'get_results', 'analyze'],
            'status': 'pending',
            'keywords': ['仿真', '模拟', 'simulation', '运行情况', '预测']
        }
        
        # 系统辨识服务
        self.services['identification'] = {
            'name': 'identification',
            'url': None,
            'description': '系统辨识服务 - 识别水网系统特性和参数',
            'type': 'identification',
            'methods': ['identify_parameters', 'model_validation', 'sensitivity_analysis'],
            'status': 'pending',
            'keywords': ['辨识', '识别', '参数', 'identification', '特性']
        }
        
        # 智能调度服务
        self.services['scheduling'] = {
            'name': 'scheduling',
            'url': None,
            'description': '智能调度服务 - 优化水资源调度方案',
            'type': 'scheduling',
            'methods': ['optimize_schedule', 'evaluate_plan', 'generate_alternatives'],
            'status': 'pending',
            'keywords': ['调度', '优化', 'scheduling', '方案', '计划']
        }
        
        # 控制优化服务
        self.services['control'] = {
            'name': 'control',
            'url': None,
            'description': '控制优化服务 - 优化水网控制策略',
            'type': 'control',
            'methods': ['design_controller', 'tune_parameters', 'stability_analysis'],
            'status': 'pending',
            'keywords': ['控制', 'control', '调节', '策略', 'PID', 'MPC']
        }
        
        # 性能测试服务
        self.services['testing'] = {
            'name': 'testing',
            'url': None,
            'description': '性能测试服务 - 测试和评估系统性能',
            'type': 'testing',
            'methods': ['run_tests', 'benchmark', 'reliability_analysis'],
            'status': 'pending',
            'keywords': ['测试', 'test', '评估', '性能', 'benchmark']
        }
    
    def register_service(
        self,
        name: str,
        url: str,
        description: str = '',
        service_type: str = 'general',
        methods: List[str] = None,
        keywords: List[str] = None
    ):
        """
        注册MCP服务
        
        Args:
            name: 服务名称
            url: 服务URL
            description: 服务描述
            service_type: 服务类型
            methods: 支持的方法列表
            keywords: 关键词列表
        """
        self.services[name] = {
            'name': name,
            'url': url,
            'description': description,
            'type': service_type,
            'methods': methods or [],
            'keywords': keywords or [],
            'status': 'active',
            'registered_at': datetime.now().isoformat()
        }
        logger.info(f"注册MCP服务: {name} -> {url}")
    
    def list_services(self) -> List[Dict]:
        """列出所有MCP服务"""
        return list(self.services.values())
    
    def get_service(self, name: str) -> Optional[Dict]:
        """获取指定服务信息"""
        return self.services.get(name)
    
    def call_service(
        self,
        service_name: str,
        params: Dict[str, Any],
        method: str = 'execute',
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        调用MCP服务
        
        Args:
            service_name: 服务名称
            params: 参数字典
            method: 调用方法
            timeout: 超时时间（秒）
            
        Returns:
            服务响应结果
        """
        service = self.services.get(service_name)
        
        if not service:
            raise ValueError(f"服务不存在: {service_name}")
        
        if not service['url']:
            # 服务未配置URL，返回模拟响应
            logger.warning(f"服务 {service_name} 未配置URL，返回模拟数据")
            return self._get_mock_response(service_name, params)
        
        try:
            # 调用实际的MCP服务
            url = f"{service['url']}/{method}"
            response = requests.post(
                url,
                json=params,
                timeout=timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"成功调用MCP服务: {service_name}.{method}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"调用MCP服务失败: {service_name} - {str(e)}")
            raise Exception(f"服务调用失败: {str(e)}")
    
    def _get_mock_response(self, service_name: str, params: Dict) -> Dict[str, Any]:
        """获取模拟响应（用于开发测试）"""
        
        mock_responses = {
            'simulation': {
                'status': 'success',
                'message': '仿真服务未配置，这是模拟数据',
                'data': {
                    'simulation_time': '2025-10-26 10:00:00',
                    'flow_rate': 125.5,
                    'water_level': 12.3,
                    'pressure': 0.8,
                    'efficiency': 0.92,
                    'note': '这是仿真模拟数据，请配置实际的MCP服务URL'
                }
            },
            'identification': {
                'status': 'success',
                'message': '辨识服务未配置，这是模拟数据',
                'data': {
                    'identified_parameters': {
                        'roughness': 0.013,
                        'time_constant': 150.0,
                        'gain': 1.2
                    },
                    'confidence': 0.85,
                    'note': '这是辨识模拟数据，请配置实际的MCP服务URL'
                }
            },
            'scheduling': {
                'status': 'success',
                'message': '调度服务未配置，这是模拟数据',
                'data': {
                    'optimal_schedule': [
                        {'time': '00:00', 'flow': 100},
                        {'time': '06:00', 'flow': 150},
                        {'time': '12:00', 'flow': 200},
                        {'time': '18:00', 'flow': 120}
                    ],
                    'total_cost': 15800,
                    'efficiency': 0.88,
                    'note': '这是调度模拟数据，请配置实际的MCP服务URL'
                }
            },
            'control': {
                'status': 'success',
                'message': '控制服务未配置，这是模拟数据',
                'data': {
                    'controller_type': 'PID',
                    'parameters': {
                        'Kp': 1.5,
                        'Ki': 0.3,
                        'Kd': 0.1
                    },
                    'stability_margin': 6.5,
                    'note': '这是控制模拟数据，请配置实际的MCP服务URL'
                }
            },
            'testing': {
                'status': 'success',
                'message': '测试服务未配置，这是模拟数据',
                'data': {
                    'test_results': {
                        'passed': 8,
                        'failed': 0,
                        'warnings': 2
                    },
                    'performance_score': 92.5,
                    'reliability': 0.98,
                    'note': '这是测试模拟数据，请配置实际的MCP服务URL'
                }
            }
        }
        
        return mock_responses.get(service_name, {
            'status': 'pending',
            'message': f'服务 {service_name} 未配置',
            'data': None
        })
    
    def process_user_query(self, query: str) -> Optional[Dict]:
        """
        处理用户查询，判断是否需要调用MCP服务
        
        Args:
            query: 用户查询文本
            
        Returns:
            如果需要调用服务，返回服务响应；否则返回None
        """
        query_lower = query.lower()
        
        # 检查是否匹配任何服务的关键词
        for service_name, service in self.services.items():
            for keyword in service['keywords']:
                if keyword in query_lower:
                    logger.info(f"查询匹配到服务: {service_name}")
                    
                    # 这里可以添加更复杂的参数提取逻辑
                    params = self._extract_parameters(query, service_name)
                    
                    try:
                        # 调用相应的服务
                        result = self.call_service(service_name, params)
                        return {
                            'service': service_name,
                            'query': query,
                            'result': result
                        }
                    except Exception as e:
                        logger.error(f"调用服务失败: {str(e)}")
                        return None
        
        return None
    
    def _extract_parameters(self, query: str, service_name: str) -> Dict:
        """从查询文本中提取参数（简单实现，可以用NLP增强）"""
        params = {
            'query': query,
            'timestamp': datetime.now().isoformat()
        }
        
        # 提取数字参数
        numbers = re.findall(r'\d+\.?\d*', query)
        if numbers:
            params['values'] = [float(n) for n in numbers]
        
        return params
    
    def get_health_status(self) -> Dict:
        """获取所有服务的健康状态"""
        status = {
            'total': len(self.services),
            'active': sum(1 for s in self.services.values() if s['status'] == 'active'),
            'pending': sum(1 for s in self.services.values() if s['status'] == 'pending'),
            'services': {}
        }
        
        for name, service in self.services.items():
            status['services'][name] = {
                'status': service['status'],
                'has_url': service['url'] is not None
            }
        
        return status
