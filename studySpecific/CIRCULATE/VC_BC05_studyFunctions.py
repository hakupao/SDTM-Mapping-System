from VC_BC03_fetchConfig import *
from VC_BC04_operateType import *
import numpy as np

def leftjoin(table1, table2):
    
    # 获取格式化后的数据集
    format_dataset = getFormatDataset(table1, table2)
    # 获取table1的数据集
    df_left = format_dataset[table1] 
    # 获取table2的数据集
    df_right = format_dataset[table2]
    
    # 将两个数据集进行左连接，并填充缺失值为空字符串
    merged_df = pandas.merge(df_left, df_right, how='left', on='SUBJID').fillna('')
    
    return merged_df.astype(str)

def tableMerge(*tableList):
    """
    功能：检测输入的表的列名是否完全一致，如果一致，则上下拼接。
    处理过程中所有数据都按照字符串处理。
    """
    # 格式化数据集
    format_dataset = getFormatDataset(*tableList)
    merged_info = pandas.DataFrame()
    
    for file_name in tableList:
        # 获取当前表的格式化数据
        file_filter_data = format_dataset[file_name]
        
        # 如果 merged_info 为空，直接赋值
        if merged_info.empty:
            merged_info = file_filter_data
        else:
            # 检查列名是否一致
            if set(merged_info.columns) != set(file_filter_data.columns):
                raise ValueError(f"表 {file_name} 的列名与其他表不一致，无法拼接。")
            
            # 上下拼接数据
            merged_info = pandas.concat([merged_info, file_filter_data], axis=0)
    
    # 返回拼接后的 DataFrame，所有数据类型转换为字符串
    return merged_info.astype(str)

def make_DMFrame():
    """
    创建并返回一个格式化的 DataFrame (dmframe)，通过处理和合并多个输入数据源。
    """

    # 获取格式化数据集
    format_dataset = getFormatDataset('INEX', 'SS_A_ALL', 'CM_A_CH_PRP', 'PAT', 'TI_A[VER]')
    
    # 从数据集中提取 DataFrame
    inex_df = format_dataset['INEX']
    ss_a_all_df = format_dataset['SS_A_ALL']
    cm_a_ch_prp_df = format_dataset['CM_A_CH_PRP']
    pat_df = format_dataset['PAT']
    ti_a_ver_df = format_dataset['TI_A[VER]']
    
    # 初始化主 DataFrame，包含患者信息
    dmframe = pat_df[['SUBJID', 'INVESTIG', 'BRTHDAT', 'SEX', 'PATINT']]
    
    # 处理 INVESTIG 字段
    def split_investig(row):
        investig = row['INVESTIG']
        if not investig:  # 如果 INVESTIG 为空
            return '', ''
        
        # 使用全角括号分割字符串
        parts = investig.split('（')
        if len(parts) == 2:  # 如果有括号
            doctor = parts[0].strip()
            hospital = parts[1].replace('）', '').strip()
            return doctor, hospital
        return investig, ''  # 如果没有括号，医院名为空
    
    # 应用拆分函数
    dmframe[['INVESTIG', 'SITEID']] = dmframe.apply(split_investig, axis=1, result_type='expand')
    
    
    # 处理 INEX 数据
    INEX_df = inex_df[['SUBJID', 'RFICDAT', 'REGDAT_A', 'COHORT', 'AGE', 'ICINVNAM','YEARS']].copy()
    dmframe = pandas.merge(dmframe, INEX_df, how='left', on='SUBJID').fillna('')
    
    # 处理 SS_A_ALL 数据
    ss_a_all_df = ss_a_all_df[['SUBJID', 'OUTDAT1', 'OUTDAT2', 'SURVSTAT']].astype(str)
    
    # 删除SURVSTAT为空的行
    ss_a_all_df = ss_a_all_df[ss_a_all_df['SURVSTAT'] != '']
    
    
    # 创建RFENDTC字段
    ss_a_all_df['RFENDTC'] = ss_a_all_df['OUTDAT1'].where(
        ss_a_all_df['OUTDAT1'].notna() & (ss_a_all_df['OUTDAT1'] != ""),
        ss_a_all_df['OUTDAT2']
    )
    
    #创建OUTDAT字段，等于RFENDTC
    ss_a_all_df['OUTDAT'] = ss_a_all_df['RFENDTC']
    
    # 将OUTDAT为“”的行替换为NA
    ss_a_all_df['OUTDAT'] = ss_a_all_df['OUTDAT'].replace('', np.nan)
    
    # 按SUBJID顺序，OUTDAT倒序排列数据。如果OUTDAT为""，则排在最前面
    ss_a_all_df = ss_a_all_df.sort_values(
        by=['SUBJID', 'OUTDAT'],
        ascending=[True, False],
        na_position='first'  # 将空值排在最前面
    )
    
    # 对每个SUBJID只保留第一条记录，使用drop_duplicates保持行的完整性
    ss_a_all_df = ss_a_all_df.drop_duplicates(subset=['SUBJID'], keep='first')
        
    # 合并到dmframe
    dmframe = pandas.merge(dmframe, ss_a_all_df, how='left', on='SUBJID').fillna('')
    
    # 处理 CM_A_CH_PRP 数据（治疗开始日期）
    RFXSTDTC_df = cm_a_ch_prp_df[['SUBJID', 'CHSPID', 'CMSTDCH']].copy()
    RFXSTDTC_df = RFXSTDTC_df.drop_duplicates(subset=['SUBJID', 'CHSPID', 'CMSTDCH'], keep='first')
    RFXSTDTC_df = RFXSTDTC_df[RFXSTDTC_df['CHSPID'] == 'TREATMENT1']
    RFXSTDTC_df = RFXSTDTC_df[['SUBJID', 'CMSTDCH']].drop_duplicates(subset=['SUBJID'], keep='first')
    dmframe = pandas.merge(dmframe, RFXSTDTC_df, how='left', on='SUBJID').fillna('')
    
    # 处理 CM_A_CH_PRP 数据（最后治疗结束日期）
    RFXENDTC_df = cm_a_ch_prp_df[['SUBJID', 'CHSPID', 'CMENDCH']].copy()
    RFXENDTC_df = RFXENDTC_df.drop_duplicates(subset=['SUBJID', 'CHSPID', 'CMENDCH'], keep='first')
    RFXENDTC_df['CHSPID'] = RFXENDTC_df['CHSPID'].str.replace('TREATMENT', '').astype(int)
        
    # 按SUBJID和CHSPID排序
    RFXENDTC_df = RFXENDTC_df.sort_values(
        by=['SUBJID', 'CHSPID'],
        ascending=[True, False]
    )
    
    # 对每个SUBJID只保留第一条记录，使用drop_duplicates保持行的完整性
    RFXENDTC_df = RFXENDTC_df.drop_duplicates(subset=['SUBJID'], keep='first')
    
    RFXENDTC_df = RFXENDTC_df[['SUBJID', 'CMENDCH']]
    
    dmframe = pandas.merge(dmframe, RFXENDTC_df, how='left', on='SUBJID').fillna('')
    
    # 处理 TI_A[VER] 数据
    ti_a_ver_df = ti_a_ver_df[['SUBJID', 'CHKVALUE']].rename(columns={'CHKVALUE': 'PRTVER'})
    dmframe = pandas.merge(dmframe, ti_a_ver_df, how='left', on='SUBJID').fillna('')
    
    # 确保所有字段都是字符串类型
    return dmframe.astype(str)

def get_updated_type_from_hierarchy(row, hierarchy):
    """
    根据类型的层级关系获取最细分的有效类型值。
    有效值定义为既不为空也不为"UNKNOWN"的值。
    
    Args:
        row (Series): DataFrame的一行数据，必须包含所有类型字段
        hierarchy (str): 选择使用的层级关系。必须是 "type", "typef" 或 "typer" 之一

    Returns:
        str: 最细分的有效类型值
        
    Raises:
        ValueError: 如果 hierarchy 参数不是有效值
    """
    # 层级关系映射
    hierarchies = {
        "type": ["TYPE213", "TYPE212", "TYPE2_1", "TYPE_2", "TYPE"],
        "typef": ["TYPE213F", "TYPE212F", "TYPE21F", "TYPE_F"],
        "typer": ["TYPE213R", "TYPE212R", "TYPE21R", "TYPE_R"]
    }
    
    # 验证 hierarchy 参数
    if hierarchy not in hierarchies:
        raise ValueError("hierarchy 必须是 'type', 'typef' 或 'typer' 之一")
    
    # 获取层级关系
    fields = hierarchies[hierarchy]
    base_type = fields[-1]
    
    # 遍历层级直到找到有效值
    for field in fields:
        if field in row and row[field] not in ["", "UNKNOWN"]:
            return row[field]
    
    # 返回最基础的类型值
    return row.get(base_type, "")

def process_MH_A_PT():
    """
    处理MH_A_PT数据集的所有字段
    """
    # 获取MH_A_PT数据集
    format_dataset = getFormatDataset('MH_A_PT','SUPR')
    MH_A_PT_df = format_dataset['MH_A_PT']
    SUPR_df = format_dataset['SUPR']
        
    # 添加一列BLANK，值为空字符串
    MH_A_PT_df['BLANK'] = ""
    
    MH_A_PT_df = pandas.merge(MH_A_PT_df, SUPR_df, how='left', on='SUBJID').fillna('')
     
    # 覆盖原有的 TYPE 字段，使用提取出来的公共函数
    MH_A_PT_df["TYPE"] = MH_A_PT_df.apply(lambda row: get_updated_type_from_hierarchy(row, "type"), axis=1)  
    
    MH_A_PT_df['LYYN'] = MH_A_PT_df['LY_LY1'].where(
        MH_A_PT_df['LY_LY1'].notna() & (MH_A_PT_df['LY_LY1'] != ""),
        MH_A_PT_df['LYYN']
    )
    
    MH_A_PT_df['VYN'] = MH_A_PT_df['V_V1'].where(
        MH_A_PT_df['V_V1'].notna() & (MH_A_PT_df['V_V1'] != ""),
        MH_A_PT_df['VYN']
    )
        
    MH_A_PT_df['MACROCL12'] = MH_A_PT_df['MACROCL1'].where(
        MH_A_PT_df['MACROCL1'].notna() & (MH_A_PT_df['MACROCL1'] != ""),
        MH_A_PT_df['MACROCL2']
    )
    
    MH_A_PT_df['PNYN'] = MH_A_PT_df['PN_PN1'].where(
        MH_A_PT_df['PN_PN1'].notna() & (MH_A_PT_df['PN_PN1'] != ""),
        MH_A_PT_df['PNYN']
    )
    
    MH_A_PT_df['EXYN'] = MH_A_PT_df['EX_Y'].where(
        MH_A_PT_df['EX_Y'].notna() & (MH_A_PT_df['EX_Y'] != ""),
        MH_A_PT_df['EXYN']
    )

    MH_A_PT_df['TSTAGE'] = MH_A_PT_df['TSTAGET1'].where(
        MH_A_PT_df['TSTAGET1'].notna() & (MH_A_PT_df['TSTAGET1'] != ""),
        MH_A_PT_df['TSTAGET4'].where(
            MH_A_PT_df['TSTAGET4'].notna() & (MH_A_PT_df['TSTAGET4'] != ""),
            MH_A_PT_df['TSTAGE']
        )
    )
    
    MH_A_PT_df['NSTAGE'] = MH_A_PT_df['NSTAGEN1'].where(
        MH_A_PT_df['NSTAGEN1'].notna() & (MH_A_PT_df['NSTAGEN1'] != ""),
        MH_A_PT_df['NSTAGEN2'].where(
            MH_A_PT_df['NSTAGEN2'].notna() & (MH_A_PT_df['NSTAGEN2'] != ""),
            MH_A_PT_df['NSTAGE']
        )
    )
    
    MH_A_PT_df['MSTAGE'] = MH_A_PT_df['MSTAGM1C'].where(
        MH_A_PT_df['MSTAGM1C'].notna() & (MH_A_PT_df['MSTAGM1C'] != ""),
        MH_A_PT_df['MSTAGEM1'].where(
            MH_A_PT_df['MSTAGEM1'].notna() & (MH_A_PT_df['MSTAGEM1'] != ""),
            MH_A_PT_df['MSTAGE']
        )
    )
    
    MH_A_PT_df['PTNM_T'] = MH_A_PT_df['PTNM_T4'].where(
        MH_A_PT_df['PTNM_T4'].notna() & (MH_A_PT_df['PTNM_T4'] != ""),
        MH_A_PT_df['PTNM_T']
    )
    
    MH_A_PT_df['PTNM_N'] = MH_A_PT_df['PTNM_N1'].where(
        MH_A_PT_df['PTNM_N1'].notna() & (MH_A_PT_df['PTNM_N1'] != ""),
        MH_A_PT_df['PTNM_N2'].where(
            MH_A_PT_df['PTNM_N2'].notna() & (MH_A_PT_df['PTNM_N2'] != ""),
            MH_A_PT_df['PTNM_N']
        )
    )
    
    return MH_A_PT_df.astype(str)

def process_RGACOHD_MH():
    """
    处理RGACOHD_MH数据集的所有字段
    """
    # 获取RGACOHD_MH数据集
    format_dataset = getFormatDataset('RGACOHD_MH','RGACOHD')
    RGACOHD_MH_df = format_dataset['RGACOHD_MH']
    RGACOHD_df = format_dataset['RGACOHD']
    
    # 添加一列BLANK，值为空字符串
    RGACOHD_MH_df['BLANK'] = ""
       
    RGACOHD_MH_df = pandas.merge(RGACOHD_MH_df, RGACOHD_df, how='left', on='SUBJID').fillna('')

    # 覆盖原有的 TYPE 字段，使用提取出来的公共函数
    RGACOHD_MH_df["TYPE"] = RGACOHD_MH_df.apply(lambda row: get_updated_type_from_hierarchy(row, "type"), axis=1)  

    RGACOHD_MH_df['LYYN'] = RGACOHD_MH_df['LY_LY1'].where(
        RGACOHD_MH_df['LY_LY1'].notna() & (RGACOHD_MH_df['LY_LY1'] != ""),
        RGACOHD_MH_df['LYYN']
    )
    
    RGACOHD_MH_df['VYN'] = RGACOHD_MH_df['V_V1'].where(
        RGACOHD_MH_df['V_V1'].notna() & (RGACOHD_MH_df['V_V1'] != ""),
        RGACOHD_MH_df['VYN']
    )
    
    RGACOHD_MH_df['ERSTM'] = RGACOHD_MH_df['ERSTM_ER'].where(
        RGACOHD_MH_df['ERSTM_ER'].notna() & (RGACOHD_MH_df['ERSTM_ER'] != ""),
        RGACOHD_MH_df['ERSTM']
    )
    
    RGACOHD_MH_df['MACROCL12'] = RGACOHD_MH_df['MACROCL1'].where(
        RGACOHD_MH_df['MACROCL1'].notna() & (RGACOHD_MH_df['MACROCL1'] != ""),
        RGACOHD_MH_df['MACROCL2']
    )
    
    RGACOHD_MH_df['PNYN'] = RGACOHD_MH_df['PN_PN1'].where(
        RGACOHD_MH_df['PN_PN1'].notna() & (RGACOHD_MH_df['PN_PN1'] != ""),
        RGACOHD_MH_df['PNYN']
    )

    RGACOHD_MH_df['TSTAGE'] = RGACOHD_MH_df['TSTAGET1'].where(
        RGACOHD_MH_df['TSTAGET1'].notna() & (RGACOHD_MH_df['TSTAGET1'] != ""),
        RGACOHD_MH_df['TSTAGET4'].where(
            RGACOHD_MH_df['TSTAGET4'].notna() & (RGACOHD_MH_df['TSTAGET4'] != ""),
            RGACOHD_MH_df['TSTAGE']
        )
    )
    
    RGACOHD_MH_df['PTNM_T'] = RGACOHD_MH_df['PTNM_T4'].where(
        RGACOHD_MH_df['PTNM_T4'].notna() & (RGACOHD_MH_df['PTNM_T4'] != ""),
        RGACOHD_MH_df['PTNM_T']
    )
    
    return RGACOHD_MH_df.astype(str)

def process_MH_A():
    """
    处理MH_A数据集的所有字段
    """
    # 获取MH_A数据集
    format_dataset = getFormatDataset('MH_A')
    MH_A_df = format_dataset['MH_A']
    
    # 覆盖原有的 TYPE_F 字段，使用提取出来的公共函数
    MH_A_df["TYPE_F"] = MH_A_df.apply(lambda row: get_updated_type_from_hierarchy(row, "typef"), axis=1) 
    
    # 覆盖原有的 TYPE_R 字段，使用提取出来的公共函数
    MH_A_df["TYPE_R"] = MH_A_df.apply(lambda row: get_updated_type_from_hierarchy(row, "typer"), axis=1) 
    
    MH_A_df['TNM_T'] = MH_A_df['TNM_T4'].where(
        MH_A_df['TNM_T4'].notna() & (MH_A_df['TNM_T4'] != ""),
        MH_A_df['TNM_T']
    )
    
    MH_A_df['TNM_N'] = MH_A_df['TNM_N2'].where(
        MH_A_df['TNM_N2'].notna() & (MH_A_df['TNM_N2'] != ""),
        MH_A_df['TNM_N1'].where(
            MH_A_df['TNM_N1'].notna() & (MH_A_df['TNM_N1'] != ""),
            MH_A_df['TNM_N']
        )
    )
    
    MH_A_df['TNM_M'] = MH_A_df['TNM_M1'].where(
        MH_A_df['TNM_M1'].notna() & (MH_A_df['TNM_M1'] != ""),
        MH_A_df['TNM_M']
    )
    
    MH_A_df['PTNM_T'] = MH_A_df['PTNM_T4'].where(
        MH_A_df['PTNM_T4'].notna() & (MH_A_df['PTNM_T4'] != ""),
        MH_A_df['PTNM_T']
    )
    
    MH_A_df['PTNM_N'] = MH_A_df['PTNM_N1'].where(
        MH_A_df['PTNM_N1'].notna() & (MH_A_df['PTNM_N1'] != ""),
        MH_A_df['PTNM_N2'].where(
            MH_A_df['PTNM_N2'].notna() & (MH_A_df['PTNM_N2'] != ""),
            MH_A_df['PTNM_N']
        )
    )
    
    MH_A_df['TSTAGE'] = MH_A_df['TSTAGET1'].where(
        MH_A_df['TSTAGET1'].notna() & (MH_A_df['TSTAGET1'] != ""),
        MH_A_df['TSTAGET4'].where(
            MH_A_df['TSTAGET4'].notna() & (MH_A_df['TSTAGET4'] != ""),
            MH_A_df['TSTAGE']
        )
    )
    
    MH_A_df['NSTAGE'] = MH_A_df['NSTAGEN1'].where(
        MH_A_df['NSTAGEN1'].notna() & (MH_A_df['NSTAGEN1'] != ""),
        MH_A_df['NSTAGEN2'].where(
            MH_A_df['NSTAGEN2'].notna() & (MH_A_df['NSTAGEN2'] != ""),
            MH_A_df['NSTAGE']
        )
    )
    
    MH_A_df['MSTAGE'] = MH_A_df['MSTAGM1C'].where(
        MH_A_df['MSTAGM1C'].notna() & (MH_A_df['MSTAGM1C'] != ""),
        MH_A_df['MSTAGEM1'].where(
            MH_A_df['MSTAGEM1'].notna() & (MH_A_df['MSTAGEM1'] != ""),
            MH_A_df['MSTAGE']
        )
    )
    
    return MH_A_df.astype(str)

def process_MH_A_RC():
    """
    处理MH_A_RC数据集的所有字段
    """
    # 获取MH_A_RC数据集
    format_dataset = getFormatDataset('MH_A_RC','SUPR')
    MH_A_RC_df = format_dataset['MH_A_RC']
    SUPR_df = format_dataset['SUPR']
 
    MH_A_RC_df = pandas.merge(MH_A_RC_df, SUPR_df, how='left', on='SUBJID').fillna('')
    
    # 覆盖原有的 TYPE 字段，使用提取出来的公共函数
    MH_A_RC_df["TYPE"] = MH_A_RC_df.apply(lambda row: get_updated_type_from_hierarchy(row, "type"), axis=1) 
    
    return MH_A_RC_df.astype(str)  

def process_CO():
    
    # 获取CO这个dataframe
    format_dataset = getFormatDataset('CO')
    CO_CO_df = format_dataset['CO']
    
    # 定义字段集合
    clinical_columns = ['COCNCLV', 'COCNCLNG', 'COCNCPRT', 'COCNCDLY', 'COCNCOTH']
    pathological_columns = ['COCNPLVR', 'COCNPLNG', 'COCNPPRT', 'COCNPDLY', 'COCNPOTH']
    
    # 处理CLINICAL字段
    def generate_clinical(row):
        # 筛选非空值
        values = [str(row[col]).strip() for col in clinical_columns if pandas.notnull(row[col]) and row[col] != '']
        if values:  # 如果有非空值
            return 'CLINICAL: ' + ','.join(values)
        return ''  # 如果全为空，则返回空字符串
    
    CO_CO_df['COCNC'] = CO_CO_df.apply(generate_clinical, axis=1)
    
    # 处理PATHOLOGICAL字段
    def generate_pathological(row):
        # 筛选非空值
        values = [str(row[col]).strip() for col in pathological_columns if pandas.notnull(row[col]) and row[col] != '']
        if values:  # 如果有非空值
            return 'PATHOLOGICAL: ' + ','.join(values)
        return ''  # 如果全为空，则返回空字符串
    
    CO_CO_df['COCNP'] = CO_CO_df.apply(generate_pathological, axis=1)
    
    # 处理COCNEMON字段
    CO_CO_df['COCNEMON'] = CO_CO_df['COCNEMON'].apply(
        lambda x: f'Number of metastatic organs＝{x}' if pandas.notnull(x) and x != '' else ''
    )
    
    return CO_CO_df.astype(str)

def get_DD_from_SS_ALL():
    
    # 获取SS_A_ALL这个dataframe
    format_dataset = getFormatDataset('SS_A_ALL')
    SS_A_ALL_DD_df = format_dataset['SS_A_ALL']
    
    # 提取指定字段并转换为字符串
    SS_A_ALL_DD_df = SS_A_ALL_DD_df[['SUBJID', 'SURVSTAT', 'OUTDAT1', 'OUTDAT2', 'PRCDTH', 'PRCDTHDE']].astype(str)
    
    # 删除SURVSTAT为空的行
    SS_A_ALL_DD_df = SS_A_ALL_DD_df[SS_A_ALL_DD_df['SURVSTAT'] != '']
    
    # 新建OUTDAT字段
    SS_A_ALL_DD_df['OUTDAT'] = SS_A_ALL_DD_df['OUTDAT1'].where(
        SS_A_ALL_DD_df['OUTDAT1'].notna() & (SS_A_ALL_DD_df['OUTDAT1'] != ""),
        SS_A_ALL_DD_df['OUTDAT2']
    )
    
    # 将OUTDAT为“”的行替换为NA
    SS_A_ALL_DD_df['OUTDAT'] = SS_A_ALL_DD_df['OUTDAT'].replace("", np.nan)
    
    # 按SUBJID顺序，OUTDAT倒序排列数据。如果OUTDAT为""，则排在最前面
    SS_A_ALL_DD_df = SS_A_ALL_DD_df.sort_values(
        by=['SUBJID', 'OUTDAT'],
        ascending=[True, False],
        na_position='first'  # 将空值排在最前面
    )
    
    # 对每个SUBJID只保留第一条记录，使用drop_duplicates保持行的完整性
    SS_A_ALL_DD_df = SS_A_ALL_DD_df.drop_duplicates(subset=['SUBJID'], keep='first')
        
    return SS_A_ALL_DD_df.astype(str)
    
def add_field_to_file(data_source_key, fields_with_values):
    
    # add_field_to_file('FILE' ,{"NEW_FIELD_1": "Value1","NEW_FIELD_2": "Value2"})
    
    """
    给数据集添加指定的字段并填充固定的值。

    参数：
        data_source_key (str): 用于从 getFormatDataset 函数获取数据集的键值。
        fields_with_values (dict): 字典形式，键为需要添加的字段名，值为对应的固定值。

    返回值：
        pd.DataFrame: 修改后的 DataFrame，所有列均转换为字符串类型。
    """
    # 从 getFormatDataset 获取指定键对应的数据集
    format_dataset = getFormatDataset(data_source_key)
    
    # 提取目标 DataFrame
    add_field_df = format_dataset[data_source_key]

    # 遍历字典，为每个字段添加对应的固定值
    for field, value in fields_with_values.items():
        add_field_df[field] = value

    # 将所有列转换为字符串类型并返回
    return add_field_df.astype(str)

def get_GF_from_LB_A_BM():
    """
    获取 'LB_A_BM' 数据集并处理特定字段。
    
    返回值：
        pandas.DataFrame: 包含处理后数据的数据框，所有列均转换为字符串类型。
    """
    # 获取 'LB_A_BM' 数据集
    format_dataset = getFormatDataset('LB_A_BM[BM]')
    LB_A_BM_df = format_dataset['LB_A_BM[BM]']
    
    def process_group(group):
        if (group['CHKVALUE'] == 'WILD TYPE').all():
            return group.head(1)
        else:
            return group[group['CHKVALUE'] != 'WILD TYPE']

    # 应用处理逻辑
    processed_df = LB_A_BM_df.groupby(['SUBJID', 'CHKTYPE'], group_keys=False).apply(process_group)

    # 添加 CLASSIFICATION 字段
    def classify(value):
        if value == 'UNKNOWN':
            return 'UNKNOWN'
        elif value == 'OTHER':
            return ''
        elif value in ('WILD TYPE', 'NEGATIVE'):
            return 'NEGATIVE'
        else:
            return 'POSITIVE'

    processed_df['CLASSIFICATION'] = processed_df['CHKVALUE'].map(classify)

    # 返回所有列转换为字符串后的结果
    return processed_df.astype(str)

def process_INEX():
    """
    处理INEX数据集
    """
    # 获取INEX数据集
    format_dataset = getFormatDataset('INEX','RGACOHB')
    INEX_df = format_dataset['INEX']
    RGACOHB_df = format_dataset['RGACOHB']
    
    # 提取SUBJID、ARMCOHBX、ARMCOHBT字段
    RGACOHB_df = RGACOHB_df[['SUBJID','ARMCOHBX','ARMCOHBT']].copy()
    
    # 合并INEX和RGACOHB数据集
    INEX_df = pandas.merge(INEX_df, RGACOHB_df, how='left', on='SUBJID').fillna('')
    
    # 返回所有列转换为字符串后的结果
    return INEX_df.astype(str)
    
    
