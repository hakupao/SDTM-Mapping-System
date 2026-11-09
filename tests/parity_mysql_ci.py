"""mysql_ci_key 与 MySQL utf8mb4_general_ci 的一致性核对（普通脚本，需要 MySQL；不被 pytest 收集）。

1. 字符核对：对 U+0000..U+FFFF（除代理区）每个字符和几个 BMP 外字符，
   mysql_ci_key(ch) 必须等于 MySQL WEIGHT_STRING(ch COLLATE utf8mb4_general_ci) 对应的字符。
2. 对库里每个 vc05_*_metadata / vc05_*_codelist 表的 FORMVAL、METAVAL、CODE、VALUE_EN、CODELISTID：
   - 分组核对：MySQL GROUP BY col 的每组成员集合 == 按 mysql_ci_key 分组的成员集合
   - 排序核对：MySQL ORDER BY col 的结果映射成键序列后必须非降序

用法: python tests/parity_mysql_ci.py      全部 OK 时最后一行 PARITY OK，否则打印前 20 例并退出 1
"""
import sys
from collections import defaultdict
from pathlib import Path

PIPELINE = Path(__file__).resolve().parent.parent / 'pipeline'
sys.path.insert(0, str(PIPELINE))

import mysql.connector  # noqa: E402

from VC_BC01_constant import DB_DATABASE, DB_HOST, DB_PASSWORD, DB_USER  # noqa: E402
from sdtm_sqlite import mysql_ci_key  # noqa: E402

COLUMNS = ('FORMVAL', 'METAVAL', 'CODE', 'VALUE_EN', 'CODELISTID')
COLL = 'utf8mb4_general_ci'
MAX_EXAMPLES = 20


def _dec(hexstr):
    return bytes.fromhex(hexstr).decode('utf-8')


def _targets(cur):
    cur.execute(
        "SELECT TABLE_NAME, COLUMN_NAME FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() "
        r"AND (TABLE_NAME LIKE 'vc05\_%\_metadata' OR TABLE_NAME LIKE 'vc05\_%\_codelist') "
        "AND COLUMN_NAME IN (" + ','.join(['%s'] * len(COLUMNS)) + ") "
        "ORDER BY TABLE_NAME, COLUMN_NAME", COLUMNS)
    return cur.fetchall()


def check_chars(cur):
    """逐字符比较键与 MySQL 权重，返回不一致列表 [(字符, 键, MySQL 权重字符)]。"""
    chars = [chr(cp) for cp in range(0x10000) if not 0xD800 <= cp <= 0xDFFF]
    chars += ['\U00010000', '\U0001F600', '\U0001F603', '\U00020000', '\U0010FFFF']
    bad = []
    for i in range(0, len(chars), 500):
        chunk = chars[i:i + 500]
        sql = ' UNION ALL '.join(
            f"SELECT HEX(WEIGHT_STRING(CONVERT(UNHEX('{ch.encode('utf-8').hex()}') USING utf8mb4) "
            f"COLLATE {COLL}))" for ch in chunk)
        cur.execute(sql)
        for ch, (w,) in zip(chunk, cur.fetchall()):
            expected = bytes.fromhex(w).decode('utf-16-be')
            if ch == ' ':
                expected = ''  # PAD SPACE：单独一个空格等于空串
            if mysql_ci_key(ch) != expected:
                bad.append((ch, mysql_ci_key(ch), expected))
    return len(chars), bad


def check_column(cur, table, col):
    """返回 (不同值个数, 分组不一致列表, 排序不一致列表)。"""
    # 先把不同的二进制值放进临时表，大表只扫一遍
    cur.execute("DROP TEMPORARY TABLE IF EXISTS parity_vals")
    cur.execute(f"CREATE TEMPORARY TABLE parity_vals (b LONGBLOB) "
                f"SELECT DISTINCT BINARY `{col}` AS b FROM `{table}` WHERE `{col}` IS NOT NULL")
    v = f"CONVERT(b USING utf8mb4) COLLATE {COLL}"
    cur.execute("SELECT HEX(b) FROM parity_vals")
    values = [_dec(r[0]) for r in cur.fetchall()]
    # MySQL 的分组：每组成员（不同的二进制值）
    cur.execute(f"SELECT GROUP_CONCAT(HEX(b) SEPARATOR ',') FROM parity_vals GROUP BY {v}")
    mysql_groups = {frozenset(_dec(h) for h in row[0].split(',')) for row in cur.fetchall()}

    by_key = defaultdict(set)
    for val in values:
        by_key[mysql_ci_key(val)].add(val)
    py_groups = {frozenset(s) for s in by_key.values()}

    group_bad = []
    for g in mysql_groups - py_groups:
        group_bad.append(('mysql', sorted(g), [mysql_ci_key(x) for x in sorted(g)]))
    for g in py_groups - mysql_groups:
        group_bad.append(('python', sorted(g), [mysql_ci_key(x) for x in sorted(g)]))

    # MySQL 的排序：不同二进制值按排序规则排列，键序列必须非降序（相等值之间次序不保证）
    cur.execute(f"SELECT HEX(b) FROM parity_vals ORDER BY {v}")
    order_bad = []
    prev_v, prev_k = None, None
    for val in (_dec(r[0]) for r in cur.fetchall()):
        kv = mysql_ci_key(val)
        if prev_k is not None and kv < prev_k:
            order_bad.append((prev_v, val, prev_k, kv))
        prev_v, prev_k = val, kv
    cur.execute("DROP TEMPORARY TABLE parity_vals")
    return len(values), group_bad, order_bad


def main():
    conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
                                   database=DB_DATABASE, charset='utf8mb4')
    cur = conn.cursor()
    cur.execute("SET SESSION group_concat_max_len = 1073741824")
    targets = _targets(cur)
    if not targets:
        print('no vc05_*_metadata / vc05_*_codelist tables found')
        return 1
    failures = 0
    n, char_bad = check_chars(cur)
    if char_bad:
        failures += 1
        print(f'FAIL  characters ({n} checked): {len(char_bad)} mismatches')
        for ch, key, expected in char_bad[:MAX_EXAMPLES]:
            print(f'      U+{ord(ch):04X} {ch!r}: key {key!r} != MySQL weight {expected!r}')
    else:
        print(f'OK    characters  ({n} checked against WEIGHT_STRING)')
    for table, col in targets:
        n, group_bad, order_bad = check_column(cur, table, col)
        if not group_bad and not order_bad:
            print(f'OK    {table}.{col}  ({n} distinct values)')
            continue
        failures += 1
        print(f'FAIL  {table}.{col}  ({n} distinct values): '
              f'{len(group_bad)} group mismatches, {len(order_bad)} order inversions')
        for side, members, keys in group_bad[:MAX_EXAMPLES]:
            print(f'      group only in {side}: {members!r} keys={keys!r}')
        for a, b, ka, kb in order_bad[:MAX_EXAMPLES]:
            print(f'      order: {a!r} before {b!r} in MySQL but key {ka!r} > {kb!r}')
    conn.close()
    if failures:
        print(f'PARITY FAILED ({failures} checks)')
        return 1
    print('PARITY OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
