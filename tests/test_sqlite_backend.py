import pytest
from sdtm_sqlite import mysql_ci_key as k


def test_ci_key_case_and_trailing_space():
    assert k('Yes') == k('YES') == k('yes  ')
    assert k(None) is None
    assert k('   ') == k('') == ''
    assert k(' a') != k('a')            # 只忽略末尾空格，不忽略开头


def test_ci_key_latin_accents_fold():
    assert k('é') == k('E') and k('Ñ') == k('n')


def test_ci_key_japanese_not_folded():
    assert k('ガ') != k('カ')
    assert k('あ') != k('ア')


def test_ci_key_fullwidth_case_folds_but_not_width():
    assert k('ａ') == k('Ａ')
    assert k('Ａ') != k('A')


def test_ci_key_non_bmp_all_equal():
    assert k('😀') == k('😃')


def test_ci_key_order_matches_mysql():
    vals = ['chylous ascites', 'Grade II', 'anemia']
    assert sorted(vals, key=k) == ['anemia', 'chylous ascites', 'Grade II']


# 下面三条来自对 MySQL 5.7.44 全部 BMP 字符 WEIGHT_STRING 的逐个核对：
# 用 Python 的 upper()/NFD 推测折叠规则会在这些地方和 MySQL 不一致，所以改为内置权重表。

def test_ci_key_sharp_s_equals_s():
    assert k('ß') == k('s') == k('S')       # general_ci: ß = s（不是 ss）


def test_ci_key_greek_tonos_folds():
    assert k('ά') == k('Ά') == k('α') == k('Α')
    assert k('ΐ') == k('ι')


def test_ci_key_letters_unknown_to_mysql_not_case_folded():
    # Unicode 5.0 以后才有大小写配对的字母，MySQL 5.7 的表里不折叠
    assert k('ƀ') != k('Ƀ')
    assert k('ⱥ') != k('Ⱥ')


# ---------------------------------------------------------------------------
# SQLiteDatabaseManager
# ---------------------------------------------------------------------------
def _db(tmp_path):
    from sdtm_sqlite import SQLiteDatabaseManager
    db = SQLiteDatabaseManager(str(tmp_path / 'w.sqlite'), keep_work_tables=False)
    db.connect()
    return db


def test_codelist_case_duplicate_ignored(tmp_path):
    db = _db(tmp_path); db.create_codelist_table('CL')
    assert db.insert_codelist_rows('CL', [('COVAL', 'Yes', '', 'yes-en', ''),
                                          ('COVAL', 'YES', '', 'dup', '')]) == (1, 1)


def test_view_translates_case_and_space_insensitively(tmp_path):
    db = _db(tmp_path); db.create_codelist_table('CL'); db.create_metadata_table('MD')
    db.insert_codelist_rows('CL', [('COVAL', 'Yes ', '', 'YES-EN', 'Y')])
    db.load_metadata_rows('MD', [('F', 1, 'U1', 'S1', 'lbl', 'COVAL', 'YES', 'YES', 0, 'COVAL', ''),
                                 ('F', 2, 'U1', 'S1', 'lbl', 'COVAL', 'No', 'No', 0, 'COVAL', '')])
    db.create_transdata_view('TV', 'MD', 'CL')
    rows = db.cursor.execute('SELECT ROWNUM, TRANSVAL, SDTMVAL FROM TV ORDER BY ROWNUM').fetchall()
    assert rows == [(1, 'YES-EN', 'Y'), (2, 'No', '')]


def test_metadata_values_round_trip(tmp_path):
    db = _db(tmp_path); db.create_metadata_table('MD')
    odd = 'a\\b "q", line1\nline2 \U0001F600'
    assert db.load_metadata_rows('MD', [('F', 1, 'U1', 'S1', 'l', 'X', odd, odd, 0, '', '')]) == 1
    assert db.cursor.execute('SELECT No, METAVAL, FORMVAL, CHKFIELDID FROM MD').fetchall() == [(1, odd, odd, '')]


def test_ci_helpers_work_tables_and_indexes(tmp_path):
    db = _db(tmp_path)
    assert db.implicit_group_order is False and db.is_connected()
    assert db.ci_col('FORMVAL') == 'FORMVAL_K' and db.ci('x') == 'ci_key(x)'
    assert db.ci_literal("Yes  ") == "'" + k("Yes") + "'"
    assert db.ci_literal("a'B") == "'" + k("a'B").replace("'", "''") + "'"
    assert db.cursor.execute('SELECT ' + db.ci("'YES '")).fetchone()[0] == k('yes')
    db.create_codelist_table('CL'); db.create_metadata_table('MD')
    db.load_metadata_rows('MD', [('F-1', 1, 'U1', 'S1', 'l', 'X', 'v', 'v', 1, '', ''),
                                 ('F-1', 2, 'U1', 'S1', 'l', 'X', 'w', None, 0, '', '')])
    db.create_transdata_view('TV', 'MD', 'CL')
    assert db.create_performance_indexes('MD') == 3
    assert db.create_performance_indexes('MD') == 0
    name = db.create_temp_table_for_file('TV', 'F-1')
    assert name == 'work_f_1'
    cols = [d[0] for d in db.cursor.execute(f'SELECT * FROM {name}').description]
    assert {'FORMVAL_K', 'METAVAL_K', 'TRANSVAL_K'} <= set(cols)
    assert db.cursor.execute(f'SELECT COUNT(*) FROM {name}').fetchone() == (1,)
    db.cleanup_work_tables()
    assert not db.table_exists(name)
    db.disconnect()
    assert not db.is_connected()


def test_no_mysql_import():
    import subprocess, sys, os
    pipe = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pipeline')
    code = f"import sys; sys.path.insert(0, {pipe!r}); import sdtm_sqlite; assert 'mysql' not in sys.modules"
    assert subprocess.run([sys.executable, '-c', code]).returncode == 0


def test_rollback_mid_load_leaves_db_consistent(tmp_path):
    db = _db(tmp_path); db.create_metadata_table('MD')
    db.load_metadata_rows('MD', [('F', 1, 'U1', 'S1', 'l', 'X', 'keep', 'keep', 0, '', '')])

    def rows():
        yield (2, 'F', 2, 'U1', 'S1', 'l', 'X', 'gone', 'gone', 0, '', '', None, 'G', 'G')
        raise RuntimeError('boom')

    sql = ('INSERT INTO MD (No, FILENAME, ROWNUM, USUBJID, SUBJID, FIELDLBL, FIELDID, METAVAL, FORMVAL, '
           'DATETYPE, CODELISTID, CHKFIELDID, CODELISTID_K, FORMVAL_K, METAVAL_K) '
           'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)')
    try:
        db.connection.executemany(sql, rows())
    except RuntimeError:
        pass
    db.connection.rollback()
    assert db.connection.execute('PRAGMA integrity_check').fetchone() == ('ok',)
    assert db.connection.execute('SELECT METAVAL FROM MD').fetchall() == [('keep',)]
    db.connection.execute(sql, (3, 'F', 3, 'U1', 'S1', 'l', 'X', 'x', 'x', 0, '', '', None, 'X', 'X'))
    db.connection.rollback()
    assert db.connection.execute('SELECT COUNT(*) FROM MD').fetchone() == (1,)
    db.disconnect()


# ---------------------------------------------------------------------------
# OP04 query builders use the dialect hooks
# ---------------------------------------------------------------------------
def _op04_db(tmp_path, rows):
    db = _db(tmp_path); db.create_codelist_table('CL'); db.create_metadata_table('MD')
    db.load_metadata_rows('MD', rows)
    db.create_transdata_view('TV', 'MD', 'CL')
    return db


def _m(rownum, fieldid, val):
    return ('F', rownum, 'U1', 'S1', 'lbl', fieldid, val, val, 0, '', '')


def test_chk_order_case_insensitive(tmp_path):
    import VC_OP04_format as op04
    db = _op04_db(tmp_path, [_m(1, 'A', 'Grade II'), _m(1, 'B', 'chylous ascites')])
    q = op04.build_optimized_chk_query(
        db, 'F', ['t.`CHKTYPE`', 't.`CHKVALUE`'], ["'A'", "'B'"], {'T': ['A', 'B']},
        [], [], {}, {}, {}, 'TV')
    rows = db.cursor.execute(q).fetchall()
    assert [r[2] for r in rows] == ['chylous ascites', 'Grade II']


def test_otherdetails_metaval_case_insensitive(tmp_path):
    import VC_OP04_format as op04
    db = _op04_db(tmp_path, [_m(1, 'SEL', 'OTHER'), _m(1, 'TXT', 'free text')])
    q = op04.build_optimized_chk_query(
        db, 'F', ['t.`CHKTYPE`', 't.`CHKVALUE`'], ["'SEL'"], {'T': ['SEL']},
        [], [], {'TXT': 'SEL'}, {'SEL': 'Other'}, {}, 'TV')
    rows = db.cursor.execute(q).fetchall()
    header = [d[0] for d in db.cursor.description]
    assert rows and rows[0][header.index('OTHERDETAILS')] == 'free text'


def test_chk_order_and_otherdetails_exact_rows(tmp_path):
    """CHK 排序（ROWNUM, CHKTYPE, CHKVALUE 均不区分大小写、忽略末尾空格）与 OTHERDETAILS 的完整结果。"""
    import VC_OP04_format as op04
    db = _op04_db(tmp_path, [
        _m(2, 'A', 'x'),
        _m(1, 'B', 'banana'), _m(1, 'A', 'cherry'), _m(1, 'B', 'Apple '), _m(1, 'A', 'apricot'),
        _m(1, 'C', 'Zed'), _m(1, 'SEL', 'OTHER'), _m(1, 'TXT', 'free text'),
    ])
    q = op04.build_optimized_chk_query(
        db, 'F', ['t.`CHKTYPE`', 't.`CHKVALUE`'], ["'A'", "'B'", "'C'", "'SEL'"],
        {'beta': ['A', 'B'], 'Alpha': ['C'], 'sel': ['SEL']},
        [], [], {'TXT': 'SEL'}, {'SEL': 'Other '}, {}, 'TV')
    rows = db.cursor.execute(q).fetchall()
    assert [d[0] for d in db.cursor.description] == ['SUBJID', 'CHKTYPE', 'CHKVALUE', 'OTHERDETAILS']
    assert rows == [
        ('S1', 'Alpha', 'Zed', None),
        ('S1', 'beta', 'Apple ', None),
        ('S1', 'beta', 'apricot', None),
        ('S1', 'beta', 'banana', None),
        ('S1', 'beta', 'cherry', None),
        ('S1', 'sel', 'OTHER', 'free text'),
        ('S1', 'beta', 'x', None),
    ]


def test_chk_query_text_for_mysql_has_no_key_columns():
    import VC_OP04_format as op04
    from VC_BC02_baseUtils import MySQLDatabaseManager
    db = MySQLDatabaseManager.__new__(MySQLDatabaseManager)
    q = ' '.join(op04.build_optimized_chk_query(
        db, 'F', ['t.`CHKTYPE`', 't.`CHKVALUE`'], ["'SEL'"], {'T': ['SEL']},
        [], [], {'TXT': 'SEL'}, {'SEL': 'Other'}, {}, 'TV').split())
    assert '_K' not in q and 'ci_key' not in q
    assert "AND t.`METAVAL` = 'Other'" in q
    assert q.endswith('ORDER BY t.`ROWNUM`,t.`CHKTYPE`,t.`CHKVALUE`;')


def test_chk_query_on_sqlite_sorts_by_key_columns(tmp_path):
    """SQLite 的排序与 OTHERDETAILS 比较用预算键列，不逐行调用 ci_key()。"""
    import VC_OP04_format as op04
    db = _db(tmp_path)
    q = ' '.join(op04.build_optimized_chk_query(
        db, 'F', ['t.`CHKTYPE`', 't.`CHKVALUE`'], ["'SEL'"], {'T': ['SEL']},
        [], [], {'TXT': 'SEL'}, {'SEL': 'Other'}, {}, 'TV').split())
    assert 'ci_key(' not in q
    assert q.endswith('ORDER BY t.`ROWNUM`,t.`CHKTYPE_K`,t.`CHKVALUE_K`;')


def test_main_query_sorted_without_order_by(tmp_path):
    import VC_OP04_format as op04
    db = _op04_db(tmp_path, [_m(3, 'X', 'c'), _m(1, 'X', 'a'), _m(2, 'X', 'b')])
    fields = ["max(CASE WHEN FIELDID = 'X' THEN TRANSVAL END) AS `X`"]
    q = op04.build_optimized_main_query(db, 'F', fields, 'TV', enable_order_by=False)
    assert [r[1] for r in db.cursor.execute(q).fetchall()] == ['a', 'b', 'c']


def test_main_query_order_by_text_follows_dialect(tmp_path):
    import VC_OP04_format as op04
    db = _db(tmp_path)
    fields = ["max(CASE WHEN FIELDID = 'X' THEN TRANSVAL END) AS `X`"]

    class MySQLLike:
        implicit_group_order = True
        ci_col = staticmethod(lambda n: n)
        ci = staticmethod(lambda e: e)

    def norm(q):
        return ' '.join(q.split())

    q = norm(op04.build_optimized_main_query(db, 'F', fields, 'TV', enable_order_by=False))
    assert 'GROUP BY `FILENAME`,`ROWNUM`,`SUBJID` ORDER BY `FILENAME`,`ROWNUM`,`SUBJID`;' in q
    q = norm(op04.build_optimized_main_query(db, 'F', fields, 'work_f', enable_order_by=False))
    assert 'GROUP BY `ROWNUM`,`SUBJID` ORDER BY `ROWNUM`,`SUBJID`;' in q
    q = norm(op04.build_optimized_main_query(MySQLLike(), 'F', fields, 'TV', enable_order_by=False))
    assert 'ORDER BY' not in q
    q = norm(op04.build_optimized_main_query(MySQLLike(), 'F', fields, 'TV', enable_order_by=True))
    assert q.endswith('ORDER BY `ROWNUM`;')


_KILL_CHILD = r'''
import sys
sys.path.insert(0, sys.argv[1])
from sdtm_sqlite import SQLiteDatabaseManager
db = SQLiteDatabaseManager(sys.argv[2])
db.connect()
db.connection.execute('PRAGMA cache_size=20')   # 小缓存：事务中的脏页尽快写进库文件

def rows():
    n = 0
    while True:
        n += 1
        if n == 20000:
            print('IN_TRANSACTION', flush=True)
        yield ('F', n, 'U1', 'S1', 'l', 'X', 'v%d' % n, 'v%d' % n, 0, 'CL', '')

db.load_metadata_rows('MD', rows())
'''


def test_killed_mid_load_leaves_db_usable(tmp_path):
    """runner 用 terminate()（Windows 下 = TerminateProcess）取消步骤：被杀后库文件必须完好。"""
    import os, subprocess, sys
    from sdtm_sqlite import SQLiteDatabaseManager
    path = str(tmp_path / 'w.sqlite')
    db = SQLiteDatabaseManager(path)
    db.connect(); db.create_metadata_table('MD')
    db.load_metadata_rows('MD', [('F', i, 'U1', 'S1', 'l', 'X', 'keep', 'keep', 0, '', '') for i in range(1, 5001)])
    db.disconnect()

    pipe = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pipeline')
    proc = subprocess.Popen([sys.executable, '-c', _KILL_CHILD, pipe, path],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        for line in proc.stdout:
            if 'IN_TRANSACTION' in line:
                break
        else:
            raise AssertionError('child exited before reaching the transaction')
        proc.kill()
    finally:
        proc.kill()
        proc.wait(timeout=30)
        proc.stdout.close()

    db = SQLiteDatabaseManager(path)
    db.connect()
    try:
        assert db.connection.execute('PRAGMA integrity_check').fetchone() == ('ok',)
        assert db.connection.execute('SELECT COUNT(*), MIN(METAVAL) FROM MD').fetchone() == (5000, 'keep')
        db.create_codelist_table('CL')
        assert db.insert_codelist_rows('CL', [('CL', 'a', '', 'A', '')]) == (1, 0)
        assert db.load_metadata_rows('MD', [('F', 1, 'U1', 'S1', 'l', 'X', 'n', 'n', 0, '', '')]) == 1
    finally:
        db.disconnect()


def test_op04_reports_missing_input_tables(tmp_path):
    import VC_OP04_format as op04
    db = _db(tmp_path)
    msg = op04.missing_input_tables_message(db)
    assert op04.CODELIST_TABLE_NAME in msg and op04.METADATA_TABLE_NAME in msg
    assert 'sqlite' in msg and str(tmp_path / 'w.sqlite') in msg and 'OP02 and OP03' in msg
    with pytest.raises(SystemExit) as exc:
        op04._run_format(db, 0)
    assert exc.value.code == 1
    db.create_codelist_table(op04.CODELIST_TABLE_NAME)
    msg = op04.missing_input_tables_message(db)
    assert op04.METADATA_TABLE_NAME in msg and op04.CODELIST_TABLE_NAME not in msg
    db.create_metadata_table(op04.METADATA_TABLE_NAME)
    assert op04.missing_input_tables_message(db) is None
    db.disconnect()


# ---------------------------------------------------------------------------
# Backend factory default / MySQL manager helpers (no MySQL connection)
# ---------------------------------------------------------------------------
def test_default_backend_is_sqlite_work_file():
    import os
    import VC_BC02_baseUtils as bc02
    from sdtm_sqlite import SQLiteDatabaseManager
    assert bc02.DB_BACKEND == 'sqlite'          # conftest 配置只有 STUDIES_ROOT_PATH
    db = bc02.DatabaseManager()                  # 只构造，不 connect（不在 examples/ 下建文件）
    assert isinstance(db, SQLiteDatabaseManager) and not db.is_connected()
    assert os.path.normcase(db.path) == os.path.normcase(
        os.path.join(bc02.SPECIFIC_PATH, f'{bc02.STUDY_ID}_work.sqlite'))


def test_mysql_manager_helpers_without_connection():
    import VC_BC02_baseUtils as bc02
    m = bc02.MySQLDatabaseManager()
    assert m.is_connected() is False
    assert m.ci_literal("it's") == "'it''s'"
    assert m.ci_literal("a''b") == "'a''''b'"
    assert m.ci_literal(5) == "'5'"


def test_legacy_mysql_config_prints_backend_notice(tmp_path):
    """DB_HOST 等有值但没写 DB_BACKEND：DatabaseManager() 在 stderr 提示默认已改为 SQLite。"""
    import json, os, subprocess, sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    import VC_BC01_constant as bc01
    assert bc01.DB_BACKEND_NOTICE == ''          # conftest 配置：没有 DB_* 项，不提示
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    factory = ("import sys; sys.path.insert(0, sys.argv[1]); import VC_BC02_baseUtils as b; "
               "db = b.DatabaseManager(); print(type(db).__name__)")
    constant_only = ("import sys; sys.path.insert(0, sys.argv[1]); import VC_BC01_constant as c; "
                     "print(repr(c.DB_BACKEND_NOTICE))")

    def run(code, cfg):
        p = tmp_path / 'cfg.json'
        p.write_text(json.dumps(cfg), encoding='utf-8')
        env = dict(os.environ, PROJECT_CONFIG_PATH=str(p), SDTM_STUDY='DEMO', PYTHONUTF8='1')
        return subprocess.run([sys.executable, '-c', code, os.path.join(root, 'pipeline')],
                              env=env, capture_output=True, text=True, encoding='utf-8')

    studies = os.path.join(root, 'examples', 'studies')
    r = run(factory, {'STUDIES_ROOT_PATH': studies, 'DB_HOST': '127.0.0.1'})
    assert r.returncode == 0 and r.stdout.strip() == 'SQLiteDatabaseManager'
    assert 'DB_BACKEND' in r.stderr and 'now SQLite' in r.stderr
    r = run(constant_only, {'STUDIES_ROOT_PATH': studies, 'DB_HOST': '127.0.0.1', 'DB_BACKEND': 'mysql'})
    assert r.returncode == 0 and r.stdout.strip() == "''"
