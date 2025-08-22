#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VAPORCONE WebSocket事件处理模块

提供实时通信功能，包括：
- 客户端连接管理
- 实时日志推送
- 执行状态更新
- 系统事件广播
"""

from .events import setup_socketio_events

__all__ = ['setup_socketio_events']
