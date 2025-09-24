# VAPORCONE Project Agent

## Project Snapshot
- Purpose: migrate raw clinical CSVs into CDISC SDTM deliverables and regulatory M5 packages for study `CIRCULATE`.
- Stack: Python 3.11 with pandas/numpy/openpyxl for data shaping and MySQL for metadata storage; see `requirements.txt`.
- Runtime layout: base components drive Excel-configured operations under `studySpecific/CIRCULATE`, producing staged outputs in timestamped subfolders beneath `02_Cleaning`, `03_Format`, `04_SDTM`, `05_Inputfile`, and `06_Inputpackage`.

## End-to-End Flow
- `VC_OP01_cleaning.py:13` → filters raw CSVs using Excel rules and writes cleaned/removed data splits.
- `VC_OP02_insertCodeList.py:13` → loads `CodeList` sheet into MySQL lookup tables.
- `VC_OP03_insertMetadata.py:15` → denormalises cleaned CSV rows into metadata staging tables and bulk loads to MySQL.
- `VC_OP04_format.py:266` → rebuilds formatted CSVs from database views with performance-aware SQL orchestration.
- `VC_OP05_mapping.py:237` → vectorises SDTM domain assembly, parallelising per-domain work and generating sequencing.
- `VC_PS01_makeInputCSV.py:13` → separates SDTM standard vs supplemental fields, adds site codes, emits submission CSVs.
- `VC_PS02_csv2json.py:14` → groups CSV content by subject and packages JSON + zipped `m5` deliverable.
- Optional experiment: `experiment/combine_test/VC_OP06_combine.py:18` replays combine operations outside production paths.

## Module Inventory
- **Constants** — `VC_BC01_constant.py:37` centralises study settings (paths, table names), Excel sheet identifiers, field aliases, regex helpers, static SDTM field dictionaries, and execution flags.
- **Utilities & DB** — `VC_BC02_baseUtils.py:13` offers logging, filesystem helpers, CSV utilities, and `DatabaseManager` (`VC_BC02_baseUtils.py:256`) for connection lifecycle, table/index management, bulk import prep, and EXPLAIN diagnostics.
- **Config Readers** — `VC_BC03_fetchConfig.py` exposes parsing helpers:
  - `getSheetSetting(...):16` builds per-sheet column/row maps from `SheetSetting`.
  - `getCaseDict(...):57` resolves `SUBJID→USUBJID` for migrated subjects.
  - `getFileDict(...):99` interprets file-level metadata (title/data row offsets, subject key, custom filters).
  - `getProcess(...):146` separates transferable vs dropped columns, captures CHK extract specs, and returns `{fieldDict, transFieldDict, chkFileDict, ex_fieldsDict}`.
  - `getCodeListInfo(...):246` reads codelist rows and flags.
  - `getMapping(...):289` constructs nested `domain → definition row → variable` maps with operator parameters and per-variable SUPP flags while tracking merge rules.
  - `getDomainsSetting(...):383` and `getSites(...):418` load sorting keys and site code translations.
  - `getCombineInfo(...):432` retrieves experimental combine recipes.
- **Data Operators** — `VC_BC04_operateType.py` provides cached CSV loading, table joins, precomputed mapping introspection (`precompute_mapping_rules:105`), fast sequencing (`ultra_fast_sequence_generation:187`), and vectorised field mapping helpers (`vectorized_field_mapping:253`).
- **Study Logic** — `studySpecific/CIRCULATE/VC_BC05_studyFunctions.py` implements bespoke joins, merges, and derivations (e.g., `make_DMFrame:84`, `process_MH_A:398`, `process_SUPR_MR:805`) invoked by mapping definitions.
- **Experiment Tools** — `experiment/combine_test/VC_OP06_combine.py` reads `Combine_process` steps, dispatching MERGE/SORT/CONCAT behaviours into a sandboxed `TEST_COMBINE` area.

## Configuration Assets
### `studySpecific/CIRCULATE/CIRCU- CONFIG_NAME (VC_BC01_constant.py:70) binds every run to {STUDY_ID}_OperationConf.xlsx inside SPECIFIC_PATH; all loaders share this entry point.
- Sheet names consumed by the code are defined in VC_BC01_constant.py:71 (SHEETSETTING_SHEET_NAME, FILELIST_SHEET_NAME, CASELIST_SHEET_NAME, etc.), so the workbook must expose tabs with those exact identifiers.
- Column headers the parsers rely on are declared via the COL_* constants in VC_BC01_constant.py:92, letting the readers resolve positions regardless of column order.
- Each reader in VC_BC03_fetchConfig.py enforces its own contract; if a column is missing, the function exits with sys.exit() messages that identify the offending sheet or field, so mismatches surface immediately.

### Shee- **SheetSetting** — getSheetSetting (VC_BC03_fetchConfig.py:16) scans row 1 until the first blank, expecting labels such as SheetName, StartingRow, and any column names referenced by other sheets. Data rows map SheetName to column offsets so later lookups stay position-independent.
- **Patients** — getCaseDict (VC_BC03_fetchConfig.py:57) reads USUBJID, SUBJID, and MIGRATIONFLAG. Entries marked with MARK_CROSS are skipped, and any flag outside MARK_CIRCLE triggers a hard failure. Auxiliary columns (VEGA, ALTAIR, etc.) are tolerated because the function never references them.
- **Files** — getFileDict (VC_BC03_fetchConfig.py:99) requires FILENAME, MIGRATIONFLAG, TITLEROW, DATAROW, SUBJIDFIELDID, plus optional PROCESSINGLOGIC. Filenames may include a .csv suffix; the loader strips it. Missing subject IDs or non-numeric row markers abort the run.
- **Process** — getProcess (VC_BC03_fetchConfig.py:146) depends on FILENAME, FIELDNAME, LABEL, MIGRATIONFLAG, CODELISTNAME, CHKTYPE, and OTHERDETAILSPROCESS. It also locates the DATAEXTRACTION header token in row 1 and reads CHK file names from row 2 to assemble chkFileDict. OTHERDETAILSPROCESS values must follow the "value:field" pattern; malformed entries raise an error.
- **CodeList** — getCodeListInfo (VC_BC03_fetchConfig.py:246) expects CODELISTNAME, CODE, VALUERAW, VALUEEN, VALUESDTM to build both grouped dictionaries and SQL-ready rows. Legacy lists with a 4OTHER suffix are ignored.
- **Mapping** — getMapping (VC_BC03_fetchConfig.py:289) consumes DEFINITION, DOMAIN, VARIABLE, NDKEY, FILENAME, FIELDNAME, OPERTYPE, PARAMETER, and any SUPPTIMEFLG column. Definition rows are keyed by Excel row number, so preserving order keeps rule precedence intact.
- **DomainsSetting** — getDomainsSetting (VC_BC03_fetchConfig.py:383) reads DOMAIN, SEQFIELD, SORTKEYS, splitting SORTKEYS on commas and auto-appending USUBJID when missing.
- **Sites** — getSites (VC_BC03_fetchConfig.py:418) maps COL_SITENAME to COL_SITECODE, supplying the SITEID remap used in VC_PS01_makeInputCSV.py.
- **Combine & Combine_process** — getCombineInfo (VC_BC03_fetchConfig.py:432) joins FILENAME to FUNCTION and step parameters (PARA1–PARA8). The experimental VC_OP06_combine.py reuses the same schema to test merges outside the main pipeline.
- **Refactoring** — getRefactoringInfo (VC_BC03_fetchConfig.py:274) pairs FILENAME with FUNCTION callbacks for optional per-file post-processing.

### Secondary workbooks
- studySpecific/CIRCULATE/CIRCULATE_Mapping仕様書.xlsx mirrors the operational workbook for documentation only; none of the scripts import it. Any drift between this reference file and CONFIG_NAME is harmless unless analysts rely on it for manual reviews.
## Generated Artefacts
- Cleaning stage: timestamped folder `studySpecific/CIRCULATE/02_Cleaning/cleaning_dataset_YYYYMMDDhhmmss` containing `C-*.csv` plus `deletedCols/`, `deletedRows/` snapshots.
- Format stage: `03_Format/format_dataset_*` with `F-*.csv` files, optional combine outputs.
- SDTM stage: `04_SDTM/sdtm_dataset_*` per-domain CSVs ready for downstream packaging.
- Input files: `05_Inputfile` contains curated CSVs used to assemble json packages (`PAGEID`, `RECORDID`, and site remapping handled in `VC_PS01_makeInputCSV.py:13`).
- Submission package: `06_Inputpackage/m5/m5/datasets/[UAT]CIRCULATE/tabulations/` holds `sdtm/crf/*.json` (subject-level payloads) and zipped archive `m5.zip` created in `VC_PS02_csv2json.py:22`.

## Database Touchpoints
- Metadata tables: `VC_OP02_insertCodeList.py:13` creates `CODELIST_TABLE_NAME` (`VC_BC01_constant.py:31`), `VC_OP03_insertMetadata.py:38` stages into `{METADATA_TABLE_NAME, METADATA_TABLE_NAME}_STAGING`, and `VC_OP04_format.py` materialises views/temporary tables from these structures.
- Index strategy toggled via constants (`ENABLE_PERFORMANCE_INDEXES`, etc.) inside `VC_OP04_format.py:55`.

## Execution Notes
- Run modules sequentially after verifying `RAW_DATA_ROOT_PATH` and MySQL credentials inside `VC_BC01_constant.py`.
- Each operation prints active timestamped folders; downstream steps auto-discover the latest dataset via `find_latest_timestamped_path` (`VC_BC02_baseUtils.py:102`).
- Study-specific derivations from `VC_BC05_studyFunctions.py` are referenced by name in the `Mapping` sheet `OPERTYPE` column.

## Useful Commands
```powershell
# Clean → SDTM → Package
python VC_OP01_cleaning.py
python VC_OP02_insertCodeList.py
python VC_OP03_insertMetadata.py
python VC_OP04_format.py
python VC_OP05_mapping.py
python VC_PS01_makeInputCSV.py
python VC_PS02_csv2json.py
```



