# Getting Started

From a fresh clone to a finished M5 package, then to your own study.

## 1. Prerequisites

- **Python 3.11+**
- **MySQL** (tested with 5.7), local or remote. The configured user needs `CREATE DATABASE` /
  `CREATE TABLE` / `CREATE VIEW`: the pipeline creates its database, tables and views itself.

## 2. Install

```bash
git clone https://github.com/hakupao/SDTM-Mapping-System.git
cd SDTM-Mapping-System

python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
# source .venv/bin/activate         # Linux / macOS

pip install -r requirements.txt      # runtime, includes textual for the TUI
pip install -r requirements-dev.txt  # optional: pytest
```

## 3. Point the program at a study folder

Create `project.local.json` in the repository root (copy
`examples/project.local.json.example`). It describes **this machine only** and is git-ignored.

```json
{
  "STUDIES_ROOT_PATH": "examples/studies",
  "DEFAULT_STUDY": "DEMO",
  "DB_HOST": "127.0.0.1", "DB_USER": "root", "DB_PASSWORD": "root"
}
```

A relative `STUDIES_ROOT_PATH` is resolved against the repository root. All keys are
described in [configuration.md](configuration.md#project-settings--projectlocaljson).

## 4. Run the bundled DEMO

```bash
python sdtm.py DEMO run all     # Windows: sdtm DEMO run all
```

Three fake subjects go through all 7 steps in about 20 seconds. The outputs land in
timestamped folders under `examples/studies/DEMO/` (`02_Cleaning/` … `06_Inputpackage/`);
the final `06_Inputpackage/…/m5.zip` is the M5 package. What each output should contain is
listed in [`examples/studies/DEMO/README.md`](../examples/studies/DEMO/README.md).

To check the code without MySQL:

```bash
pytest -q        # about 3 seconds, reads the DEMO workbook only
```

## 5. Create your own study

1. Make a folder for your studies **outside this repository** (clinical data must never enter
   the public history), for example a sibling private repo `SDTM-Studies/`, and set
   `STUDIES_ROOT_PATH` to it.
2. Copy `examples/studies/DEMO/` to `<STUDIES_ROOT_PATH>/<STUDY_ID>/` and rename the
   workbook to `<STUDY_ID>_OperationConf.xlsx`.
3. Put the raw CSV exports in `01_RawData/` and describe them in the workbook
   (Files → Process → CodeList → Mapping). The sheets are explained in
   [configuration.md](configuration.md).
4. Logic the Excel DSL cannot express goes into the study's `VC_BC05_studyFunctions.py`
   (Combine functions).
5. Run `sdtm <STUDY_ID>` and press `a`, or `sdtm <STUDY_ID> run all`.

## 6. Ways to run

```bash
sdtm <STUDY>                      # Terminal UI (python sdtm.py <STUDY> without sdtm.bat)
sdtm <STUDY> run all              # all 7 steps, then exit
sdtm <STUDY> run 3 5              # steps OP03 .. OP05
sdtm <STUDY> run op05             # one step by id
sdtm <STUDY> status               # latest output folder of each stage
sdtm <STUDY> shell                # line console
sdtm studies                      # list studies under STUDIES_ROOT_PATH

python app/run_pipeline.py --study <STUDY> [start] [end] [--continue] [--dry-run]
python pipeline/VC_OP05_mapping.py   # one stage script on its own
```

`<STUDY>` may be omitted when `SDTM_STUDY` or `DEFAULT_STUDY` is set, or when only one study
exists. Every command and TUI key is listed in [cli.md](cli.md).

## Next

- [architecture.md](architecture.md): how the 7 steps, the modules and the two repositories fit together
- [configuration.md](configuration.md): the Excel DSL, operation types and settings files
