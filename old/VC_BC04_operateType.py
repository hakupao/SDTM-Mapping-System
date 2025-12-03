from VC_BC03_fetchConfig import *
sys.path.append(SPECIFIC_PATH)
from VC_BC05_studyFunctions import * # type: ignore

def singleTable(table):
    format_dataset = getFormatDataset(table)
    be_converted_list = format_dataset[table]
    return be_converted_list.astype(str)

def tableJoinType1(*tableList):
    format_dataset = getFormatDataset(*tableList)
    left_info = pandas.DataFrame()
    for file_name in tableList:
        file_filter_data = format_dataset[file_name]
        if left_info.empty:
            left_info = file_filter_data
        else:
            be_converted_list = pandas.merge(left_info, file_filter_data, left_on='SUBJID', right_on='SUBJID', how='outer').fillna('')
            left_info = be_converted_list
    return be_converted_list.astype(str)

#   singleTableWithFilter(table='TRF',filterField='SAMPTYP',filterValue='腫瘍組織検体')
#   singleTableWithFilter(table='TRF',filterField='SAMPTYP',filterValue='血液検体')
# def singleTableWithFilter(**kwargs):
#     table = kwargs.get('table')
#     filterField = kwargs.get('filterField')
#     filterValue = kwargs.get('filterValue')
#     format_dataset = getFormatDataset(table)
#     be_converted_list = format_dataset[table]
#     be_converted_list = be_converted_list[(be_converted_list[filterField] == filterValue)]
#     return be_converted_list.astype(str)


### 
# 执行mapping
# domain_row：移行目标行，除STUDYID，DOMAIN，USUBJID，SUBJID外，其余字段值皆为空
# standard_field：移行目标行字段
# opertype：操作类别，Mapping表OPERTYPE列
# parameter：操作时所需参数，Mapping表PARAMETER列
# be_converted_row：移行对象行
# updated_column_names：移行对象列名
# column_names：移行对象文件实际列名
# codeDict：
### 
def doMapping(domain_row, standard_field, opertype, parameter, be_converted_row, updated_column_names, codeDict, continue_flg):
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
            # flg_field_column = [col for col in column_names if col.endswith(flg_field)]
            # if len(flg_field_column) > 1:
            #     print(f'{OPERTYPE_IIF} {flg_field_column} naming is duplicated')
            #     sys.exit()

            # flg_field = flg_field_column[0]
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
            return domain_row, continue_flg
        if be_converted_row[updated_column_names[0]]:
            try:
                domain_row[standard_field] = codeDict[parameter][be_converted_row[updated_column_names[0]]]
            except KeyError:
                print(f"KeyError: '{be_converted_row[updated_column_names[0]]}' not found in codeDict for parameter '{parameter}'.")
                print(f"Available keys: {list(codeDict[parameter].keys())}")
                domain_row[standard_field] = None
    elif opertype == OPERTYPE_PRF:
        domain_row[standard_field] = parameter + be_converted_row[updated_column_names[0]]
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

    return domain_row, continue_flg

