# Study folder template

Copy this folder to `<STUDIES_ROOT_PATH>/<STUDY_ID>/` and rename the files.

```
<STUDY_ID>/
├── <STUDY_ID>_OperationConf.xlsx   # required: the Excel mapping DSL (see main README)
├── VC_BC05_studyFunctions.py       # required: study-specific Python functions (may be minimal)
├── study.json                      # optional: per-study settings (see below)
├── 01_RawData/                     # raw CSV input (path can be changed in study.json)
├── 02_Cleaning/  03_Format/  04_SDTM/  05_Inputfile/  06_Inputpackage/   # pipeline outputs
└── 20_Doc/                         # study documents (EDC spec, protocol, design notes)
```

A folder is recognised as a study when it contains `<STUDY_ID>_OperationConf.xlsx`
or `study.json`.

## study.json

All keys are optional. Defaults are derived from the study id.

| Key | Default | Meaning |
|-----|---------|---------|
| `M5_PROJECT_NAME` | `<STUDY_ID>` | Project name written into the M5 package |
| `RAW_DATA_DIR` | `01_RawData` | Raw CSV directory, relative to the study folder |
| `RAW_DATA_ROOT_PATH` | – | Absolute raw CSV directory (overrides `RAW_DATA_DIR`) |
| `CODELIST_TABLE_NAME` | `VC05_<STUDY_ID>_CODELIST` | MySQL table for code lists |
| `METADATA_TABLE_NAME` | `VC05_<STUDY_ID>_METADATA` | MySQL table for metadata |
| `TRANSDATA_VIEW_NAME` | `VC05_<STUDY_ID>_TRANSDATA` | MySQL view for formatted data |

## Running

```bash
sdtm <STUDY_ID>                  # TUI for this study
sdtm <STUDY_ID> run 1 7          # run all steps
python run_pipeline.py --study <STUDY_ID>
```
