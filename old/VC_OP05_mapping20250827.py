"""
VAPORCONE 项目映射模块

该模块负责将格式化的数据映射为SDTM标准格式，包括：
- 读取映射配置
- 执行字段映射操作
- 处理序列号生成
- 生成SDTM数据集
"""

from VC_BC03_fetchConfig import *
from old.VC_BC04_operateType import *


def main():
    """
    主函数，执行数据映射流程
    """
    logger = create_logger(
        os.path.join(SPECIFIC_PATH, 'log_file.log'), 
        log_level=logging.DEBUG
    )
    sdtm_dataset_path = create_directory(SDTMDATASET_PATH, SDTMDATASET_FILE_PATH)
    
    # 🆕 动态获取最新的格式化数据文件夹路径
    actual_format_path = find_latest_timestamped_path(FORMAT_PATH, 'format_dataset')
    print(f'使用格式化数据路径: {actual_format_path}')
    
    workbook = load_workbook(filename=os.path.join(SPECIFIC_PATH, CONFIG_NAME))
    sheetSetting = getSheetSetting(workbook)
    caseDict = getCaseDict(workbook, sheetSetting)
    codeDict, _, _ = getCodeListInfo(workbook, sheetSetting)
    mappingDict, definition_merge_rule = getMapping(workbook, sheetSetting)
    domainsSettingDict = getDomainsSetting(workbook, sheetSetting)
    
    # 初始化序列号字典
    sequenceDict = {}
    for usubjid in caseDict.values():
        if usubjid not in sequenceDict:
            sequenceDict[usubjid] = {}
        for domain_name in STANDARD_FIELDS.keys():
            sequenceDict[usubjid][domain_name] = 1
				
    domain_dataset = {}

    # 循环所有移行目的Domain
    for domain_key, domain_param in mappingDict.items():
        seq_field = domain_key + VARIABLE_SEQSUFF

        # 把转换后的domain存入domain_dataset
        if domain_key not in domain_dataset:
            domain_dataset[domain_key] = []

        # 每个domain的全部字段（包括标准和非标准字段，非标准字段来源于mapping）
        standard_fields = STANDARD_FIELDS[domain_key]

        # 去重
        unique_combinations = set()

        # 循环每个处理
        for definition_row_num, definition_param in domain_param.items():
            # sort_keys = {0: VARIABLE_USUBJID}
            combo_file_name = definition_merge_rule[definition_row_num][COL_MERGERULE]
            if not combo_file_name:
                print(f'{definition_row_num} MERGERULE is null')
                continue
            cycle_time = definition_merge_rule[definition_row_num][COL_DEFINITION]

            be_converted_list = pandas.read_csv(os.path.join(actual_format_path, f'{PREFIX_F}{combo_file_name}{EXTENSION}'), dtype=str, na_filter=False)

            # column_names = be_converted_list.columns.tolist()
            for i in range(cycle_time):
                definition_dataset = []

                # 循环移行对象的行
                for index, be_converted_row in be_converted_list.iterrows():
                    null_deletion = False
                    continue_flg = False
                    row_subjid = be_converted_row[VARIABLE_SUBJID]
                    row_usubjid = caseDict[row_subjid]

                    domain_row = {key: 
                                  STUDY_ID if key == VARIABLE_STUDYID else 
                                  domain_key if key == VARIABLE_DOMAIN else
                                  row_usubjid if key == VARIABLE_USUBJID else
                                  row_subjid if key == VARIABLE_SUBJID else
                                  MARK_BLANK for key in standard_fields}
                    
                    # 循环处理的每行
                    for standard_field, sdtm_field_param in definition_param.items():
                        fieldname_list = []
                        updated_column_names = []
                        fieldname = sdtm_field_param[COL_FIELDNAME]
                        # 该处理循环多次时 fieldname 的处理
                        if re.match(PATTERN_CYCLE_PRA, fieldname):
                            fieldname_str = re.sub(PATTERN_CYCLE_PRA, r"\1", fieldname)
                            fieldname_list = fieldname_str.split(MARK_DOLLAR)
                            updated_column_names = [fieldname_list[i]]
                        else:
                            fieldname_list = [f for f in fieldname.split(MARK_DOLLAR) if f]
                            updated_column_names = fieldname_list

                        opertype = sdtm_field_param[COL_OPERTYPE]

                        parameter = sdtm_field_param[COL_PARAMETER]
                        # 该处理循环多次时 parameter 的处理
                        if re.match(PATTERN_CYCLE_PRA, parameter):
                            parameter_str = re.sub(PATTERN_CYCLE_PRA, r"\1", parameter)
                            parameter_list = parameter_str.split(MARK_DOLLAR)
                            parameter = parameter_list[i]

                        domain_row, continue_flg = doMapping(domain_row, standard_field, opertype, parameter, be_converted_row, updated_column_names, codeDict, continue_flg, definition_row_num)
                        
                        if sdtm_field_param[COL_NDKEY] and domain_row[standard_field]:
                            null_deletion = True

                    # 不符合mapping的条件（SEL）
                    if continue_flg:
                        continue

                    # 根据mapping的E列中,任何为〇的字段有值就转换,否则就跳过
                    if null_deletion:
                        # 去重,如果转换后的两行一模一样就只取一行
                        combination = tuple(domain_row[s] for s in standard_fields)
                        if combination not in unique_combinations:
                            unique_combinations.add(combination)
                            definition_dataset.append(domain_row)

                if seq_field in standard_fields:
                    if domain_key in domainsSettingDict:
                        sort_keys = domainsSettingDict[domain_key]
                    else:    
                        sort_keys = [VARIABLE_USUBJID]
                    
                    definition_dataset.sort(key=lambda x: [
                        int(x[sortField].replace('TREATMENT', '')) if sortField == 'EPOCH' and x[sortField] and 'TREATMENT' in x[sortField] else
                        int(x[sortField]) if sortField == 'EPOCH' and x[sortField] else
                        x[sortField]
                        for sortField in sort_keys
                    ])
                    
                    prev_usubjid = None
                    seq_counter = 1
                    for item in definition_dataset:
                        usubjid = item[VARIABLE_USUBJID]
                        if usubjid != prev_usubjid:
                            seq_counter = sequenceDict[usubjid][domain_key]
                        item[seq_field] = str(seq_counter) 
                        seq_counter += 1
                        sequenceDict[usubjid][domain_key] = seq_counter
                        prev_usubjid = usubjid
                    
                domain_dataset[domain_key].extend(definition_dataset)
                
        print(f'{domain_key} conversion is completed.')
                
    # 输出全部转换完毕的domain
    for domain, dataList in domain_dataset.items():
        header = STANDARD_FIELDS[domain]
        if dataList:
            dataList.sort(
                key=lambda x: tuple(int(x[var]) if var == f'{domain}{VARIABLE_SEQSUFF}' else x[var] for var in (VARIABLE_USUBJID, f'{domain}{VARIABLE_SEQSUFF}') if var in header)
            )
            with open(os.path.join(sdtm_dataset_path, f'{domain}{EXTENSION}'), 'w', newline=MARK_BLANK, encoding='utf-8-sig') as file:
                writer = csv.DictWriter(file, fieldnames=header)
                writer.writeheader()
                writer.writerows(dataList)
        print(f'{domain} file is saved.')

if __name__ == "__main__":
    print(f'Study:{STUDY_ID} Processing has begun.' )
    main()
    print(f'Study:{STUDY_ID} Processing is over.' )
