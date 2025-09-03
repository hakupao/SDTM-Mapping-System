import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Select,
  Button,
  Space,
  Input,
  Switch,
  Tag,
  Alert,
  DatePicker,
  Row,
  Col,
  Statistic,
  notification
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  ClearOutlined,
  DownloadOutlined,
  SearchOutlined,
  FilterOutlined,
  ReloadOutlined,
  WifiOutlined,
  WifiOutlined as WifiOffOutlined
} from '@ant-design/icons';
import moment from 'moment';
import io from 'socket.io-client';

const { Option } = Select;
const { Search } = Input;
const { RangePicker } = DatePicker;

const LogMonitor = ({ currentStudy }) => {
  const [logs, setLogs] = useState([]);
  const [isRealTime, setIsRealTime] = useState(false); // 默认关闭实时日志
  const [logLevel, setLogLevel] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [socket, setSocket] = useState(null);
  const logContainerRef = useRef(null);

  // 初始化WebSocket连接
  useEffect(() => {
    const newSocket = io('http://localhost:5000');
    
    newSocket.on('connect', () => {
      console.log('WebSocket连接已建立');
      setIsConnected(true);
      
      // 加入日志监控房间
      newSocket.emit('join_log_room', { study_id: currentStudy || 'default' });
      
      // 显示连接成功通知
      notification.success({
        message: '实时连接已建立',
        description: '日志监控已连接到后端服务',
        duration: 3
      });
    });
    
    newSocket.on('disconnect', () => {
      console.log('WebSocket连接已断开');
      setIsConnected(false);
      
      notification.warning({
        message: '连接已断开',
        description: '与后端服务的连接已断开，请检查网络连接',
        duration: 5
      });
    });
    
    newSocket.on('connection_established', (data) => {
      console.log('连接确认:', data);
    });
    
    newSocket.on('room_joined', (data) => {
      console.log('已加入房间:', data);
    });
    
    newSocket.on('log_update', (data) => {
      console.log('收到实时日志更新:', data);
      
      if (isRealTime && data.log) {
        // 添加新的日志条目到列表开头
        setLogs(prevLogs => {
          const newLogs = [data.log, ...prevLogs];
          // 保持日志数量在合理范围内
          return newLogs.slice(0, 1000);
        });
        
        // 显示实时日志通知
        notification.info({
          message: '新日志',
          description: `${data.log.module}: ${data.log.message}`,
          duration: 2,
          placement: 'bottomRight'
        });
      }
    });
    
    newSocket.on('system_notification', (data) => {
      console.log('收到系统通知:', data);
      
      if (data.notification) {
        notification.info({
          message: '系统通知',
          description: data.notification.message,
          duration: 4
        });
      }
    });
    
    setSocket(newSocket);
    
    // 清理函数
    return () => {
      if (newSocket) {
        newSocket.disconnect();
      }
    };
  }, [currentStudy]);
  
  // 当研究ID改变时，重新加入房间
  useEffect(() => {
    if (socket && isConnected) {
      socket.emit('join_log_room', { study_id: currentStudy || 'default' });
    }
  }, [currentStudy, socket, isConnected]);

  // 从后端API获取真实日志数据
  const fetchLogs = async () => {
    try {
      const response = await fetch('/api/logs/list');
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setLogs(data.data || []);
        }
      }
    } catch (error) {
      console.error('获取日志失败:', error);
      // 如果无法获取日志，保持空状态
      setLogs([]);
    }
  };

  // 通过WebSocket请求日志
  const requestLogsViaSocket = () => {
    if (socket && isConnected) {
      socket.emit('request_logs', {
        level: logLevel,
        limit: 100,
        search: searchTerm,
        module: '',
        start_time: '',
        end_time: ''
      });
    }
  };

  // 初始化时获取真实日志
  useEffect(() => {
    fetchLogs();
  }, []);

  // 实时日志获取 - 通过WebSocket或定期轮询
  useEffect(() => {
    if (!isRealTime) return;

    if (socket && isConnected) {
      // 使用WebSocket实时推送
      console.log('启用WebSocket实时日志推送');
    } else {
      // 降级到定期轮询
      console.log('WebSocket未连接，使用轮询模式');
      const interval = setInterval(() => {
        fetchLogs();
      }, 3000); // 每3秒刷新一次

      return () => clearInterval(interval);
    }
  }, [isRealTime, socket, isConnected]);

  // 自动滚动到底部
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  // 过滤日志
  const filteredLogs = logs.filter(log => {
    const levelMatch = logLevel === 'all' || log.level === logLevel;
    const searchMatch = searchTerm === '' || 
      log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.module.toLowerCase().includes(searchTerm.toLowerCase());
    return levelMatch && searchMatch;
  });

  // 获取日志级别样式
  const getLogLevelClass = (level) => {
    switch (level) {
      case 'ERROR':
        return 'log-error';
      case 'WARNING':
        return 'log-warning';
      case 'INFO':
        return 'log-info';
      case 'DEBUG':
        return 'log-debug';
      default:
        return '';
    }
  };

  // 获取日志级别标签
  const getLogLevelTag = (level) => {
    const colors = {
      'ERROR': 'red',
      'WARNING': 'orange',
      'INFO': 'blue',
      'DEBUG': 'default'
    };
    return <Tag color={colors[level]} size="small">{level}</Tag>;
  };

  // 日志统计
  const logStats = {
    total: filteredLogs.length,
    error: filteredLogs.filter(log => log.level === 'ERROR').length,
    warning: filteredLogs.filter(log => log.level === 'WARNING').length,
    info: filteredLogs.filter(log => log.level === 'INFO').length,
    debug: filteredLogs.filter(log => log.level === 'DEBUG').length
  };

  // 清空日志
  const clearLogs = async () => {
    try {
      const response = await fetch('/api/logs/clear', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setLogs([]);
          // 刷新获取最新的日志（包括清空操作的日志）
          setTimeout(fetchLogs, 500);
        }
      }
    } catch (error) {
      console.error('清空日志失败:', error);
      // 如果API调用失败，仍然清空前端显示
      setLogs([]);
    }
  };

  // 导出日志
  const exportLogs = () => {
    const logText = filteredLogs.map(log => 
      `[${log.timestamp}] [${log.level}] [${log.module}] ${log.message}${log.details ? ` | ${log.details}` : ''}`
    ).join('\n');
    
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentStudy}_logs_${moment().format('YYYYMMDD_HHmmss')}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // 手动刷新日志
  const handleRefresh = () => {
    if (socket && isConnected) {
      requestLogsViaSocket();
    } else {
      fetchLogs();
    }
  };

  return (
    <div className="log-monitor fade-in">
      {/* 日志监控标题 */}
      <Alert
        message={`${currentStudy} 研究日志监控`}
        description={
          <div>
            <div>实时监控系统运行日志，包括数据处理过程、函数调用、错误信息等</div>
            <div style={{ marginTop: 8 }}>
              <Tag color={isConnected ? 'green' : 'red'} icon={isConnected ? <WifiOutlined /> : <WifiOffOutlined />}>
                {isConnected ? '实时连接已建立' : '实时连接已断开'}
              </Tag>
            </div>
          </div>
        }
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      {/* 日志统计 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6} lg={4}>
          <Card size="small">
            <Statistic
              title="总日志数"
              value={logStats.total}
              valueStyle={{ fontSize: '20px' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6} lg={4}>
          <Card size="small">
            <Statistic
              title="错误"
              value={logStats.error}
              valueStyle={{ color: '#ff4d4f', fontSize: '20px' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6} lg={4}>
          <Card size="small">
            <Statistic
              title="警告"
              value={logStats.warning}
              valueStyle={{ color: '#faad14', fontSize: '20px' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6} lg={4}>
          <Card size="small">
            <Statistic
              title="信息"
              value={logStats.info}
              valueStyle={{ color: '#1890ff', fontSize: '20px' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6} lg={4}>
          <Card size="small">
            <Statistic
              title="调试"
              value={logStats.debug}
              valueStyle={{ color: '#666', fontSize: '20px' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 日志控制面板 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} md={12}>
            <Space wrap>
              <span>实时监控:</span>
              <Switch
                checked={isRealTime}
                onChange={setIsRealTime}
                checkedChildren={<PlayCircleOutlined />}
                unCheckedChildren={<PauseCircleOutlined />}
                disabled={!isConnected}
              />
              
              <span>自动滚动:</span>
              <Switch
                checked={autoScroll}
                onChange={setAutoScroll}
              />
              
              <span>日志级别:</span>
              <Select
                value={logLevel}
                onChange={setLogLevel}
                style={{ width: 100 }}
                size="small"
              >
                <Option value="all">全部</Option>
                <Option value="ERROR">错误</Option>
                <Option value="WARNING">警告</Option>
                <Option value="INFO">信息</Option>
                <Option value="DEBUG">调试</Option>
              </Select>
            </Space>
          </Col>
          
          <Col xs={24} md={12}>
            <Space wrap>
              <Search
                placeholder="搜索日志..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ width: 200 }}
                size="small"
              />
              
              <Button 
                size="small" 
                icon={<ReloadOutlined />} 
                onClick={handleRefresh}
                loading={!isConnected && isRealTime}
              >
                刷新
              </Button>
              <Button size="small" icon={<ClearOutlined />} onClick={clearLogs}>
                清空
              </Button>
              <Button size="small" icon={<DownloadOutlined />} onClick={exportLogs}>
                导出
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 日志显示区域 */}
      <Card title={`日志流 (${filteredLogs.length} 条)`}>
        <div
          ref={logContainerRef}
          className="log-container"
          style={{
            height: '500px',
            overflow: 'auto',
            background: '#001529',
            color: '#fff',
            fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
            fontSize: '12px',
            padding: '16px',
            borderRadius: '6px'
          }}
        >
          {filteredLogs.map(log => (
            <div key={log.id} className={`log-line ${getLogLevelClass(log.level)}`}>
              <span style={{ color: '#888', marginRight: '8px' }}>
                [{log.timestamp}]
              </span>
              <span style={{ marginRight: '8px' }}>
                {getLogLevelTag(log.level)}
              </span>
              <span style={{ color: '#61dafb', marginRight: '8px' }}>
                [{log.module}]
              </span>
              <span>{log.message}</span>
              {log.details && (
                <div style={{ 
                  marginLeft: '24px', 
                  color: '#888', 
                  fontSize: '11px',
                  marginTop: '2px'
                }}>
                  └─ {log.details}
                </div>
              )}
            </div>
          ))}
          
          {filteredLogs.length === 0 && (
            <div style={{ textAlign: 'center', color: '#888', marginTop: '50px' }}>
              {!isConnected ? '等待连接后端服务...' : '暂无日志记录'}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

export default LogMonitor;
