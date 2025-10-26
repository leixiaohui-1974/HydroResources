# -*- coding: utf-8 -*-
"""
配置文件 - 存储应用配置和密钥
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """应用配置类"""
    
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # 微信公众号配置
    WECHAT_TOKEN = os.getenv('WECHAT_TOKEN', 'your-wechat-token')
    WECHAT_APP_ID = os.getenv('WECHAT_APP_ID', '')
    WECHAT_APP_SECRET = os.getenv('WECHAT_APP_SECRET', '')
    
    # 腾讯云API配置（元宝大模型）
    TENCENT_SECRET_ID = os.getenv('TENCENT_SECRET_ID', 'your-secret-id')
    TENCENT_SECRET_KEY = os.getenv('TENCENT_SECRET_KEY', 'your-secret-key')
    TENCENT_REGION = os.getenv('TENCENT_REGION', 'ap-guangzhou')
    
    # 腾讯元宝大模型配置
    HUNYUAN_MODEL = os.getenv('HUNYUAN_MODEL', 'hunyuan-lite')  # 可选: hunyuan-lite, hunyuan-standard, hunyuan-pro
    HUNYUAN_TEMPERATURE = float(os.getenv('HUNYUAN_TEMPERATURE', '0.7'))
    HUNYUAN_MAX_TOKENS = int(os.getenv('HUNYUAN_MAX_TOKENS', '2000'))
    
    # MCP服务配置
    MCP_SERVICES_DIR = os.getenv('MCP_SERVICES_DIR', './mcp_services')
    MCP_TIMEOUT = int(os.getenv('MCP_TIMEOUT', 30))  # 秒
    
    # 数据库配置（可选，用于存储对话历史）
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///hydronet.db')
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'hydronet.log')
    
    # 系统配置
    MAX_CONVERSATION_HISTORY = int(os.getenv('MAX_CONVERSATION_HISTORY', 10))
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 3600))  # 秒
