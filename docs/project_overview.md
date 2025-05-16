# SDTM数据迁移工具 - 项目概述

## 项目简介

SDTM（Study Data Tabulation Model）数据迁移工具是一个专门用于临床试验数据标准化处理的Python应用程序。该工具主要用于将原始临床试验数据转换为符合CDISC SDTM标准的格式，便于监管提交和数据分析。

## 项目架构

本项目采用模块化设计，主要包括以下组件：

### 基础模块 (Base Components)
- `VC_BC01_constant.py`: 定义全局常量和配置
- `VC_BC02_baseUtils.py`: 基础工具函数
- `VC_BC03_fetchConfig.py`: 配置文件读取处理
- `VC_BC04_operateType.py`: 数据操作类型定义
- `VC_BC05_studyFunctions.py`: 研究特定的函数（位于studySpecific目录下）

### 操作模块 (Operation Modules)
- `VC_OP00_checkConfig.py`: 检查配置有效性
- `VC_OP01_cleaning.py`: 数据清洗
- `VC_OP02_insertCodeList.py`: 代码列表插入
- `VC_OP03_insertMetadata.py`: 元数据插入
- `VC_OP04_format.py`: 数据格式化
- `VC_OP05_mapping.py`: 数据映射到SDTM域

### 处理脚本 (Processing Scripts)
- `VC_PS01_makeInputCSV.py`: 生成输入CSV文件
- `VC_PS02_csv2json.py`: CSV转JSON工具

## 数据流程

1. **数据清洗**: 原始数据通过清洗步骤，去除无效数据
2. **代码列表处理**: 应用编码标准化
3. **元数据处理**: 添加必要的元数据
4. **格式转换**: 转换为标准格式
5. **SDTM映射**: 映射到SDTM标准域
6. **最终输出**: 生成合规的SDTM数据集

## 目录结构

```
SDTM/
├── studySpecific/ - 存放研究特定的配置和数据
│   └── [研究ID]/ - 各研究的专用目录
│       ├── 01_RawData/ - 原始数据
│       ├── 02_Cleaning/ - 清洗后的数据
│       ├── 03_Format/ - 格式化后的数据
│       ├── 04_SDTM/ - 最终SDTM格式数据
│       └── logs/ - 日志文件
├── docs/ - 项目文档
├── VC_BC*.py - 基础组件
├── VC_OP*.py - 操作模块
└── VC_PS*.py - 处理脚本
```

## 适用场景

- 临床试验数据标准化
- 监管合规数据准备
- 多源数据整合与转换
- 多中心临床研究数据处理 