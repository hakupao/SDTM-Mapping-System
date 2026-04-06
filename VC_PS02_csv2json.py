"""
VAPORCONE 项目CSV转JSON模块

该模块负责将CSV文件转换为JSON格式的数据包，包括：
- 读取输入CSV文件
- 构建JSON数据结构
- 生成M5格式的数据包
- 创建压缩文件
"""

from VC_BC03_fetchConfig import *

STEP_ID = 'PS02'
STEP_NAME = 'CSV2JSON'


def main():
    """
    主函数，执行CSV转JSON流程
    """
    logger = create_logger(
        os.path.join(SPECIFIC_PATH, 'log_file.log'),
        log_level=logging.DEBUG
    )

    actual_inputpackage_path = create_directory(INPUTPACKAGE_PATH, INPUTPACKAGE_DATASET_PATH)
    print(f'输出路径: {actual_inputpackage_path}')
    makePackage(actual_inputpackage_path, logger)


def resolve_inputfile_path():
    """
    获取最新的输入CSV目录，并兼容历史的根目录直写结构
    """
    actual_inputfile_path = find_latest_timestamped_path(INPUTFILE_PATH, 'inputfile_dataset')
    if os.path.exists(actual_inputfile_path):
        return actual_inputfile_path

    legacy_files = [
        item for item in os.listdir(INPUTFILE_PATH)
        if os.path.isfile(os.path.join(INPUTFILE_PATH, item))
    ] if os.path.exists(INPUTFILE_PATH) else []

    if legacy_files:
        print(f'未找到时间戳Input CSV目录，回退到原始目录: {INPUTFILE_PATH}')
        return INPUTFILE_PATH

    return actual_inputfile_path


def makePackage(packagePath, logger):
    """
    创建数据包，将CSV文件转换为JSON格式并打包
    """
    inputFilePath = resolve_inputfile_path()
    print(f'输入路径: {inputFilePath}')

    if not os.path.exists(inputFilePath):
        log_and_print(logger, 'ERROR', f'Input CSV路径不存在: {inputFilePath}')
        sys.exit(1)

    projectName = M5_PROJECT_NAME

    # 定义输出目录结构
    tabulations_path = os.path.join(
        packagePath, 'm5', 'm5', 'datasets', projectName, 'tabulations'
    )
    out_crf_sub_folder = os.path.join(tabulations_path, 'sdtm', 'crf')
    out_others_sub_folder = os.path.join(tabulations_path, 'sdtm', 'others')
    out_cp_sub_folder = os.path.join(tabulations_path, 'cp')

    create_directory(out_crf_sub_folder, out_others_sub_folder, out_cp_sub_folder)

    zip_source_folder = os.path.join(packagePath, 'm5')
    zipfile = os.path.join(packagePath, 'm5')

    # 数据字典初始化
    usubjid_dict = {}
    usubjid_subjid_dict = {}
    subjid_other_all_dict = {}

    all_files = os.listdir(inputFilePath)
    if not all_files:
        log_and_print(logger, 'ERROR', f'Input CSV目录为空: {inputFilePath}')
        sys.exit(1)

    # 预检查: DM.csv必须存在
    if 'DM.csv' not in all_files:
        log_and_print(
            logger, 'ERROR',
            f'DM.csv未找到。DM是必须的基准文件。路径: {inputFilePath}, 可用文件: {all_files}'
        )
        sys.exit(1)

    print(f'配置加载完成: 待处理文件={len(all_files)}')
    print_summary_sep()

    # 文件级统计
    file_stats = []
    skipped_files = []

    for file_name in all_files:
        with open(os.path.join(inputFilePath, file_name), 'r', encoding="utf-8-sig") as csvfile:
            dict_result = csv.DictReader(csvfile)

            if file_name == 'DM.csv':
                # 处理DM（人口统计学）数据
                for row in dict_result:
                    usubjid_dict[row['USUBJID']] = row
                    usubjid_subjid_dict[row['USUBJID']] = row['SUBJID']
                file_stats.append({'file': 'DM', 'subjects': len(usubjid_dict), 'records': len(usubjid_dict)})
                logger.info(f'DM加载完成: {len(usubjid_dict)} 个受试者')
            else:
                # 处理其他数据文件
                other_file_name_without_extension, extension = os.path.splitext(file_name)
                subjid_other_one_dict = {}
                record_count = 0

                for row in dict_result:
                    if 'USUBJID' in row:
                        record_count += 1
                        if row['USUBJID'] not in subjid_other_one_dict:
                            subjid_other_one_dict[row['USUBJID']] = []
                        subjid_other_one_dict[row['USUBJID']].append(row)
                    else:
                        log_and_print(
                            logger, 'WARN',
                            f'{other_file_name_without_extension}: USUBJID列不存在，跳过。'
                            f'请确认Input CSV是否正确生成'
                        )
                        skipped_files.append(other_file_name_without_extension)
                        break

                if subjid_other_one_dict:
                    subjid_other_all_dict[other_file_name_without_extension] = subjid_other_one_dict
                    file_stats.append({
                        'file': other_file_name_without_extension,
                        'subjects': len(subjid_other_one_dict),
                        'records': record_count,
                    })

    # 受试者一致性校验
    orphaned_subjects = {}
    for domain_name, domain_data in subjid_other_all_dict.items():
        for usubjid in domain_data:
            if usubjid not in usubjid_dict:
                if usubjid not in orphaned_subjects:
                    orphaned_subjects[usubjid] = []
                orphaned_subjects[usubjid].append(domain_name)

    if orphaned_subjects:
        log_and_print(
            logger, 'WARN',
            f'{len(orphaned_subjects)} 个受试者在域文件中有数据但DM中不存在:'
        )
        for i, (usubjid, domains) in enumerate(orphaned_subjects.items()):
            if i >= 10:
                print(f'  ... 还有 {len(orphaned_subjects) - 10} 个')
                break
            print(f'  USUBJID=[{usubjid}] 出现在: {", ".join(domains)}')

    # 为每个受试者生成JSON文件
    json_count = 0
    for usubjid in usubjid_dict:
        out_dict = {}
        out_dict['study_id'] = usubjid_dict[usubjid]['STUDYID']
        out_dict['unified_id'] = usubjid_dict[usubjid]['USUBJID']
        out_dict['crf_datas'] = {}
        out_dict['crf_datas']['DM'] = usubjid_dict[usubjid]

        # 添加其他数据
        for subjid_other_file_name in subjid_other_all_dict:
            if usubjid in subjid_other_all_dict[subjid_other_file_name]:
                out_dict['crf_datas'][subjid_other_file_name] = subjid_other_all_dict[subjid_other_file_name][usubjid]

        # 输出JSON文件
        with open(
            os.path.join(out_crf_sub_folder, usubjid_subjid_dict[usubjid] + '.json'),
            "w",
            encoding="utf-8-sig"
        ) as out_file:
            json.dump(out_dict, out_file, ensure_ascii=False)
        json_count += 1

    # 创建压缩文件
    shutil.make_archive(zipfile, 'zip', zip_source_folder)

    # 处理摘要
    W = [16, 8, 8]  # 各列显示宽度
    cols = ['文件', '受试者数', '记录数']
    print_summary_header(f'处理摘要 - {STEP_NAME}')
    print(
        cjk_ljust(cols[0], W[0]) + ' '
        + ' '.join(cjk_rjust(c, w) for c, w in zip(cols[1:], W[1:]))
    )
    print_summary_sep()
    for s in file_stats:
        print(f'{s["file"]:<{W[0]}} {s["subjects"]:>{W[1]}} {s["records"]:>{W[2]}}')
    print_summary_sep()
    print_summary_kv('生成JSON文件', f'{json_count} 个')
    print_summary_kv('域文件数', len(file_stats))
    if skipped_files:
        print_summary_kv('跳过文件', skipped_files)
    if orphaned_subjects:
        print_summary_kv('孤立受试者', f'{len(orphaned_subjects)} 个')
    print_summary_kv('M5压缩包', f'{zipfile}.zip')
    logger.info(f'M5完成: JSON={json_count}, 域={len(file_stats)}, 孤立受试者={len(orphaned_subjects)}')


if __name__ == "__main__":
    print_step_header(STEP_ID, STEP_NAME)
    main()
    print_step_footer(STEP_ID, STEP_NAME)
