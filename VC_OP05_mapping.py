"""
VAPORCONE 项目映射模块

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

import sys
import time
import traceback
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict
import numpy as np
import pandas as pd
from VC_BC03_fetchConfig import *
from VC_BC04_operateType import *

STEP_ID = 'OP05'
STEP_NAME = 'Mapping'

# 全局变量
actual_format_path = None

def vectorized_domain_mapping_ultra(domain_key, precomputed_rules, caseDict, codeDict, standard_fields, domainsSettingDict, sequenceDict, error_logs=None):
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
    - error_logs (list, optional): 错误收集列表

    返回:
    - DataFrame: 映射后的数据框
    """
    all_results = []
    seq_field = domain_key + VARIABLE_SEQSUFF

    unique_combinations = set()
    sorted_definition_items = sorted(precomputed_rules.items(), key=lambda x: x[0])

    for definition_row_num, rule_info in sorted_definition_items:
        combo_file_name = rule_info['combo_file_name']
        cycle_time = rule_info['cycle_time']
        field_rules = rule_info['field_rules']
        needed_columns = rule_info['needed_columns']

        print(f"处理 Definition {definition_row_num}: {combo_file_name}, cycles={cycle_time}")

        def log_error(message, stage=None, field=None, detail=None):
            if error_logs is None:
                return
            error_entry = {
                'domain': domain_key,
                'definition_row': definition_row_num,
                'combo_file_name': combo_file_name,
                'stage': stage,
                'field': field,
                'message': message
            }
            if detail:
                error_entry['detail'] = detail
            error_logs.append(error_entry)

        file_path = os.path.join(actual_format_path, f'{PREFIX_F}{combo_file_name}{EXTENSION}')
        be_converted_df = get_cached_csv(
            file_path,
            needed_columns,
            error_callback=log_error
        )

        if be_converted_df is None:
            log_error(message='读取源数据失败，已跳过该Definition', stage='数据准备')
            continue

        if be_converted_df.empty:
            continue

        try:
            be_converted_df = be_converted_df.copy()
            be_converted_df['USUBJID'] = be_converted_df['SUBJID'].map(caseDict)

            n_rows = len(be_converted_df)
            base_data = {
                'STUDYID': np.full(n_rows, STUDY_ID, dtype='object'),
                'DOMAIN': np.full(n_rows, domain_key, dtype='object'),
                'USUBJID': be_converted_df['USUBJID'].values,
                'SUBJID': be_converted_df['SUBJID'].values
            }

            for field in standard_fields:
                if field not in base_data:
                    base_data[field] = np.full(n_rows, MARK_BLANK, dtype='object')

            for cycle_idx in range(cycle_time):
                result_df = pd.DataFrame(base_data.copy())
                continue_flags = np.zeros(len(result_df), dtype=bool)

                for standard_field, field_rule in field_rules.items():
                    try:
                        result_df, field_continue_flags = vectorized_field_mapping(
                            result_df,
                            be_converted_df,
                            standard_field,
                            field_rule,
                            cycle_idx,
                            codeDict,
                            definition_row_num=definition_row_num,
                            error_callback=log_error
                        )
                        continue_flags |= field_continue_flags
                    except Exception as e:
                        log_error(
                            message=f"字段 {standard_field} 处理异常: {e}",
                            stage='字段映射',
                            field=standard_field,
                            detail=str(e)
                        )

                null_deletion_flags = np.zeros(len(result_df), dtype=bool)

                for standard_field, field_rule in field_rules.items():
                    if field_rule['ndkey'] and standard_field in result_df.columns:
                        non_empty = (result_df[standard_field] != '') & (result_df[standard_field].notna())
                        null_deletion_flags |= non_empty.values

                valid_rows = ~continue_flags & null_deletion_flags
                if np.any(valid_rows):
                    filtered_df = result_df[valid_rows].copy()

                    # 跨 cycle/definition 去重：用非序号字段组合做唯一键
                    dedup_cols = [f for f in standard_fields if f != seq_field]
                    # 先去除批内重复
                    filtered_df = filtered_df.drop_duplicates(subset=dedup_cols, keep='first')
                    # 再去除跨批重复
                    filtered_df['_dedup_key'] = filtered_df[dedup_cols].apply(lambda r: tuple(r), axis=1)
                    new_mask = ~filtered_df['_dedup_key'].isin(unique_combinations)
                    unique_combinations.update(filtered_df.loc[new_mask, '_dedup_key'])
                    filtered_df = filtered_df.loc[new_mask].drop(columns=['_dedup_key'])

                    if len(filtered_df) > 0:
                        cycle_dataset = filtered_df

                        if seq_field in cycle_dataset.columns and len(cycle_dataset) > 0:
                            if domain_key in domainsSettingDict:
                                sort_keys = domainsSettingDict[domain_key]
                            else:
                                sort_keys = [VARIABLE_USUBJID]

                            cycle_dataset = ultra_fast_sequence_generation(
                                cycle_dataset, seq_field, sort_keys, domain_key, sequenceDict
                            )
                        else:
                            if domain_key in domainsSettingDict:
                                sort_keys = domainsSettingDict[domain_key]
                            else:
                                sort_keys = [VARIABLE_USUBJID]

                            if len(cycle_dataset) > 0:
                                actual_sort_keys, epoch_col = prepare_epoch_sort(cycle_dataset, sort_keys)

                                available_sort_keys = [key for key in actual_sort_keys if key in cycle_dataset.columns]
                                if available_sort_keys:
                                    cycle_dataset = cycle_dataset.sort_values(available_sort_keys, kind='mergesort')

                                if epoch_col and epoch_col in cycle_dataset.columns:
                                    cycle_dataset = cycle_dataset.drop(epoch_col, axis=1)

                        all_results.append(cycle_dataset)
        except KeyError as e:
            log_error(
                message=f"Definition {definition_row_num} 关键列缺失: {e}",
                stage='数据准备',
                detail=str(e)
            )
        except Exception as e:
            log_error(
                message=f"Definition {definition_row_num} 处理失败: {e}",
                stage='Definition处理',
                detail=str(e)
            )

    if all_results:
        combined_df = pd.concat(all_results, ignore_index=True)
        return combined_df
    return pd.DataFrame()


def process_single_domain(args):
    """
    单个Domain的处理函数 - 用于并行处理

    参数:
    - args (tuple): 包含处理参数的元组

    返回:
    - tuple: (域名, 结果数据, 记录数, 错误列表)
    """
    domain_key, domain_param, definition_merge_rule, caseDict, codeDict, standard_fields, domainsSettingDict, format_path, initial_sequence_dict = args

    error_logs = []

    try:
        global actual_format_path, csv_cache
        actual_format_path = format_path
        csv_cache = {}

        sequenceDict = initial_sequence_dict.copy()
        for usubjid in sequenceDict:
            sequenceDict[usubjid] = sequenceDict[usubjid].copy()

        precomputed_rules = precompute_mapping_rules(domain_param, definition_merge_rule)
        print(f"Domain {domain_key} - 预计算完成，规则数: {len(precomputed_rules)}")

        domain_df = vectorized_domain_mapping_ultra(
            domain_key,
            precomputed_rules,
            caseDict,
            codeDict,
            standard_fields[domain_key],
            domainsSettingDict,
            sequenceDict,
            error_logs=error_logs
        )
        print(f"Domain {domain_key} - 映射完成，记录数: {len(domain_df) if not domain_df.empty else 0}")

        if not domain_df.empty:
            domain_df = domain_df[standard_fields[domain_key]]
            result_data = domain_df.to_dict('records')
        else:
            result_data = []

        return domain_key, result_data, len(result_data), error_logs

    except Exception as e:
        message = f"Domain {domain_key} 处理出错: {e}"
        print(message)
        error_logs.append({
            'domain': domain_key,
            'definition_row': None,
            'combo_file_name': None,
            'stage': 'Domain处理',
            'message': message,
            'detail': str(e)
        })
        return domain_key, [], 0, error_logs


def main():
    """
    主函数
    """
    print(f"开始SDTM映射处理")
    start_time = time.time()

    logger = create_logger(
        os.path.join(SPECIFIC_PATH, 'log_file.log'),
        log_level=logging.DEBUG
    )
    sdtm_dataset_path = create_directory(SDTMDATASET_PATH, SDTMDATASET_FILE_PATH)

    global actual_format_path
    actual_format_path = find_latest_timestamped_path(FORMAT_PATH, 'format_dataset')
    print(f'使用格式化数据路径: {actual_format_path}')

    try:
        workbook = load_workbook(filename=os.path.join(SPECIFIC_PATH, CONFIG_NAME))
        sheetSetting = getSheetSetting(workbook)

        caseDict = getCaseDict(workbook, sheetSetting)
        codeDict, _ = getCodeListInfo(workbook, sheetSetting)
        mappingDict, definition_merge_rule = getMapping(workbook, sheetSetting)
        domainsSettingDict = getDomainsSetting(workbook, sheetSetting)
    except MappingConfigurationError as config_error:
        print("\n映射配置读取失败:")
        print(f"- 原因: {config_error}")
        if getattr(config_error, 'sheet', None):
            print(f"- 工作表: {config_error.sheet}")
        if getattr(config_error, 'row', None) is not None:
            print(f"- Excel行号: {config_error.row}")
        if getattr(config_error, 'original_exception', None):
            original = config_error.original_exception
            print(f"- 原始异常: {type(original).__name__}: {original}")
        return False
    except Exception as exc:
        print("\n执行初始化配置时发生未捕获的错误:")
        print(f"- 原因: {exc}")
        traceback.print_exc()
        return False

    sequenceDict = {}
    for usubjid in caseDict.values():
        if usubjid not in sequenceDict:
            sequenceDict[usubjid] = {}
        for domain_name in STANDARD_FIELDS.keys():
            sequenceDict[usubjid][domain_name] = 1

    domain_args = []
    for domain_key, domain_param in mappingDict.items():
        args = (domain_key, domain_param, definition_merge_rule, caseDict,
                codeDict, STANDARD_FIELDS, domainsSettingDict, actual_format_path, sequenceDict)
        domain_args.append(args)

    domain_dataset = {}
    all_errors = []
    domain_summary = []  # 按 Domain 统计
    progress = ProgressReporter(total=len(domain_args), desc='Mapping')

    use_parallel = len(domain_args) >= 3

    if use_parallel:
        max_workers = min(mp.cpu_count() - 1, len(domain_args), 4)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_domain = {executor.submit(process_single_domain, args): args[0]
                                for args in domain_args}

            for future in as_completed(future_to_domain):
                domain_key = future_to_domain[future]
                try:
                    domain_key, result_data, record_count, domain_errors = future.result()
                    domain_dataset[domain_key] = result_data
                    all_errors.extend(domain_errors)
                    domain_summary.append({
                        'domain': domain_key, 'records': record_count,
                        'errors': len(domain_errors),
                    })
                except Exception as e:
                    message = f'Domain {domain_key} 处理失败: {e}'
                    domain_dataset[domain_key] = []
                    domain_summary.append({'domain': domain_key, 'records': 0, 'errors': 1})
                    all_errors.append({
                        'domain': domain_key,
                        'definition_row': None,
                        'combo_file_name': None,
                        'stage': 'Domain处理',
                        'message': message,
                        'detail': str(e)
                    })
                progress.update()
    else:
        for args in domain_args:
            try:
                domain_key, result_data, record_count, domain_errors = process_single_domain(args)
                domain_dataset[domain_key] = result_data
                all_errors.extend(domain_errors)
                domain_summary.append({
                    'domain': domain_key, 'records': record_count,
                    'errors': len(domain_errors),
                })
            except Exception as e:
                domain_key = args[0]
                message = f'Domain {domain_key} 处理失败: {e}'
                domain_dataset[domain_key] = []
                domain_summary.append({'domain': domain_key, 'records': 0, 'errors': 1})
                all_errors.append({
                    'domain': domain_key,
                    'definition_row': None,
                    'combo_file_name': None,
                    'stage': 'Domain处理',
                    'message': message,
                    'detail': str(e)
                })
            progress.update()

    progress.finish()

    print("开始保存SDTM数据集文件...")
    output_start = time.time()

    for domain, dataList in domain_dataset.items():
        if dataList:
            df = pd.DataFrame(dataList)
            header = STANDARD_FIELDS[domain]

            seq_field = domain + VARIABLE_SEQSUFF
            if seq_field in header and seq_field in df.columns:
                df[VARIABLE_USUBJID] = df[VARIABLE_USUBJID].astype('category')
                df[seq_field] = pd.to_numeric(df[seq_field], errors='coerce').fillna(0).astype('int32')
                df = df.sort_values([VARIABLE_USUBJID, seq_field])

            output_path = os.path.join(sdtm_dataset_path, f'{domain}{EXTENSION}')
            df[header].to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f'{domain} file saved - {len(dataList)} 条记录')

    output_time = time.time() - output_start
    total_time = time.time() - start_time

    total_records = sum(len(data) for data in domain_dataset.values())

    TW = [10, 10, 8]
    tcols = ['Domain', '记录数', '错误数']
    print_summary_header(f'处理摘要 - {STEP_NAME}')
    print(
        cjk_ljust(tcols[0], TW[0]) + ' '
        + ' '.join(cjk_rjust(c, w) for c, w in zip(tcols[1:], TW[1:]))
    )
    print_summary_sep()
    for s in sorted(domain_summary, key=lambda x: x['domain']):
        print(f'{s["domain"]:<{TW[0]}} {s["records"]:>{TW[1]}} {s["errors"]:>{TW[2]}}')
    print_summary_sep()
    print_summary_kv('处理Domain数量', len(domain_dataset))
    print_summary_kv('生成总记录数', total_records)
    print_summary_kv('总处理时间', f'{total_time:.2f}s')
    if total_time > 0:
        print_summary_kv('处理速度', f'{total_records/total_time:.0f} rec/s')

    if all_errors:
        print_summary_kv('错误/失败数量', len(all_errors))
        for err in all_errors:
            location_parts = []
            if err.get('definition_row'):
                location_parts.append(f"Definition {err['definition_row']}")
            if err.get('combo_file_name'):
                location_parts.append(err['combo_file_name'])
            location = ' / '.join(location_parts) if location_parts else '配置位置未知'
            stage = err.get('stage') or '处理阶段未知'
            field_info = f", 字段: {err['field']}" if err.get('field') else ''
            print(f"- Domain {err['domain']} | {stage} | {location}{field_info}")
            print(f"  {err['message']}")
            detail = err.get('detail')
            if detail and detail not in err['message']:
                print(f"  详情: {detail}")
    else:
        print_summary_kv('错误/失败数量', 0)

    return True


if __name__ == "__main__":
    print_step_header(STEP_ID, STEP_NAME)
    success = main()
    if success:
        print_step_footer(STEP_ID, STEP_NAME)
    else:
        print(f'[ERROR] {STEP_ID} {STEP_NAME} 处理中断')
        sys.exit(1)
