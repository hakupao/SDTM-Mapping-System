import React, { useState } from 'react';
import {
  Card,
  Tabs,
  Form,
  Input,
  Button,
  Space,
  Alert,
  Descriptions,
  Tag,
  Upload,
  Modal,
  Progress,
  List,
  Select,
  Switch
} from 'antd';
import {
  SettingOutlined,
  UploadOutlined,
  DownloadOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  FileExcelOutlined,
  DatabaseOutlined,
  FolderOutlined
} from '@ant-design/icons';

const { TabPane } = Tabs;
const { TextArea } = Input;
const { Option } = Select;

const ConfigManagement = ({ currentStudy }) => {
  const [configData, setConfigData] = useState({
    study: {
      STUDY_ID: 'CIRCULATE',
      CODELIST_TABLE_NAME: 'VC05_CIRCULATE_CODELIST',
      METADATA_TABLE_NAME: 'VC05_CIRCULATE_METADATA',
      TRANSDATA_VIEW_NAME: 'VC05_CIRCULATE_TRANSDATA',
      M5_PROJECT_NAME: '[UAT]CIRCULATE',
      RAW_DATA_ROOT_PATH: 'C:\\Users\\張泊江\\iTMS株式会社\\DXユニット開発チーム - 統合DB\\02_VAPORCONE\\60_CIRCULATE_GALAXY\\01_Raw Data\\データセット\\20250627_CSV'
    },
    database: {
      DB_HOST: '127.0.0.1',
      DB_USER: 'root',
      DB_PASSWORD: 'root',
      DB_DATABASE: 'VC-DataMigration_2.0'
    },
    paths: {
      ROOT_PATH: 'C:\\Local\\iTMS\\SDTM',
      INPUTFILE_PATH: '',
      INPUTPACKAGE_PATH: '',
      CLEANINGSTEP_PATH: '',
      FORMAT_PATH: '',
      SDTMDATASET_PATH: ''
    }
  });

  const [configStatus, setConfigStatus] = useState({
    excel: { status: 'success', message: 'Excel配置文件已加载' },
    database: { status: 'success', message: '数据库连接正常' },
    paths: { status: 'warning', message: '部分路径需要验证' },
    functions: { status: 'success', message: '研究特定函数正常' }
  });

  const [isUploadModalVisible, setIsUploadModalVisible] = useState(false);

  // 配置验证
  const validateConfig = () => {
    Modal.info({
      title: '配置验证',
      content: (
        <div>
          <List
            dataSource={[
              { name: 'Excel配置文件', status: 'success', message: '配置完整，格式正确' },
              { name: '数据库连接', status: 'success', message: '连接正常' },
              { name: '文件路径', status: 'warning', message: '原始数据路径需要确认' },
              { name: '研究函数', status: 'success', message: '16个函数全部可用' }
            ]}
            renderItem={item => (
              <List.Item>
                <List.Item.Meta
                  avatar={
                    item.status === 'success' ? 
                      <CheckCircleOutlined style={{ color: '#52c41a' }} /> :
                      <ExclamationCircleOutlined style={{ color: '#faad14' }} />
                  }
                  title={item.name}
                  description={item.message}
                />
              </List.Item>
            )}
          />
        </div>
      )
    });
  };

  // 导出配置
  const exportConfig = () => {
    const config = JSON.stringify(configData, null, 2);
    const blob = new Blob([config], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentStudy}_config.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="config-management fade-in">
      {/* 配置状态总览 */}
      <Alert
        message={`${currentStudy} 研究配置管理`}
        description="管理研究配置参数，包括数据库连接、文件路径、Excel配置等"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      {/* 配置状态卡片 */}
      <Card title="配置状态总览" style={{ marginBottom: 24 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          {Object.entries(configStatus).map(([key, config]) => (
            <Card key={key} size="small">
              <div style={{ textAlign: 'center' }}>
                {config.status === 'success' ? (
                  <CheckCircleOutlined style={{ fontSize: '24px', color: '#52c41a', marginBottom: '8px' }} />
                ) : (
                  <ExclamationCircleOutlined style={{ fontSize: '24px', color: '#faad14', marginBottom: '8px' }} />
                )}
                <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                  {key === 'excel' ? 'Excel配置' : 
                   key === 'database' ? '数据库' :
                   key === 'paths' ? '文件路径' : '研究函数'}
                </div>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  {config.message}
                </div>
              </div>
            </Card>
          ))}
        </div>

        <div style={{ marginTop: 16, textAlign: 'center' }}>
          <Space>
            <Button type="primary" onClick={validateConfig}>
              验证配置
            </Button>
            <Button icon={<DownloadOutlined />} onClick={exportConfig}>
              导出配置
            </Button>
            <Button icon={<UploadOutlined />} onClick={() => setIsUploadModalVisible(true)}>
              导入配置
            </Button>
          </Space>
        </div>
      </Card>

      {/* 配置详情 */}
      <Card title="配置详情">
        <Tabs defaultActiveKey="study">
          <TabPane tab={<span><SettingOutlined />研究配置</span>} key="study">
            <Form layout="vertical">
              <Form.Item label="研究ID">
                <Input value={configData.study.STUDY_ID} disabled />
              </Form.Item>
              <Form.Item label="代码列表表名">
                <Input value={configData.study.CODELIST_TABLE_NAME} />
              </Form.Item>
              <Form.Item label="元数据表名">
                <Input value={configData.study.METADATA_TABLE_NAME} />
              </Form.Item>
              <Form.Item label="转换数据视图名">
                <Input value={configData.study.TRANSDATA_VIEW_NAME} />
              </Form.Item>
              <Form.Item label="M5项目名称">
                <Input value={configData.study.M5_PROJECT_NAME} />
              </Form.Item>
              <Form.Item label="原始数据根路径">
                <TextArea 
                  value={configData.study.RAW_DATA_ROOT_PATH} 
                  rows={2}
                />
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane tab={<span><DatabaseOutlined />数据库配置</span>} key="database">
            <Form layout="vertical">
              <Form.Item label="数据库主机">
                <Input value={configData.database.DB_HOST} />
              </Form.Item>
              <Form.Item label="用户名">
                <Input value={configData.database.DB_USER} />
              </Form.Item>
              <Form.Item label="密码">
                <Input.Password value={configData.database.DB_PASSWORD} />
              </Form.Item>
              <Form.Item label="数据库名">
                <Input value={configData.database.DB_DATABASE} />
              </Form.Item>
              <Form.Item>
                <Button type="primary">测试连接</Button>
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane tab={<span><FolderOutlined />路径配置</span>} key="paths">
            <Form layout="vertical">
              <Form.Item label="根路径">
                <Input value={configData.paths.ROOT_PATH} />
              </Form.Item>
              <Form.Item label="输入文件路径">
                <Input placeholder="自动生成" disabled />
              </Form.Item>
              <Form.Item label="输入包路径">
                <Input placeholder="自动生成" disabled />
              </Form.Item>
              <Form.Item label="清洗步骤路径">
                <Input placeholder="自动生成" disabled />
              </Form.Item>
              <Form.Item label="格式化路径">
                <Input placeholder="自动生成" disabled />
              </Form.Item>
              <Form.Item label="SDTM数据集路径">
                <Input placeholder="自动生成" disabled />
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane tab={<span><FileExcelOutlined />Excel配置</span>} key="excel">
            <Alert
              message="Excel配置文件信息"
              description="当前系统读取的是 CIRCULATE_OperationConf.xlsx 文件中的配置"
              type="info"
              style={{ marginBottom: 16 }}
            />

            <Descriptions column={2} bordered>
              <Descriptions.Item label="配置文件">CIRCULATE_OperationConf.xlsx</Descriptions.Item>
              <Descriptions.Item label="最后更新">2024-01-15 14:30</Descriptions.Item>
              <Descriptions.Item label="工作表数量">9个</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color="green">正常</Tag>
              </Descriptions.Item>
            </Descriptions>

            <div style={{ marginTop: 16 }}>
              <h4>工作表状态:</h4>
              <List
                dataSource={[
                  { name: 'SheetSetting', status: 'success', records: 9 },
                  { name: 'Files', status: 'success', records: 23 },
                  { name: 'Patients', status: 'success', records: 150 },
                  { name: 'Process', status: 'success', records: 245 },
                  { name: 'CodeList', status: 'success', records: 89 },
                  { name: 'Mapping', status: 'success', records: 156 },
                  { name: 'DomainsSetting', status: 'success', records: 8 },
                  { name: 'Sites', status: 'success', records: 5 },
                  { name: 'EXDETAILS', status: 'success', records: 12 }
                ]}
                renderItem={item => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                      title={item.name}
                      description={`${item.records} 条记录`}
                    />
                    <Tag color="green">正常</Tag>
                  </List.Item>
                )}
              />
            </div>

            <div style={{ marginTop: 16 }}>
              <Space>
                <Button icon={<UploadOutlined />}>
                  上传新配置文件
                </Button>
                <Button icon={<DownloadOutlined />}>
                  下载当前配置
                </Button>
                <Button>
                  重新加载配置
                </Button>
              </Space>
            </div>
          </TabPane>
        </Tabs>
      </Card>

      {/* 配置导入模态框 */}
      <Modal
        title="导入配置"
        open={isUploadModalVisible}
        onCancel={() => setIsUploadModalVisible(false)}
        footer={null}
      >
        <Upload.Dragger
          name="config"
          multiple={false}
          accept=".json,.xlsx"
        >
          <p className="ant-upload-drag-icon">
            <UploadOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持 JSON 配置文件或 Excel 配置文件
          </p>
        </Upload.Dragger>
      </Modal>
    </div>
  );
};

export default ConfigManagement;
