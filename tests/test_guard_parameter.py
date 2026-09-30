"""ガード条件（&FIELD:VALUE の行）を含む PARAMETER は、どの OPERTYPE でも改行を $$$ に変換する（カンマは触らない）。"""
import VC_BC03_fetchConfig as fc
from wb_helpers import set_rows

HDR = 2


def _params(wb, rows):
    set_rows(wb["Mapping"], HDR, rows)
    ss = fc.getSheetSetting(wb)
    mapping, _ = fc.getMapping(wb, ss)
    return {var: cfg[fc.COL_PARAMETER] for grp in mapping["SS"].values() for var, cfg in grp.items()}


def test_guard_lines_split_for_literal_opertypes(demo_wb):
    p = _params(demo_wb, [
        ("G1", "SS", "SSTESTCD", None, "LSVDAT", None, "DEF", "FIXED\n&OUTCOME:Y"),
        (None, "SS", "SSORRES", None, None, "LSVDAT", "FIX", "&OUTCOME:Y\n&LSVDAT:not null"),
        (None, "SS", "SSSTRESC", None, None, "LSVDAT", "TPL", "P{}Y, ok\n&OUTCOME:Y"),
        (None, "SS", "SSDTC", None, None, "LSVDAT", "SEL", "LSVDAT:x\n&OUTCOME:!N"),
    ])
    assert p == {"SSTESTCD": "FIXED$$$&OUTCOME:Y",
                 "SSORRES": "&OUTCOME:Y$$$&LSVDAT:not null",
                 "SSSTRESC": "P{}Y, ok$$$&OUTCOME:Y",
                 "SSDTC": "LSVDAT:x$$$&OUTCOME:!N"}


def test_literal_without_guard_untouched(demo_wb):
    p = _params(demo_wb, [("G1", "SS", "SSTESTCD", None, "LSVDAT", None, "DEF", "a & b\nline2")])
    assert p == {"SSTESTCD": "a & b\nline2"}
