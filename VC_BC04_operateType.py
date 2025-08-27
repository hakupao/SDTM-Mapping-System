"""
VAPORCONE 项目操作类型处理模块 - 优化版本
优化前参考：
VC_BC04_operateType20250827.py

该模块实现了数据转换过程中的各种操作类型，包括：
- 单表操作
- 多表联合操作
- 字段映射处理
- 特殊操作类型处理
- 优化的向量化操作处理
"""

import re
import numpy as np
import pandas as pd
from VC_BC03_fetchConfig import *
sys.path.append(SPECIFIC_PATH)
from VC_BC05_studyFunctions import * # type: ignore

# 编译的正则表达式模式（优化性能）
COMPILED_CYCLE_PATTERN = re.compile(PATTERN_CYCLE_PRA)

# CSV缓存字典
csv_cache = {}

def get_cached_csv(file_path, needed_columns=None):
    """
    优化的CSV缓存读取
    
    参数:
    - file_path (str): CSV文件路径
    - needed_columns (list, optional): 需要读取的列名列表
    
    返回:
    - DataFrame: 读取的数据框
    """
    # 在并行处理中，每个进程有自己的缓存
    global csv_cache
    if csv_cache is None:
        csv_cache = {}
    
    cache_key = (file_path, tuple(sorted(needed_columns)) if needed_columns else None)
    
    if cache_key not in csv_cache:
        try:
            read_kwargs = {
                'dtype': str, 
                'na_filter': False,
                'engine': 'c',  # 使用C引擎提速
                'low_memory': False
            }
            if needed_columns:
                read_kwargs['usecols'] = needed_columns
            csv_cache[cache_key] = pd.read_csv(file_path, **read_kwargs)
        except Exception as e:
            print(f"读取CSV文件失败: {file_path}, 错误: {e}")
            return pd.DataFrame()
    
    return csv_cache[cache_key]

def singleTable(table):
    """
    单表操作，获取并返回指定表的数据
    
    参数:
    - table (str): 表名
    
    返回:
    - DataFrame: 转换为字符串类型的数据框
    """
    format_dataset = getFormatDataset(table)
    be_converted_list = format_dataset[table]
    return be_converted_list.astype(str)

def tableJoinType1(*tableList):
    """
    多表联合操作类型1，基于SUBJID字段进行外连接
    
    参数:
    - *tableList: 可变长度的表名列表
    
    返回:
    - DataFrame: 联合后的数据框，转换为字符串类型
    """
    format_dataset = getFormatDataset(*tableList)
    left_info = pandas.DataFrame()
    
    for file_name in tableList:
        file_filter_data = format_dataset[file_name]
        if left_info.empty:
            left_info = file_filter_data
        else:
            be_converted_list = pandas.merge(
                left_info, 
                file_filter_data, 
                left_on='SUBJID', 
                right_on='SUBJID', 
                how='outer'
            ).fillna('')
            left_info = be_converted_list
    
    return be_converted_list.astype(str)

def precompute_mapping_rules(domain_param, definition_merge_rule):
    """
    预计算映射规则，优化性能
    
    参数:
    - domain_param (dict): 域参数字典
    - definition_merge_rule (dict): 定义合并规则字典
    
    返回:
    - dict: 预计算的映射规则字典
    """
    precomputed_rules = {}
    
    for definition_row_num, definition_param_dict in domain_param.items():
        if definition_row_num not in definition_merge_rule:
            continue
            
        combo_file_name = definition_merge_rule[definition_row_num][COL_MERGERULE]
        if not combo_file_name:
            continue
            
        cycle_time = definition_merge_rule[definition_row_num][COL_DEFINITION]
        
        field_rules = {}
        needed_columns = set(['SUBJID'])
        
        for standard_field, sdtm_field_param in definition_param_dict.items():
            fieldname = sdtm_field_param[COL_FIELDNAME]
            parameter = sdtm_field_param[COL_PARAMETER]
            opertype = sdtm_field_param[COL_OPERTYPE]
            
            fieldname_cycles = []
            parameter_cycles = []
            
            for i in range(cycle_time):
                if COMPILED_CYCLE_PATTERN.match(fieldname):
                    fieldname_str = COMPILED_CYCLE_PATTERN.sub(r"\1", fieldname)
                    fieldname_list = fieldname_str.split(MARK_DOLLAR)
                    updated_column_names = [fieldname_list[i]] if i < len(fieldname_list) else []
                else:
                    fieldname_list = [f for f in fieldname.split(MARK_DOLLAR) if f]
                    updated_column_names = fieldname_list
                
                fieldname_cycles.append(updated_column_names)
                needed_columns.update(updated_column_names)
                
                if COMPILED_CYCLE_PATTERN.match(parameter):
                    parameter_str = COMPILED_CYCLE_PATTERN.sub(r"\1", parameter)
                    parameter_list = parameter_str.split(MARK_DOLLAR)
                    cycle_parameter = parameter_list[i] if i < len(parameter_list) else ""
                else:
                    cycle_parameter = parameter
                
                parameter_cycles.append(cycle_parameter)
                
                # 添加额外需要的列（用于条件判断）
                if opertype == OPERTYPE_IIF and cycle_parameter:
                    for param_record in cycle_parameter.split(MARK_DOLLAR):
                        if MARK_COLON in param_record:
                            flg_field = param_record.split(MARK_COLON)[0]
                            needed_columns.add(flg_field)
                elif opertype == OPERTYPE_SEL and cycle_parameter:
                    if MARK_COLON in cycle_parameter:
                        flg_field = cycle_parameter.split(MARK_COLON)[0]
                        needed_columns.add(flg_field)
            
            field_rules[standard_field] = {
                'fieldname_cycles': fieldname_cycles,
                'parameter_cycles': parameter_cycles,
                'opertype': opertype,
                'ndkey': sdtm_field_param[COL_NDKEY]
            }
        
        precomputed_rules[definition_row_num] = {
            'combo_file_name': combo_file_name,
            'cycle_time': cycle_time,
            'field_rules': field_rules,
            'needed_columns': list(needed_columns)
        }
    
    return precomputed_rules

def ultra_fast_sequence_generation(df, seq_field, sort_keys, domain_key, sequenceDict):
    """
    超高效序号生成算法 - 保持序号连续性
    
    参数:
    - df (DataFrame): 数据框
    - seq_field (str): 序号字段名
    - sort_keys (list): 排序键列表
    - domain_key (str): 域名
    - sequenceDict (dict): 序号字典
    
    返回:
    - DataFrame: 添加序号后的数据框
    """
    if df.empty or seq_field not in df.columns:
        return df
    
    # 1. 预排序优化 - 完全复制原版排序逻辑
    sort_df = df.copy()
    
    # 2. 预处理EPOCH字段（如果存在）
    epoch_col = None
    for sort_key in sort_keys:
        if sort_key == 'EPOCH' and 'EPOCH' in sort_df.columns:
            epoch_col = '_EPOCH_SORT'
            # 向量化的EPOCH数值提取
            sort_df[epoch_col] = sort_df['EPOCH'].fillna('').astype(str)
            sort_df[epoch_col] = sort_df[epoch_col].str.replace('TREATMENT', '', regex=False)
            sort_df[epoch_col] = pd.to_numeric(sort_df[epoch_col], errors='coerce').fillna(0).astype('int32')
            break
    
    # 3. 构建实际排序列
    actual_sort_keys = []
    for key in sort_keys:
        if key == 'EPOCH' and epoch_col:
            actual_sort_keys.append(epoch_col)
        else:
            actual_sort_keys.append(key)
    
    # 4. 高效排序
    sort_df = sort_df.sort_values(actual_sort_keys, kind='mergesort')  # 稳定排序
    
    # 5. 序号生成 - 保持连续性（复制原版逻辑）
    sequences = []
    prev_usubjid = None
    seq_counter = 1
    
    for idx, row in sort_df.iterrows():
        usubjid = row[VARIABLE_USUBJID]
        if usubjid != prev_usubjid:
            # 🔑 关键：使用全局sequenceDict保持连续性
            seq_counter = sequenceDict[usubjid][domain_key]
        sequences.append(str(seq_counter))
        seq_counter += 1
        # 🔑 关键：更新全局sequenceDict
        sequenceDict[usubjid][domain_key] = seq_counter
        prev_usubjid = usubjid
    
    sort_df[seq_field] = sequences
    
    # 6. 清理临时列
    if epoch_col and epoch_col in sort_df.columns:
        sort_df = sort_df.drop(epoch_col, axis=1)
    
    return sort_df

def vectorized_field_mapping(result_df, be_converted_df, standard_field, field_rule, cycle_idx, codeDict, definition_row_num=None):
    """
    向量化字段映射处理 - 集成所有操作类型处理
    
    参数:
    - result_df (DataFrame): 结果数据框
    - be_converted_df (DataFrame): 源数据框
    - standard_field (str): 标准字段名
    - field_rule (dict): 字段规则
    - cycle_idx (int): 循环索引
    - codeDict (dict): 代码字典
    - definition_row_num (int, optional): 定义行号（用于错误报告）
    
    返回:
    - tuple: (更新后的结果数据框, 继续标志数组)
    """
    fieldname_cycle = field_rule['fieldname_cycles'][cycle_idx] if cycle_idx < len(field_rule['fieldname_cycles']) else []
    parameter_cycle = field_rule['parameter_cycles'][cycle_idx] if cycle_idx < len(field_rule['parameter_cycles']) else ""
    opertype = field_rule['opertype']
    
    continue_flags = np.zeros(len(result_df), dtype=bool)
    
    # DEF操作不需要fieldname，直接处理
    if not fieldname_cycle and opertype != OPERTYPE_DEF:
        return result_df, continue_flags
    
    try:
        if opertype == OPERTYPE_DEF:
            result_df[standard_field] = parameter_cycle
        elif opertype == OPERTYPE_FIX:
            if fieldname_cycle and fieldname_cycle[0] in be_converted_df.columns:
                result_df[standard_field] = be_converted_df[fieldname_cycle[0]].values
        elif opertype == OPERTYPE_FLG:
            # FLG: 基于条件的标志映射
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
        elif opertype == OPERTYPE_IIF:
            # IIF: 条件选择
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
        elif opertype == OPERTYPE_COB:
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
        elif opertype == OPERTYPE_CDL:
            if parameter_cycle == "BLANK" and fieldname_cycle and fieldname_cycle[0] in be_converted_df.columns:
                result_df[standard_field] = be_converted_df[fieldname_cycle[0]].values
            elif parameter_cycle in codeDict and fieldname_cycle and fieldname_cycle[0] in be_converted_df.columns:
                source_values = be_converted_df[fieldname_cycle[0]]
                mapped_values = source_values.map(codeDict[parameter_cycle]).fillna('')
                result_df[standard_field] = mapped_values.values
        elif opertype == OPERTYPE_PRF:
            if fieldname_cycle and fieldname_cycle[0] in be_converted_df.columns:
                source_values = be_converted_df[fieldname_cycle[0]]
                prefixed_values = [parameter_cycle + str(x) if x else '' for x in source_values]
                result_df[standard_field] = prefixed_values
        elif opertype == OPERTYPE_SEL:
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
        elif opertype:
            # 处理特殊操作类型 - 调用specialType函数（如果存在）
            try:
                # 尝试导入并调用specialType函数
                for idx in range(len(be_converted_df)):
                    be_converted_row = be_converted_df.iloc[idx]
                    domain_row = {col: result_df.iloc[idx][col] for col in result_df.columns}
                    row_continue_flg = False
                    
                    try:
                        # 尝试调用specialType函数
                        domain_row, row_continue_flg = specialType(  # type: ignore
                            domain_row, standard_field, opertype, parameter_cycle,
                            be_converted_row, fieldname_cycle, codeDict, False
                        )
                        result_df.iloc[idx, result_df.columns.get_loc(standard_field)] = domain_row[standard_field]
                        if row_continue_flg:
                            continue_flags[idx] = True
                    except NameError:
                        # specialType函数未定义，跳过处理
                        print(f"警告: 特殊操作类型 '{opertype}' 无法处理，specialType函数未定义")
                        if definition_row_num:
                            print(f"警告发生在Excel的第 {definition_row_num} 行")
                        break
                    except Exception as e:
                        # specialType函数调用失败
                        print(f"警告: 特殊操作类型 '{opertype}' 处理失败: {str(e)}")
                        if definition_row_num:
                            print(f"警告发生在Excel的第 {definition_row_num} 行")
                        continue
            except Exception as e:
                print(f"处理特殊操作类型时发生错误: {str(e)}")
                if definition_row_num:
                    print(f"错误发生在Excel的第 {definition_row_num} 行")
                
    except KeyError as e:
        # 处理键错误
        print(f'KeyError: 字段 {standard_field} 处理出错')
        print(f'KeyError: 操作类型 {opertype} 处理出错')
        print(f'KeyError: 参数 {parameter_cycle} 处理出错')
        print(f'KeyError: 详细错误信息: {str(e)}')
        if definition_row_num:
            print(f'错误发生在Excel的第 {definition_row_num} 行')
        # 不退出程序，而是继续处理
                
    except Exception as e:
        print(f"字段映射处理时发生错误: {str(e)}")
        print(f"处理字段: {standard_field}, 操作类型: {opertype}, 参数: {parameter_cycle}")
        if definition_row_num:
            print(f"错误发生在Excel的第 {definition_row_num} 行")
        # 不退出程序，继续处理其他字段
    
    return result_df, continue_flags
