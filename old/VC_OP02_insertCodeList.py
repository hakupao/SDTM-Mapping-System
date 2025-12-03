from VC_BC03_fetchConfig import *

def main():
    # コードーリストを取込
    workbook = load_workbook(filename=os.path.join(SPECIFIC_PATH, CONFIG_NAME))
    sheetSetting = getSheetSetting(workbook)
    _, codeList, _ = getCodeListInfo(workbook,sheetSetting)
   
    db = DatabaseManager()
    db.connect()
    try:
        db.create_codelist_table(CODELIST_TABLE_NAME)
        count = 0

        for row in codeList:
            query_select = f'SELECT * FROM {CODELIST_TABLE_NAME} WHERE  `CODELISTID` = %s AND `CODE` = %s;'
            values = [row[0],row[1]]
            db.cursor.execute(query_select, tuple(values))
            existing_records = db.cursor.fetchall()
            if existing_records:
                print(f'[{row[0]}] [{row[1]}] is existed')
            else:
                query_insert = f'INSERT INTO {CODELIST_TABLE_NAME} (`CODELISTID`, `CODE`, `VALUE_RAW`, `VALUE_EN`, `VALUE_SDTM`) VALUES (%s,%s,%s,%s,%s); '
                values_insert = [row[0],row[1],row[2],row[3],row[4]]
                db.cursor.execute(query_insert, values_insert)
                count += 1
                if count % 1000 == 0:
                    db.connection.commit()
                    print(count, 'records inserted.')

        db.connection.commit()
        print(count, 'records inserted.')

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
