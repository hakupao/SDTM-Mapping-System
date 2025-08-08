# SDTM数据迁移工具 - 安装与使用指南

## 环境要求

- Python 3.8+（建议 3.10/3.11）
- MySQL 8+
- Windows 10/11（已验证）或 Linux/Mac
- 建议启用虚拟环境（venv/conda）

## 获取代码

```bash
# HTTPS（示例）
git clone https://github.com/hakupao/SDTM-Mapping-System.git
cd SDTM-Mapping-System
```

Windows PowerShell 提示：若在 PowerShell 执行管道命令遇到兼容性问题，请去掉 `| cat` 之类的管道，或改用 Git Bash。

## 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

## 安装依赖

```bash
pip install -r requirements.txt
```

可选：若需开发规范（PEP8/Black/Flake8/isort），可另行安装：
```bash
pip install black isort flake8
```

## 数据库配置

在 `VC_BC01_constant.py` 中设置数据库与路径（示例）：
```python
DB_HOST = '127.0.0.1'
DB_USER = 'root'
DB_PASSWORD = 'root'
DB_DATABASE = 'VC-DataMigration_2.0'

STUDY_ID = 'CIRCULATE'
ROOT_PATH = r'C:\Local\iTMS\SDTM'
SPECIFIC_PATH = os.path.join(ROOT_PATH, 'studySpecific', STUDY_ID)
```

注意：请确保 MySQL 可访问、字符集使用 `utf8mb4`。

## 准备研究配置

1) 在 `studySpecific/` 下建立研究目录并放置配置 Excel：
- `studySpecific/<STUDY_ID>/<STUDY_ID>_OperationConf.xlsx`

2) 在 Excel 配置中维护：
- `SheetSetting/Patients/Files/Process/CodeList/Mapping/DomainsSetting` 等

3) 若有研究特定函数，请在：
- `studySpecific/<STUDY_ID>/VC_BC05_studyFunctions.py`
中实现（如 `make_DMFrame`、`process_*`、`get_*`、`tableMerge`）。

## 端到端运行顺序

以下命令需在仓库根目录执行，且已激活虚拟环境并配置好数据库：

```bash
# 0.（可选）检查配置完整性
python VC_OP00_checkConfig.py

# 1. 清洗原始数据（输出 C-*.csv / DC-*.csv / DR-*.csv）
python VC_OP01_cleaning.py

# 2. 写入代码表（重复记录自动跳过）
python VC_OP02_insertCodeList.py

# 3. 写入元数据表（日期规范化、TRANSVAL/SDTMVAL 准备）
python VC_OP03_insertMetadata.py

# 4. 生成格式化中间产物 F-*.csv（含检查型）
python VC_OP04_format.py

# 5. 映射到 SDTM 域 CSV（自动序列号，输出到带时间戳目录）
python VC_OP05_mapping.py

# 6. 生成输入 CSV 与 SUPP*.csv
python VC_PS01_makeInputCSV.py

# 7. 生成 JSON 包并打包为 m5.zip
python VC_PS02_csv2json.py
```

产物位置（以 `CIRCULATE` 为例）：
- `studySpecific/CIRCULATE/02_Cleaning/cleaning_dataset/`
- `studySpecific/CIRCULATE/03_Format/format_dataset/`
- `studySpecific/CIRCULATE/04_SDTM/sdtm_dataset[-时间戳]/`
- `studySpecific/CIRCULATE/05_Inputfile/`
- `studySpecific/CIRCULATE/06_Inputpackage/m5.zip`

## 故障排除（Troubleshooting）

- 数据库连接失败：
  - 确认服务运行、账号密码/库名/权限
  - 确认字符集/排序规则为 `utf8mb4`
- CSV 未找到：
  - `Files` 的 `FILENAME` 会先尝试精确匹配 `<name>.csv`，找不到才做包含匹配；检查原始文件名
- 日期解析异常：
  - 工具支持 `YYYY`/`YYYY-MM`/`YYYY-MM-DD`，并处理 `9999/99` 占位；若数据为其他格式，请先在清洗阶段规整
- PowerShell 命令异常：
  - 去掉管道或改用 Git Bash

Further verification is required. 