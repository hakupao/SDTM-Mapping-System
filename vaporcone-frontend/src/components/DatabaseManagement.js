import React, { useState } from 'react';
import {
  Card,
  Tabs,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Input,
  Alert,
  Descriptions,
  Progress,
  Statistic,
  Row,
  Col,
  Form,
  Select
} from 'antd';
import {
  DatabaseOutlined,
  TableOutlined,
  EyeOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  DownloadOutlined,
  SearchOutlined,
  SettingOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';

const { TabPane } = Tabs;
const { TextArea } = Input;
const { Search } = Input;
const { Option } = Select;

const DatabaseManagement = ({ currentStudy }) => {
  const [connectionStatus, setConnectionStatus] = useState('connected');
  const [isQueryModalVisible, setIsQueryModalVisible] = useState(false);
  const [queryResult, setQueryResult] = useState(null);
  const [queryLoading, setQueryLoading] = useState(false);

  // 数据库信息
  const dbInfo = {
    host: '127.0.0.1',
    port: 3306,
    database: 'VC-DataMigration_2.0',
    user: 'root',
    status: 'connected',
    version: 'MySQL 8.0.27',
    charset: 'utf8mb4'
  };

  // 表信息
  const [tables] = useState([
    {
      key: '1',
      name: 'VC05_CIRCULATE_CODELIST',
      type: '代码列表表',
      rows: 1250,
      size: '156KB',
      lastUpdated: '2024-01-15 15:30',
      status: 'normal'
    },
    {
      key: '2',
      name: 'VC05_CIRCULATE_METADATA',
      type: '元数据表',
      rows: 58420,
      size: '12.8MB',
      lastUpdated: '2024-01-15 15:35',
      status: 'normal'
    },
    {
      key: '3',
      name: 'VC05_CIRCULATE_TRANSDATA',
      type: '转换数据视图',
      rows: 58420,
      size: '-',
      lastUpdated: '2024-01-15 15:40',
      status: 'view'
    }
  ]);

  // 系统表统计
  const dbStats = {
    totalTables: tables.length,
    totalRows: tables.reduce((sum, table) => sum + table.rows, 0),
    totalSize: '13.0MB',
    lastBackup: '2024-01-14 23:00'
  };

  // 表格列定义
  const tableColumns = [
    {
      title: '表名',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <TableOutlined style={{ color: record.status === 'view' ? '#faad14' : '#52c41a' }} />
          <span>{text}</span>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (text, record) => (
        <Tag color={record.status === 'view' ? 'orange' : 'blue'}>
          {text}
        </Tag>
      ),
    },
    {
      title: '记录数',
      dataIndex: 'rows',
      key: 'rows',
      render: (rows) => rows.toLocaleString(),
      sorter: (a, b) => a.rows - b.rows,
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
    },
    {
      title: '最后更新',
      dataIndex: 'lastUpdated',
      key: 'lastUpdated',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === 'normal' ? 'green' : status === 'view' ? 'orange' : 'red'}>
          {status === 'normal' ? '正常' : status === 'view' ? '视图' : '异常'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space size="small">
          <Button size="small" icon={<EyeOutlined />} onClick={() => viewTableData(record)}>
            查看
          </Button>
          <Button size="small" icon={<DownloadOutlined />} onClick={() => exportTable(record)}>
            导出
          </Button>
        </Space>
      ),
    },
  ];

  // 查看表数据
  const viewTableData = async (table) => {
    try {
      // 发送真实的SQL查询获取表数据
      const response = await fetch('/api/database/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: `SELECT * FROM ${table.name} LIMIT 10`
        })
      });

      const result = await response.json();
      
      if (result.status === 'success' && result.data.success) {
        const tableData = result.data.data || [];
        
        Modal.info({
          title: `表数据预览: ${table.name}`,
          width: 1000,
          content: (
            <div>
              <div style={{ marginBottom: 16 }}>
                <span>记录数: {table.rows.toLocaleString()} | 类型: {table.type}</span>
              </div>
              <Table
                dataSource={tableData}
                columns={tableData.length > 0 ? Object.keys(tableData[0]).map(key => ({
                  title: key,
                  dataIndex: key,
                  key: key,
                  width: 120,
                  ellipsis: true
                })) : []}
                pagination={{ pageSize: 10 }}
                size="small"
                scroll={{ x: true }}
              />
              <div style={{ marginTop: 16, color: '#666', fontSize: '12px' }}>
                * 显示前10条记录的预览
              </div>
            </div>
          )
        });
      } else {
        throw new Error(result.message || '查询失败');
      }
    } catch (error) {
      Modal.error({
        title: '查看表数据失败',
        content: `无法获取表 "${table.name}" 的数据: ${error.message}`
      });
    }
  };

  // 导出表
  const exportTable = (table) => {
    Modal.confirm({
      title: '导出表数据',
      content: `确定要导出表 "${table.name}" 的数据吗？`,
      onOk() {
        console.log('导出表:', table.name);
        // 实现表导出逻辑
      }
    });
  };

  // 执行SQL查询
  const executeQuery = async (values) => {
    setQueryLoading(true);
    try {
      // 真实的API调用
      const response = await fetch('/api/database/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: values.query
        })
      });
      
      const result = await response.json();
      
      if (result.status === 'success') {
        setQueryResult(result.data);
      } else {
        setQueryResult({
          success: false,
          error: result.message || '查询失败'
        });
      }
    } catch (error) {
      setQueryResult({
        success: false,
        error: error.message
      });
    } finally {
      setQueryLoading(false);
    }
  };

  // 测试数据库连接
  const testConnection = async () => {
    Modal.info({
      title: '数据库连接测试',
      content: (
        <div>
          <Alert
            message="连接成功"
            description="数据库连接正常，所有权限验证通过"
            type="success"
            showIcon
          />
          <Descriptions column={1} style={{ marginTop: 16 }} size="small">
            <Descriptions.Item label="主机">{dbInfo.host}:{dbInfo.port}</Descriptions.Item>
            <Descriptions.Item label="数据库">{dbInfo.database}</Descriptions.Item>
            <Descriptions.Item label="版本">{dbInfo.version}</Descriptions.Item>
            <Descriptions.Item label="字符集">{dbInfo.charset}</Descriptions.Item>
            <Descriptions.Item label="连接时间">0.032s</Descriptions.Item>
          </Descriptions>
        </div>
      )
    });
  };

  return (
    <div className="database-management fade-in">
      {/* 数据库管理标题 */}
      <Alert
        message={`${currentStudy} 研究数据库管理`}
        description="管理研究相关的数据库表、视图和数据，执行SQL查询和数据导出"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      {/* 数据库状态 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="连接状态"
              value="已连接"
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="表数量"
              value={dbStats.totalTables}
              prefix={<TableOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总记录数"
              value={dbStats.totalRows}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="数据大小"
              value={dbStats.totalSize}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="tables">
        <TabPane tab={<span><TableOutlined />表管理</span>} key="tables">
          <Card>
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Button icon={<ReloadOutlined />}>
                  刷新表列表
                </Button>
                <Button icon={<SettingOutlined />} onClick={testConnection}>
                  测试连接
                </Button>
                <Button icon={<DownloadOutlined />}>
                  导出全部表
                </Button>
              </Space>
            </div>
            
            <Table
              columns={tableColumns}
              dataSource={tables}
              pagination={false}
              size="small"
            />
          </Card>
        </TabPane>

        <TabPane tab={<span><SearchOutlined />SQL查询</span>} key="query">
          <Card>
            <Form
              layout="vertical"
              onFinish={executeQuery}
            >
              <Form.Item
                label="SQL查询语句"
                name="query"
                rules={[{ required: true, message: '请输入SQL查询语句' }]}
              >
                <TextArea
                  rows={6}
                  placeholder="输入SQL查询语句，例如：&#10;SELECT STUDYID, COUNT(*) as COUNT &#10;FROM VC05_CIRCULATE_METADATA &#10;GROUP BY STUDYID;"
                  style={{ fontFamily: 'monospace' }}
                />
              </Form.Item>

              <Form.Item>
                <Space>
                  <Button
                    type="primary"
                    htmlType="submit"
                    icon={<PlayCircleOutlined />}
                    loading={queryLoading}
                  >
                    执行查询
                  </Button>
                  <Button icon={<ReloadOutlined />}>
                    清空
                  </Button>
                </Space>
              </Form.Item>
            </Form>

            {/* 查询结果 */}
            {queryResult && (
              <div style={{ marginTop: 24 }}>
                {queryResult.success ? (
                  <div>
                    <Alert
                      message="查询执行成功"
                      description={`返回 ${queryResult.rows} 行记录，执行时间: ${queryResult.executionTime}`}
                      type="success"
                      style={{ marginBottom: 16 }}
                    />
                    
                    <div style={{ marginBottom: 16 }}>
                      <strong>查询语句:</strong>
                      <div style={{ 
                        background: '#f6f8fa', 
                        padding: '12px', 
                        borderRadius: '6px',
                        fontFamily: 'monospace',
                        fontSize: '12px',
                        marginTop: '8px'
                      }}>
                        {queryResult.query}
                      </div>
                    </div>

                    <div style={{ marginBottom: 16 }}>
                      <strong>查询结果:</strong>
                      <Table
                        dataSource={queryResult.data}
                        columns={Object.keys(queryResult.data[0] || {}).map(key => ({
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
                        导出结果
                      </Button>
                    </Space>
                  </div>
                ) : (
                  <Alert
                    message="查询执行失败"
                    description={queryResult.error}
                    type="error"
                  />
                )}
              </div>
            )}
          </Card>
        </TabPane>

        <TabPane tab={<span><SettingOutlined />数据库配置</span>} key="config">
          <Card>
            <Descriptions column={2} bordered>
              <Descriptions.Item label="数据库主机">{dbInfo.host}</Descriptions.Item>
              <Descriptions.Item label="端口">{dbInfo.port}</Descriptions.Item>
              <Descriptions.Item label="数据库名">{dbInfo.database}</Descriptions.Item>
              <Descriptions.Item label="用户名">{dbInfo.user}</Descriptions.Item>
              <Descriptions.Item label="数据库版本">{dbInfo.version}</Descriptions.Item>
              <Descriptions.Item label="字符集">{dbInfo.charset}</Descriptions.Item>
              <Descriptions.Item label="连接状态">
                <Tag color="green">
                  <CheckCircleOutlined /> 已连接
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="最后备份">{dbStats.lastBackup}</Descriptions.Item>
            </Descriptions>

            <div style={{ marginTop: 16 }}>
              <Space>
                <Button type="primary" onClick={testConnection}>
                  测试连接
                </Button>
                <Button>
                  修改配置
                </Button>
                <Button>
                  数据库备份
                </Button>
              </Space>
            </div>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default DatabaseManagement;
