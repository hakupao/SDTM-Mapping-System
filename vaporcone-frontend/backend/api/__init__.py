#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VAPORCONE API蓝图初始化模块

统一管理所有API蓝图的注册和配置，包括：
- Flask-RESTX API实例化
- 各功能模块蓝图注册
- API文档配置
- 错误处理
- 响应模型定义
"""

from flask import Blueprint
from flask_restx import Api
from config import Config, API_AUTHORIZATIONS, SWAGGER_UI_CONFIG


# 创建API蓝图
api_blueprint = Blueprint('api', __name__, url_prefix='/api')

# 创建Flask-RESTX API实例
api = Api(
    api_blueprint,
    title=Config.API_TITLE,
    version=Config.API_VERSION,
    description=Config.API_DESCRIPTION,
    doc='/docs/',  # Swagger UI 路径 /api/docs/
    authorizations=API_AUTHORIZATIONS,
    security=['apikey'],  # 默认安全方案
    validate=True,  # 启用请求验证
    **SWAGGER_UI_CONFIG
)


# 导入并注册各个命名空间
def register_namespaces():
    """注册所有API命名空间"""
    
    try:
        # 系统状态API
        from .system import ns as system_ns
        api.add_namespace(system_ns, path='/system')
        
        # 日志监控API  
        from .logs import ns as logs_ns
        api.add_namespace(logs_ns, path='/logs')
        
        # 流程执行API
        from .execution import ns as execution_ns
        api.add_namespace(execution_ns, path='/execution')
        
        # 研究函数API
        from .functions import ns as functions_ns
        api.add_namespace(functions_ns, path='/functions')
        
        # 文件管理API
        from .files import ns as files_ns
        api.add_namespace(files_ns, path='/files')
        
        # 数据库管理API
        from .database import ns as database_ns
        api.add_namespace(database_ns, path='/database')
        
        print("✅ 所有API命名空间注册成功")
        
    except ImportError as e:
        print(f"⚠️ 警告：部分API模块导入失败: {e}")
        print("💡 这可能是因为某些模块尚未创建，系统将继续运行")


# 通用响应模型
from flask_restx import fields

# 标准成功响应模型
success_response = api.model('SuccessResponse', {
    'status': fields.String(required=True, description='响应状态', example='success'),
    'message': fields.String(description='响应消息', example='操作成功'),
    'data': fields.Raw(description='响应数据')
})

# 标准错误响应模型  
error_response = api.model('ErrorResponse', {
    'status': fields.String(required=True, description='响应状态', example='error'),
    'message': fields.String(required=True, description='错误消息', example='操作失败'),
    'error_code': fields.String(description='错误代码', example='VALIDATION_ERROR'),
    'details': fields.Raw(description='错误详情')
})

# 分页响应模型
pagination_response = api.model('PaginationResponse', {
    'status': fields.String(required=True, description='响应状态', example='success'),
    'data': fields.List(fields.Raw, description='数据列表'),
    'pagination': fields.Nested(api.model('Pagination', {
        'page': fields.Integer(description='当前页码'),
        'per_page': fields.Integer(description='每页条数'),
        'total': fields.Integer(description='总条数'),
        'pages': fields.Integer(description='总页数')
    }))
})


# 全局错误处理
@api.errorhandler
def default_error_handler(error):
    """默认错误处理器"""
    return {
        'status': 'error',
        'message': str(error),
        'error_code': 'INTERNAL_ERROR'
    }, 500


@api.errorhandler(ValueError)
def value_error_handler(error):
    """处理值错误"""
    return {
        'status': 'error', 
        'message': '参数值错误',
        'error_code': 'VALUE_ERROR',
        'details': str(error)
    }, 400


@api.errorhandler(KeyError)
def key_error_handler(error):
    """处理缺少必要参数错误"""
    return {
        'status': 'error',
        'message': f'缺少必要参数: {str(error)}',
        'error_code': 'MISSING_PARAMETER'
    }, 400


# 执行命名空间注册
register_namespaces()


# 导出主要对象
__all__ = ['api_blueprint', 'api', 'success_response', 'error_response', 'pagination_response']
