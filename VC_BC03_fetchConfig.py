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


class MappingConfigurationError(Exception):
    """
    Raised when the mapping specification workbook contains invalid or inconsistent data.

    Attributes
    ----------
    sheet : str
        Excel sheet where the problem was found.
    row : int | None
        Excel row index (1-based) that triggered the error, if known.
    original_exception : Exception | None
        Underlying exception for additional context.
    """

    def __init__(self, message, sheet=None, row=None, original_exception=None):
        super().__init__(message)
        self.sheet = sheet
        self.row = row
        self.original_exception = original_exception


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
    current_row_num = patients_sheetsetting[COL_STARTINGROW]
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
            current_row_num += 1
            continue
        if migration_flag not in MARK_CIRCLE:
            raise MappingConfigurationError(
                f"第{current_row_num}行的MigrationFlag值无效: '{migration_flag}'，SUBJID='{subjid}'。"
                f"期望值为 {MARK_CIRCLE} 或 {MARK_CROSS}。",
                sheet=CASELIST_SHEET_NAME,
                row=current_row_num
            )

        caseDict[subjid] = usubjid
        current_row_num += 1

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
    current_row_num = files_sheetsetting[COL_STARTINGROW]
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
            current_row_num += 1
            continue
        if migration_flag not in MARK_CIRCLE:
            raise MappingConfigurationError(
                f"第{current_row_num}行的MigrationFlag值无效: '{migration_flag}'，文件名='{file_name}'。"
                f"期望值为 {MARK_CIRCLE} 或 {MARK_CROSS}。",
                sheet=FILELIST_SHEET_NAME,
                row=current_row_num
            )
        if not file_name:
            raise MappingConfigurationError(
                f"第{current_row_num}行的FileName列为空。",
                sheet=FILELIST_SHEET_NAME,
                row=current_row_num
            )
        if not subjid_fieldid:
            raise MappingConfigurationError(
                f"第{current_row_num}行的SubjIdFieldId列为空，文件名='{file_name}'。",
                sheet=FILELIST_SHEET_NAME,
                row=current_row_num
            )
        if not title_row.isdigit() or not data_row.isdigit():
            raise MappingConfigurationError(
                f"第{current_row_num}行的TitleRow('{title_row}')或DataRow('{data_row}')不是有效数字，文件名='{file_name}'。",
                sheet=FILELIST_SHEET_NAME,
                row=current_row_num
            )

        if file_name.endswith(EXTENSION):
            file_name = file_name.removesuffix(EXTENSION)

        if file_name not in fileDict:
            fileDict[file_name] = {}
        fileDict[file_name][COL_SUBJIDFIELDID] = subjid_fieldid
        fileDict[file_name][COL_PROCESSINGLOGIC] = processing_logic
        fileDict[file_name][COL_TITLEROW] = int(title_row)
        fileDict[file_name][COL_DATARROW] = int(data_row)
        current_row_num += 1
    return fileDict

# 仕様書からシートProcess読込
def getProcess(workbook, sheetSetting):
    colnum_file_name = sheetSetting[PROCESS_SHEET_NAME][COL_FILENAME]
    colnum_field_name = sheetSetting[PROCESS_SHEET_NAME][COL_FIELDNAME]
    colnum_label = sheetSetting[PROCESS_SHEET_NAME][COL_LABEL]
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
    
    # 找到 Process 工作表第1行中 DATAEXTRACTION 的位置
    for cell in process_sheet[1]:
        if cell.value and cell.value.strip() == COL_DATAEXTRACTION:
            colnum_data_extraction = cell.column
            break

    # 从 SheetSetting 中识别 DataExtraction 文件名
    # 只有在 SheetSetting 中配置的列名才会被处理，空白列（如備考）会被忽略
    if colnum_data_extraction > 0:
        # 获取 Process 工作表第2行的列名 -> 列位置映射
        process_row2_columns = {cell.value.strip(): cell.column 
                                for cell in process_sheet[2] if cell.value}
        
        # 从 SheetSetting 配置中找出落在 DataExtraction 区域的列名
        for key in sheetSetting[PROCESS_SHEET_NAME]:
            if key in [COL_STARTINGROW, COL_MAXCOL]:
                continue
            if key in process_row2_columns and process_row2_columns[key] >= colnum_data_extraction:
                chk_file_names.append(key)

    starting_row = sheetSetting[PROCESS_SHEET_NAME][COL_STARTINGROW]
    max_col = sheetSetting[PROCESS_SHEET_NAME][COL_MAXCOL]
    current_row_num = starting_row

    for row in process_sheet.iter_rows(min_row=starting_row, min_col=1, max_col=max_col, values_only=True):
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
                raise MappingConfigurationError(
                    f"第{current_row_num}行的OtherDetailsProcess格式错误: '{other_details_process}'，"
                    f"文件名='{file_name}'，字段='{field_id}'。期望格式为 '值:字段名'。",
                    sheet=PROCESS_SHEET_NAME,
                    row=current_row_num
                )

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
            current_row_num += 1
            continue
        else:
            fieldDict[dfile_name].append(field_id)
            current_row_num += 1
            continue

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

        for i, chkfileName in enumerate(chk_file_names):
            target_col_idx = colnum_data_extraction + i - 1
            fileFieldflg = get_cell_value(row, target_col_idx)
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

        current_row_num += 1

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
    codeList = []
    current_row_num = codeList_sheetsetting[COL_STARTINGROW]

    for row in workbook[CODELIST_SHEET_NAME].iter_rows(min_row=codeList_sheetsetting[COL_STARTINGROW], min_col=1, max_col=codeList_sheetsetting[COL_MAXCOL], values_only=True):
        if not any(row):
            break
        codelist_name = get_cell_value(row, colnum_codelist_name)
        code = get_cell_value(row, colnum_code)
        value_raw = get_cell_value(row, colnum_value_raw)
        value_en = get_cell_value(row, colnum_value_en)
        value_sdtm = get_cell_value(row, colnum_value_sdtm)

        if not codelist_name:
            raise MappingConfigurationError(
                f"第{current_row_num}行的CodelistName列为空。",
                sheet=CODELIST_SHEET_NAME,
                row=current_row_num
            )
        if not code:
            raise MappingConfigurationError(
                f"第{current_row_num}行的Code列为空，CodelistName='{codelist_name}'。",
                sheet=CODELIST_SHEET_NAME,
                row=current_row_num
            )

        # 注意：已移除4OTHER功能，不再处理带有4OTHER后缀的代码表
        if codelist_name not in codeDict:
            codeDict[codelist_name] = {}
        codeDict[codelist_name][value_en] = value_sdtm
        codeList.append([codelist_name,code,value_raw,value_en,value_sdtm])
        current_row_num += 1
    return codeDict, codeList

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
    active_definition_row = None
    current_row_num = starting_row_num
    current_definition_file = None

    for row in workbook[MAPPING_SHEET_NAME].iter_rows(
        min_row=starting_row_num,
        min_col=1,
        max_col=mapping_sheetsetting[COL_MAXCOL],
        values_only=True
    ):
        if not any(row):
            break

        try:
            definition = get_cell_value(row, colnum_definition)
            domain = get_cell_value(row, colnum_domain)
            variable = get_cell_value(row, colnum_variable)
            nd_keys = get_cell_value(row, colnum_nd_keys)
            file_name = get_cell_value(row, colnum_file_name)

            if not domain:
                raise MappingConfigurationError(
                    f"第{current_row_num}行的Domain列为空。",
                    sheet=MAPPING_SHEET_NAME,
                    row=current_row_num
                )

            # 🔑 每行重置cycle_time为默认值1，避免使用前一个Definition的值
            cycle_time = 1

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
            elif MARK_COMMA in parameter and not parameter.endswith(MARK_COMMA):
                parameter = parameter.replace(MARK_COMMA, MARK_DOLLAR)

            if not variable:
                raise MappingConfigurationError(
                    f"第{current_row_num}行的Variable列为空，Domain '{domain}' 的字段配置不完整。",
                    sheet=MAPPING_SHEET_NAME,
                    row=current_row_num
                )

            if nd_keys and nd_keys not in MARK_CIRCLE:
                raise MappingConfigurationError(
                    f"第{current_row_num}行的删除键设置无效: {nd_keys}",
                    sheet=MAPPING_SHEET_NAME,
                    row=current_row_num
                )

            if definition:
                if not file_name:
                    raise MappingConfigurationError(
                        f"第{current_row_num}行的FileName列为空。",
                        sheet=MAPPING_SHEET_NAME,
                        row=current_row_num
                    )
                active_definition_row = current_row_num
                current_definition_file = file_name
                if active_definition_row not in definition_merge_rule:
                    definition_merge_rule[active_definition_row] = {}
                definition_merge_rule[active_definition_row][COL_MERGERULE] = file_name
                definition_merge_rule[active_definition_row][COL_DEFINITION] = cycle_time
            elif active_definition_row is None:
                raise MappingConfigurationError(
                    f"第{current_row_num}行缺少Definition值，无法确定映射组。",
                    sheet=MAPPING_SHEET_NAME,
                    row=current_row_num
                )
            else:
                # 沿用当前Definition的文件名，允许Excel中省略重复值
                if file_name:
                    current_definition_file = file_name
                else:
                    if current_definition_file is None:
                        raise MappingConfigurationError(
                            f"第{current_row_num}行缺少FileName，且未找到可沿用的Definition文件名。",
                            sheet=MAPPING_SHEET_NAME,
                            row=current_row_num
                        )
                    file_name = current_definition_file

            if domain_key != domain and PREFIX_SUPP + domain_key != domain:
                domain_key = domain

            if domain_key not in STANDARD_FIELDS:
                raise MappingConfigurationError(
                    f"第{current_row_num}行的Domain '{domain}' 未在STANDARD_FIELDS中定义。",
                    sheet=MAPPING_SHEET_NAME,
                    row=current_row_num
                )

            # 将追加的SUPP字段加入标准字段集中 
            supp_time_flg = False
            outputFields = STANDARD_FIELDS[domain_key]
            if variable not in outputFields:
                if variable.endswith('DTC'):
                    supp_time_flg = True
                STANDARD_FIELDS[domain_key].append(variable)

            if domain_key not in mappingDict:
                mappingDict[domain_key] = {}

            if not oper_type:
                current_row_num += 1
                continue

            if active_definition_row not in mappingDict[domain_key]:
                mappingDict[domain_key][active_definition_row] = {}
            if variable not in mappingDict[domain_key][active_definition_row]:
                mappingDict[domain_key][active_definition_row][variable] = {}

            mappingDict[domain_key][active_definition_row][variable][COL_NDKEY] = nd_keys in MARK_CIRCLE
            mappingDict[domain_key][active_definition_row][variable][COL_FIELDNAME] = field_name
            mappingDict[domain_key][active_definition_row][variable][COL_OPERTYPE] = oper_type
            mappingDict[domain_key][active_definition_row][variable][COL_PARAMETER] = parameter
            mappingDict[domain_key][active_definition_row][variable]['SUPPTIMEFLG'] = supp_time_flg

        except MappingConfigurationError:
            raise
        except Exception as exc:
            raise MappingConfigurationError(
                f"读取Mapping工作表第{current_row_num}行时发生未处理的错误: {exc}",
                sheet=MAPPING_SHEET_NAME,
                row=current_row_num,
                original_exception=exc
            ) from exc

        current_row_num += 1

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
            sortkeys.insert(0, COL_USUBJID)
        domainsSettingDict[domain_name] = sortkeys
    return domainsSettingDict

# Refactoring時に必要なファイルを読込
def getFormatDataset(*fileNames):
    allFileNameList = list(fileNames)

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
    current_row_num = site_sheetsetting[COL_STARTINGROW]
    for row in workbook[SITEMASTER_SHEET_NAME].iter_rows(min_row=site_sheetsetting[COL_STARTINGROW], min_col=1, max_col=site_sheetsetting[COL_MAXCOL], values_only=True):
        if not any(row):
            break
        site_name = get_cell_value(row, colnum_sitename)
        site_code = get_cell_value(row, colnum_sitecode)
        if not site_name:
            raise MappingConfigurationError(
                f"第{current_row_num}行的SiteName列为空。",
                sheet=SITEMASTER_SHEET_NAME,
                row=current_row_num
            )
        if not site_code:
            raise MappingConfigurationError(
                f"第{current_row_num}行的SiteCode列为空，SiteName='{site_name}'。",
                sheet=SITEMASTER_SHEET_NAME,
                row=current_row_num
            )
        siteDict[site_name] = site_code
        current_row_num += 1
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
