# VAPORCONE 重构后端架构说明

## 📁 项目结构

```
backend/
├── app.py                  # 🚀 主应用入口 (重构版本)
├── config.py               # ⚙️ 配置管理
├── api/                    # 🔗 API蓝图模块
│   ├── __init__.py        # API蓝图注册和配置
│   ├── system.py          # 系统状态API
│   ├── logs.py            # 日志监控API
│   ├── execution.py       # 流程执行API
│   ├── functions.py       # 研究函数API
│   ├── files.py           # 文件管理API
│   └── database.py        # 数据库管理API
├── services/               # 🛠️ 业务逻辑服务层
│   ├── __init__.py
│   ├── system_service.py  # 系统服务
│   ├── log_service.py     # 日志服务
│   └── execution_service.py # 执行服务
├── models/                 # 📊 数据模型
├── utils/                  # 🔧 工具函数
├── websockets/             # 🔄 WebSocket处理
│   ├── __init__.py
│   └── events.py

```

## 🆕 主要改进

### 1. **模块化架构**
- 按功能域拆分API蓝图
- 业务逻辑分离到服务层
- 清晰的职责划分

### 2. **Flask-RESTX集成**
- 自动生成Swagger UI文档
- API接口标准化
- 请求/响应验证
- 中文化API文档

### 3. **代码规模对比**
```
原架构:
- app.py: 1189行 (过于庞大)

重构后:
- app.py: ~150行 (主入口)
- 各API蓝图: ~100-200行/模块
- 各服务类: ~200-400行/模块
```

## 🚀 启动方式

### 方法1：使用新的重构版本
```bash
cd vaporcone-frontend/backend
   python app.py
```

### 方法2：继续使用原版本 (备份)
```bash
cd vaporcone-frontend/backend  
python app.py
```

## 📖 API文档访问

启动服务器后，访问以下地址：

- **Swagger UI**: http://localhost:5000/api/docs/
- **健康检查**: http://localhost:5000/health
- **系统状态**: http://localhost:5000/api/system/status

## 🔧 配置管理

### 环境变量
```bash
# 设置运行环境
export FLASK_ENV=development  # 开发环境
export FLASK_ENV=production   # 生产环境
```

### 配置文件
- `config.py` - 集中管理所有配置参数
- 支持开发/生产环境配置分离
- API文档、CORS、WebSocket等配置

## 📡 API模块说明

### 系统状态模块 (`api/system.py`)
- `GET /api/system/status` - 系统资源监控
- `GET /api/system/studies` - 研究列表
- `GET /api/system/health` - 健康检查

### 日志监控模块 (`api/logs.py`)
- `GET /api/logs/list` - 日志查询和过滤
- `POST /api/logs/clear` - 清空日志
- `GET /api/logs/statistics` - 日志统计

### 流程执行模块 (`api/execution.py`)  
- `POST /api/execution/start` - 启动流程
- `POST /api/execution/run-step` - 单步执行
- `GET /api/execution/history` - 执行历史

## 🔄 WebSocket功能

### 实时事件
- `new_log` - 新日志推送
- `execution_update` - 执行状态更新
- `system_notification` - 系统通知

### 客户端订阅
```javascript
// 订阅日志推送
socket.emit('subscribe_logs');

// 监听新日志
socket.on('new_log', (logEntry) => {
    console.log('新日志:', logEntry);
});
```

## 🛠️ 服务层架构

### SystemService (系统服务)
- 系统状态监控
- 研究项目管理
- 健康检查逻辑

### LogService (日志服务)
- 日志存储和检索
- 日志过滤和搜索
- 日志导出功能

### ExecutionService (执行服务)
- 流程控制和调度
- 脚本执行管理
- 执行历史跟踪

## 🔄 迁移指南

### 从原app.py迁移到新架构

1. **安装新依赖**
   ```bash
   pip install Flask-RESTX==1.3.0
   ```

2. **更新启动脚本**
   - 将启动命令改为 `python app.py`
   - 或修改现有脚本文件

3. **前端调用兼容性**
   - API路径保持不变: `/api/xxx`
   - 响应格式保持兼容
   - WebSocket事件名称一致

4. **逐步迁移功能**
   - 可以并行运行两个版本进行测试
   - 确认功能正常后切换到新版本

## ⚠️ 注意事项

1. **VAPORCONE模块依赖**
   - 系统仍需要VAPORCONE核心模块
   - 确保VC_BC01_constant.py等文件存在

2. **数据库连接**
   - 数据库配置通过VAPORCONE模块获取
   - 确保数据库连接正常

3. **文件权限**
   - 确保脚本文件有执行权限
   - 临时目录写入权限

## 🚧 下一步优化计划

1. **数据库抽象层**
   - 实现ORM模型
   - 数据库操作标准化

2. **中间件系统**
   - 请求日志记录
   - 错误处理中间件
   - 性能监控中间件

3. **测试覆盖**
   - 单元测试
   - 集成测试
   - API测试

4. **缓存系统**
   - Redis集成
   - 查询结果缓存
   - 性能优化

---

## 💡 技术栈

- **框架**: Flask + Flask-RESTX
- **文档**: 自动生成Swagger UI
- **实时通信**: SocketIO
- **架构模式**: 蓝图 + 服务层
- **配置管理**: 环境配置分离
