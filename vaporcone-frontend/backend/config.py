#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VAPORCONE 配置管理模块

集中管理应用程序的所有配置参数，包括：
- Flask应用配置
- 数据库连接配置  
- API文档配置
- 日志配置
- WebSocket配置
"""

import os


class Config:
    """基础配置类"""
    
    # Flask应用配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'vaporcone-secret-key'
    
    # API文档配置
    API_TITLE = 'VAPORCONE 数据处理平台 API'
    API_VERSION = 'v1.0'
    API_DESCRIPTION = '''
    临床数据标准化处理系统接口文档
    
    ## 主要功能模块
    - 系统状态监控
    - 数据处理流程执行
    - 日志监控和管理
    - 文件管理
    - 数据库操作
    - 研究特定函数管理
    '''
    
    # CORS配置
    CORS_ORIGINS = "*"
    
    # WebSocket配置
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    
    # 分页配置
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 200
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    MAX_SYSTEM_LOGS = 1000
    MAX_EXECUTION_HISTORY = 500
    
    # 执行配置
    SCRIPT_TIMEOUT = 300  # 5分钟
    MAX_CONCURRENT_EXECUTIONS = 1
    
    # 文件预览配置
    FILE_PREVIEW_LINES = 10
    
    @staticmethod
    def init_app(app):
        """初始化应用程序配置"""
        pass


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 开发环境特定的初始化
        import logging
        logging.basicConfig(level=logging.DEBUG)


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 生产环境特定的初始化
        import logging
        logging.basicConfig(level=logging.WARNING)


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


# API认证配置
API_AUTHORIZATIONS = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header', 
        'name': 'X-API-KEY',
        'description': 'API密钥认证'
    },
    'Bearer': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': 'Bearer Token认证'
    }
}

# Swagger UI配置
SWAGGER_UI_CONFIG = {
    'docExpansion': 'none',  # 默认不展开
    'defaultModelsExpandDepth': 2,
    'defaultModelExpandDepth': 2,
    'displayRequestDuration': True,
    'filter': True,
    'showExtensions': True,
    'showCommonExtensions': True,
    'tryItOutEnabled': True
}
