"""A4：抽取列按第 2 行的列名定位，不要求物理连续、也不要求与 SheetSetting 同序。"""
import VC_BC03_fetchConfig as fc


def _add_extraction(wb):
    """Process: I 列 = EX_A（DATAEXTRACTION 起点），J 列 = 備考（不在 SheetSetting），K 列 = EX_B。
    SheetSetting 里 Process 行按 EX_B、EX_A 的顺序登记（与物理列序相反）。"""
    ss_ws, pr = wb["SheetSetting"], wb["Process"]
    ss_ws.cell(row=1, column=11).value = "Col I"
    ss_ws.cell(row=1, column=12).value = "Col J"
    proc_row = next(r for r in range(2, ss_ws.max_row + 1) if ss_ws.cell(row=r, column=1).value == "Process")
    ss_ws.cell(row=proc_row, column=11).value = "EX_B"
    ss_ws.cell(row=proc_row, column=12).value = "EX_A"
    pr.cell(row=1, column=9).value = "DATAEXTRACTION"
    pr.cell(row=2, column=9).value = "EX_A"
    pr.cell(row=2, column=10).value = "備考"
    pr.cell(row=2, column=11).value = "EX_B"
    pr.cell(row=3, column=9).value = "○"    # RGST.SubjectId → EX_A
    pr.cell(row=3, column=10).value = "メモ"  # 備考列的内容不能被当成抽取标记
    pr.cell(row=3, column=11).value = "○"   # RGST.SubjectId → EX_B
    pr.cell(row=5, column=11).value = "○"   # RGST.SEXCD → EX_B


def test_extraction_columns_non_contiguous_and_reordered(demo_wb):
    _add_extraction(demo_wb)
    _, _, chk, ex_fields = fc.getProcess(demo_wb, fc.getSheetSetting(demo_wb))
    assert chk["RGST"] == {"EX_A": {"SubjectId": ""}, "EX_B": {"SubjectId": "", "SEXCD": ""}}
    assert ex_fields.get("RGST", []) == []


def test_process_without_dataextraction_has_no_extraction(demo_wb):
    """DEMO 原样没有 DATAEXTRACTION 标记：getProcess 不应该抽取任何列，但正常解析仍要工作。"""
    _, transFields, chk, _ = fc.getProcess(demo_wb, fc.getSheetSetting(demo_wb))
    assert chk == {}
    assert "RGST" in transFields
