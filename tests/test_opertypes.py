# -*- coding: utf-8 -*-
"""
処理タイプの単体テスト（DB 不要）。実行: python tests/test_opertypes.py
対象: TPL（テンプレート）、guard 条件（&FIELD:VALUE）、既存 PRF / FLG / IIF / SEL の回帰。
"""
import os, sys
import numpy as np
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from VC_BC06_operateTypeFunctions import *          # noqa
from VC_BC04_operateType import vectorized_field_mapping  # noqa

src = pd.DataFrame({
    'SUBJID': ['1', '2', '3', '4'],
    'CODE':   ['DEATH', '', 'AE', 'PD'],
    'YN':     ['Y', 'Y', 'N', ''],
    'PARENT': ['Y', 'N', 'Y', 'Y'],
    'YEARS':  ['20', '20.5', '', '3'],
    'A':      ['a1', 'a2', 'a3', 'a4'],
    'B':      ['b1', 'b2', 'b3', 'b4'],
})

def run(opertype, fieldname, parameter, ndkey=False):
    res = pd.DataFrame({'X': [''] * len(src)})
    rule = {'fieldname_cycles': [[f for f in fieldname.split('$$$') if f]],
            'parameter_cycles': [parameter], 'opertype': opertype, 'ndkey': ndkey}
    out, cont = vectorized_field_mapping(res, src, 'X', rule, 0, {}, definition_row_num=1)
    return list(out['X']), list(cont)

# --- TPL
assert run('TPL', 'CODE', 'SCRT DISCONTINUED: {}')[0] == ['SCRT DISCONTINUED: DEATH', '', 'SCRT DISCONTINUED: AE', 'SCRT DISCONTINUED: PD']
assert run('TPL', 'YEARS', 'P{}Y')[0] == ['P20Y', 'P20.5Y', '', 'P3Y']
assert run('TPL', 'CODE', 'X-')[0] == ['X-DEATH', '', 'X-AE', 'X-PD'], 'TPL without {} behaves like PRF'
# --- PRF unchanged
assert run('PRF', 'CODE', 'X-')[0] == ['X-DEATH', '', 'X-AE', 'X-PD']
# --- guard on FLG (AND of two fields)
assert run('FLG', 'YN', 'Y:HYPERTENSION$$$&PARENT:Y')[0] == ['HYPERTENSION', '', '', '']
# --- guard on FIX with null / !VALUE / not null
assert run('FIX', 'YEARS', '&YN:Y')[0] == ['20', '20.5', '', '']
assert run('FIX', 'A', '&YN:null')[0] == ['', '', '', 'a4']
assert run('FIX', 'A', '&YN:!Y')[0] == ['', '', 'a3', 'a4']
assert run('FIX', 'A', '&YEARS:not null')[0] == ['a1', 'a2', '', 'a4']
# --- two guards
assert run('FIX', 'A', '&YN:Y$$$&PARENT:Y')[0] == ['a1', '', '', '']
# --- guard on IIF (per-branch conditions still work)
assert run('IIF', 'A$$$B', 'YN:Y$$$YN:N$$$&PARENT:Y')[0] == ['a1', '', 'b3', '']
# --- guard on DEF (fixed value only where guard holds)
assert run('DEF', '', 'FIXED$$$&PARENT:Y')[0] == ['FIXED', '', 'FIXED', 'FIXED']
# --- guard on SEL drops the row (continue flag) as well
vals, cont = run('SEL', 'A', 'YN:Y$$$&PARENT:Y')
assert cont == [False, True, True, True], cont          # row 2: guard fails, rows 3/4: SEL condition fails
assert vals[0] == 'a1' and vals[1] == '', vals          # SEL keeps the value on dropped rows (existing behaviour); guard blanks it
# --- missing guard column → nothing passes
assert run('FIX', 'A', '&NOPE:Y')[0] == ['', '', '', '']
# --- split_guards leaves parameters without & untouched
assert split_guards('YN:Y$$$YN:N') == ('YN:Y$$$YN:N', [])
assert split_guards('') == ('', [])
print('all opertype tests passed')
