#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VAPORCONE 重构架构测试脚本

用于测试新架构的各个模块是否正常工作
"""

import sys
import os


def test_imports():
    """测试模块导入"""
    print("🧪 测试模块导入...")
    
    try:
        # 测试Flask-RESTX
        try:
            import flask_restx
            print("✅ Flask-RESTX 导入成功")
        except ImportError:
            print("❌ Flask-RESTX 未安装，请运行: pip install Flask-RESTX==1.3.0")
            return False
        
        # 测试配置模块
        from config import config, Config
        print("✅ 配置模块导入成功")
        
        # 测试服务模块
        from services import SystemService, LogService, ExecutionService
        print("✅ 服务模块导入成功")
        
        # 测试WebSocket模块
        from websockets import setup_socketio_events
        print("✅ WebSocket模块导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False


def test_services():
    """测试服务功能"""
    print("\n🧪 测试服务功能...")
    
    try:
        # 测试日志服务
        from services.log_service import LogService
        log_service = LogService()
        log_entry = log_service.add_log('INFO', 'TestModule', '测试日志')
        print(f"✅ 日志服务测试成功: {log_entry['id']}")
        
        # 测试系统服务
        from services.system_service import SystemService
        system_service = SystemService()
        status = system_service.get_system_info()
        print(f"✅ 系统服务测试成功: {status['system']}")
        
        # 测试执行服务
        from services.execution_service import ExecutionService
        execution_service = ExecutionService()
        steps = execution_service.get_available_steps()
        print(f"✅ 执行服务测试成功: {len(steps)}个步骤")
        
        return True
        
    except Exception as e:
        print(f"❌ 服务测试失败: {e}")
        return False


def test_api_creation():
    """测试API创建"""
    print("\n🧪 测试API创建...")
    
    try:
        from app import create_app
        app, socketio = create_app('testing')
        
        print(f"✅ Flask应用创建成功: {app.name}")
        print(f"✅ SocketIO创建成功: {type(socketio).__name__}")
        
        # 测试路由注册
        with app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                print("✅ 根路由响应正常")
            else:
                print(f"⚠️ 根路由响应异常: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ API创建测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🔍 VAPORCONE 重构架构测试")
    print("=" * 50)
    
    # 设置Python路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    tests = [
        ("模块导入", test_imports),
        ("服务功能", test_services),
        ("API创建", test_api_creation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 执行测试: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} 测试通过")
        else:
            print(f"❌ {test_name} 测试失败")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！新架构准备就绪")
        print("\n🚀 启动命令:")
        print("   python app.py")
        print("\n📖 API文档:")
        print("   http://localhost:5000/api/docs/")
    else:
        print("⚠️ 部分测试失败，请检查依赖和配置")
        print("\n💡 可能需要:")
        print("   pip install -r requirements.txt")


if __name__ == '__main__':
    main()
