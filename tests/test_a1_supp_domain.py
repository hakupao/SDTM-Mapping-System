"""A1：SUPPxx 直接去前缀取主域 xx，不再依赖前一行是谁。"""
import pytest

import VC_BC03_fetchConfig as fc
from wb_helpers import set_rows


def _mapping(wb, rows):
    set_rows(wb["Mapping"], 2, rows)
    return fc.getMapping(wb, fc.getSheetSetting(wb))[0]


def test_supp_row_not_adjacent_to_its_parent(demo_wb):
    m = _mapping(demo_wb, [
        ("G1", "CM", "CMTRT", None, "LSVDAT", "LSVDAT", "FIX", None),
        ("G2", "SS", "SSTESTCD", None, "LSVDAT", None, "DEF", "X"),
        (None, "SUPPCM", "QVAL", None, None, "LSVDAT", "FIX", None),
    ])
    assert "QVAL" in m["CM"][3]      # 键是所在组 DEFINITION 行的行号：SUPPCM 行属于第 3 行的 G2
    assert "QVAL" not in m["SS"][3]


def test_supp_row_adjacent_still_works(demo_wb):
    m = _mapping(demo_wb, [
        ("G1", "SS", "SSTESTCD", None, "LSVDAT", None, "DEF", "X"),
        (None, "SUPPSS", "QVAL2", None, None, "LSVDAT", "FIX", None),
    ])
    assert set(m["SS"][2]) == {"SSTESTCD", "QVAL2"}


def test_unknown_supp_domain_still_raises(demo_wb):
    with pytest.raises(fc.MappingConfigurationError) as exc:
        _mapping(demo_wb, [("G1", "SUPPZZ", "QVAL", None, "LSVDAT", "LSVDAT", "FIX", None)])
    assert "SUPPZZ" in str(exc.value) and exc.value.row == 2
