#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
本模块包含 MYSTUDY 研究特定的数据处理函数。
请在此添加 join / merge / 字段处理等 study-specific 逻辑。

模板提供两个示例函数：
- left_join_on_SUBJID: 基于 SUBJID 的左连接
- filter_df_by_field: 基于字段值的简单筛选

按需删除或修改。
"""

from VC_BC03_fetchConfig import *
from VC_BC04_operateType import *
import numpy as np
import pandas as pd


def left_join_on_SUBJID(main_file, sub_file, fields=None):
    """
    基于 SUBJID 进行左连接的示例函数。
    main_file / sub_file 接受表名 (str) 或 pandas.DataFrame。
    fields 指定从 sub 表保留的列名 (Iterable[str] | str | None)。
    """
    tables_to_fetch = []
    if isinstance(main_file, str):
        tables_to_fetch.append(main_file)
    if isinstance(sub_file, str):
        tables_to_fetch.append(sub_file)

    format_dataset = getFormatDataset(*tables_to_fetch) if tables_to_fetch else {}

    left_df = main_file.copy() if isinstance(main_file, pd.DataFrame) else format_dataset[main_file].copy()
    right_df = sub_file.copy() if isinstance(sub_file, pd.DataFrame) else format_dataset[sub_file].copy()

    if fields is not None:
        if isinstance(fields, str):
            fields = [fields]
        keep_cols = ['SUBJID'] + [c for c in fields if c in right_df.columns]
        right_df = right_df[keep_cols]

    merged = pd.merge(left_df, right_df, on='SUBJID', how='left')
    return merged.astype(str)


def filter_df_by_field(source, **filters):
    """
    通用筛选函数。
    source 可以是表名 (str) 或 pandas.DataFrame。
    filters 形如 EventId='AT REGISTRATION'，多个条件取 AND。
    """
    if isinstance(source, str):
        format_dataset = getFormatDataset(source)
        df = format_dataset[source].copy()
    else:
        df = source.copy()

    for col, value in filters.items():
        df = df[df[col] == value]

    df = df.dropna(axis=1, how='all')
    return df
