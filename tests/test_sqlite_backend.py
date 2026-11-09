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
