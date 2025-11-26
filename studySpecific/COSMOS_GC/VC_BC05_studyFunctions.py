#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
该模块包含CIRCULATE研究特定的数据处理函数。
主要功能包括数据表合并、字段处理和各种数据集的特定处理逻辑。
"""

from VC_BC03_fetchConfig import *
from VC_BC04_operateType import *
import numpy as np
import pandas
from decimal import Decimal


def left_join_on_SUBJID(main_file=None, sub_file=None, fields=None):
    """
    基于SUBJID进行左连接。

    参数:
    - main_file (str | pandas.DataFrame): 主表名称或数据框。
    - sub_file (str | pandas.DataFrame): 副表名称或数据框。
    - fields (Iterable[str] | str | None): 需要从副表中保留的列名，默认整表。

    返回:
    - pandas.DataFrame: 左连接后的结果，所有列为字符串类型。

    调用方法示例:
    left_join_on_SUBJID(main_file="COHORT", sub_file="IE", fields=["REGDTC"])
    left_join_on_SUBJID(main_df, sub_df, fields=None)
    """
    if main_file is None:
        raise ValueError("参数 'main_file' 不能为空。")
    if sub_file is None:
        raise ValueError("参数 'sub_file' 不能为空。")

    main_is_df = isinstance(main_file, pandas.DataFrame)
    sub_is_df = isinstance(sub_file, pandas.DataFrame)

    tables_to_fetch = []
    if not main_is_df:
        tables_to_fetch.append(main_file)

    if not sub_is_df:
        tables_to_fetch.append(sub_file)

    format_dataset = getFormatDataset(*tables_to_fetch) if tables_to_fetch else {}

    if main_is_df:
        left_df = main_file.copy()
        left_name = 'main'
    else:
        if main_file not in format_dataset:
            raise KeyError(f"主表 '{main_file}' 不存在于格式化数据集中。")
        left_df = format_dataset[main_file].copy()
        left_name = main_file

    if sub_is_df:
        right_df = sub_file.copy()
        right_name = 'sub'
    else:
        if sub_file not in format_dataset:
            raise KeyError(f"副表 '{sub_file}' 不存在于格式化数据集中。")
        right_df = format_dataset[sub_file].copy()
        right_name = sub_file

    if 'SUBJID' not in left_df.columns:
        raise KeyError(f"主表 '{left_name}' 缺少 'SUBJID' 字段，无法执行左连接。")
    if 'SUBJID' not in right_df.columns:
        raise KeyError(f"副表 '{right_name}' 缺少 'SUBJID' 字段，无法执行左连接。")

    if fields is None:
        selected_columns = list(right_df.columns)
    else:
        if isinstance(fields, str):
            selected_columns = [fields]
        else:
            selected_columns = list(fields)
        if 'SUBJID' not in selected_columns:
            selected_columns.insert(0, 'SUBJID')

        missing_columns = [col for col in selected_columns if col not in right_df.columns]
        if missing_columns:
            raise KeyError(f"副表缺少指定字段: {missing_columns}")

    right_subset = right_df.loc[:, selected_columns]

    merged_df = pandas.merge(
        left_df,
        right_subset,
        how='left',
        on='SUBJID',
        sort=False,
        suffixes=('', f'_{right_name}')
    )

    return merged_df.fillna('').astype(str)


def get_DEMOGRAPHIC_Data():
    
    format_dataset = getFormatDataset('PAT', 'IE', 'COHORT', 'TUMRECUR', 'DS', 'TRTINFO')
    pat_df = format_dataset['PAT']
    ie_df = format_dataset['IE']
    cohort_df = format_dataset['COHORT']
    tumrecur_df = format_dataset['TUMRECUR']
    ds_df = format_dataset['DS']
    trtinfo_df = format_dataset['TRTINFO']
    
    pat_df = pat_df[['SUBJID', 'AGE', 'SEX', 'STNAME']].copy()

    ie_df = ie_df[['SUBJID', 'REGDTC', 'RFICDTC', 'ICINVNAM', 'ICFVER']].copy()
    
    dm_df = pandas.merge(
        pat_df,
        ie_df,
        how='left',
        on='SUBJID'
    )
    # 给 cohort_df 添加新列 COHORT_ALL，值为 COHORT, COHORTA, COHORTB 的合并字符串(互斥)
    cohort_df['COHORT_ALL'] = cohort_df[['COHORT', 'COHORTA', 'COHORTB']].agg(''.join, axis=1)
    
    dm_df = pandas.merge(
        dm_df,
        cohort_df,
        how='left',
        on='SUBJID'
    )
    
    tumrecur_df = tumrecur_df[['SUBJID', 'FLWNUM', 'OUTCOME', 'DSSSDTC', 'DEATHDTC']].copy()
    ds_df = ds_df[['SUBJID', 'OUTCOME', 'DSSSDTC', 'DEATHDTC', 'DSENDTC']].copy()
    
    # 只保留 FLWNUM 字段数据的前两个字符
    tumrecur_df['ORDER'] = tumrecur_df['FLWNUM'].str[:2]
    tumrecur_df['DSENDTC'] = ''  # TUMRECUR 数据的 DSENDTC 固定为空字符串
    
    ds_df['ORDER'] = '99'  # DS 数据的 ORDER 固定为 '99'
    
    outcome_df = pandas.concat(
        [
            tumrecur_df[['SUBJID', 'ORDER', 'OUTCOME', 'DSSSDTC', 'DEATHDTC', 'DSENDTC']],
            ds_df[['SUBJID', 'ORDER', 'OUTCOME', 'DSSSDTC', 'DEATHDTC', 'DSENDTC']]
        ], 
        ignore_index=True
        )
    
    # 根据 SUBJID （升序）和 ORDER （降序）排序，每个 SUBJID 只保留第一条记录
    outcome_df = outcome_df.sort_values(by=['SUBJID', 'ORDER'], ascending=[True, False])
    outcome_df = outcome_df.drop_duplicates(subset=['SUBJID'], keep='first')
    
    outcome_df['RFENDTC'] =outcome_df[['DSSSDTC', 'DEATHDTC']].agg("".join, axis=1)
    
    dm_df = pandas.merge(
        dm_df,
        outcome_df,
        how='left',
        on='SUBJID'
    )

    trtinfo_df = trtinfo_df[['SUBJID', 'PRSTDTC', 'PRSEQ']].copy()
    
    # 对 trtinfo_df 按 SUBJID, PRSEQ, PRSTDTC 排序，保留每个 SUBJID 的第一条记录
    trtinfo_df = trtinfo_df.sort_values(by=['SUBJID', 'PRSEQ', 'PRSTDTC'], ascending=[True, True, True])
    trtinfo_df = trtinfo_df.drop_duplicates(subset=['SUBJID'], keep='first')

    dm_df = pandas.merge(
        dm_df,
        trtinfo_df,
        how='left',
        on='SUBJID'
    )
    
    return dm_df.fillna('').astype(str)

def TUMDATA_process():
    format_dataset = getFormatDataset('TUMDATA')
    tumdata_df = format_dataset['TUMDATA'].copy()

    def _has_value(series_name):
        if series_name not in tumdata_df.columns:
            return pandas.Series(False, index=tumdata_df.index)
        return tumdata_df[series_name].fillna('').astype(str).str.strip() != ''

    cstage_has_value = _has_value('CSTAGE')
    cstage2_has_value = _has_value('CSTAGE2')

    if 'CANCER' not in tumdata_df.columns:
        tumdata_df['CANCER'] = ''

    tumdata_df.loc[cstage_has_value, 'CANCER'] = 'GASTRIC CANCER'
    tumdata_df.loc[~cstage_has_value & cstage2_has_value, 'CANCER'] = 'GASTROINTESTINAL STROMAL TUMOR'

    return tumdata_df.fillna('').astype(str)
