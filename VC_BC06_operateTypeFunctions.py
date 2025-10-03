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
- CAL: 数学运算计算（加减乘除）
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
        result_values = [MARK_BLANK] * len(source_col)

        for part in parameter_cycle.split(MARK_DOLLAR):
            if MARK_COLON in part:
                sVal, fVal = part.split(MARK_COLON, 1)
                if sVal.lower() == 'null':
                    sVal = MARK_BLANK

                # 向量化条件匹配
                mask = (source_col == sVal)
                for i, match in enumerate(mask):
                    if match:
                        result_values[i] = fVal

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
        result_values = [MARK_BLANK] * len(be_converted_df)
        parameters = parameter_cycle.split(MARK_DOLLAR)

        for idx, param_record in enumerate(parameters):
            if MARK_COLON in param_record:
                flg_field, flg_value = param_record.split(MARK_COLON, 1)
                if flg_field in be_converted_df.columns:
                    condition_mask = (be_converted_df[flg_field] == flg_value)

                    # 选择对应的列
                    col_idx = 0 if len(fieldname_cycle) == 1 else idx
                    if col_idx < len(fieldname_cycle) and fieldname_cycle[col_idx] in be_converted_df.columns:
                        source_values = be_converted_df[fieldname_cycle[col_idx]]
                        for i, match in enumerate(condition_mask):
                            if match:
                                result_values[i] = source_values.iloc[i]

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
        # 高效字符串连接
        combined_values = []
        for idx in range(len(be_converted_df)):
            vals = [str(be_converted_df.iloc[idx][col]) for col in valid_cols
                   if be_converted_df.iloc[idx][col]]
            combined_values.append(separator.join(vals))
        result_df[standard_field] = combined_values

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


def opertype_CAL(result_df, be_converted_df, standard_field, fieldname_cycle, parameter_cycle, **kwargs):
    """
    CAL操作: 数学运算计算（加减乘除）

    支持的参数格式:
    - +500  : 字段值加上500
    - -20   : 字段值减去20
    - *1000 : 字段值乘以1000
    - /600  : 字段值除以600

    参数:
    - result_df (DataFrame): 结果数据框
    - be_converted_df (DataFrame): 源数据框
    - standard_field (str): 标准字段名
    - fieldname_cycle (list): 字段名列表（通常只有一个字段）
    - parameter_cycle (str): 参数（格式: +数值 / -数值 / *数值 / /数值）

    返回:
    - tuple: (更新后的结果数据框, 继续标志数组)
    """
    continue_flags = np.zeros(len(result_df), dtype=bool)

    if not fieldname_cycle or not parameter_cycle:
        return result_df, continue_flags

    # 获取源字段
    if fieldname_cycle[0] not in be_converted_df.columns:
        return result_df, continue_flags

    try:
        # 将源字段转换为数值类型
        source_values = pd.to_numeric(be_converted_df[fieldname_cycle[0]], errors='coerce')

        # 解析运算符和数值
        operator = parameter_cycle[0]
        operand_str = parameter_cycle[1:].strip()

        # 确保operand是有效数值
        if not operand_str:
            print(f"CAL运算参数错误: 缺少数值，参数为 '{parameter_cycle}'")
            result_df[standard_field] = [MARK_BLANK] * len(be_converted_df)
            return result_df, continue_flags

        operand = float(operand_str)
        result_values = None

        # 根据运算符执行计算
        if operator == '+':
            result_values = source_values + operand
        elif operator == '-':
            result_values = source_values - operand
        elif operator == '*':
            result_values = source_values * operand
        elif operator == '/':
            if operand != 0:
                result_values = source_values / operand
            else:
                print(f"CAL运算错误: 除数不能为0")
                result_values = source_values * 0  # 返回0
        else:
            print(f"CAL运算错误: 未知的运算符 '{operator}'，支持的运算符: +, -, *, /")
            result_df[standard_field] = [MARK_BLANK] * len(be_converted_df)
            return result_df, continue_flags

        # 将结果转换为字符串，处理NaN和空值
        if result_values is not None:
            result_values = result_values.fillna('').astype(str)
            result_values = result_values.replace('nan', '')
            result_df[standard_field] = result_values.values

    except ValueError as e:
        print(f"CAL运算参数转换失败: {str(e)}")
        print(f"参数: {parameter_cycle}")
        result_df[standard_field] = [MARK_BLANK] * len(be_converted_df)
    except Exception as e:
        print(f"CAL运算处理失败: {str(e)}")
        print(f"字段: {fieldname_cycle}, 参数: {parameter_cycle}")
        result_df[standard_field] = [MARK_BLANK] * len(be_converted_df)

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
    OPERTYPE_CAL: opertype_CAL,
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
