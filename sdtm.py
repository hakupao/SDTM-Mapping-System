"""
SDTM ENSEMBLE Interactive Pipeline Console

在项目根目录输入 sdtm 即可启动交互式控制台。
"""

import subprocess
import sys
import os
import time
import json
from datetime import datetime

# 将项目根目录加入 sys.path 以便导入 VC_BC 模块
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from VC_BC02_baseUtils import PipelineProgress

# ── 常量 ──────────────────────────────────────────────────────────
W = 70

STEPS = [
    (1, 'VC_OP01_cleaning',       'OP01', 'Cleaning',       '数据清洗'),
    (2, 'VC_OP02_insertCodeList', 'OP02', 'InsertCodeList', '代码表插入'),
    (3, 'VC_OP03_insertMetadata', 'OP03', 'InsertMetadata', '元数据插入'),
    (4, 'VC_OP04_format',         'OP04', 'Format',         '数据格式化'),
    (5, 'VC_OP05_mapping',        'OP05', 'Mapping',        'SDTM映射'),
    (6, 'VC_PS01_makeInputCSV',   'PS01', 'MakeInputCSV',   '输入CSV生成'),
    (7, 'VC_PS02_csv2json',       'PS02', 'CSV2JSON',       'M5打包'),
]

# step_id → seq 快速查表
STEP_ID_MAP = {s[3].upper(): s[0] for s in STEPS}  # OP01->1, PS02->7

STAGE_DIRS = [
    ('02_Cleaning',     'cleaning_dataset'),
    ('03_Format',       'format_dataset'),
    ('04_SDTM',         'sdtm_dataset'),
    ('05_Inputfile',    'inputfile_dataset'),
    ('06_Inputpackage', 'inputpackage_dataset'),
]


# ── 项目配置 ──────────────────────────────────────────────────────
def load_config():
    """从当前工作目录加载 project.local.json（支持在不同项目目录下运行）。"""
    config_path = os.path.join(os.getcwd(), 'project.local.json')
    if os.path.isfile(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


# ── 数据状态 ──────────────────────────────────────────────────────
def get_status(study_id):
    """扫描各阶段的时间戳文件夹，返回状态列表。"""
    specific = os.path.join(ROOT_DIR, 'studySpecific', study_id)
    rows = []
    for folder, pattern in STAGE_DIRS:
        stage_path = os.path.join(specific, folder)
        if not os.path.isdir(stage_path):
            rows.append((folder, '-', '-'))
            continue
        ts_folders = sorted(
            [d for d in os.listdir(stage_path)
             if d.startswith(pattern + '-') and os.path.isdir(os.path.join(stage_path, d))],
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


# ── 执行流水线 ────────────────────────────────────────────────────
def run_steps(start, end, continue_on_error=False):
    selected = [s for s in STEPS if start <= s[0] <= end]
    if not selected:
        print(f'  [ERROR] 无效范围: {start}~{end}')
        return

    print()
    for seq, module, step_id, name, desc in selected:
        print(f'  [{seq}] {step_id}  {name:<16} {desc}')
    print()
    print(f'  共 {len(selected)} 个步骤')
    print('-' * W)

    results = []
    t0 = time.time()

    steps_info = [(s[2], s[4]) for s in selected]  # (step_id, desc_cn)
    pp = PipelineProgress(len(selected), steps_info)

    for i, (seq, module, step_id, name, desc) in enumerate(selected):
        pp.begin_step(i)

        ts = time.time()
        proc = subprocess.Popen(
            [sys.executable, '-u', os.path.join(ROOT_DIR, f'{module}.py')],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            cwd=os.getcwd(),
        )

        for raw_line in proc.stdout:
            line = raw_line.decode('utf-8', errors='replace').rstrip('\r\n')
            if pp.parse_and_update(line):
                continue
            pp.print_line(line)

        proc.wait()
        pp.end_step()
        elapsed = time.time() - ts

        ok = proc.returncode == 0
        status = 'OK' if ok else f'FAIL (exit {proc.returncode})'
        results.append((seq, step_id, status, elapsed))

        if not ok:
            print(f'\n  [ERROR] {step_id} 失败 (exit {proc.returncode})')
            if not continue_on_error:
                print(f'  流程中断。')
                break

    total = time.time() - t0
    pp.cleanup()

    # 摘要
    print()
    print('=' * W)
    print('  Pipeline 执行摘要')
    print('=' * W)
    print(f'  {"#":<4} {"步骤":<8} {"状态":<20} {"耗时":>8}')
    print('-' * W)
    for seq, step_id, status, elapsed in results:
        mark = ' ' if status == 'OK' else '!'
        print(f' {mark}{seq:<4} {step_id:<8} {status:<20} {elapsed:>7.1f}s')
    print('-' * W)
    print(f'  总耗时: {total:.1f}s')
    failed = [r for r in results if r[2] != 'OK']
    if failed:
        print(f'  失败: {", ".join(r[1] for r in failed)}')
    else:
        print(f'  全部 {len(results)} 步成功')
    print('=' * W)


# ── 解析 run 参数 ─────────────────────────────────────────────────
def parse_run_args(parts):
    """
    解析 run 子命令参数，返回 (start, end, continue_flag)
    支持:  run  /  run all  /  run 3  /  run 3 5  /  run op03  /  run op03 ps01
           任意后缀 --continue
    """
    cont = '--continue' in parts
    args = [p for p in parts if p != '--continue']

    if not args or args[0] in ('all', ''):
        return 1, 7, cont

    def to_seq(token):
        token_upper = token.upper()
        if token_upper in STEP_ID_MAP:
            return STEP_ID_MAP[token_upper]
        try:
            n = int(token)
            if 1 <= n <= 7:
                return n
        except ValueError:
            pass
        return None

    s = to_seq(args[0])
    if s is None:
        print(f'  [ERROR] 无法识别步骤: {args[0]}')
        return None, None, cont

    if len(args) >= 2:
        e = to_seq(args[1])
        if e is None:
            print(f'  [ERROR] 无法识别步骤: {args[1]}')
            return None, None, cont
        return s, e, cont

    return s, 7, cont


# ── 命令处理 ──────────────────────────────────────────────────────
def cmd_help():
    print()
    print('  run [all]            全部运行 (OP01 ~ PS02)')
    print('  run <n>              从第 n 步开始')
    print('  run <n> <m>          运行第 n ~ m 步')
    print('  run op03             从 OP03 开始 (支持步骤ID)')
    print('  run op03 ps01        运行 OP03 ~ PS01')
    print('  run ... --continue   失败后继续执行后续步骤')
    print()
    print('  status               查看各阶段数据状态')
    print('  list                 列出所有步骤')
    print('  help                 显示本帮助')
    print('  exit / quit          退出')
    print()


def cmd_list():
    print()
    for seq, module, step_id, name, desc in STEPS:
        print(f'  [{seq}] {step_id}  {name:<16} {desc}')
    print()


def cmd_status(study_id):
    rows = get_status(study_id)
    print()
    print(f'  {"阶段":<20} {"最新运行时间":<22} {"历史版本"}')
    print('  ' + '-' * (W - 4))
    for folder, latest, count in rows:
        mark = ' ' if latest != '-' else '?'
        print(f' {mark}{folder:<20} {latest:<22} {count}')
    print()


def cmd_run(parts):
    start, end, cont = parse_run_args(parts)
    if start is None:
        return
    run_steps(start, end, continue_on_error=cont)


# ── 欢迎画面 ──────────────────────────────────────────────────────
def print_banner(study_id):
    print()
    print('=' * W)
    print('  \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2557   \u2588\u2588\u2588\u2557')
    print('  \u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u255a\u2550\u2550\u2588\u2588\u2554\u2550\u2550\u255d\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2551')
    print('  \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2551  \u2588\u2588\u2551   \u2588\u2588\u2551   \u2588\u2588\u2554\u2588\u2588\u2588\u2588\u2554\u2588\u2588\u2551')
    print('  \u255a\u2550\u2550\u2550\u2550\u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2551   \u2588\u2588\u2551   \u2588\u2588\u2551\u255a\u2588\u2588\u2554\u255d\u2588\u2588\u2551')
    print('  \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d   \u2588\u2588\u2551   \u2588\u2588\u2551 \u255a\u2550\u255d \u2588\u2588\u2551')
    print('  \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d\u255a\u2550\u2550\u2550\u2550\u2550\u255d    \u255a\u2550\u255d   \u255a\u2550\u255d     \u255a\u2550\u255d  Pipeline Console')
    print()
    print(f'  Study: {study_id}')
    print(f'  输入 help 查看可用命令, 输入 exit 退出')
    print('=' * W)


# ── 主循环 ────────────────────────────────────────────────────────
def main():
    cfg = load_config()
    study_id = cfg.get('STUDY_ID', 'UNKNOWN')

    # 如果带了命令行参数，直接执行不进入交互模式
    if len(sys.argv) > 1:
        arg_line = ' '.join(sys.argv[1:])
        dispatch(arg_line, study_id)
        return

    print_banner(study_id)

    while True:
        try:
            line = input('\nsdtm> ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\n  Bye!')
            break

        if not line:
            continue

        dispatch(line, study_id)


def dispatch(line, study_id):
    parts = line.split()
    cmd = parts[0].lower()

    if cmd in ('exit', 'quit', 'q'):
        print('  Bye!')
        sys.exit(0)
    elif cmd == 'help':
        cmd_help()
    elif cmd == 'list':
        cmd_list()
    elif cmd == 'status':
        cmd_status(study_id)
    elif cmd == 'run':
        cmd_run(parts[1:])
    else:
        print(f'  未知命令: {cmd}  (输入 help 查看可用命令)')


if __name__ == '__main__':
    main()
