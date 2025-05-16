import pandas as pd
import os
from pathlib import Path

def get_csv_info(folder_path, output_file):
    # 创建一个空的DataFrame来存储结果
    result_df = pd.DataFrame()
    
    # 遍历文件夹中的所有CSV文件
    for file in Path(folder_path).glob('*.csv'):
        try:
            # 读取CSV文件的前几行来获取列名
            df = pd.read_csv(file, nrows=0)
            columns = df.columns.tolist()
            
            # 创建临时DataFrame来存储当前文件的信息
            temp_df = pd.DataFrame({
                '文件名': [file.name] * len(columns),
                '字段名': columns
            })
            
            # 将当前文件的信息添加到结果DataFrame中
            result_df = pd.concat([result_df, temp_df], ignore_index=True)
            
        except Exception as e:
            print(f"处理文件 {file.name} 时出错: {str(e)}")
    
    # 将结果保存为Excel文件
    result_df.to_excel(output_file, index=False)
    print(f"结果已保存到: {output_file}")

if __name__ == "__main__":
    # 设置文件夹路径和输出文件路径
    folder_path = r"studySpecific\CIRCULATE\03_Format\format_dataset"
    output_file = r"studySpecific\CIRCULATE\03_Format\format_dataset\csv_info.xlsx"
    
    get_csv_info(folder_path, output_file)
