# Configuration

Everything a study needs is described in four places: the Excel workbook, the operation
types used in its Mapping sheet, the study's Python functions, and two small JSON files.

## Excel Config DSL — `OperationConf.xlsx`

The master configuration workbook drives the entire pipeline. Each sheet controls a specific aspect:

| Sheet | Columns (row 1 = header) | Purpose |
|-------|--------------------------|---------|
| **SheetSetting** | `SheetName`, `StartingRow`, then the column names of every other sheet | Index of the workbook: for each sheet, the first data row and the order of its columns. The parser reads all other sheets through this table |
| **Patients** | `USUBJID`, `SUBJID`, `MIGRATIONFLAG` | Subjects to migrate and their `SUBJID` → `USUBJID` mapping |
| **Files** | `FILENAME`, `MIGRATIONFLAG`, `TITLEROW`, `DATARROW`, `SUBJIDFIELDID`, `PROCESSINGLOGIC` | Raw CSV files in `01_RawData/`: header row, first data row, subject-id column |
| **Process** | `FILENAME`, `FIELDNAME`, `LABEL`, `DATATYPE`, `CODELISTNAME`, `MIGRATIONFLAG`, `CHKTYPE`, `OTHERDETAILSPROCESS` | Every field of every raw file: label, data type, code list, whether to keep it, extra formatting rules |
| **CodeList** | `CODELISTNAME`, `CODE`, `VALUERAW`, `VALUEEN`, `VALUESDTM` | Code / terminology value mappings (raw value → English → SDTM controlled term) |
| **Mapping** | `DEFINITION`, `DOMAIN`, `VARIABLE`, `NDKEY`, `FILENAME`, `FIELDNAME`, `OPERTYPE`, `PARAMETER` | SDTM domain rules: one row per target variable, with source file/field and the operation applied |
| **Combine** | `FILENAME`, `FUNCTION` | Derived tables built by a Python call in `VC_BC05_studyFunctions.py` (e.g. `DM()`), usable as `FILENAME` in Mapping. A Combine name equal to a Files name post-processes and overwrites that file's `F-` output |
| **DomainsSetting** | `DOMAIN`, `SEQFIELD`, `SORTKEYS` | Per-domain sort keys and the `--SEQ` variable to number records with |
| **Sites** | `SITENAME`, `SITECODE` | Site name → site code lookup used when building the M5 input CSVs |

All nine sheets must exist. `examples/studies/DEMO/DEMO_OperationConf.xlsx` is a minimal working workbook; its README walks through every sheet.

## Mapping Operation Types — `OPERTYPE`

| Type | Result | `PARAMETER` example |
|:----:|--------|---------------------|
| `DEF` | A constant | `SURVIVAL STATUS` |
| `FIX` | The source field value as is | – |
| `FLG` | Map source values to output values (one `source:output` pair per line, or comma-separated) | `1:Y,0:N` |
| `IIF` | Copy the source field only where a flag field has the given value (one pair per source field) | `FLAG_FIELD:Y` |
| `COB` | Join the non-blank values of several source fields | `:/` (separator `/`) |
| `CDL` | Look the value up in a CodeList (`VALUESDTM`) | `CL_SEX` |
| `SEL` | Copy the source field and keep only rows meeting a condition | `FIELD:VALUE`, `FIELD:!VALUE`, `FIELD:not null` |
| `PRF` | Add a prefix | `P` |
| `TPL` | Fill a template; `{}` is the source value, empty stays empty | `SCRT DISCONTINUED: {}` |

**Guard lines** work with every type: a `PARAMETER` line that starts with `&` is an extra AND
condition `&FIELD:VALUE` (`VALUE` may also be `null`, `not null` or `!VALUE`). Rows that fail a
guard get an empty value; on the `NDKEY` variable that drops the record, and on `SEL` the row is
dropped too.

**`NDKEY`** marks the one variable per `DEFINITION` block that decides whether a record is
written: blank → no record. Only the first `〇` in a block counts, so put guard lines for a
parent item on that row. More detail: [AGENT_KNOWLEDGE.md §6](AGENT_KNOWLEDGE.md).

## Study-Specific Functions — `VC_BC05_studyFunctions.py`

For domain logic that cannot be expressed in the Excel DSL, each study defines custom Python functions:

```python
def DM():
    """Custom DM domain generation.

    Sources: RGST (registration), LSVDAT (last survival), OC (outcome)
    Computes: RFENDAT (end date), DTHFLG (death flag)
    """
    ...
```

## Project Settings — `project.local.json`

Machine-level settings (not committed). All keys are optional.

| Key | Description |
|-----|-------------|
| `STUDIES_ROOT_PATH` | Parent directory of the study folders. Default: `<project root>/studySpecific` |
| `DEFAULT_STUDY` | Study used when none is given on the command line / `SDTM_STUDY` |
| `DB_HOST` / `DB_USER` / `DB_PASSWORD` / `DB_DATABASE` | MySQL connection (defaults: `127.0.0.1` / `root` / `root` / `VC-DataMigration_2.0`) |

**Study resolution order:** command-line argument → `SDTM_STUDY` env var → `DEFAULT_STUDY` →
legacy `STUDY_ID` → the only study folder present → error listing available studies.

## Study Settings — `<STUDY_ID>/study.json`

Optional, lives inside the study folder. Everything is derived from the study id when absent.

| Key | Default | Description |
|-----|---------|-------------|
| `M5_PROJECT_NAME` | `<STUDY_ID>` | Project name in M5 package output |
| `RAW_DATA_DIR` | `01_RawData` | Raw CSV directory, relative to the study folder |
| `RAW_DATA_ROOT_PATH` | – | Absolute raw CSV directory (overrides `RAW_DATA_DIR`) |
| `CODELIST_TABLE_NAME` | `VC05_<STUDY_ID>_CODELIST` | MySQL table for code list data |
| `METADATA_TABLE_NAME` | `VC05_<STUDY_ID>_METADATA` | MySQL table for metadata |
| `TRANSDATA_VIEW_NAME` | `VC05_<STUDY_ID>_TRANSDATA` | MySQL view for formatted data |

> **Legacy format:** a `project.local.json` that contains `STUDY_ID`, table names and
> `RAW_DATA_ROOT_PATH` (pre-2026-09 layout) keeps working unchanged.
