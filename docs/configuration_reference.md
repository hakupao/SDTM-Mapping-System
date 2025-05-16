# 配置参考文档

本文档详细说明SDTM数据迁移工具的配置文件结构和参数。

## 配置文件概述

配置文件为Excel格式，命名为`[研究ID]_OperationConf.xlsx`，包含多个工作表，每个工作表控制特定功能。

## 工作表说明

### SheetSetting

控制其他工作表的设置。

| 列名       | 数据类型 | 说明                       |
|-----------|---------|----------------------------|
| SHEETNAME | 文本    | 工作表名称                  |
| STARTINGROW | 数字   | 数据起始行（一般为标题下一行）|
| MAXCOL    | 数字    | 最大列数                    |

### Files

定义源数据文件信息。

| 列名         | 数据类型 | 说明                        |
|-------------|---------|----------------------------|
| FILENAME    | 文本    | 文件名（不含扩展名）          |
| TITLEROW    | 数字    | 标题行号                    |
| DATARROW    | 数字    | 数据起始行号                |
| SUBJIDFIELDID | 文本  | 受试者ID字段标识符          |
| PROCESSINGLOGIC | 文本 | 处理逻辑（可选）            |

### Process

定义字段处理方式。

| 列名         | 数据类型 | 说明                      |
|-------------|---------|---------------------------|
| FILENAME    | 文本    | 对应Files表中的文件名      |
| FIELDNAME   | 文本    | 字段名称                  |
| LABEL       | 文本    | 字段标签                  |
| CODELISTNAME | 文本   | 代码列表名称（若适用）     |
| CHKTYPE     | 文本    | 检查类型                  |
| OTHERDETAILSPROCESS | 文本 | 其他细节处理方式      |
| DATAEXTRACTION | 文本 | 数据提取方式              |
| OTHERVAL    | 文本    | 其他值                    |

### CodeList

定义代码列表映射。

| 列名       | 数据类型 | 说明                      |
|-----------|---------|---------------------------|
| CODELISTNAME | 文本  | 代码列表名称              |
| CODE      | 文本    | 代码值                    |
| VALUERAW  | 文本    | 原始值                    |
| VALUEEN   | 文本    | 英文值                    |
| VALUESDTM | 文本    | SDTM标准值                |

### Mapping

定义SDTM域映射规则。

| 列名      | 数据类型 | 说明                      |
|----------|---------|---------------------------|
| DEFINITION | 文本   | 定义名称                  |
| DOMAIN   | 文本    | SDTM域                    |
| VARIABLE | 文本    | SDTM变量                  |
| NDKEY    | 文本    | 非重复键（Y/N）            |
| SORTKEYS | 文本    | 排序键                    |
| MERGERULE | 文本   | 合并规则                  |
| OPERTYPE | 文本    | 操作类型                  |
| PARAMETER | 文本    | 参数                     |

### Combine (可选)

定义文件合并规则。

| 列名      | 数据类型 | 说明                      |
|----------|---------|---------------------------|
| FILENAME | 文本    | 合并后的文件名             |
| FUNCTION | 文本    | 合并使用的函数名称         |

### DomainsSetting (可选)

定义SDTM域附加设置。

| 列名      | 数据类型 | 说明                      |
|----------|---------|---------------------------|
| DOMAIN   | 文本    | SDTM域名称                |
| 各种设置列 | 文本    | 域特定设置                |

## 操作类型参考

在Mapping表的OPERTYPE列中可使用以下值：

| 操作类型代码 | 说明                        | 参数示例                  |
|------------|----------------------------|-----------------------------|
| DEF        | 默认值                      | "C"                        |
| FIX        | 固定值                      | "CIRCULATE"                |
| FLG        | 标志值                      | "Y"                        |
| IIF        | 条件判断                    | "if(A=='X',1,2)"           |
| COB        | 字段组合                    | "A+'-'+B"                  |
| CDL        | 代码查找                    | "CODELISTNAME,FIELD"       |
| SEL        | 选择                        | "FIELD1,FIELD2,FIELD3"     |
| PRF        | 前缀处理                    | "PREFIX,FIELD"             |

## 配置示例

### 简单域映射示例

```
定义名: DM_DOMAIN
域: DM
变量: DOMAIN
操作类型: FIX
参数: "DM"

定义名: DM_USUBJID
域: DM
变量: USUBJID
操作类型: COB
参数: "STUDYID+'-'+SUBJID"
```

## 高级配置技巧

### 条件映射

使用IIF操作类型进行条件映射：

```
操作类型: IIF
参数: "if(SEX=='M','MALE',if(SEX=='F','FEMALE','UNKNOWN'))"
```

### 多字段选择

使用SEL操作类型选择第一个非空值：

```
操作类型: SEL
参数: "BIRTHDAT,BIRTHDT,DOB"
``` 