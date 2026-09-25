import VC_BC03_fetchConfig as fc


def test_demo_parses(demo_wb):
    ss = fc.getSheetSetting(demo_wb)
    assert fc.getCaseDict(demo_wb, ss) == {"DEMO-001": "DEMO-001", "DEMO-002": "DEMO-002", "DEMO-003": "DEMO-003"}
    mapping, _ = fc.getMapping(demo_wb, ss)
    assert "SS" in mapping
    code_dict, _ = fc.getCodeListInfo(demo_wb, ss)
    assert code_dict["CL_SEX"] == {"M": "M", "F": "F"}
