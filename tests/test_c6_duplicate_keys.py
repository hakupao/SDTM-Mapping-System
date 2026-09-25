"""C6：同键同值放行（多个 CODE → 同一个值是合法用法）；同键不同值报错。"""
import pytest

import VC_BC03_fetchConfig as fc
from wb_helpers import append_rows


def _codes(wb):
    return fc.getCodeListInfo(wb, fc.getSheetSetting(wb))[0]


def _cases(wb):
    return fc.getCaseDict(wb, fc.getSheetSetting(wb))


def test_codelist_same_key_same_value_passes(demo_wb):
    append_rows(demo_wb["CodeList"], [("CL_X", "E_A", "a", "SAME", "S1"), ("CL_X", "E_B", "b", "SAME", "S1")])
    assert _codes(demo_wb)["CL_X"] == {"SAME": "S1"}


def test_codelist_same_key_different_value_raises(demo_wb):
    first = append_rows(demo_wb["CodeList"], [("CL_Y", "A", "a", "K", "V1"), ("CL_Y", "B", "b", "K", "V2")])
    with pytest.raises(fc.MappingConfigurationError) as exc:
        _codes(demo_wb)
    assert exc.value.row == first + 1 and f"第{first}行" in str(exc.value)


def test_codelist_empty_valueen_is_not_checked(demo_wb):
    """CIRCULATE 的 COVAL：VALUEEN 为空、CODE 是自由文本，作者确认是有意的权宜存放。"""
    append_rows(demo_wb["CodeList"], [("COVAL", "text 1", None, None, None), ("COVAL", "text 2", None, None, "X")])
    _codes(demo_wb)


def test_casedict_same_subjid_same_usubjid_passes(demo_wb):
    append_rows(demo_wb["Patients"], [("DEMO-001", "DEMO-001", "○")])
    assert _cases(demo_wb)["DEMO-001"] == "DEMO-001"


def test_casedict_same_subjid_different_usubjid_raises(demo_wb):
    row = append_rows(demo_wb["Patients"], [("DEMO-009", "DEMO-001", "○")])
    with pytest.raises(fc.MappingConfigurationError) as exc:
        _cases(demo_wb)
    assert exc.value.row == row and "第2行" in str(exc.value)


def test_casedict_cross_row_is_ignored(demo_wb):
    append_rows(demo_wb["Patients"], [("DEMO-009", "DEMO-001", "×")])
    assert _cases(demo_wb)["DEMO-001"] == "DEMO-001"
