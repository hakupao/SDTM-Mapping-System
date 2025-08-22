import React, { useState, useEffect } from 'react';
import { Layout, Menu, Avatar, Dropdown, Space, Typography, Tag } from 'antd';
import {
  DashboardOutlined,
  PlayCircleOutlined,
  SettingOutlined,
  FolderOutlined,
  FileTextOutlined,
  DatabaseOutlined,
  UserOutlined,
  ExperimentOutlined
} from '@ant-design/icons';
import Dashboard from './components/Dashboard';
import ProcessExecution from './components/ProcessExecution';
import ConfigManagement from './components/ConfigManagement';
import FileManagement from './components/FileManagement';
import LogMonitor from './components/LogMonitor';
import DatabaseManagement from './components/DatabaseManagement';
import StudyFunctions from './components/StudyFunctions';
import './App.css';

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

function App() {
  const [collapsed, setCollapsed] = useState(false);
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [currentStudy, setCurrentStudy] = useState('CIRCULATE');
  const [studyList] = useState(['CIRCULATE', 'GOZILA', 'MONSTAR2']);

  // 用户菜单
  const userMenu = (
    <Menu>
      <Menu.Item key="profile">个人资料</Menu.Item>
      <Menu.Item key="settings">设置</Menu.Item>
      <Menu.Divider />
      <Menu.Item key="logout">退出登录</Menu.Item>
    </Menu>
  );

  // 研究切换菜单
  const studyMenu = (
    <Menu
      onClick={({ key }) => setCurrentStudy(key)}
      selectedKeys={[currentStudy]}
    >
      {studyList.map(study => (
        <Menu.Item key={study}>
          {study}
        </Menu.Item>
      ))}
    </Menu>
  );

  // 侧边栏菜单项
  const menuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: '主控台',
    },
    {
      key: 'execution',
      icon: <PlayCircleOutlined />,
      label: '流程执行',
    },
    {
      key: 'functions',
      icon: <ExperimentOutlined />,
      label: '研究函数',
    },
    {
      key: 'config',
      icon: <SettingOutlined />,
      label: '配置管理',
    },
    {
      key: 'files',
      icon: <FolderOutlined />,
      label: '文件管理',
    },
    {
      key: 'logs',
      icon: <FileTextOutlined />,
      label: '日志监控',
    },
    {
      key: 'database',
      icon: <DatabaseOutlined />,
      label: '数据库',
    },
  ];

  // 渲染当前页面内容
  const renderContent = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard currentStudy={currentStudy} />;
      case 'execution':
        return <ProcessExecution currentStudy={currentStudy} />;
      case 'functions':
        return <StudyFunctions currentStudy={currentStudy} />;
      case 'config':
        return <ConfigManagement currentStudy={currentStudy} />;
      case 'files':
        return <FileManagement currentStudy={currentStudy} />;
      case 'logs':
        return <LogMonitor currentStudy={currentStudy} />;
      case 'database':
        return <DatabaseManagement currentStudy={currentStudy} />;
      default:
        return <Dashboard currentStudy={currentStudy} />;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        padding: '0 16px', 
        background: '#fff', 
        borderBottom: '1px solid #f0f0f0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Title level={4} style={{ margin: 0, marginRight: 24 }}>
            VAPORCONE 数据处理平台
          </Title>
          <Space>
            <span>当前研究:</span>
            <Dropdown overlay={studyMenu} trigger={['click']}>
              <Tag color="blue" style={{ cursor: 'pointer', fontSize: '14px' }}>
                {currentStudy} ▼
              </Tag>
            </Dropdown>
          </Space>
        </div>
        
        <Space>
          <Tag color="green">系统运行正常</Tag>
          <Dropdown overlay={userMenu} trigger={['click']}>
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} />
              <span>管理员</span>
            </Space>
          </Dropdown>
        </Space>
      </Header>

      <Layout>
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={(value) => setCollapsed(value)}
          style={{
            background: '#fff',
            borderRight: '1px solid #f0f0f0'
          }}
        >
          <Menu
            mode="inline"
            selectedKeys={[currentPage]}
            items={menuItems}
            style={{ height: '100%', borderRight: 0 }}
            onClick={({ key }) => setCurrentPage(key)}
          />
        </Sider>

        <Layout style={{ padding: '24px' }}>
          <Content
            style={{
              background: '#fff',
              padding: 24,
              margin: 0,
              minHeight: 280,
              borderRadius: '8px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)'
            }}
          >
            {renderContent()}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
}

export default App;
