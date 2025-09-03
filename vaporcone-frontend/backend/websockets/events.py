#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VAPORCONE WebSocket事件处理模块

提供实时通信功能，包括：
- 实时日志推送
- 执行状态更新
- 系统通知
- 客户端连接管理
"""

from flask_socketio import emit, join_room, leave_room
from flask import request
import json
from datetime import datetime


def setup_socketio_events(socketio):
    """设置WebSocket事件处理"""
    
    # 存储广播函数，供其他模块使用
    broadcast_functions = {
        'log_update': None,
        'execution_status': None,
        'system_notification': None
    }
    
    @socketio.on('connect')
    def handle_connect():
        """处理客户端连接"""
        client_id = request.sid
        print(f"🔌 客户端已连接: {client_id}")
        
        # 发送连接确认
        emit('connection_established', {
            'status': 'connected',
            'client_id': client_id,
            'timestamp': datetime.now().isoformat(),
            'message': '已连接到VAPORCONE实时通信服务'
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """处理客户端断开连接"""
        client_id = request.sid
        print(f"🔌 客户端已断开: {client_id}")
    
    @socketio.on('join_log_room')
    def handle_join_log_room(data):
        """加入日志监控房间"""
        client_id = request.sid
        room = f'logs_{data.get("study_id", "default")}'
        join_room(room)
        print(f"📊 客户端 {client_id} 加入日志房间: {room}")
        
        emit('room_joined', {
            'room': room,
            'status': 'success',
            'message': f'已加入日志监控房间: {room}'
        })
    
    @socketio.on('leave_log_room')
    def handle_leave_log_room(data):
        """离开日志监控房间"""
        client_id = request.sid
        room = f'logs_{data.get("study_id", "default")}'
        leave_room(room)
        print(f"📊 客户端 {client_id} 离开日志房间: {room}")
        
        emit('room_left', {
            'room': room,
            'status': 'success',
            'message': f'已离开日志监控房间: {room}'
        })
    
    @socketio.on('join_execution_room')
    def handle_join_execution_room(data):
        """加入执行监控房间"""
        client_id = request.sid
        room = f'execution_{data.get("study_id", "default")}'
        join_room(room)
        print(f"⚡ 客户端 {client_id} 加入执行房间: {room}")
        
        emit('room_joined', {
            'room': room,
            'status': 'success',
            'message': f'已加入执行监控房间: {room}'
        })
    
    @socketio.on('leave_execution_room')
    def handle_leave_execution_room(data):
        """离开执行监控房间"""
        client_id = request.sid
        room = f'execution_{data.get("study_id", "default")}'
        leave_room(room)
        print(f"⚡ 客户端 {client_id} 离开执行房间: {room}")
        
        emit('room_left', {
            'room': room,
            'status': 'success',
            'message': f'已离开执行监控房间: {room}'
        })
    
    @socketio.on('request_logs')
    def handle_request_logs(data):
        """处理日志请求"""
        try:
            from services.log_service import LogService
            log_service = LogService()
            
            # 获取日志数据
            logs_result = log_service.get_logs(
                level=data.get('level', 'all'),
                limit=data.get('limit', 100),
                search=data.get('search', ''),
                module=data.get('module', ''),
                start_time=data.get('start_time', ''),
                end_time=data.get('end_time', '')
            )
            
            # 发送日志数据
            emit('logs_response', {
                'status': 'success',
                'data': logs_result,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            emit('logs_response', {
                'status': 'error',
                'message': f'获取日志失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            })
    
    @socketio.on('request_execution_status')
    def handle_request_execution_status(data):
        """处理执行状态请求"""
        try:
            from services.execution_service import ExecutionService
            execution_service = ExecutionService()
            
            # 获取执行状态
            status = execution_service.get_execution_status()
            current_status = execution_service.get_current_execution_status()
            
            # 发送执行状态
            emit('execution_status_response', {
                'status': 'success',
                'data': {
                    'overview': status,
                    'current_steps': current_status
                },
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            emit('execution_status_response', {
                'status': 'error',
                'message': f'获取执行状态失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            })
    
    # 定义广播函数
    def broadcast_log_update(log_entry, study_id='default'):
        """广播日志更新"""
        room = f'logs_{study_id}'
        socketio.emit('log_update', {
            'log': log_entry,
            'timestamp': datetime.now().isoformat()
        }, room=room)
        print(f"📊 广播日志更新到房间 {room}: {log_entry.get('message', '')[:50]}...")
    
    def broadcast_execution_status(status_data, study_id='default'):
        """广播执行状态更新"""
        room = f'execution_{study_id}'
        socketio.emit('execution_status_update', {
            'status': status_data,
            'timestamp': datetime.now().isoformat()
        }, room=room)
        print(f"⚡ 广播执行状态更新到房间 {room}")
    
    def broadcast_system_notification(notification, study_id='default'):
        """广播系统通知"""
        room = f'logs_{study_id}'  # 系统通知也发送到日志房间
        socketio.emit('system_notification', {
            'notification': notification,
            'timestamp': datetime.now().isoformat()
        }, room=room)
        print(f"🔔 广播系统通知到房间 {room}: {notification.get('message', '')[:50]}...")
    
    # 存储广播函数
    broadcast_functions['log_update'] = broadcast_log_update
    broadcast_functions['execution_status'] = broadcast_execution_status
    broadcast_functions['system_notification'] = broadcast_system_notification
    
    # 设置日志服务的实时回调
    try:
        from services.log_service import LogService
        log_service = LogService()
        
        # 注册实时日志回调
        def log_callback(log_entry):
            """日志回调函数"""
            # 从日志模块名推断研究ID
            study_id = 'default'
            if 'ProcessExecution' in log_entry.get('module', ''):
                study_id = 'current'  # 当前执行的研究
            
            # 广播日志更新
            broadcast_log_update(log_entry, study_id)
        
        log_service.register_real_time_callback(log_callback)
        print("✅ 实时日志回调已注册")
        
    except Exception as e:
        print(f"⚠️ 注册实时日志回调失败: {e}")
    
    return broadcast_functions
