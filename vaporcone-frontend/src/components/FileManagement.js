import React, { useState, useEffect } from 'react';
import {
  Card,
  Tabs,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Upload,
  Progress,
  Alert,
  Input,
  Select,
  Tooltip,
  Breadcrumb
} from 'antd';
import {
  FolderOutlined,
  FileOutlined,
  UploadOutlined,
  DownloadOutlined,
  EyeOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  HomeOutlined,
  FileTextOutlined
} from '@ant-design/icons';

const { TabPane } = Tabs;
const { Search } = Input;
const { Option } = Select;

const FileManagement = ({ currentStudy }) => {
  const [currentPath, setCurrentPath] = useState('/');
  const [fileFilter, setFileFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  // 真实文件数据
  const [fileData, setFileData] = useState({
    raw: [],
    cleaned: [],
    formatted: [],
    sdtm: [],
    output: []
  });

  // 从后端API获取文件列表
  const fetchFiles = async (type) => {
    try {
      const response = await fetch(`/api/files/list?type=${type}`);
      const data = await response.json();
      
      if (data.status === 'success') {
        const files = data.data.map((file, index) => ({
          key: `${type}-${index}`,
          name: file.name,
          size: file.size,
          type: file.type,
          modified: file.modified,
          status: file.status || 'normal'
        }));
        
        setFileData(prev => ({
          ...prev,
          [type]: files
        }));
      }
    } catch (error) {
      console.error(`获取${type}文件列表失败:`, error);
      // 保持空数组
      setFileData(prev => ({
        ...prev,
        [type]: []
      }));
    }
  };

  // 初始化时获取所有类型的文件
  useEffect(() => {
    const fileTypes = ['raw', 'cleaned', 'formatted', 'sdtm', 'output'];
    fileTypes.forEach(type => {
      fetchFiles(type);
    });
  }, []);

  // 刷新文件列表
  const refreshFiles = () => {
    const fileTypes = ['raw', 'cleaned', 'formatted', 'sdtm', 'output'];
    fileTypes.forEach(type => {
      fetchFiles(type);
    });
  };

  // 获取状态标签
  const getStatusTag = (status) => {
    const statusConfig = {
      normal: { color: 'default', text: '正常' },
      processing: { color: 'blue', text: '处理中' },
      completed: { color: 'green', text: '已完成' },
      error: { color: 'red', text: '错误' }
    };
    const config = statusConfig[status] || statusConfig.normal;
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 获取文件类型图标
  const getFileIcon = (type) => {
    switch (type) {
      case 'csv':
        return <FileTextOutlined style={{ color: '#52c41a' }} />;
      case 'zip':
        return <FileOutlined style={{ color: '#faad14' }} />;
      default:
        return <FileOutlined />;
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '文件名',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          {getFileIcon(record.type)}
          <span>{text}</span>
        </Space>
      ),
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      sorter: (a, b) => {
        const sizeA = parseFloat(a.size) * (a.size.includes('MB') ? 1024 : 1);
        const sizeB = parseFloat(b.size) * (b.size.includes('MB') ? 1024 : 1);
        return sizeA - sizeB;
      },
    },
    {
      title: '修改时间',
      dataIndex: 'modified',
      key: 'modified',
      sorter: (a, b) => new Date(a.modified) - new Date(b.modified),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => getStatusTag(status),
      filters: [
        { text: '正常', value: 'normal' },
        { text: '处理中', value: 'processing' },
        { text: '已完成', value: 'completed' },
        { text: '错误', value: 'error' },
      ],
      onFilter: (value, record) => record.status === value,
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="预览">
            <Button size="small" icon={<EyeOutlined />} onClick={() => previewFile(record)} />
          </Tooltip>
          <Tooltip title="下载">
            <Button size="small" icon={<DownloadOutlined />} onClick={() => downloadFile(record)} />
          </Tooltip>
          <Tooltip title="删除">
            <Button size="small" danger icon={<DeleteOutlined />} onClick={() => deleteFile(record)} />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 文件操作
  const previewFile = (file) => {
    Modal.info({
      title: `预览文件: ${file.name}`,
      width: 800,
      content: (
        <div>
          <div style={{ marginBottom: 16 }}>
            <span>文件大小: {file.size} | 修改时间: {file.modified}</span>
          </div>
          <div style={{ 
            background: '#f6f8fa', 
            padding: '16px', 
            borderRadius: '6px',
            fontFamily: 'monospace',
            fontSize: '12px',
            maxHeight: '400px',
            overflow: 'auto'
          }}>
            <pre>
{`STUDYID,DOMAIN,USUBJID,SUBJID,RFSTDTC,RFENDTC,SITEID,AGE,SEX
CIRCULATE,DM,CIRCULATE-001,001,2023-01-15,,001,65,M
CIRCULATE,DM,CIRCULATE-002,002,2023-01-16,,001,58,F
CIRCULATE,DM,CIRCULATE-003,003,2023-01-18,,002,72,M
...`}
            </pre>
          </div>
        </div>
      )
    });
  };

  const downloadFile = (file) => {
    console.log('下载文件:', file.name);
    // 实现文件下载逻辑
  };

  const deleteFile = (file) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除文件 "${file.name}" 吗？此操作不可恢复。`,
      onOk() {
        console.log('删除文件:', file.name);
        // 实现文件删除逻辑
      }
    });
  };

  // 获取当前选中的文件数据
  const getCurrentFiles = (tab) => {
    return fileData[tab] || [];
  };

  // 渲染文件统计
  const renderFileStats = (files) => {
    const totalSize = files.reduce((acc, file) => {
      const size = parseFloat(file.size);
      const unit = file.size.includes('MB') ? 1 : 0.001;
      return acc + (size * unit);
    }, 0);

    const statusCounts = files.reduce((acc, file) => {
      acc[file.status] = (acc[file.status] || 0) + 1;
      return acc;
    }, {});

    return (
      <div style={{ display: 'flex', gap: '24px', marginBottom: '16px' }}>
        <span>文件总数: <strong>{files.length}</strong></span>
        <span>总大小: <strong>{totalSize.toFixed(1)}MB</strong></span>
        {Object.entries(statusCounts).map(([status, count]) => (
          <span key={status}>
            {status === 'normal' ? '正常' : 
             status === 'processing' ? '处理中' : 
             status === 'completed' ? '已完成' : '错误'}: 
            <strong>{count}</strong>
          </span>
        ))}
      </div>
    );
  };

  return (
    <div className="file-management fade-in">
      {/* 文件管理标题 */}
      <Alert
        message={`${currentStudy} 研究文件管理`}
        description="管理数据处理流程中的各类文件，包括原始数据、中间结果和最终输出"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      {/* 文件浏览器 */}
      <Card 
        title="文件浏览器"
        extra={
          <Button 
            icon={<ReloadOutlined />} 
            onClick={refreshFiles}
            size="small"
          >
            刷新
          </Button>
        }
      >
        <Tabs defaultActiveKey="raw">
          <TabPane tab={<span><FolderOutlined />原始数据</span>} key="raw">
            <div>
              {renderFileStats(getCurrentFiles('raw'))}
              <div style={{ marginBottom: 16 }}>
                <Space>
                  <Search
                    placeholder="搜索文件..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    style={{ width: 200 }}
                  />
                  <Select
                    value={fileFilter}
                    onChange={setFileFilter}
                    style={{ width: 120 }}
                  >
                    <Option value="all">全部文件</Option>
                    <Option value="csv">CSV文件</Option>
                    <Option value="excel">Excel文件</Option>
                  </Select>
                  <Button icon={<UploadOutlined />}>
                    上传文件
                  </Button>
                </Space>
              </div>
              <Table
                columns={columns}
                dataSource={getCurrentFiles('raw')}
                pagination={{ pageSize: 10 }}
                size="small"
              />
            </div>
          </TabPane>

          <TabPane tab={<span><FileTextOutlined />清洗数据</span>} key="cleaned">
            <div>
              {renderFileStats(getCurrentFiles('cleaned'))}
              <Table
                columns={columns}
                dataSource={getCurrentFiles('cleaned')}
                pagination={{ pageSize: 10 }}
                size="small"
              />
            </div>
          </TabPane>

          <TabPane tab={<span><FileTextOutlined />格式化数据</span>} key="formatted">
            <div>
              {renderFileStats(getCurrentFiles('formatted'))}
              <Table
                columns={columns}
                dataSource={getCurrentFiles('formatted')}
                pagination={{ pageSize: 10 }}
                size="small"
              />
            </div>
          </TabPane>

          <TabPane tab={<span><FileTextOutlined />SDTM数据集</span>} key="sdtm">
            <div>
              {renderFileStats(getCurrentFiles('sdtm'))}
              <Table
                columns={columns}
                dataSource={getCurrentFiles('sdtm')}
                pagination={{ pageSize: 10 }}
                size="small"
              />
            </div>
          </TabPane>

          <TabPane tab={<span><DownloadOutlined />最终输出</span>} key="output">
            <div>
              {renderFileStats(getCurrentFiles('output'))}
              <div style={{ marginBottom: 16 }}>
                <Space>
                  <Button type="primary" icon={<DownloadOutlined />}>
                    下载全部文件
                  </Button>
                  <Button icon={<DownloadOutlined />}>
                    下载M5包
                  </Button>
                </Space>
              </div>
              <Table
                columns={columns}
                dataSource={getCurrentFiles('output')}
                pagination={{ pageSize: 10 }}
                size="small"
              />
            </div>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default FileManagement;
