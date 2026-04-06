"""
VAPORCONE 项目输入CSV创建模块

该模块负责将SDTM数据集转换为输入CSV文件，包括：
- 分离标准字段和补充字段
- 生成主数据文件
- 生成补充数据文件
- 处理站点代码转换
"""

from VC_BC03_fetchConfig import *

STEP_ID = 'PS01'
STEP_NAME = 'MakeInputCSV'


def main():
    """
    主函数，执行输入CSV文件创建流程
    """
    logger = create_logger(
        os.path.join(SPECIFIC_PATH, 'log_file.log'),
        log_level=logging.DEBUG
    )

    actual_inputfile_path = create_directory(INPUTFILE_PATH, INPUTFILE_DATASET_PATH)
    print(f'输出路径: {actual_inputfile_path}')

    workbook = load_workbook(filename=os.path.join(SPECIFIC_PATH, CONFIG_NAME))
    sheetSetting = getSheetSetting(workbook)
    siteDict = getSites(workbook, sheetSetting)

    # 动态获取最新的SDTM数据文件夹路径
    actual_sdtm_path = find_latest_timestamped_path(SDTMDATASET_PATH, 'sdtm_dataset')

    if not os.path.exists(actual_sdtm_path):
        log_and_print(logger, 'ERROR', f'SDTM数据路径不存在: {actual_sdtm_path}')
        sys.exit(1)

    all_files = os.listdir(actual_sdtm_path)
    if not all_files:
        log_and_print(logger, 'ERROR', f'SDTM数据目录为空: {actual_sdtm_path}')
        sys.exit(1)

    inclusion_domain = [f.replace('.csv', '') for f in all_files]
    print(f'配置加载完成: 站点={len(siteDict)}, SDTM路径={actual_sdtm_path}')
    print(f'待处理域: {inclusion_domain}')
    print_summary_sep()

    # 处理摘要收集
    summary = []
    site_warnings = []

    for full_name in all_files:
        sdtm_data_file_path = os.path.join(actual_sdtm_path, full_name)

        domain = full_name.replace('.csv', '')

        # 防御性校验: 检查domain是否在STANDARD_FIELDS中
        if domain not in STANDARD_FIELDS:
            log_and_print(
                logger, 'ERROR',
                f'域[{domain}]未在STANDARD_FIELDS中定义，跳过。请检查VC_BC01_constant.py'
            )
            continue

        standard_fields = STANDARD_FIELDS[domain]

        # 读取SDTM数据文件
        data_list = []
        with open(sdtm_data_file_path, 'r', newline='', encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames
            for row in reader:
                data_list.append(row)

        # 区分标准字段和补充字段
        common_fields = [field for field in fieldnames if field in standard_fields]
        supp_fields = [field for field in fieldnames if field not in standard_fields]
        supp_data_list = []

        # 为非排除域添加PAGEID和RECORDID字段
        for shorten_name in list(set(inclusion_domain) - set(EXCLUSION_DOMAIN)):
            if shorten_name in full_name:
                common_fields.append("PAGEID")
                common_fields.append("RECORDID")
                break

        csv_file_path = os.path.join(actual_inputfile_path, full_name)
        site_warning_count = 0
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
                                site_warning_count += 1
                                if site_warning_count <= 3:
                                    site_warnings.append(
                                        f'  域[{domain}] USUBJID=[{rUSUBJID}] SITEID=[{row_field_val}] '
                                        f'在Sites工作表中未定义'
                                    )
                                logger.warning(
                                    f'域[{domain}] USUBJID=[{rUSUBJID}] SITEID=[{row_field_val}] 未在Sites工作表中定义'
                                )
                            else:
                                output_row[field] = siteDict[row_field_val]

                writer.writerow(output_row)

                if supp_fields:
                    for field in supp_fields:
                        field_val = row.get(field, '')
                        if field_val is None:
                            field_val = ''

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
            supp_csv_file_path = os.path.join(actual_inputfile_path, "SUPP" + full_name)
            with open(supp_csv_file_path, 'w', newline='', encoding='utf-8-sig') as suppcsvfile_out:
                writer = csv.DictWriter(suppcsvfile_out, ["STUDYID", "RDOMAIN", "USUBJID", "IDVAR", "IDVARVAL", "QNAM", "QLABEL", "QVAL", "QORIG"])
                writer.writeheader()
                writer.writerows(supp_data_list)

        summary.append({
            'domain': domain, 'records': len(data_list),
            'standard_fields': len(common_fields), 'supp_fields': len(supp_fields),
            'supp_records': len(supp_data_list), 'site_warnings': site_warning_count,
        })
        logger.info(
            f'域[{domain}] 记录={len(data_list)}, 标准字段={len(common_fields)}, '
            f'补充字段={len(supp_fields)}, SUPP记录={len(supp_data_list)}'
        )

    # SITEID警告汇总
    if site_warnings:
        print()
        log_and_print(logger, 'WARN', 'SITEID转换警告:')
        for w in site_warnings:
            print(w)
        total_site_warns = sum(s['site_warnings'] for s in summary)
        if total_site_warns > len(site_warnings):
            print(f'  ... 共 {total_site_warns} 条(请检查Sites工作表)')

    # 处理摘要
    W = [10, 8, 10, 10, 10, 10]  # 各列显示宽度
    cols = ['域', '记录数', '标准字段', '补充字段', 'SUPP记录', 'SITE警告']
    print_summary_header(f'处理摘要 - {STEP_NAME}')
    print(
        cjk_ljust(cols[0], W[0]) + ' '
        + ' '.join(cjk_rjust(c, w) for c, w in zip(cols[1:], W[1:]))
    )
    print_summary_sep()
    for s in summary:
        print(
            f'{s["domain"]:<{W[0]}} {s["records"]:>{W[1]}} {s["standard_fields"]:>{W[2]}} '
            f'{s["supp_fields"]:>{W[3]}} {s["supp_records"]:>{W[4]}} {s["site_warnings"]:>{W[5]}}'
        )
    print_summary_sep()
    print_summary_kv('处理域数', len(summary))
    print_summary_kv('总记录数', sum(s['records'] for s in summary))


if __name__ == "__main__":
    print_step_header(STEP_ID, STEP_NAME)
    main()
    print_step_footer(STEP_ID, STEP_NAME)
