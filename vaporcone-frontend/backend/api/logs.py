#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VAPORCONE 日志监控API模块

提供日志管理和监控相关的API接口，包括：
- 系统日志查询和过滤
- 日志清理
- 实时日志推送
- 日志统计分析
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from services.log_service import LogService


# 创建日志监控命名空间
ns = Namespace('logs', description='日志监控API')

# 日志条目模型
log_entry_model = ns.model('LogEntry', {
    'id': fields.Integer(required=True, description='日志ID', example=1001),
    'timestamp': fields.String(required=True, description='时间戳', example='2024-01-01 12:00:00.123'),
    'level': fields.String(required=True, description='日志级别', enum=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
    'module': fields.String(required=True, description='模块名称', example='VC_OP01_cleaning'),
    'message': fields.String(required=True, description='日志消息', example='数据处理完成'),
    'details': fields.String(description='详细信息', example='处理了1000条记录')
})

# 日志查询参数模型
log_query_params = ns.model('LogQueryParams', {
    'level': fields.String(description='日志级别过滤', enum=['all', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='all'),
    'limit': fields.Integer(description='返回条数限制', default=100, min=1, max=1000),
    'search': fields.String(description='搜索关键词'),
    'module': fields.String(description='模块名称过滤'),
    'start_time': fields.String(description='开始时间', example='2024-01-01 00:00:00'),
    'end_time': fields.String(description='结束时间', example='2024-01-01 23:59:59')
})

# 日志统计模型
log_statistics_model = ns.model('LogStatistics', {
    'total_logs': fields.Integer(description='总日志数'),
    'levels': fields.Nested(ns.model('LogLevelStats', {
        'DEBUG': fields.Integer(description='DEBUG级别日志数'),
        'INFO': fields.Integer(description='INFO级别日志数'),
        'WARNING': fields.Integer(description='WARNING级别日志数'),
        'ERROR': fields.Integer(description='ERROR级别日志数'),
        'CRITICAL': fields.Integer(description='CRITICAL级别日志数')
    })),
    'modules': fields.List(fields.Nested(ns.model('ModuleStats', {
        'module': fields.String(description='模块名称'),
        'count': fields.Integer(description='日志条数')
    }))),
    'timeline': fields.List(fields.Nested(ns.model('TimelineStats', {
        'hour': fields.String(description='小时', example='2024-01-01 12:00'),
        'count': fields.Integer(description='该小时的日志数')
    })))
})


@ns.route('/list')
class LogsList(Resource):
    """日志列表查询"""
    
    @ns.doc('get_logs')
    @ns.expect(ns.parser().add_argument('level', type=str, help='日志级别', location='args', default='all')
                           .add_argument('limit', type=int, help='返回条数', location='args', default=100)
                           .add_argument('search', type=str, help='搜索关键词', location='args')
                           .add_argument('module', type=str, help='模块名称', location='args')
                           .add_argument('start_time', type=str, help='开始时间', location='args')
                           .add_argument('end_time', type=str, help='结束时间', location='args'))
    @ns.response(200, '获取成功', ns.model('LogsResponse', {
        'status': fields.String(example='success'),
        'data': fields.List(fields.Nested(log_entry_model)),
        'total': fields.Integer(description='符合条件的总日志数'),
        'filtered': fields.Integer(description='过滤后的日志数')
    }))
    @ns.response(500, '服务器错误')
    def get(self):
        """
        获取系统日志列表
        
        支持按级别、模块、时间范围、关键词进行过滤查询
        """
        try:
            # 获取查询参数
            level = request.args.get('level', 'all')
            limit = int(request.args.get('limit', 100))
            search = request.args.get('search', '')
            module = request.args.get('module', '')
            start_time = request.args.get('start_time', '')
            end_time = request.args.get('end_time', '')
            
            log_service = LogService()
            result = log_service.get_logs(
                level=level,
                limit=limit,
                search=search,
                module=module,
                start_time=start_time,
                end_time=end_time
            )
            
            return {
                'status': 'success',
                'data': result['logs'],
                'total': result['total'],
                'filtered': result['filtered']
            }
        except ValueError as e:
            ns.abort(400, f'参数错误: {str(e)}')
        except Exception as e:
            ns.abort(500, f'获取日志失败: {str(e)}')


@ns.route('/clear')
class LogsClear(Resource):
    """清空日志"""
    
    @ns.doc('clear_logs')
    @ns.response(200, '清空成功', ns.model('ClearResponse', {
        'status': fields.String(example='success'),
        'message': fields.String(example='日志已清空'),
        'cleared_count': fields.Integer(description='清空的日志条数')
    }))
    @ns.response(500, '服务器错误')
    def post(self):
        """
        清空系统日志
        
        删除所有历史日志记录，该操作不可恢复
        """
        try:
            log_service = LogService()
            cleared_count = log_service.clear_logs()
            
            return {
                'status': 'success',
                'message': '日志已清空',
                'cleared_count': cleared_count
            }
        except Exception as e:
            ns.abort(500, f'清空日志失败: {str(e)}')


@ns.route('/statistics')
class LogsStatistics(Resource):
    """日志统计分析"""
    
    @ns.doc('get_log_statistics')
    @ns.expect(ns.parser().add_argument('period', type=str, help='统计周期', location='args', 
                                       choices=['1h', '6h', '24h', '7d'], default='24h'))
    @ns.response(200, '获取成功', ns.model('StatisticsResponse', {
        'status': fields.String(example='success'),
        'data': fields.Nested(log_statistics_model)
    }))
    def get(self):
        """
        获取日志统计信息
        
        提供指定时间周期内的日志级别分布、模块分布、时间分布等统计数据
        """
        try:
            period = request.args.get('period', '24h')
            log_service = LogService()
            statistics = log_service.get_log_statistics(period)
            
            return {
                'status': 'success',
                'data': statistics
            }
        except Exception as e:
            ns.abort(500, f'获取日志统计失败: {str(e)}')


@ns.route('/export')
class LogsExport(Resource):
    """日志导出"""
    
    @ns.doc('export_logs')
    @ns.expect(ns.parser().add_argument('format', type=str, help='导出格式', location='args', 
                                       choices=['csv', 'json', 'txt'], default='csv')
                           .add_argument('level', type=str, help='日志级别', location='args', default='all')
                           .add_argument('start_time', type=str, help='开始时间', location='args')
                           .add_argument('end_time', type=str, help='结束时间', location='args'))
    @ns.response(200, '导出成功')
    @ns.response(400, '参数错误')
    def get(self):
        """
        导出日志文件
        
        支持CSV、JSON、TXT格式导出，可按时间范围和级别过滤
        """
        try:
            export_format = request.args.get('format', 'csv')
            level = request.args.get('level', 'all')
            start_time = request.args.get('start_time', '')
            end_time = request.args.get('end_time', '')
            
            log_service = LogService()
            file_path = log_service.export_logs(
                format=export_format,
                level=level,
                start_time=start_time,
                end_time=end_time
            )
            
            from flask import send_file
            return send_file(file_path, as_attachment=True)
            
        except ValueError as e:
            ns.abort(400, f'参数错误: {str(e)}')
        except Exception as e:
            ns.abort(500, f'导出日志失败: {str(e)}')


@ns.route('/levels')
class LogLevels(Resource):
    """日志级别管理"""
    
    @ns.doc('get_log_levels')
    @ns.response(200, '获取成功')
    def get(self):
        """
        获取所有可用的日志级别
        
        返回系统支持的日志级别列表及其描述
        """
        try:
            log_service = LogService()
            levels = log_service.get_available_log_levels()
            
            return {
                'status': 'success',
                'data': levels
            }
        except Exception as e:
            ns.abort(500, f'获取日志级别失败: {str(e)}')


@ns.route('/modules')
class LogModules(Resource):
    """日志模块管理"""
    
    @ns.doc('get_log_modules')
    @ns.response(200, '获取成功')
    def get(self):
        """
        获取所有日志模块列表
        
        返回产生日志的所有模块名称及其日志数量
        """
        try:
            log_service = LogService()
            modules = log_service.get_log_modules()
            
            return {
                'status': 'success',
                'data': modules
            }
        except Exception as e:
            ns.abort(500, f'获取日志模块失败: {str(e)}')
