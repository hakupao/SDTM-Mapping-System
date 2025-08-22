# VAPORCONE 数据处理平台前端界面

基于 React + Ant Design 构建的现代化 Web 界面，用于管理和监控 VAPORCONE SDTM 数据转换流水线。

## ⚠️ 重要说明

**本系统采用真实数据运行模式**：
- 🚫 **不提供模拟数据或演示模式**
- 📊 **完全依赖真实的VAPORCONE数据和配置**  
- 🔒 **必须具备正确的系统环境和数据库连接**
- 🛠️ **VAPORCONE核心模块为系统运行的必要条件**
- ⚠️ **缺少核心模块或数据库连接将导致系统无法正常工作**

## 功能特性

### 🎯 核心功能
- **主控台 (Dashboard)**: 
  - ✅ **系统状态监控**: CPU、内存、磁盘使用率实时显示
  - ✅ **执行进度总览**: 数据处理流程状态可视化
  - ✅ **最近执行记录**: 历史操作日志和状态追踪
  - ✅ **ECharts图表**: 系统性能和数据处理趋势图表
- **流程执行 (ProcessExecution)**: 
  - ✅ **选择性执行**: 支持单独执行或批量执行指定步骤
  - ✅ **实时监控**: WebSocket实时更新执行状态和日志
  - ✅ **8步流程**: OP00-OP05 + PS01-PS02 完整数据处理链
  - ✅ **步骤依赖管理**: 智能检测步骤依赖关系
  - ✅ **错误处理**: 详细的错误信息和执行结果反馈
  - ✅ **执行时间预估**: 每个步骤的预计执行时间显示
- **研究函数管理 (StudyFunctions)**: 管理和测试研究特定的Python函数
- **配置管理 (ConfigManagement)**: 研究配置参数管理和Excel配置文件处理
- **文件管理 (FileManagement)**: 
  - ✅ **多阶段文件浏览**: raw、cleaned、formatted、sdtm、output
  - ✅ **文件预览**: 支持CSV文件内容预览
  - ✅ **文件信息**: 大小、修改时间、状态显示
- **日志监控 (LogMonitor)**: 实时日志流、错误追踪、日志级别过滤
- **数据库管理 (DatabaseManagement)**: 
  - ✅ **数据库状态监控**: 连接状态、表统计信息
  - ✅ **SQL查询执行**: 支持自定义SQL查询
  - ✅ **数据预览**: 表数据查看和导出

### 🔧 技术特点
- **前端技术栈**: React 18.2.0 + Ant Design 5.0.0 + React Router 6.3.0
- **图表可视化**: ECharts 5.4.0 + echarts-for-react 3.0.2
- **实时通信**: Socket.IO Client 4.5.0 + WebSocket 实时更新
- **HTTP客户端**: Axios 1.1.0 处理API调用
- **样式组件**: Styled Components 5.3.6 + Ant Design Icons 4.8.0
- **后端API**: Python Flask + Flask-SocketIO + Flask-CORS
- **响应式设计**: 支持桌面端和移动端适配
- **多研究支持**: 支持 CIRCULATE、GOZILA、MONSTAR2 等多个研究
- **智能监控**: 系统资源监控、错误预警、性能分析

## 系统架构

```
vaporcone-frontend/
├── public/                 # 静态资源
├── src/                   # React 源代码
│   ├── components/        # React 组件
│   │   ├── Dashboard.js           # 主控台
│   │   ├── ProcessExecution.js    # 流程执行
│   │   ├── StudyFunctions.js      # 研究函数管理
│   │   ├── ConfigManagement.js    # 配置管理
│   │   ├── FileManagement.js      # 文件管理
│   │   ├── LogMonitor.js          # 日志监控
│   │   └── DatabaseManagement.js  # 数据库管理
│   ├── App.js             # 主应用组件
│   ├── App.css            # 全局样式
│   └── index.js           # 应用入口
├── backend/               # Python 后端API
│   ├── app.py            # Flask API服务器
│   └── requirements.txt   # Python依赖
├── package.json          # 项目配置
└── README.md            # 说明文档
```

## 快速启动 🚀

### 一键启动 (推荐)
```bash
# Windows 用户
双击运行 start.bat

# 或者在命令行中运行
start.bat
```

这个脚本会自动：
1. 🔍 **环境检查**: 验证Node.js和Python安装情况
2. 🔌 **端口管理**: 自动检查并释放被占用的端口3000和5000
3. 📦 **依赖安装**: 自动安装前端npm依赖和后端Python依赖
4. 🐍 **虚拟环境**: 自动创建和激活Python虚拟环境
5. 🔍 **模块检查**: 验证VAPORCONE核心模块可用性
6. 🚀 **服务启动**: 启动后端API服务器 (端口5000) 和前端开发服务器 (端口3000)
7. 🌐 **自动打开**: 3秒后自动在浏览器中打开系统界面

### 手动安装和运行

#### 环境要求
- Node.js 16.0+
- Python 3.8+
- MySQL 8.0+ (可选，用于真实数据库连接)

#### 前端安装

1. **安装依赖**
```bash
cd vaporcone-frontend
npm install
```

2. **启动开发服务器**
```bash
npm start
```

前端将在 http://localhost:3000 启动

#### 后端安装

1. **虚拟环境管理**

启动脚本会智能检测和使用虚拟环境：

```bash
# 脚本会按优先级自动选择虚拟环境：
# 1. 根目录虚拟环境 (SDTM/.venv) - 推荐
# 2. backend目录虚拟环境 (backend/.venv)  
# 3. 如果都不存在，会在backend目录创建新环境
```

**推荐配置 - 根目录统一虚拟环境：**
```bash
# 在SDTM根目录下
python -m venv .venv

# Windows 激活
.venv\Scripts\activate

# Linux/Mac 激活  
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

**替代方案 - backend独立虚拟环境：**
```bash
cd vaporcone-frontend/backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

2. **安装Python依赖**

启动脚本会自动处理依赖安装：
```bash
# 脚本会智能选择依赖文件：
# 1. 优先使用根目录的 requirements.txt (推荐)
# 2. 其次使用 backend/requirements.txt
# 3. 如果都不存在，会创建临时依赖文件
```

**手动安装依赖（可选）：**
```bash
# 如果使用根目录虚拟环境
pip install -r requirements.txt

# 如果使用backend虚拟环境  
pip install -r backend/requirements.txt
```

3. **启动后端API服务器**
```bash
python app.py
```

后端API将在 http://localhost:5000 启动

### 测试API接口
```bash
# 运行API测试脚本
python test_api.py
```

### 停止服务

#### 一键停止 (推荐)
```bash
# Windows 用户
.\stop.bat              # 基础版本 - 快速停止所有服务
.\stop_enhanced.bat     # 增强版本 (推荐) - 提供详细选项和状态检查
```

**增强版停止脚本功能：**
- 🔍 **状态检查**: 检测当前运行的前端和后端服务
- 🎯 **选择性停止**: 可选择停止特定服务或全部服务
- 💪 **强制停止**: 提供强制终止所有相关进程的选项
- 📊 **详细信息**: 显示进程PID、端口占用等详细信息
- 🧹 **资源清理**: 自动清理临时文件和缓存
- ✅ **停止验证**: 验证服务是否完全停止

#### 状态检查
```bash
# 查看运行状态
.\test_stop.bat
```

**状态检查脚本功能：**
- 📊 实时显示前端和后端服务状态
- 🔌 检查端口3000和5000的占用情况
- 📋 列出所有相关进程信息
- 🎮 提供快速操作选项（启动/停止/打开界面）

#### 手动停止
```bash
# 手动停止进程
# Windows
taskkill /f /im node.exe     # 停止前端
taskkill /f /im python.exe   # 停止后端

# Linux/Mac  
pkill -f "node.*npm"         # 停止前端
pkill -f "python.*app.py"    # 停止后端
```

### 配置数据库

确保MySQL数据库运行正常，并在 `VC_BC01_constant.py` 中配置正确的数据库连接参数：

```python
DB_HOST = '127.0.0.1'
DB_USER = 'root'
DB_PASSWORD = 'your_password'
DB_DATABASE = 'VC-DataMigration_2.0'
```

## 使用指南

### 1. 研究切换
- 在顶部导航栏点击研究名称下拉菜单
- 选择要管理的研究（CIRCULATE、GOZILA、MONSTAR2等）

### 2. 流程执行
- 进入"流程执行"页面
- 点击"开始执行"运行完整的8步流程
- 实时监控每个步骤的执行状态和进度

### 3. 研究函数管理
- 查看当前研究的所有特定函数
- 测试函数功能和性能
- 查看函数代码和文档

### 4. 文件管理
- 浏览各个阶段的数据文件
- 预览文件内容
- 下载最终输出文件

### 5. 日志监控
- 实时查看系统运行日志
- 按级别过滤日志（ERROR、WARNING、INFO、DEBUG）
- 搜索特定日志内容
- 导出日志文件

### 6. 数据库管理
- 查看数据库表状态
- 执行自定义SQL查询
- 预览表数据
- 导出查询结果

## API 接口

### 系统状态
```
GET /api/system/status      # 获取系统状态
GET /api/system/studies     # 获取研究列表
```

### 流程执行
```
GET  /api/execution/status  # 获取执行状态
POST /api/execution/start   # 开始执行
POST /api/execution/stop    # 停止执行
POST /api/execution/reset   # 重置执行
```

### 研究函数
```
GET  /api/functions/list    # 获取函数列表
POST /api/functions/test    # 测试函数
```

### 文件管理
```
GET  /api/files/list        # 获取文件列表
POST /api/files/preview     # 预览文件
```

### 数据库
```
GET  /api/database/status   # 获取数据库状态
POST /api/database/query    # 执行SQL查询
```

## WebSocket 事件

### 客户端订阅
```javascript
socket.on('execution_update', (data) => {
    // 处理执行状态更新
});

socket.on('log_entry', (log) => {
    // 处理实时日志
});
```

## 故障排除

### 🔧 常见问题和解决方案

#### 1. **VAPORCONE模块导入失败**
```
错误信息: No module named 'VC_BC01_constant'
```

**解决方案：**
- ⚠️ **这是系统错误！** VAPORCONE核心模块是系统运行的必要条件
- 🔧 **必须解决此问题才能使用系统功能**
- 请确保以下文件存在于项目根目录：
  ```bash
  # 检查VAPORCONE核心文件是否存在
  ls ../VC_BC01_constant.py     # 核心配置文件
  ls ../VC_BC02_baseUtils.py    # 基础工具模块
  ls ../VC_BC03_fetchConfig.py  # 配置获取模块
  ls ../VC_OP00_checkConfig.py  # 配置检查脚本
  ls ../VC_OP01_cleaning.py     # 数据清洗脚本
  # ... 其他OP和PS脚本
  ```
- 🛠️ **如果文件缺失**：请从VAPORCONE项目中获取完整的核心模块文件

#### 2. **前端无法连接后端**
```
错误信息: Network Error 或 CORS 错误
```

**解决方案：**
- 检查后端API服务器是否运行在端口5000
- 运行测试脚本验证API：`python test_api.py`
- 检查防火墙是否阻止端口5000

#### 3. **数据库连接失败**
```
错误信息: Can't connect to MySQL server
```

**解决方案：**
- ⚠️ **这是系统错误！** 数据库连接是系统正常工作的必要条件
- 🔧 **必须建立数据库连接才能使用系统功能**
- **检查步骤**：
  1. **MySQL服务状态**: 确保MySQL服务正在运行
  2. **连接参数**: 验证 `VC_BC01_constant.py` 中的数据库连接参数
  3. **用户权限**: 确认数据库用户具有足够的读写权限
  4. **网络连接**: 检查数据库服务器的网络可达性
  5. **数据库存在**: 确认目标数据库已创建
- 🛠️ **配置示例**：
  ```python
  # VC_BC01_constant.py 中的配置
  DB_HOST = '127.0.0.1'
  DB_USER = 'root' 
  DB_PASSWORD = 'your_password'
  DB_DATABASE = 'VC-DataMigration_2.0'
  ```

#### 4. **端口被占用**
```
错误信息: Port 3000/5000 is already in use
```

**解决方案：**
```bash
# Windows - 查找并结束占用端口的进程
netstat -ano | findstr :3000
netstat -ano | findstr :5000
taskkill /pid <PID> /f

# 或者使用不同端口启动
npm start -- --port 3001
```

#### 5. **npm 依赖安装失败**
```
错误信息: npm install 失败
```

**解决方案：**
```bash
# 清理缓存并重新安装
npm cache clean --force
rm -rf node_modules package-lock.json
npm install

# 或使用 yarn
yarn install
```

### ⚡ 启动检查清单

启动前请确认：

**🔧 基础环境**
- [ ] Node.js 16.0+ 已安装 (`node --version`)
- [ ] Python 3.8+ 已安装 (`python --version`)
- [ ] 端口 3000 和 5000 未被占用
- [ ] 网络连接正常

**🛠️ VAPORCONE核心组件 (必需)**
- [ ] **VC_BC01_constant.py** - 核心配置文件
- [ ] **VC_BC02_baseUtils.py** - 基础工具模块
- [ ] **VC_BC03_fetchConfig.py** - 配置获取模块
- [ ] **所有处理脚本** (VC_OP00-OP05, VC_PS01-PS02)

**🗄️ 数据库配置 (必需)**
- [ ] **MySQL 8.0+ 服务正在运行**
- [ ] **数据库连接参数正确配置**
- [ ] **数据库用户权限充足**
- [ ] **目标数据库已创建**

**📊 数据和配置文件 (必需)**
- [ ] **研究配置文件** (`CIRCULATE_OperationConf.xlsx` 等) 存在
- [ ] **原始数据文件** 位于正确的目录下
- [ ] **studySpecific目录结构** 完整

⚠️ **注意**: 以上所有项目都是系统正常运行的必要条件，缺少任何一项都会导致功能异常

### 📋 运行模式说明

系统**完全采用真实数据运行模式**：

✅ **生产环境模式 (唯一支持的模式)**
   - ✅ VAPORCONE核心模块必须完整可用
   - ✅ 真实数据库连接必须正常建立
   - ✅ 所有数据和配置文件必须准备就绪
   - ✅ 研究配置文件 (*.xlsx) 必须存在
   - ✅ 原始数据文件必须位于正确目录
   - ✅ 系统提供完整的数据处理功能

❌ **不支持的模式**
   - ❌ 演示模式
   - ❌ 模拟数据模式
   - ❌ 离线模式
   - ❌ 测试数据模式

⚠️ **重要提醒**: 任何核心组件缺失都将导致系统无法启动或功能异常

### 📞 获取帮助

如果遇到其他问题：

1. **查看日志**
   - 前端：浏览器开发者工具控制台
   - 后端：终端输出

2. **运行诊断**
   ```bash
   .\test_stop.bat      # 检查服务运行状态
   python test_api.py   # 测试API接口 (如果存在)
   ```

3. **重新启动**
   ```bash
   # 停止所有服务
   .\stop_enhanced.bat
   
   # 重新运行启动脚本
   .\start.bat
   ```

4. **脚本功能说明**
   - `start.bat`: 一键启动完整系统
   - `stop.bat`: 基础版停止脚本
   - `stop_enhanced.bat`: 增强版停止脚本 (推荐)
   - `test_stop.bat`: 系统状态检查和快速操作

5. **虚拟环境策略说明**
   
   启动脚本采用智能虚拟环境检测：
   
   **🏆 最佳实践（您当前的配置）：**
   - ✅ **根目录虚拟环境** (`SDTM/.venv`)
   - ✅ **统一依赖管理** (`SDTM/requirements.txt`)
   - ✅ **整个VAPORCONE生态共享环境**
   
   **🔄 自动适配：**
   - 🔍 **优先检测**: 根目录虚拟环境
   - 🔍 **备选方案**: backend目录虚拟环境  
   - 🔍 **兜底策略**: 自动创建backend虚拟环境
   
   **💡 优势：**
   - 避免重复安装相同依赖包
   - 保持VAPORCONE核心模块和Web API环境一致
   - 简化依赖管理和版本控制

## 开发说明

### 添加新组件
1. 在 `src/components/` 目录创建新组件文件
2. 在 `App.js` 中导入并注册组件
3. 添加相应的路由和菜单项

### 添加新API接口
1. 在 `backend/app.py` 中添加新的路由
2. 在前端组件中调用API接口
3. 更新API文档

### 自定义样式
- 全局样式：编辑 `src/App.css`
- 组件样式：使用Ant Design的主题定制
- 响应式设计：使用Ant Design的Grid系统

## 许可证

本项目为内部使用，请遵守公司相关规定。

## 联系方式

如有问题或建议，请联系开发团队。
