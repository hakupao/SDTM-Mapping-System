"""
VAPORCONE 项目CSV转JSON模块

该模块负责将CSV文件转换为JSON格式的数据包，包括：
- 读取输入CSV文件
- 构建JSON数据结构
- 生成M5格式的数据包
- 创建压缩文件
"""

from VC_BC03_fetchConfig import *


def main():
    """
    主函数，执行CSV转JSON流程
    """
    create_directory(INPUTPACKAGE_PATH)
    makePackage()


def makePackage():
    """
    创建数据包，将CSV文件转换为JSON格式并打包
    """
    inputFilePath = INPUTFILE_PATH
    packagePath = INPUTPACKAGE_PATH
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
    for file_name in all_files:
        with open(os.path.join(inputFilePath, file_name), 'r', encoding="utf-8-sig") as csvfile:
            dict_result = csv.DictReader(csvfile)
            
            if file_name == 'DM.csv':
                # 处理DM（人口统计学）数据
                for row in dict_result:
                    usubjid_dict[row['USUBJID']] = row
                    usubjid_subjid_dict[row['USUBJID']] = row['SUBJID']
                print("DM len:", len(usubjid_dict))
                print('---------')
            else:
                # 处理其他数据文件
                other_file_name_without_extension, extension = os.path.splitext(file_name)
                subjid_other_one_dict = {}
                
                for row in dict_result:
                    if 'USUBJID' in row:
                        if row['USUBJID'] not in subjid_other_one_dict:
                            subjid_other_one_dict[row['USUBJID']] = []
                        subjid_other_one_dict[row['USUBJID']].append(row)
                    else:
                        print(other_file_name_without_extension + ' skip')
                        break

                if subjid_other_one_dict:
                    subjid_other_all_dict[other_file_name_without_extension] = subjid_other_one_dict

    # 输出文件统计信息
    for subjid_other_file_name in subjid_other_all_dict:
        print(subjid_other_file_name + " len:", len(subjid_other_all_dict[subjid_other_file_name]))
    print('---------')

    # 为每个受试者生成JSON文件
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

    # 创建压缩文件
    shutil.make_archive(zipfile, 'zip', zip_source_folder)

if __name__ == "__main__":
    print(f'Study:{STUDY_ID} Processing has begun.' )
    main()
    print(f'Study:{STUDY_ID} Processing is over.' )
