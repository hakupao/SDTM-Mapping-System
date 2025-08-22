import React, { useState, useEffect } from 'react';
import {
  Card,
  Steps,
  Button,
  Space,
  Progress,
  Alert,
  Descriptions,
  Tag,
  Modal,
  Form,
  Input,
  Switch,
  Divider,
  Row,
  Col,
  Timeline,
  Statistic,
  Checkbox,
  Table,
  Tooltip,
  message,
  List,
  Typography
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  SettingOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  SwapOutlined,
  ExportOutlined,
  SyncOutlined
} from '@ant-design/icons';

const { Step } = Steps;
const { Text, Title } = Typography;

const ProcessExecution = ({ currentStudy }) => {
  const [availableSteps, setAvailableSteps] = useState([]);
  const [selectedSteps, setSelectedSteps] = useState([]);
  const [executionStatus, setExecutionStatus] = useState('idle'); // idle, running, completed, error
  const [executionResults, setExecutionResults] = useState([]);
  const [currentExecuting, setCurrentExecuting] = useState(null);
  const [isConfigModalVisible, setIsConfigModalVisible] = useState(false);
  const [executionLogs, setExecutionLogs] = useState([]);
  const [executionHistory, setExecutionHistory] = useState([]);
  const [isHistoryModalVisible, setIsHistoryModalVisible] = useState(false);

  // 获取可用步骤和执行状态
  useEffect(() => {
    fetchAvailableSteps();
    fetchExecutionStatus();
  }, []);

  const fetchAvailableSteps = async () => {
    try {
      const response = await fetch('/api/execution/steps');
      const data = await response.json();
      if (data.status === 'success') {
        setAvailableSteps(data.data);
      }
    } catch (error) {
      message.error('获取步骤列表失败');
    }
  };

  // 获取执行状态
  const fetchExecutionStatus = async () => {
    try {
      const response = await fetch('/api/execution/status-current');
      const data = await response.json();
      if (data.status === 'success') {
        // 确保data.data是一个数组
        const results = Array.isArray(data.data) ? data.data : [];
        setExecutionResults(results);
      }
    } catch (error) {
      console.error('获取执行状态失败:', error);
      // 不显示错误消息，因为可能是首次加载没有执行记录
      // 设置为空数组以防止错误
      setExecutionResults([]);
    }
  };

  // 获取执行历史
  const fetchExecutionHistory = async () => {
    try {
      const response = await fetch('/api/execution/history?limit=100');
      const data = await response.json();
      if (data.status === 'success') {
        setExecutionHistory(data.data);
      }
    } catch (error) {
      console.error('获取执行历史失败:', error);
      message.error('获取执行历史失败');
    }
  };

  // 获取图标
  const getStepIcon = (category) => {
    switch (category) {
      case 'preparation':
        return <SettingOutlined />;
      case 'processing':
        return <SyncOutlined />;
      case 'database':
        return <DatabaseOutlined />;
      case 'transformation':
        return <SwapOutlined />;
      case 'output':
        return <ExportOutlined />;
      default:
        return <FileTextOutlined />;
    }
  };

  // 获取状态颜色
  const getStatusColor = (stepId) => {
    // 确保executionResults是数组
    if (!Array.isArray(executionResults)) return 'default';
    const result = executionResults.find(r => r.step_id === stepId);
    if (!result) return 'default';
    return result.result.success ? 'success' : 'error';
  };

  // 获取状态文本
  const getStatusText = (stepId) => {
    if (currentExecuting === stepId) return '执行中';
    // 确保executionResults是数组
    if (!Array.isArray(executionResults)) return '待执行';
    const result = executionResults.find(r => r.step_id === stepId);
    if (!result) return '待执行';
    return result.result.success ? '完成' : '失败';
  };

  // 执行单个步骤
  const executeSingleStep = async (step) => {
    setCurrentExecuting(step.id);
    setExecutionLogs(prev => [...prev, {
      time: new Date().toLocaleTimeString(),
      message: `开始执行: ${step.name}`,
      type: 'info'
    }]);

    try {
      const response = await fetch('/api/execution/run-step', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          step_name: step.name,
          script_name: step.script
        }),
      });

      const data = await response.json();
      
      const newResult = {
        step_id: step.id,
        step_name: step.name,
        result: data.data
      };

      setExecutionResults(prev => {
        const filtered = prev.filter(r => r.step_id !== step.id);
        return [...filtered, newResult];
      });

      setExecutionLogs(prev => [...prev, {
        time: new Date().toLocaleTimeString(),
        message: `${step.name} ${data.data.success ? '执行成功' : '执行失败'}`,
        type: data.data.success ? 'success' : 'error',
        details: data.data.message
      }]);

      if (data.data.success) {
        message.success(`${step.name} 执行成功`);
      } else {
        message.error(`${step.name} 执行失败`);
      }

      // 刷新执行状态以获取最新的执行记录
      setTimeout(fetchExecutionStatus, 500);

    } catch (error) {
      setExecutionLogs(prev => [...prev, {
        time: new Date().toLocaleTimeString(),
        message: `${step.name} 执行异常: ${error.message}`,
        type: 'error'
      }]);
      message.error('执行失败');
    } finally {
      setCurrentExecuting(null);
    }
  };

  // 执行选中的步骤
  const executeSelectedSteps = async () => {
    if (selectedSteps.length === 0) {
      message.warning('请选择要执行的步骤');
      return;
    }

    setExecutionStatus('running');
    setExecutionLogs(prev => [...prev, {
      time: new Date().toLocaleTimeString(),
      message: `开始批量执行 ${selectedSteps.length} 个步骤`,
      type: 'info'
    }]);

    try {
      const response = await fetch('/api/execution/run-steps', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          step_ids: selectedSteps
        }),
      });

      const data = await response.json();
      
      if (data.status === 'success') {
        setExecutionResults(data.data.results);
        setExecutionStatus(data.data.execution_status);
        
        setExecutionLogs(prev => [...prev, {
          time: new Date().toLocaleTimeString(),
          message: `批量执行完成，状态: ${data.data.execution_status}`,
          type: data.data.execution_status === 'completed' ? 'success' : 'error'
        }]);

        message.success('批量执行完成');
        
        // 刷新执行状态以获取最新的执行记录
        setTimeout(fetchExecutionStatus, 500);
      } else {
        throw new Error(data.message);
      }

    } catch (error) {
      setExecutionStatus('error');
      setExecutionLogs(prev => [...prev, {
        time: new Date().toLocaleTimeString(),
        message: `批量执行失败: ${error.message}`,
        type: 'error'
      }]);
      message.error('批量执行失败');
    }
  };

  // 重置状态
  const resetExecution = () => {
    setExecutionStatus('idle');
    setExecutionResults([]);
    setCurrentExecuting(null);
    setExecutionLogs([]);
    setSelectedSteps([]);
    
    // 刷新执行状态以获取最新记录
    fetchExecutionStatus();
    
    message.info('状态已重置');
  };

  // 表格列定义
  const columns = [
    {
      title: '选择',
      key: 'select',
      width: 60,
      render: (_, record) => (
        <Checkbox
          checked={selectedSteps.includes(record.id)}
          onChange={(e) => {
            if (e.target.checked) {
              setSelectedSteps([...selectedSteps, record.id]);
            } else {
              setSelectedSteps(selectedSteps.filter(id => id !== record.id));
            }
          }}
          disabled={currentExecuting !== null}
        />
      ),
    },
    {
      title: '步骤',
      key: 'step',
      render: (_, record) => (
        <Space>
          {getStepIcon(record.category)}
          <div>
            <div style={{ fontWeight: 'bold' }}>{record.name}</div>
            <Text type="secondary" style={{ fontSize: '12px' }}>{record.id}</Text>
          </div>
        </Space>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '预计时间',
      dataIndex: 'estimated_time',
      key: 'estimated_time',
      width: 100,
    },
    {
      title: '状态',
      key: 'status',
      width: 100,
      render: (_, record) => (
        <Tag color={getStatusColor(record.id)}>
          {getStatusText(record.id)}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<PlayCircleOutlined />}
            onClick={() => executeSingleStep(record)}
            loading={currentExecuting === record.id}
            disabled={currentExecuting !== null && currentExecuting !== record.id}
            size="small"
          >
            执行
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]}>
        {/* 控制面板 */}
        <Col span={24}>
          <Card title="流程执行控制" size="small">
            <Space size="large">
              <Space>
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={executeSelectedSteps}
                  loading={executionStatus === 'running'}
                  disabled={selectedSteps.length === 0}
                >
                  执行选中 ({selectedSteps.length})
                </Button>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={resetExecution}
                  disabled={executionStatus === 'running'}
                >
                  重置
                </Button>
                <Button
                  icon={<ClockCircleOutlined />}
                  onClick={() => {
                    fetchExecutionHistory();
                    setIsHistoryModalVisible(true);
                  }}
                >
                  执行历史
                </Button>
              </Space>
              
              <Space>
                <Button
                  type="link"
                  onClick={() => {
                    if (selectedSteps.length === availableSteps.length) {
                      setSelectedSteps([]);
                    } else {
                      setSelectedSteps(availableSteps.map(step => step.id));
                    }
                  }}
                >
                  {selectedSteps.length === availableSteps.length ? '取消全选' : '全选'}
                </Button>
              </Space>

              <div>
                <Text type="secondary">
                  当前研究: <Text strong>{currentStudy}</Text>
                </Text>
              </div>
            </Space>
          </Card>
        </Col>

        {/* 步骤表格 */}
        <Col span={16}>
          <Card title="可执行步骤" size="small">
            <Table
              columns={columns}
              dataSource={availableSteps}
              rowKey="id"
              pagination={false}
              size="small"
              loading={currentExecuting !== null}
            />
          </Card>
        </Col>

        {/* 执行日志 */}
        <Col span={8}>
          <Card title="执行日志" size="small">
            <div style={{ height: '400px', overflow: 'auto' }}>
              <List
                dataSource={executionLogs}
                renderItem={(log, index) => (
                  <List.Item key={index} style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                    <div style={{ width: '100%' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <Text style={{ fontSize: '12px', color: '#666' }}>{log.time}</Text>
                        <Tag
                          color={log.type === 'success' ? 'green' : log.type === 'error' ? 'red' : 'blue'}
                          size="small"
                        >
                          {log.type === 'success' ? '成功' : log.type === 'error' ? '错误' : '信息'}
                        </Tag>
                      </div>
                      <div style={{ fontSize: '12px' }}>
                        {log.message}
                        {log.details && (
                          <div style={{ marginTop: '4px', color: '#666', fontSize: '11px' }}>
                            {log.details}
                          </div>
                        )}
                      </div>
                    </div>
                  </List.Item>
                )}
              />
              {executionLogs.length === 0 && (
                <div style={{ textAlign: 'center', color: '#999', marginTop: '50px' }}>
                  暂无执行日志
                </div>
              )}
            </div>
          </Card>
        </Col>

        {/* 执行结果统计 */}
        {Array.isArray(executionResults) && executionResults.length > 0 && (
          <Col span={24}>
            <Card title="执行结果" size="small">
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic
                    title="总步骤"
                    value={executionResults.length}
                    prefix={<FileTextOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="成功"
                    value={executionResults.filter(r => r.result && r.result.success).length}
                    valueStyle={{ color: '#3f8600' }}
                    prefix={<CheckCircleOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="失败"
                    value={executionResults.filter(r => r.result && !r.result.success).length}
                    valueStyle={{ color: '#cf1322' }}
                    prefix={<CloseCircleOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="成功率"
                    value={executionResults.length > 0 ? ((executionResults.filter(r => r.result && r.result.success).length / executionResults.length) * 100).toFixed(1) : 0}
                    suffix="%"
                    valueStyle={{ 
                      color: executionResults.filter(r => r.result && r.result.success).length === executionResults.length ? '#3f8600' : '#cf1322' 
                    }}
                  />
                </Col>
              </Row>
            </Card>
          </Col>
        )}
      </Row>

      {/* 执行历史模态框 */}
      <Modal
        title="执行历史记录"
        open={isHistoryModalVisible}
        onCancel={() => setIsHistoryModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setIsHistoryModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={1000}
      >
        <Table
          dataSource={executionHistory}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
          columns={[
            {
              title: '时间',
              dataIndex: 'timestamp',
              key: 'timestamp',
              width: 150,
            },
            {
              title: '步骤',
              key: 'step',
              width: 200,
              render: (_, record) => (
                <Space>
                  {getStepIcon('processing')}
                  <div>
                    <div style={{ fontWeight: 'bold' }}>{record.step_name}</div>
                    <Text type="secondary" style={{ fontSize: '12px' }}>{record.step_id}</Text>
                  </div>
                </Space>
              ),
            },
            {
              title: '状态',
              key: 'status',
              width: 100,
              render: (_, record) => (
                <Tag color={record.success ? 'success' : 'error'}>
                  {record.success ? '成功' : '失败'}
                </Tag>
              ),
            },
            {
              title: '执行时间',
              dataIndex: 'execution_time',
              key: 'execution_time',
              width: 100,
              render: (time) => time ? `${time}秒` : '-',
            },
            {
              title: '消息',
              dataIndex: 'message',
              key: 'message',
              ellipsis: true,
              render: (text) => (
                <Tooltip title={text}>
                  <span>{text}</span>
                </Tooltip>
              ),
            }
          ]}
        />
      </Modal>
    </div>
  );
};

export default ProcessExecution;