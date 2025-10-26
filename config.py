# -*- coding: utf-8 -*-
"""
配置文件 - 阿里云完整版（支持Web + 微信公众号）
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
    
    # 阿里云API配置（必需）
    ALIYUN_API_KEY = os.getenv('ALIYUN_API_KEY', 'your-api-key')
    ALIYUN_REGION = os.getenv('ALIYUN_REGION', 'cn-hangzhou')
    
    # 通义千问大模型配置
    QWEN_MODEL = os.getenv('QWEN_MODEL', 'qwen-turbo')  # 可选: qwen-turbo, qwen-plus, qwen-max
    QWEN_TEMPERATURE = float(os.getenv('QWEN_TEMPERATURE', '0.7'))
    QWEN_MAX_TOKENS = int(os.getenv('QWEN_MAX_TOKENS', '2000'))
    
    # 微信公众号配置（可选，如不需要可不配置）
    WECHAT_ENABLED = os.getenv('WECHAT_ENABLED', 'false').lower() == 'true'
    WECHAT_TOKEN = os.getenv('WECHAT_TOKEN', 'your-wechat-token')
    WECHAT_APP_ID = os.getenv('WECHAT_APP_ID', '')
    WECHAT_APP_SECRET = os.getenv('WECHAT_APP_SECRET', '')
    
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
    
    # 数据库配置（多租户SaaS必需）
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://hydronet:password@localhost/hydronet')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # JWT配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 28800))  # 8小时
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000))  # 30天
    
    # Redis配置（用于限流和缓存）
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    RATELIMIT_STORAGE_URL = REDIS_URL
