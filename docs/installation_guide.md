# SDTM数据迁移工具 - 安装与使用指南

## 环境要求

- Python 3.8 或更高版本
- MySQL数据库
- Windows或Linux操作系统

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/hakupao/SDTM-Mapping-System.git
cd SDTM-Mapping-System
```

### 2. 创建虚拟环境 (推荐)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. 安装依赖包

```bash
pip install -r requirements.txt
```

## 数据库配置

在使用工具前，需要在`VC_BC01_constant.py`中配置数据库连接参数：

```python
DB_HOST = '127.0.0.1'           # 数据库主机地址
DB_USER = 'your_username'       # 数据库用户名
DB_PASSWORD = 'your_password'   # 数据库密码
DB_DATABASE = 'your_database'   # 数据库名称
```

## 研究配置

### 1. 创建研究特定目录

```bash
mkdir -p studySpecific/YOUR_STUDY_ID
```

### 2. 准备配置文件

在研究目录中创建Excel配置文件`YOUR_STUDY_ID_OperationConf.xlsx`，包含以下工作表：
- SheetSetting: 工作表设置
- Files: 文件列表
- Process: 处理逻辑
- CodeList: 代码列表
- Mapping: 映射规则
- 其他必要工作表

### 3. 修改常量文件

在`VC_BC01_constant.py`中设置研究ID和相关表名：

```python
STUDY_ID = 'YOUR_STUDY_ID'
CODELIST_TABLE_NAME = 'VC_YOUR_STUDY_ID_CODELIST'
METADATA_TABLE_NAME = 'VC_YOUR_STUDY_ID_METADATA'
TRANSDATA_VIEW_NAME = 'VC_YOUR_STUDY_ID_TRANSDATA'
```

## 使用流程

### 1. 数据准备

将原始数据文件放置在适当的位置 (例如：studySpecific/YOUR_STUDY_ID/01_RawData/)

### 2. 数据清洗

```bash
python VC_OP01_cleaning.py
```

### 3. 代码列表插入

```bash
python VC_OP02_insertCodeList.py
```

### 4. 元数据插入

```bash
python VC_OP03_insertMetadata.py
```

### 5. 格式转换

```bash
python VC_OP04_format.py
```

### 6. SDTM映射

```bash
python VC_OP05_mapping.py
```

## 故障排除

### 常见问题

1. **数据库连接错误**
   - 确认数据库服务正在运行
   - 验证连接参数正确无误
   - 确保用户有适当的权限

2. **配置文件问题**
   - 检查Excel工作表名称是否正确
   - 确保必要的列存在且格式正确

3. **Python依赖问题**
   - 尝试更新pip: `pip install --upgrade pip`
   - 使用`--no-cache-dir`选项: `pip install -r requirements.txt --no-cache-dir`

### 日志查看

程序执行时会生成日志文件，可通过查看日志文件了解详细执行情况：

```
studySpecific/YOUR_STUDY_ID/log_file.log
``` 