#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Study-specific functions for the DEMO study.

Every FUNCTION named in the Combine sheet of DEMO_OperationConf.xlsx is
evaluated in this module during OP04 (Format). Each function returns a
pandas.DataFrame that becomes a virtual source table (its FILENAME in the
Combine sheet), which the Mapping sheet can then reference like a raw file.

Two functions are provided:
- filter_df_by_field : keep the rows of a formatted table whose field equals a value
- DM                 : build the DM source table by joining RGST / LSVDAT / OC
"""

import pandas as pd

from VC_BC03_fetchConfig import *
from VC_BC04_operateType import *


def filter_df_by_field(source, **filters):
    """
    Return the rows of `source` whose `field == value` (exactly one filter).

    `source` is a formatted table name (str) or a DataFrame. Columns that are
    blank in every remaining row are dropped. All values are returned as str.

    Combine sheet example:
        REV_DS | filter_df_by_field('REV', EventId='RE-EVALUATION')
    """
    if isinstance(source, str):
        format_dataset = getFormatDataset(source)
        if source not in format_dataset:
            raise KeyError(f"Formatted table '{source}' not found.")
        df = format_dataset[source].copy()
    elif isinstance(source, pd.DataFrame):
        df = source.copy()
    else:
        raise TypeError("source must be a table name (str) or a DataFrame.")

    if len(filters) != 1:
        raise ValueError("Pass exactly one field=value filter.")
    field_name, value = next(iter(filters.items()))
    if field_name not in df.columns:
        raise KeyError(f"Column '{field_name}' not found in '{source}'.")

    target = '' if value is None else str(value)
    series = df[field_name].fillna('').astype(str).str.strip()
    filtered = df.loc[series == target].copy()

    if not filtered.empty:
        non_blank = filtered.fillna('').astype(str).apply(lambda s: s.str.strip().ne('')).any(axis=0)
        filtered = filtered.loc[:, non_blank]

    return filtered.fillna('').astype(str)


def DM():
    """
    Build the DM source table.

    Sources : RGST (registration: SEXCD, AGE), LSVDAT (last known alive date),
              OC (death date)
    Derived : RFENDAT = DTHDAT if present else LSVDAT
              DTHFLG  = 'Y' when DTHDAT is present, else ''

    The Mapping sheet maps these columns onto DM.RFENDTC / DTHDTC / DTHFL / AGE / SEX.
    """
    format_dataset = getFormatDataset('RGST', 'LSVDAT', 'OC')

    rgst = format_dataset['RGST'].copy()
    lsv = format_dataset['LSVDAT'][['SUBJID', 'LSVDAT']].copy()
    oc = format_dataset['OC'][['SUBJID', 'DTHDAT']].copy()

    dm = rgst.merge(lsv, on='SUBJID', how='left').merge(oc, on='SUBJID', how='left').fillna('')

    dm['RFENDAT'] = dm.apply(lambda r: r['DTHDAT'] if r['DTHDAT'] != '' else r['LSVDAT'], axis=1)
    dm['DTHFLG'] = dm['DTHDAT'].apply(lambda x: 'Y' if x != '' else '')

    return dm.astype(str)
