# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Config-driven ETL: raw clinical CSV exports → CDISC SDTM datasets → M5 submission package. Mapping rules
live in a per-study Excel workbook (`<STUDY_ID>_OperationConf.xlsx`); a 7-step pipeline backed by MySQL
executes them. Python 3.11+, pandas/numpy/openpyxl/mysql-connector, Textual for the TUI. No package
build (`pyproject.toml` / `setup.py` absent): syntax checks + tests + a DEMO run are the build.

## Commands

Run everything from the repository root.

```bash
pip install -r requirements.txt -r requirements-dev.txt

pytest -q                                   # whole suite, ~3 s, no MySQL needed
pytest -q tests/test_opertypes.py           # one file
pytest -q tests/test_opertypes.py::<name>   # one test
pytest -q -k guard                          # by keyword

python -m py_compile sdtm.py app/*.py pipeline/*.py

python sdtm.py <STUDY> run all              # all 7 steps (Windows: sdtm <STUDY> run all)
python sdtm.py <STUDY> run 3 5              # OP03..OP05;  run op05 = one step by id
python sdtm.py <STUDY> status               # latest output folder per stage
python sdtm.py <STUDY>                      # Textual TUI
python app/run_pipeline.py --study <STUDY> [start] [end] [--continue] [--dry-run]
python pipeline/VC_OP05_mapping.py          # one stage on its own (study from SDTM_STUDY / DEFAULT_STUDY)
```

End-to-end check after engine changes: run the bundled DEMO study (`python sdtm.py DEMO run all`, ~20 s).
It needs a running MySQL and a `project.local.json` with `"STUDIES_ROOT_PATH": "examples/studies"`, or
point `PROJECT_CONFIG_PATH` at a temp config containing that. Expected outputs are listed in
`examples/studies/DEMO/README.md`. When a change should not alter results, diff the new timestamped
output folders against the previous run (`m5.zip` differs only in zip timestamps; compare its members).

Optional lint tooling (not enforced): `black`, `isort`, `flake8` on `sdtm.py app pipeline`.

## Architecture

### Two repositories, study chosen at run time
This repo holds only the program. Studies (workbook, `VC_BC05_studyFunctions.py`, optional
`study.json`, `01_RawData/`, and the `02_Cleaning/` … `06_Inputpackage/` outputs) live in a separate,
private folder named by `STUDIES_ROOT_PATH` in the git-ignored, machine-level `project.local.json`.
Clinical data must never be committed here; `examples/studies/DEMO` is the only study in the repo.

Study resolution (`pipeline/sdtm_study.py`): CLI arg → `SDTM_STUDY` env → `DEFAULT_STUDY` → legacy
`STUDY_ID` → the only study folder present. `program_root()` is the repository root (parent of
`pipeline/`); relative `STUDIES_ROOT_PATH` and the default `project.local.json` resolve against it.
Table/view names derive from the study id (`VC05_<STUDY_ID>_CODELIST` …) unless `study.json` overrides.

### Layout and why `pipeline/` stays flat
- `sdtm.py` / `sdtm.bat`: the single entry point; puts `pipeline/` and `app/` on `sys.path`.
- `pipeline/`: every `VC_*` module + `sdtm_study.py`. **Not a package, on purpose.** Modules import each
  other by bare name with wildcard imports (`from VC_BC03_fetchConfig import *`), and each study's
  `VC_BC05_studyFunctions.py` does `from VC_BC04_operateType import *`. Turning this into a package or
  renaming modules breaks every study and creates duplicate module objects. Module names and numbers are
  also the vocabulary used in specs and study docs; keep them.
- `app/`: `sdtm_core.py` (step table `STEPS`, status, `iter_pipeline_events()` runner), `sdtm_tui.py`,
  `run_pipeline.py`. `sdtm_core.STEPS` and `run_pipeline.STEPS` are two copies of the step list.

### Layers (`VC_<LAYER><NN>_<name>.py`)
`BC01 → BC02 → BC03 → BC04/BC06 → OP*/PS*` (one-way):
- `VC_BC01_constant`: resolves the study **at import time** (exits with code 2 if none), loads settings,
  DB params, `STANDARD_FIELDS`, operation-type constants, output prefixes.
- `VC_BC02_baseUtils`: logger, timestamped dirs (`create_directory`, `find_latest_timestamped_path`),
  `make_format_value` (central date normalisation), `DatabaseManager`, `PipelineProgress`.
- `VC_BC03_fetchConfig`: parses/validates the 9 workbook sheets; raises `MappingConfigurationError`
  with sheet/row/field context.
- `VC_BC04_operateType`: applies Mapping rules (`precompute_mapping_rules`, `vectorized_field_mapping`,
  `ultra_fast_sequence_generation`, CSV cache); appends the study dir to `sys.path` and imports
  `VC_BC05_studyFunctions` (Combine functions) from there.
- `VC_BC06_operateTypeFunctions`: the operation types `DEF FIX FLG IIF COB CDL SEL PRF TPL`, registered
  in `get_opertype_function()`, plus guard lines (`&FIELD:VALUE`, AND-conditions on any type).
- `OP01..OP05` (cleaning → code list → metadata → format/Combine → SDTM mapping) and `PS01..PS02`
  (domain CSVs + `SUPP--` → M5 package).

### How a run executes
Each step is a **separate process**: the runner launches `python -u pipeline/<module>.py` (path from
`sdtm_study.stage_script()`), passing the study through `SDTM_STUDY` and setting `PIPELINE_ENV_KEY`.
Stage scripts emit progress lines prefixed with `PROGRESS_MARKER`, which the runner turns into
events for the TUI/CLI. Stages communicate only through files and MySQL: every step writes a new
timestamped folder (`<stage>/<name>_dataset-YYYYMMDDHHMMSS/`) and reads the latest folder of the step
before it. OP02/OP03 load the CODELIST/METADATA tables, OP04 builds the TRANSDATA view.

Engine detail (sheet semantics, `NDKEY`, Combine overlay, guards): `docs/AGENT_KNOWLEDGE.md`,
`docs/configuration.md`, `docs/architecture.md`.

## Conventions and gotchas

- Dataframes are string-first: `dtype=str`, `fillna('')`, `na_filter=False`. Don't introduce implicit
  numeric/date coercion; date normalisation goes through `make_format_value`.
- Tests: `tests/conftest.py` must set `PROJECT_CONFIG_PATH` / `SDTM_STUDY=DEMO` before any `VC_*` import
  (because of BC01's import-time resolution). `getMapping` appends to the module-level `STANDARD_FIELDS`,
  shared across a pytest process; tests must not assert on it. The `demo_wb` fixture loads a fresh
  in-memory DEMO workbook; `tests/wb_helpers.py` writes rows into it.
- Never hardcode study ids or paths; derive them from `project.local.json`, `study.json` and BC01
  constants. Keep the timestamped-folder pattern; don't overwrite earlier runs.
- Preserve output prefix contracts (`C-`, `DC-`, `DR-`, `F-`, `SUPP`) and `utf-8-sig` CSV encoding.
- Use `DatabaseManager` for DB lifecycle; keep table/view names config-driven; batched loads via staging +
  `LOAD DATA LOCAL INFILE`; MySQL 5.7 compatibility.
- Performance-sensitive: prefer vectorised pandas over row loops; keep `ultra_fast_sequence_generation`
  deterministic; keep the performance instrumentation in OP04/OP05; don't change OP05's multiprocessing
  strategy without validating.
- Adding an operation type: `opertype_<NEW>` in BC06, register in `get_opertype_function()`, constant in
  BC01, test in `tests/test_opertypes.py`, document in `docs/configuration.md` and `docs/AGENT_KNOWLEDGE.md` §6.
- Legacy camelCase helper names (`getSheetSetting`, `getCaseDict` …) and module docstrings are
  conventions; match the surrounding style. Code comments and docstrings are mostly Chinese/Japanese.
