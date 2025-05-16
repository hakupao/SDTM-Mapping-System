from VC_BC03_fetchConfig import *


def main():
    
    logger = create_logger(os.path.join(SPECIFIC_PATH, 'log_file.log'), log_level=logging.DEBUG)
    
    workbook = load_workbook(filename=os.path.join(SPECIFIC_PATH, CONFIG_NAME))
    sheetSetting = getSheetSetting(workbook)
    
    mappingError(workbook, sheetSetting)
    

def mappingError(workbook, sheetSetting):
    
    colnum_domain = sheetSetting[MAPPING_SHEET_NAME][COL_DOMAIN]
    colnum_variable = sheetSetting[MAPPING_SHEET_NAME][COL_VARIABLE]
    colnum_field_name = sheetSetting[MAPPING_SHEET_NAME][COL_FIELDNAME]
    colnum_oper_type = sheetSetting[MAPPING_SHEET_NAME][COL_OPERTYPE]
    colnum_parameter = sheetSetting[MAPPING_SHEET_NAME][COL_PARAMETER]

    starting_row_num = sheetSetting[MAPPING_SHEET_NAME][COL_STARTINGROW]
    mapping_sheet = workbook[MAPPING_SHEET_NAME]
    
    for row in mapping_sheet.iter_rows(min_row=starting_row_num, 
                                       min_col=1, 
                                       max_col=sheetSetting[MAPPING_SHEET_NAME][COL_MAXCOL], 
                                       values_only=True):
        starting_row_num += 1
        if not any(row):  # 如果整行都为空，退出循环
            break
        
        domain = get_cell_value(row, colnum_domain)
        variable = get_cell_value(row, colnum_variable)
        field_name = get_cell_value(row, colnum_field_name)
        oper_type = get_cell_value(row, colnum_oper_type)
        parameter = get_cell_value(row, colnum_parameter)
        
        error_colnum = starting_row_num - 1
    
        # 判断 domain 或 variable 是否为空
        if not domain :
            print(f"Error Missing 'domain' at row {error_colnum}")
        
        if not variable :
            print(f"Error Missing 'variable' at row {error_colnum}")
            
        if oper_type != 'DEF' and not field_name :
            print(f"Error Missing 'field_name' at row {error_colnum}")
            
        if oper_type != 'FIX' and oper_type != 'COB' and not parameter :
            print(f"Error Missing 'parameter' at row {error_colnum}")

if __name__ == "__main__":
    print("Start checking config...")
    main()
    print("Checking config done!")