"""
VAPORCONE 项目元数据插入模块

该模块负责将处理后的数据作为元数据插入到数据库中，包括：
- 读取清洗后的数据文件
- 判断字段类型（日期类型等）
- 格式化字段值
- 插入元数据表
"""

from VC_BC03_fetchConfig import *
import time  # 性能计时

STEP_ID = 'OP03'
STEP_NAME = 'InsertMetadata'


def main():
    """
    主函数，执行元数据插入流程
    """
    logger = create_logger(
        os.path.join(SPECIFIC_PATH, 'log_file.log'),
        log_level=logging.DEBUG
    )

    # 获取配置信息
    workbook = load_workbook(filename=os.path.join(SPECIFIC_PATH, CONFIG_NAME))
    sheetSetting = getSheetSetting(workbook)

    # 获取相关字典和配置
    caseDict = getCaseDict(workbook, sheetSetting)
    fileDict = getFileDict(workbook, sheetSetting)
    # 注意：已移除4OTHER功能，不再需要codeDict4other
    codeDict, _ = getCodeListInfo(workbook, sheetSetting)
    _, transFieldDict, _, _ = getProcess(workbook, sheetSetting)

    # 根据mapping定义的SDTM字段判断是否为日期型
    # SDTM字段以DTC结尾则说明mapping至该字段的原文件字段一定为日期型，否则则一定不是
    dateTypeDict = {}
    mappingDict, _ = getMapping(workbook, sheetSetting)
    
    for domain_val in mappingDict.values():
        for row_param in domain_val.values():
            for variable in row_param.keys():
                if variable in TIME_VARIABLE or row_param[variable]['SUPPTIMEFLG']:
                    rFieldName = row_param[variable][COL_FIELDNAME]
                    if re.match(PATTERN_CYCLE_PRA, rFieldName):
                        rFieldName = re.sub(PATTERN_CYCLE_PRA, r"\1", rFieldName)
                    fieldname_list = rFieldName.split(MARK_DOLLAR)
                    for fieldname in fieldname_list:
                        dateTypeDict[fieldname] = True
                    
    # 总体计时开始
    t_total_start = time.perf_counter()
                    
    db = DatabaseManager()
    db.connect()
    try:
        # 创建正式表
        db.create_metadata_table(METADATA_TABLE_NAME)
        
        data = []
        # 统计与计时变量
        total_files_processed = 0
        total_records_to_insert = 0
        file_summary = []  # 按文件统计
        build_start = time.perf_counter()
        
        # 🆕 动态获取最新的清洗数据文件夹路径
        actual_cleaning_path = find_latest_timestamped_path(CLEANINGSTEP_PATH, 'cleaning_dataset')
        # 使用最新的清洗数据路径
        
        # 获取清洗后的数据文件列表
        all_files = os.listdir(actual_cleaning_path)
        files_only = [
            file for file in all_files 
            if os.path.isfile(os.path.join(actual_cleaning_path, file))
        ]
        
        eligible_files = [f for f in fileDict.keys() if f in transFieldDict]
        progress_build = ProgressReporter(total=len(eligible_files), desc='Build')

        for fileName in fileDict.keys():
            if fileName not in transFieldDict:
                continue
            
            # 查找对应的清洗文件
            full_name = next((
                file_name for file_name in files_only 
                if f'C-{fileName}{EXTENSION}' == file_name
            ), None)
            
            if not full_name:
                full_name = next((
                    file_name for file_name in files_only 
                    if f'C-{fileName}{EXTENSION}' in file_name
                ), None)
            
            if not full_name:
                print(f'{fileName}{EXTENSION} is undefined')
                sys.exit()

            subjectId_fieldID = fileDict[fileName][COL_SUBJIDFIELDID]
            file_param = transFieldDict[fileName]
            file_record_count = 0
            with open(os.path.join(actual_cleaning_path, full_name), 'r', newline=MARK_BLANK, encoding='utf-8-sig') as read_file:
                dict_result = csv.DictReader(read_file)
                tROWNUM = 0
                for row in dict_result:
                    tROWNUM += 1
                    tSUBJID = row[subjectId_fieldID]
                    tUSUBJID = caseDict[tSUBJID]
                    for tFIELDID, field_param in file_param.items():
                        if tFIELDID == subjectId_fieldID:
                            continue
                        if tFIELDID not in row:
                            continue

                        tMETAVAL = row[tFIELDID].strip()

                        if not tMETAVAL:
                            continue

                        tFIELDLBL = field_param[COL_LABEL]
                        tCODELISTID = field_param[COL_CODELISTNAME]
                        tCHKFIELDID = field_param[COL_CHKTYPE]
                        tDATETYPE = dateTypeDict[tFIELDID] if tFIELDID in dateTypeDict else False

                        tFORMVAL = make_format_value(tMETAVAL, tDATETYPE)
                        data.append((fileName, tROWNUM, tUSUBJID, tSUBJID, tFIELDLBL, tFIELDID, tMETAVAL, tFORMVAL, tDATETYPE, tCODELISTID, tCHKFIELDID))
                        file_record_count += 1

            file_summary.append({
                'file': fileName, 'rows': tROWNUM,
                'fields': len(file_param), 'records': file_record_count,
            })
            total_files_processed += 1
            progress_build.update()

        progress_build.finish()
        build_elapsed = time.perf_counter() - build_start
        total_records_to_insert = len(data)
        
        final_count = db.load_metadata_rows(METADATA_TABLE_NAME, data)

        # 处理摘要
        t_total_elapsed = time.perf_counter() - t_total_start
        overall_rps = (total_records_to_insert / t_total_elapsed) if t_total_elapsed > 0 else 0.0

        TW = [14, 8, 8, 10]
        tcols = ['文件', '数据行', '字段数', '元数据条数']
        print_summary_header(f'处理摘要 - {STEP_NAME}')
        print(
            cjk_ljust(tcols[0], TW[0]) + ' '
            + ' '.join(cjk_rjust(c, w) for c, w in zip(tcols[1:], TW[1:]))
        )
        print_summary_sep()
        for s in file_summary:
            print(
                f'{s["file"]:<{TW[0]}} {s["rows"]:>{TW[1]}} {s["fields"]:>{TW[2]}} '
                f'{s["records"]:>{TW[3]}}'
            )
        print_summary_sep()
        print_summary_kv('处理文件数', total_files_processed)
        print_summary_kv('准备插入记录数', total_records_to_insert)
        print_summary_kv('实际插入记录数', final_count)
        print_summary_kv('总耗时', f'{t_total_elapsed:.3f}s')
        print_summary_kv('总体吞吐', f'{overall_rps:.1f} rec/s')
        logger.info(
            f'Metadata插入完成: 文件={total_files_processed}, '
            f'记录={final_count}, 耗时={t_total_elapsed:.3f}s'
        )

    except Exception as e:
        log_and_print(logger, 'ERROR', f'Metadata插入失败: {e}')
        traceback.print_exc()
    finally:
        if db.cursor:
            db.cursor.close()
        if db.connection and db.connection.is_connected():
            db.disconnect()

if __name__ == '__main__':
    print_step_header(STEP_ID, STEP_NAME)
    main()
    print_step_footer(STEP_ID, STEP_NAME)
