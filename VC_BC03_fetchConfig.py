"""
VAPORCONE 项目配置获取模块

该模块负责从Excel配置文件中读取各种配置信息，包括：
- 工作表设置
- 病例信息
- 文件配置
- 字段映射
- 代码列表
- 域设置等
"""

from VC_BC02_baseUtils import *


def getSheetSetting(workbook):
    """
    从工作簿中读取工作表设置配置
    
    参数:
    - workbook: Excel工作簿对象
    
    返回:
    - dict: 工作表设置字典，包含各工作表的列配置和起始行信息
    """
    # 动态设置max_col，使其为第一行从左至右直到值为空的列数
    max_col = 0
    for cell in workbook[SHEETSETTING_SHEET_NAME][1]:
        if cell.value is None:
            break
        max_col += 1

    sheet_setting = {}
    for row in workbook[SHEETSETTING_SHEET_NAME].iter_rows(
        min_row=2, min_col=1, max_col=max_col, values_only=True
    ):
        if not any(row):
            break
        
        sheet_name = get_cell_value(row, 0)
        starting_row = get_cell_value(row, 1)
        
        if sheet_name not in sheet_setting:
            sheet_setting[sheet_name] = {}
        
        if starting_row:
            sheet_setting[sheet_name][COL_STARTINGROW] = int(get_cell_value(row, 1))
        
        for colnum in range(2, max_col):
            cell_val = get_cell_value(row, colnum)
            if cell_val:
                sheet_setting[sheet_name][cell_val] = colnum - 2
                sheet_setting[sheet_name][COL_MAXCOL] = colnum - 1
    
    return sheet_setting

def getCaseDict(workbook, sheetSetting):
    """
    从工作簿中读取病例字典配置
    
    参数:
    - workbook: Excel工作簿对象
    - sheetSetting: 工作表设置字典
    
    返回:
    - dict: 病例字典，SUBJID -> USUBJID 的映射
    """
    patients_sheetsetting = sheetSetting[CASELIST_SHEET_NAME]
    colnum_subjid = patients_sheetsetting[COL_SUBJID]
    colnum_usubjid = patients_sheetsetting[COL_USUBJID]
    colnum_migration_flag = patients_sheetsetting[COL_MIGRATIONFLAG]

    caseDict = {}
    for row in workbook[CASELIST_SHEET_NAME].iter_rows(
        min_row=patients_sheetsetting[COL_STARTINGROW], 
        min_col=1, 
        max_col=patients_sheetsetting[COL_MAXCOL], 
        values_only=True
    ):
        if not any(row):
            break
        
        subjid = get_cell_value(row, colnum_subjid)
        usubjid = get_cell_value(row, colnum_usubjid)
        migration_flag = get_cell_value(row, colnum_migration_flag)

        # 跳过标记为不迁移的病例
        if migration_flag in MARK_CROSS:
            continue
        if migration_flag not in MARK_CIRCLE:
            print(f'Study:[{STUDY_ID}] case:[{subjid}] is mapping wrong')
            sys.exit()

        caseDict[subjid] = usubjid
    
    return caseDict

# 仕様書からシートFiles読込
def getFileDict(workbook, sheetSetting):
    files_sheetsetting = sheetSetting[FILELIST_SHEET_NAME]
    colnum_file_name = files_sheetsetting[COL_FILENAME]
    colnum_migration_flag = files_sheetsetting[COL_MIGRATIONFLAG]
    colnum_title_row = files_sheetsetting[COL_TITLEROW]
    colnum_data_row = files_sheetsetting[COL_DATARROW]
    colnum_subjid_fieldid = files_sheetsetting[COL_SUBJIDFIELDID]
    colnum_processing_logic = files_sheetsetting[COL_PROCESSINGLOGIC]

    fileDict = {}
    for row in workbook[FILELIST_SHEET_NAME].iter_rows(min_row=files_sheetsetting[COL_STARTINGROW], min_col=1, max_col=files_sheetsetting[COL_MAXCOL], values_only=True):
        if not any(row):
            break
        migration_flag = get_cell_value(row, colnum_migration_flag)
        file_name = get_cell_value(row, colnum_file_name)
        title_row = get_cell_value(row, colnum_title_row)
        data_row = get_cell_value(row, colnum_data_row)
        subjid_fieldid = get_cell_value(row, colnum_subjid_fieldid)
        processing_logic = get_cell_value(row, colnum_processing_logic)
        
        if migration_flag in MARK_CROSS:
            continue
        if migration_flag not in MARK_CIRCLE:
            print(f'Study:[{STUDY_ID}] File:[{file_name}] is mapping wrong')
            sys.exit()
        if not file_name:
            print(f'Study:[{STUDY_ID}] File:[{file_name}] is undefined')
            sys.exit()
        if not subjid_fieldid:
            print(f'Study:[{STUDY_ID}] File:[{file_name}] subjid_fieldid is undefined')
            sys.exit()
        if not title_row.isdigit() or not data_row.isdigit():
            print(f'Study:[{STUDY_ID}] File:[{file_name}] row is wrong')
            sys.exit()

        if file_name.endswith(EXTENSION):
            file_name = file_name.removesuffix(EXTENSION)

        if file_name not in fileDict:
            fileDict[file_name] = {}
        fileDict[file_name][COL_SUBJIDFIELDID] = subjid_fieldid
        fileDict[file_name][COL_PROCESSINGLOGIC] = processing_logic
        fileDict[file_name][COL_TITLEROW] = int(title_row)
        fileDict[file_name][COL_DATARROW] = int(data_row)
    return fileDict

# 仕様書からシートProcess読込
def getProcess(workbook, sheetSetting):
    colnum_file_name = sheetSetting[PROCESS_SHEET_NAME][COL_FILENAME]
    colnum_field_name = sheetSetting[PROCESS_SHEET_NAME][COL_FIELDNAME]
    colnum_label = sheetSetting[PROCESS_SHEET_NAME][COL_LABEL]
    # colnum_data_type = sheetSetting[PROCESS_SHEET_NAME][COL_DATATYPE]
    colnum_codelist_name = sheetSetting[PROCESS_SHEET_NAME][COL_CODELISTNAME]
    colnum_migration_flag = sheetSetting[PROCESS_SHEET_NAME][COL_MIGRATIONFLAG]
    colnum_chk_type = sheetSetting[PROCESS_SHEET_NAME][COL_CHKTYPE]
    colnum_other_details_process = sheetSetting[PROCESS_SHEET_NAME][COL_OTHERDETAILSPROCESS]
    
    ex_fieldsDict = {}
    fieldDict = {}
    transFieldDict = {}
    chkFileDict = {}

    process_sheet = workbook[PROCESS_SHEET_NAME]
    chk_file_names = []
    colnum_data_extraction = 0
    for cell in process_sheet[1]:
        if cell.value and cell.value.strip() == COL_DATAEXTRACTION:
            colnum_data_extraction = cell.column
            break

    for cell in process_sheet[2]:
        if cell.column >= colnum_data_extraction and cell.value:
            chk_file_names.append(cell.value.strip())

    for row in process_sheet.iter_rows(min_row=sheetSetting[PROCESS_SHEET_NAME][COL_STARTINGROW], min_col=1, max_col=sheetSetting[PROCESS_SHEET_NAME][COL_MAXCOL], values_only=True):
        if not any(row):
            break
        file_name = get_cell_value(row, colnum_file_name)
        field_id = get_cell_value(row, colnum_field_name)
        label = get_cell_value(row, colnum_label)
        codelist_name = get_cell_value(row, colnum_codelist_name)
        migration_flag = get_cell_value(row, colnum_migration_flag)
        chk_type = get_cell_value(row, colnum_chk_type)
        other_details_process = get_cell_value(row, colnum_other_details_process)
        other_val = MARK_BLANK
        other_details_field = MARK_BLANK
        if other_details_process:
            try:
                other_val, other_details_field = other_details_process.split(MARK_COLON, 1)
            except ValueError:
                print(f'Study:[{STUDY_ID}] File:[{file_name}] Field:[{field_id}] OtherDetailsProcess is wrong')
                sys.exit()

        if file_name.endswith(EXTENSION):
            file_name = file_name.removesuffix(EXTENSION)

        dfile_name = PREFIX_DC + file_name

        if file_name not in fieldDict:
            fieldDict[file_name] = []
        if dfile_name not in fieldDict:
            fieldDict[dfile_name] = []
        if migration_flag in MARK_CIRCLE:
            fieldDict[file_name].append(field_id)
        elif migration_flag in MARK_CROSS:
            fieldDict[dfile_name].append(field_id)
            continue
        else:
            fieldDict[dfile_name].append(field_id)
            continue
            # print(f'Study:[{STUDY_ID}] File:[{file_name}] Field:[{field_id}] CleaningStep is wrong') 

        if file_name not in transFieldDict:
            transFieldDict[file_name] = {}
        if field_id not in transFieldDict[file_name]:
            transFieldDict[file_name][field_id] = {}
        transFieldDict[file_name][field_id][COL_LABEL] = label
        transFieldDict[file_name][field_id][COL_CODELISTNAME] = codelist_name
        transFieldDict[file_name][field_id][COL_CHKTYPE] = chk_type
        transFieldDict[file_name][field_id][COL_OTHERVAL] = other_val
        transFieldDict[file_name][field_id][COL_OTHERDETAILSFIELD] = other_details_field

        if file_name not in ex_fieldsDict:
            ex_fieldsDict[file_name] = []
        # if other_details_field:
        #     ex_fieldsDict[file_name].append(other_details_field)

        for i, chkfileName in enumerate(chk_file_names):
            fileFieldflg = get_cell_value(row, colnum_data_extraction + i - 1)
            if fileFieldflg:
                if file_name not in chkFileDict:
                    chkFileDict[file_name] = {}
                if chkfileName not in chkFileDict[file_name]:
                    chkFileDict[file_name][chkfileName] = {}

                if fileFieldflg in MARK_CIRCLE:
                    if field_id not in chkFileDict[file_name][chkfileName]:
                        chkFileDict[file_name][chkfileName][field_id] = chk_type
                elif fileFieldflg:
                    if COL_OTHERDETAILS not in chkFileDict[file_name][chkfileName]:
                        chkFileDict[file_name][chkfileName][COL_OTHERDETAILS] = {}
                    chkFileDict[file_name][chkfileName][COL_OTHERDETAILS][field_id] = fileFieldflg
                    ex_fieldsDict[file_name].append(field_id)

    return fieldDict,transFieldDict,chkFileDict,ex_fieldsDict

# 仕様書からシートCodeList読込
def getCodeListInfo(workbook, sheetSetting):
    codeList_sheetsetting = sheetSetting[CODELIST_SHEET_NAME]
    colnum_codelist_name = codeList_sheetsetting[COL_CODELISTNAME]
    colnum_code = codeList_sheetsetting[COL_CODE]
    colnum_value_raw = codeList_sheetsetting[COL_VALUERAW]
    colnum_value_en = codeList_sheetsetting[COL_VALUEEN]
    colnum_value_sdtm = codeList_sheetsetting[COL_VALUESDTM]

    codeDict = {}
    codeDict4other = {}
    codeList = []

    for row in workbook[CODELIST_SHEET_NAME].iter_rows(min_row=codeList_sheetsetting[COL_STARTINGROW], min_col=1, max_col=codeList_sheetsetting[COL_MAXCOL], values_only=True):
        if not any(row):
            break
        codelist_name = get_cell_value(row, colnum_codelist_name)
        code = get_cell_value(row, colnum_code)
        value_raw = get_cell_value(row, colnum_value_raw)
        value_en = get_cell_value(row, colnum_value_en)
        value_sdtm = get_cell_value(row, colnum_value_sdtm)

        if codelist_name.endswith(SUFFIX_4OTHER):
            if codelist_name not in codeDict4other:
                codeDict4other[codelist_name] = {}
            codeDict4other[codelist_name][code] = value_en
            
            if codelist_name[:-6] not in codeDict:
                codeDict[codelist_name[:-6]] = {}
            codeDict[codelist_name[:-6]][value_en] = value_sdtm
        else:
            if codelist_name not in codeDict:
                codeDict[codelist_name] = {}
            codeDict[codelist_name][value_en] = value_sdtm
        codeList.append([codelist_name,code,value_raw,value_en,value_sdtm])
    return codeDict, codeList, codeDict4other

# 仕様書からシートRefactoring読込
def getRefactoringInfo(workbook, sheetSetting):
    refactoring_sheetsetting = sheetSetting[REFACTORING_SHEET_NAME]
    colnum_file_name = refactoring_sheetsetting[COL_FILENAME]
    colnum_function = refactoring_sheetsetting[COL_FUNCTION]

    refactoringDict = {}
    for row in workbook[REFACTORING_SHEET_NAME].iter_rows(min_row=refactoring_sheetsetting[COL_STARTINGROW], min_col=1, max_col=refactoring_sheetsetting[COL_MAXCOL], values_only=True):
        if not any(row):
            break
        file_name = get_cell_value(row, colnum_file_name)
        function = get_cell_value(row, colnum_function)
        refactoringDict[file_name] = function
    return refactoringDict

# 仕様書からシートMapping読込
def getMapping(workbook, sheetSetting):
    mapping_sheetsetting = sheetSetting[MAPPING_SHEET_NAME]
    colnum_definition = mapping_sheetsetting[COL_DEFINITION]
    colnum_domain = mapping_sheetsetting[COL_DOMAIN]
    colnum_variable = mapping_sheetsetting[COL_VARIABLE]
    colnum_nd_keys = mapping_sheetsetting[COL_NDKEY]
    colnum_file_name = mapping_sheetsetting[COL_FILENAME]
    colnum_field_name = mapping_sheetsetting[COL_FIELDNAME]
    colnum_oper_type = mapping_sheetsetting[COL_OPERTYPE]
    colnum_parameter = mapping_sheetsetting[COL_PARAMETER]
    starting_row_num = mapping_sheetsetting[COL_STARTINGROW]

    domain_key = ''
    mappingDict = {}
    definition_merge_rule = {}
    cycle_time = 1
    for row in workbook[MAPPING_SHEET_NAME].iter_rows(min_row=starting_row_num, min_col=1, max_col=mapping_sheetsetting[COL_MAXCOL], values_only=True):
        starting_row_num += 1
        if not any(row):
            break

        definition = get_cell_value(row, colnum_definition)
        domain = get_cell_value(row, colnum_domain)
        variable = get_cell_value(row, colnum_variable)
        nd_keys = get_cell_value(row, colnum_nd_keys)
        file_name = get_cell_value(row, colnum_file_name)
        if MARK_LINEBREAK in file_name:
            cycle_string, file_name = file_name.split(MARK_LINEBREAK, 1)
            match = re.search(PATTERN_CYCLE_NUM, cycle_string)
            cycle_time = int(match.group(1)) if match else 1

        field_name = get_cell_value(row, colnum_field_name)
        if MARK_LINEBREAK in field_name:
            field_name = field_name.replace(MARK_LINEBREAK, MARK_DOLLAR)
        elif MARK_COMMA in field_name:
            field_name = field_name.replace(MARK_COMMA, MARK_DOLLAR)

        oper_type = get_cell_value(row, colnum_oper_type)
        parameter = get_cell_value(row, colnum_parameter)
        if MARK_LINEBREAK in parameter:
            parameter = parameter.replace(MARK_LINEBREAK, MARK_DOLLAR)
        elif MARK_COMMA in parameter and not parameter.endswith(MARK_COMMA) :
            parameter = parameter.replace(MARK_COMMA, MARK_DOLLAR)

        if not variable:
            print(f'Study:[{STUDY_ID}] Domain:[{domain}] field is undefined')
            sys.exit()

        if nd_keys and nd_keys not in MARK_CIRCLE:
            print(f'deletion_key:{nd_keys} is wrong')
            sys.exit()

        if definition:
            definition_row_num = starting_row_num
            if definition_row_num not in definition_merge_rule:
                definition_merge_rule[definition_row_num] = {}
            definition_merge_rule[definition_row_num][COL_MERGERULE] = file_name
            definition_merge_rule[definition_row_num][COL_DEFINITION] = cycle_time

        if domain_key != domain and PREFIX_SUPP + domain_key != domain:
            domain_key = domain

        # 将追加的SUPP字段加入标准字段集中 
        supp_time_flg = False
        outputFields = STANDARD_FIELDS[domain_key]
        if variable not in outputFields:
            if variable.endswith('DTC'):
                supp_time_flg = True
            STANDARD_FIELDS[domain_key].append(variable)
            print(f'Study:[{STUDY_ID}] Domain:[{domain_key}] Suppfield:[{variable}] is appended')

        if domain_key not in mappingDict:
            mappingDict[domain_key] = {}
        
        if not oper_type:
            continue

        if definition_row_num not in mappingDict[domain_key]:
            mappingDict[domain_key][definition_row_num] = {}
        if variable not in mappingDict[domain_key][definition_row_num]:
            mappingDict[domain_key][definition_row_num][variable] = {}

        mappingDict[domain_key][definition_row_num][variable][COL_NDKEY] = True if nd_keys in MARK_CIRCLE else False
        mappingDict[domain_key][definition_row_num][variable][COL_FIELDNAME] = field_name
        mappingDict[domain_key][definition_row_num][variable][COL_OPERTYPE] = oper_type
        mappingDict[domain_key][definition_row_num][variable][COL_PARAMETER] = parameter
        mappingDict[domain_key][definition_row_num][variable]['SUPPTIMEFLG'] = supp_time_flg
    
    return mappingDict, definition_merge_rule

# 仕様書からシートDomainsSetting読込
def getDomainsSetting(workbook, sheetSetting):
    domainsSetting_sheetsetting = sheetSetting[DOMAINSSETTING_SHEET_NAME]
    colnum_domain = domainsSetting_sheetsetting[COL_DOMAIN]
    colnum_sortkey = domainsSetting_sheetsetting[COL_SORTKEYS]
    
    domainsSettingDict = {}
    for row in workbook[DOMAINSSETTING_SHEET_NAME].iter_rows(min_row=domainsSetting_sheetsetting[COL_STARTINGROW], min_col=1, max_col=domainsSetting_sheetsetting[COL_MAXCOL], values_only=True):
        if not any(row):
            break
        domain_name = get_cell_value(row, colnum_domain)
        sortkeys = [s.strip() for s in get_cell_value(row, colnum_sortkey).split(',')]
        if COL_USUBJID not in sortkeys:
            sortkeys.appendleft(COL_USUBJID)
        domainsSettingDict[domain_name] = sortkeys
    return domainsSettingDict

# Refactoring時に必要なファイルを読込
def getFormatDataset(*fileNames, **fileNameList):
    allFileNameList = fileNameList.get('fileNameList')
    if not allFileNameList:
        allFileNameList = []
    allFileNameList.extend(fileNames)

    # 🆕 动态获取最新的格式化数据文件夹路径
    actual_format_path = find_latest_timestamped_path(FORMAT_PATH, 'format_dataset')
    
    format_dataset = {}
    all_files = os.listdir(actual_format_path)
    files_only = [file for file in all_files if os.path.isfile(os.path.join(actual_format_path, file))]          
    for fileName in files_only:
        shortFileName = fileName.removeprefix(PREFIX_F).removesuffix(EXTENSION)
        if shortFileName in allFileNameList:
            format_dataset[shortFileName] = pandas.read_csv(os.path.join(actual_format_path, fileName), dtype=str, na_filter=False)
    return format_dataset

def getSites(workbook, sheetSetting):
    site_sheetsetting = sheetSetting[SITEMASTER_SHEET_NAME]
    colnum_sitename = site_sheetsetting[COL_SITENAME]
    colnum_sitecode = site_sheetsetting[COL_SITECODE]
    
    siteDict = {}
    for row in workbook[SITEMASTER_SHEET_NAME].iter_rows(min_row=site_sheetsetting[COL_STARTINGROW], min_col=1, max_col=site_sheetsetting[COL_MAXCOL], values_only=True):
        if not any(row):
            break
        site_name = get_cell_value(row, colnum_sitename)
        site_code = get_cell_value(row, colnum_sitecode)
        siteDict[site_name] = site_code
    return siteDict

def getCombineInfo(workbook, sheetSetting):
    colnum_file_name = sheetSetting[COMBINE_SHEET_NAME][COL_FILENAME]
    colnum_function = sheetSetting[COMBINE_SHEET_NAME][COL_FUNCTION]
    combine_sheet = workbook[COMBINE_SHEET_NAME]
    combineDict = {}
    for row in combine_sheet.iter_rows(min_row=sheetSetting[COMBINE_SHEET_NAME][COL_STARTINGROW], min_col=1, max_col=sheetSetting[COMBINE_SHEET_NAME][COL_MAXCOL], values_only=True):
        if not any(row):
            break
        file_name = get_cell_value(row, colnum_file_name)
        function = get_cell_value(row, colnum_function)
        combineDict[file_name] = function
    return combineDict
