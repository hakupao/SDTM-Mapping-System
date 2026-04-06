"""
VAPORCONE 全流程一键运行脚本

用法:
    python run_pipeline.py                # 运行全部 7 步 (OP01 ~ PS02)
    python run_pipeline.py 3              # 从第 3 步 (OP03) 开始运行
    python run_pipeline.py 3 5            # 只运行第 3 ~ 5 步 (OP03 ~ OP05)
    python run_pipeline.py --continue     # 某步失败后继续运行后续步骤
    python run_pipeline.py --dry-run      # 只打印将要执行的步骤，不实际运行
"""

import subprocess
import sys
import time
import argparse

# 有序的步骤定义: (序号, 模块名, 步骤ID, 描述)
STEPS = [
    (1, 'VC_OP01_cleaning',        'OP01', 'Cleaning          - 数据清洗'),
    (2, 'VC_OP02_insertCodeList',  'OP02', 'InsertCodeList    - 代码表插入'),
    (3, 'VC_OP03_insertMetadata',  'OP03', 'InsertMetadata    - 元数据插入'),
    (4, 'VC_OP04_format',          'OP04', 'Format            - 数据格式化'),
    (5, 'VC_OP05_mapping',         'OP05', 'Mapping           - SDTM映射'),
    (6, 'VC_PS01_makeInputCSV',    'PS01', 'MakeInputCSV      - 输入CSV生成'),
    (7, 'VC_PS02_csv2json',        'PS02', 'CSV2JSON          - M5打包'),
]

W = 70


def run_pipeline(start=1, end=7, continue_on_error=False, dry_run=False):
    selected = [s for s in STEPS if start <= s[0] <= end]

    if not selected:
        print(f'[ERROR] 无效的步骤范围: {start} ~ {end} (有效范围: 1 ~ 7)')
        sys.exit(1)

    # 打印计划
    print()
    print('=' * W)
    print('  VAPORCONE Pipeline Runner')
    print('=' * W)
    print()
    for seq, module, step_id, desc in selected:
        print(f'  [{seq}] {step_id}  {desc}')
    print()
    if continue_on_error:
        print('  模式: --continue (某步失败后继续)')
    if dry_run:
        print('  模式: --dry-run (仅预览，不执行)')
        print('=' * W)
        return

    print(f'  共 {len(selected)} 个步骤')
    print('=' * W)

    # 执行
    results = []
    pipeline_start = time.time()

    for seq, module, step_id, desc in selected:
        print()
        print(f'>>> [{seq}/{end}] 启动 {step_id} ...')
        print()

        step_start = time.time()
        proc = subprocess.run(
            [sys.executable, f'{module}.py'],
            cwd=sys.path[0] or '.',
        )
        elapsed = time.time() - step_start

        success = proc.returncode == 0
        status = 'OK' if success else f'FAIL (exit {proc.returncode})'
        results.append((seq, step_id, status, elapsed))

        if not success:
            print()
            print(f'[ERROR] {step_id} 失败 (exit code: {proc.returncode})')
            if not continue_on_error:
                print(f'[ERROR] 流程中断。使用 --continue 可跳过失败步骤继续运行。')
                break

    # 汇总
    pipeline_elapsed = time.time() - pipeline_start
    print()
    print('=' * W)
    print('  Pipeline 执行摘要')
    print('=' * W)
    print(f'  {"#":<4} {"步骤":<8} {"状态":<18} {"耗时":>10}')
    print('-' * W)
    for seq, step_id, status, elapsed in results:
        print(f'  {seq:<4} {step_id:<8} {status:<18} {elapsed:>8.1f}s')
    print('-' * W)
    print(f'  总耗时: {pipeline_elapsed:.1f}s')

    failed = [r for r in results if not r[2].startswith('OK')]
    if failed:
        print(f'  失败步骤: {", ".join(r[1] for r in failed)}')
    else:
        print(f'  全部 {len(results)} 个步骤执行成功')
    print('=' * W)

    if failed:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='VAPORCONE 全流程运行器 (OP01 ~ PS02)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_pipeline.py              运行全部 7 步
  python run_pipeline.py 3            从第 3 步 (OP03) 开始
  python run_pipeline.py 3 5          只运行第 3 ~ 5 步
  python run_pipeline.py --continue   失败后继续
  python run_pipeline.py --dry-run    仅预览不执行
""",
    )
    parser.add_argument(
        'start', nargs='?', type=int, default=1,
        help='起始步骤序号 (1~7, 默认1)',
    )
    parser.add_argument(
        'end', nargs='?', type=int, default=None,
        help='结束步骤序号 (1~7, 默认=最后一步)',
    )
    parser.add_argument(
        '--continue', dest='continue_on_error', action='store_true',
        help='某步失败后继续运行后续步骤',
    )
    parser.add_argument(
        '--dry-run', dest='dry_run', action='store_true',
        help='仅打印执行计划，不实际运行',
    )

    args = parser.parse_args()
    end = args.end if args.end is not None else 7

    run_pipeline(
        start=args.start,
        end=end,
        continue_on_error=args.continue_on_error,
        dry_run=args.dry_run,
    )


if __name__ == '__main__':
    main()
