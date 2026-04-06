"""
VAPORCONE 项目数据清洗模块

该模块负责对原始数据进行清洗处理，包括：
- 根据配置筛选需要迁移的数据
- 分离迁移和非迁移的列
- 处理空白行和无效数据
- 输出清洗后的数据文件
"""

from VC_BC03_fetchConfig import *

STEP_ID = 'OP01'
STEP_NAME = 'Cleaning'


def main():
    """
    主函数，执行数据清洗流程
    """
    logger = create_logger(
        os.path.join(SPECIFIC_PATH, 'log_file.log'),
        log_level=logging.DEBUG
    )

    # 创建时间戳文件夹并获取实际路径
    actual_cleaning_path = create_directory(CLEANINGSTEP_PATH, CLEANINGSTEP_TRANSFER_FILE_PATH)

    # 构建实际的子文件夹路径并创建
    actual_deleted_cols_path = os.path.join(actual_cleaning_path, 'deletedCols')
    actual_deleted_rows_path = os.path.join(actual_cleaning_path, 'deletedRows')

    os.makedirs(actual_deleted_cols_path, exist_ok=True)
    os.makedirs(actual_deleted_rows_path, exist_ok=True)

    print(f'输出路径: {actual_cleaning_path}')
    print(f'  ├── 清洗数据: {actual_cleaning_path}')
    print(f'  ├── 删除列:   {actual_deleted_cols_path}')
    print(f'  └── 删除行:   {actual_deleted_rows_path}')

    workbook = load_workbook(filename=os.path.join(SPECIFIC_PATH, CONFIG_NAME))
    sheetSetting = getSheetSetting(workbook)
    caseDict = getCaseDict(workbook, sheetSetting)
    fileDict = getFileDict(workbook, sheetSetting)
    fieldDict, _, _, _ = getProcess(workbook, sheetSetting)

    fileList = list(fileDict.keys())
    print(f'配置加载完成: 受试者={len(caseDict)}, 文件={len(fileList)}')
    print_summary_sep()

    # 获取原始数据文件列表
    all_files = os.listdir(RAW_DATA_ROOT_PATH)
    files_only = [
        file for file in all_files
        if os.path.isfile(os.path.join(RAW_DATA_ROOT_PATH, file))
    ]

    # 处理摘要收集
    summary = []

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
            msg = (f'原始数据文件未找到: [{shorten_name}], '
                   f'搜索路径: {RAW_DATA_ROOT_PATH}, 可用文件: {files_only}')
            log_and_print(logger, 'ERROR', msg)
            sys.exit(1)

        file_param = fileDict[shorten_name]
        subjid_field_id = file_param[COL_SUBJIDFIELDID]
        processing_logic = file_param[COL_PROCESSINGLOGIC]

        if shorten_name not in fieldDict:
            log_and_print(logger, 'SKIP', f'{shorten_name}: 无迁移字段配置')
            continue
        transfer_file_fields = fieldDict[shorten_name]
        not_transfer_file_fields = fieldDict[PREFIX_DC + shorten_name]

        header = []
        transfer_data = []
        not_transfer_data = []
        not_transfer_rows_data = []
        title_row = fileDict[shorten_name][COL_TITLEROW]
        data_row = fileDict[shorten_name][COL_DATARROW]

        # 行级统计
        count_total = 0
        count_excluded_patient = 0
        count_excluded_logic = 0
        count_blank = 0
        not_define_fields = set()

        with open(os.path.join(RAW_DATA_ROOT_PATH, full_name), 'r', newline=MARK_BLANK, encoding="utf-8-sig") as read_file:
            csv_reader = csv.reader(read_file)

            for _ in range(title_row - 1):
                next(csv_reader, None)

            header = next(csv_reader)

            for _ in range(data_row - title_row - 1):
                next(csv_reader, None)

            dict_result = csv.DictReader(read_file, fieldnames=header)
            header = dict_result.fieldnames

            for row in dict_result:
                count_total += 1
                subjid_field_val = row[subjid_field_id]

                if subjid_field_val not in caseDict:
                    not_transfer_rows_data.append(row)
                    count_excluded_patient += 1
                    continue

                if processing_logic and not eval(file_param[COL_PROCESSINGLOGIC], {"__builtins__": {}}, {"row": row}):
                    not_transfer_rows_data.append(row)
                    count_excluded_logic += 1
                    continue

                isBlankRow = True
                for key, value in row.items():
                    if key != subjid_field_id and key in transfer_file_fields and value:
                        isBlankRow = False
                        break

                if isBlankRow:
                    not_transfer_rows_data.append(row)
                    count_blank += 1
                    logger.info(f'File:[{full_name}] Patient:[{subjid_field_val}] 空白行(第{count_total}行)')
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
            log_and_print(
                logger, 'WARN',
                f'{shorten_name}: {len(not_define_fields)} 个未定义字段 {not_define_fields} '
                f'(原始文件中存在但Process工作表中未配置)'
            )

        if not transfer_file_fields:
            log_and_print(logger, 'SKIP', f'{shorten_name}: 无迁移字段')
            continue

        count_migrated = len(transfer_data)

        # 输出清洗数据
        with open(os.path.join(actual_cleaning_path, f'{PREFIX_C}{shorten_name}{EXTENSION}'), 'w', newline=MARK_BLANK, encoding="utf-8-sig") as writer_transfer_file:
            transfer_writer = csv.DictWriter(writer_transfer_file, fieldnames=transfer_file_fields)
            transfer_writer.writeheader()
            transfer_writer.writerows(transfer_data)

        # 输出未迁移列数据
        if not_transfer_file_fields:
            with open(os.path.join(actual_deleted_cols_path, f'{PREFIX_DC}{shorten_name}{EXTENSION}'), 'w', newline=MARK_BLANK, encoding="utf-8-sig") as writer_not_transfer_file:
                not_transfer_writer = csv.DictWriter(writer_not_transfer_file, fieldnames=not_transfer_file_fields)
                not_transfer_writer.writeheader()
                not_transfer_writer.writerows(not_transfer_data)

        # 输出未迁移行数据
        if not_transfer_rows_data:
            with open(os.path.join(actual_deleted_rows_path, f'{PREFIX_DR}{shorten_name}{EXTENSION}'), 'w', newline=MARK_BLANK, encoding="utf-8-sig") as writer_not_transfer_case_file:
                not_transfer_case_writer = csv.DictWriter(writer_not_transfer_case_file, fieldnames=header)
                not_transfer_case_writer.writeheader()
                not_transfer_case_writer.writerows(not_transfer_rows_data)

        # 记录单文件摘要
        summary.append({
            'file': shorten_name, 'total': count_total, 'migrated': count_migrated,
            'excluded_patient': count_excluded_patient, 'excluded_logic': count_excluded_logic,
            'blank': count_blank, 'undefined_fields': len(not_define_fields),
            'transfer_cols': len(transfer_file_fields), 'deleted_cols': len(not_transfer_file_fields),
        })
        logger.info(
            f'File:[{shorten_name}] 总行数={count_total}, 迁移={count_migrated}, '
            f'排除(患者)={count_excluded_patient}, 排除(逻辑)={count_excluded_logic}, 空行={count_blank}'
        )

    # 处理摘要
    W = [14, 8, 8, 10, 10, 8, 8]  # 各列显示宽度
    cols = ['文件', '总行数', '迁移', '排除患者', '排除逻辑', '空行', '未定义']
    print_summary_header(f'处理摘要 - {STEP_NAME}')
    print(
        cjk_ljust(cols[0], W[0]) + ' '
        + ' '.join(cjk_rjust(c, w) for c, w in zip(cols[1:], W[1:]))
    )
    print_summary_sep()
    total_all = total_migrated = total_excluded = 0
    for s in summary:
        print(
            f'{s["file"]:<{W[0]}} {s["total"]:>{W[1]}} {s["migrated"]:>{W[2]}} '
            f'{s["excluded_patient"]:>{W[3]}} {s["excluded_logic"]:>{W[4]}} {s["blank"]:>{W[5]}} '
            f'{s["undefined_fields"]:>{W[6]}}'
        )
        total_all += s['total']
        total_migrated += s['migrated']
        total_excluded += s['excluded_patient'] + s['excluded_logic'] + s['blank']
    print_summary_sep()
    print_summary_kv('处理文件数', len(summary))
    print_summary_kv('跳过文件数', len(fileList) - len(summary))
    print_summary_kv('总行数', total_all)
    print_summary_kv('总迁移行数', total_migrated)
    print_summary_kv('总排除行数', total_excluded)


if __name__ == "__main__":
    print_step_header(STEP_ID, STEP_NAME)
    main()
    print_step_footer(STEP_ID, STEP_NAME)
