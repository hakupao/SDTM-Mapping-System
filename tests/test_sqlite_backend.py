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
    odd = 'a\b "q", line1\nline2 \U0001F600'
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
