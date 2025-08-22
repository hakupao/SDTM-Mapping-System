import React, { useState, useEffect } from 'react';
import { 
  Row, 
  Col, 
  Card, 
  Statistic, 
  Progress, 
  List, 
  Tag, 
  Button, 
  Space,
  Timeline,
  Alert,
  Divider
} from 'antd';
import {
  PlayCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  FunctionOutlined
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';

const Dashboard = ({ currentStudy }) => {
  const [systemStatus, setSystemStatus] = useState({
    cpu: 0,
    memory: 0,
    disk: 0,
    database: 'unknown'
  });

  const [processStatus, setProcessStatus] = useState({
    total: 8,
    completed: 0,
    running: 0,
    pending: 0,
    failed: 0
  });

  const [recentExecutions, setRecentExecutions] = useState([]);

  // 从后端API获取系统状态
  const fetchSystemStatus = async () => {
    try {
      const response = await fetch('/api/system/status');
      const data = await response.json();
      
      if (data.status === 'success') {
        setSystemStatus(data.data);
      }
    } catch (error) {
      console.error('获取系统状态失败:', error);
    }
  };

  // 从后端API获取流程状态
  const fetchProcessStatus = async () => {
    try {
      const response = await fetch('/api/execution/status');
      const data = await response.json();
      
      if (data.status === 'success') {
        setProcessStatus(data.data);
      }
    } catch (error) {
      console.error('获取流程状态失败:', error);
    }
  };

  // 从后端API获取最近执行记录
  const fetchRecentExecutions = async () => {
    try {
      const response = await fetch('/api/execution/history');
      const data = await response.json();
      
      if (data.status === 'success') {
        setRecentExecutions(data.data || []);
      }
    } catch (error) {
      console.error('获取执行历史失败:', error);
      setRecentExecutions([]);
    }
  };

  // 初始化数据
  useEffect(() => {
    fetchSystemStatus();
    fetchProcessStatus();
    fetchRecentExecutions();
    fetchStudyFunctions();
    
    // 定期刷新数据
    const interval = setInterval(() => {
      fetchSystemStatus();
      fetchProcessStatus();
      fetchStudyFunctions();
    }, 30000); // 每30秒刷新一次
    
    return () => clearInterval(interval);
  }, []);

  const [studyFunctions, setStudyFunctions] = useState({
    total: 0,
    available: 0,
    avgTime: 0,
    recentCalls: []
  });

  // 从后端API获取研究函数状态
  const fetchStudyFunctions = async () => {
    try {
      const response = await fetch('/api/functions/list');
      const data = await response.json();
      
      if (data.status === 'success') {
        const functions = data.data || [];
        setStudyFunctions({
          total: functions.length,
          available: functions.filter(f => f.status === 'normal').length,
          avgTime: functions.reduce((acc, f) => acc + parseFloat(f.avg_time || 0), 0) / functions.length || 0,
          recentCalls: functions.slice(0, 3).map(f => ({
            name: f.name,
            time: f.last_call || '--',
            duration: f.avg_time || '--',
            status: f.status || 'unknown'
          }))
        });
      }
    } catch (error) {
      console.error('获取研究函数状态失败:', error);
    }
  };

  // 流程状态图表配置
  const getProcessChart = () => ({
    title: {
      text: '流程执行状态',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    series: [
      {
        name: '执行状态',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '18',
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: [
          { value: processStatus.completed, name: '已完成', itemStyle: { color: '#52c41a' } },
          { value: processStatus.running, name: '进行中', itemStyle: { color: '#faad14' } },
          { value: processStatus.pending, name: '待执行', itemStyle: { color: '#d9d9d9' } },
          { value: processStatus.failed, name: '失败', itemStyle: { color: '#ff4d4f' } }
        ]
      }
    ]
  });

  // 系统监控图表配置
  const getSystemChart = () => ({
    title: {
      text: '系统资源监控',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['CPU', '内存', '磁盘']
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        formatter: '{value}%'
      }
    },
            series: [
          {
            name: '使用率',
            type: 'bar',
            data: [
              { value: systemStatus.cpu || 0, itemStyle: { color: (systemStatus.cpu || 0) > 80 ? '#ff4d4f' : (systemStatus.cpu || 0) > 60 ? '#faad14' : '#52c41a' } },
              { value: systemStatus.memory_percent || 0, itemStyle: { color: (systemStatus.memory_percent || 0) > 80 ? '#ff4d4f' : (systemStatus.memory_percent || 0) > 60 ? '#faad14' : '#52c41a' } },
              { value: systemStatus.disk || 0, itemStyle: { color: (systemStatus.disk || 0) > 90 ? '#ff4d4f' : (systemStatus.disk || 0) > 70 ? '#faad14' : '#52c41a' } }
            ],
            barWidth: '60%'
          }
        ]
  });

  const handleQuickAction = (action) => {
    console.log(`执行快速操作: ${action}`);
    // TODO: 实现与后端的API调用
  };

  return (
    <div className="dashboard fade-in">
      {/* 顶部警告信息 */}
      <Alert
        message={`当前研究: ${currentStudy}`}
        description="系统运行正常，所有模块工作正常"
        type="success"
        showIcon
        style={{ marginBottom: 24 }}
      />

      {/* 概览统计 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="流程完成度"
              value={processStatus.completed}
              suffix={`/ ${processStatus.total}`}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
            <Progress 
              percent={Math.round((processStatus.completed / processStatus.total) * 100)} 
              size="small" 
              status="active"
              style={{ marginTop: 8 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="研究函数"
              value={studyFunctions.available}
              suffix={`/ ${studyFunctions.total}`}
              prefix={<FunctionOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
            <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
              平均耗时: {studyFunctions.avgTime}s
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="数据库状态"
              value={systemStatus.database === 'connected' ? '已连接' : '未连接'}
              prefix={<DatabaseOutlined style={{ color: systemStatus.database === 'connected' ? '#52c41a' : '#ff4d4f' }} />}
              valueStyle={{ color: systemStatus.database === 'connected' ? '#52c41a' : '#ff4d4f' }}
            />
            <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
              {systemStatus.platform || 'Windows'} - Python {systemStatus.python_version || '3.8+'}
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="系统负载"
              value={systemStatus.cpu || 0}
              suffix="%"
              prefix={<ClockCircleOutlined style={{ color: (systemStatus.cpu || 0) > 70 ? '#faad14' : '#52c41a' }} />}
              valueStyle={{ color: (systemStatus.cpu || 0) > 70 ? '#faad14' : '#52c41a' }}
            />
            <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
              内存: {systemStatus.memory || 0}/{systemStatus.memory_total || 8}GB / 磁盘: {systemStatus.disk || 0}%
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 左侧：流程状态和快速操作 */}
        <Col xs={24} lg={12}>
          <Card title="流程状态总览" style={{ marginBottom: 16 }}>
            <ReactECharts option={getProcessChart()} style={{ height: '300px' }} />
          </Card>

          <Card title="快速操作">
            <Space wrap style={{ width: '100%' }}>
              <Button 
                type="primary" 
                icon={<PlayCircleOutlined />}
                onClick={() => handleQuickAction('start_all')}
              >
                一键执行全流程
              </Button>
              <Button 
                icon={<PlayCircleOutlined />}
                onClick={() => handleQuickAction('continue')}
              >
                继续执行
              </Button>
              <Button 
                icon={<ExclamationCircleOutlined />}
                onClick={() => handleQuickAction('reset')}
              >
                重置流程
              </Button>
              <Button 
                icon={<FunctionOutlined />}
                onClick={() => handleQuickAction('test_functions')}
              >
                函数性能测试
              </Button>
            </Space>
          </Card>
        </Col>

        {/* 右侧：系统监控和执行历史 */}
        <Col xs={24} lg={12}>
          <Card title="系统监控" style={{ marginBottom: 16 }}>
            <ReactECharts option={getSystemChart()} style={{ height: '200px' }} />
          </Card>

          <Card title="最近执行记录">
            <List
              dataSource={recentExecutions.slice(0, 5)}
              renderItem={item => (
                <List.Item>
                  <List.Item.Meta
                    title={
                      <Space>
                        <span>{item.step_name || item.study_id || '未知步骤'}</span>
                        <Tag color={item.success ? 'green' : 'red'}>
                          {item.success ? '成功' : '失败'}
                        </Tag>
                      </Space>
                    }
                    description={
                      <Space>
                        <span>{item.timestamp ? new Date(item.timestamp).toLocaleString() : '--'}</span>
                        <span>耗时: {item.execution_time ? `${item.execution_time}秒` : '--'}</span>
                        <span>步骤: {item.step_id || '--'}</span>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
            {recentExecutions.length === 0 && (
              <div style={{ textAlign: 'center', color: '#999', padding: '20px' }}>
                暂无执行记录
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 底部：研究函数调用记录 */}
      <Card title="最近函数调用记录" style={{ marginTop: 16 }}>
        <Timeline>
          {studyFunctions.recentCalls && studyFunctions.recentCalls.length > 0 ? (
            studyFunctions.recentCalls.map((call, index) => (
              <Timeline.Item
                key={index}
                color={call.status === 'normal' ? 'green' : call.status === 'warning' ? 'orange' : 'blue'}
                dot={call.status === 'warning' ? <ExclamationCircleOutlined /> : undefined}
              >
                <Space>
                  <strong>{call.name}</strong>
                  <span>{call.time || call.last_call || '--'}</span>
                  <Tag color={call.status === 'normal' ? 'green' : 'blue'}>
                    {call.duration || call.avg_time || '--'}
                  </Tag>
                  <span style={{ color: '#666', fontSize: '12px' }}>
                    {call.category || 'system'}
                  </span>
                </Space>
              </Timeline.Item>
            ))
          ) : (
            <Timeline.Item color="gray">
              <span style={{ color: '#999' }}>暂无函数调用记录</span>
            </Timeline.Item>
          )}
        </Timeline>
      </Card>
    </div>
  );
};

export default Dashboard;
