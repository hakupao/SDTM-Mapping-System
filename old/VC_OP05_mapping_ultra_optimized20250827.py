"""
VAPORCONE 项目映射模块 - 超级优化版本 (重构版)

该模块负责将格式化的数据映射为SDTM标准格式，包括：
- 读取映射配置
- 执行字段映射操作
- 处理序列号生成
- 生成SDTM数据集

专门针对序号生成瓶颈的终极优化：
1. 并行Domain处理 - 多进程处理不同域
2. 序号算法改进 - 高效序号分配策略
3. 预排序优化 - 智能排序键预处理
4. 批量处理 - 减少单条记录处理开销
5. 内存优化 - 数据类型和内存使用优化
"""

import time
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict
import numpy as np
import pandas as pd
from VC_BC03_fetchConfig import *
from VC_BC04_operateType import *

# 全局变量
actual_format_path = None

def vectorized_domain_mapping_ultra(domain_key, precomputed_rules, caseDict, codeDict, standard_fields, domainsSettingDict, sequenceDict):
    """
    超级优化的域映射处理
    
    参数:
    - domain_key (str): 域名
    - precomputed_rules (dict): 预计算的映射规则
    - caseDict (dict): 案例字典
    - codeDict (dict): 代码字典
    - standard_fields (list): 标准字段列表
    - domainsSettingDict (dict): 域设置字典
    - sequenceDict (dict): 序号字典
    
    返回:
    - DataFrame: 映射后的数据框
    """
    all_results = []
    seq_field = domain_key + VARIABLE_SEQSUFF
    
    # 🔑 添加Domain级别去重，与原版保持一致
    unique_combinations = set()
    
    # 🔑 关键修复：按definition_row_num排序，保持Excel定义顺序
    sorted_definition_items = sorted(precomputed_rules.items(), key=lambda x: x[0])
    
    for definition_row_num, rule_info in sorted_definition_items:
        combo_file_name = rule_info['combo_file_name']
        cycle_time = rule_info['cycle_time']
        field_rules = rule_info['field_rules']
        needed_columns = rule_info['needed_columns']
        
        print(f"处理 Definition {definition_row_num}: {combo_file_name}, cycles={cycle_time}")
        
        # 读取CSV
        file_path = os.path.join(actual_format_path, f'{PREFIX_F}{combo_file_name}{EXTENSION}')
        be_converted_df = get_cached_csv(file_path, needed_columns)
        
        if be_converted_df.empty:
            continue
        
        # 优化的预处理
        be_converted_df = be_converted_df.copy()
        be_converted_df['USUBJID'] = be_converted_df['SUBJID'].map(caseDict)
        
        # 批量初始化基础数据
        n_rows = len(be_converted_df)
        base_data = {
            'STUDYID': np.full(n_rows, STUDY_ID, dtype='object'),
            'DOMAIN': np.full(n_rows, domain_key, dtype='object'),
            'USUBJID': be_converted_df['USUBJID'].values,
            'SUBJID': be_converted_df['SUBJID'].values
        }
        
        # 批量初始化所有字段
        for field in standard_fields:
            if field not in base_data:
                base_data[field] = np.full(n_rows, MARK_BLANK, dtype='object')
        
        # 🔑 修改为原版逻辑：每个cycle处理后立即合并到all_results，而不是Definition级别批量处理
        for cycle_idx in range(cycle_time):
            result_df = pd.DataFrame(base_data.copy())
            continue_flags = np.zeros(len(result_df), dtype=bool)
            
            # 向量化字段处理 - 先完成所有字段的赋值操作
            for standard_field, field_rule in field_rules.items():
                try:
                    result_df, field_continue_flags = vectorized_field_mapping(
                        result_df, be_converted_df, standard_field, field_rule, cycle_idx, codeDict
                    )
                    continue_flags |= field_continue_flags
                except Exception as e:
                    pass
            
            # 所有字段处理完成后，统一检查ndkey条件
            null_deletion_flags = np.zeros(len(result_df), dtype=bool)
            
            # 检查每行是否至少有一个ndkey=True的字段有非空值
            for standard_field, field_rule in field_rules.items():
                if field_rule['ndkey']:  # 只检查ndkey=True的字段
                    if standard_field in result_df.columns:
                        non_empty = (result_df[standard_field] != '') & (result_df[standard_field].notna())
                        null_deletion_flags |= non_empty.values
            
            # 应用过滤条件：不在continue_flags中 AND 至少有一个ndkey字段有值
            valid_rows = ~continue_flags & null_deletion_flags
            if np.any(valid_rows):
                filtered_df = result_df[valid_rows].copy()
                
                # 🔑 添加Domain级别去重逻辑，与原版保持一致
                # 去重处理：检查每行数据组合是否已存在
                deduped_rows = []
                for idx, row in filtered_df.iterrows():
                    # 创建用于去重的组合（排除SEQ字段）
                    combination = tuple(row[field] for field in standard_fields if field != seq_field)
                    if combination not in unique_combinations:
                        unique_combinations.add(combination)
                        deduped_rows.append(row)
                
                if deduped_rows:
                    # 重新构建DataFrame
                    cycle_dataset = pd.DataFrame(deduped_rows)
                    
                    # 🔑 改为原版逻辑：每个cycle处理完立即排序、分配序号、合并
                    if seq_field in cycle_dataset.columns and len(cycle_dataset) > 0:
                        # 获取排序键
                        if domain_key in domainsSettingDict:
                            sort_keys = domainsSettingDict[domain_key]
                        else:
                            sort_keys = [VARIABLE_USUBJID]
                        
                        # 在cycle级别进行排序和序号分配
                        cycle_dataset = ultra_fast_sequence_generation(cycle_dataset, seq_field, sort_keys, domain_key, sequenceDict)
                    
                    else:
                        # DM domain等没有SEQ字段的情况，只进行排序处理
                        # 获取排序键
                        if domain_key in domainsSettingDict:
                            sort_keys = domainsSettingDict[domain_key]
                        else:
                            sort_keys = [VARIABLE_USUBJID]
                        
                        # 只进行排序，不分配序号
                        if len(cycle_dataset) > 0:
                            # 处理EPOCH字段（如果存在）
                            if 'EPOCH' in sort_keys and 'EPOCH' in cycle_dataset.columns:
                                # 创建临时排序列
                                epoch_sort_col = '_EPOCH_SORT_TEMP'
                                cycle_dataset[epoch_sort_col] = cycle_dataset['EPOCH'].fillna('').astype(str)
                                cycle_dataset[epoch_sort_col] = cycle_dataset[epoch_sort_col].str.replace('TREATMENT', '', regex=False)
                                cycle_dataset[epoch_sort_col] = pd.to_numeric(cycle_dataset[epoch_sort_col], errors='coerce').fillna(0).astype('int32')
                                
                                # 替换排序键中的EPOCH
                                actual_sort_keys = []
                                for key in sort_keys:
                                    if key == 'EPOCH':
                                        actual_sort_keys.append(epoch_sort_col)
                                    else:
                                        actual_sort_keys.append(key)
                            else:
                                actual_sort_keys = sort_keys
                            
                            # 执行排序
                            available_sort_keys = [key for key in actual_sort_keys if key in cycle_dataset.columns]
                            if available_sort_keys:
                                cycle_dataset = cycle_dataset.sort_values(available_sort_keys, kind='mergesort')
                            
                            # 清理临时列
                            if 'EPOCH' in sort_keys and '_EPOCH_SORT_TEMP' in cycle_dataset.columns:
                                cycle_dataset = cycle_dataset.drop('_EPOCH_SORT_TEMP', axis=1)
                    
                    # 立即添加到结果中（类似原版的domain_dataset[domain_key].extend(definition_dataset)）
                    all_results.append(cycle_dataset)
    
    # 🔑 修改为原版逻辑：合并结果（排序和序号已在cycle级别完成）
    if all_results:
        combined_df = pd.concat(all_results, ignore_index=True)
        return combined_df
    else:
        return pd.DataFrame()

def process_single_domain(args):
    """
    单个Domain的处理函数 - 用于并行处理
    
    参数:
    - args (tuple): 包含处理参数的元组
    
    返回:
    - tuple: (域名, 结果数据, 记录数)
    """
    domain_key, domain_param, definition_merge_rule, caseDict, codeDict, standard_fields, domainsSettingDict, format_path, initial_sequence_dict = args
    
    try:
        # 设置当前进程的格式化路径和缓存
        global actual_format_path, csv_cache
        actual_format_path = format_path
        csv_cache = {}  # 每个进程独立的缓存
        
        # 创建本进程的sequenceDict副本
        sequenceDict = initial_sequence_dict.copy()
        for usubjid in sequenceDict:
            sequenceDict[usubjid] = sequenceDict[usubjid].copy()
                
        # 预计算映射规则
        precomputed_rules = precompute_mapping_rules(domain_param, definition_merge_rule)
        print(f"Domain {domain_key} - 预计算完成，规则数: {len(precomputed_rules)}")
        
        # 向量化域映射
        domain_df = vectorized_domain_mapping_ultra(
            domain_key, precomputed_rules, caseDict, codeDict, 
            standard_fields[domain_key], domainsSettingDict, sequenceDict
        )
        print(f"Domain {domain_key} - 映射完成，记录数: {len(domain_df) if not domain_df.empty else 0}")
        
        if not domain_df.empty:
            # 确保列顺序
            domain_df = domain_df[standard_fields[domain_key]]
            result_data = domain_df.to_dict('records')
        else:
            result_data = []
        
        return domain_key, result_data, len(result_data)
        
    except Exception as e:
        print(f"Domain {domain_key} 处理出错: {e}")
        return domain_key, [], 0

def main():
    """
    主函数 - 超级优化版本 (重构版)
    """
    print(f"开始SDTM映射处理 - 超级优化版本 (重构版)")
    start_time = time.time()
    
    # 配置读取阶段
    logger = create_logger(
        os.path.join(SPECIFIC_PATH, 'log_file.log'), 
        log_level=logging.DEBUG
    )
    sdtm_dataset_path = create_directory(SDTMDATASET_PATH, SDTMDATASET_FILE_PATH)
    
    global actual_format_path
    actual_format_path = find_latest_timestamped_path(FORMAT_PATH, 'format_dataset')
    print(f'使用格式化数据路径: {actual_format_path}')
    
    workbook = load_workbook(filename=os.path.join(SPECIFIC_PATH, CONFIG_NAME))
    sheetSetting = getSheetSetting(workbook)
    
    caseDict = getCaseDict(workbook, sheetSetting)
    codeDict, _, _ = getCodeListInfo(workbook, sheetSetting)
    mappingDict, definition_merge_rule = getMapping(workbook, sheetSetting)
    domainsSettingDict = getDomainsSetting(workbook, sheetSetting)
    
    # 初始化序列号字典
    sequenceDict = {}
    for usubjid in caseDict.values():
        if usubjid not in sequenceDict:
            sequenceDict[usubjid] = {}
        for domain_name in STANDARD_FIELDS.keys():
            sequenceDict[usubjid][domain_name] = 1
    
    # 准备并行处理参数
    domain_args = []
    for domain_key, domain_param in mappingDict.items():
        args = (domain_key, domain_param, definition_merge_rule, caseDict, 
                codeDict, STANDARD_FIELDS, domainsSettingDict, actual_format_path, sequenceDict)
        domain_args.append(args)
    
    domain_dataset = {}
    
    # 决定是否使用并行处理
    use_parallel = len(domain_args) >= 3  # 至少3个Domain才使用并行
    
    if use_parallel:
        # 使用进程池并行处理
        max_workers = min(mp.cpu_count() - 1, len(domain_args), 4)  # 最多4个进程
        print(f"使用 {max_workers} 个进程并行处理 {len(domain_args)} 个Domain")
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_domain = {executor.submit(process_single_domain, args): args[0] 
                              for args in domain_args}
            
            # 收集结果
            for future in as_completed(future_to_domain):
                domain_key = future_to_domain[future]
                try:
                    domain_key, result_data, record_count = future.result()
                    domain_dataset[domain_key] = result_data
                    print(f'{domain_key} conversion completed (并行) - {record_count} 条记录')
                except Exception as e:
                    print(f'Domain {domain_key} 处理失败: {e}')
                    domain_dataset[domain_key] = []
    else:
        # 串行处理（小数据集）
        print("使用串行处理（Domain数量较少）")
        for args in domain_args:
            try:
                domain_key, result_data, record_count = process_single_domain(args)
                domain_dataset[domain_key] = result_data
                print(f'{domain_key} conversion completed (串行) - {record_count} 条记录')
            except Exception as e:
                print(f'Domain {args[0]} 处理失败: {e}')
                domain_dataset[args[0]] = []
    
    # 优化的文件输出
    print("开始保存SDTM数据集文件...")
    output_start = time.time()
    
    for domain, dataList in domain_dataset.items():
        if dataList:
            # 直接使用pandas进行高效输出
            df = pd.DataFrame(dataList)
            header = STANDARD_FIELDS[domain]
            
            # 最终排序优化
            seq_field = domain + VARIABLE_SEQSUFF
            if seq_field in header and seq_field in df.columns:
                # 确保数据类型
                df[VARIABLE_USUBJID] = df[VARIABLE_USUBJID].astype('category')
                df[seq_field] = pd.to_numeric(df[seq_field], errors='coerce').fillna(0).astype('int32')
                df = df.sort_values([VARIABLE_USUBJID, seq_field])
            
            # 高效写入
            output_path = os.path.join(sdtm_dataset_path, f'{domain}{EXTENSION}')
            df[header].to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f'{domain} file saved - {len(dataList)} 条记录')
    
    output_time = time.time() - output_start
    total_time = time.time() - start_time
    
    print(f"\n=== 处理完成统计 ===")
    print(f"总处理时间: {total_time:.2f} 秒")
    print(f"文件输出时间: {output_time:.2f} 秒")
    print(f"数据处理时间: {total_time - output_time:.2f} 秒")
    print(f"处理的Domain数量: {len(domain_dataset)}")
    total_records = sum(len(data) for data in domain_dataset.values())
    print(f"生成的总记录数: {total_records}")
    if total_time > 0:
        print(f"处理速度: {total_records/total_time:.0f} 记录/秒")

if __name__ == "__main__":
    print(f'Study:{STUDY_ID} Processing has begun.' )
    main()
    print(f'Study:{STUDY_ID} Processing is over.' )
