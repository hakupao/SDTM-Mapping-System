"""
VAPORCONE 项目操作类型函数模块

该模块将各种操作类型(opertype)的处理逻辑拆分为独立函数，
从 VC_BC04_operateType.py 中的 vectorized_field_mapping 函数重构而来。

支持的操作类型：
- DEF: 定义固定值
- FIX: 固定字段映射
- FLG: 标志映射
- IIF: 条件选择
- COB: 字段组合
- CDL: 代码列表映射
- PRF: 前缀添加
- SEL: 选择性映射
- TPL: 模板（PARAMETER 中的 {} 用源值替换；前缀/后缀/包围一次搞定）

通用 guard 条件（所有操作类型）:
  PARAMETER 中以 '&' 开头的行是附加条件 '&FIELD:VALUE'（VALUE 可为 null / !VALUE / not null，与 SEL 相同）。
  全部满足的行才保留结果；不满足的行结果为空（NDKEY 变量为空则整行不输出）。SEL 时还会丢弃该行。
  例: FLG  HT_YNCD  Y:HYPERTENSION  +  &COMP_YNCD:Y   → 既往歴あり かつ 高血圧あり のときだけ値を出す
"""

import numpy as np
import pandas as pd
from VC_BC03_fetchConfig import *


def opertype_DEF(result_df, be_converted_df, standard_field, parameter_cycle, **kwargs):
    """
    DEF操作: 定义固定值

    参数:
    - result_df (DataFrame): 结果数据框
    - be_converted_df (DataFrame): 源数据框
    - standard_field (str): 标准字段名
    - parameter_cycle (str): 参数值

    返回:
    - tuple: (更新后的结果数据框, 继续标志数组)
    """
    result_df[standard_field] = parameter_cycle
    continue_flags = np.zeros(len(result_df), dtype=bool)
    return result_df, continue_flags


def opertype_FIX(result_df, be_converted_df, standard_field, fieldname_cycle, **kwargs):
    """
    FIX操作: 固定字段映射

    参数:
    - result_df (DataFrame): 结果数据框
    - be_converted_df (DataFrame): 源数据框
    - standard_field (str): 标准字段名
    - fieldname_cycle (list): 字段名列表

    返回:
    - tuple: (更新后的结果数据框, 继续标志数组)
    """
    continue_flags = np.zeros(len(result_df), dtype=bool)

    if fieldname_cycle and fieldname_cycle[0] in be_converted_df.columns:
        result_df[standard_field] = be_converted_df[fieldname_cycle[0]].values

    return result_df, continue_flags


def opertype_FLG(result_df, be_converted_df, standard_field, fieldname_cycle, parameter_cycle, **kwargs):
    """
    FLG操作: 基于条件的标志映射

    参数:
    - result_df (DataFrame): 结果数据框
    - be_converted_df (DataFrame): 源数据框
    - standard_field (str): 标准字段名
    - fieldname_cycle (list): 字段名列表
    - parameter_cycle (str): 参数（格式: sVal:fVal$sVal2:fVal2）

    返回:
    - tuple: (更新后的结果数据框, 继续标志数组)
    """
    continue_flags = np.zeros(len(result_df), dtype=bool)

    if fieldname_cycle and fieldname_cycle[0] in be_converted_df.columns:
        source_col = be_converted_df[fieldname_cycle[0]]
        result_values = np.full(len(source_col), MARK_BLANK, dtype='object')

        for part in parameter_cycle.split(MARK_DOLLAR):
            if MARK_COLON in part:
                sVal, fVal = part.split(MARK_COLON, 1)
                if sVal.lower() == 'null':
                    sVal = MARK_BLANK

                mask = (source_col == sVal).values
                result_values = np.where(mask, fVal, result_values)

        result_df[standard_field] = result_values

    return result_df, continue_flags


def opertype_IIF(result_df, be_converted_df, standard_field, fieldname_cycle, parameter_cycle, **kwargs):
    """
    IIF操作: 条件选择

    参数:
    - result_df (DataFrame): 结果数据框
    - be_converted_df (DataFrame): 源数据框
    - standard_field (str): 标准字段名
    - fieldname_cycle (list): 字段名列表
    - parameter_cycle (str): 参数（格式: flg_field:flg_value$...）

    返回:
    - tuple: (更新后的结果数据框, 继续标志数组)
    """
    continue_flags = np.zeros(len(result_df), dtype=bool)

    if fieldname_cycle:
        result_values = np.full(len(be_converted_df), MARK_BLANK, dtype='object')
        parameters = parameter_cycle.split(MARK_DOLLAR)

        for idx, param_record in enumerate(parameters):
            if MARK_COLON in param_record:
                flg_field, flg_value = param_record.split(MARK_COLON, 1)
                if flg_field in be_converted_df.columns:
                    condition_mask = (be_converted_df[flg_field] == flg_value).values

                    col_idx = 0 if len(fieldname_cycle) == 1 else idx
                    if col_idx < len(fieldname_cycle) and fieldname_cycle[col_idx] in be_converted_df.columns:
                        source_values = be_converted_df[fieldname_cycle[col_idx]].values
                        result_values = np.where(condition_mask, source_values, result_values)

        result_df[standard_field] = result_values

    return result_df, continue_flags


def opertype_COB(result_df, be_converted_df, standard_field, fieldname_cycle, parameter_cycle, **kwargs):
    """
    COB操作: 字段组合

    参数:
    - result_df (DataFrame): 结果数据框
    - be_converted_df (DataFrame): 源数据框
    - standard_field (str): 标准字段名
    - fieldname_cycle (list): 字段名列表
    - parameter_cycle (str): 参数（格式: :separator）

    返回:
    - tuple: (更新后的结果数据框, 继续标志数组)
    """
    continue_flags = np.zeros(len(result_df), dtype=bool)

    separator = MARK_BLANK
    if parameter_cycle and MARK_COLON in parameter_cycle:
        separator = parameter_cycle.split(MARK_COLON)[1]

    valid_cols = [col for col in fieldname_cycle if col in be_converted_df.columns]
    if valid_cols:
        # 向量化字符串连接
        str_df = be_converted_df[valid_cols].fillna('').astype(str)
        result_df[standard_field] = str_df.apply(
            lambda row: separator.join(v for v in row if v), axis=1
        )

    return result_df, continue_flags


def opertype_CDL(result_df, be_converted_df, standard_field, fieldname_cycle, parameter_cycle, codeDict, **kwargs):
    """
    CDL操作: 代码列表映射

    参数:
    - result_df (DataFrame): 结果数据框
    - be_converted_df (DataFrame): 源数据框
    - standard_field (str): 标准字段名
    - fieldname_cycle (list): 字段名列表
    - parameter_cycle (str): 参数（代码字典键或"BLANK"）
    - codeDict (dict): 代码字典

    返回:
    - tuple: (更新后的结果数据框, 继续标志数组)
    """
    continue_flags = np.zeros(len(result_df), dtype=bool)

    if parameter_cycle == "BLANK" and fieldname_cycle and fieldname_cycle[0] in be_converted_df.columns:
        result_df[standard_field] = be_converted_df[fieldname_cycle[0]].values
    elif parameter_cycle in codeDict and fieldname_cycle and fieldname_cycle[0] in be_converted_df.columns:
        source_values = be_converted_df[fieldname_cycle[0]]
        mapped_values = source_values.map(codeDict[parameter_cycle]).fillna('')
        result_df[standard_field] = mapped_values.values

    return result_df, continue_flags


def opertype_PRF(result_df, be_converted_df, standard_field, fieldname_cycle, parameter_cycle, **kwargs):
    """
    PRF操作: 前缀添加

    参数:
    - result_df (DataFrame): 结果数据框
    - be_converted_df (DataFrame): 源数据框
    - standard_field (str): 标准字段名
    - fieldname_cycle (list): 字段名列表
    - parameter_cycle (str): 前缀字符串

    返回:
    - tuple: (更新后的结果数据框, 继续标志数组)
    """
    continue_flags = np.zeros(len(result_df), dtype=bool)

    if fieldname_cycle and fieldname_cycle[0] in be_converted_df.columns:
        source_values = be_converted_df[fieldname_cycle[0]]
        prefixed_values = [parameter_cycle + str(x) if x else '' for x in source_values]
        result_df[standard_field] = prefixed_values

    return result_df, continue_flags


def opertype_TPL(result_df, be_converted_df, standard_field, fieldname_cycle, parameter_cycle, **kwargs):
    """
    TPL操作: 模板替换。PARAMETER 例: 'SCRT DISCONTINUED: {}'、'P{}Y'。
    源值为空时结果为空。PARAMETER 中没有 {} 时视为前缀（与 PRF 相同）。
    """
    continue_flags = np.zeros(len(result_df), dtype=bool)

    if fieldname_cycle and fieldname_cycle[0] in be_converted_df.columns:
        template = parameter_cycle if MARK_TEMPLATE in parameter_cycle else parameter_cycle + MARK_TEMPLATE
        source_values = be_converted_df[fieldname_cycle[0]]
        result_df[standard_field] = [template.replace(MARK_TEMPLATE, str(x)) if x else '' for x in source_values]

    return result_df, continue_flags


def split_guards(parameter):
    """
    PARAMETER から guard 条件（'&FIELD:VALUE' の部分）を取り出す。
    返回: (guard を除いた parameter, [(field, cond), ...])
    """
    if not parameter or MARK_GUARD not in parameter:
        return parameter, []
    rest, guards = [], []
    for part in parameter.split(MARK_DOLLAR):
        if part.startswith(MARK_GUARD) and MARK_COLON in part:
            field, cond = part[len(MARK_GUARD):].split(MARK_COLON, 1)
            guards.append((field.strip(), cond.strip()))
        else:
            rest.append(part)
    return MARK_DOLLAR.join(rest), guards


def guard_mask(be_converted_df, guards):
    """
    guard 条件をすべて満たす行を True にした numpy 配列を返す。条件の書き方は SEL と同じ:
    VALUE（等しい）/ null（空）/ !VALUE（等しくない）/ not null（空でない）。
    列が無い guard は満たさないものとして扱う（設定ミスを黙って通さない）。
    """
    mask = np.ones(len(be_converted_df), dtype=bool)
    for field, cond in guards:
        if field not in be_converted_df.columns:
            mask[:] = False
            continue
        col = be_converted_df[field].fillna('').astype(str)
        if cond.lower() == 'not null':
            mask &= (col != '').values
        elif cond.lower() == 'null':
            mask &= (col == '').values
        elif cond.startswith('!'):
            mask &= (col != cond[1:]).values
        else:
            mask &= (col == cond).values
    return mask


def opertype_SEL(result_df, be_converted_df, standard_field, fieldname_cycle, parameter_cycle, **kwargs):
    """
    SEL操作: 选择性映射

    参数:
    - result_df (DataFrame): 结果数据框
    - be_converted_df (DataFrame): 源数据框
    - standard_field (str): 标准字段名
    - fieldname_cycle (list): 字段名列表
    - parameter_cycle (str): 参数（格式: flg_field:condition）

    返回:
    - tuple: (更新后的结果数据框, 继续标志数组)
    """
    continue_flags = np.zeros(len(result_df), dtype=bool)

    if fieldname_cycle and fieldname_cycle[0] in be_converted_df.columns:
        result_df[standard_field] = be_converted_df[fieldname_cycle[0]].values

        if MARK_COLON in parameter_cycle:
            flg_field, cVal = parameter_cycle.split(MARK_COLON, 1)
            if flg_field in be_converted_df.columns:
                rVal = be_converted_df[flg_field]

                if cVal.lower() == 'not null':
                    continue_flags |= (rVal.isna() | (rVal == '')).values
                elif cVal.startswith('!'):
                    target_val = cVal.replace('!', MARK_BLANK)
                    continue_flags |= (rVal == target_val).values
                else:
                    continue_flags |= (rVal != cVal).values

    return result_df, continue_flags




# 操作类型函数映射字典
OPERTYPE_FUNCTION_MAP = {
    OPERTYPE_DEF: opertype_DEF,
    OPERTYPE_FIX: opertype_FIX,
    OPERTYPE_FLG: opertype_FLG,
    OPERTYPE_IIF: opertype_IIF,
    OPERTYPE_COB: opertype_COB,
    OPERTYPE_CDL: opertype_CDL,
    OPERTYPE_PRF: opertype_PRF,
    OPERTYPE_SEL: opertype_SEL,
    OPERTYPE_TPL: opertype_TPL,
}


def get_opertype_function(opertype):
    """
    获取操作类型对应的处理函数

    参数:
    - opertype (str): 操作类型

    返回:
    - function: 对应的处理函数，如果不存在则返回 None
    """
    return OPERTYPE_FUNCTION_MAP.get(opertype)
