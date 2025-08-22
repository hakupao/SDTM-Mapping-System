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
  Statistic
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  ClearOutlined,
  DownloadOutlined,
  SearchOutlined,
  FilterOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import moment from 'moment';

const { Option } = Select;
const { Search } = Input;
const { RangePicker } = DatePicker;

const LogMonitor = ({ currentStudy }) => {
  const [logs, setLogs] = useState([]);
  const [isRealTime, setIsRealTime] = useState(false); // 默认关闭实时日志
  const [logLevel, setLogLevel] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const logContainerRef = useRef(null);

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

  // 初始化时获取真实日志
  useEffect(() => {
    fetchLogs();
  }, []);

  // 实时日志获取 - 通过WebSocket或定期轮询
  useEffect(() => {
    if (!isRealTime) return;

    // 定期获取新日志
    const interval = setInterval(() => {
      fetchLogs();
    }, 3000); // 每3秒刷新一次

    return () => clearInterval(interval);
  }, [isRealTime]);

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

  return (
    <div className="log-monitor fade-in">
      {/* 日志监控标题 */}
      <Alert
        message={`${currentStudy} 研究日志监控`}
        description="实时监控系统运行日志，包括数据处理过程、函数调用、错误信息等"
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
              
              <Button size="small" icon={<ReloadOutlined />} onClick={fetchLogs}>
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
              暂无日志记录
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

export default LogMonitor;
