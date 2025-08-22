#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VAPORCONE 系统服务模块

提供系统状态监控和管理的业务逻辑，包括：
- 系统资源监控
- 数据库连接状态检查
- 研究项目管理
- 健康检查
"""

import os
import sys
import platform
from datetime import datetime, timedelta


class SystemService:
    """系统服务类"""
    
    def __init__(self):
        """初始化系统服务"""
        self.start_time = datetime.now()
        
        # 尝试导入VAPORCONE模块
        self.vaporcone_available = False
        try:
            # 添加父目录到Python路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            grandparent_dir = os.path.dirname(parent_dir)
            grandparent_dir = os.path.dirname(grandparent_dir)  # 回到项目根目录
            sys.path.insert(0, grandparent_dir)
            
            from VC_BC01_constant import STUDY_ID, ROOT_PATH, RAW_DATA_ROOT_PATH, DB_HOST, DB_DATABASE
            from VC_BC02_baseUtils import DatabaseManager
            self.vaporcone_available = True
            
            # 存储VAPORCONE相关变量
            self.study_id = STUDY_ID
            self.root_path = ROOT_PATH
            self.raw_data_root_path = RAW_DATA_ROOT_PATH
            self.db_host = DB_HOST
            self.db_database = DB_DATABASE
            
        except ImportError as e:
            print(f"⚠️ VAPORCONE模块未加载: {e}")
            self.vaporcone_available = False
            
            # 提供默认值
            self.study_id = 'UNKNOWN'
            self.root_path = ''
            self.raw_data_root_path = ''
            self.db_host = ''
            self.db_database = ''
    
    def get_system_status(self):
        """获取系统状态信息"""
        try:
            import psutil
            
            # 获取真实的系统资源使用情况
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 检查数据库连接状态
            db_status = self._check_database_connection()
            
            return {
                'cpu': round(cpu_percent, 1),
                'memory': round(memory.used / (1024**3), 1),  # GB
                'memory_total': round(memory.total / (1024**3), 1),
                'memory_percent': round(memory.percent, 1),
                'disk': round(disk.percent, 1),
                'disk_used': round(disk.used / (1024**3), 1),
                'disk_total': round(disk.total / (1024**3), 1),
                'database': db_status,
                'platform': platform.system(),
                'python_version': platform.python_version(),
                'timestamp': datetime.now().isoformat()
            }
        except ImportError:
            # 如果没有psutil，提供基本的模拟数据
            return {
                'cpu': 0,
                'memory': 0,
                'memory_total': 8,
                'memory_percent': 0,
                'disk': 0,
                'disk_used': 0,
                'disk_total': 100,
                'database': 'connected' if self.vaporcone_available else 'disconnected',
                'platform': platform.system(),
                'python_version': platform.python_version(),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_studies_list(self):
        """获取可用的研究列表"""
        studies = []
        
        if not self.vaporcone_available:
            raise Exception("系统核心模块未加载，无法获取研究列表")
        
        study_specific_path = os.path.join(self.root_path, 'studySpecific')
        
        if os.path.exists(study_specific_path):
            for item in os.listdir(study_specific_path):
                item_path = os.path.join(study_specific_path, item)
                if os.path.isdir(item_path):
                    config_file = os.path.join(item_path, f'{item}_OperationConf.xlsx')
                    studies.append({
                        'id': item,
                        'name': item,
                        'config_exists': os.path.exists(config_file),
                        'status': 'active' if item == self.study_id else 'inactive'
                    })
        
        return studies
    
    def perform_health_check(self):
        """执行系统健康检查"""
        checks = []
        overall_status = 'healthy'
        
        # 检查VAPORCONE模块
        vaporcone_status = self.vaporcone_available
        checks.append({
            'name': 'VAPORCONE模块',
            'status': 'pass' if vaporcone_status else 'fail',
            'message': '核心模块已加载' if vaporcone_status else '核心模块未加载'
        })
        
        # 检查数据库连接
        db_status = self._check_database_connection()
        db_connected = db_status == 'connected'
        checks.append({
            'name': '数据库连接',
            'status': 'pass' if db_connected else 'fail',
            'message': '数据库连接正常' if db_connected else '数据库连接失败'
        })
        
        # 检查磁盘空间
        disk_ok = self._check_disk_space()
        checks.append({
            'name': '磁盘空间',
            'status': 'pass' if disk_ok else 'warning',
            'message': '磁盘空间充足' if disk_ok else '磁盘空间不足'
        })
        
        # 检查内存使用
        memory_ok = self._check_memory_usage()
        checks.append({
            'name': '内存使用',
            'status': 'pass' if memory_ok else 'warning',
            'message': '内存使用正常' if memory_ok else '内存使用过高'
        })
        
        # 计算运行时间
        uptime = datetime.now() - self.start_time
        uptime_str = self._format_uptime(uptime)
        
        # 确定整体状态
        failed_checks = [c for c in checks if c['status'] == 'fail']
        warning_checks = [c for c in checks if c['status'] == 'warning']
        
        if failed_checks:
            overall_status = 'error'
        elif warning_checks:
            overall_status = 'warning'
        
        return {
            'status': overall_status,
            'vaporcone_modules': vaporcone_status,
            'database_connection': db_connected,
            'disk_space': disk_ok,
            'memory_usage': memory_ok,
            'uptime': uptime_str,
            'checks': checks
        }
    
    def get_system_info(self):
        """获取系统基本信息"""
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'python_implementation': platform.python_implementation(),
            'vaporcone_status': 'loaded' if self.vaporcone_available else 'not_loaded',
            'current_study': self.study_id,
            'root_path': self.root_path,
            'start_time': self.start_time.isoformat()
        }
    
    def get_system_metrics(self, period='1h'):
        """获取系统性能指标历史数据"""
        # 这里应该从实际的监控数据库或缓存中获取历史数据
        # 目前返回模拟数据
        
        now = datetime.now()
        if period == '1h':
            delta = timedelta(hours=1)
            interval = timedelta(minutes=5)
        elif period == '6h':
            delta = timedelta(hours=6)
            interval = timedelta(minutes=30)
        elif period == '24h':
            delta = timedelta(hours=24)
            interval = timedelta(hours=2)
        else:
            delta = timedelta(hours=1)
            interval = timedelta(minutes=5)
        
        start_time = now - delta
        metrics = []
        
        current_time = start_time
        while current_time <= now:
            # 模拟数据 - 在实际应用中应该从监控系统获取
            metrics.append({
                'timestamp': current_time.isoformat(),
                'cpu': round(20 + (current_time.minute % 30), 1),
                'memory': round(4.0 + (current_time.minute % 20) * 0.1, 1),
                'disk': round(60 + (current_time.hour % 10), 1)
            })
            current_time += interval
        
        return {
            'period': period,
            'metrics': metrics,
            'summary': {
                'avg_cpu': sum(m['cpu'] for m in metrics) / len(metrics),
                'avg_memory': sum(m['memory'] for m in metrics) / len(metrics),
                'avg_disk': sum(m['disk'] for m in metrics) / len(metrics)
            }
        }
    
    def _check_database_connection(self):
        """检查数据库连接状态"""
        if not self.vaporcone_available:
            return 'disconnected'
        
        try:
            from VC_BC02_baseUtils import DatabaseManager
            db = DatabaseManager()
            db.connect()
            if db.connection:
                db.disconnect()
                return 'connected'
            else:
                return 'disconnected'
        except Exception:
            return 'disconnected'
    
    def _check_disk_space(self):
        """检查磁盘空间是否充足"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            return disk.percent < 90  # 磁盘使用率小于90%认为正常
        except ImportError:
            return True  # 无法检查则假设正常
    
    def _check_memory_usage(self):
        """检查内存使用是否正常"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return memory.percent < 85  # 内存使用率小于85%认为正常
        except ImportError:
            return True  # 无法检查则假设正常
    
    def _format_uptime(self, uptime):
        """格式化运行时间"""
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}天 {hours}小时 {minutes}分钟"
        elif hours > 0:
            return f"{hours}小时 {minutes}分钟"
        else:
            return f"{minutes}分钟"
