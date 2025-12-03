from VC_BC03_fetchConfig import *

def main():
    # コードーリストを取込
    workbook = load_workbook(filename=os.path.join(SPECIFIC_PATH, CONFIG_NAME))
    sheetSetting = getSheetSetting(workbook)

    # 参加者リストを取込
    caseDict = getCaseDict(workbook,sheetSetting)
    fileDict = getFileDict(workbook,sheetSetting)
    _, _, codeDict4other = getCodeListInfo(workbook,sheetSetting)
    # 除外リスト（フィールド）を取込
    _, transFieldDict, _, _ = getProcess(workbook,sheetSetting)

    # 根据mapping定义的SDTM字段判读是否为日期型。
    # SDTM字段以DTC结尾则说明mapping至该字段的原文件字段一定为日期型，否则则一定不是
    dateTypeDict = {}
    mappingDict, _ = getMapping(workbook,sheetSetting)
    for domain_val in mappingDict.values():
        for row_param in domain_val.values():
            for variable in row_param.keys():
                if variable in TIME_VARIABLE:
                    rFieldName = row_param[variable][COL_FIELDNAME]
                    if re.match(PATTERN_CYCLE_PRA, rFieldName):
                        rFieldName = re.sub(PATTERN_CYCLE_PRA, r"\1", rFieldName)                  
                    fieldname_list = rFieldName.split(MARK_DOLLAR)
                    for fieldname in fieldname_list:
                        dateTypeDict[fieldname] = True
                    
    db = DatabaseManager()
    db.connect()
    try:
        db.create_metadata_table(METADATA_TABLE_NAME)
        data = []
        # ローデータファイルリストを取込
        all_files = os.listdir(CLEANINGSTEP_TRANSFER_FILE_PATH)
        files_only = [file for file in all_files if os.path.isfile(os.path.join(CLEANINGSTEP_TRANSFER_FILE_PATH, file))]
        for fileName in fileDict.keys():
            if fileName not in transFieldDict:
                continue
            full_name = next((file_name for file_name in files_only if f'C-{fileName}{EXTENSION}' == file_name), None)
            if not full_name:
                full_name = next((file_name for file_name in files_only if f'C-{fileName}{EXTENSION}' in file_name), None)
            if not full_name:
                print(f'{fileName}{EXTENSION} is undefined')
                sys.exit()

            subjectId_fieldID = fileDict[fileName][COL_SUBJIDFIELDID]
            file_param = transFieldDict[fileName]
            with open(os.path.join(CLEANINGSTEP_TRANSFER_FILE_PATH, full_name), 'r', newline=MARK_BLANK, encoding='utf-8-sig') as read_file:
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
                        # tDATETYPE = field_param[COL_DATATYPE]
                        tDATETYPE = dateTypeDict[tFIELDID] if tFIELDID in dateTypeDict else False 

                        tFORMVAL = make_format_value(tMETAVAL, tDATETYPE, field_param, row, codeDict4other)
                        data.append((fileName, tROWNUM, tUSUBJID, tSUBJID, tFIELDLBL, tFIELDID, tMETAVAL, tFORMVAL, tDATETYPE, tCODELISTID, tCHKFIELDID))

        sql = f"INSERT INTO {METADATA_TABLE_NAME} (No, FILENAME, ROWNUM, USUBJID, SUBJID, FIELDLBL, FIELDID, METAVAL, FORMVAL, DATETYPE, CODELISTID, CHKFIELDID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        count = 0
        for row in data:
            count += 1
            row_with_count = (count,) + row
            db.cursor.execute(sql, row_with_count)
            if count % 1000 == 0:
                db.connection.commit()
                if count % 10000 == 0:
                    print(count, "records inserted.")

        db.connection.commit()
        print(count, "records inserted.")

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
