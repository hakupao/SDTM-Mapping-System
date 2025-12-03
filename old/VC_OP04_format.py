from VC_BC03_fetchConfig import *
from VC_BC04_operateType import *

def main():

    db = DatabaseManager()
    db.connect()
    db.create_transdata_view(TRANSDATA_VIEW_NAME, METADATA_TABLE_NAME, CODELIST_TABLE_NAME)

    logger = create_logger(os.path.join(SPECIFIC_PATH, 'log_file.log'), log_level=logging.DEBUG)

    create_directory(FORMAT_TRANSFER_FILE_PATH)
    
    workbook = load_workbook(filename=os.path.join(SPECIFIC_PATH, CONFIG_NAME))
    sheetSetting = getSheetSetting(workbook)
    fileDict = getFileDict(workbook,sheetSetting)
    _,transFieldDict,chkFileDict,ex_fieldsDict = getProcess(workbook,sheetSetting)
    
    for fileName in transFieldDict.keys():
        if fileName not in fileDict:
            continue
        print(f'{fileName} is outputting')
        exceptFields = ex_fieldsDict[fileName]
        rownum_fieldID = MARK_BLANK
        file_param = transFieldDict[fileName]

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
                        other_fields = flg
                            
                        if other_fields:
                            for _, other_details_field in other_fields.items():
                                fieldID_otherVal[other_details_field] = file_param[other_details_field][COL_OTHERVAL]

                            other_fields_sql = 'COALESCE(' + ','.join([f't{other_field}.`{other_field}`' for other_field in other_fields.keys()]) + ') `OTHERDETAILS`'
                        if other_fields_sql and other_fields_sql not in select_fieldIDs:
                            select_fieldIDs.append(other_fields_sql)
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
                        # if other_fields_sql and other_fields_sql not in select_fieldIDs:
                        #     select_fieldIDs.append(other_fields_sql)
                        chk_fieldIDs.append(f'\'{_chkFieldID}\'')
                        if flg not in case_fieldIDs:
                            case_fieldIDs[flg] = []
                        case_fieldIDs[flg].append(_chkFieldID)
                    else:
                        select_fieldIDs.append(f'tt.`{_chkFieldID}`')
                        max_fieldIDs.append(f'''
                                            max(if((`FILENAME` = '{fileName}' AND `FIELDID` = '{_chkFieldID}'),`TRANSVAL`,NULL)) AS `{_chkFieldID}`
                                            ''')
                        having_fieldIDs.append(f'{_chkFieldID} IS NOT null')

                case_sql = []
                for key, vals in case_fieldIDs.items():
                    chkfields = ', '.join([f'\'{val}\''  for val in vals])
                    case_sql.append(f'WHEN `FIELDID` IN ({chkfields}) THEN \'{key}\'')
                other_join_sql = ''
                if other_fields:
                    other_join_sql = ' '.join([f'''LEFT JOIN (
                            SELECT `ROWNUM`,max(if((`FILENAME` = '{fileName}' AND `FIELDID` = '{other_field}'),`TRANSVAL`,NULL)) AS `{other_field}`
                            FROM {TRANSDATA_VIEW_NAME} GROUP BY `FILENAME`,`ROWNUM`,`SUBJID` HAVING {other_field} IS NOT null
                        ) t{other_field} ON t.`ROWNUM` = t{other_field}.`ROWNUM` AND t.`FIELDID` = '{other_details_field}' AND t.`METAVAL` = '{fieldID_otherVal[other_details_field]}'
                        '''
                        for other_field, other_details_field in other_fields.items()
                    ])
                
                tFIELDID = MARK_BLANK
                rFIELDID = MARK_BLANK
                outputFileName = f'{PREFIX_F}{fileName}[{chkfileName}]{EXTENSION}'
                outputfilePath = os.path.join(FORMAT_TRANSFER_FILE_PATH, outputFileName)

                max_fieldIDs_sql = MARK_BLANK
                if max_fieldIDs:
                    max_fieldIDs_sql = f'''LEFT JOIN (
                                SELECT `ROWNUM`
                                ,{', '.join(max_fieldIDs)}
                                FROM {TRANSDATA_VIEW_NAME}
                                GROUP BY `FILENAME`,`ROWNUM`,`SUBJID`
                                HAVING {' OR '.join(having_fieldIDs)}
                            ) tt ON t.`ROWNUM` = tt.`ROWNUM` '''
                
                query = f'''
                    SELECT {tFIELDID}t.`SUBJID`,{', '.join(select_fieldIDs)}
                    FROM (
                        SELECT {rFIELDID}`ROWNUM`,`SUBJID`,`FIELDID`,CASE
                        {' '.join(case_sql)}
                        ELSE '' END AS `CHKTYPE`,`TRANSVAL` AS `CHKVALUE`,`METAVAL`
                        FROM {TRANSDATA_VIEW_NAME}
                        WHERE `FILENAME` = '{fileName}'
                        AND `FIELDID` IN ({', '.join(chk_fieldIDs)})
                    ) t {max_fieldIDs_sql}
                    {other_join_sql}
                    WHERE t.`CHKVALUE` IS NOT NULL AND t.`CHKVALUE` <> ''
                    ORDER BY t.`ROWNUM`,t.`CHKTYPE`,t.`CHKVALUE`;
                '''

                logger.info(query.replace('                    ',MARK_BLANK))
                db.cursor.execute(query)
                results = db.cursor.fetchall()
                header = [i[0] for i in db.cursor.description]
                empty_columns = []
                for i in range(len(header)):
                    column_values = [row[i] for row in results]
                    if all(value == None for value in column_values):
                        empty_columns.append(header[i])

                if results:
                    if empty_columns:
                        print(f'{outputFileName} columns:{empty_columns} is empty')



                    with open(outputfilePath, 'w', newline=MARK_BLANK, encoding='utf-8-sig') as file:
                        writer = csv.writer(file)
                        writer.writerow([i[0] for i in db.cursor.description])
                        writer.writerows(results)
                
        fields = ['max(if((FIELDID = \'' + fieldID + '\'),TRANSVAL,NULL)) AS `' + fieldID  + '`' 
                  for fieldID in file_param.keys() 
                  if fieldID != fileDict[fileName][COL_SUBJIDFIELDID] 
                  and not file_param[fieldID][COL_CHKTYPE]
                  and fieldID not in exceptFields
                  ]
        if fields:
            query = f'''
                SELECT {rownum_fieldID} `SUBJID`,
                {', '.join(fields)}
                FROM {TRANSDATA_VIEW_NAME}
                WHERE `FILENAME` = '{fileName}'
                GROUP BY `FILENAME`,`ROWNUM`,`SUBJID`
                ORDER BY `ROWNUM`;
            '''
            logger.info(query.replace('            ',MARK_BLANK))
            db.cursor.execute(query)
            results = db.cursor.fetchall()

            with open(os.path.join(FORMAT_TRANSFER_FILE_PATH, f'{PREFIX_F}{fileName}{EXTENSION}'), 'w', newline=MARK_BLANK, encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow([i[0] for i in db.cursor.description])
                writer.writerows(results)

    for file_name, function_name in getCombineInfo(workbook, sheetSetting).items():
        be_converted_list = eval(function_name)
        be_converted_list.fillna('').to_csv(os.path.join(FORMAT_TRANSFER_FILE_PATH, f'{PREFIX_F}{file_name}{EXTENSION}'), index=False, encoding='utf-8-sig')
        print(f'{file_name} is outputting')

if __name__ == "__main__":
    print(f'Study:{STUDY_ID} Processing has begun.' )
    main()
    print(f'Study:{STUDY_ID} Processing is over.' )
