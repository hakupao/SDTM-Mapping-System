# 配置参考文档

本文档详细说明 SDTM 数据迁移工具的配置文件结构和参数（OperationConf.xlsx）。

## 配置文件概述（Workbook）

配置文件为 Excel，命名为 `[研究ID]_OperationConf.xlsx`。各工作表用于控制不同阶段：清洗、元数据、格式化、映射、导出等。

主要工作表一览：
- SheetSetting（工作表列配置）
- Patients（病例清单）
- Files（源文件与读取规则）
- Process（字段处理与检查来源）
- CodeList（代码清单与映射）
- Mapping（SDTM 域与变量映射）
- DomainsSetting（可选：域排序键）
- Refactoring（可选：中间产物函数）
- Combine（可选：格式化阶段组合函数）
- Sites（可选：站点映射）
- HumanTrans / EXDETAILS（如项目需要）

---

## SheetSetting

用于定义各工作表的“起始行”和“列名→列序”关系。程序会从首行自左向右探测到空单元格处停止，以计算最大列数。

| 列名 | 数据类型 | 说明 |
|---|---|---|
| SHEETNAME | 文本 | 工作表名称 |
| STARTINGROW | 数字 | 数据起始行（通常为表头下一行） |
| 其余列 | 文本 | 该工作表的字段名；程序据此建立“字段名→列序”映射 |

说明：MAXCOL 由程序内部推导，无需手工维护。

## Patients（病例清单）

提供 SUBJID→USUBJID 的对应关系与是否迁移标记。

| 列名 | 数据类型 | 说明 |
|---|---|---|
| SUBJID | 文本 | 受试者本地 ID |
| USUBJID | 文本 | 统一受试者 ID |
| MIGRATIONFLAG | 文本 | 是否迁移。使用“〇/×”（圆圈/叉）表示；× 或空表示不迁移 |

规则：非“〇”的记录将被跳过；若标记异常会终止执行并提示行信息。

## Files（源文件）

定义原始 CSV 文件的读取规则和过滤逻辑。

| 列名 | 数据类型 | 说明 |
|---|---|---|
| FILENAME | 文本 | 文件名（不含扩展名 .csv） |
| TITLEROW | 数字 | 标题行号（从 1 开始） |
| DATAROW | 数字 | 数据起始行号（从 1 开始） |
| SUBJIDFIELDID | 文本 | 受试者 ID 字段名（用于匹配 Patients） |
| PROCESSINGLOGIC | 文本 | 过滤表达式（可选，Python 表达式，eval 执行） |

读取匹配：优先精确匹配 `${FILENAME}.csv`，若未找到则回退到“包含”匹配。

## Process（字段处理与检查来源）

定义清洗后参与“元数据→格式化”的字段，以及“检查型文件”的数据来源。

核心字段：
- FILENAME：对应 `Files` 的文件名（不含扩展名，可与清洗后 `C-*.csv` 对应）
- FIELDNAME：字段名
- LABEL：字段中文/英文标签
- CODELISTNAME：引用 `CodeList` 的列表标识（支持“_4OTHER”扩展）
- CHKTYPE：检查类型（与“检查型文件”行聚合逻辑相关）
- OTHERDETAILSPROCESS：形如 `其他值:其他说明字段`，用于“其他值”细化映射
- DATAEXTRACTION 及其右侧若干列：用于声明“检查型文件”的字段来源与条件

说明：
- MIGRATIONFLAG 在本表按“〇/×”决定字段是否迁移；× 会落入 `deletedCols` 输出。
- DATAEXTRACTION 行与下一行的多列用于声明检查文件（例如 `MH_A_RC` 之类）的列选择、CASE WHEN 聚合、HAVING 以及与 OTHERDETAILS 的联接；程序会据此生成 `F-<file>[<chkname>].csv`。

## CodeList（代码清单）

| 列名 | 数据类型 | 说明 |
|---|---|---|
| CODELISTNAME | 文本 | 代码列表名称 |
| CODE | 文本 | 源代码值 |
| VALUERAW | 文本 | 原始值 |
| VALUEEN | 文本 | 英文值（TRANSVAL） |
| VALUESDTM | 文本 | SDTM 标准值（SDTMVAL） |

扩展规则：当 `CODELISTNAME` 以 `_4OTHER` 结尾时，该表既提供“其他详情字段→英文值”的字典，也会在主表中建立“英文值→SDTM 值”的映射，用于“其他”取值的二次转换。

## Mapping（域与变量映射）

| 列名 | 数据类型 | 说明 |
|---|---|---|
| DEFINITION | 文本 | 定义名（与 MERGERULE/循环次数绑定） |
| DOMAIN | 文本 | 目标 SDTM 域（如 DM、CM 等；SUPP 域用 `SUPPxx`） |
| VARIABLE | 文本 | 目标变量 |
| NDKEY | 文本 | 非空保留键（“〇”表示该变量非空则保留该行） |
| FILENAME | 文本 | 来源组合文件名（与 `F-*.csv` 对应，可带循环语法） |
| FIELDNAME | 文本 | 来源字段名（支持 `$` 分隔多字段；支持 `CYCLE(...)` 循环） |
| OPERTYPE | 文本 | 操作类型（见下表） |
| PARAMETER | 文本 | 操作参数（支持 `$` 分隔与 `CYCLE(...)`） |

补充：
- MERGERULE 与循环次数保存在内部结构中，由程序根据 `DEFINITION` 行解析。
- 程序会将非标准变量自动追加到 `STANDARD_FIELDS[DOMAIN]`，并在输出时写入。
- `DomainsSetting` 可声明排序键；若未声明，默认以 `USUBJID` 排序；序列号字段按域规则自动生成。

## DomainsSetting（可选）

声明各 SDTM 域的排序键（排序用于生成序列号与稳定输出）。

| 列名 | 数据类型 | 说明 |
|---|---|---|
| DOMAIN | 文本 | SDTM 域名 |
| SORTKEYS | 文本 | 逗号分隔的排序字段列表；程序会包含 `USUBJID` |

## Refactoring（可选）

为格式化阶段提供中间产物函数的映射。

| 列名 | 数据类型 | 说明 |
|---|---|---|
| FILENAME | 文本 | 中间产物名（将生成 `F-<name>.csv`） |
| FUNCTION | 文本 | 可执行函数名（字符串，将通过 eval 调用） |

函数需定义于 `VC_BC04_operateType.py` 或研究特定模块 `studySpecific/<STUDY>/VC_BC05_studyFunctions.py` 中。

## Combine（可选）

与 Refactoring 类似，但用于将若干中间产物再组合输出为最终 `F-<name>.csv`。字段同上。

## Sites（可选）

在导出输入 CSV（`VC_PS01_makeInputCSV.py`）时用于将 SITEID 转换为目标系统代码。

| 列名 | 数据类型 | 说明 |
|---|---|---|
| SITENAME | 文本 | 站点名 |
| SITECODE | 文本 | 站点代码（输出时替换 SITEID） |

## HumanTrans / EXDETAILS（如项目需要）

若项目需要更复杂的“人工翻译/其他详情”映射，可在这两个工作表中维护。程序在 Process→OTHERDETAILSPROCESS 与 CodeList 的 `_4OTHER` 机制下自动连动。

---

## 操作类型参考（OPERTYPE）

| 代码 | 说明 | 参数格式 | 备注 |
|---|---|---|---|
| DEF | 赋常量 | `值` | 将 PARAMETER 原样写入目标变量 |
| FIX | 取单列 | 无 | 取 `FIELDNAME` 的第一列值 |
| FLG | 值映射 | `src:dst$src:dst` | 以分段映射；`null` 表示空串 |
| IIF | 条件选择 | `fld:val$fld:val` | 逐段匹配，匹配段取对应列（多列时按段索引） |
| COB | 拼接 | `SEP:分隔符` | 将多列以分隔符拼接（默认空串） |
| CDL | 代码表映射 | `CODELISTNAME` 或 `BLANK` | `BLANK` 表示不经映射直取原值 |
| PRF | 前缀 | `前缀` | 将参数作为前缀拼接到列值前 |
| SEL | 选择/过滤 | `字段:条件` | 条件支持 `not null`、`!值`、`值` 三种；不满足则跳过整行 |

注意：`FIELDNAME`/`PARAMETER` 支持使用 `$` 作为多段分隔；`CYCLE(a$b$...)` 可在多次循环中按段取值。

---

## 生成与链路要点

- 清洗（VC_OP01_cleaning）：根据 `Patients/Files/Process` 输出 `C-*.csv`、`deletedCols/DC-*.csv`、`deletedRows/DR-*.csv`；若提供研究特定排序函数 `sort_csv_data` 将按文件类型进行二级排序。
- 代码表（VC_OP02_insertCodeList）：建立/填充代码表，键 `(CODELISTID, CODE)`；重复将跳过。
- 元数据（VC_OP03_insertMetadata）：判断日期型（变量名含 `DTC` 或 TIME_VARIABLE 集合/补充时间标志），调用 `make_format_value` 处理 9999 年/99 月/日与 3 种日期粒度（YYYY、YYYY-MM、YYYY-MM-DD）。
- 格式化（VC_OP04_format）：创建视图 `TRANSDATA_VIEW_NAME`，生成 `F-*.csv` 及检查型 `F-<file>[<chk>].csv`；日志记录空列提示。
- 映射（VC_OP05_mapping）：去重逻辑基于 `NDKEY` 非空；按 `DomainsSetting` 排序并为含 `SEQ` 的域生成序号；输出至 `04_SDTM/sdtm_dataset-YYYYMMDDhhmmss/`。
- 导出输入 CSV（VC_PS01_makeInputCSV）：对非排除域（参见 `EXCLUSION_DOMAIN`）增加 `PAGEID/RECORDID`；生成 `SUPP*.csv` 作为补充域；若 `SITEID` 在 `Sites` 中存在则替换为站点代码。
- 打包（VC_PS02_csv2json）：生成 `m5/m5/datasets/<M5_PROJECT_NAME>/tabulations/{sdtm,cp}` 结构并压缩为 `m5.zip`。

Further verification is required. 