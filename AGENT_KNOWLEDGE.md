# VAPORCONE 项目 Agent 知识库

本文档为 AI Agent 提供项目快速参考，帮助快速理解项目结构、模块职责和关键信息，无需每次都读取整个项目。

## 1. 项目概览

### 1.1 项目目的
VAPORCONE 是一个临床试验数据处理系统，将原始临床试验数据转换为符合 CDISC SDTM 标准的数据格式，并生成可用于监管提交的 M5 数据包。

### 1.2 核心工作流程
```
原始数据 → 数据清洗 → 代码列表插入 → 元数据插入 → 数据格式化 → 数据映射 → SDTM数据集 → 生成CSV → 生成JSON数据包
```

### 1.3 技术栈
- **Python**: 3.11.0
- **数据库**: MySQL (mysql-connector-python 9.4.0)
- **数据处理**: pandas 2.3.1, numpy 2.2.6
- **Excel处理**: openpyxl 3.1.5
- **日期处理**: python-dateutil 2.9.0

## 2. 模块架构说明

### 2.1 模块依赖关系

```
VC_BC01 (常量) 
  ↓
VC_BC02 (工具) ← VC_BC03 (配置读取)
  ↓
VC_BC04 (操作调度) → VC_BC06 (操作实现)
  ↓                    ↑
VC_BC05 (研究特定函数) ┘
  ↓
VC_OP01-05 (操作模块)
  ↓
VC_PS01-02 (后处理模块)
```

### 2.2 基础模块 (BC - Base Components)

#### VC_BC01_constant.py
- **职责**: 全局常量定义和配置加载
- **关键内容**:
  - 加载 `project.local.json` 配置
  - 数据库连接参数 (DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE)
  - SDTM标准字段定义 (STANDARD_FIELDS)
  - 文件路径常量 (CLEANINGSTEP_PATH, FORMAT_PATH, SDTMDATASET_PATH等)
  - 操作类型常量 (OPERTYPE_DEF, OPERTYPE_FIX, OPERTYPE_FLG等)
- **关键函数**: `_load_project_config()`

#### VC_BC02_baseUtils.py
- **职责**: 基础工具函数和数据库管理
- **关键函数**:
  - `create_logger()`: 创建日志记录器
  - `create_directory()`: 创建带时间戳的目录
  - `find_latest_timestamped_path()`: 查找最新时间戳文件夹
  - `make_format_value()`: 格式化字段值（日期处理）
  - `DatabaseManager`: 数据库管理类
    - `connect()`: 连接数据库
    - `create_codelist_table()`: 创建代码列表表
    - `create_metadata_table()`: 创建元数据表
    - `create_transdata_view()`: 创建转换数据视图
    - `create_performance_indexes()`: 创建性能优化索引

#### VC_BC03_fetchConfig.py
- **职责**: 从Excel配置文件读取配置信息
- **关键函数**:
  - `getSheetSetting()`: 读取工作表设置
  - `getCaseDict()`: 读取病例字典 (SUBJID → USUBJID)
  - `getFileDict()`: 读取文件配置
  - `getProcess()`: 读取字段处理配置
  - `getCodeListInfo()`: 读取代码列表
  - `getMapping()`: 读取映射配置
  - `getDomainsSetting()`: 读取域设置
  - `getSites()`: 读取站点信息
  - `getFormatDataset()`: 读取格式化数据集
- **异常类**: `MappingConfigurationError`

#### VC_BC04_operateType.py
- **职责**: 数据类型操作调度和优化
- **关键函数**:
  - `singleTable()`: 单表操作
  - `tableJoinType1()`: 多表联合操作
  - `precompute_mapping_rules()`: 预计算映射规则（性能优化）
  - `ultra_fast_sequence_generation()`: 超高效序号生成
  - `vectorized_field_mapping()`: 向量化字段映射
  - `get_cached_csv()`: CSV缓存读取

#### VC_BC05_studyFunctions.py
- **位置**: `studySpecific/[STUDY_ID]/VC_BC05_studyFunctions.py`
- **职责**: 研究特定的数据处理函数
- **关键函数** (CIRCULATE研究示例):
  - `leftjoin()`: 左连接操作
  - `tableMerge()`: 表合并操作
  - 其他研究特定的数据处理函数

#### VC_BC06_operateTypeFunctions.py
- **职责**: 操作类型具体实现函数
- **支持的操作类型**:
  - `opertype_DEF`: 定义固定值
  - `opertype_FIX`: 固定字段映射
  - `opertype_FLG`: 标志映射
  - `opertype_IIF`: 条件选择
  - `opertype_COB`: 字段组合
  - `opertype_CDL`: 代码列表映射
  - `opertype_PRF`: 前缀添加
  - `opertype_SEL`: 选择性映射
  - `opertype_CAL`: 数学运算计算
- **关键函数**: `get_opertype_function()`: 获取操作类型函数

### 2.3 操作模块 (OP - Operations)

#### VC_OP01_cleaning.py
- **职责**: 原始数据清洗
- **处理流程**:
  1. 读取Excel配置
  2. 筛选需要迁移的数据
  3. 分离迁移和非迁移的列
  4. 处理空白行和无效数据
  5. 输出清洗后的数据文件 (C_, DC_, DR_ 前缀)
- **输出**: `02_Cleaning/cleaning_dataset-[timestamp]/`

#### VC_OP02_insertCodeList.py
- **职责**: 代码列表数据库插入
- **处理流程**:
  1. 读取配置文件中的代码列表
  2. 创建代码列表数据库表
  3. 填充代码列表数据
- **数据库表**: `CODELIST_TABLE_NAME` (从project.local.json读取)

#### VC_OP03_insertMetadata.py
- **职责**: 元数据插入到数据库
- **处理流程**:
  1. 读取字段映射配置
  2. 创建元数据表
  3. 填充元数据
- **数据库表**: `METADATA_TABLE_NAME` (从project.local.json读取)

#### VC_OP04_format.py
- **职责**: 数据格式化处理
- **处理流程**:
  1. 创建转换数据视图
  2. 处理检查文件 (CHK)
  3. 应用数据类型转换
  4. 格式化日期时间字段
  5. 处理特殊值和编码
  6. 生成格式化数据文件
- **性能优化**:
  - 数据库索引优化
  - 查询重构优化
  - 临时表物化
  - 性能监控
- **输出**: `03_Format/format_dataset-[timestamp]/`

#### VC_OP05_mapping.py
- **职责**: 数据字段映射为SDTM格式
- **处理流程**:
  1. 读取映射配置
  2. 执行字段映射操作
  3. 处理序列号生成
  4. 生成SDTM数据集
- **性能优化**:
  - 并行Domain处理
  - 序号算法改进
  - 预排序优化
- **输出**: `04_SDTM/sdtm_dataset-[timestamp]/`

#### VC_OP06_combine.py (实验性)
- **职责**: 数据合并
- **位置**: `experiment/combine_test/VC_OP06_combine.py`

### 2.4 后处理模块 (PS - Post Processing)

#### VC_PS01_makeInputCSV.py
- **职责**: 生成输入CSV文件
- **处理流程**:
  1. 分离标准字段和补充字段
  2. 生成主数据文件
  3. 生成补充数据文件 (SUPP)
  4. 处理站点代码转换
- **输出**: `05_Inputfile/*.csv`

#### VC_PS02_csv2json.py
- **职责**: CSV转JSON数据包
- **处理流程**:
  1. 读取输入CSV文件
  2. 构建JSON数据结构
  3. 生成M5格式的数据包
  4. 创建ZIP压缩文件
- **输出**: `06_Inputpackage/m5.zip`

## 3. 文件快速索引

### 3.1 按功能分类

#### 配置和常量
- `VC_BC01_constant.py`: 全局常量定义
- `VC_BC03_fetchConfig.py`: Excel配置读取
- `project.local.json`: 本地项目配置
- `requirements.txt`: Python依赖

#### 工具和基础功能
- `VC_BC02_baseUtils.py`: 基础工具函数、数据库管理
- `VC_BC04_operateType.py`: 操作类型调度
- `VC_BC06_operateTypeFunctions.py`: 操作类型实现

#### 研究特定
- `studySpecific/[STUDY_ID]/VC_BC05_studyFunctions.py`: 研究特定函数
- `studySpecific/[STUDY_ID]/[STUDY_ID]_OperationConf.xlsx`: 研究配置文件

#### 数据处理流程
- `VC_OP01_cleaning.py`: 数据清洗
- `VC_OP02_insertCodeList.py`: 代码列表插入
- `VC_OP03_insertMetadata.py`: 元数据插入
- `VC_OP04_format.py`: 数据格式化
- `VC_OP05_mapping.py`: 数据映射

#### 后处理
- `VC_PS01_makeInputCSV.py`: 生成CSV
- `VC_PS02_csv2json.py`: 生成JSON数据包

### 3.2 关键类和函数位置

| 功能 | 文件 | 类/函数 |
|------|------|---------|
| 数据库管理 | VC_BC02_baseUtils.py | `DatabaseManager` |
| 日志记录 | VC_BC02_baseUtils.py | `create_logger()` |
| 配置读取 | VC_BC03_fetchConfig.py | `get*()` 系列函数 |
| 操作类型调度 | VC_BC04_operateType.py | `vectorized_field_mapping()` |
| 操作类型实现 | VC_BC06_operateTypeFunctions.py | `opertype_*()` 系列函数 |
| 序号生成 | VC_BC04_operateType.py | `ultra_fast_sequence_generation()` |
| 研究特定函数 | studySpecific/[STUDY_ID]/VC_BC05_studyFunctions.py | 研究相关函数 |

## 4. 配置说明

### 4.1 project.local.json 结构

```json
{
  "STUDY_ID": "CIRCULATE",                    // 研究ID
  "CODELIST_TABLE_NAME": "VC05_CIRCULATE_CODELIST",  // 代码列表表名
  "METADATA_TABLE_NAME": "VC05_CIRCULATE_METADATA",  // 元数据表名
  "TRANSDATA_VIEW_NAME": "VC05_CIRCULATE_TRANSDATA", // 转换数据视图名
  "M5_PROJECT_NAME": "[UAT]CIRCULATE",        // M5项目名称
  "ROOT_PATH": "C:\\Local\\iTMS\\SDTM_CIRCULATE",    // 项目根路径
  "RAW_DATA_ROOT_PATH": "C:\\Local\\iTMS\\SDTM_CIRCULATE\\studySpecific\\CIRCULATE\\20251114_CSV"  // 原始数据路径
}
```

### 4.2 数据库配置

在 `VC_BC01_constant.py` 中定义：
```python
DB_HOST = '127.0.0.1'
DB_USER = 'root'
DB_PASSWORD = 'root'
DB_DATABASE = 'VC-DataMigration_2.0'
```

### 4.3 Excel配置文件结构

配置文件位于: `studySpecific/[STUDY_ID]/[STUDY_ID]_OperationConf.xlsx`

必需的工作表:
- **SheetSetting**: 工作表配置
- **Patients**: 病例信息
- **Files**: 文件配置
- **Process**: 字段处理配置
- **CodeList**: 代码列表
- **Mapping**: 字段映射配置
- **DomainsSetting**: 域设置
- **Sites**: 站点信息
- **Refactoring**: 重构配置（可选）
- **Combine**: 合并配置（可选）

### 4.4 环境变量

- `PROJECT_CONFIG_PATH`: 可选，指定project.local.json的路径

## 5. 常见任务指南

### 5.1 如何添加新的操作类型

1. 在 `VC_BC06_operateTypeFunctions.py` 中添加新函数:
   ```python
   def opertype_NEW(result_df, be_converted_df, standard_field, fieldname_cycle, parameter_cycle, **kwargs):
       # 实现逻辑
       return result_df, continue_flags
   ```

2. 在 `get_opertype_function()` 函数中注册:
   ```python
   OPER_TYPE_FUNCTIONS = {
       'DEF': opertype_DEF,
       # ...
       'NEW': opertype_NEW,  # 添加新操作类型
   }
   ```

3. 在 `VC_BC01_constant.py` 中添加常量:
   ```python
   OPERTYPE_NEW = 'NEW'
   ```

### 5.2 如何添加新的研究特定函数

1. 在 `studySpecific/[STUDY_ID]/VC_BC05_studyFunctions.py` 中添加函数
2. 函数会被 `VC_BC04_operateType.py` 自动导入（通过 `sys.path.append(SPECIFIC_PATH)`）
3. 在Excel配置的Refactoring或Mapping工作表中引用函数名

### 5.3 如何调试性能问题

1. **启用性能监控**:
   - 在 `VC_OP04_format.py` 中设置 `ENABLE_PERFORMANCE_MONITORING = True`
   - 查看详细的耗时统计

2. **数据库查询优化**:
   - 检查索引是否创建: `DatabaseManager.create_performance_indexes()`
   - 使用 `analyze_query_performance()` 分析查询计划

3. **启用EXPLAIN分析**:
   - 在 `VC_OP04_format.py` 中设置 `ENABLE_EXPLAIN_ANALYSIS = True`

4. **临时表优化**:
   - 启用 `USE_TEMP_TABLES = True` 使用文件级临时表
   - 启用 `ENABLE_WORK_TABLE_PERSISTENCE = True` 保留工作表以供重用

### 5.4 如何添加新的研究

1. 创建研究目录: `studySpecific/[NEW_STUDY_ID]/`
2. 创建配置文件: `[NEW_STUDY_ID]_OperationConf.xlsx`
3. 创建研究特定函数文件: `VC_BC05_studyFunctions.py`
4. 更新 `project.local.json` 配置
5. 准备原始数据目录

### 5.5 如何处理错误

1. **MappingConfigurationError**: Excel配置错误，检查Mapping工作表
2. **数据库连接失败**: 检查数据库服务和连接参数
3. **文件路径错误**: 检查 `project.local.json` 中的路径配置
4. **字段映射错误**: 检查Excel配置中的字段名和操作类型

## 6. 代码模式

### 6.1 命名规范

- **文件命名**: `VC_[模块类型][序号]_[功能].py`
  - `VC_BC##_`: 基础组件模块
  - `VC_OP##_`: 操作处理模块
  - `VC_PS##_`: 后处理模块

- **函数命名**: 
  - 操作类型函数: `opertype_[TYPE]()`
  - 配置读取函数: `get[ConfigName]()`
  - 工具函数: 小写+下划线

- **常量命名**: 全大写+下划线
  - `STUDY_ID`, `DB_HOST`, `OPERTYPE_DEF`

### 6.2 代码组织模式

1. **导入顺序**:
   ```python
   # 标准库
   import os
   import sys
   
   # 第三方库
   import pandas
   import numpy
   
   # 项目内部模块
   from VC_BC01_constant import *
   from VC_BC02_baseUtils import *
   ```

2. **模块结构**:
   ```python
   """
   模块文档字符串
   """
   # 导入
   # 常量定义
   # 函数定义
   # 类定义
   # main函数（如果可执行）
   ```

3. **错误处理模式**:
   - 使用 `MappingConfigurationError` 处理配置错误
   - 使用日志记录器记录错误
   - 提供详细的错误信息（包括Excel行号）

### 6.3 最佳实践

1. **性能优化**:
   - 使用向量化操作（pandas/numpy）
   - 预计算映射规则
   - 使用CSV缓存
   - 创建数据库索引

2. **代码复用**:
   - 使用 `VC_BC02_baseUtils.py` 中的工具函数
   - 研究特定函数放在 `VC_BC05_studyFunctions.py`

3. **配置管理**:
   - 使用 `project.local.json` 管理项目配置
   - 使用Excel文件管理数据处理规则

4. **日志记录**:
   - 使用 `create_logger()` 创建日志记录器
   - 记录关键步骤和错误信息

5. **时间戳管理**:
   - 使用 `create_directory()` 创建带时间戳的目录
   - 使用 `find_latest_timestamped_path()` 查找最新输出

## 7. 数据流程详解

### 7.1 数据流转路径

```
原始CSV文件 (RAW_DATA_ROOT_PATH)
  ↓ [VC_OP01_cleaning.py]
清洗数据 (02_Cleaning/cleaning_dataset-[timestamp]/)
  ↓ [VC_OP02_insertCodeList.py]
代码列表表 (数据库)
  ↓ [VC_OP03_insertMetadata.py]
元数据表 (数据库)
  ↓ [VC_OP04_format.py]
格式化数据 (03_Format/format_dataset-[timestamp]/)
  ↓ [VC_OP05_mapping.py]
SDTM数据集 (04_SDTM/sdtm_dataset-[timestamp]/)
  ↓ [VC_PS01_makeInputCSV.py]
输入CSV文件 (05_Inputfile/*.csv)
  ↓ [VC_PS02_csv2json.py]
M5数据包 (06_Inputpackage/m5.zip)
```

### 7.2 数据库表结构

#### 代码列表表 (CODELIST_TABLE_NAME)
- `CODELISTID`: 代码列表ID
- `CODE`: 代码值
- `VALUE_RAW`: 原始值
- `VALUE_EN`: 英文值
- `VALUE_SDTM`: SDTM值

#### 元数据表 (METADATA_TABLE_NAME)
- `No`: 序号
- `FILENAME`: 文件名
- `ROWNUM`: 行号
- `USUBJID`: 受试者唯一ID
- `SUBJID`: 受试者ID
- `FIELDLBL`: 字段标签
- `FIELDID`: 字段ID
- `METAVAL`: 元数据值
- `FORMVAL`: 格式化值
- `DATETYPE`: 日期类型标志
- `CODELISTID`: 代码列表ID
- `CHKFIELDID`: 检查字段ID

#### 转换数据视图 (TRANSDATA_VIEW_NAME)
- 基于元数据表和代码列表表的LEFT JOIN
- 包含 `TRANSVAL` (转换值) 和 `SDTMVAL` (SDTM值)

## 8. 快速参考

### 8.1 常用命令

```bash
# 完整处理流程
python VC_OP01_cleaning.py
python VC_OP02_insertCodeList.py
python VC_OP03_insertMetadata.py
python VC_OP04_format.py
python VC_OP05_mapping.py
python VC_PS01_makeInputCSV.py
python VC_PS02_csv2json.py
```

### 8.2 关键路径变量

- `ROOT_PATH`: 项目根路径
- `SPECIFIC_PATH`: 研究特定路径 (`ROOT_PATH/studySpecific/[STUDY_ID]`)
- `CLEANINGSTEP_PATH`: 清洗步骤路径
- `FORMAT_PATH`: 格式化路径
- `SDTMDATASET_PATH`: SDTM数据集路径
- `INPUTFILE_PATH`: 输入文件路径
- `INPUTPACKAGE_PATH`: 输入包路径

### 8.3 标准字段前缀

- `C_`: 清洗后的迁移数据
- `DC_`: 删除的列数据
- `DR_`: 删除的行数据
- `F_`: 格式化后的数据
- `SUPP`: 补充字段前缀

### 8.4 操作类型速查

| 操作类型 | 说明 | 参数 |
|---------|------|------|
| DEF | 定义固定值 | 固定值 |
| FIX | 固定字段映射 | 源字段名 |
| FLG | 标志映射 | 条件表达式 |
| IIF | 条件选择 | 条件:值对 |
| COB | 字段组合 | 字段列表 |
| CDL | 代码列表映射 | 代码列表ID |
| PRF | 前缀添加 | 前缀值 |
| SEL | 选择性映射 | 条件:字段 |
| CAL | 数学运算 | 运算表达式 |

---

**最后更新**: 2025年
**维护者**: 项目开发团队

