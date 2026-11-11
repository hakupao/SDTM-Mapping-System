"""sdtm.py 一次性命令的退出码：步骤失败或参数无法识别时非 0（供脚本 / CI 判断）。"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUDIES = ROOT / 'examples' / 'studies'


def _sdtm(tmp_path, *args):
    # 中转库指向一个空的临时文件：OP04 找不到 OP02/OP03 的表，在写任何输出之前以 1 退出
    cfg = tmp_path / 'project.local.json'
    cfg.write_text(json.dumps({'STUDIES_ROOT_PATH': str(STUDIES),
                               'SQLITE_PATH': str(tmp_path / 'empty.sqlite')}), encoding='utf-8')
    env = {**os.environ, 'PROJECT_CONFIG_PATH': str(cfg), 'PYTHONIOENCODING': 'utf-8'}
    env.pop('SDTM_STUDY', None)
    return subprocess.run([sys.executable, str(ROOT / 'sdtm.py'), 'DEMO', *args],
                          cwd=str(ROOT), env=env, capture_output=True, text=True, encoding='utf-8')


def test_run_exits_nonzero_when_a_step_fails(tmp_path):
    r = _sdtm(tmp_path, 'run', '4')
    assert 'OP04' in r.stdout and 'FAIL' in r.stdout, r.stdout + r.stderr
    assert r.returncode == 1


def test_run_exits_nonzero_on_unrecognised_step(tmp_path):
    r = _sdtm(tmp_path, 'run', 'nosuchstep')
    assert r.returncode == 1, r.stdout + r.stderr


def test_status_exits_zero(tmp_path):
    r = _sdtm(tmp_path, 'status')
    assert r.returncode == 0, r.stdout + r.stderr
