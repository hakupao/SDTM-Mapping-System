import os
import pandas as pd

# 定义路径管理器
class PathManager:
    
    def __init__(self, base_folder):
        self.base_folder = base_folder

    def get_input_folder(self):
        return os.path.join(self.base_folder, '02_Cleaning', 'cleaning_dataset')

    def get_other_details_path(self):
        return os.path.join(self.base_folder, 'OtherDetails.csv')

    def get_output_csv_path(self):
        return os.path.join(self.base_folder, 'Formatted_OtherDetails.csv')

    def get_output_excel_path(self):
        return os.path.join(self.base_folder, 'Formatted_OtherDetails.xlsx')

# 初始化路径管理器
base_folder = r'studySpecific\CIRCULATE'
path_manager = PathManager(base_folder)

# 读取 OtherDetails.csv 文件
other_details_df = pd.read_csv(path_manager.get_other_details_path())

# 初始化一个空的 DataFrame 用于输出
output_df = pd.DataFrame(columns=['FILENAME', 'REGNUM', 'FIELDNAME_OTHER', 'VALUE_OTHER', 'FIELDNAME_OTHERDETAILS', 'VALUE_OTHERDETAILS'])

# 遍历输入文件夹中的文件
input_folder = path_manager.get_input_folder()
for filename in os.listdir(input_folder):
    if filename.startswith('C-') and filename.endswith('.csv'):
        # 移除 'C-' 前缀以匹配 OtherDetails.csv
        file_key = filename[2:]

        # 读取当前的 CSV 文件
        file_path = os.path.join(input_folder, filename)
        try:
            current_df = pd.read_csv(file_path, low_memory=False)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue

        # 检查当前 DataFrame 是否包含必要列
        if 'REGNUM' not in current_df.columns:
            print(f"Warning: 'REGNUM' column not found in {filename}. Skipping...")
            continue

        # 过滤 OtherDetails DataFrame 以获取当前文件的详细信息
        file_details = other_details_df[other_details_df['FILENAME'] == file_key]

        # 遍历过滤后的详细信息的行
        for _, row in file_details.iterrows():
            fieldname_other = row['FIELDNAME_OTHER']
            fieldname_otherdetails = row['FIELDNAME_OTHERDETAILS']

            # 检查列是否存在
            if fieldname_other not in current_df.columns or fieldname_otherdetails not in current_df.columns:
                print(f"Warning: Missing column {fieldname_other} or {fieldname_otherdetails} in {filename}")
                # 记录到日志文件
                with open('missing_columns_log.txt', 'a') as log_file:
                    log_file.write(f"Missing column {fieldname_other} or {fieldname_otherdetails} in {filename}\n")
                continue

            # 从当前的 CSV 中提取相关列
            for _, data_row in current_df.iterrows():
                value_other = data_row[fieldname_other]
                value_otherdetails = data_row[fieldname_otherdetails]

                # 检查 VALUE_OTHERDETAILS 是否为空
                if pd.notna(value_otherdetails):
                    new_row = pd.DataFrame({
                        'REGNUM': [data_row['REGNUM']],
                        'FILENAME': [file_key],
                        'FIELDNAME_OTHER': [fieldname_other],
                        'VALUE_OTHER': [value_other],
                        'FIELDNAME_OTHERDETAILS': [fieldname_otherdetails],
                        'VALUE_OTHERDETAILS': [value_otherdetails]
                    })

                    # 检查 new_row 是否为空或全 NA
                    if not new_row.empty and not new_row.isnull().all(axis=None):
                        output_df = pd.concat([output_df, new_row], ignore_index=True)

# 以 VALUE_OTHER, VALUE_OTHERDETAILS 为 key，对数据进行去重
output_df = output_df.drop_duplicates(subset=['FILENAME', 'FIELDNAME_OTHER', 'VALUE_OTHER', 'FIELDNAME_OTHERDETAILS', 'VALUE_OTHERDETAILS', 'REGNUM'])

# 保存输出 DataFrame 到一个新的 CSV 文件，带有 BOM
output_csv_path = path_manager.get_output_csv_path()
output_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')

# 输出一份 Excel 文件
output_excel_path = path_manager.get_output_excel_path()
output_df.to_excel(output_excel_path, index=False)

print(f"Processing completed. Results saved to:\nCSV: {output_csv_path}\nExcel: {output_excel_path}")
