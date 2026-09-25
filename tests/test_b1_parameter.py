"""B1：只有 FLG / IIF 的参数和 CYCLE(...) 才把逗号 / 换行换成 $$$；其余是字面值，原样保留。"""
import VC_BC03_fetchConfig as fc
from wb_helpers import set_rows

HDR = 2  # DEMO 的 Mapping 从第 2 行起是数据


def _params(wb, rows):
    set_rows(wb["Mapping"], HDR, rows)
    ss = fc.getSheetSetting(wb)
    mapping, _ = fc.getMapping(wb, ss)
    return {var: cfg[fc.COL_PARAMETER] for grp in mapping["SS"].values() for var, cfg in grp.items()}


def test_literal_parameters_keep_commas_and_newlines(demo_wb):
    p = _params(demo_wb, [
        ("G1", "SS", "SSTESTCD", None, "LSVDAT", None, "DEF", "in 60 days, the patient"),
        (None, "SS", "SSTEST", None, None, None, "DEF", "line1\nline2"),
        (None, "SS", "SSORRES", None, None, "LSVDAT", "PRF", "A,B-"),
        (None, "SS", "SSSTRESC", None, None, "LSVDAT", "SEL", "LSVDAT:x,y"),
    ])
    assert p == {"SSTESTCD": "in 60 days, the patient", "SSTEST": "line1\nline2",
                 "SSORRES": "A,B-", "SSSTRESC": "LSVDAT:x,y"}


def test_multi_segment_parameters_still_converted(demo_wb):
    p = _params(demo_wb, [
        ("G1", "SS", "SSORRES", None, "LSVDAT", "LSVDAT", "FLG", "1:A,2:B"),
        (None, "SS", "SSSTRESC", None, None, "LSVDAT", "IIF", "LSVDAT:1\nLSVDAT:2"),
    ])
    assert p == {"SSORRES": "1:A$$$2:B", "SSSTRESC": "LSVDAT:1$$$LSVDAT:2"}


def test_def_in_cycle_still_converted(demo_wb):
    p = _params(demo_wb, [("G1", "SS", "SSTESTCD", None, "LSVDAT", None, "DEF", "CYCLE(A,B)")])
    assert p == {"SSTESTCD": "CYCLE(A$$$B)"}


def test_flg_in_cycle_still_converted(demo_wb):
    p = _params(demo_wb, [("G1", "SS", "SSORRES", None, "LSVDAT", "LSVDAT", "FLG", "CYCLE(1:A,1:B)")])
    assert p == {"SSORRES": "CYCLE(1:A$$$1:B)"}


def test_cob_trailing_comma_separator_unchanged(demo_wb):
    p = _params(demo_wb, [("G1", "SS", "SSORRES", None, "LSVDAT", "LSVDAT", "COB", ":,")])
    assert p == {"SSORRES": ":,"}
