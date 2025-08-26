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


def main():
    """
    主函数，执行元数据插入流程
    """
    # 获取配置信息
    workbook = load_workbook(filename=os.path.join(SPECIFIC_PATH, CONFIG_NAME))
    sheetSetting = getSheetSetting(workbook)

    # 获取相关字典和配置
    caseDict = getCaseDict(workbook, sheetSetting)
    fileDict = getFileDict(workbook, sheetSetting)
    _, _, codeDict4other = getCodeListInfo(workbook, sheetSetting)
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
        
        # 创建暂存表（使用AUTO_INCREMENT主键，无二级索引）
        staging_table_name = f"{METADATA_TABLE_NAME}_STAGING"
        staging_sql = f"""
        CREATE TABLE IF NOT EXISTS {staging_table_name} (
            No INT AUTO_INCREMENT PRIMARY KEY,
            FILENAME VARCHAR(100),
            ROWNUM INT,
            USUBJID VARCHAR(50),
            SUBJID VARCHAR(50),
            FIELDLBL VARCHAR(200),
            FIELDID VARCHAR(100),
            METAVAL TEXT,
            FORMVAL TEXT,
            DATETYPE BOOLEAN,
            CODELISTID VARCHAR(100),
            CHKFIELDID VARCHAR(100)
        ) ENGINE=InnoDB
        """
        db.cursor.execute(f"DROP TABLE IF EXISTS {staging_table_name}")
        db.cursor.execute(staging_sql)
        # 暂存表已创建
        
        data = []
        # 统计与计时变量
        total_files_processed = 0
        total_records_to_insert = 0
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

                        tFORMVAL = make_format_value(tMETAVAL, tDATETYPE, field_param, row, codeDict4other)
                        data.append((fileName, tROWNUM, tUSUBJID, tSUBJID, tFIELDLBL, tFIELDID, tMETAVAL, tFORMVAL, tDATETYPE, tCODELISTID, tCHKFIELDID))

            total_files_processed += 1

        build_elapsed = time.perf_counter() - build_start
        total_records_to_insert = len(data)
        
        # 生成CSV文件用于LOAD DATA
        csv_file_path = os.path.join(SPECIFIC_PATH, f"{METADATA_TABLE_NAME}_staging.csv")
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            # 不写入表头，直接写入数据行（对应暂存表除了AUTO_INCREMENT主键外的所有列）
            for row in data:
                # 转换DATETYPE为1/0（MySQL BOOLEAN）
                row_list = list(row)
                row_list[8] = 1 if row_list[8] else 0  # DATETYPE列
                csv_writer.writerow(row_list)
        # CSV文件生成完成

        # 使用LOAD DATA进行批量导入
        load_data_start = time.perf_counter()
        
        # 性能优化设置（导入窗口内临时使用）
        # 设置性能优化参数
        optimization_settings = [
            "SET SESSION foreign_key_checks = 0",
            "SET SESSION unique_checks = 0", 
            "SET SESSION sql_log_bin = 0",  # 如果不需要复制到从库
        ]
        
        for setting in optimization_settings:
            try:
                db.cursor.execute(setting)
            except Exception as e:
                print(f"⚠ 设置跳过: {setting}, 错误: {e}")
        
        # 执行LOAD DATA INFILE
        # 使用绝对路径并处理Windows路径分隔符
        csv_file_path_normalized = csv_file_path.replace('\\', '/')
        load_data_sql = f"""
        LOAD DATA LOCAL INFILE '{csv_file_path_normalized}'
        INTO TABLE {staging_table_name}
        FIELDS TERMINATED BY ','
        OPTIONALLY ENCLOSED BY '"'
        LINES TERMINATED BY '\\n'
        (FILENAME, ROWNUM, USUBJID, SUBJID, FIELDLBL, FIELDID, METAVAL, FORMVAL, DATETYPE, CODELISTID, CHKFIELDID)
        """
        
        db.cursor.execute(load_data_sql)
        db.connection.commit()
        
        # 检查导入结果
        db.cursor.execute(f"SELECT COUNT(*) FROM {staging_table_name}")
        imported_count = db.cursor.fetchone()[0]
        load_data_elapsed = time.perf_counter() - load_data_start
        
        print(f"LOAD DATA完成: {imported_count} 条记录, 耗时: {load_data_elapsed:.3f}s")
        
        # 从暂存表转移数据到正式表（保持原有表结构和索引）
        transfer_start = time.perf_counter()
        print("从暂存表转移数据到正式表...")
        
        # 清空正式表（如果需要）
        db.cursor.execute(f"TRUNCATE TABLE {METADATA_TABLE_NAME}")
        
        # 使用INSERT INTO ... SELECT 转移数据，手动分配顺序主键No
        # 分批转移数据以显示进度（同时手动分配No）
        db.cursor.execute(f"SELECT COUNT(*) FROM {staging_table_name}")
        total_staging_records = db.cursor.fetchone()[0]
        batch_size = 50000
        current_no = 1
        
        for offset in range(0, total_staging_records, batch_size):
            batch_sql = f"""
            INSERT INTO {METADATA_TABLE_NAME} 
            (No, FILENAME, ROWNUM, USUBJID, SUBJID, FIELDLBL, FIELDID, METAVAL, FORMVAL, DATETYPE, CODELISTID, CHKFIELDID)
            SELECT 
            @row_number := @row_number + 1 as No,
            FILENAME, ROWNUM, USUBJID, SUBJID, FIELDLBL, FIELDID, METAVAL, FORMVAL, DATETYPE, CODELISTID, CHKFIELDID
            FROM (SELECT @row_number := {current_no - 1}) r, 
            (SELECT * FROM {staging_table_name} ORDER BY No LIMIT {batch_size} OFFSET {offset}) s
            """
            
            db.cursor.execute(batch_sql)
            current_no += batch_size
            
            # 显示进度
            if offset + batch_size < total_staging_records:
                progress = min(offset + batch_size, total_staging_records)
                print(f"转移进度: {progress}/{total_staging_records} ({progress/total_staging_records*100:.1f}%)")
        
        db.connection.commit()
        
        # 验证转移结果
        db.cursor.execute(f"SELECT COUNT(*) FROM {METADATA_TABLE_NAME}")
        final_count = db.cursor.fetchone()[0]
        transfer_elapsed = time.perf_counter() - transfer_start
        
        print(f"数据转移完成: {final_count} 条记录, 耗时: {transfer_elapsed:.3f}s")
        
        # 清理暂存表和CSV文件
        try:
            db.cursor.execute(f"DROP TABLE {staging_table_name}")
            os.remove(csv_file_path)
        except Exception as e:
            print(f"⚠ 清理时出现警告: {e}")
        
        # 恢复优化设置
        restore_settings = [
            "SET SESSION foreign_key_checks = 1",
            "SET SESSION unique_checks = 1",
            "SET SESSION sql_log_bin = 1",
        ]
        
        for setting in restore_settings:
            try:
                db.cursor.execute(setting)
            except Exception as e:
                print(f"⚠ 恢复设置跳过: {setting}, 错误: {e}")
        
        # 总结统计输出
        t_total_elapsed = time.perf_counter() - t_total_start
        overall_rps = (total_records_to_insert / t_total_elapsed) if t_total_elapsed > 0 else 0.0

        print("—— 性能统计 ——")
        print(f"处理文件数: {total_files_processed}")
        print(f"准备插入记录数: {total_records_to_insert}")
        print(f"实际插入记录数: {final_count}")
        print(f"总耗时: {t_total_elapsed:.3f}s")
        print(f"总体吞吐: {overall_rps:.1f} rec/s")
        
    except Exception as e:
        print(f'Error: {e}')
        traceback.print_exc()
    finally:
        if db.cursor:
            db.cursor.close()
            print('Cursor closed.')
        if db.connection.is_connected():
            db.disconnect()
            print('Connection closed.')

if __name__ == '__main__':
    print(f'Study:{STUDY_ID} Processing has begun.' )
    main()
    print(f'Study:{STUDY_ID} Processing is over.' )
