"""
VAPORCONE 项目基础工具模块

该模块提供了项目中使用的基础工具函数和数据库管理类，包括：
- 日志记录器创建
- 数据处理工具函数
- 数据库操作管理类
"""

from VC_BC01_constant import *


def create_logger(file_name, log_level=logging.DEBUG):
    """
    创建一个日志记录器(Logger)，避免重复添加 Handler 造成资源泄露。

    参数:
    - file_name (str): 日志文件路径，用于存储日志内容。
    - log_level (int): 日志级别，默认为 logging.DEBUG。

    返回:
    - logging.Logger: 配置完成的日志记录器实例。
    """
    logger = logging.getLogger(file_name)
    
    # 检查是否已添加过 Handler，避免重复添加
    if not logger.hasHandlers():
        logger.setLevel(log_level)  # 设置日志记录器级别
        
        # 创建文件 Handler
        file_handler = logging.FileHandler(file_name, encoding='utf-8')
        file_handler.setLevel(log_level)  # 设置 Handler 日志级别
        
        # 定义日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # 将 Handler 添加到 Logger
        logger.addHandler(file_handler)
        
    return logger

def get_cell_value(row, idx):
    """
    获取单元格值并进行格式化处理
    
    参数:
    - row: 行数据
    - idx (int): 列索引
    
    返回:
    - str: 格式化后的单元格值
    """
    cell_value = row[idx]
    if cell_value is None:
        return ''
    return str(cell_value).strip()

def create_directory(*paths):
    """
    创建目录，如果目录包含时间戳文件夹名称则添加时间戳
    
    支持的时间戳文件夹类型：
    - cleaning_dataset: 清洗步骤输出
    - format_dataset: 格式化步骤输出  
    - sdtm_dataset: 映射步骤输出
    
    参数:
    - *paths: 可变长度的路径参数
    
    返回:
    - str: 返回包含时间戳的路径（如果适用）
    """
    current_time = datetime.now()
    current_time_str = current_time.strftime('%Y%m%d%H%M%S')
    
    # 支持多种需要时间戳的文件夹类型
    timestamp_folders = [
        'cleaning_dataset',  # 清洗步骤
        'format_dataset',    # 格式化步骤
        'sdtm_dataset'       # 映射步骤（原有）
    ]
    
    return_path = ''
    
    for path in paths:
        # 检查路径是否包含任何需要时间戳的文件夹
        for timestamp_folder in timestamp_folders:
            if timestamp_folder in path:
                path = path.replace(timestamp_folder, f'{timestamp_folder}-{current_time_str}')
                return_path = path
                break
        
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            print(f'Error: {e}')
            sys.exit(1)
    
    return return_path

def find_latest_timestamped_path(base_path, folder_pattern):
    """
    查找最新的时间戳文件夹路径
    
    参数:
    - base_path (str): 基础路径（父目录）
    - folder_pattern (str): 文件夹模式名称（如 'cleaning_dataset', 'format_dataset', 'sdtm_dataset'）
    
    返回:
    - str: 最新的时间戳文件夹完整路径，如果找不到则返回原始路径
    """
    try:
        if not os.path.exists(base_path):
            print(f'警告: 基础路径不存在 - {base_path}')
            return os.path.join(base_path, folder_pattern)
        
        # 获取目录下所有文件夹
        all_items = os.listdir(base_path)
        folders = [item for item in all_items if os.path.isdir(os.path.join(base_path, item))]
        
        # 查找匹配模式的时间戳文件夹
        timestamped_folders = []
        for folder in folders:
            if folder.startswith(f'{folder_pattern}-') and len(folder) == len(folder_pattern) + 15:  # pattern + '-' + 14位时间戳
                try:
                    # 验证时间戳格式 YYYYMMDDHHMMSS
                    timestamp_part = folder[len(folder_pattern) + 1:]
                    datetime.strptime(timestamp_part, '%Y%m%d%H%M%S')
                    timestamped_folders.append(folder)
                except ValueError:
                    continue
        
        if timestamped_folders:
            # 按时间戳排序，返回最新的
            timestamped_folders.sort(reverse=True)
            latest_folder = timestamped_folders[0]
            latest_path = os.path.join(base_path, latest_folder)
            print(f'找到最新的时间戳文件夹: {latest_folder}')
            return latest_path
        else:
            # 如果没有找到时间戳文件夹，检查是否存在原始文件夹
            original_path = os.path.join(base_path, folder_pattern)
            if os.path.exists(original_path):
                print(f'使用原始文件夹: {folder_pattern}')
                return original_path
            else:
                print(f'警告: 未找到 {folder_pattern} 相关文件夹，返回原始路径')
                return original_path
                
    except Exception as e:
        print(f'查找时间戳文件夹时出错: {e}')
        return os.path.join(base_path, folder_pattern)

def try_convert_to_int(value):
    """
    尝试将值转换为整数
    
    参数:
    - value: 要转换的值
    
    返回:
    - int 或 原值: 转换成功返回整数，失败返回原值
    """
    try:
        return int(value)
    except ValueError:
        return value
    
def make_format_value(tMETAVAL, isDateType, field_param, row, codeDict4other):
    """
    格式化字段值，处理日期类型和其他特殊值
    
    参数:
    - tMETAVAL (str): 原始元数据值
    - isDateType (bool): 是否为日期类型
    - field_param (dict): 字段参数配置
    - row (dict): 当前行数据
    - codeDict4other (dict): 其他值的代码字典
    
    返回:
    - str: 格式化后的值
    """
    logger = create_logger(
        os.path.join(SPECIFIC_PATH, 'log_file.log'), 
        log_level=logging.DEBUG
    )

    tFORMVAL = None

    # 日期匹配的正则表达式模式
    regex_patterns = [
        r'\d{4}-\d{1,2}-\d{1,2}$',
        r'\d{4}-\d{1,2}(-\D*\d*)?',
        r'\d{4}(-\D*\d*){0,2}'
    ]
    
    tMETAVAL = tMETAVAL.strip()
    if isDateType:
        # 处理日期类型字段
        formatted_date = ''
        if tMETAVAL:
            # 将 '/' 替换为 '-'
            tMETAVAL = tMETAVAL.replace('/', '-')
            year, month, day = tMETAVAL.split('-')
            
            # 处理特殊的日期值（9999, 99等表示未知）
            if year == '9999':
                year = ''
            if month == '99':
                month = ''
            if day == '99':
                day = ''
            
            tMETAVAL = '-'.join([year, month, day])
            
            # 根据不同的日期格式进行解析
            for idx, regex_pattern in enumerate(regex_patterns, start=1):
                match = re.match(regex_pattern, tMETAVAL)
                if match:
                    if idx == 1:  # 完整日期格式 YYYY-MM-DD
                        parsed_date = parser.parse(tMETAVAL)
                        formatted_date = parsed_date.strftime('%Y-%m-%d')
                        break
                    elif idx == 2:  # 年月格式 YYYY-MM
                        if len(tMETAVAL) > 6:
                            tMETAVAL = tMETAVAL[:7]
                            if not tMETAVAL[-1].isdigit():
                                tMETAVAL = tMETAVAL[:6]
                        parsed_date = parser.parse(tMETAVAL)
                        formatted_date = parsed_date.strftime('%Y-%m')
                        break
                    elif idx == 3:  # 年格式 YYYY
                        if len(tMETAVAL) > 4:
                            tMETAVAL = tMETAVAL[:4]
                        parsed_date = parser.parse(tMETAVAL)
                        formatted_date = parsed_date.strftime('%Y')
                        break
                    else:
                        print(f'Date:[{tMETAVAL}] is wrong')
        tFORMVAL = formatted_date  
    else:
        # 处理非日期类型字段
        tFORMVAL = tMETAVAL
        
    return tFORMVAL

class DatabaseManager:
    """
    数据库管理类，提供MySQL数据库的连接和操作功能
    """
    
    def __init__(self):
        """
        初始化数据库管理器
        """
        self.host = DB_HOST
        self.user = DB_USER
        self.password = DB_PASSWORD
        self.database = DB_DATABASE
        self.connection = None
        self.cursor = None

    def connect(self):
        """
        连接到MySQL数据库
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset="utf8mb4",
                use_unicode=True,
                allow_local_infile=True  # 启用LOCAL INFILE支持
            )
            self.cursor = self.connection.cursor()
            print('Connected to the database.')
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print('Error: Access denied. Please check your username and password.')
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print('Error: Database does not exist.')
            else:
                print(f'Error: {err}')

    def disconnect(self):
        if self.connection:
            self.connection.close()
            print('Disconnected from the database.')

    def execute_query(self, query, values=None):
        cursor = self.connection.cursor()
        try:
            if values:
                cursor.execute(query, values)
            else:
                cursor.execute(query)
            self.connection.commit()
        except mysql.connector.Error as err:
            print(f'Error: {err}')
        finally:
            cursor.close()

    def table_exists(self, table_name):
        cursor = self.connection.cursor()
        try:
            cursor.execute(f'SHOW TABLES LIKE \'{table_name}\'')
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def delete_table_if_exists(self, table_name):
        if self.table_exists(table_name):
            print(f'Table {table_name} already exists.')
            cursor = self.connection.cursor()
            try:
                cursor.execute(f'DROP TABLE {table_name}')
                print(f'Table {table_name} has been deleted.')
            finally:
                cursor.close()

    def create_codelist_table(self, table_name):
        self.delete_table_if_exists(table_name)
        query = f'''CREATE TABLE {table_name} (
                    `CODELISTID` VARCHAR(256) NOT NULL COLLATE 'UTF8MB4_GENERAL_CI',
                    `CODE` VARCHAR(256) NOT NULL COLLATE 'UTF8MB4_GENERAL_CI',
                    `VALUE_RAW` TEXT NOT NULL COLLATE 'UTF8MB4_GENERAL_CI',
                    `VALUE_EN` TEXT NOT NULL COLLATE 'UTF8MB4_GENERAL_CI',
                    `VALUE_SDTM` TEXT NOT NULL COLLATE 'UTF8MB4_GENERAL_CI',
                    PRIMARY KEY (`CODELISTID`, `CODE`) USING BTREE
                )
                COLLATE='UTF8MB4_GENERAL_CI'
                ENGINE=InnoDB
                ;
                '''
        self.execute_query(query)
        print(f'Table {table_name} created.')

    def create_metadata_table(self, table_name):
        self.delete_table_if_exists(table_name)
        query = f'''CREATE TABLE {table_name} (
                    `No` INT(11) NULL DEFAULT NULL,
                    `FILENAME` VARCHAR(64) NOT NULL DEFAULT '' COLLATE 'UTF8MB4_GENERAL_CI',
                    `ROWNUM` INT(11) NOT NULL DEFAULT '0',
                    `USUBJID` VARCHAR(16) NOT NULL COLLATE 'UTF8MB4_GENERAL_CI',
                    `SUBJID` VARCHAR(16) NULL DEFAULT NULL COLLATE 'UTF8MB4_GENERAL_CI',
                    `FIELDLBL` TEXT NULL DEFAULT NULL COLLATE 'UTF8MB4_GENERAL_CI',
                    `FIELDID` VARCHAR(64) NOT NULL COLLATE 'UTF8MB4_GENERAL_CI',
                    `METAVAL` TEXT NOT NULL COLLATE 'UTF8MB4_GENERAL_CI',
                    `FORMVAL` TEXT NULL DEFAULT NULL COLLATE 'UTF8MB4_GENERAL_CI',
                    `DATETYPE` INT(11) NULL DEFAULT NULL,
                    `CODELISTID` VARCHAR(64) NULL DEFAULT NULL COLLATE 'UTF8MB4_GENERAL_CI',
                    `CHKFIELDID` VARCHAR(64) NULL DEFAULT NULL COLLATE 'UTF8MB4_GENERAL_CI',
                    PRIMARY KEY (`ROWNUM`, `USUBJID`, `FIELDID`, `FILENAME`) USING BTREE
                )
                COLLATE='UTF8MB4_GENERAL_CI'
                ENGINE=InnoDB
                ;
                '''
        self.execute_query(query)
        print(f'Table {table_name} created.')

    def create_transdata_view(self, view_name, metadata_table_name, codelist_table_name):
        if self.table_exists(view_name):
            print(f"View {view_name} already exists.")
        else:
            query = f'''
            CREATE ALGORITHM = UNDEFINED DEFINER=`root`@`%` SQL SECURITY DEFINER VIEW {view_name} AS 
            SELECT 
                `m`.`No` AS `No`,
                `m`.`FILENAME` AS `FILENAME`,
                `m`.`ROWNUM` AS `ROWNUM`,
                `m`.`USUBJID` AS `USUBJID`,
                `m`.`SUBJID` AS `SUBJID`,
                `m`.`FIELDLBL` AS `FIELDLBL`,
                `m`.`FIELDID` AS `FIELDID`,
                `m`.`METAVAL` AS `METAVAL`,
                `m`.`FORMVAL` AS `FORMVAL`,
                IF(ISNULL(`c`.`VALUE_EN`), `m`.`FORMVAL`, `c`.`VALUE_EN`) AS `TRANSVAL`,
                IF(ISNULL(`c`.`VALUE_SDTM`),'',`c`.`VALUE_SDTM`) AS `SDTMVAL`,
                `m`.`CHKFIELDID` AS `CHKFIELDID`
            FROM 
                {metadata_table_name} `m` 
            LEFT JOIN 
                {codelist_table_name} `c` ON ((`m`.`CODELISTID` = `c`.`CODELISTID`) AND (`m`.`FORMVAL` = `c`.`CODE`));
            '''
            self.execute_query(query)
            print(f'View {view_name} created.')
