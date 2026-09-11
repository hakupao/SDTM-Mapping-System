# DEMO study

A complete, runnable study with fake data for three subjects. It exercises every
sheet of the Excel DSL and all seven pipeline steps, producing DM, DS (+ SUPPDS)
and SS. Use it to check your setup and as the template for a real study.

## Run it

Prerequisites: Python 3.11+, `pip install -r requirements.txt`, and a MySQL
server whose user may create databases (the pipeline creates everything itself).

```bash
# project.local.json in the repository root
{
  "STUDIES_ROOT_PATH": "examples/studies",
  "DEFAULT_STUDY": "DEMO",
  "DB_HOST": "127.0.0.1", "DB_USER": "root", "DB_PASSWORD": "root"
}

python run_pipeline.py --study DEMO      # all 7 steps, ~10 s
# or: sdtm DEMO run all
```

Output lands in timestamped folders under this directory
(`02_Cleaning/` … `06_Inputpackage/`); they are git-ignored. The final
`06_Inputpackage/…/m5.zip` is the M5 package.

Expected result (`05_Inputfile/…/`):

| File | Rows | What to look at |
|------|:----:|-----------------|
| `DM.csv` | 3 | `RFENDTC` = death date or last-alive date, `DTHFL` = Y for DEMO-002, `SITEID` = S001, `SEX`/`AGE` from RGST |
| `SS.csv` | 3 | one `SURVSTAT` record per subject: ALIVE from LSVDAT, DEAD from OC |
| `DS.csv` | 2 | re-evaluation decision; DEMO-003 has no decision, so its row is dropped by the `NDKEY` rule |
| `SUPPDS.csv` | 2 | `DSYNFLG` (re-evaluation performed flag) as a supplemental qualifier |

## Folder layout

```
DEMO/
├── DEMO_OperationConf.xlsx    # the mapping DSL (required, name = <STUDY_ID>_OperationConf.xlsx)
├── VC_BC05_studyFunctions.py  # Python functions referenced by the Combine sheet (required)
├── study.json                 # optional per-study settings
├── 01_RawData/                # raw CSV exports: RGST, LSVDAT, OC, REV
└── 02_Cleaning/ … 06_Inputpackage/   # created by the pipeline
```

A folder under `STUDIES_ROOT_PATH` is recognised as a study when it contains
`<STUDY_ID>_OperationConf.xlsx` or `study.json`.

## Raw CSV format

Row 1 holds display labels, row 2 the field ids, data starts at row 3
(`TITLEROW` = 2, `DATARROW` = 3 in the Files sheet). UTF-8 with BOM.
Dates are `YYYY/MM/DD` and are converted to ISO 8601 by OP03.

```
Subject Id,Sex,Sex - Code,Age at consent
SubjectId,SEX,SEXCD,AGE
DEMO-001,Male,M,54
```

## How the workbook drives the pipeline

| Sheet | In this demo |
|-------|--------------|
| **SheetSetting** | Lists the other 8 sheets, their first data row and column order. Column names here are what the parser looks for, so the header row of each sheet is free text |
| **Patients** | 3 subjects, all flagged `○` (migrate). `×` would exclude a subject from every file |
| **Files** | 4 raw files, subject id column `SubjectId`. `PROCESSINGLOGIC` may hold a Python expression over `row` to drop rows |
| **Process** | Every field of every file. `○` keeps the field, `×` drops it (the label columns `SEX`, `REV_YN`, `REV_R` are dropped, the code columns kept). `DATATYPE` `Date` triggers date normalisation; `CODELISTNAME` links a field to CodeList |
| **CodeList** | `CODE` is what the raw file contains, `VALUEEN` the formatted value, `VALUESDTM` the controlled term written by the `CDL` operation |
| **Mapping** | One block per `DEFINITION`. Rows without a DEFINITION belong to the block above. `FILENAME` is a raw file or a Combine table; `OPERTYPE` `DEF` writes the constant in PARAMETER, `FIX` copies FIELDNAME, `CDL` looks FIELDNAME up in the code list named in PARAMETER. A record is kept only if at least one `NDKEY`-marked variable is non-blank |
| **Combine** | `REV_DS` filters REV to re-evaluation rows; `DM` joins RGST, LSVDAT and OC and derives `RFENDAT` / `DTHFLG`. Both are functions in `VC_BC05_studyFunctions.py` |
| **DomainsSetting** | Sort keys per domain and the `--SEQ` variable to number records |
| **Sites** | `SITEID` values written by Mapping are replaced by `SITECODE` in PS01 |

Other operation types available in Mapping: `FLG`, `IIF`, `COB`, `SEL`, `PRF`
(see `VC_BC06_operateTypeFunctions.py`).

## study.json

All keys are optional; defaults derive from the study id.

| Key | Default | Meaning |
|-----|---------|---------|
| `M5_PROJECT_NAME` | `<STUDY_ID>` | Project name written into the M5 package |
| `RAW_DATA_DIR` | `01_RawData` | Raw CSV directory, relative to the study folder |
| `RAW_DATA_ROOT_PATH` | – | Absolute raw CSV directory (overrides `RAW_DATA_DIR`) |
| `CODELIST_TABLE_NAME` | `VC05_<STUDY_ID>_CODELIST` | MySQL table for code lists |
| `METADATA_TABLE_NAME` | `VC05_<STUDY_ID>_METADATA` | MySQL table for metadata |
| `TRANSDATA_VIEW_NAME` | `VC05_<STUDY_ID>_TRANSDATA` | MySQL view for formatted data |

## Starting a real study from this one

1. Copy `DEMO/` to `<STUDIES_ROOT_PATH>/<STUDY_ID>/` and rename the workbook to
   `<STUDY_ID>_OperationConf.xlsx`.
2. Replace `01_RawData/` with your exports and rewrite Files / Process for them.
3. Add code lists, then write Mapping one domain at a time, running
   `sdtm <STUDY_ID> run 1 5` after each domain.
4. Put any logic the DSL cannot express into `VC_BC05_studyFunctions.py` and
   reference it from Combine.
