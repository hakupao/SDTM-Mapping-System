"""
Shared SDTM console metadata, status helpers, and pipeline runner.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime

from VC_BC02_baseUtils import PIPELINE_ENV_KEY, PROGRESS_MARKER

W = 70

STEPS = [
    (1, 'VC_OP01_cleaning', 'OP01', 'Cleaning', '数据清洗'),
    (2, 'VC_OP02_insertCodeList', 'OP02', 'InsertCodeList', '代码表插入'),
    (3, 'VC_OP03_insertMetadata', 'OP03', 'InsertMetadata', '元数据插入'),
    (4, 'VC_OP04_format', 'OP04', 'Format', '数据格式化'),
    (5, 'VC_OP05_mapping', 'OP05', 'Mapping', 'SDTM映射'),
    (6, 'VC_PS01_makeInputCSV', 'PS01', 'MakeInputCSV', '输入CSV生成'),
    (7, 'VC_PS02_csv2json', 'PS02', 'CSV2JSON', 'M5打包'),
]

STEP_ID_MAP = {}
for _step in STEPS:
    STEP_ID_MAP[_step[2].upper()] = _step[0]
    STEP_ID_MAP[_step[3].upper()] = _step[0]

STAGE_DIRS = [
    ('02_Cleaning', 'cleaning_dataset'),
    ('03_Format', 'format_dataset'),
    ('04_SDTM', 'sdtm_dataset'),
    ('05_Inputfile', 'inputfile_dataset'),
    ('06_Inputpackage', 'inputpackage_dataset'),
]


def load_config(cwd=None):
    """从当前工作目录加载 project.local.json。"""
    base_dir = cwd or os.getcwd()
    config_path = os.path.join(base_dir, 'project.local.json')
    if os.path.isfile(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def get_status(study_id, cwd=None):
    """扫描各阶段的时间戳文件夹，返回状态列表。"""
    base_dir = cwd or os.getcwd()
    specific = os.path.join(base_dir, 'studySpecific', study_id)
    rows = []
    for folder, pattern in STAGE_DIRS:
        stage_path = os.path.join(specific, folder)
        if not os.path.isdir(stage_path):
            rows.append((folder, '-', '-'))
            continue
        ts_folders = sorted(
            [
                d for d in os.listdir(stage_path)
                if d.startswith(pattern + '-')
                and os.path.isdir(os.path.join(stage_path, d))
            ],
            reverse=True,
        )
        if ts_folders:
            latest = ts_folders[0]
            ts_part = latest[len(pattern) + 1:]
            try:
                dt = datetime.strptime(ts_part, '%Y%m%d%H%M%S')
                time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                time_str = ts_part
            rows.append((folder, time_str, f'{len(ts_folders)} 个版本'))
        else:
            rows.append((folder, '-', '-'))
    return rows


def selected_steps(start, end):
    """返回 start/end 范围内的流水线步骤。"""
    return [step for step in STEPS if start <= step[0] <= end]


def parse_progress_line(line):
    """解析子进程进度协议行；非进度行返回 None。"""
    if not line.startswith(PROGRESS_MARKER):
        return None

    parts = line[len(PROGRESS_MARKER):].split('/', 2)
    try:
        current = int(parts[0])
        total = int(parts[1])
    except (ValueError, IndexError):
        return {'current': 0, 'total': 0, 'desc': ''}

    return {
        'current': current,
        'total': total,
        'desc': parts[2] if len(parts) > 2 else '',
    }


def iter_pipeline_events(
    start,
    end,
    continue_on_error=False,
    cwd=None,
    stop_requested=None,
    on_process_start=None,
    on_process_end=None,
):
    """
    Run pipeline steps and yield event dictionaries for CLI/TUI renderers.

    Event kinds:
      pipeline_start, step_start, progress, log, step_end, pipeline_end, error
    """
    base_dir = cwd or os.getcwd()
    selected = selected_steps(start, end)
    if not selected:
        yield {'kind': 'error', 'message': f'无效范围: {start}~{end}'}
        return

    results = []
    pipeline_start = time.time()
    yield {'kind': 'pipeline_start', 'selected': selected}

    for index, (seq, module, step_id, name, desc) in enumerate(selected):
        if stop_requested and stop_requested():
            break

        yield {
            'kind': 'step_start',
            'index': index,
            'seq': seq,
            'module': module,
            'step_id': step_id,
            'name': name,
            'desc': desc,
        }

        step_start = time.time()
        env = {
            **os.environ,
            PIPELINE_ENV_KEY: '1',
            'PYTHONIOENCODING': 'utf-8',
        }
        proc = subprocess.Popen(
            [sys.executable, '-u', f'{module}.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=base_dir,
            env=env,
        )
        if on_process_start:
            on_process_start(proc)

        stopped = False
        try:
            for raw_line in proc.stdout:
                if stop_requested and stop_requested():
                    stopped = True
                    proc.terminate()
                    break

                line = raw_line.decode('utf-8', errors='replace').rstrip('\r\n')
                progress = parse_progress_line(line)
                if progress is not None:
                    yield {'kind': 'progress', 'step_id': step_id, **progress}
                else:
                    yield {'kind': 'log', 'step_id': step_id, 'line': line}

            if stopped:
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            else:
                proc.wait()
        finally:
            if on_process_end:
                on_process_end(proc)

        elapsed = time.time() - step_start
        if stopped:
            status = 'STOPPED'
            ok = False
        else:
            ok = proc.returncode == 0
            status = 'OK' if ok else f'FAIL (exit {proc.returncode})'

        result = {
            'seq': seq,
            'step_id': step_id,
            'status': status,
            'elapsed': elapsed,
            'ok': ok,
        }
        results.append(result)
        yield {'kind': 'step_end', **result}

        if stopped or (not ok and not continue_on_error):
            break

    total_elapsed = time.time() - pipeline_start
    failed = [result for result in results if not result['ok']]
    yield {
        'kind': 'pipeline_end',
        'results': results,
        'elapsed': total_elapsed,
        'failed': failed,
    }
