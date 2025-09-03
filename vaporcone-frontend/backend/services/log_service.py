#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VAPORCONE 日志服务模块

提供日志管理的业务逻辑，包括：
- 日志存储和检索（内存+文件持久化）
- 日志过滤和搜索
- 日志统计分析
- 日志导出
- 实时日志推送
"""

import os
import json
import csv
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from threading import Lock


class LogService:
    """日志服务类"""
    
    def __init__(self):
        """初始化日志服务"""
        # 全局日志存储 - 内存缓存
        self.system_logs = []
        self.log_id_counter = 0
        
        # 线程安全锁
        self.log_lock = Lock()
        
        # 日志文件路径
        self.log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 当前日志文件
        self.current_log_file = os.path.join(
            self.log_dir, 
            f'vaporcone_{datetime.now().strftime("%Y%m%d")}.log'
        )
        
        # 日志级别定义
        self.log_levels = {
            'DEBUG': {'value': 10, 'description': '调试信息', 'color': '#6c757d'},
            'INFO': {'value': 20, 'description': '一般信息', 'color': '#17a2b8'},
            'WARNING': {'value': 30, 'description': '警告信息', 'color': '#ffc107'},
            'ERROR': {'value': 40, 'description': '错误信息', 'color': '#dc3545'},
            'CRITICAL': {'value': 50, 'description': '严重错误', 'color': '#6f42c1'}
        }
        
        # 设置文件日志记录器
        self._setup_file_logging()
        
        # 从文件加载历史日志
        self._load_historical_logs()
        
        # 实时日志回调函数列表
        self.real_time_callbacks = []
    
    def _setup_file_logging(self):
        """设置文件日志记录器"""
        try:
            # 创建格式化器
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S.%f'
            )
            
            # 创建文件处理器
            file_handler = logging.FileHandler(
                self.current_log_file, 
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)
            
            # 创建控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.INFO)
            
            # 配置根日志记录器
            self.logger = logging.getLogger('VAPORCONE')
            self.logger.setLevel(logging.DEBUG)
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
            
            # 避免日志重复
            self.logger.propagate = False
            
        except Exception as e:
            print(f"⚠️ 文件日志设置失败: {e}")
            self.logger = None
    
    def _load_historical_logs(self):
        """从文件加载历史日志"""
        try:
            if os.path.exists(self.current_log_file):
                with open(self.current_log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 解析日志文件中的日志条目
                for line in lines:
                    if line.strip():
                        log_entry = self._parse_log_line(line)
                        if log_entry:
                            self.system_logs.append(log_entry)
                            if log_entry['id'] > self.log_id_counter:
                                self.log_id_counter = log_entry['id']
                
                print(f"✅ 从文件加载了 {len(self.system_logs)} 条历史日志")
                
        except Exception as e:
            print(f"⚠️ 加载历史日志失败: {e}")
    
    def _parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """解析日志行"""
        try:
            # 尝试解析标准格式的日志行
            if '[' in line and ']' in line:
                parts = line.split('] [')
                if len(parts) >= 3:
                    timestamp = parts[0].replace('[', '').strip()
                    level = parts[1].strip()
                    module_message = parts[2].replace(']', '').strip()
                    
                    # 分离模块和消息
                    if ' ' in module_message:
                        module, message = module_message.split(' ', 1)
                    else:
                        module = module_message
                        message = ''
                    
                    # 验证时间戳格式
                    try:
                        datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        try:
                            datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            return None
                    
                    # 验证日志级别
                    if level not in self.log_levels:
                        return None
                    
                    self.log_id_counter += 1
                    return {
                        'id': self.log_id_counter,
                        'timestamp': timestamp,
                        'level': level,
                        'module': module,
                        'message': message,
                        'details': None
                    }
        except Exception:
            pass
        
        return None
    
    def add_log(self, level: str, module: str, message: str, details: Optional[str] = None) -> Dict[str, Any]:
        """添加系统日志记录"""
        with self.log_lock:
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
            
            # 保持日志数量在合理范围内（最多保留2000条）
            if len(self.system_logs) > 2000:
                self.system_logs = self.system_logs[-2000:]
            
            # 写入文件日志
            if self.logger:
                log_level = getattr(logging, level.upper(), logging.INFO)
                log_message = f"{module} {message}"
                if details:
                    log_message += f" | {details}"
                self.logger.log(log_level, log_message)
            
            # 触发实时日志推送
            self._notify_real_time_callbacks(log_entry)
            
            return log_entry
    
    def add_process_log(self, step_name: str, script_name: str, stdout: str, stderr: str, 
                       success: bool, execution_time: Optional[float] = None) -> Dict[str, Any]:
        """添加流程执行日志"""
        level = 'INFO' if success else 'ERROR'
        module = 'ProcessExecution'
        
        # 构建消息
        if success:
            message = f"{step_name} 执行成功"
            details = f"脚本: {script_name}"
            if execution_time:
                details += f"\n执行时间: {execution_time}秒"
            if stdout:
                # 截取输出前1000字符
                stdout_preview = stdout[:1000]
                if len(stdout) > 1000:
                    stdout_preview += f"\n...(输出被截断，总长度: {len(stdout)}字符)"
                details += f"\n输出:\n{stdout_preview}"
        else:
            message = f"{step_name} 执行失败"
            details = f"脚本: {script_name}"
            if execution_time:
                details += f"\n执行时间: {execution_time}秒"
            if stderr:
                details += f"\n错误信息:\n{stderr}"
            if stdout:
                details += f"\n标准输出:\n{stdout}"
        
        return self.add_log(level, module, message, details)
    
    def add_stream_log(self, step_name: str, stream_type: str, content: str) -> Dict[str, Any]:
        """添加流式日志（实时输出）"""
        level = 'INFO'
        module = f'ProcessStream_{step_name}'
        
        # 截取内容长度
        if len(content) > 500:
            content = content[:500] + "...(内容被截断)"
        
        message = f"{step_name} {stream_type}输出"
        details = content
        
        return self.add_log(level, module, message, details)
    
    def register_real_time_callback(self, callback):
        """注册实时日志回调函数"""
        if callback not in self.real_time_callbacks:
            self.real_time_callbacks.append(callback)
    
    def unregister_real_time_callback(self, callback):
        """注销实时日志回调函数"""
        if callback in self.real_time_callbacks:
            self.real_time_callbacks.remove(callback)
    
    def _notify_real_time_callbacks(self, log_entry: Dict[str, Any]):
        """通知所有实时日志回调函数"""
        for callback in self.real_time_callbacks:
            try:
                callback(log_entry)
            except Exception as e:
                print(f"⚠️ 实时日志回调执行失败: {e}")
    
    def get_logs(self, level: str = 'all', limit: int = 100, search: str = '',
                 module: str = '', start_time: str = '', end_time: str = '') -> Dict[str, Any]:
        """获取日志列表"""
        
        with self.log_lock:
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
        with self.log_lock:
            cleared_count = len(self.system_logs)
            self.system_logs = []
            
            # 添加清空日志的记录
            self.add_log('INFO', 'LogSystem', '系统日志已清空', f'清空了{cleared_count}条日志记录')
            
            return cleared_count
    
    def get_log_statistics(self, period: str = '24h') -> Dict[str, Any]:
        """获取日志统计信息"""
        
        with self.log_lock:
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
                try:
                    log_time = datetime.strptime(log['timestamp'][:19], '%Y-%m-%d %H:%M:%S')
                    if log_time >= start_time:
                        period_logs.append(log)
                except ValueError:
                    continue
            
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
                try:
                    log_hour = log['timestamp'][:13] + ':00'  # 截取到小时
                    if log_hour in timeline_stats:
                        timeline_stats[log_hour] += 1
                    else:
                        timeline_stats[log_hour] = 1
                except (ValueError, IndexError):
                    continue
            
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
        filepath = os.path.join(self.log_dir, filename)
        
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
        with self.log_lock:
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
