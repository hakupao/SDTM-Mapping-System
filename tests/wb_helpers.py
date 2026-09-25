"""在内存里改 DEMO 工作簿的小工具。"""


def set_rows(ws, start_row, rows):
    """从 start_row 起覆盖写入 rows，并清空其后原有的数据行。"""
    for r in range(start_row, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            ws.cell(row=r, column=c).value = None
    for i, row in enumerate(rows):
        for j, value in enumerate(row, start=1):
            ws.cell(row=start_row + i, column=j).value = value


def append_rows(ws, rows):
    """在最后一行之后追加 rows，返回第一条新行的 Excel 行号。"""
    first = ws.max_row + 1
    for i, row in enumerate(rows):
        for j, value in enumerate(row, start=1):
            ws.cell(row=first + i, column=j).value = value
    return first
