#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VAPORCONE 日志服务模块

提供日志管理的业务逻辑，包括：
- 日志存储和检索
- 日志过滤和搜索
- 日志统计分析
- 日志导出
- 实时日志推送
"""

import os
import json
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


class LogService:
    """日志服务类"""
    
    def __init__(self):
        """初始化日志服务"""
        # 全局日志存储 - 在实际应用中可以考虑使用数据库或Redis
        self.system_logs = []
        self.log_id_counter = 0
        
        # 日志级别定义
        self.log_levels = {
            'DEBUG': {'value': 10, 'description': '调试信息', 'color': '#6c757d'},
            'INFO': {'value': 20, 'description': '一般信息', 'color': '#17a2b8'},
            'WARNING': {'value': 30, 'description': '警告信息', 'color': '#ffc107'},
            'ERROR': {'value': 40, 'description': '错误信息', 'color': '#dc3545'},
            'CRITICAL': {'value': 50, 'description': '严重错误', 'color': '#6f42c1'}
        }
    
    def add_log(self, level: str, module: str, message: str, details: Optional[str] = None) -> Dict[str, Any]:
        """添加系统日志记录"""
        self.log_id_counter += 1
        log_entry = {
            'id': self.log_id_counter,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'level': level,
            'module': module,
            'message': message,
            'details': details
        }
        
        # 添加到系统日志列表
        self.system_logs.append(log_entry)
        
        # 保持日志数量在合理范围内（最多保留1000条）
        if len(self.system_logs) > 1000:
            self.system_logs = self.system_logs[-1000:]
        
        return log_entry
    
    def get_logs(self, level: str = 'all', limit: int = 100, search: str = '',
                 module: str = '', start_time: str = '', end_time: str = '') -> Dict[str, Any]:
        """获取日志列表"""
        
        # 验证参数
        if limit < 1 or limit > 1000:
            raise ValueError("limit参数必须在1-1000之间")
        
        if level != 'all' and level not in self.log_levels:
            raise ValueError(f"无效的日志级别: {level}")
        
        # 过滤日志
        filtered_logs = self.system_logs.copy()
        
        # 按级别过滤
        if level != 'all':
            filtered_logs = [log for log in filtered_logs if log['level'] == level]
        
        # 按模块过滤
        if module:
            filtered_logs = [log for log in filtered_logs if module.lower() in log['module'].lower()]
        
        # 按关键词搜索
        if search:
            search_lower = search.lower()
            filtered_logs = [
                log for log in filtered_logs 
                if search_lower in log['message'].lower() or 
                   search_lower in log['module'].lower() or
                   (log['details'] and search_lower in log['details'].lower())
            ]
        
        # 按时间范围过滤
        if start_time:
            try:
                start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                filtered_logs = [
                    log for log in filtered_logs 
                    if datetime.strptime(log['timestamp'][:19], '%Y-%m-%d %H:%M:%S') >= start_dt
                ]
            except ValueError:
                raise ValueError("start_time格式错误，应为 YYYY-MM-DD HH:MM:SS")
        
        if end_time:
            try:
                end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                filtered_logs = [
                    log for log in filtered_logs 
                    if datetime.strptime(log['timestamp'][:19], '%Y-%m-%d %H:%M:%S') <= end_dt
                ]
            except ValueError:
                raise ValueError("end_time格式错误，应为 YYYY-MM-DD HH:MM:SS")
        
        # 按时间倒序排列并限制数量
        filtered_logs = list(reversed(filtered_logs))[:limit]
        
        return {
            'logs': filtered_logs,
            'total': len(self.system_logs),
            'filtered': len(filtered_logs)
        }
    
    def clear_logs(self) -> int:
        """清空系统日志"""
        cleared_count = len(self.system_logs)
        self.system_logs = []
        
        # 添加清空日志的记录
        self.add_log('INFO', 'LogSystem', '系统日志已清空', f'清空了{cleared_count}条日志记录')
        
        return cleared_count
    
    def get_log_statistics(self, period: str = '24h') -> Dict[str, Any]:
        """获取日志统计信息"""
        
        # 计算时间范围
        now = datetime.now()
        if period == '1h':
            start_time = now - timedelta(hours=1)
        elif period == '6h':
            start_time = now - timedelta(hours=6)
        elif period == '24h':
            start_time = now - timedelta(hours=24)
        elif period == '7d':
            start_time = now - timedelta(days=7)
        else:
            start_time = now - timedelta(hours=24)
        
        # 筛选时间范围内的日志
        period_logs = []
        for log in self.system_logs:
            log_time = datetime.strptime(log['timestamp'][:19], '%Y-%m-%d %H:%M:%S')
            if log_time >= start_time:
                period_logs.append(log)
        
        # 统计各级别日志数量
        level_stats = {level: 0 for level in self.log_levels}
        for log in period_logs:
            if log['level'] in level_stats:
                level_stats[log['level']] += 1
        
        # 统计各模块日志数量
        module_stats = {}
        for log in period_logs:
            module = log['module']
            if module in module_stats:
                module_stats[module] += 1
            else:
                module_stats[module] = 1
        
        # 转换为列表格式，按数量排序
        module_list = [
            {'module': module, 'count': count}
            for module, count in sorted(module_stats.items(), key=lambda x: x[1], reverse=True)
        ]
        
        # 生成时间线统计（按小时）
        timeline_stats = {}
        for log in period_logs:
            log_hour = log['timestamp'][:13] + ':00'  # 截取到小时
            if log_hour in timeline_stats:
                timeline_stats[log_hour] += 1
            else:
                timeline_stats[log_hour] = 1
        
        timeline_list = [
            {'hour': hour, 'count': count}
            for hour, count in sorted(timeline_stats.items())
        ]
        
        return {
            'total_logs': len(period_logs),
            'levels': level_stats,
            'modules': module_list,
            'timeline': timeline_list
        }
    
    def export_logs(self, format: str = 'csv', level: str = 'all', 
                   start_time: str = '', end_time: str = '') -> str:
        """导出日志文件"""
        
        # 获取要导出的日志
        logs_result = self.get_logs(
            level=level,
            limit=10000,  # 导出时不限制数量
            start_time=start_time,
            end_time=end_time
        )
        logs = logs_result['logs']
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'vaporcone_logs_{timestamp}.{format}'
        filepath = os.path.join(os.path.dirname(__file__), '..', 'temp', filename)
        
        # 确保临时目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 根据格式导出
        if format == 'csv':
            self._export_to_csv(logs, filepath)
        elif format == 'json':
            self._export_to_json(logs, filepath)
        elif format == 'txt':
            self._export_to_txt(logs, filepath)
        else:
            raise ValueError(f"不支持的导出格式: {format}")
        
        return filepath
    
    def get_available_log_levels(self) -> List[Dict[str, Any]]:
        """获取可用的日志级别"""
        return [
            {
                'level': level,
                'value': info['value'],
                'description': info['description'],
                'color': info['color']
            }
            for level, info in self.log_levels.items()
        ]
    
    def get_log_modules(self) -> List[Dict[str, Any]]:
        """获取日志模块列表"""
        module_counts = {}
        for log in self.system_logs:
            module = log['module']
            if module in module_counts:
                module_counts[module] += 1
            else:
                module_counts[module] = 1
        
        return [
            {
                'module': module,
                'count': count,
                'last_log_time': self._get_last_log_time(module)
            }
            for module, count in sorted(module_counts.items(), key=lambda x: x[1], reverse=True)
        ]
    
    def _export_to_csv(self, logs: List[Dict], filepath: str):
        """导出为CSV格式"""
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['timestamp', 'level', 'module', 'message', 'details']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for log in logs:
                writer.writerow({
                    'timestamp': log['timestamp'],
                    'level': log['level'],
                    'module': log['module'],
                    'message': log['message'],
                    'details': log['details'] or ''
                })
    
    def _export_to_json(self, logs: List[Dict], filepath: str):
        """导出为JSON格式"""
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump({
                'export_time': datetime.now().isoformat(),
                'total_logs': len(logs),
                'logs': logs
            }, jsonfile, ensure_ascii=False, indent=2)
    
    def _export_to_txt(self, logs: List[Dict], filepath: str):
        """导出为TXT格式"""
        with open(filepath, 'w', encoding='utf-8') as txtfile:
            txtfile.write("VAPORCONE 系统日志导出\n")
            txtfile.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            txtfile.write(f"总日志数: {len(logs)}\n")
            txtfile.write("=" * 80 + "\n\n")
            
            for log in logs:
                txtfile.write(f"时间: {log['timestamp']}\n")
                txtfile.write(f"级别: {log['level']}\n")
                txtfile.write(f"模块: {log['module']}\n")
                txtfile.write(f"消息: {log['message']}\n")
                if log['details']:
                    txtfile.write(f"详情: {log['details']}\n")
                txtfile.write("-" * 40 + "\n\n")
    
    def _get_last_log_time(self, module: str) -> str:
        """获取指定模块的最后日志时间"""
        for log in reversed(self.system_logs):
            if log['module'] == module:
                return log['timestamp']
        return "无记录"
