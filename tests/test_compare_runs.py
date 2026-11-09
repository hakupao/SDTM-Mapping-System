"""tests/compare_runs.py 的两目录模式与 --help。"""
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import compare_runs

SCRIPT = Path(__file__).resolve().parent / 'compare_runs.py'


def _tree(root, csv_text='a,b\r\n1,2\r\n', zip_time=(2020, 1, 1, 0, 0, 0)):
    root.mkdir(parents=True)
    (root / 'sub').mkdir()
    (root / 'sub' / 'DM.csv').write_text(csv_text, encoding='utf-8-sig')
    (root / 'run.log').write_text(str(zip_time), encoding='utf-8')   # *.log 不比较
    with zipfile.ZipFile(root / 'm5.zip', 'w') as z:
        z.writestr(zipfile.ZipInfo('m5/dm.json', date_time=zip_time), '{"a": 1}')
    return root


def test_missing_directory_fails(tmp_path, capsys):
    a = _tree(tmp_path / 'a')
    assert compare_runs.main([str(a), str(tmp_path / 'nope')]) == 1
    assert compare_runs.main([str(tmp_path / 'x'), str(tmp_path / 'y')]) == 1
    assert 'not an existing directory' in capsys.readouterr().out


def test_identical_dirs_pass(tmp_path):
    assert compare_runs.main([str(_tree(tmp_path / 'a')), str(_tree(tmp_path / 'b'))]) == 0


def test_differing_csv_fails(tmp_path, capsys):
    a = _tree(tmp_path / 'a')
    b = _tree(tmp_path / 'b', csv_text='a,b\r\n1,3\r\n')
    assert compare_runs.main([str(a), str(b)]) == 1
    assert 'sub/DM.csv: content differs' in capsys.readouterr().out


def test_zip_timestamps_ignored(tmp_path):
    a = _tree(tmp_path / 'a')
    b = _tree(tmp_path / 'b', zip_time=(2024, 6, 30, 12, 34, 56))
    assert (a / 'm5.zip').read_bytes() != (b / 'm5.zip').read_bytes()
    assert compare_runs.main([str(a), str(b)]) == 0


def test_help_on_cp932_console():
    env = dict(os.environ, PYTHONIOENCODING='cp932')
    env.pop('PYTHONUTF8', None)
    r = subprocess.run([sys.executable, str(SCRIPT), '--help'], env=env, capture_output=True)
    assert r.returncode == 0, r.stderr
    assert b'usage' in r.stdout
