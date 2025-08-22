#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VAPORCONE 重构后的主应用入口

基于Flask-RESTX的模块化架构，提供：
- API蓝图管理
- 自动生成Swagger文档
- WebSocket实时通信
- 统一错误处理
- 配置管理
"""

import os
import sys
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from config import config
from api import api_blueprint
from websockets import setup_socketio_events


def create_app(config_name=None):
    """应用工厂函数"""
    
    # 确定配置环境
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # 创建Flask应用实例
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 初始化扩展
    CORS(app, origins=app.config.get('CORS_ORIGINS', '*'))
    
    # 创建SocketIO实例
    socketio = SocketIO(
        app, 
        cors_allowed_origins=app.config.get('SOCKETIO_CORS_ALLOWED_ORIGINS', '*'),
        logger=True,
        engineio_logger=True
    )
    
    # 设置WebSocket事件处理
    broadcast_functions = setup_socketio_events(socketio)
    
    # 将广播函数存储到应用上下文中，供其他模块使用
    app.broadcast_functions = broadcast_functions
    
    # 注册蓝图
    app.register_blueprint(api_blueprint)
    
    # 添加根路由
    @app.route('/')
    def index():
        """根路由 - 重定向到API文档"""
        return {
            'message': 'VAPORCONE 数据处理平台 API',
            'version': app.config.get('API_VERSION', '1.0'),
            'docs': '/api/docs/',
            'status': 'running'
        }
    
    @app.route('/health')
    def health_check():
        """健康检查端点"""
        return {
            'status': 'healthy',
            'timestamp': '2024-01-01T00:00:00Z',
            'version': app.config.get('API_VERSION', '1.0')
        }
    
    # 全局错误处理
    @app.errorhandler(404)
    def not_found(error):
        """处理404错误"""
        return {
            'status': 'error',
            'message': 'API端点未找到',
            'error_code': 'NOT_FOUND'
        }, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """处理500错误"""
        return {
            'status': 'error',
            'message': '服务器内部错误',
            'error_code': 'INTERNAL_ERROR'
        }, 500
    
    @app.errorhandler(400)
    def bad_request(error):
        """处理400错误"""
        return {
            'status': 'error',
            'message': '请求参数错误',
            'error_code': 'BAD_REQUEST'
        }, 400
    
    # 存储socketio实例供外部使用
    app.socketio = socketio
    
    return app, socketio


def setup_vaporcone_modules():
    """设置VAPORCONE模块路径"""
    try:
        # 添加父目录到Python路径，以便导入VAPORCONE模块
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        grandparent_dir = os.path.dirname(parent_dir)
        sys.path.insert(0, grandparent_dir)
        
        print(f"当前目录: {current_dir}")
        print(f"添加到Python路径: {grandparent_dir}")
        
        # 尝试导入VAPORCONE模块
        from VC_BC01_constant import STUDY_ID, ROOT_PATH
        print(f"✅ VAPORCONE模块导入成功")
        print(f"📁 当前研究: {STUDY_ID}")
        print(f"🏠 根路径: {ROOT_PATH}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 错误：无法导入VAPORCONE模块: {e}")
        print("🚫 VAPORCONE模块是系统正常运行的必要组件")
        print("💡 请确保：")
        print("   1. VC_BC01_constant.py 等核心文件存在")
        print("   2. 数据库连接配置正确")
        print("   3. 运行环境配置正确")
        return False


def main():
    """主函数 - 启动应用"""
    
    print("🚀 启动 VAPORCONE 重构版后端API服务器...")
    
    # 设置VAPORCONE模块
    vaporcone_loaded = setup_vaporcone_modules()
    
    # 创建应用
    app, socketio = create_app()
    
    # 显示启动信息
    print(f"📊 API文档地址: http://localhost:5000/api/docs/")
    print(f"🔍 健康检查: http://localhost:5000/health")
    print(f"🌐 VAPORCONE模块状态: {'✅ 已加载' if vaporcone_loaded else '❌ 未加载'}")
    
    # 添加系统启动日志
    try:
        from services.log_service import LogService
        log_service = LogService()
        log_service.add_log(
            'INFO', 
            'System', 
            'VAPORCONE 重构版数据处理平台启动',
            f'VAPORCONE模块状态: {"已加载" if vaporcone_loaded else "未加载"}\n重构架构: Flask-RESTX + 蓝图模式'
        )
    except Exception as e:
        print(f"⚠️ 日志服务初始化失败: {e}")
    
    # 启动服务器
    try:
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=5000, 
            debug=True,
            use_reloader=False  # 避免重复加载模块
        )
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")


if __name__ == '__main__':
    main()
