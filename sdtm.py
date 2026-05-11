"""
SDTM ENSEMBLE Pipeline Console.

在项目根目录输入 sdtm 即可启动 TUI；命令行参数仍保留原有 CLI 行为。
"""

import os
import sys
import time

# 优先从当前工作目录导入模块（sdtm 可能通过 PATH 从别处启动）。
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
_CWD = os.getcwd()
if _CWD not in sys.path:
    sys.path.insert(0, _CWD)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)


for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, 'reconfigure'):
        _stream.reconfigure(encoding='utf-8', errors='replace')

from VC_BC02_baseUtils import PROGRESS_MARKER, PipelineProgress
from sdtm_core import (
    STEP_ID_MAP,
    STEPS,
    W,
    get_status,
    iter_pipeline_events,
    load_config,
)


def run_steps(start, end, continue_on_error=False):
    """以传统 CLI 方式执行流水线步骤。"""
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

    steps_info = [(s[2], s[4]) for s in selected]
    pp = PipelineProgress(len(selected), steps_info)
    results = []
    total_start = time.time()

    try:
        for event in iter_pipeline_events(
            start,
            end,
            continue_on_error=continue_on_error,
            cwd=os.getcwd(),
        ):
            kind = event['kind']
            if kind == 'step_start':
                pp.begin_step(event['index'])
            elif kind == 'progress':
                marker = (
                    f"{PROGRESS_MARKER}{event['current']}/"
                    f"{event['total']}/{event['desc']}"
                )
                pp.parse_and_update(marker)
            elif kind == 'log':
                pp.print_line(event['line'])
            elif kind == 'step_end':
                pp.end_step()
                results.append(event)
                if event['status'] != 'OK':
                    print(f"\n  [ERROR] {event['step_id']} 失败 ({event['status']})")
                    if not continue_on_error:
                        print('  流程中断。')
            elif kind == 'error':
                print(f"  [ERROR] {event['message']}")
                return
    finally:
        pp.cleanup()

    total = time.time() - total_start
    print_run_summary(results, total)


def print_run_summary(results, total):
    """打印传统 CLI 执行摘要。"""
    print()
    print('=' * W)
    print('  Pipeline 执行摘要')
    print('=' * W)
    print(f'  {"#":<4} {"步骤":<8} {"状态":<20} {"耗时":>8}')
    print('-' * W)
    for result in results:
        mark = ' ' if result['status'] == 'OK' else '!'
        print(
            f" {mark}{result['seq']:<4} {result['step_id']:<8} "
            f"{result['status']:<20} {result['elapsed']:>7.1f}s"
        )
    print('-' * W)
    print(f'  总耗时: {total:.1f}s')
    failed = [r for r in results if r['status'] != 'OK']
    if failed:
        print(f'  失败: {", ".join(r["step_id"] for r in failed)}')
    else:
        print(f'  全部 {len(results)} 步成功')
    print('=' * W)


def parse_run_args(parts):
    """
    解析 run 子命令参数，返回 (start, end, continue_flag)。

    支持:
      run / run all / run 3 / run 3 5 / run op03 / run op03 ps01
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

    start = to_seq(args[0])
    if start is None:
        print(f'  [ERROR] 无法识别步骤: {args[0]}')
        return None, None, cont

    if len(args) >= 2:
        end = to_seq(args[1])
        if end is None:
            print(f'  [ERROR] 无法识别步骤: {args[1]}')
            return None, None, cont
        return start, end, cont

    return start, start, cont


def cmd_help():
    print()
    print('  tui                  启动 TUI 界面')
    print('  run [all]            全部运行 (OP01 ~ PS02)')
    print('  run <n>              仅运行第 n 步')
    print('  run <n> <m>          运行第 n ~ m 步')
    print('  run op03             仅运行 OP03 (支持步骤ID)')
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


def print_banner(study_id):
    print()
    print('=' * W)
    print('  ███████╗██████╗ ████████╗███╗   ███╗')
    print('  ██╔════╝██╔══██╗╚══██╔══╝████╗ ████║')
    print('  ███████╗██║  ██║   ██║   ██╔████╔██║')
    print('  ╚════██║██║  ██║   ██║   ██║╚██╔╝██║')
    print('  ███████║██████╔╝   ██║   ██║ ╚═╝ ██║')
    print('  ╚══════╝╚═════╝    ╚═╝   ╚═╝     ╚═╝  Pipeline Console')
    print()
    print(f'  Study: {study_id}')
    print('  输入 help 查看可用命令, 输入 exit 退出')
    print('=' * W)


def launch_tui():
    """启动 Textual TUI；缺少依赖时返回 False。"""
    try:
        from sdtm_tui import main as tui_main
    except ModuleNotFoundError as exc:
        if exc.name == 'textual':
            print('  [ERROR] 缺少 TUI 依赖 textual。请先运行: pip install -r requirements.txt')
            return False
        raise

    tui_main()
    return True


def run_shell(study_id):
    """保留原交互式 CLI shell。"""
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
    if cmd in ('tui', 'ui'):
        launch_tui()
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


def main():
    cfg = load_config()
    study_id = cfg.get('STUDY_ID', 'UNKNOWN')

    if len(sys.argv) > 1:
        first = sys.argv[1].lower()
        if first in ('tui', '--tui', 'ui', '--ui'):
            launch_tui()
            return
        if first in ('shell', 'cli', '--shell', '--cli'):
            run_shell(study_id)
            return

        arg_line = ' '.join(sys.argv[1:])
        dispatch(arg_line, study_id)
        return

    if not launch_tui():
        run_shell(study_id)


if __name__ == '__main__':
    main()
