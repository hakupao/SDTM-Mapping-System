#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VAPORCONE 执行服务模块

提供流程执行管理的业务逻辑，包括：
- 流程控制和调度
- 脚本执行管理
- 执行状态跟踪
- 执行历史记录
- 依赖关系处理
"""

import os
import sys
import subprocess
import threading
import time
from datetime import datetime
from typing import List, Dict, Any, Optional


class ExecutionService:
    """执行服务类"""
    
    def __init__(self):
        """初始化执行服务"""
        
        # 全局执行状态
        self.current_execution = {
            'status': 'idle',  # idle, running, paused, completed, error
            'current_step': 0,
            'total_steps': 8,
            'start_time': None,
            'logs': []
        }
        
        # 全局执行历史记录存储
        self.execution_history = []
        self.execution_history_id_counter = 0
        
        # 尝试导入VAPORCONE模块
        self.vaporcone_available = False
        try:
            # 添加父目录到Python路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            grandparent_dir = os.path.dirname(parent_dir)
            grandparent_dir = os.path.dirname(grandparent_dir)  # 回到项目根目录
            sys.path.insert(0, grandparent_dir)
            
            from VC_BC01_constant import STUDY_ID
            self.vaporcone_available = True
            self.study_id = STUDY_ID
            self.grandparent_dir = grandparent_dir
            
        except ImportError as e:
            print(f"⚠️ VAPORCONE模块未加载: {e}")
            self.vaporcone_available = False
            self.study_id = 'UNKNOWN'
            self.grandparent_dir = ''
        
        # 步骤定义
        self.steps_definition = [
            {
                'id': 'OP00',
                'name': '配置检查',
                'script': 'VC_OP00_checkConfig.py',
                'description': '检查配置文件完整性和有效性',
                'category': 'preparation',
                'dependencies': [],
                'estimated_time': '30秒'
            },
            {
                'id': 'OP01',
                'name': '数据清洗',
                'script': 'VC_OP01_cleaning.py',
                'description': '清洗原始数据，处理异常值和缺失值',
                'category': 'processing',
                'dependencies': ['OP00'],
                'estimated_time': '2-5分钟'
            },
            {
                'id': 'OP02',
                'name': '代码列表插入',
                'script': 'VC_OP02_insertCodeList.py',
                'description': '将代码列表数据插入数据库',
                'category': 'database',
                'dependencies': ['OP00'],
                'estimated_time': '1分钟'
            },
            {
                'id': 'OP03',
                'name': '元数据插入',
                'script': 'VC_OP03_insertMetadata.py',
                'description': '将处理后的元数据插入数据库',
                'category': 'database',
                'dependencies': ['OP01', 'OP02'],
                'estimated_time': '3-8分钟'
            },
            {
                'id': 'OP04',
                'name': '格式化',
                'script': 'VC_OP04_format.py',
                'description': '格式化数据为标准SDTM结构',
                'category': 'transformation',
                'dependencies': ['OP03'],
                'estimated_time': '2-6分钟'
            },
            {
                'id': 'OP05',
                'name': '映射转换',
                'script': 'VC_OP05_mapping.py',
                'description': '执行数据映射和SDTM标准转换',
                'category': 'transformation',
                'dependencies': ['OP04'],
                'estimated_time': '5-15分钟'
            },
            {
                'id': 'PS01',
                'name': 'CSV生成',
                'script': 'VC_PS01_makeInputCSV.py',
                'description': '生成标准SDTM CSV文件',
                'category': 'output',
                'dependencies': ['OP05'],
                'estimated_time': '1-3分钟'
            },
            {
                'id': 'PS02',
                'name': 'JSON转换',
                'script': 'VC_PS02_csv2json.py',
                'description': '将CSV转换为JSON格式并打包',
                'category': 'output',
                'dependencies': ['PS01'],
                'estimated_time': '1-2分钟'
            }
        ]
    
    def get_execution_status(self) -> Dict[str, Any]:
        """获取执行状态"""
        total_steps = len(self.steps_definition)
        
        if not self.execution_history:
            # 没有执行历史
            return {
                'total': total_steps,
                'completed': 0,
                'running': 0,
                'pending': total_steps,
                'failed': 0,
                'last_execution': None,
                'execution_status': 'idle'
            }
        
        # 统计各步骤的最新状态
        step_status = {}
        for record in self.execution_history:
            step_id = record['step_id']
            if step_id not in step_status or record['timestamp'] > step_status[step_id]['timestamp']:
                step_status[step_id] = record
        
        completed = sum(1 for s in step_status.values() if s['success'])
        failed = sum(1 for s in step_status.values() if not s['success'])
        executed = len(step_status)
        pending = total_steps - executed
        
        # 获取最近的执行记录
        latest_record = max(self.execution_history, key=lambda x: x['timestamp']) if self.execution_history else None
        
        return {
            'total': total_steps,
            'completed': completed,
            'running': 0,  # 当前没有正在运行的
            'pending': pending,
            'failed': failed,
            'last_execution': latest_record['timestamp'] if latest_record else None,
            'execution_status': self.current_execution.get('status', 'idle')
        }
    
    def start_execution(self, study_id: Optional[str] = None) -> Dict[str, str]:
        """开始执行流程"""
        if not self.vaporcone_available:
            raise Exception("VAPORCONE模块未加载，无法执行流程")
        
        if self.current_execution['status'] == 'running':
            raise Exception("已有流程正在执行中")
        
        # 更新执行状态
        self.current_execution['status'] = 'running'
        self.current_execution['start_time'] = datetime.now().isoformat()
        self.current_execution['current_step'] = 0
        
        # 启动后台执行线程
        execution_thread = threading.Thread(
            target=self._execute_pipeline,
            args=(study_id or self.study_id,)
        )
        execution_thread.daemon = True
        execution_thread.start()
        
        return {
            'message': '流程开始执行',
            'execution_id': f'exec_{int(time.time())}'
        }
    
    def stop_execution(self) -> Dict[str, str]:
        """停止执行流程"""
        self.current_execution['status'] = 'paused'
        return {'message': '流程已暂停'}
    
    def reset_execution(self) -> Dict[str, str]:
        """重置执行流程"""
        self.current_execution.update({
            'status': 'idle',
            'current_step': 0,
            'start_time': None,
            'logs': []
        })
        return {'message': '流程已重置'}
    
    def run_single_step(self, step_name: str, script_name: str) -> Dict[str, Any]:
        """执行单个步骤"""
        return self._execute_script(script_name, step_name)
    
    def run_multiple_steps(self, step_ids: List[str]) -> Dict[str, Any]:
        """执行多个指定步骤"""
        if not self.vaporcone_available:
            raise Exception("VAPORCONE模块未加载，无法执行步骤")
        
        # 获取步骤映射
        step_mapping = {step['id']: (step['name'], step['script']) for step in self.steps_definition}
        
        # 更新执行状态
        self.current_execution['status'] = 'running'
        self.current_execution['start_time'] = datetime.now().isoformat()
        self.current_execution['current_step'] = 0
        
        results = []
        
        # 逐步执行选择的步骤
        for i, step_id in enumerate(step_ids):
            if step_id not in step_mapping:
                continue
                
            if self.current_execution['status'] != 'running':
                break
                
            step_name, script_name = step_mapping[step_id]
            self.current_execution['current_step'] = i
            
            # 执行脚本
            result = self._execute_script(script_name, step_name, i)
            results.append({
                'step_id': step_id,
                'step_name': step_name,
                'result': result
            })
            
            if not result['success']:
                self.current_execution['status'] = 'error'
                break
        
        if self.current_execution['status'] == 'running':
            self.current_execution['status'] = 'completed'
            self.current_execution['current_step'] = len(step_ids)
        
        return {
            'execution_status': self.current_execution['status'],
            'results': results
        }
    
    def get_available_steps(self) -> List[Dict[str, Any]]:
        """获取可用的执行步骤列表"""
        return self.steps_definition
    
    def get_execution_history(self, limit: int = 50, step_id: str = '') -> List[Dict[str, Any]]:
        """获取执行历史记录"""
        # 过滤历史记录
        filtered_history = self.execution_history
        
        if step_id:
            filtered_history = [record for record in filtered_history if record['step_id'] == step_id]
        
        # 按时间倒序并限制数量
        filtered_history = list(reversed(filtered_history))[:limit]
        
        return filtered_history
    
    def clear_execution_history(self) -> Dict[str, Any]:
        """清空执行历史记录"""
        cleared_count = len(self.execution_history)
        self.execution_history = []
        
        # 添加日志记录
        from services.log_service import LogService
        log_service = LogService()
        log_service.add_log('INFO', 'ExecutionHistory', '执行历史记录已清空', f'清空了{cleared_count}条记录')
        
        return {
            'message': '执行历史已清空',
            'cleared_count': cleared_count
        }
    
    def get_current_execution_status(self) -> List[Dict[str, Any]]:
        """获取当前执行状态（基于历史记录）"""
        if not self.execution_history:
            return []  # 返回空数组
        
        # 按步骤ID分组，获取每个步骤的最新执行状态
        step_status = {}
        for record in self.execution_history:
            step_id = record['step_id']
            if step_id not in step_status or record['timestamp'] > step_status[step_id]['timestamp']:
                step_status[step_id] = {
                    'step_id': step_id,
                    'step_name': record['step_name'],
                    'result': {
                        'success': record['success'],
                        'message': record['message'],
                        'stdout': record['stdout'],
                        'stderr': record['stderr']
                    },
                    'timestamp': record['timestamp'],
                    'execution_time': record['execution_time']
                }
        
        return list(step_status.values())
    
    def _execute_script(self, script_name: str, step_name: str, step_index: Optional[int] = None) -> Dict[str, Any]:
        """执行单个脚本"""
        try:
            if not self.vaporcone_available:
                raise Exception("VAPORCONE模块未加载，无法执行脚本")
            
            # 获取脚本路径
            script_path = os.path.join(self.grandparent_dir, script_name)
            
            if not os.path.exists(script_path):
                raise Exception(f"脚本文件不存在: {script_path}")
            
            # 记录开始执行的日志
            from services.log_service import LogService
            log_service = LogService()
            log_service.add_log('INFO', 'ProcessExecution', f'开始执行: {step_name}', f'脚本: {script_name}')
            
            # 执行Python脚本
            start_time = time.time()
            result = subprocess.run(
                [sys.executable, script_path], 
                capture_output=True, 
                text=True,
                cwd=self.grandparent_dir,  # 设置工作目录
                timeout=300  # 5分钟超时
            )
            execution_time = round(time.time() - start_time, 2)
            
            # 检查执行结果
            if result.returncode == 0:
                message = f"{step_name} 执行成功"
                
                # 记录成功日志
                log_details = f"执行时间: {execution_time}秒"
                if result.stdout:
                    # 截取输出前500字符
                    stdout_preview = result.stdout[:500]
                    if len(result.stdout) > 500:
                        stdout_preview += "...(输出被截断)"
                    log_details += f"\n输出: {stdout_preview}"
                    message += f"\n输出: {stdout_preview}"
                
                log_service.add_log('INFO', 'ProcessExecution', f'{step_name} 执行成功', log_details)
                
            else:
                message = f"{step_name} 执行失败\n错误: {result.stderr}"
                
                # 记录错误日志
                error_details = f"执行时间: {execution_time}秒\n错误代码: {result.returncode}"
                if result.stderr:
                    error_details += f"\n错误信息: {result.stderr}"
                if result.stdout:
                    error_details += f"\n标准输出: {result.stdout}"
                
                log_service.add_log('ERROR', 'ProcessExecution', f'{step_name} 执行失败', error_details)
            
            # 构造返回结果
            script_result = {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'message': message,
                'execution_time': execution_time
            }
            
            # 推断step_id
            step_id = self._infer_step_id(script_name, step_name)
            
            # 添加执行历史记录
            self._add_execution_record(step_id, step_name, script_name, script_result, execution_time)
            
            return script_result
            
        except subprocess.TimeoutExpired:
            error_msg = f"{step_name} 执行超时"
            
            # 记录超时日志
            from services.log_service import LogService
            log_service = LogService()
            log_service.add_log('ERROR', 'ProcessExecution', f'{step_name} 执行超时', f'脚本: {script_name}, 超时时间: 300秒')
            
            # 记录超时的执行历史
            timeout_result = {'success': False, 'message': error_msg, 'stdout': '', 'stderr': '执行超时', 'execution_time': 300.0}
            step_id = self._infer_step_id(script_name, step_name)
            self._add_execution_record(step_id, step_name, script_name, timeout_result, 300.0)
            
            return timeout_result
            
        except Exception as e:
            error_msg = f"{step_name} 执行异常: {str(e)}"
            
            # 记录异常日志
            from services.log_service import LogService
            log_service = LogService()
            log_service.add_log('ERROR', 'ProcessExecution', f'{step_name} 执行异常', f'脚本: {script_name}\n异常信息: {str(e)}')
            
            # 记录异常的执行历史
            exception_result = {'success': False, 'message': error_msg, 'stdout': '', 'stderr': str(e), 'execution_time': None}
            step_id = self._infer_step_id(script_name, step_name)
            self._add_execution_record(step_id, step_name, script_name, exception_result, None)
            
            return exception_result
    
    def _execute_pipeline(self, study_id: str):
        """执行数据处理流水线"""
        try:
            for i, step in enumerate(self.steps_definition):
                if self.current_execution['status'] != 'running':
                    break
                    
                self.current_execution['current_step'] = i
                
                # 执行脚本
                result = self._execute_script(step['script'], step['name'], i)
                
                if not result['success']:
                    self.current_execution['status'] = 'error'
                    break
            
            if self.current_execution['status'] == 'running':
                self.current_execution['status'] = 'completed'
                self.current_execution['current_step'] = len(self.steps_definition)
                
        except Exception as e:
            self.current_execution['status'] = 'error'
            from services.log_service import LogService
            log_service = LogService()
            log_service.add_log('ERROR', 'ProcessExecution', f'流程执行出错: {str(e)}')
    
    def _add_execution_record(self, step_id: str, step_name: str, script_name: str, 
                            result: Dict[str, Any], execution_time: Optional[float]):
        """添加执行历史记录"""
        self.execution_history_id_counter += 1
        execution_record = {
            'id': self.execution_history_id_counter,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'step_id': step_id,
            'step_name': step_name,
            'script_name': script_name,
            'success': result.get('success', False),
            'message': result.get('message', ''),
            'stdout': result.get('stdout', ''),
            'stderr': result.get('stderr', ''),
            'execution_time': execution_time,
            'study_id': self.study_id
        }
        
        # 添加到执行历史列表
        self.execution_history.append(execution_record)
        
        # 保持历史记录数量在合理范围内（最多保留500条）
        if len(self.execution_history) > 500:
            self.execution_history = self.execution_history[-500:]
    
    def _infer_step_id(self, script_name: str, step_name: str) -> str:
        """从脚本名推断步骤ID"""
        if 'OP00' in script_name or '配置检查' in step_name:
            return 'OP00'
        elif 'OP01' in script_name or '数据清洗' in step_name:
            return 'OP01'
        elif 'OP02' in script_name or '代码列表' in step_name:
            return 'OP02'
        elif 'OP03' in script_name or '元数据' in step_name:
            return 'OP03'
        elif 'OP04' in script_name or '格式化' in step_name:
            return 'OP04'
        elif 'OP05' in script_name or '映射' in step_name:
            return 'OP05'
        elif 'PS01' in script_name or 'CSV' in step_name:
            return 'PS01'
        elif 'PS02' in script_name or 'JSON' in step_name:
            return 'PS02'
        else:
            return script_name.replace('.py', '').replace('VC_', '')
