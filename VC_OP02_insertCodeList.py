"""
VAPORCONE 项目代码列表插入模块

该模块负责将配置文件中的代码列表信息插入到数据库中，包括：
- 读取代码列表配置
- 创建代码列表表
- 插入代码列表数据
- 处理重复数据
"""

from VC_BC03_fetchConfig import *


def main():
    """
    主函数，执行代码列表插入流程
    """
    # 获取代码列表配置
    workbook = load_workbook(filename=os.path.join(SPECIFIC_PATH, CONFIG_NAME))
    sheetSetting = getSheetSetting(workbook)
    _, codeList = getCodeListInfo(workbook, sheetSetting)
   
    db = DatabaseManager()
    db.connect()
    try:
        db.create_codelist_table(CODELIST_TABLE_NAME)
        count = 0

        query_insert = (
            f'INSERT IGNORE INTO {CODELIST_TABLE_NAME} '
            f'(`CODELISTID`, `CODE`, `VALUE_RAW`, `VALUE_EN`, `VALUE_SDTM`) '
            f'VALUES (%s, %s, %s, %s, %s);'
        )
        for row in codeList:
            values_insert = [row[0], row[1], row[2], row[3], row[4]]
            db.cursor.execute(query_insert, values_insert)
            count += 1

            if count % 1000 == 0:
                db.connection.commit()
                print(count, 'records processed.')

        db.connection.commit()
        print(f'{count} records processed (duplicates skipped).')

    except Exception as e:
        print(f'Error: {e}')
        traceback.print_exc()
        if db.connection and db.connection.is_connected():
            db.connection.rollback()
            print('Transaction rolled back.')
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
