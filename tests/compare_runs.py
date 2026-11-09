"""比较两次 pipeline 运行的输出文件夹（仅标准库）。

用法:
    python tests/compare_runs.py <dirA> <dirB>
    python tests/compare_runs.py --study <STUDY> [--root <STUDIES_ROOT>]

*.csv 逐字节比较；*.zip 比较成员名集合与各成员内容（忽略 zip 时间戳）；忽略 *.log。
全部一致退出码 0，否则打印差异文件清单并退出 1。
"""
import argparse
import json
import os
import re
import sys
import zipfile
from pathlib import Path

STAGES = ['02_Cleaning', '03_Format', '04_SDTM', '05_Inputfile', '06_Inputpackage']
TS_RE = re.compile(r'-(\d{14})$')


def _collect(root):
    files = {}
    for p in root.rglob('*'):
        if p.is_file() and p.suffix.lower() in ('.csv', '.zip'):
            files[p.relative_to(root).as_posix()] = p
    return files


def _zip_members(path):
    with zipfile.ZipFile(path) as z:
        return {i.filename: z.read(i) for i in z.infolist() if not i.is_dir()}


def compare_dirs(dir_a, dir_b):
    """返回差异描述列表（空列表 = 完全一致）。"""
    a, b = _collect(Path(dir_a)), _collect(Path(dir_b))
    diffs = []
    for rel in sorted(set(a) | set(b)):
        if rel not in a:
            diffs.append(f'{rel}: only in B')
        elif rel not in b:
            diffs.append(f'{rel}: only in A')
        elif rel.lower().endswith('.zip'):
            try:
                ma, mb = _zip_members(a[rel]), _zip_members(b[rel])
            except zipfile.BadZipFile:
                diffs.append(f'{rel}: bad zip')
                continue
            if set(ma) != set(mb):
                diffs.append(f'{rel}: zip member names differ')
                continue
            bad = [n for n in sorted(ma) if ma[n] != mb[n]]
            if bad:
                diffs.append(f'{rel}: zip members differ: {", ".join(bad)}')
        elif a[rel].read_bytes() != b[rel].read_bytes():
            diffs.append(f'{rel}: content differs')
    return diffs


def _resolve_root(root):
    if root:
        return Path(root)
    cfg = os.environ.get('PROJECT_CONFIG_PATH') or str(Path(__file__).resolve().parent.parent / 'project.local.json')
    with open(cfg, encoding='utf-8') as f:
        val = json.load(f)['STUDIES_ROOT_PATH']
    p = Path(val)
    return p if p.is_absolute() else Path(__file__).resolve().parent.parent / p


def _latest_two(stage_dir):
    found = []
    for d in stage_dir.iterdir() if stage_dir.is_dir() else []:
        m = TS_RE.search(d.name)
        if d.is_dir() and m:
            found.append((m.group(1), d))
    found.sort(key=lambda t: t[0])
    return [d for _, d in found[-2:]]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('dirs', nargs='*', help='dirA dirB')
    ap.add_argument('--study')
    ap.add_argument('--root')
    args = ap.parse_args(argv)

    if args.study:
        study_dir = _resolve_root(args.root) / args.study
        ok = True
        for stage in STAGES:
            pair = _latest_two(study_dir / stage)
            if len(pair) < 2:
                print(f'{stage}: FAIL need 2 timestamped folders, found {len(pair)}')
                ok = False
                continue
            diffs = compare_dirs(pair[0], pair[1])
            if diffs:
                ok = False
                print(f'{stage}: DIFF {len(diffs)} files  ({pair[0].name} vs {pair[1].name})')
                for d in diffs:
                    print(f'    {d}')
            else:
                print(f'{stage}: OK  ({pair[0].name} vs {pair[1].name})')
    elif len(args.dirs) == 2:
        diffs = compare_dirs(*args.dirs)
        ok = not diffs
        if diffs:
            print(f'DIFF {len(diffs)} files')
            for d in diffs:
                print(f'    {d}')
        else:
            print('OK')
    else:
        ap.error('give <dirA> <dirB> or --study <STUDY>')

    print('ALL IDENTICAL' if ok else 'DIFFERENCES FOUND')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
