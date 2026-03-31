#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
该模块包含CIRCULATE研究特定的数据处理函数。
主要功能包括数据表合并、字段处理和各种数据集的特定处理逻辑。
"""

from VC_BC03_fetchConfig import *
from VC_BC04_operateType import *
import numpy as np
import pandas as pd
from decimal import Decimal
from datetime import datetime

def filter_df_by_field(source, **filters):
    """
    通用数据筛选函数。

    用法示例:
    filter_df_by_field('TME', EventId='AT REGISTRATION')
    filter_df_by_field(tme_df, EventId='AT REGISTRATION')

    规则：
    - 仅保留字段名严格等于指定值的记录；
    - 删除全空列（空字符串/NaN）。
    """
    if source is None:
        raise ValueError("引数 source は空にできません。")

    if isinstance(source, str):
        format_dataset = getFormatDataset(source)
        if source not in format_dataset:
            raise KeyError(f"整形済みデータセットに '{source}' テーブルが見つかりません。")
        df = format_dataset[source].copy()
    elif isinstance(source, pandas.DataFrame):
        df = source.copy()
    else:
        raise TypeError("引数 source には DataFrame またはテーブル名の文字列を指定してください。")

    if len(filters) != 1:
        raise ValueError("filters にはフィルタ条件を 1 件だけ指定してください。")

    field_name, value = next(iter(filters.items()))

    if field_name not in df.columns:
        raise KeyError(f"データに厳密一致する列名 '{field_name}' が存在しないため、フィルタリングできません。")

    target_value = '' if value is None else str(value)
    series = df[field_name].fillna('').astype(str).str.strip()
    filtered_df = df.loc[series == target_value].copy()

    # 删除全空列（空字符串/NaN）
    if not filtered_df.empty:
        non_blank_cols = (
            filtered_df.fillna('')
            .astype(str)
            .apply(lambda s: s.str.strip().ne(''))
            .any(axis=0)
        )
        filtered_df = filtered_df.loc[:, non_blank_cols]

    return filtered_df.fillna('').astype(str)

def DM():
    """
    生成 DM (DM) 数据集。

    数据来源：
    - RGST: 症例登録
    - LSVDAT: 最終生存確認日
    - OC: 転帰

    生成字段：
    - RFENDAT: 研究结束日期（优先使用 DTHDAT，其次使用 LSVDAT）
    - DTHFLG: 死亡标志（有死亡日期时为 'Y'，否则为空）

    返回:
        pd.DataFrame: 处理后的 DM 数据集，所有字段为字符串类型
    """
    # 获取所需数据表
    format_dataset = getFormatDataset('LSVDAT', 'OC', 'RGST')

    # 提取必要字段
    lsvdat_df = format_dataset['LSVDAT'][['SUBJID', 'LSVDAT']].copy()
    oc_df = format_dataset['OC'][['SUBJID', 'DTHDAT']].copy()
    rgst_df = format_dataset['RGST'].copy()

    # 以 RGST 为主表，左连接其他数据
    dm_df = pd.merge(rgst_df, lsvdat_df, on='SUBJID', how='left')
    dm_df = pd.merge(dm_df, oc_df, on='SUBJID', how='left')

    # 填充合并后可能产生的 NaN 为空字符串（保持数据一致性）
    dm_df = dm_df.fillna('')

    # 数据质量检查：记录同时存在 LSVDAT 和 DTHDAT 的受试者
    dual_date_subjects = dm_df.query('LSVDAT != "" and DTHDAT != ""')[['SUBJID', 'LSVDAT', 'DTHDAT']]
    if not dual_date_subjects.empty:
        print(f"[DM] 警告: {len(dual_date_subjects)} 名の被験者で LSVDAT と DTHDAT の両方が入力されています。")
        print(dual_date_subjects.to_string(index=False))

    # 数据质量检查：记录 LSVDAT 和 DTHDAT 同时为空的受试者（将导致 RFENDAT 为空）
    no_date_subjects = dm_df.query('LSVDAT == "" and DTHDAT == ""')[['SUBJID']]
    if not no_date_subjects.empty:
        print(f"[DM] 警告: {len(no_date_subjects)} 名の被験者で LSVDAT と DTHDAT がいずれも未入力です。")
        print(no_date_subjects.to_string(index=False))

    # 生成 RFENDAT：优先使用 DTHDAT，其次使用 LSVDAT
    dm_df['RFENDAT'] = dm_df.apply(
        lambda row: row['DTHDAT'] if row['DTHDAT'] != '' else row['LSVDAT'],
        axis=1
    )

    # 生成 DTHFLG：有死亡日期时为 'Y'
    dm_df['DTHFLG'] = dm_df['DTHDAT'].apply(lambda x: 'Y' if x != '' else '')

    return dm_df.astype(str)
