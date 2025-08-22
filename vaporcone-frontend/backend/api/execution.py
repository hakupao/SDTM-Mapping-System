#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VAPORCONE 流程执行API模块

提供数据处理流程执行相关的API接口，包括：
- 流程控制（启动、停止、重置）
- 单步执行
- 批量执行
- 执行状态查询
- 执行历史管理
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from services.execution_service import ExecutionService


# 创建流程执行命名空间
ns = Namespace('execution', description='流程执行API')

# 执行状态模型
execution_status_model = ns.model('ExecutionStatus', {
    'total': fields.Integer(description='总步骤数', example=8),
    'completed': fields.Integer(description='已完成步骤数', example=3),
    'running': fields.Integer(description='正在运行步骤数', example=1),
    'pending': fields.Integer(description='待执行步骤数', example=4),
    'failed': fields.Integer(description='失败步骤数', example=0),
    'last_execution': fields.String(description='最后执行时间'),
    'execution_status': fields.String(description='执行状态', enum=['idle', 'running', 'paused', 'completed', 'error'])
})

# 执行步骤模型
execution_step_model = ns.model('ExecutionStep', {
    'id': fields.String(required=True, description='步骤ID', example='OP01'),
    'name': fields.String(required=True, description='步骤名称', example='数据清洗'),
    'script': fields.String(required=True, description='脚本文件名', example='VC_OP01_cleaning.py'),
    'description': fields.String(description='步骤描述'),
    'category': fields.String(description='步骤分类', enum=['preparation', 'processing', 'database', 'transformation', 'output']),
    'dependencies': fields.List(fields.String, description='依赖的步骤ID'),
    'estimated_time': fields.String(description='预计执行时间', example='2-5分钟')
})

# 执行结果模型
execution_result_model = ns.model('ExecutionResult', {
    'success': fields.Boolean(description='执行是否成功'),
    'stdout': fields.String(description='标准输出'),
    'stderr': fields.String(description='错误输出'),
    'message': fields.String(description='执行消息'),
    'execution_time': fields.Float(description='执行时间(秒)')
})

# 执行历史记录模型
execution_history_model = ns.model('ExecutionHistory', {
    'id': fields.Integer(description='记录ID'),
    'timestamp': fields.String(description='执行时间'),
    'step_id': fields.String(description='步骤ID'),
    'step_name': fields.String(description='步骤名称'),
    'script_name': fields.String(description='脚本名称'),
    'success': fields.Boolean(description='执行是否成功'),
    'message': fields.String(description='执行消息'),
    'stdout': fields.String(description='标准输出'),
    'stderr': fields.String(description='错误输出'),
    'execution_time': fields.Float(description='执行时间(秒)'),
    'study_id': fields.String(description='研究ID')
})

# 当前步骤状态模型
current_step_status_model = ns.model('CurrentStepStatus', {
    'step_id': fields.String(description='步骤ID'),
    'step_name': fields.String(description='步骤名称'),
    'result': fields.Nested(execution_result_model),
    'timestamp': fields.String(description='最后执行时间'),
    'execution_time': fields.Float(description='执行时间(秒)')
})


@ns.route('/status')
class ExecutionStatus(Resource):
    """执行状态查询"""
    
    @ns.doc('get_execution_status')
    @ns.response(200, '获取成功', ns.model('ExecutionStatusResponse', {
        'status': fields.String(example='success'),
        'data': fields.Nested(execution_status_model)
    }))
    def get(self):
        """
        获取流程执行状态
        
        返回当前流程的整体执行状态，包括各步骤的完成情况
        """
        try:
            execution_service = ExecutionService()
            status_data = execution_service.get_execution_status()
            
            return {
                'status': 'success',
                'data': status_data
            }
        except Exception as e:
            ns.abort(500, f'获取执行状态失败: {str(e)}')


@ns.route('/start')
class ExecutionStart(Resource):
    """开始执行流程"""
    
    @ns.doc('start_execution')
    @ns.expect(ns.model('StartExecutionRequest', {
        'study_id': fields.String(description='研究ID', example='CIRCULATE')
    }))
    @ns.response(200, '启动成功')
    @ns.response(400, '请求参数错误')
    @ns.response(500, '服务器错误')
    def post(self):
        """
        开始执行完整的数据处理流程
        
        启动后台线程执行所有数据处理步骤
        """
        try:
            data = request.get_json() or {}
            study_id = data.get('study_id')
            
            execution_service = ExecutionService()
            result = execution_service.start_execution(study_id)
            
            return {
                'status': 'success',
                'message': result['message'],
                'execution_id': result.get('execution_id')
            }
        except ValueError as e:
            ns.abort(400, f'参数错误: {str(e)}')
        except Exception as e:
            ns.abort(500, f'启动执行失败: {str(e)}')


@ns.route('/stop')
class ExecutionStop(Resource):
    """停止执行流程"""
    
    @ns.doc('stop_execution')
    @ns.response(200, '停止成功')
    def post(self):
        """
        停止当前正在执行的流程
        
        将正在运行的流程设置为暂停状态
        """
        try:
            execution_service = ExecutionService()
            result = execution_service.stop_execution()
            
            return {
                'status': 'success',
                'message': result['message']
            }
        except Exception as e:
            ns.abort(500, f'停止执行失败: {str(e)}')


@ns.route('/reset')
class ExecutionReset(Resource):
    """重置执行流程"""
    
    @ns.doc('reset_execution')
    @ns.response(200, '重置成功')
    def post(self):
        """
        重置流程执行状态
        
        将流程状态重置为初始状态，清除执行进度
        """
        try:
            execution_service = ExecutionService()
            result = execution_service.reset_execution()
            
            return {
                'status': 'success',
                'message': result['message']
            }
        except Exception as e:
            ns.abort(500, f'重置执行失败: {str(e)}')


@ns.route('/run-step')
class ExecutionRunStep(Resource):
    """执行单个步骤"""
    
    @ns.doc('run_single_step')
    @ns.expect(ns.model('RunStepRequest', {
        'step_name': fields.String(required=True, description='步骤名称', example='数据清洗'),
        'script_name': fields.String(required=True, description='脚本文件名', example='VC_OP01_cleaning.py')
    }))
    @ns.response(200, '执行完成', ns.model('RunStepResponse', {
        'status': fields.String(example='success'),
        'data': fields.Nested(execution_result_model)
    }))
    @ns.response(400, '请求参数错误')
    def post(self):
        """
        执行指定的单个处理步骤
        
        独立执行某个特定的数据处理步骤
        """
        try:
            data = request.get_json()
            step_name = data.get('step_name')
            script_name = data.get('script_name')
            
            if not step_name or not script_name:
                ns.abort(400, '缺少必要参数: step_name 或 script_name')
            
            execution_service = ExecutionService()
            result = execution_service.run_single_step(step_name, script_name)
            
            return {
                'status': 'success' if result['success'] else 'error',
                'data': result
            }
        except Exception as e:
            ns.abort(500, f'执行步骤失败: {str(e)}')


@ns.route('/run-steps')
class ExecutionRunSteps(Resource):
    """执行多个步骤"""
    
    @ns.doc('run_multiple_steps')
    @ns.expect(ns.model('RunStepsRequest', {
        'step_ids': fields.List(fields.String, required=True, description='步骤ID列表', example=['OP01', 'OP02'])
    }))
    @ns.response(200, '执行完成')
    @ns.response(400, '请求参数错误')
    def post(self):
        """
        按顺序执行指定的多个步骤
        
        用户可以选择要执行的步骤，系统将按依赖关系顺序执行
        """
        try:
            data = request.get_json()
            step_ids = data.get('step_ids', [])
            
            if not step_ids:
                ns.abort(400, '未选择要执行的步骤')
            
            execution_service = ExecutionService()
            result = execution_service.run_multiple_steps(step_ids)
            
            return {
                'status': 'success',
                'data': result
            }
        except Exception as e:
            ns.abort(500, f'执行多步骤失败: {str(e)}')


@ns.route('/steps')
class ExecutionSteps(Resource):
    """获取执行步骤列表"""
    
    @ns.doc('get_execution_steps')
    @ns.response(200, '获取成功', ns.model('StepsResponse', {
        'status': fields.String(example='success'),
        'data': fields.List(fields.Nested(execution_step_model))
    }))
    def get(self):
        """
        获取所有可执行的处理步骤
        
        返回完整的数据处理步骤列表，包括步骤信息和依赖关系
        """
        try:
            execution_service = ExecutionService()
            steps = execution_service.get_available_steps()
            
            return {
                'status': 'success',
                'data': steps
            }
        except Exception as e:
            ns.abort(500, f'获取步骤列表失败: {str(e)}')


@ns.route('/history')
class ExecutionHistory(Resource):
    """执行历史管理"""
    
    @ns.doc('get_execution_history')
    @ns.expect(ns.parser().add_argument('limit', type=int, help='返回条数', location='args', default=50)
                           .add_argument('step_id', type=str, help='步骤ID过滤', location='args'))
    @ns.response(200, '获取成功', ns.model('HistoryResponse', {
        'status': fields.String(example='success'),
        'data': fields.List(fields.Nested(execution_history_model))
    }))
    def get(self):
        """
        获取执行历史记录
        
        查看历史执行记录，支持按步骤ID过滤
        """
        try:
            limit = int(request.args.get('limit', 50))
            step_id = request.args.get('step_id', '')
            
            execution_service = ExecutionService()
            history = execution_service.get_execution_history(limit, step_id)
            
            return {
                'status': 'success',
                'data': history
            }
        except Exception as e:
            ns.abort(500, f'获取执行历史失败: {str(e)}')


@ns.route('/history/clear')
class ExecutionHistoryClear(Resource):
    """清空执行历史"""
    
    @ns.doc('clear_execution_history')
    @ns.response(200, '清空成功')
    def post(self):
        """
        清空所有执行历史记录
        
        删除所有历史执行记录，该操作不可恢复
        """
        try:
            execution_service = ExecutionService()
            result = execution_service.clear_execution_history()
            
            return {
                'status': 'success',
                'message': result['message'],
                'cleared_count': result['cleared_count']
            }
        except Exception as e:
            ns.abort(500, f'清空执行历史失败: {str(e)}')


@ns.route('/status-current')
class ExecutionCurrentStatus(Resource):
    """当前步骤状态"""
    
    @ns.doc('get_current_step_status')
    @ns.response(200, '获取成功', ns.model('CurrentStatusResponse', {
        'status': fields.String(example='success'),
        'data': fields.List(fields.Nested(current_step_status_model))
    }))
    def get(self):
        """
        获取各步骤的当前执行状态
        
        返回每个步骤的最新执行结果和状态
        """
        try:
            execution_service = ExecutionService()
            current_status = execution_service.get_current_execution_status()
            
            return {
                'status': 'success',
                'data': current_status
            }
        except Exception as e:
            ns.abort(500, f'获取当前状态失败: {str(e)}')
