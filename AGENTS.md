# AGENTS.md
Guide for autonomous coding agents working in `SDTM_ENSEMBLE`.
Use this as the baseline for edits, validation, and safe execution.

## 1) Repository Overview
- Language: Python 3.11+
- Main dependencies: `pandas`, `numpy`, `openpyxl`, `mysql-connector-python`, `python-dateutil`
- Architecture: config-driven ETL from raw clinical CSVs to CDISC SDTM and M5 package output
- Main config files:
  - `project.local.json`
  - `studySpecific/<STUDY_ID>/<STUDY_ID>_OperationConf.xlsx`
- Core module chain:
  - `VC_BC01_constant.py` -> constants + project config
  - `VC_BC02_baseUtils.py` -> logger/fs/db helpers
  - `VC_BC03_fetchConfig.py` -> Excel config parsing
  - `VC_BC04_operateType.py` + `VC_BC06_operateTypeFunctions.py` -> mapping engine
  - `VC_OP01`..`VC_OP05` + `VC_PS01`..`VC_PS02` -> stage scripts

## 2) Environment Setup
Run from repository root:
```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt
python -c "import pandas,numpy,mysql.connector,openpyxl,dateutil; print('deps ok')"
```

## 3) Build, Lint, and Test Commands
There is no formal package build pipeline (`pyproject.toml`/`setup.py` absent).
Treat syntax checks + impacted stage runs as build verification.

### 3.1 Syntax checks
All top-level pipeline files:
```bash
python -m py_compile VC_BC01_constant.py VC_BC02_baseUtils.py VC_BC03_fetchConfig.py VC_BC04_operateType.py VC_BC06_operateTypeFunctions.py VC_OP01_cleaning.py VC_OP02_insertCodeList.py VC_OP03_insertMetadata.py VC_OP04_format.py VC_OP05_mapping.py VC_PS01_makeInputCSV.py VC_PS02_csv2json.py
```
Single-file syntax check:
```bash
python -m py_compile VC_OP04_format.py
```

### 3.2 Lint/format
Recommended tooling and commands:
```bash
pip install black flake8 isort
black *.py
black VC_OP05_mapping.py
isort *.py
isort VC_BC04_operateType.py
flake8 *.py
flake8 VC_OP03_insertMetadata.py
```

### 3.3 Tests (current state + single-test guidance)
- Current repo state: no dedicated `tests/` suite and no `pytest.ini`.
- Validate with targeted stage smoke runs and syntax checks.
- If pytest tests are added, use:
```bash
pytest -q
pytest -q tests/test_mapping.py
pytest -q tests/test_mapping.py::test_sequence_generation
pytest -q -k sequence
```

## 4) Pipeline Commands
Full run:
```bash
python VC_OP01_cleaning.py
python VC_OP02_insertCodeList.py
python VC_OP03_insertMetadata.py
python VC_OP04_format.py
python VC_OP05_mapping.py
python VC_PS01_makeInputCSV.py
python VC_PS02_csv2json.py
```
Run a single stage (preferred for scoped changes):
```bash
python VC_OP04_format.py
```
Experiment script:
```bash
python experiment/combine_test/VC_OP06_combine.py
```

## 5) Code Style and Engineering Rules

### 5.1 Imports
- Respect dependency layering (`BC` -> `OP` -> `PS`).
- Existing files frequently use wildcard imports from shared modules.
- Do not mass-refactor wildcard imports unless explicitly requested.
- In new files, prefer explicit imports where practical.
- Keep stdlib imports before third-party imports when editing blocks.

### 5.2 Formatting and structure
- Use 4-space indentation and PEP 8-compatible formatting.
- Preserve module/function docstrings; they are part of project conventions.
- Keep stage scripts procedural and readable; avoid unnecessary abstraction.
- Add comments only when business logic is non-obvious.

### 5.3 Types and dataframe handling
- Codebase is mostly untyped Python; keep style consistent unless hints add clear value.
- Preserve string-first dataframe behavior (`dtype=str`, `fillna('')`, `na_filter=False`).
- Avoid introducing implicit numeric/date coercion in shared paths.
- Keep date normalization centralized through `make_format_value`.

### 5.4 Naming conventions
- Module naming pattern: `VC_<MODULE><NN>_<name>.py`.
- Constants: uppercase snake case.
- Many helper names are legacy camelCase (`getSheetSetting`, `getCaseDict`, etc.).
- Match local naming style in files you edit.

### 5.5 Error handling
- Validate config early and fail fast for invalid workbook mappings.
- Preserve `MappingConfigurationError` behavior and context fields.
- Include actionable context in failures (sheet, row, file, domain, field).
- Use explicit `try/except` around DB/file/mapping boundaries.

### 5.6 Logging and diagnostics
- Use `create_logger(..., logging.DEBUG)` and existing log path conventions.
- Keep progress prints in long-running stage scripts.
- Preserve performance instrumentation in `VC_OP04_format.py` and `VC_OP05_mapping.py`.

### 5.7 Paths and outputs
- Never hardcode study-specific paths; derive from constants/config.
- Respect timestamped output folders (`create_directory`, `find_latest_timestamped_path`).
- `VC_PS01_makeInputCSV.py` writes to `05_Inputfile/inputfile_dataset-[timestamp]/` and consumes the latest `04_SDTM/sdtm_dataset-[timestamp]/`.
- `VC_PS02_csv2json.py` reads the latest `05_Inputfile/inputfile_dataset-[timestamp]/` and writes to `06_Inputpackage/inputpackage_dataset-[timestamp]/`.
- Keep CSV encoding consistent (`utf-8-sig` where currently used).
- Preserve output prefix contracts: `C-`, `DC-`, `DR-`, `F-`, `SUPP`.

### 5.8 Database conventions
- Use `DatabaseManager` for connect/disconnect and table/view lifecycle.
- Keep table/view names config-driven (`CODELIST_TABLE_NAME`, `METADATA_TABLE_NAME`, `TRANSDATA_VIEW_NAME`).
- Prefer batched inserts for large loads (staging + `LOAD DATA LOCAL INFILE`).
- Maintain MySQL compatibility assumptions in current SQL.

### 5.9 Performance-sensitive areas
- Prefer vectorized pandas/numpy operations over row-wise Python loops.
- Be careful with sequence logic (`ultra_fast_sequence_generation`) and determinism.
- Reuse CSV cache and precomputed mapping rules in BC04/OP05 paths.
- Avoid changing multiprocessing strategy in mapping unless necessary and validated.

## 6) Agent Completion Checklist
1. Run `py_compile` on touched Python files.
2. Run the narrowest impacted stage script(s).
3. Run `VC_OP05_mapping.py` when mapping/config logic changes.
4. Validate output artifacts when schemas/fields change.
5. Update this guide if commands/conventions materially change.

## 7) Cursor/Copilot Rules Status
Checked for editor-specific policy files:
- `.cursor/rules/`: not found
- `.cursorrules`: not found
- `.github/copilot-instructions.md`: not found
No additional Cursor/Copilot policy files are currently defined.
