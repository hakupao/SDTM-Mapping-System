"""
VAPORCONE 项目数据清洗模块

该模块负责对原始数据进行清洗处理，包括：
- 根据配置筛选需要迁移的数据
- 分离迁移和非迁移的列
- 处理空白行和无效数据
- 输出清洗后的数据文件
"""

from VC_BC03_fetchConfig import *
# 导入研究特定的排序函数，如果导入失败则跳过排序处理
try:
    from studySpecific.CIRCULATE.VC_BC05_studyFunctions import sort_csv_data
    SORT_FUNCTION_AVAILABLE = True
except ImportError:
    print("警告：未找到排序函数，将跳过排序处理")
    SORT_FUNCTION_AVAILABLE = False


def main():
    """
    主函数，执行数据清洗流程
    """
    logger = create_logger(
        os.path.join(SPECIFIC_PATH, 'log_file.log'), 
        log_level=logging.DEBUG
    )

    create_directory(
        CLEANINGSTEP_PATH, 
        CLEANINGSTEP_TRANSFER_FILE_PATH, 
        CLEANINGSTEP_NOT_TRANSFER_COLS_PATH, 
        CLEANINGSTEP_NOT_TRANSFER_ROWS_PATH
    )

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
        
        # 对迁移数据进行排序处理，如果VC_BC05_studyFunctions.py没有sort_csv_data函数，则跳过处理
        if not transfer_file_fields:
            print(f'Study:[{STUDY_ID}] File:[{shorten_name}] is not migration')
            continue
        
        if transfer_data and SORT_FUNCTION_AVAILABLE:
            try:
                transfer_data = sort_csv_data(transfer_data, shorten_name, subjid_field_id)
                print(f'Study:[{STUDY_ID}] File:[{shorten_name}] Transfer data sorted: {len(transfer_data)} records')
                logger.info(f'Study:[{STUDY_ID}] File:[{shorten_name}] Transfer data sorted: {len(transfer_data)} records')
            except Exception as e:
                print(f'Study:[{STUDY_ID}] File:[{shorten_name}] 排序处理失败，跳过排序: {str(e)}')
                logger.warning(f'Study:[{STUDY_ID}] File:[{shorten_name}] 排序处理失败，跳过排序: {str(e)}')
        elif transfer_data and not SORT_FUNCTION_AVAILABLE:
            print(f'Study:[{STUDY_ID}] File:[{shorten_name}] 排序函数不可用，跳过排序处理')
            logger.info(f'Study:[{STUDY_ID}] File:[{shorten_name}] 排序函数不可用，跳过排序处理')
        
        # 移行データを出力
        if transfer_file_fields:
            with open(os.path.join(CLEANINGSTEP_TRANSFER_FILE_PATH, f'{PREFIX_C}{shorten_name}{EXTENSION}'), 'w', newline=MARK_BLANK, encoding="utf-8-sig") as writer_transfer_file:
                transfer_writer = csv.DictWriter(writer_transfer_file, fieldnames=transfer_file_fields)
                transfer_writer.writeheader()
                transfer_writer.writerows(transfer_data)

        # 移行以外のデータを出力
        if not_transfer_file_fields:
            with open(os.path.join(CLEANINGSTEP_NOT_TRANSFER_COLS_PATH, f'{PREFIX_DC}{shorten_name}{EXTENSION}'), 'w', newline=MARK_BLANK, encoding="utf-8-sig") as writer_not_transfer_file:
                not_transfer_writer = csv.DictWriter(writer_not_transfer_file, fieldnames=not_transfer_file_fields)
                not_transfer_writer.writeheader()
                not_transfer_writer.writerows(not_transfer_data)

        if not_transfer_rows_data:
            with open(os.path.join(CLEANINGSTEP_NOT_TRANSFER_ROWS_PATH, f'{PREFIX_DR}{shorten_name}{EXTENSION}'), 'w', newline=MARK_BLANK, encoding="utf-8-sig") as writer_not_transfer_case_file:
                not_transfer_case_writer = csv.DictWriter(writer_not_transfer_case_file, fieldnames=header)
                not_transfer_case_writer.writeheader()
                not_transfer_case_writer.writerows(not_transfer_rows_data)

if __name__ == "__main__":
    print(f'Study:{STUDY_ID} Processing has begun.' )
    main()
    print(f'Study:{STUDY_ID} Processing is over.' )
