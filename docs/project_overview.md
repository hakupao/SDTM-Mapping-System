# SDTM数据迁移工具 - 项目概述

## 项目简介

SDTM（Study Data Tabulation Model）数据迁移工具用于将原始临床试验数据转换为符合 CDISC SDTM 标准的结构化数据，支持监管提交与分析使用。工具覆盖从原始数据清洗、元数据抽取、格式化聚合、映射转换，到输入包（CSV/JSON/Zip）生成的完整链路。

## 项目架构

项目采用模块化设计：

### 基础模块（Base Components）
- `VC_BC01_constant.py`：全局常量、路径、数据库、研究ID、表名、时间变量定义
- `VC_BC02_baseUtils.py`：通用工具（日志、目录创建、日期格式化、DB 管理等）
- `VC_BC03_fetchConfig.py`：从 Excel 配置读取 SheetSetting、Patients、Files、Process、CodeList、Mapping、DomainsSetting、Combine、Sites 等
- `VC_BC04_operateType.py`：操作类型实现（单表/联合、COB/FLG/IIF/CDL/SEL/PRF 等）
- `studySpecific/<STUDY>/VC_BC05_studyFunctions.py`：研究特定函数（如 `make_DMFrame`、`process_*`、`get_*`、`tableMerge`）

### 操作模块（Operation Modules）
- `VC_OP00_checkConfig.py`：配置静态检查（必填项与基本一致性）
- `VC_OP01_cleaning.py`：清洗原始 CSV，生成 `02_Cleaning/cleaning_dataset` 与未迁移列/行
- `VC_OP02_insertCodeList.py`：创建并填充代码表
- `VC_OP03_insertMetadata.py`：将清洗后数据写入元数据表（日期类型规范化）
- `VC_OP04_format.py`：创建转换视图与中间产物 `F-*.csv`、检查型 `F-<name>[chk].csv`
- `VC_OP05_mapping.py`：依据 Mapping 生成 SDTM 域 CSV（按域排序并生成序列号）
- `VC_PS01_makeInputCSV.py`：从 SDTM 生成输入 CSV 和 `SUPP*.csv`
- `VC_PS02_csv2json.py`：打包为 `m5/m5/datasets/<M5_PROJECT_NAME>/tabulations` 并生成 `m5.zip`

### 目录结构（关键产物）

- `studySpecific/<STUDY>/02_Cleaning/`
  - `cleaning_dataset/`：清洗后 `C-*.csv`
  - `cleaning_dataset/deletedCols/`：未迁移列 `DC-*.csv`
  - `cleaning_dataset/deletedRows/`：未迁移行 `DR-*.csv`
- `studySpecific/<STUDY>/03_Format/format_dataset/`：格式化产物 `F-*.csv` 与检查型 `F-<name>[chk].csv`
- `studySpecific/<STUDY>/04_SDTM/sdtm_dataset[-时间戳]/`：SDTM 域 CSV
- `studySpecific/<STUDY>/05_Inputfile/`：输入 CSV 与 `SUPP*.csv`
- `studySpecific/<STUDY>/06_Inputpackage/`：`m5/` 目录与 `m5.zip`

## 数据流程（端到端）

1. 清洗（Cleaning）
   - 从 OperationConf.xlsx 读取 `Patients/Files/Process`
   - 定位原始 CSV（精确匹配优先，其次包含匹配）
   - 过滤与字段拆分，输出 `C-*.csv`、`DC-*.csv`、`DR-*.csv`
   - 若定义 `sort_csv_data`，按文件类型进行二级排序
2. 代码表（Insert CodeList）
   - 建表并增量插入（存在则跳过）
3. 元数据（Insert Metadata）
   - 自动判定日期字段（变量名末尾 `DTC`/TIME_VARIABLE/补充时间标志）
   - 规范日期：支持 `YYYY`/`YYYY-MM`/`YYYY-MM-DD` 与 `9999/99` 占位
4. 格式化（Format）
   - 生成数据库视图，用于 TRANSVAL/SDTMVAL 聚合
   - 输出中间产物 `F-*.csv` 与检查型 `F-<file>[<chk>].csv`
5. 映射（Mapping）
   - 依据 Mapping→DEFINITION/MERGERULE、`OPERTYPE`、`NDKEY` 去重保留
   - 根据 `DomainsSetting` 排序并生成序列号
   - 输出至 `sdtm_dataset-YYYYMMDDhhmmss/`
6. 导出与打包（Input CSV / JSON / Zip）
   - 非排除域添加 `PAGEID/RECORDID`
   - 生成 `SUPP*.csv` 补充域
   - 依据 `Sites` 替换 `SITEID`
   - 打包为 `m5.zip`

## 适用场景

- 临床试验数据标准化与 SDTM 产出
- 监管报送数据准备
- 多源临床数据整合与统一
- 研究特定（Study-specific）规则与多域映射

Further verification is required. 