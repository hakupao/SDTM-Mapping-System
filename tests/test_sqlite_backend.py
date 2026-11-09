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
