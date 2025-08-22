#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VAPORCONE 系统状态API模块

提供系统状态监控相关的API接口，包括：
- 系统资源使用情况
- 数据库连接状态
- 可用研究列表
- 系统健康检查
"""

import os
import platform
from datetime import datetime
from flask import request
from flask_restx import Namespace, Resource, fields
from services.system_service import SystemService


# 创建系统状态命名空间
ns = Namespace('system', description='系统状态监控API')

# 系统状态响应模型
system_status_model = ns.model('SystemStatus', {
    'cpu': fields.Float(description='CPU使用率(%)', example=25.6),
    'memory': fields.Float(description='内存使用量(GB)', example=4.2),
    'memory_total': fields.Float(description='总内存(GB)', example=8.0),
    'memory_percent': fields.Float(description='内存使用率(%)', example=52.5),
    'disk': fields.Float(description='磁盘使用率(%)', example=68.3),
    'disk_used': fields.Float(description='已用磁盘空间(GB)', example=256.7),
    'disk_total': fields.Float(description='总磁盘空间(GB)', example=512.0),
    'database': fields.String(description='数据库连接状态', enum=['connected', 'disconnected']),
    'platform': fields.String(description='操作系统平台', example='Windows'),
    'python_version': fields.String(description='Python版本', example='3.9.7'),
    'timestamp': fields.DateTime(description='状态获取时间')
})

# 研究信息模型
study_model = ns.model('Study', {
    'id': fields.String(required=True, description='研究ID', example='CIRCULATE'),
    'name': fields.String(required=True, description='研究名称', example='CIRCULATE'),
    'config_exists': fields.Boolean(description='配置文件是否存在', example=True),
    'status': fields.String(description='研究状态', enum=['active', 'inactive'], example='active')
})

# 系统健康检查模型
health_check_model = ns.model('HealthCheck', {
    'status': fields.String(description='整体健康状态', enum=['healthy', 'warning', 'error']),
    'vaporcone_modules': fields.Boolean(description='VAPORCONE模块状态'),
    'database_connection': fields.Boolean(description='数据库连接状态'),
    'disk_space': fields.Boolean(description='磁盘空间状态'),
    'memory_usage': fields.Boolean(description='内存使用状态'),
    'uptime': fields.String(description='运行时间', example='2天 5小时 30分钟'),
    'checks': fields.List(fields.Nested(ns.model('HealthCheckItem', {
        'name': fields.String(description='检查项名称'),
        'status': fields.String(enum=['pass', 'fail', 'warning']),
        'message': fields.String(description='检查结果信息')
    })))
})


@ns.route('/status')
class SystemStatus(Resource):
    """系统状态监控"""
    
    @ns.doc('get_system_status')
    @ns.response(200, '获取成功', ns.model('SystemStatusResponse', {
        'status': fields.String(example='success'),
        'data': fields.Nested(system_status_model)
    }))
    @ns.response(500, '服务器错误')
    def get(self):
        """
        获取系统资源使用状态
        
        返回包括CPU、内存、磁盘使用情况以及数据库连接状态等系统信息
        """
        try:
            system_service = SystemService()
            status_data = system_service.get_system_status()
            
            return {
                'status': 'success',
                'data': status_data
            }
        except Exception as e:
            ns.abort(500, f'获取系统状态失败: {str(e)}')


@ns.route('/studies')
class StudiesList(Resource):
    """研究列表管理"""
    
    @ns.doc('get_studies')
    @ns.response(200, '获取成功', ns.model('StudiesResponse', {
        'status': fields.String(example='success'),
        'data': fields.List(fields.Nested(study_model))
    }))
    @ns.response(500, '服务器错误')
    def get(self):
        """
        获取可用的研究列表
        
        扫描studySpecific目录下的所有研究项目，返回研究信息和配置状态
        """
        try:
            system_service = SystemService()
            studies_data = system_service.get_studies_list()
            
            return {
                'status': 'success',
                'data': studies_data
            }
        except Exception as e:
            ns.abort(500, f'获取研究列表失败: {str(e)}')


@ns.route('/health')
class HealthCheck(Resource):
    """系统健康检查"""
    
    @ns.doc('health_check')
    @ns.response(200, '检查完成', ns.model('HealthCheckResponse', {
        'status': fields.String(example='success'),
        'data': fields.Nested(health_check_model)
    }))
    def get(self):
        """
        执行系统健康检查
        
        全面检查系统各项组件的健康状态，包括模块加载、数据库连接、资源使用等
        """
        try:
            system_service = SystemService()
            health_data = system_service.perform_health_check()
            
            return {
                'status': 'success',
                'data': health_data
            }
        except Exception as e:
            ns.abort(500, f'健康检查失败: {str(e)}')


@ns.route('/info')
class SystemInfo(Resource):
    """系统基本信息"""
    
    @ns.doc('get_system_info')
    @ns.response(200, '获取成功')
    def get(self):
        """
        获取系统基本信息
        
        包括操作系统、Python版本、VAPORCONE版本等基础信息
        """
        try:
            system_service = SystemService()
            info_data = system_service.get_system_info()
            
            return {
                'status': 'success',
                'data': info_data
            }
        except Exception as e:
            ns.abort(500, f'获取系统信息失败: {str(e)}')


@ns.route('/metrics')
class SystemMetrics(Resource):
    """系统性能指标"""
    
    @ns.doc('get_system_metrics')
    @ns.param('period', '时间周期', enum=['1h', '6h', '24h'], default='1h')
    @ns.response(200, '获取成功')
    def get(self):
        """
        获取系统性能指标历史数据
        
        返回指定时间周期内的CPU、内存、磁盘等性能指标变化趋势
        """
        try:
            period = request.args.get('period', '1h')
            system_service = SystemService()
            metrics_data = system_service.get_system_metrics(period)
            
            return {
                'status': 'success',
                'data': metrics_data
            }
        except Exception as e:
            ns.abort(500, f'获取系统指标失败: {str(e)}')
