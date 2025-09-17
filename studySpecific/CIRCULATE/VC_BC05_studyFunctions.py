#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
该模块包含CIRCULATE研究特定的数据处理函数。
主要功能包括数据表合并、字段处理和各种数据集的特定处理逻辑。
"""

from VC_BC03_fetchConfig import *
from VC_BC04_operateType import *
import numpy as np
import pandas

def leftjoin(table1, table2):
    """
    执行两个数据表的左连接操作。
    
    参数:
        table1 (str): 左表的名称
        table2 (str): 右表的名称
        
    返回:
        pandas.DataFrame: 左连接后的数据表，所有值转换为字符串类型
    """
    # 获取格式化后的数据集
    format_dataset = getFormatDataset(table1, table2)
    
    # 获取左右表数据
    df_left = format_dataset[table1]
    df_right = format_dataset[table2]
    
    # 执行左连接并填充缺失值为空字符串
    merged_df = pandas.merge(df_left, df_right, how='left', on='SUBJID').fillna('')
    
    # 返回结果，所有列转换为字符串类型
    return merged_df.astype(str)

def tableMerge(sort_field, *tableList):
    """
    将多个数据表垂直拼接（上下拼接），并按指定字段排序。
    
    检查所有输入表的列名是否一致，如果一致则进行拼接。
    所有数据在处理过程中都会被转换为字符串类型。
    拼接后的数据会按照SUBJID和指定字段进行升序排序。
    
    参数:
        sort_field (str): 用于排序的字段名，将与SUBJID一起用于排序
        *tableList: 可变参数，包含所有需要拼接的表名
        
    返回:
        pandas.DataFrame: 拼接后并排序的数据表，所有值转换为字符串类型
        
    异常:
        ValueError: 当输入表的列名不一致时抛出
    """
    # 获取格式化数据集
    format_dataset = getFormatDataset(*tableList)
    merged_info = pandas.DataFrame()
    
    for table_index, file_name in enumerate(tableList):
        # 获取当前表的格式化数据
        file_filter_data = format_dataset[file_name].copy()
        
        # 如果结果表为空，直接赋值
        if merged_info.empty:
            merged_info = file_filter_data
        else:
            # 检查列名是否一致
            merged_columns = set(merged_info.columns)
            current_columns = set(file_filter_data.columns)
            
            if merged_columns != current_columns:
                raise ValueError(f"表 {file_name} 的列名与其他表不一致，无法拼接。")
            
            # 垂直拼接数据
            merged_info = pandas.concat([merged_info, file_filter_data], axis=0)
    
    # 按照SUBJID和指定字段进行升序排序
    merged_info = merged_info.sort_values(by=['SUBJID', sort_field], ascending=[True, True])
    
    # 返回拼接后的数据表，所有列转换为字符串类型
    return merged_info.astype(str)

def make_DMFrame():
    """
    创建并返回一个格式化的人口统计学数据框(Demographics DataFrame)。
    
    该函数通过处理和合并多个输入数据源，构建一个包含患者基本信息、
    入组信息、生存状态、治疗信息等的综合数据框。
    
    返回:
        pandas.DataFrame: 包含完整人口统计学信息的数据框，所有值转换为字符串类型
    """
    # 获取格式化数据集
    format_dataset = getFormatDataset('INEX', 'SS_A_ALL', 'CM_A_CH_PRP', 'PAT', 'TI_A[VER]')
    
    # 从数据集中提取各个数据框
    inex_df = format_dataset['INEX']  # 入组信息
    ss_a_all_df = format_dataset['SS_A_ALL']  # 生存状态
    cm_a_ch_prp_df = format_dataset['CM_A_CH_PRP']  # 治疗信息
    pat_df = format_dataset['PAT']  # 患者基本信息
    ti_a_ver_df = format_dataset['TI_A[VER]']  # 版本信息
    
    # 初始化主数据框，包含患者基本信息
    dmframe = pat_df[['SUBJID', 'INVESTIG', 'BRTHDAT', 'SEX', 'PATINT', 'Site_Object_SiteName']].copy()
    
    # 处理研究者(INVESTIG)数据，去掉括号和括号内的内容
    dmframe['INVESTIG'] = dmframe['INVESTIG'].str.replace(r'（.*?）', '', regex=True)
    
    # 处理入组(INEX)数据
    inex_subset = inex_df[['SUBJID', 'RFICDAT', 'REGDAT_A', 'COHORT', 'AGE', 'ICINVNAM', 'YEARS']].copy()
    dmframe = pandas.merge(dmframe, inex_subset, how='left', on='SUBJID').fillna('')
    
    # 处理生存状态(SS_A_ALL)数据
    ss_a_all_df = ss_a_all_df[['SUBJID', 'OUTDAT1', 'OUTDAT2', 'SURVSTAT','FUDAT','SSTIMEP']].astype(str)
    
    # 删除生存状态为空的行
    ss_a_all_df = ss_a_all_df[ss_a_all_df['SURVSTAT'] != '']
    
    # 创建结局日期(OUTDAT)字段，优先使用OUTDAT1，若为空则使用OUTDAT2
    ss_a_all_df['OUTDAT'] = ss_a_all_df['OUTDAT1'].where(
        ss_a_all_df['OUTDAT1'].notna() & (ss_a_all_df['OUTDAT1'] != ""),
        ss_a_all_df['OUTDAT2']
    )
    
    # 创建排序优先级：死亡记录优先，然后按结局日期降序
    ss_a_all_df['SURVSTAT_PRIORITY'] = ss_a_all_df['SURVSTAT'].apply(lambda x: 0 if x == 'DEAD' else 1)
    
    # 按受试者ID、生存状态优先级、结局日期排序
    ss_a_all_df = ss_a_all_df.sort_values(
        by=['SUBJID', 'SURVSTAT_PRIORITY', 'OUTDAT','FUDAT','SSTIMEP'],
        ascending=[True, True, False, False, False]
    )
    
    # 对每个受试者只保留第一条记录
    ss_a_all_df = ss_a_all_df.drop_duplicates(subset=['SUBJID'], keep='first')
    
    # 删除临时的优先级字段
    ss_a_all_df = ss_a_all_df.drop('SURVSTAT_PRIORITY', axis=1)
        
    # 合并生存状态数据到主数据框
    dmframe = pandas.merge(dmframe, ss_a_all_df, how='left', on='SUBJID').fillna('')
    
    # 处理治疗开始日期数据
    treatment_start_df = cm_a_ch_prp_df[['SUBJID', 'CHSPID', 'CMSTDCH']].copy()
    treatment_start_df = treatment_start_df.drop_duplicates(subset=['SUBJID', 'CHSPID', 'CMSTDCH'], keep='first')
    treatment_start_df = treatment_start_df[treatment_start_df['CHSPID'] == 'TREATMENT1']
    treatment_start_df = treatment_start_df[['SUBJID', 'CMSTDCH']].drop_duplicates(subset=['SUBJID'], keep='first')
    dmframe = pandas.merge(dmframe, treatment_start_df, how='left', on='SUBJID').fillna('')
    
    # 处理最后治疗结束日期数据
    treatment_end_df = cm_a_ch_prp_df[['SUBJID', 'CHSPID', 'CMENDCH']].copy()
    treatment_end_df = treatment_end_df.drop_duplicates(subset=['SUBJID', 'CHSPID', 'CMENDCH'], keep='first')
    treatment_end_df['CHSPID'] = treatment_end_df['CHSPID'].str.replace('TREATMENT', '').astype(int)
        
    # 按受试者ID和治疗ID排序（治疗ID降序，获取最后一次治疗）
    treatment_end_df = treatment_end_df.sort_values(
        by=['SUBJID', 'CHSPID'],
        ascending=[True, False]
    )
    
    # 对每个受试者只保留第一条记录
    treatment_end_df = treatment_end_df.drop_duplicates(subset=['SUBJID'], keep='first')
    treatment_end_df = treatment_end_df[['SUBJID', 'CMENDCH']]
    
    # 合并治疗结束日期到主数据框
    dmframe = pandas.merge(dmframe, treatment_end_df, how='left', on='SUBJID').fillna('')
    
    # 处理版本信息数据
    ti_a_ver_df = ti_a_ver_df[['SUBJID', 'CHKVALUE']].rename(columns={'CHKVALUE': 'PRTVER'})
    dmframe = pandas.merge(dmframe, ti_a_ver_df, how='left', on='SUBJID').fillna('')
    
    # 返回结果，所有列转换为字符串类型
    return dmframe.astype(str)

def get_updated_type_from_hierarchy(row, hierarchy):
    """
    根据类型的层级关系获取最细分的有效类型值。
    
    从最细分的类型字段开始检查，返回第一个有效值。
    有效值定义为既不为空也不为"UNKNOWN"的值。
    如果所有层级都没有有效值，则返回基础类型字段的值。
    
    参数:
        row (pandas.Series): DataFrame的一行数据，必须包含相关类型字段
        hierarchy (str): 选择使用的层级关系，必须是 "type", "typef" 或 "typer" 之一

    返回:
        str: 最细分的有效类型值，如果没有有效值则返回基础类型或空字符串
        
    异常:
        ValueError: 当hierarchy参数不是有效值时抛出
    """
    # 定义不同类型的层级关系映射（从最细分到最基础）
    hierarchies = {
        "type": ["TYPE213", "TYPE212", "TYPE2_1", "TYPE_2", "TYPE"],
        "typef": ["TYPE213F", "TYPE212F", "TYPE21F", "TYPE_F"],
        "typer": ["TYPE213R", "TYPE212R", "TYPE21R", "TYPE_R"]
    }
    
    # 验证hierarchy参数是否有效
    if hierarchy not in hierarchies:
        raise ValueError("hierarchy必须是'type', 'typef'或'typer'之一")
    
    # 获取指定层级关系的字段列表
    fields = hierarchies[hierarchy]
    base_type = fields[-1]  # 最基础的类型字段
    
    # 从最细分的类型字段开始，遍历层级直到找到有效值
    for field in fields:
        if field in row and row[field] not in ["", "UNKNOWN"]:
            return row[field]
    
    # 如果没有找到有效值，返回基础类型字段的值或空字符串
    return row.get(base_type, "")

def process_MH_A_PT():
    """
    处理MH_A_PT数据集的所有字段。
    
    该函数合并MH_A_PT和SUPR数据集，并处理多个字段，包括类型层级、
    淋巴结、血管、神经等相关字段，以及TNM分期相关字段。
    
    返回:
        pandas.DataFrame: 处理后的MH_A_PT数据集，所有值转换为字符串类型
    """
    # 获取MH_A_PT和SUPR数据集
    format_dataset = getFormatDataset('MH_A_PT', 'SUPR')
    
    mh_a_pt_df = format_dataset['MH_A_PT']
    supr_df = format_dataset['SUPR']
    
    # 提取SUPR中的SUBJID、SUDAT字段
    supr_df = supr_df[['SUBJID', 'SUDAT']].copy()
        
    # 添加空白列
    mh_a_pt_df['BLANK'] = ""
    
    # 合并数据集
    mh_a_pt_df = pandas.merge(mh_a_pt_df, supr_df, how='left', on='SUBJID').fillna('')
     
    # 使用层级关系更新TYPE字段
    mh_a_pt_df["TYPE"] = mh_a_pt_df.apply(
        lambda row: get_updated_type_from_hierarchy(row, "type"), axis=1
    )  
    
    # 处理淋巴结侵犯(LYYN)字段，优先使用LY_LY1
    mh_a_pt_df['LYYN'] = mh_a_pt_df['LY_LY1'].where(
        mh_a_pt_df['LY_LY1'].notna() & (mh_a_pt_df['LY_LY1'] != ""),
        mh_a_pt_df['LYYN']
    )
    
    # 处理血管侵犯(VYN)字段，优先使用V_V1
    mh_a_pt_df['VYN'] = mh_a_pt_df['V_V1'].where(
        mh_a_pt_df['V_V1'].notna() & (mh_a_pt_df['V_V1'] != ""),
        mh_a_pt_df['VYN']
    )
        
    # 处理宏观分类(MACROCL12)字段，优先使用MACROCL1
    mh_a_pt_df['MACROCL12'] = mh_a_pt_df['MACROCL1'].where(
        mh_a_pt_df['MACROCL1'].notna() & (mh_a_pt_df['MACROCL1'] != ""),
        mh_a_pt_df['MACROCL2']
    )
    
    # 处理神经侵犯(PNYN)字段，优先使用PN_PN1
    mh_a_pt_df['PNYN'] = mh_a_pt_df['PN_PN1'].where(
        mh_a_pt_df['PN_PN1'].notna() & (mh_a_pt_df['PN_PN1'] != ""),
        mh_a_pt_df['PNYN']
    )
    
    # 处理外科切缘(EXYN)字段，优先使用EX_Y
    mh_a_pt_df['EXYN'] = mh_a_pt_df['EX_Y'].where(
        mh_a_pt_df['EX_Y'].notna() & (mh_a_pt_df['EX_Y'] != ""),
        mh_a_pt_df['EXYN']
    )

    # 处理T分期(TSTAGE)字段，按优先级使用TSTAGET1、TSTAGET4
    mh_a_pt_df['TSTAGE'] = mh_a_pt_df['TSTAGET1'].where(
        mh_a_pt_df['TSTAGET1'].notna() & (mh_a_pt_df['TSTAGET1'] != ""),
        mh_a_pt_df['TSTAGET4'].where(
            mh_a_pt_df['TSTAGET4'].notna() & (mh_a_pt_df['TSTAGET4'] != ""),
            mh_a_pt_df['TSTAGE']
        )
    )
    
    # 处理N分期(NSTAGE)字段，按优先级使用NSTAGEN1、NSTAGEN2
    mh_a_pt_df['NSTAGE'] = mh_a_pt_df['NSTAGEN1'].where(
        mh_a_pt_df['NSTAGEN1'].notna() & (mh_a_pt_df['NSTAGEN1'] != ""),
        mh_a_pt_df['NSTAGEN2'].where(
            mh_a_pt_df['NSTAGEN2'].notna() & (mh_a_pt_df['NSTAGEN2'] != ""),
            mh_a_pt_df['NSTAGE']
        )
    )
    
    # 处理M分期(MSTAGE)字段，按优先级使用MSTAGM1C、MSTAGEM1
    mh_a_pt_df['MSTAGE'] = mh_a_pt_df['MSTAGM1C'].where(
        mh_a_pt_df['MSTAGM1C'].notna() & (mh_a_pt_df['MSTAGM1C'] != ""),
        mh_a_pt_df['MSTAGEM1'].where(
            mh_a_pt_df['MSTAGEM1'].notna() & (mh_a_pt_df['MSTAGEM1'] != ""),
            mh_a_pt_df['MSTAGE']
        )
    )
    
    # 处理病理T分期(PTNM_T)字段，优先使用PTNM_T4
    mh_a_pt_df['PTNM_T'] = mh_a_pt_df['PTNM_T4'].where(
        mh_a_pt_df['PTNM_T4'].notna() & (mh_a_pt_df['PTNM_T4'] != ""),
        mh_a_pt_df['PTNM_T']
    )
    
    # 处理病理N分期(PTNM_N)字段，按优先级使用PTNM_N1、PTNM_N2
    mh_a_pt_df['PTNM_N'] = mh_a_pt_df['PTNM_N1'].where(
        mh_a_pt_df['PTNM_N1'].notna() & (mh_a_pt_df['PTNM_N1'] != ""),
        mh_a_pt_df['PTNM_N2'].where(
            mh_a_pt_df['PTNM_N2'].notna() & (mh_a_pt_df['PTNM_N2'] != ""),
            mh_a_pt_df['PTNM_N']
        )
    )
    
    # 返回结果，所有列转换为字符串类型
    return mh_a_pt_df.astype(str)

def process_RGACOHD_MH():
    """
    处理RGACOHD_MH数据集的所有字段。
    
    该函数合并RGACOHD_MH和RGACOHD数据集，并处理多个字段，包括类型层级、
    淋巴结、血管、雌激素受体、神经等相关字段，以及TNM分期相关字段。
    
    返回:
        pandas.DataFrame: 处理后的RGACOHD_MH数据集，所有值转换为字符串类型
    """
    # 获取RGACOHD_MH和RGACOHD数据集
    format_dataset = getFormatDataset('RGACOHD_MH', 'RGACOHD')
    rgacohd_mh_df = format_dataset['RGACOHD_MH']
    rgacohd_df = format_dataset['RGACOHD']
    
    rgacohd_df = rgacohd_df[['SUBJID', 'SUDAT_D']].copy()
    
    # 添加空白列
    rgacohd_mh_df['BLANK'] = ""
       
    # 合并数据集
    rgacohd_mh_df = pandas.merge(rgacohd_mh_df, rgacohd_df, how='left', on='SUBJID').fillna('')

    # 使用层级关系更新TYPE字段
    rgacohd_mh_df["TYPE"] = rgacohd_mh_df.apply(
        lambda row: get_updated_type_from_hierarchy(row, "type"), axis=1
    )  

    # 处理淋巴结侵犯(LYYN)字段，优先使用LY_LY1
    rgacohd_mh_df['LYYN'] = rgacohd_mh_df['LY_LY1'].where(
        rgacohd_mh_df['LY_LY1'].notna() & (rgacohd_mh_df['LY_LY1'] != ""),
        rgacohd_mh_df['LYYN']
    )
    
    # 处理血管侵犯(VYN)字段，优先使用V_V1
    rgacohd_mh_df['VYN'] = rgacohd_mh_df['V_V1'].where(
        rgacohd_mh_df['V_V1'].notna() & (rgacohd_mh_df['V_V1'] != ""),
        rgacohd_mh_df['VYN']
    )
    
    # 处理雌激素受体(ERSTM)字段，优先使用ERSTM_ER
    rgacohd_mh_df['ERSTM'] = rgacohd_mh_df['ERSTM_ER'].where(
        rgacohd_mh_df['ERSTM_ER'].notna() & (rgacohd_mh_df['ERSTM_ER'] != ""),
        rgacohd_mh_df['ERSTM']
    )
    
    # 处理宏观分类(MACROCL12)字段，优先使用MACROCL1
    rgacohd_mh_df['MACROCL12'] = rgacohd_mh_df['MACROCL1'].where(
        rgacohd_mh_df['MACROCL1'].notna() & (rgacohd_mh_df['MACROCL1'] != ""),
        rgacohd_mh_df['MACROCL2']
    )
    
    # 处理神经侵犯(PNYN)字段，优先使用PN_PN1
    rgacohd_mh_df['PNYN'] = rgacohd_mh_df['PN_PN1'].where(
        rgacohd_mh_df['PN_PN1'].notna() & (rgacohd_mh_df['PN_PN1'] != ""),
        rgacohd_mh_df['PNYN']
    )

    # 处理T分期(TSTAGE)字段，按优先级使用TSTAGET1、TSTAGET4
    rgacohd_mh_df['TSTAGE'] = rgacohd_mh_df['TSTAGET1'].where(
        rgacohd_mh_df['TSTAGET1'].notna() & (rgacohd_mh_df['TSTAGET1'] != ""),
        rgacohd_mh_df['TSTAGET4'].where(
            rgacohd_mh_df['TSTAGET4'].notna() & (rgacohd_mh_df['TSTAGET4'] != ""),
            rgacohd_mh_df['TSTAGE']
        )
    )
    
    # 处理病理T分期(PTNM_T)字段，优先使用PTNM_T4
    rgacohd_mh_df['PTNM_T'] = rgacohd_mh_df['PTNM_T4'].where(
        rgacohd_mh_df['PTNM_T4'].notna() & (rgacohd_mh_df['PTNM_T4'] != ""),
        rgacohd_mh_df['PTNM_T']
    )
    
    # 返回结果，所有列转换为字符串类型
    return rgacohd_mh_df.astype(str)

def process_MH_A():
    """
    处理MH_A数据集的所有字段。
    
    该函数处理MH_A数据集中的类型层级字段和TNM分期相关字段，
    包括临床TNM分期和病理TNM分期。
    
    返回:
        pandas.DataFrame: 处理后的MH_A数据集，所有值转换为字符串类型
    """
    # 获取MH_A数据集
    format_dataset = getFormatDataset('MH_A')
    mh_a_df = format_dataset['MH_A']
    
    # 使用层级关系更新TYPE_F字段
    mh_a_df["TYPE_F"] = mh_a_df.apply(
        lambda row: get_updated_type_from_hierarchy(row, "typef"), axis=1
    ) 
    
    # 使用层级关系更新TYPE_R字段
    mh_a_df["TYPE_R"] = mh_a_df.apply(
        lambda row: get_updated_type_from_hierarchy(row, "typer"), axis=1
    ) 
    
    # 处理临床T分期(TNM_T)字段，优先使用TNM_T4
    mh_a_df['TNM_T'] = mh_a_df['TNM_T4'].where(
        mh_a_df['TNM_T4'].notna() & (mh_a_df['TNM_T4'] != ""),
        mh_a_df['TNM_T']
    )
    
    # 处理临床N分期(TNM_N)字段，按优先级使用TNM_N2、TNM_N1
    mh_a_df['TNM_N'] = mh_a_df['TNM_N2'].where(
        mh_a_df['TNM_N2'].notna() & (mh_a_df['TNM_N2'] != ""),
        mh_a_df['TNM_N1'].where(
            mh_a_df['TNM_N1'].notna() & (mh_a_df['TNM_N1'] != ""),
            mh_a_df['TNM_N']
        )
    )
    
    # 处理临床M分期(TNM_M)字段，优先使用TNM_M1
    mh_a_df['TNM_M'] = mh_a_df['TNM_M1'].where(
        mh_a_df['TNM_M1'].notna() & (mh_a_df['TNM_M1'] != ""),
        mh_a_df['TNM_M']
    )
    
    # 处理病理T分期(PTNM_T)字段，优先使用PTNM_T4
    mh_a_df['PTNM_T'] = mh_a_df['PTNM_T4'].where(
        mh_a_df['PTNM_T4'].notna() & (mh_a_df['PTNM_T4'] != ""),
        mh_a_df['PTNM_T']
    )
    
    # 处理病理N分期(PTNM_N)字段，按优先级使用PTNM_N1、PTNM_N2
    mh_a_df['PTNM_N'] = mh_a_df['PTNM_N1'].where(
        mh_a_df['PTNM_N1'].notna() & (mh_a_df['PTNM_N1'] != ""),
        mh_a_df['PTNM_N2'].where(
            mh_a_df['PTNM_N2'].notna() & (mh_a_df['PTNM_N2'] != ""),
            mh_a_df['PTNM_N']
        )
    )
    
    # 处理T分期(TSTAGE)字段，按优先级使用TSTAGET1、TSTAGET4
    mh_a_df['TSTAGE'] = mh_a_df['TSTAGET1'].where(
        mh_a_df['TSTAGET1'].notna() & (mh_a_df['TSTAGET1'] != ""),
        mh_a_df['TSTAGET4'].where(
            mh_a_df['TSTAGET4'].notna() & (mh_a_df['TSTAGET4'] != ""),
            mh_a_df['TSTAGE']
        )
    )
    
    # 处理N分期(NSTAGE)字段，按优先级使用NSTAGEN1、NSTAGEN2
    mh_a_df['NSTAGE'] = mh_a_df['NSTAGEN1'].where(
        mh_a_df['NSTAGEN1'].notna() & (mh_a_df['NSTAGEN1'] != ""),
        mh_a_df['NSTAGEN2'].where(
            mh_a_df['NSTAGEN2'].notna() & (mh_a_df['NSTAGEN2'] != ""),
            mh_a_df['NSTAGE']
        )
    )
    
    # 处理M分期(MSTAGE)字段，按优先级使用MSTAGM1C、MSTAGEM1
    mh_a_df['MSTAGE'] = mh_a_df['MSTAGM1C'].where(
        mh_a_df['MSTAGM1C'].notna() & (mh_a_df['MSTAGM1C'] != ""),
        mh_a_df['MSTAGEM1'].where(
            mh_a_df['MSTAGEM1'].notna() & (mh_a_df['MSTAGEM1'] != ""),
            mh_a_df['MSTAGE']
        )
    )
    
    # 返回结果，所有列转换为字符串类型
    return mh_a_df.astype(str)

def process_MH_A_RC():
    """
    处理MH_A_RC数据集的所有字段。
    
    该函数合并MH_A_RC和SUPR数据集，并处理类型层级字段。
    
    返回:
        pandas.DataFrame: 处理后的MH_A_RC数据集，所有值转换为字符串类型
    """
    # 获取MH_A_RC数据集
    format_dataset = getFormatDataset('MH_A_RC','SUPR_MR_FULL')
    mh_a_rc_df = format_dataset['MH_A_RC']
    supr_mr_full_df = format_dataset['SUPR_MR_FULL']
    
    # 提取 supr_mr_full_df 中的SUBJID、DAT字段，并对两个字段去重
    supr_mr_full_df = supr_mr_full_df[['SUBJID', 'DAT']].copy()
    supr_mr_full_df = supr_mr_full_df.drop_duplicates(subset=['SUBJID', 'DAT'], keep='first')
    
    # 合并数据集
    mh_a_rc_df = pandas.merge(mh_a_rc_df, supr_mr_full_df, how='left', on='SUBJID').fillna('')
    
    # 使用层级关系更新TYPE字段
    mh_a_rc_df["TYPE"] = mh_a_rc_df.apply(
        lambda row: get_updated_type_from_hierarchy(row, "type"), axis=1
    ) 
    
    # 返回结果，所有列转换为字符串类型
    return mh_a_rc_df.astype(str)  

def process_CO():
    """
    处理CO数据集的所有字段。
    
    该函数处理CO数据集中的临床和病理字段，将多个相关字段合并为汇总字段，
    并格式化转移器官数量字段。
    
    返回:
        pandas.DataFrame: 处理后的CO数据集，所有值转换为字符串类型
    """
    # 获取CO数据集
    format_dataset = getFormatDataset('CO')
    co_df = format_dataset['CO']
    
    # 定义临床和病理字段集合
    clinical_columns = ['COCNCLV', 'COCNCLNG', 'COCNCPRT', 'COCNCDLY', 'COCNCOTH']
    pathological_columns = ['COCNPLVR', 'COCNPLNG', 'COCNPPRT', 'COCNPDLY', 'COCNPOTH']
    
    # 处理临床字段，生成汇总字段COCNC
    def generate_clinical(row):
        # 筛选非空值
        values = [
            str(row[col]).strip() 
            for col in clinical_columns 
            if pandas.notnull(row[col]) and row[col] != ''
        ]
        if values:  # 如果有非空值
            return 'CLINICAL: ' + ', '.join(values)
        return ''  # 如果全为空，则返回空字符串
    
    co_df['COCNC'] = co_df.apply(generate_clinical, axis=1)
    
    # 处理病理字段，生成汇总字段COCNP
    def generate_pathological(row):
        # 筛选非空值
        values = [
            str(row[col]).strip() 
            for col in pathological_columns 
            if pandas.notnull(row[col]) and row[col] != ''
        ]
        if values:  # 如果有非空值
            return 'PATHOLOGICAL: ' + ', '.join(values)
        return ''  # 如果全为空，则返回空字符串
    
    co_df['COCNP'] = co_df.apply(generate_pathological, axis=1)
    
    # 处理转移器官数量字段COCNEMON，格式化为描述性文本
    co_df['COCNEMON'] = co_df['COCNEMON'].apply(
        lambda x: f'Number of metastatic organs＝{x}' if pandas.notnull(x) and x != '' else ''
    )
    
    # 返回结果，所有列转换为字符串类型
    return co_df.astype(str)

def get_DD_from_SS_ALL():
    """
    从SS_A_ALL数据集获取死亡数据。
    
    该函数从SS_A_ALL数据集中提取与死亡相关的字段，并进行处理：
    1. 提取SUBJID、SURVSTAT、OUTDAT1、OUTDAT2、PRCDTH、PRCDTHDE字段
    2. 过滤掉SURVSTAT为空的记录
    3. 合并OUTDAT1和OUTDAT2为OUTDAT字段
    4. 按照死亡状态优先级和日期排序
    5. 为每个受试者保留一条记录
    
    返回:
        pandas.DataFrame: 处理后的死亡数据集，所有值转换为字符串类型
    """
    # 获取SS_A_ALL数据集
    format_dataset = getFormatDataset('SS_A_ALL')
    ss_a_all_dd_df = format_dataset['SS_A_ALL']
    
    # 提取指定字段并转换为字符串
    ss_a_all_dd_df = ss_a_all_dd_df[
        ['SUBJID', 'SURVSTAT', 'OUTDAT1', 'OUTDAT2', 'PRCDTH', 'PRCDTHDE','FUDAT', 'SSTIMEP']
    ].astype(str)
    
    # 删除SURVSTAT为空的行
    ss_a_all_dd_df = ss_a_all_dd_df[ss_a_all_dd_df['SURVSTAT'] != '']
    
    # 新建OUTDAT字段，优先使用OUTDAT1
    ss_a_all_dd_df['OUTDAT'] = ss_a_all_dd_df['OUTDAT1'].where(
        ss_a_all_dd_df['OUTDAT1'].notna() & (ss_a_all_dd_df['OUTDAT1'] != ""),
        ss_a_all_dd_df['OUTDAT2']
    )
    
    # 添加优先级字段，死亡状态优先级更高
    ss_a_all_dd_df['SURVSTAT_PRIORITY'] = ss_a_all_dd_df['SURVSTAT'].apply(
        lambda x: 0 if x == 'DEAD' else 1
    )
    
    # 按照受试者ID、状态优先级和日期排序
    ss_a_all_dd_df = ss_a_all_dd_df.sort_values(
        by=['SUBJID', 'SURVSTAT_PRIORITY', 'OUTDAT','FUDAT','SSTIMEP'],
        ascending=[True, True, False, False, False]
    )
    
    # 对每个SUBJID只保留第一条记录，使用drop_duplicates保持行的完整性
    ss_a_all_dd_df = ss_a_all_dd_df.drop_duplicates(subset=['SUBJID'], keep='first')
    
    # 删除临时使用的SURVSTAT_PRIORITY字段
    ss_a_all_dd_df = ss_a_all_dd_df.drop(columns=['SURVSTAT_PRIORITY'])
    
    # 返回结果，所有列转换为字符串类型
    return ss_a_all_dd_df.astype(str)
    
def get_GF_from_LB_A_BM():
    """
    从LB_A_BM数据集获取基因检测结果并进行处理。
    
    该函数处理LB_A_BM数据集中的基因检测结果，主要功能包括：
    1. 对每个受试者的每种检测类型，如果全部为NEGATIVE则只保留一条记录
    2. 处理KRAS和NRAS突变，更新RAS状态
    3. 根据检测值添加分类字段(CLASSIFICATION)
    
    返回:
        pandas.DataFrame: 处理后的基因检测数据集，所有值转换为字符串类型
    """
    # 获取LB_A_BM数据集
    format_dataset = getFormatDataset('LB_A_BM[BM]')
    lb_a_bm_df = format_dataset['LB_A_BM[BM]']
    
    def process_group(group):
        """处理每个分组的数据，保留非野生型记录或仅一条野生型记录"""
        if (group['CHKVALUE'] == 'NEGATIVE').all():
            return group.head(1)  # 如果全部为NEGATIVE，只保留第一条记录
        else:
            return group[group['CHKVALUE'] != 'NEGATIVE']  # 否则保留所有非NEGATIVE记录

    # 按受试者ID和检测类型分组处理
    # 使用 pandas.concat 来避免 apply 的 FutureWarning
    grouped_results = []
    for (subjid, chktype), group in lb_a_bm_df.groupby(['SUBJID', 'CHKTYPE']):
        processed_group = process_group(group)
        grouped_results.append(processed_group)
    
    processed_df = pandas.concat(grouped_results, ignore_index=True)
    
    # 新建字段 ORRES，内容和 CHKVALUE 一致
    processed_df['ORRES'] = processed_df['CHKVALUE']
    
    # 重置索引以便后续操作
    processed_df = processed_df.reset_index(drop=True)
    
    # 按受试者ID分组，处理RAS状态更新逻辑
    for subjid in processed_df['SUBJID'].unique():
        # 获取当前受试者的所有记录
        subjid_mask = processed_df['SUBJID'] == subjid
        subjid_data = processed_df[subjid_mask]
        
        # 检查NRAS和KRAS是否有NEGATIVE值
        nras_positive = any(
            (subjid_data['CHKTYPE'] == 'NRAS') & (subjid_data['ORRES'] != 'NEGATIVE')
        )
        kras_positive = any(
            (subjid_data['CHKTYPE'] == 'KRAS') & (subjid_data['ORRES'] != 'NEGATIVE')
        )
        
        # 如果NRAS或KRAS任一不为NEGATIVE，则将该受试者的RAS设置为POSITIVE
        if nras_positive or kras_positive:
            ras_mask = subjid_mask & (processed_df['CHKTYPE'] == 'RAS')
            processed_df.loc[ras_mask, 'ORRES'] = 'POSITIVE'
        
    # 将 ORRES 字段中为 POSITIVE 和 NEGATIVE 的数据赋值给新建字段 DETECTION
    processed_df['DETECTION'] = processed_df['ORRES'].where(
        processed_df['ORRES'].isin(['POSITIVE', 'NEGATIVE']), ''
    )
        
    # 将 ORRES 字段中不为 POSITIVE 和 NEGATIVE 的数据赋值给新建字段 PREDICTED
    processed_df['PREDICTED'] = processed_df['ORRES'].where(
        ~processed_df['ORRES'].isin(['POSITIVE', 'NEGATIVE']), ''
    )
    
    # 将 PREDICTED 字段中的数据赋值给新建字段 RESCAT ，将 RESCAT 字段中为 OTHER,"",MSI-H 变为 "" ，其余都变为 POSITIVE
    processed_df['RESCAT'] = processed_df['PREDICTED'].apply(
        lambda x: 'POSITIVE' if x != 'OTHER' and x != '' and x != 'MSI-H' else ''
    )
          
    # 返回结果，所有列转换为字符串类型
    return processed_df.astype(str)

def process_INEX():
    """
    处理INEX数据集并合并RGACOHB数据集的相关字段。
    
    该函数从INEX和RGACOHB数据集中提取数据，并进行合并处理：
    1. 获取INEX和RGACOHB数据集
    2. 从RGACOHB中提取SUBJID、ARMCOHBX、ARMCOHBT字段
    3. 将两个数据集按SUBJID外连接合并
    
    返回:
        pandas.DataFrame: 合并后的数据集，所有值转换为字符串类型
    """
    # 获取INEX和RGACOHB数据集
    format_dataset = getFormatDataset('INEX', 'RGACOHB')
    inex_df = format_dataset['INEX']
    rgacohb_df = format_dataset['RGACOHB']
    
    # 提取RGACOHB中的SUBJID、ARMCOHBX、ARMCOHBT字段
    rgacohb_df = rgacohb_df[['SUBJID', 'ARMCOHBX', 'ARMCOHBT']].copy()
    
    # 合并INEX和RGACOHB数据集，使用外连接确保保留所有记录
    merged_df = pandas.merge(
        inex_df, rgacohb_df, how='outer', on='SUBJID'
    ).fillna('')
    
    # 返回结果，所有列转换为字符串类型
    return merged_df.astype(str)

def get_CE():
    """
    获取并处理CE数据集，将宽格式数据转换为长格式。
    
    该函数从CE和CE_OTH数据集中提取数据，并进行处理：
    1. 合并CE和CE_OTH数据集
    2. 将宽格式数据(CETERM1-20和CETOXG1-20)转换为长格式
    3. 处理CETERMOT字段，仅在CETERM20有值时保留
    
    返回:
        pandas.DataFrame: 转换为长格式的CE数据集，所有值转换为字符串类型
    """
    # 获取CE和CE_OTH数据集
    format_dataset = getFormatDataset('CE', 'CE_OTH')
    ce_df = format_dataset['CE']
    ce_oth_df = format_dataset['CE_OTH']
   
    # 合并数据集并填充空值
    merged_df = pandas.merge(ce_df, ce_oth_df, how='left', on='SUBJID').fillna('')

    # 确定ID变量，这些变量在转换后保持不变
    id_vars = ['SUBJID', 'CEYN']
    # CETERMOT需要特殊处理，但我们先将其作为ID变量
    if 'CETERMOT' in merged_df.columns:
        id_vars.append('CETERMOT')
    else:
        # 如果CETERMOT列不存在，创建一个空列以避免错误
        merged_df['CETERMOT'] = ''
        id_vars.append('CETERMOT')

    # 使用 pandas.wide_to_long 高效地将宽表转换为长表
    # stubnames 定义了需要转换的列的前缀
    try:
        long_df = pandas.wide_to_long(
            merged_df,
            stubnames=['CETERM', 'CETOXG'],
            i=id_vars,
            j='_event_num',  # 临时列，用于存储事件编号 (1-20)
            sep='',
            suffix='\\d+'
        ).reset_index()
    except ValueError:
        # 如果输入数据为空或不包含任何CETERM/CETOXG列，则返回一个空的DataFrame
        return pandas.DataFrame(columns=['SUBJID', 'CEYN', 'CETERM', 'CETOXG', 'CETERMOT'])

    # 清理数据：删除 CETERM 为空或'nan'的行
    long_df.dropna(subset=['CETERM'], inplace=True)
    long_df = long_df[~long_df['CETERM'].astype(str).str.strip().isin(['', 'nan'])]

    # 应用 CETERMOT 的特殊逻辑：仅在事件编号为20时保留其值
    long_df['CETERMOT'] = np.where(long_df['_event_num'] == 20, long_df['CETERMOT'], '')

    # 删除不再需要的临时事件编号列，并选择最终需要的列
    result_df = long_df.drop(columns=['_event_num'])[['SUBJID', 'CEYN', 'CETERM', 'CETOXG', 'CETERMOT']]
    
    # 返回结果，所有列转换为字符串类型
    return result_df.astype(str)

def process_SUPR_SMPL():
    # 获取 SUPR_SMPL 和 SUPR 数据集
    format_dataset = getFormatDataset('SUPR_SMPL', 'SUPR')
    supr_smp_df = format_dataset['SUPR_SMPL']
    supr_df = format_dataset['SUPR']
    
    # 提取SUPR中的SUBJID、SUDAT字段
    supr_df = supr_df[['SUBJID', 'SUDAT']].copy()

    # 合并数据集
    merged_df = pandas.merge(supr_smp_df, supr_df, how='left', on='SUBJID').fillna('')
    
    # 生成一个新字段DAT，如果 SUTTDATS 为TISSUE COLLECTION DATE IS SAME AS THE SURGERY DATE，则 DAT 的值为 SUPR 的 SUDAT 的值，否则 DAT 的值为 SUPR_SMPL 的 SUTTDAT 的值
    merged_df['DAT'] = merged_df['SUDAT'].where(merged_df['SUTTDATS'] == 'TISSUE COLLECTION DATE IS SAME AS THE SURGERY DATE', merged_df['SUTTDAT'])

    # 对DAT 字段的数据(一部分是yyyy/mm/dd，一部分是yyyy-mm-dd)进行ISO 8601 格式化(将/变为-，对mm和dd进行补零)
    merged_df['DAT'] = merged_df['DAT'].apply(lambda x: datetime.strptime(x, '%Y/%m/%d').strftime('%Y-%m-%d') if '/' in x else x)

    # 返回结果，所有列转换为字符串类型
    return merged_df.astype(str)

def process_SUPR_MR():
    # 获取 SUPR_MR 和 SUPR 数据集
    format_dataset = getFormatDataset('SUPR_MR[SUPR_MR]', 'SUPR')
    supr_mr_df = format_dataset['SUPR_MR[SUPR_MR]']
    supr_df = format_dataset['SUPR']
    
    # 提取SUPR中的SUBJID、SUDAT字段
    supr_df = supr_df[['SUBJID', 'SUDAT']].copy()

    # 合并数据集
    merged_df = pandas.merge(supr_mr_df, supr_df, how='left', on='SUBJID').fillna('')

    # 生成一个新字段DAT，如果SUDATS 的值为SAME DAY AS PRIMARY RESECTION ，则DAT的值为 SUPR 的 SUDAT_y 的值，否则DAT的值为 SUPR_MR 的 SUDAT_x 的值
    merged_df['DAT'] = merged_df['SUDAT_y'].where(merged_df['SUDATS'] == 'SAME DAY AS PRIMARY RESECTION', merged_df['SUDAT_x'])

    # 对DAT 字段的数据(一部分是yyyy/mm/dd，一部分是yyyy-mm-dd)进行ISO 8601 格式化(将/变为-，对mm和dd进行补零)
    merged_df['DAT'] = merged_df['DAT'].apply(lambda x: datetime.strptime(x, '%Y/%m/%d').strftime('%Y-%m-%d') if '/' in x else x)

    # 返回结果，所有列转换为字符串类型
    return merged_df.astype(str)