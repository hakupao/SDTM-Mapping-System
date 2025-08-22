import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Upload,
  Select,
  Table,
  Descriptions,
  Alert,
  Divider,
  Progress,
  Statistic,
  Timeline,
  Tooltip
} from 'antd';
import {
  FunctionOutlined,
  PlayCircleOutlined,
  UploadOutlined,
  DownloadOutlined,
  EyeOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ApiOutlined,
  CodeOutlined
} from '@ant-design/icons';

const { Option } = Select;
const { TextArea } = Input;

const StudyFunctions = ({ currentStudy }) => {
  const [functions, setFunctions] = useState([
    {
      name: 'leftjoin',
      description: '执行两个数据表的左连接操作',
      status: 'normal',
      lastCall: '15:30',
      avgTime: '1.2s',
      params: ['table1: str', 'table2: str'],
      returns: 'pandas.DataFrame',
      category: 'data_merge'
    },
    {
      name: 'tableMerge',
      description: '将多个数据表垂直拼接',
      status: 'normal',
      lastCall: '15:32',
      avgTime: '2.1s',
      params: ['*tableList'],
      returns: 'pandas.DataFrame',
      category: 'data_merge'
    },
    {
      name: 'make_DMFrame',
      description: '创建人口统计学数据框',
      status: 'normal',
      lastCall: '15:35',
      avgTime: '3.4s',
      params: [],
      returns: 'pandas.DataFrame',
      category: 'data_processing'
    },
    {
      name: 'process_MH_A_PT',
      description: '处理MH_A_PT数据集的所有字段',
      status: 'warning',
      lastCall: '15:40',
      avgTime: '5.2s',
      params: [],
      returns: 'pandas.DataFrame',
      category: 'data_processing'
    },
    {
      name: 'process_RGACOHD_MH',
      description: '处理RGACOHD_MH数据集',
      status: 'normal',
      lastCall: '15:45',
      avgTime: '2.8s',
      params: [],
      returns: 'pandas.DataFrame',
      category: 'data_processing'
    },
    {
      name: 'get_DD_from_SS_ALL',
      description: '从SS_A_ALL数据集获取死亡数据',
      status: 'normal',
      lastCall: '15:50',
      avgTime: '1.5s',
      params: [],
      returns: 'pandas.DataFrame',
      category: 'data_extraction'
    },
    {
      name: 'get_GF_from_LB_A_BM',
      description: '从LB_A_BM数据集获取基因检测结果',
      status: 'normal',
      lastCall: '15:55',
      avgTime: '4.1s',
      params: [],
      returns: 'pandas.DataFrame',
      category: 'data_extraction'
    },
    {
      name: 'sort_csv_data',
      description: '对CSV数据进行排序处理',
      status: 'normal',
      lastCall: '16:00',
      avgTime: '0.8s',
      params: ['data_list: list', 'file_name: str', 'subjid_field_id: str'],
      returns: 'list',
      category: 'data_utility'
    }
  ]);

  const [isTestModalVisible, setIsTestModalVisible] = useState(false);
  const [selectedFunction, setSelectedFunction] = useState(null);
  const [testResults, setTestResults] = useState(null);
  const [testRunning, setTestRunning] = useState(false);
  const [functionFilter, setFunctionFilter] = useState('all');

  // 函数分类
  const categories = {
    all: '全部',
    data_merge: '数据合并',
    data_processing: '数据处理',
    data_extraction: '数据提取',
    data_utility: '工具函数'
  };

  // 过滤函数
  const filteredFunctions = functions.filter(func => 
    functionFilter === 'all' || func.category === functionFilter
  );

  // 函数统计
  const functionStats = {
    total: functions.length,
    normal: functions.filter(f => f.status === 'normal').length,
    warning: functions.filter(f => f.status === 'warning').length,
    error: functions.filter(f => f.status === 'error').length,
    avgTime: (functions.reduce((acc, f) => acc + parseFloat(f.avgTime), 0) / functions.length).toFixed(1)
  };

  // 测试函数
  const handleTestFunction = async (func) => {
    setSelectedFunction(func);
    setIsTestModalVisible(true);
  };

  // 执行函数测试
  const executeTest = async (values) => {
    if (!selectedFunction) {
      return;
    }
    
    setTestRunning(true);
    try {
      // 构建参数对象
      const parameters = {};
      selectedFunction.params.forEach((param, index) => {
        const paramValue = values[`param_${index}`];
        if (paramValue) {
          parameters[param] = paramValue;
        }
      });

      // 真实的API调用
      const response = await fetch('/api/functions/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          function_name: selectedFunction.name,
          parameters: parameters,
          study_id: currentStudy
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setTestResults(data.data);
      } else {
        setTestResults({
          success: false,
          error: data.message || '函数测试失败'
        });
      }
    } catch (error) {
      setTestResults({
        success: false,
        error: error.message,
        logs: ['执行失败: ' + error.message]
      });
    } finally {
      setTestRunning(false);
    }
  };

  // 查看函数代码
  const viewFunctionCode = (func) => {
    Modal.info({
      title: `函数代码: ${func.name}`,
      width: 800,
      content: (
        <div>
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="函数名">{func.name}</Descriptions.Item>
            <Descriptions.Item label="描述">{func.description}</Descriptions.Item>
            <Descriptions.Item label="参数">{func.params.join(', ')}</Descriptions.Item>
            <Descriptions.Item label="返回值">{func.returns}</Descriptions.Item>
          </Descriptions>
          <Divider />
          <div style={{ 
            background: '#f6f8fa', 
            padding: '16px', 
            borderRadius: '6px',
            fontFamily: 'monospace',
            fontSize: '12px',
            maxHeight: '400px',
            overflow: 'auto'
          }}>
            <pre>{`def ${func.name}(${func.params.join(', ')}):\n    """\n    ${func.description}\n    """\n    # 函数实现代码...\n    return result`}</pre>
          </div>
        </div>
      )
    });
  };

  // 渲染函数卡片
  const renderFunctionCard = (func) => (
    <Col xs={24} sm={12} lg={8} key={func.name}>
      <Card
        size="small"
        title={
          <Space>
            <FunctionOutlined />
            <span>{func.name}</span>
            <Tag color={func.status === 'normal' ? 'green' : func.status === 'warning' ? 'orange' : 'red'}>
              {func.status === 'normal' ? '正常' : func.status === 'warning' ? '警告' : '错误'}
            </Tag>
          </Space>
        }
        extra={
          <Space>
            <Tooltip title="测试函数">
              <Button
                size="small"
                icon={<PlayCircleOutlined />}
                onClick={() => handleTestFunction(func)}
              />
            </Tooltip>
            <Tooltip title="查看代码">
              <Button
                size="small"
                icon={<EyeOutlined />}
                onClick={() => viewFunctionCode(func)}
              />
            </Tooltip>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <div style={{ marginBottom: 8 }}>
          <div style={{ fontSize: '12px', color: '#666', marginBottom: 4 }}>
            {func.description}
          </div>
          <Space size="small">
            <span style={{ fontSize: '12px' }}>
              最近调用: {func.lastCall}
            </span>
            <span style={{ fontSize: '12px' }}>
              平均耗时: {func.avgTime}
            </span>
          </Space>
        </div>
        
        <div style={{ fontSize: '11px', color: '#999' }}>
          <div>参数: {func.params.join(', ') || '无'}</div>
          <div>返回: {func.returns}</div>
        </div>
      </Card>
    </Col>
  );

  return (
    <div className="study-functions fade-in">
      {/* 研究信息 */}
      <Alert
        message={`${currentStudy} 研究特定函数管理`}
        description="管理和测试当前研究的特定数据处理函数"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      {/* 函数统计 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="函数总数"
              value={functionStats.total}
              prefix={<FunctionOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="正常运行"
              value={functionStats.normal}
              suffix={`/ ${functionStats.total}`}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="警告状态"
              value={functionStats.warning}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="平均耗时"
              value={functionStats.avgTime}
              suffix="s"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 过滤和操作 */}
      <Card style={{ marginBottom: 24 }}>
        <Space>
          <span>函数分类:</span>
          <Select
            value={functionFilter}
            onChange={setFunctionFilter}
            style={{ width: 150 }}
          >
            {Object.entries(categories).map(([key, label]) => (
              <Option key={key} value={key}>{label}</Option>
            ))}
          </Select>
          
          <Button icon={<ApiOutlined />}>
            批量测试
          </Button>
          <Button icon={<DownloadOutlined />}>
            导出报告
          </Button>
        </Space>
      </Card>

      {/* 函数列表 */}
      <Row gutter={[16, 16]}>
        {filteredFunctions.map(renderFunctionCard)}
      </Row>

      {/* 函数测试模态框 */}
      <Modal
        title={`测试函数: ${selectedFunction?.name}`}
        open={isTestModalVisible}
        onCancel={() => {
          setIsTestModalVisible(false);
          setTestResults(null);
          setSelectedFunction(null);
        }}
        width={800}
        footer={null}
      >
        {selectedFunction && (
          <div>
            <Descriptions column={1} bordered size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="函数名">{selectedFunction.name}</Descriptions.Item>
              <Descriptions.Item label="描述">{selectedFunction.description}</Descriptions.Item>
              <Descriptions.Item label="参数">{selectedFunction.params.join(', ') || '无参数'}</Descriptions.Item>
              <Descriptions.Item label="返回值">{selectedFunction.returns}</Descriptions.Item>
            </Descriptions>

            <Form
              layout="vertical"
              onFinish={executeTest}
            >
              {selectedFunction.params.length > 0 && (
                <>
                  <Divider orientation="left">函数参数</Divider>
                  {selectedFunction.params.map((param, index) => (
                    <Form.Item
                      key={index}
                      label={param}
                      name={`param_${index}`}
                    >
                      {param.includes('list') ? (
                        <TextArea rows={3} placeholder="输入JSON格式的列表数据" />
                      ) : (
                        <Input placeholder={`输入${param}的值`} />
                      )}
                    </Form.Item>
                  ))}
                </>
              )}

              <Form.Item>
                <Space>
                  <Button
                    type="primary"
                    htmlType="submit"
                    icon={<PlayCircleOutlined />}
                    loading={testRunning}
                  >
                    执行测试
                  </Button>
                  <Upload>
                    <Button icon={<UploadOutlined />}>
                      上传测试数据
                    </Button>
                  </Upload>
                </Space>
              </Form.Item>
            </Form>

            {/* 测试结果 */}
            {testResults && (
              <>
                <Divider orientation="left">测试结果</Divider>
                {testResults.success ? (
                  <div>
                    <Alert
                      message="函数执行成功"
                      description={`执行时间: ${testResults.duration}`}
                      type="success"
                      style={{ marginBottom: 16 }}
                    />
                    
                    <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
                      <Descriptions.Item label="输出行数">{testResults.output.rows}</Descriptions.Item>
                      <Descriptions.Item label="输出列数">{testResults.output.columns}</Descriptions.Item>
                    </Descriptions>

                    <div style={{ marginBottom: 16 }}>
                      <strong>数据预览:</strong>
                      <Table
                        dataSource={testResults.output.preview}
                        columns={Object.keys(testResults.output.preview[0] || {}).map(key => ({
                          title: key,
                          dataIndex: key,
                          key: key
                        }))}
                        pagination={false}
                        size="small"
                        style={{ marginTop: 8 }}
                      />
                    </div>

                    <Space>
                      <Button icon={<DownloadOutlined />}>
                        下载完整结果
                      </Button>
                      <Button icon={<EyeOutlined />}>
                        查看详情
                      </Button>
                    </Space>
                  </div>
                ) : (
                  <Alert
                    message="函数执行失败"
                    description={testResults.error}
                    type="error"
                  />
                )}

                <Divider orientation="left">执行日志</Divider>
                <div style={{ 
                  background: '#f6f8fa', 
                  padding: '12px', 
                  borderRadius: '6px',
                  maxHeight: '200px',
                  overflow: 'auto'
                }}>
                  {testResults.logs.map((log, index) => (
                    <div key={index} style={{ fontSize: '12px', marginBottom: '4px' }}>
                      {log}
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default StudyFunctions;
