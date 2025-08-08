# SDTM数据迁移工具

这是一个专门用于临床试验数据标准化处理的Python应用程序，主要用于将原始临床试验数据转换为符合CDISC SDTM标准的格式。

## 项目文档

详细文档请参考`docs`目录：

- [项目概述](docs/project_overview.md) - 项目架构与功能详解
- [安装与使用指南](docs/installation_guide.md) - 详细的安装和使用步骤
- [配置参考](docs/configuration_reference.md) - 配置文件参数说明
- [贡献指南](docs/contributing.md) - 如何参与项目开发

## 环境要求

- Python 3.8 或更高版本（建议 3.10/3.11）
- MySQL 数据库（8+）
- pip（Python 包管理器）
- Windows 10/11 或 Linux/Mac（Windows PowerShell 需避免使用无关管道）

## 快速开始

1. 获取代码
   ```bash
   git clone https://github.com/hakupao/SDTM-Mapping-System.git
   cd SDTM-Mapping-System
   ```

2. 创建并激活虚拟环境（推荐）
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python -m venv venv
   source venv/bin/activate
   ```

3. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

4. 配置数据库与研究参数（示例，按需修改）
   在 `VC_BC01_constant.py` 中：
   ```python
   DB_HOST = '127.0.0.1'
   DB_USER = 'root'
   DB_PASSWORD = 'root'
   DB_DATABASE = 'VC-DataMigration_2.0'

   STUDY_ID = 'CIRCULATE'
   ROOT_PATH = r'C:\Local\iTMS\SDTM'
   SPECIFIC_PATH = os.path.join(ROOT_PATH, 'studySpecific', STUDY_ID)
   ```

5. 准备研究配置
   - 在 `studySpecific/<STUDY_ID>/` 放置 `<STUDY_ID>_OperationConf.xlsx`
   - 如需研究特定处理，编辑 `studySpecific/<STUDY_ID>/VC_BC05_studyFunctions.py`

6. 端到端流程（按顺序执行）
   ```bash
   python VC_OP00_checkConfig.py       # 可选：配置检查
   python VC_OP01_cleaning.py          # 清洗：输出 C-*.csv、DC-*.csv、DR-*.csv
   python VC_OP02_insertCodeList.py    # 代码表写入
   python VC_OP03_insertMetadata.py    # 元数据写入（日期规范化）
   python VC_OP04_format.py            # 格式化：F-*.csv 与检查型 F-<name>[chk].csv
   python VC_OP05_mapping.py           # 映射：输出 SDTM 域 CSV（带时间戳目录）
   python VC_PS01_makeInputCSV.py      # 生成输入 CSV 与 SUPP*.csv
   python VC_PS02_csv2json.py          # 生成 m5 包并压缩为 m5.zip
   ```

## 项目结构（关键路径）

```
SDTM/
├── studySpecific/
│   └── <STUDY_ID>/
│       ├── 02_Cleaning/
│       │   └── cleaning_dataset/       # C-*.csv、deletedCols、deletedRows
│       ├── 03_Format/
│       │   └── format_dataset/         # F-*.csv、检查型 F-<name>[chk].csv
│       ├── 04_SDTM/
│       │   └── sdtm_dataset[-时间戳]/   # 域级 CSV 输出
│       ├── 05_Inputfile/               # 输入 CSV 与 SUPP*.csv
│       └── 06_Inputpackage/            # m5/ 与 m5.zip
├── docs/                               # 项目文档
├── VC_BC*.py                           # 基础组件
├── VC_OP*.py                           # 操作模块
└── VC_PS*.py                           # 处理/打包脚本
```

## 注意事项

- 确保 MySQL 可访问（utf8mb4）且账号有建表/视图权限。
- Windows PowerShell 若执行命令异常，移除不必要的管道或使用 Git Bash。
- 运行前建议备份重要数据。

## 常见问题

如果安装依赖或运行遇到问题，可尝试：
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

## 许可证

[添加许可证信息]

## 联系方式

[添加联系方式]
