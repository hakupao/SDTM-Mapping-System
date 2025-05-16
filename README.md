# SDTM数据迁移工具

这是一个专门用于临床试验数据标准化处理的Python应用程序，主要用于将原始临床试验数据转换为符合CDISC SDTM标准的格式。

## 项目文档

详细文档请参考`docs`目录：

- [项目概述](docs/project_overview.md) - 项目架构与功能详解
- [安装与使用指南](docs/installation_guide.md) - 详细的安装和使用步骤
- [配置参考](docs/configuration_reference.md) - 配置文件参数说明
- [贡献指南](docs/contributing.md) - 如何参与项目开发

## 环境要求

- Python 3.8 或更高版本
- MySQL数据库
- pip (Python包管理器)

## 快速开始

### 安装步骤

1. 克隆或下载此项目到本地

   ```bash
   git clone https://github.com/your-username/SDTM.git
   cd SDTM
   ```

2. 安装依赖包：

   ```bash
   pip install -r requirements.txt
   ```

### 配置说明

在使用此工具之前，请确保：

1. 在 `VC_BC01_constant.py` 中配置正确的数据库连接信息：
   - DB_HOST
   - DB_USER
   - DB_PASSWORD
   - DB_DATABASE

2. 确保所有必要的文件路径都已正确配置：
   - ROOT_PATH
   - RAW_DATA_ROOT_PATH
   - 其他相关路径

### 基本使用流程

1. 设置研究特定配置
   ```bash
   # 创建研究目录
   mkdir -p studySpecific/YOUR_STUDY_ID
   # 准备配置文件 YOUR_STUDY_ID_OperationConf.xlsx
   ```

2. 运行数据处理步骤
   ```bash
   python VC_OP01_cleaning.py      # 数据清洗
   python VC_OP02_insertCodeList.py # 代码列表插入
   python VC_OP03_insertMetadata.py # 元数据插入
   python VC_OP04_format.py        # 格式转换
   python VC_OP05_mapping.py       # SDTM映射
   ```

## 项目结构

```
SDTM/
├── studySpecific/ - 研究特定的配置和数据
│   └── [研究ID]/ - 各研究的专用目录
├── docs/ - 项目文档
├── VC_BC*.py - 基础组件文件
├── VC_OP*.py - 操作模块文件
└── VC_PS*.py - 处理脚本文件
```

## 注意事项

- 请确保有足够的磁盘空间
- 确保数据库连接正常
- 建议在运行前备份重要数据

## 常见问题

如果安装依赖时遇到问题，可以尝试：

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --no-cache-dir
   ```

## 许可证

[添加许可证信息]

## 联系方式

[添加联系方式]
