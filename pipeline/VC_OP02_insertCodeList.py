"""
VAPORCONE 项目代码列表插入模块

该模块负责将配置文件中的代码列表信息插入到数据库中，包括：
- 读取代码列表配置
- 创建代码列表表
- 插入代码列表数据
- 处理重复数据
"""

from VC_BC03_fetchConfig import *

STEP_ID = 'OP02'
STEP_NAME = 'InsertCodeList'


def main():
    """
    主函数，执行代码列表插入流程
    """
    logger = create_logger(
        os.path.join(SPECIFIC_PATH, 'log_file.log'),
        log_level=logging.DEBUG
    )

    # 获取代码列表配置
    workbook = load_workbook(filename=os.path.join(SPECIFIC_PATH, CONFIG_NAME))
    sheetSetting = getSheetSetting(workbook)
    codeDict, codeList = getCodeListInfo(workbook, sheetSetting)

    print(f'配置加载完成: 记录={len(codeList)}, 代码表={len(codeDict)}')
    print_summary_sep()

    # 数据质量预检
    warnings = []
    empty_value_count = 0
    for i, row in enumerate(codeList):
        codelist_name, code, value_raw, value_en, value_sdtm = row
        if not value_en and not value_sdtm:
            empty_value_count += 1
            if empty_value_count <= 5:
                warnings.append(f'  CodeList=[{codelist_name}] Code=[{code}]: VALUE_EN和VALUE_SDTM均为空')
    if empty_value_count > 0:
        log_and_print(logger, 'WARN', f'{empty_value_count} 条记录的VALUE_EN和VALUE_SDTM均为空')
        for w in warnings:
            print(w)
        if empty_value_count > 5:
            print(f'  ... 还有 {empty_value_count - 5} 条类似警告')

    # 按代���表统计编码数
    codelist_stats = {}
    for row in codeList:
        cl_name = row[0]
        codelist_stats[cl_name] = codelist_stats.get(cl_name, 0) + 1

    db = DatabaseManager()
    db.connect()
    try:
        db.create_codelist_table(CODELIST_TABLE_NAME)
        count_inserted = 0
        count_duplicate = 0
        progress = ProgressReporter(total=len(codeList), desc='CodeList')

        query_insert = (
            f'INSERT IGNORE INTO {CODELIST_TABLE_NAME} '
            f'(`CODELISTID`, `CODE`, `VALUE_RAW`, `VALUE_EN`, `VALUE_SDTM`) '
            f'VALUES (%s, %s, %s, %s, %s);'
        )
        for row in codeList:
            values_insert = [row[0], row[1], row[2], row[3], row[4]]
            db.cursor.execute(query_insert, values_insert)
            if db.cursor.rowcount > 0:
                count_inserted += 1
            else:
                count_duplicate += 1

            total = count_inserted + count_duplicate
            if total % 1000 == 0:
                db.connection.commit()
            progress.update()

        db.connection.commit()
        progress.finish()

        # 处理摘要
        TW = [28, 8]
        tcols = ['代码表', '编码数']
        print_summary_header(f'处理摘要 - {STEP_NAME}')
        print(
            cjk_ljust(tcols[0], TW[0]) + ' '
            + ' '.join(cjk_rjust(c, w) for c, w in zip(tcols[1:], TW[1:]))
        )
        print_summary_sep()
        for cl_name, cl_count in sorted(codelist_stats.items()):
            print(f'{cl_name:<{TW[0]}} {cl_count:>{TW[1]}}')
        print_summary_sep()
        print_summary_kv('配置总记录数', len(codeList))
        print_summary_kv('成功插入', count_inserted)
        print_summary_kv('重复跳过', count_duplicate)
        print_summary_kv('代码表数量', len(codeDict))
        logger.info(f'CodeList插入完成: 插入={count_inserted}, 跳过重复={count_duplicate}, 代码表={len(codeDict)}')

    except Exception as e:
        log_and_print(logger, 'ERROR', f'CodeList插入失败: {e}')
        traceback.print_exc()
        if db.connection and db.connection.is_connected():
            db.connection.rollback()
            print('Transaction rolled back.')
    finally:
        if db.cursor:
            db.cursor.close()
        if db.connection and db.connection.is_connected():
            db.disconnect()


if __name__ == '__main__':
    print_step_header(STEP_ID, STEP_NAME)
    main()
    print_step_footer(STEP_ID, STEP_NAME)
