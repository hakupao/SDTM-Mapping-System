"""
VAPORCONE 项目操作类型处理模块

该模块实现了数据转换过程中的各种操作类型，包括：
- 单表操作
- 多表联合操作
- 字段映射处理
- 特殊操作类型处理
"""

from VC_BC03_fetchConfig import *
sys.path.append(SPECIFIC_PATH)
from VC_BC05_studyFunctions import * # type: ignore


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

def handle_key_error(standard_field, opertype, parameter, definition_row_num=None):
    """
    处理键错误，输出错误信息并退出程序
    
    参数:
    - standard_field (str): 标准字段名
    - opertype (str): 操作类型
    - parameter (str): 参数
    - definition_row_num (int, optional): 定义行号
    """
    print(f'KeyError: field: {standard_field} have some error')
    print(f'KeyError: opertype: {opertype} have some error')
    print(f'KeyError: parameter: {parameter} have some error')
    if definition_row_num:
        print(f'错误发生在Excel的第 {definition_row_num} 行')
    sys.exit()

def doMapping(domain_row, standard_field, opertype, parameter, be_converted_row, updated_column_names, codeDict, continue_flg, definition_row_num=None):
    try:
        if opertype == OPERTYPE_DEF:
            domain_row[standard_field] = parameter
        elif opertype == OPERTYPE_FIX:
            domain_row[standard_field] = be_converted_row[updated_column_names[0]]
        elif opertype == OPERTYPE_FLG:
            for part in parameter.split(MARK_DOLLAR):
                sVal, fVal = part.split(MARK_COLON, 1)
                if sVal.lower() == 'null':
                    sVal = MARK_BLANK
                if be_converted_row[updated_column_names[0]] == sVal:
                    domain_row[standard_field] = fVal
        elif opertype == OPERTYPE_IIF:
            parameters = parameter.split(MARK_DOLLAR)
            for idx, parameters_record in enumerate(parameters):
                flg_field, flg_value = parameters_record.split(MARK_COLON, 1)
                if be_converted_row[flg_field] == flg_value:
                    if len(updated_column_names) == 1:
                        idx = 0
                    domain_row[standard_field] = be_converted_row[updated_column_names[idx]]
        elif opertype == OPERTYPE_COB:
            Separator = MARK_BLANK
            if parameter:
                Separator = parameter.split(MARK_COLON)[1]
            domain_row[standard_field] = Separator.join([be_converted_row[c] for c in updated_column_names if c and be_converted_row[c]])
        elif opertype == OPERTYPE_CDL:
            if parameter == "BLANK":
                domain_row[standard_field] = be_converted_row[updated_column_names[0]]
            elif be_converted_row[updated_column_names[0]]:
                try:
                    domain_row[standard_field] = codeDict[parameter][be_converted_row[updated_column_names[0]]]
                except KeyError:
                    print(f"KeyError: '{be_converted_row[updated_column_names[0]]}' not found in codeDict for parameter '{parameter}'.")
                    print(f"Available keys: {list(codeDict[parameter].keys())}")
                    if definition_row_num:
                        print(f"错误发生在Excel的第 {definition_row_num} 行")
                    domain_row[standard_field] = None
                    
        elif opertype == OPERTYPE_PRF:
            row_field_val = be_converted_row[updated_column_names[0]]
            if row_field_val:
                domain_row[standard_field] = parameter + row_field_val
            
        elif opertype == OPERTYPE_SEL:
            domain_row[standard_field] = be_converted_row[updated_column_names[0]]
            parameter_parts = parameter.split(MARK_COLON)
            rVal = be_converted_row[parameter_parts[0]]
            cVal = parameter_parts[1]
            if cVal.lower() == 'not null':
                if not rVal:
                    continue_flg = True
            else:
                if cVal.startswith('!'):
                    if rVal == cVal.replace('!', MARK_BLANK):
                        continue_flg = True
                else:
                    if rVal != cVal:
                        continue_flg = True
        elif opertype:
            domain_row, continue_flg = specialType(domain_row, standard_field, opertype, parameter, be_converted_row, updated_column_names, codeDict, continue_flg) # type: ignore
    except KeyError:
        handle_key_error(standard_field, opertype, parameter, definition_row_num)
    except Exception as e:
        print(f"处理时发生错误: {str(e)}")
        print(f"处理字段: {standard_field}, 操作类型: {opertype}, 参数: {parameter}")
        if definition_row_num:
            print(f"错误发生在Excel的第 {definition_row_num} 行")
        sys.exit(1)

    return domain_row, continue_flg

