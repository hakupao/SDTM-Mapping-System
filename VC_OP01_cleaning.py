"""
VAPORCONE 项目数据清洗模块

该模块负责对原始数据进行清洗处理，包括：
- 根据配置筛选需要迁移的数据
- 分离迁移和非迁移的列
- 处理空白行和无效数据
- 输出清洗后的数据文件
"""

from VC_BC03_fetchConfig import *

def main():
    """
    主函数，执行数据清洗流程
    """
    logger = create_logger(
        os.path.join(SPECIFIC_PATH, 'log_file.log'), 
        log_level=logging.DEBUG
    )

    # 🆕 创建时间戳文件夹并获取实际路径
    # 只对主文件夹应用时间戳，子文件夹手动创建
    actual_cleaning_path = create_directory(CLEANINGSTEP_PATH, CLEANINGSTEP_TRANSFER_FILE_PATH)
    
    # 构建实际的子文件夹路径并创建
    actual_deleted_cols_path = os.path.join(actual_cleaning_path, 'deletedCols')
    actual_deleted_rows_path = os.path.join(actual_cleaning_path, 'deletedRows')
    
    # 手动创建子文件夹
    os.makedirs(actual_deleted_cols_path, exist_ok=True)
    os.makedirs(actual_deleted_rows_path, exist_ok=True)
    
    print(f'使用清洗输出路径: {actual_cleaning_path}')
    print(f'  ├── 清洗数据: {actual_cleaning_path}')
    print(f'  ├── 删除列: {actual_deleted_cols_path}') 
    print(f'  └── 删除行: {actual_deleted_rows_path}')

    workbook = load_workbook(filename=os.path.join(SPECIFIC_PATH, CONFIG_NAME))
    sheetSetting = getSheetSetting(workbook)
    caseDict = getCaseDict(workbook, sheetSetting)
    fileDict = getFileDict(workbook, sheetSetting)
    fieldDict, _, _, _ = getProcess(workbook, sheetSetting)

    fileList = list(fileDict.keys())

    # 获取原始数据文件列表
    all_files = os.listdir(RAW_DATA_ROOT_PATH)
    files_only = [
        file for file in all_files 
        if os.path.isfile(os.path.join(RAW_DATA_ROOT_PATH, file))
    ]
    
    for shorten_name in fileList:
        # 优先查找完全匹配的文件名
        full_name = next((
            file_name for file_name in files_only 
            if f'{shorten_name}{EXTENSION}' == file_name
        ), None)
        
        # 如果没有找到，查找包含短名称的文件
        if not full_name:
            full_name = next((
                file_name for file_name in files_only 
                if shorten_name in file_name
            ), None)
        
        if not full_name:
            print(f'Study:[{STUDY_ID}] File:[{shorten_name}] is not existed')
            sys.exit()

        file_param = fileDict[shorten_name]
        subjid_field_id = file_param[COL_SUBJIDFIELDID]
        processing_logic = file_param[COL_PROCESSINGLOGIC]

        if shorten_name not in fieldDict:
            print(f'Study:[{STUDY_ID}] File:[{shorten_name}] is not migration')
            continue
        transfer_file_fields = fieldDict[shorten_name]
        not_transfer_file_fields = fieldDict[PREFIX_DC + shorten_name]

        header = []
        transfer_data = []
        not_transfer_data = []
        not_transfer_rows_data = []
        title_row = fileDict[shorten_name][COL_TITLEROW] 
        data_row = fileDict[shorten_name][COL_DATARROW]
        with open(os.path.join(RAW_DATA_ROOT_PATH, full_name), 'r', newline=MARK_BLANK, encoding="utf-8-sig") as read_file:
            csv_reader = csv.reader(read_file)

            for _ in range(title_row - 1):
                next(csv_reader, None)

            header = next(csv_reader)

            for _ in range(data_row - title_row - 1):
                next(csv_reader, None)

            dict_result = csv.DictReader(read_file, fieldnames=header) 
            header = dict_result.fieldnames
            not_define_fields = set()

            for row in dict_result:
                subjid_field_val = row[subjid_field_id]
                if subjid_field_val not in caseDict:
                    not_transfer_rows_data.append(row)
                    continue

                if processing_logic and not eval(file_param[COL_PROCESSINGLOGIC]):
                    not_transfer_rows_data.append(row)
                    continue
                
                isBlankRow = True
                for key, value in row.items():
                    if key != subjid_field_id and key in transfer_file_fields and value:
                        isBlankRow = False
                        break

                if isBlankRow:
                    not_transfer_rows_data.append(row)
                    print(f'Study:[{STUDY_ID}] File:[{full_name}] Patient:[{subjid_field_val}] is null')
                    logger.info(f'Study:[{STUDY_ID}] File:[{full_name}] Patient:[{subjid_field_val}] is null')
                    continue

                transfer_row = {}
                not_transfer_row = {}
                for key, value in row.items():
                    if key in transfer_file_fields:
                        transfer_row[key] = value
                    elif key in not_transfer_file_fields:
                        not_transfer_row[key] = value
                    else:
                        not_define_fields.add(key)
                
                transfer_data.append(transfer_row)
                not_transfer_data.append(not_transfer_row)

            if not_define_fields:
                print(f'Study:[{STUDY_ID}] File:[{shorten_name}] {len(not_define_fields)} Fields:[{not_define_fields}] are undefined')
        
        if not transfer_file_fields:
            print(f'Study:[{STUDY_ID}] File:[{shorten_name}] is not migration')
            continue
        
        # 🆕 使用动态时间戳路径输出清洗数据
        if transfer_file_fields:
            with open(os.path.join(actual_cleaning_path, f'{PREFIX_C}{shorten_name}{EXTENSION}'), 'w', newline=MARK_BLANK, encoding="utf-8-sig") as writer_transfer_file:
                transfer_writer = csv.DictWriter(writer_transfer_file, fieldnames=transfer_file_fields)
                transfer_writer.writeheader()
                transfer_writer.writerows(transfer_data)

        # 🆕 使用动态时间戳路径输出未迁移列数据
        if not_transfer_file_fields:
            with open(os.path.join(actual_deleted_cols_path, f'{PREFIX_DC}{shorten_name}{EXTENSION}'), 'w', newline=MARK_BLANK, encoding="utf-8-sig") as writer_not_transfer_file:
                not_transfer_writer = csv.DictWriter(writer_not_transfer_file, fieldnames=not_transfer_file_fields)
                not_transfer_writer.writeheader()
                not_transfer_writer.writerows(not_transfer_data)

        # 🆕 使用动态时间戳路径输出未迁移行数据
        if not_transfer_rows_data:
            with open(os.path.join(actual_deleted_rows_path, f'{PREFIX_DR}{shorten_name}{EXTENSION}'), 'w', newline=MARK_BLANK, encoding="utf-8-sig") as writer_not_transfer_case_file:
                not_transfer_case_writer = csv.DictWriter(writer_not_transfer_case_file, fieldnames=header)
                not_transfer_case_writer.writeheader()
                not_transfer_case_writer.writerows(not_transfer_rows_data)

if __name__ == "__main__":
    print(f'Study:{STUDY_ID} Processing has begun.' )
    main()
    print(f'Study:{STUDY_ID} Processing is over.' )
