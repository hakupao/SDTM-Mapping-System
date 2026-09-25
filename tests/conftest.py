"""测试环境：VC_BC01_constant 在 import 时必须解析出一个研究，这里指向仓库自带的 DEMO。

必须在 import 任何 VC_* 模块之前设置环境变量，所以放在 conftest 顶层。
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
STUDIES = ROOT / "examples" / "studies"
DEMO_XLSX = STUDIES / "DEMO" / "DEMO_OperationConf.xlsx"

_cfg = Path(tempfile.mkdtemp(prefix="sdtm-tests-")) / "project.local.json"
_cfg.write_text(json.dumps({"STUDIES_ROOT_PATH": str(STUDIES)}), encoding="utf-8")
os.environ["PROJECT_CONFIG_PATH"] = str(_cfg)
os.environ["SDTM_STUDY"] = "DEMO"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# 注意：getMapping 会往模块级 STANDARD_FIELDS 里 append（A2 的全局状态问题，本次不改），
# 同一 pytest 进程里的测试共享它。测试不得断言 SUPPTIMEFLG 或 STANDARD_FIELDS 的内容。


@pytest.fixture
def demo_wb():
    """每个测试拿一份新的 DEMO 工作簿（内存中改，不写回磁盘）。"""
    return load_workbook(DEMO_XLSX)
