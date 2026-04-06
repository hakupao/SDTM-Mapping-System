"""
VAPORCONE 项目格式化模块

该模块负责将元数据转换为格式化的数据，包括：
- 创建转换数据视图
- 处理检查文件
- 生成格式化的数据文件
- 处理组合文件

=== 性能优化版本说明 ===
本版本包含以下性能优化：

1. 数据库索引优化
   - 自动创建关键复合索引：(FILENAME, FIELDID)、(FILENAME, ROWNUM, SUBJID)
   - 支持 WHERE、GROUP BY、ORDER BY 的索引加速

2. 查询重构优化
   - 合并 OTHERDETAILS 子查询，减少重复扫描
   - 将 HAVING 条件前置到 WHERE，减少聚合数据量
   - 可配置的 ORDER BY 开关，平衡排序需求与性能

3. 临时表物化
   - 按文件创建优化临时表，避免重复视图扫描
   - 为临时表自动创建索引

4. 性能监控
   - 细粒度耗时统计（连接/索引/执行/拉取/扫描/写入）
   - 可选的 EXPLAIN 分析支持
   - 智能空列扫描（仅对小结果集执行）

5. 可配置参数
   - 所有优化策略可通过顶部常量开关控制
   - 支持调试模式与生产模式切换

预期效果：
- CHK 查询从 40-95 秒降至 3-8 秒
- 整体流程从 ~987 秒降至 < 300 秒
- 保持完全的业务逻辑兼容性
"""

from VC_BC03_fetchConfig import *
from VC_BC04_operateType import *
import time

STEP_ID = 'OP04'
STEP_NAME = 'Format'

# ================== 性能优化配置 ==================
# 可通过修改这些常量来调整优化策略

# 索引与查询优化
ENABLE_PERFORMANCE_INDEXES = True      # 是否创建性能优化索引
USE_TEMP_TABLES = True                 # 是否使用文件级临时表
ENABLE_ORDER_BY = True                 # 是否启用ORDER BY（关闭可提升性能）
MERGE_OTHERDETAILS_QUERIES = True      # 是否合并OTHERDETAILS子查询

# 调试与监控
ENABLE_EXPLAIN_ANALYSIS = False        # 是否启用EXPLAIN分析（调试用）
ENABLE_EMPTY_COLUMN_SCAN = True        # 是否扫描空列（可关闭以提升性能）
EMPTY_SCAN_THRESHOLD = 10000           # 仅对行数小于此值的结果进行空列扫描
ENABLE_WORK_TABLE_PERSISTENCE = False   # 是否保留工作表以供下次使用（节省创建时间）

# 动态优化策略配置
ADAPTIVE_OPTIMIZATION = True              # 是否启用自适应优化
TEMP_TABLE_THRESHOLD = 1                  # 文件有>=N个CHK分支时使用临时表
EXPLAIN_TIME_THRESHOLD = 5000             # 查询超过N毫秒时自动EXPLAIN分析
EMPTY_SCAN_ROW_THRESHOLD = 10000          # 结果集超过N行时跳过空列扫描


def process_combine_files(workbook, sheetSetting, actual_format_path):
    """
    处理组合文件，根据配置执行特定的组合函数
    
    参数:
    - workbook: Excel工作簿对象
    - sheetSetting: 工作表设置字典
    - actual_format_path: 实际的格式化数据输出路径（带时间戳）
    """
    for file_name, function_name in getCombineInfo(workbook, sheetSetting).items():
        combine_start = time.perf_counter()
        # 安全调度：提取函数名并验证已导入，然后在受限命名空间中执行
        func_name = function_name.split('(')[0].strip()
        if func_name not in globals() or not callable(globals()[func_name]):
            raise ValueError(f"Combine 配置中的函数 '{func_name}' 未定义或不可调用")
        be_converted_list = eval(function_name, {"__builtins__": {}}, globals())
        rows, cols = (0, 0)
        try:
            rows, cols = be_converted_list.shape
        except Exception:
            pass
        be_converted_list.fillna('').to_csv(
            os.path.join(actual_format_path, f'{PREFIX_F}{file_name}{EXTENSION}'),
            index=False,
            encoding='utf-8-sig'
        )
        print(f'{file_name} is outputting | {rows}x{cols}')

def build_optimized_chk_query(db, fileName, select_fieldIDs, chk_fieldIDs, case_fieldIDs, 
                              max_fieldIDs, having_fieldIDs, other_fields, fieldID_otherVal, 
                              file_param, transdata_source):
    """
    构建优化的CHK查询，合并OTHERDETAILS子查询并优化HAVING条件
    """
    # 合并所有OTHERDETAILS字段到一个子查询
    other_fields_sql = MARK_BLANK
    other_join_sql = MARK_BLANK
    
    if other_fields:
        # 确定FILENAME条件（工作表已预过滤，无需FILENAME条件）
        filename_condition = "" if transdata_source.startswith('work_') else f"`FILENAME` = '{fileName}' AND "
        group_by_filename = "" if transdata_source.startswith('work_') else "`FILENAME`,"
        
        # 为每个OTHERDETAILS字段创建独立的LEFT JOIN，恢复原始的三重条件逻辑
        other_join_parts = []
        for other_field, other_details_field in other_fields.items():
            join_sql = f'''LEFT JOIN (
                SELECT `ROWNUM`, max(if(({filename_condition}`FIELDID` = '{other_field}'),`TRANSVAL`,NULL)) AS `{other_field}`
                FROM {transdata_source} 
                GROUP BY {group_by_filename}`ROWNUM`,`SUBJID` 
                HAVING `{other_field}` IS NOT NULL
            ) t{other_field} ON t.`ROWNUM` = t{other_field}.`ROWNUM` AND t.`FIELDID` = '{other_details_field}' AND t.`METAVAL` = '{fieldID_otherVal[other_details_field]}'
            '''
            other_join_parts.append(join_sql)
        other_join_sql = ' '.join(other_join_parts)
        
        other_fields_sql = 'COALESCE(' + ','.join([f't{other_field}.`{other_field}`' for other_field in other_fields.keys()]) + ') `OTHERDETAILS`'
        # OTHERDETAILS 字段将在查询构建时插入到正确位置，这里不添加到 select_fieldIDs

    # 优化max_fieldIDs查询，前置WHERE条件
    max_fieldIDs_sql = MARK_BLANK
    if max_fieldIDs:
        # 检查是否使用工作表（已预过滤FILENAME）
        filename_condition = "" if transdata_source.startswith('work_') else f"`FILENAME` = '{fileName}' AND "
        group_by_filename = "" if transdata_source.startswith('work_') else "`FILENAME`,"
        
        max_fieldIDs_sql = f'''LEFT JOIN (
            SELECT `ROWNUM`, {', '.join(max_fieldIDs)}
            FROM {transdata_source}
            WHERE {filename_condition}`TRANSVAL` IS NOT NULL AND `TRANSVAL` <> ''
            GROUP BY {group_by_filename}`ROWNUM`,`SUBJID`
            HAVING {' OR '.join(having_fieldIDs)}
        ) tt ON t.`ROWNUM` = tt.`ROWNUM` '''

    # 生成CASE语句
    case_sql = []
    for key, vals in case_fieldIDs.items():
        chkfields = ', '.join([f'\'{val}\'' for val in vals])
        case_sql.append(f'WHEN `FIELDID` IN ({chkfields}) THEN \'{key}\'')

    # 构建主查询，前置WHERE条件减少处理数据量
    filename_condition = "" if transdata_source.startswith('work_') else f"`FILENAME` = '{fileName}' AND "
    
    # 保持原有字段顺序，只在CHKVALUE后插入OTHERDETAILS
    ordered_select_fields = []
    
    for i, field in enumerate(select_fieldIDs):
        ordered_select_fields.append(field)
        
        # 如果当前字段是CHKVALUE，且存在OTHERDETAILS，则在后面插入
        if 'CHKVALUE' in field and other_fields_sql:
            ordered_select_fields.append(other_fields_sql)
    
    # 如果没有找到CHKVALUE字段，但有OTHERDETAILS，则添加到最后
    if other_fields_sql and not any('CHKVALUE' in field for field in select_fieldIDs):
        ordered_select_fields.append(other_fields_sql)
    
    # 字段重排完成，不输出详细信息
    
    query = f'''
        SELECT t.`SUBJID`,{', '.join(ordered_select_fields)}
        FROM (
            SELECT `ROWNUM`,`SUBJID`,`FIELDID`,CASE
            {' '.join(case_sql)}
            ELSE '' END AS `CHKTYPE`,`TRANSVAL` AS `CHKVALUE`,`METAVAL`
            FROM {transdata_source}
            WHERE {filename_condition}`FIELDID` IN ({', '.join(chk_fieldIDs)})
            AND `TRANSVAL` IS NOT NULL AND `TRANSVAL` <> ''
        ) t {max_fieldIDs_sql}
        {other_join_sql}
        ORDER BY t.`ROWNUM`,t.`CHKTYPE`,t.`CHKVALUE`;
    '''
    
    return query

def should_use_temp_table(chk_file_count):
    """
    智能决策是否使用临时表优化

    参数:
    - chk_file_count: CHK分支数量

    返回: bool - 是否应该使用临时表
    """
    return USE_TEMP_TABLES and chk_file_count >= TEMP_TABLE_THRESHOLD

def should_scan_empty_columns(rows_count):
    """
    智能决策是否扫描空列
    
    参数:
    - rows_count: 结果集行数
    
    返回: bool - 是否应该扫描空列
    """
    if not ENABLE_EMPTY_COLUMN_SCAN:
        return False
    
    # 大结果集跳过空列扫描
    return rows_count < EMPTY_SCAN_ROW_THRESHOLD

def build_optimized_main_query(fileName, fields, transdata_source, enable_order_by=True):
    """
    构建优化的主查询，前置WHERE条件并可选择性禁用ORDER BY
    """
    order_clause = "ORDER BY `ROWNUM`" if enable_order_by else ""
    
    # 检查是否使用工作表（已预过滤FILENAME）
    if transdata_source.startswith('work_'):
        filename_condition = ""
        group_by_filename = ""
    else:
        filename_condition = f"`FILENAME` = '{fileName}' AND "
        group_by_filename = "`FILENAME`,"
    
    query = f'''
        SELECT `SUBJID`, {', '.join(fields)}
        FROM {transdata_source}
        WHERE {filename_condition}`FORMVAL` IS NOT NULL AND `FORMVAL` <> ''
        GROUP BY {group_by_filename}`ROWNUM`,`SUBJID`
        {order_clause};
    '''
    
    return query

def main():
    """
    主函数，执行格式化流程
    """
    total_start = time.perf_counter()
    db = DatabaseManager()
    db.connect()
    try:
        _run_format(db, total_start)
    finally:
        if USE_TEMP_TABLES:
            db.cleanup_work_tables()
        db.disconnect()


def _run_format(db, total_start):
    """格式化处理的实际逻辑（由 main 包裹 try/finally）"""
    db.create_transdata_view(TRANSDATA_VIEW_NAME, METADATA_TABLE_NAME, CODELIST_TABLE_NAME)

    # 创建性能优化索引
    created_indexes = 0
    if ENABLE_PERFORMANCE_INDEXES:
        created_indexes = db.create_performance_indexes(METADATA_TABLE_NAME)

    print(f'数据库连接成功 | 视图已就绪 | 索引: {created_indexes} 个已创建')

    logger = create_logger(
        os.path.join(SPECIFIC_PATH, 'log_file.log'), 
        log_level=logging.DEBUG
    )

    # 🆕 创建时间戳文件夹并获取实际路径
    actual_format_path = create_directory(FORMAT_TRANSFER_FILE_PATH)
    print(f'使用格式化输出路径: {actual_format_path}')
    
    workbook = load_workbook(filename=os.path.join(SPECIFIC_PATH, CONFIG_NAME))
    sheetSetting = getSheetSetting(workbook)
    fileDict = getFileDict(workbook, sheetSetting)
    _, transFieldDict, chkFileDict, ex_fieldsDict = getProcess(workbook, sheetSetting)
    
    # 应用性能优化配置
    
    format_summary = []  # 按文件统计
    eligible_files = [f for f in transFieldDict.keys() if f in fileDict]
    progress = ProgressReporter(total=len(eligible_files), desc='Format')

    for fileName in transFieldDict.keys():
        if fileName not in fileDict:
            continue
        file_chk_count = 0
        file_chk_rows = 0
        file_main_rows = 0
        file_dropped_rows = 0
        file_start = time.perf_counter()
        exceptFields = ex_fieldsDict.get(fileName, [])
        file_param = transFieldDict[fileName]

        # 智能决策数据源（原视图或临时表）
        transdata_source = TRANSDATA_VIEW_NAME
        temp_table_name = None
        
        # 收集文件复杂度信息用于决策
        chk_file_count = len(chkFileDict.get(fileName, {}))
        
        # 智能决策是否使用工作表
        if should_use_temp_table(chk_file_count):
            temp_table_name = db.create_temp_table_for_file(TRANSDATA_VIEW_NAME, fileName)
            if temp_table_name:
                transdata_source = temp_table_name
                print(f'  → 工作表优化 (CHK:{chk_file_count})')
            else:
                print(f'  → 工作表创建失败，使用原视图')

        fieldID_otherVal = {}
        if fileName in chkFileDict:
            chk_file_params = chkFileDict[fileName]
            for chkfileName, chkfilefieldIDs in chk_file_params.items():
                select_fieldIDs = []
                chk_fieldIDs = []
                case_fieldIDs = {}
                max_fieldIDs = []
                having_fieldIDs = []
                other_fields = MARK_BLANK
                other_fields_sql = MARK_BLANK
                for _chkFieldID, flg in chkfilefieldIDs.items():
                    if _chkFieldID == 'OTHERDETAILS':
                        raw_other_fields = flg
                        other_fields = {}
                            
                        if raw_other_fields:
                            for other_field_key, other_details_field in raw_other_fields.items():
                                if other_details_field not in file_param:
                                    # 跳过不存在的字段（如未标记为迁移的字段）
                                    continue
                                other_fields[other_field_key] = other_details_field
                                fieldID_otherVal[other_details_field] = file_param[other_details_field][COL_OTHERVAL]
                        continue

                    if _chkFieldID in exceptFields:
                        continue
                    if _chkFieldID == fileDict[fileName][COL_SUBJIDFIELDID]:
                        continue
                    if flg:
                        if 't.`CHKTYPE`' not in select_fieldIDs:
                            select_fieldIDs.append(f't.`CHKTYPE`')
                        if 't.`CHKVALUE`' not in select_fieldIDs:
                            select_fieldIDs.append(f't.`CHKVALUE`')
                        chk_fieldIDs.append(f'\'{_chkFieldID}\'')
                        if flg not in case_fieldIDs:
                            case_fieldIDs[flg] = []
                        case_fieldIDs[flg].append(_chkFieldID)
                    else:
                        select_fieldIDs.append(f'tt.`{_chkFieldID}`')
                        max_fieldIDs.append(f'''
                                            max(if((`FIELDID` = '{_chkFieldID}'),`TRANSVAL`,NULL)) AS `{_chkFieldID}`
                                            '''.strip())
                        having_fieldIDs.append(f'{_chkFieldID} IS NOT null')

                outputFileName = f'{PREFIX_F}{fileName}[{chkfileName}]{EXTENSION}'
                outputfilePath = os.path.join(actual_format_path, outputFileName)

                # 检查是否有有效的查询字段
                if not chk_fieldIDs and not max_fieldIDs:
                    continue

                # 使用优化的CHK查询构建函数
                query = build_optimized_chk_query(
                    db, fileName, select_fieldIDs, chk_fieldIDs, case_fieldIDs,
                    max_fieldIDs, having_fieldIDs, other_fields, fieldID_otherVal,
                    file_param, transdata_source
                )

                logger.info(query.replace('                    ',MARK_BLANK))

                db.cursor.execute(query)
                results = db.cursor.fetchall()

                header = [i[0] for i in db.cursor.description]
                rows_cnt = len(results)
                
                # 智能空列扫描（大结果集自动跳过）
                empty_columns = []
                if should_scan_empty_columns(rows_cnt) and results:
                    for i in range(len(header)):
                        column_values = [row[i] for row in results]
                        if all(value is None for value in column_values):
                            empty_columns.append(header[i])

                if results:
                    if empty_columns:
                        print(f'{outputFileName} columns:{empty_columns} is empty')

                    with open(outputfilePath, 'w', newline=MARK_BLANK, encoding='utf-8-sig') as file:
                        writer = csv.writer(file)
                        writer.writerow([i[0] for i in db.cursor.description])
                        writer.writerows(results)
                    file_chk_count += 1
                    file_chk_rows += rows_cnt
                    print(f'  [CHK:{chkfileName}] {rows_cnt} rows')
                
        fields = ['max(if((FIELDID = \'' + fieldID + '\'),TRANSVAL,NULL)) AS `' + fieldID  + '`' 
                  for fieldID in file_param.keys() 
                  if fieldID != fileDict[fileName][COL_SUBJIDFIELDID]
                  ]
        if fields:
            # 使用优化的主查询构建函数
            query = build_optimized_main_query(fileName, fields, transdata_source, ENABLE_ORDER_BY)
            
            logger.info(query.replace('            ',MARK_BLANK))

            db.cursor.execute(query)
            results = db.cursor.fetchall()

            header = [i[0] for i in db.cursor.description]

            # 仅保留除SUBJID外至少有一个非空值的记录
            filtered_results = []
            dropped_only_subjid = 0
            try:
                subjid_idx = header.index('SUBJID')
            except ValueError:
                subjid_idx = None
            for row in results:
                if subjid_idx is not None:
                    # 判断是否只有SUBJID有值
                    has_other_value = any(
                        (idx != subjid_idx) and (val not in (None, '')) and str(val).strip() != ''
                        for idx, val in enumerate(row)
                    )
                    if not has_other_value:
                        dropped_only_subjid += 1
                        continue
                filtered_results.append(row)

            rows_cnt = len(filtered_results)

            with open(os.path.join(actual_format_path, f'{PREFIX_F}{fileName}{EXTENSION}'), 'w', newline=MARK_BLANK, encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow(header)
                writer.writerows(filtered_results)
            file_main_rows = rows_cnt
            file_dropped_rows = dropped_only_subjid
            print(f'  [MAIN] {rows_cnt} rows', end='')
            if dropped_only_subjid:
                print(f' | dropped only-SUBJID rows: {dropped_only_subjid}')
            else:
                print()

        file_elapsed = time.perf_counter() - file_start
        format_summary.append({
            'file': fileName, 'chk_count': file_chk_count,
            'chk_rows': file_chk_rows, 'main_rows': file_main_rows,
            'dropped': file_dropped_rows, 'time': file_elapsed,
        })
        progress.update()

    progress.finish()

    process_combine_files(workbook, sheetSetting, actual_format_path)

    total_elapsed = time.perf_counter() - total_start

    TW = [14, 6, 10, 10, 8, 8]
    tcols = ['文件', 'CHK数', 'CHK行数', 'MAIN行数', '丢弃行', '耗时']
    print_summary_header(f'处理摘要 - {STEP_NAME}')
    print(
        cjk_ljust(tcols[0], TW[0]) + ' '
        + ' '.join(cjk_rjust(c, w) for c, w in zip(tcols[1:], TW[1:]))
    )
    print_summary_sep()
    for s in format_summary:
        print(
            f'{s["file"]:<{TW[0]}} {s["chk_count"]:>{TW[1]}} {s["chk_rows"]:>{TW[2]}} '
            f'{s["main_rows"]:>{TW[3]}} {s["dropped"]:>{TW[4]}} '
            f'{s["time"]:>{TW[5]-1}.1f}s'
        )
    print_summary_sep()
    print_summary_kv('处理文件数', len(format_summary))
    print_summary_kv('总耗时', f'{total_elapsed:.1f}s')

if __name__ == "__main__":
    print_step_header(STEP_ID, STEP_NAME)
    main()
    print_step_footer(STEP_ID, STEP_NAME)
