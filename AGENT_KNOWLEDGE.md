# VAPORCONE AI Agent Guide

## 1) What This System Does
- Purpose: Convert raw clinical trial data into CDISC SDTM datasets and produce an M5 submission package.
- Core pipeline: Raw CSV → Cleaning → CodeList → Metadata → Formatting → Mapping → SDTM CSV → JSON → m5.zip.
- Tech stack: Python 3.11, MySQL (mysql-connector-python 9.4.0), pandas 2.3.1, numpy 2.2.6, openpyxl 3.1.5, dateutil 2.9.0.

## 2) Architecture & Naming
- Module prefixes: `BC` (Base Components), `OP` (Operations), `PS` (Post-Processing).
- Dependency flow:
```
VC_BC01 (Constants) → VC_BC02 (Utils) + VC_BC03 (Config)
                                      ↓
                           VC_BC04 (Dispatcher) → VC_BC06 (Operations)
                                      ↓
                           VC_BC05 (Study-Specific)
                                      ↓
                           VC_OP01-05 (Processing Stages)
                                      ↓
                           VC_PS01-02 (Output Generation)
```
- File naming: `VC_[MODULE][##]_[Function].py` (e.g., `VC_OP05_mapping.py`).

## 3) Key Modules & Responsibilities
- `VC_BC01_constant.py`: Loads `project.local.json`; defines paths, DB params, SDTM constants, operation-type constants; `_load_project_config()`.
- `VC_BC02_baseUtils.py`: Logging (`create_logger()`), directories with timestamps, date formatting (`make_format_value()`), latest-path finder, `DatabaseManager` (connect, create tables/views, `create_performance_indexes()`).
- `VC_BC03_fetchConfig.py`: Reads Excel config; `getSheetSetting()`, `getCaseDict()`, `getFileDict()`, `getProcess()`, `getCodeListInfo()`, `getMapping()`, `getDomainsSetting()`, `getSites()`, `getFormatDataset()`. Raises `MappingConfigurationError`.
- `VC_BC04_operateType.py`: Dispatch/optimization; `singleTable()`, `tableJoinType1()`, `precompute_mapping_rules()`, `ultra_fast_sequence_generation()`, `vectorized_field_mapping()`, `get_cached_csv()`.
- `VC_BC05_studyFunctions.py` (per study under `studySpecific/[STUDY_ID]/`): Study-specific joins/merges (e.g., `leftjoin()`, `tableMerge()`).
- `VC_BC06_operateTypeFunctions.py`: Implements op types `DEF/FIX/FLG/IIF/COB/CDL/PRF/SEL`; lookup via `get_opertype_function()`.

## 4) Config Sources
- `project.local.json` (example keys): `STUDY_ID`, `ROOT_PATH`, `RAW_DATA_ROOT_PATH`, `CODELIST_TABLE_NAME`, `METADATA_TABLE_NAME`, `TRANSDATA_VIEW_NAME`, `M5_PROJECT_NAME`. Optional `PROJECT_CONFIG_PATH` env var.
- Excel `studySpecific/[STUDY_ID]/[STUDY_ID]_OperationConf.xlsx` sheets: SheetSetting, Patients, Files, Process, CodeList, Mapping, DomainsSetting, Sites, Refactoring (optional), Combine (optional).

## 5) Processing Stages (inputs → outputs)
- `VC_OP01_cleaning.py`: Raw → `C_*` cleaned, `DC_*` removed cols, `DR_*` removed rows under `02_Cleaning/cleaning_dataset-[ts]/`.
- `VC_OP02_insertCodeList.py`: Config → `CODELIST_TABLE_NAME`.
- `VC_OP03_insertMetadata.py`: Config → `METADATA_TABLE_NAME`.
- `VC_OP04_format.py`: Views + type/format handling → `F_*` in `03_Format/format_dataset-[ts]/`.
- `VC_OP05_mapping.py`: Formatted → SDTM domains (`04_SDTM/sdtm_dataset-[ts]/`); uses op types and sequence generation.
- `VC_PS01_makeInputCSV.py`: SDTM → `[Domain].csv`, `SUPP*.csv` in `05_Inputfile/`.
- `VC_PS02_csv2json.py`: CSV → `06_Inputpackage/m5.zip`.
- Full run (PowerShell):  
`python VC_OP01_cleaning.py`  
`python VC_OP02_insertCodeList.py`  
`python VC_OP03_insertMetadata.py`  
`python VC_OP04_format.py`  
`python VC_OP05_mapping.py`  
`python VC_PS01_makeInputCSV.py`  
`python VC_PS02_csv2json.py`

## 6) Operation Types (BC06) Cheat Sheet
- `DEF`: fixed value.  
- `FIX`: fixed field mapping.  
- `FLG`: flag mapping (condition).  
- `IIF`: conditional value.  
- `COB`: combine fields.  
- `CDL`: code-list lookup.  
- `PRF`: add prefix.  
- `SEL`: selective mapping.  
- Add a new type: implement `opertype_NEW(...)` in `VC_BC06_operateTypeFunctions.py`, register in `get_opertype_function()`, add constant in `VC_BC01_constant.py`, update Excel mapping.

## 7) Study-Specific Logic
- Location: `studySpecific/[STUDY_ID]/VC_BC05_studyFunctions.py`.
- Add functions (joins/merges) and reference them in Excel Refactoring/Mapping.
- Create new study: add directory, create `[STUDY_ID]_OperationConf.xlsx`, implement study functions, update `project.local.json`, place raw data.

## 8) Data & Formatting Conventions
- Treat data as strings until final formatting; fill nulls with empty strings (`.fillna('')`).
- Key IDs: `SUBJID`, `USUBJID` (via `getCaseDict()`).
- Standard prefixes: `C_` (cleaned), `DC_` (removed cols), `DR_` (removed rows), `F_` (formatted), `SUPP` (supplemental).
- Timestamped outputs (e.g., `cleaning_dataset-YYYYMMDDhhmmss`) to keep multiple runs.
- Database view: `TRANSDATA_VIEW_NAME` joins metadata + codelist, exposes `TRANSVAL`/`SDTMVAL`.

## 9) Performance Tips
- Use `get_cached_csv()` and column filtering to reduce I/O.
- Prefer `vectorized_field_mapping()` over row-wise loops.
- `precompute_mapping_rules()` for mapping speed.
- Parallel domain processing in `VC_OP05_mapping.py` (ProcessPoolExecutor).
- DB: create indexes via `DatabaseManager.create_performance_indexes()`.
- Optional flags in `VC_OP04_format.py`: `ENABLE_PERFORMANCE_MONITORING`, `ENABLE_EXPLAIN_ANALYSIS`, `USE_TEMP_TABLES`, `ENABLE_WORK_TABLE_PERSISTENCE`.

## 10) Common Tasks
- Add operation type: see §6.
- Add study: see §7.
- Debug performance: enable monitoring/EXPLAIN, ensure indexes, review query plans.
- Troubleshoot:
- `MappingConfigurationError`: fix Excel mapping sheet.
- DB connection issues: verify host/user/pass/db.
- Path errors: verify `project.local.json`.
- Mapping errors: check field names/op types in Excel.

## 11) Quick References
- Paths/vars: `ROOT_PATH`, `SPECIFIC_PATH`, `CLEANINGSTEP_PATH`, `FORMAT_PATH`, `SDTMDATASET_PATH`, `INPUTFILE_PATH`, `INPUTPACKAGE_PATH`.
- Key classes/functions: `DatabaseManager`, `create_logger()`, `getSheetSetting()/getProcess()/getMapping()/getCodeListInfo()`, `vectorized_field_mapping()`, `ultra_fast_sequence_generation()`, `get_opertype_function()`.
- Outputs: `05_Inputfile/*.csv`, `06_Inputpackage/m5.zip`.
- Logs: `studySpecific/[STUDY]/log_file.log`.

## 12) How to Work Safely as an AI Agent
- Follow config-driven design; never hardcode study IDs/paths—read from `project.local.json` and Excel.
- Keep data flow pure: avoid mutating global state; prefer functional transformations on DataFrames.
- Preserve timestamped outputs; don’t overwrite prior runs unless explicitly requested.
- Validate mapping/formatting against Excel sheets before code changes.
- Prefer vectorized pandas/numpy operations; avoid row-by-row loops.
- Log clearly at major steps; surface Excel row info in errors.
- Keep naming consistent with existing patterns; use existing utils before adding new helpers.
