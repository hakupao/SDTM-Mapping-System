"""
VAPORCONE 项目输入CSV创建模块

该模块负责将SDTM数据集转换为输入CSV文件，包括：
- 分离标准字段和补充字段
- 生成主数据文件
- 生成补充数据文件
- 处理站点代码转换
"""

from VC_BC03_fetchConfig import *


def main():
    """
    主函数，执行输入CSV文件创建流程
    """
    create_directory(INPUTFILE_PATH)
    workbook = load_workbook(filename=os.path.join(SPECIFIC_PATH, CONFIG_NAME))
    sheetSetting = getSheetSetting(workbook)
    siteDict = getSites(workbook, sheetSetting)

    # 🆕 动态获取最新的SDTM数据文件夹路径
    actual_sdtm_path = find_latest_timestamped_path(SDTMDATASET_PATH, 'sdtm_dataset')
    print(f'使用SDTM数据路径: {actual_sdtm_path}')

    all_files = os.listdir(actual_sdtm_path)
    inclusion_domain = [f.replace('.csv', '') for f in all_files]

    for full_name in all_files:
        sdtm_data_file_path = os.path.join(actual_sdtm_path, full_name)
        
        domain = full_name.replace('.csv', '')
        standard_fields = STANDARD_FIELDS[domain]

        # 读取SDTM数据文件
        data_list = []
        with open(sdtm_data_file_path, 'r', newline='', encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames
            for row in reader:
                data_list.append(row)
        
        # 区分标准字段和补充字段
        common_fields = list(set(standard_fields) & set(fieldnames))
        supp_fields = list(set(fieldnames) - set(standard_fields))
        supp_data_list = []
        
        # 为非排除域添加PAGEID和RECORDID字段
        for shorten_name in list(set(inclusion_domain) - set(EXCLUSION_DOMAIN)):                
            if shorten_name in full_name:
                common_fields.append("PAGEID")
                common_fields.append("RECORDID")
                break

        csv_file_path = os.path.join(INPUTFILE_PATH, full_name)
        with open(csv_file_path, 'w', newline='', encoding='utf-8-sig') as csvfile_out:
            writer = csv.DictWriter(csvfile_out, fieldnames=common_fields)
            writer.writeheader()

            for row in data_list:
                rUSUBJID = row["USUBJID"]
                
                output_row = {}
                for field in common_fields:
                    if field == "PAGEID":
                        output_row[field] = row["SEQ"] if domain == "SREF" else row[domain + "SEQ"]
                    elif field == "RECORDID":
                        output_row[field] = "1"
                    else:
                        row_field_val = row[field]
                        output_row[field] = row_field_val

                        if field == "SITEID":
                            if row_field_val not in siteDict:
                                print(f'case:[{rUSUBJID}] site:[{row_field_val}] code is not existed')
                            else:
                                output_row[field] = siteDict[row_field_val]

                writer.writerow(output_row)

                if supp_fields:
                    for field in supp_fields:
                        field_val = row[field]
                        if field_val:
                            supp_output_row = {}
                            supp_output_row["STUDYID"] = row["STUDYID"]
                            supp_output_row["RDOMAIN"] = domain
                            supp_output_row["USUBJID"] = rUSUBJID
                            supp_output_row["IDVAR"] = "" if domain in EXCLUSION_DOMAIN else "PAGEID"
                            supp_output_row["IDVARVAL"] = "" if domain in EXCLUSION_DOMAIN else row["SEQ"] if domain == "SREF" else row[domain + "SEQ"]
                            supp_output_row["QNAM"] = field
                            supp_output_row["QLABEL"] = ""
                            supp_output_row["QVAL"] = field_val
                            supp_output_row["QORIG"] = "CRF"
                            supp_data_list.append(supp_output_row)

        if supp_data_list:
            supp_csv_file_path = os.path.join(INPUTFILE_PATH, "SUPP" + full_name)
            with open(supp_csv_file_path, 'w', newline='', encoding='utf-8-sig') as suppcsvfile_out:
                writer = csv.DictWriter(suppcsvfile_out, ["STUDYID", "RDOMAIN", "USUBJID", "IDVAR", "IDVARVAL", "QNAM", "QLABEL", "QVAL", "QORIG"])
                writer.writeheader()
                writer.writerows(supp_data_list)

if __name__ == "__main__":
    print(f'Study:{STUDY_ID} Processing has begun.' )
    main()
    print(f'Study:{STUDY_ID} Processing is over.' )
