"""C2：Combine 与 Files(○) 同名 = 在 Files 产物上加工后覆盖，F-xx.csv 必须已由主循环写出。"""
import pytest

import VC_OP04_format as op04


def test_overlay_detected_when_files_output_exists(tmp_path):
    (tmp_path / "F-DM.csv").write_text("SUBJID\n", encoding="utf-8")
    assert op04.check_combine_overlays(["DM", "REV_DS"], {"DM", "RGST"}, str(tmp_path)) == ["DM"]


def test_overlay_without_files_output_raises(tmp_path):
    with pytest.raises(RuntimeError, match="F-DM.csv"):
        op04.check_combine_overlays(["DM"], {"DM"}, str(tmp_path))


def test_overlay_ignores_names_not_in_files(tmp_path):
    """Files 中标 × 的行不进 fileDict，同名 Combine 不算覆写。"""
    assert op04.check_combine_overlays(["DM"], {"RGST"}, str(tmp_path)) == []
