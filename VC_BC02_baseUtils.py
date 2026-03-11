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

def get_cell_value(row, idx, context=None):
    """
    获取单元格值并进行格式化处理
    
    参数:
    - row: 行数据
    - idx (int): 列索引
    - context (dict, optional): 上下文信息（保留兼容性，但不再使用）
    
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
    - inputfile_dataset: 输入CSV步骤输出
    - inputpackage_dataset: 输入包步骤输出
    
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
        'sdtm_dataset',      # 映射步骤
        'inputfile_dataset',  # 输入CSV步骤
        'inputpackage_dataset'  # 输入包步骤
    ]
    
    return_path = ''
    
    for path in paths:
        # 检查路径是否包含任何需要时间戳的文件夹
        for timestamp_folder in timestamp_folders:
            normalized_parts = os.path.normpath(path).split(os.sep)
            if timestamp_folder in normalized_parts:
                normalized_parts = [
                    f'{timestamp_folder}-{current_time_str}' if part == timestamp_folder else part
                    for part in normalized_parts
                ]
                path = os.sep.join(normalized_parts)
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
    
def make_format_value(tMETAVAL, isDateType):
    """
    格式化字段值，主要处理日期类型的转换
    
    参数:
    - tMETAVAL (str): 原始元数据值
    - isDateType (bool): 是否为日期类型
    
    返回:
    - str: 格式化后的值
    
    注意：已移除4OTHER功能，简化了函数参数和逻辑
    """
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
            
            # 安全地分割日期部分
            parts = tMETAVAL.split('-')
            if len(parts) >= 3:
                year, month, day = parts[0], parts[1], parts[2]
            elif len(parts) == 2:
                year, month, day = parts[0], parts[1], ''
            else:
                year, month, day = parts[0], '', ''
            
            # 处理特殊的日期值（9999, 99等表示未知）
            if year == '9999':
                year = ''
            if month == '99':
                month = ''
            if day == '99':
                day = ''
            
            # 重新组合日期字符串
            if day:
                tMETAVAL = '-'.join([year, month, day])
            elif month:
                tMETAVAL = '-'.join([year, month])
            else:
                tMETAVAL = year
            
            # 根据不同的日期格式进行解析
            for idx, regex_pattern in enumerate(regex_patterns, start=1):
                match = re.match(regex_pattern, tMETAVAL)
                if match:
                    try:
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
                    except (ValueError, parser.ParserError):
                        print(f'Date:[{tMETAVAL}] parsing failed')
                        continue
                        
        return formatted_date
    else:
        # 处理非日期类型字段，直接返回原值
        # 注意：已移除4OTHER功能，不再处理"其他"选项的详细信息映射
        return tMETAVAL

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
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                print(f'Database {self.database} does not exist. Attempting to create it...')
                try:
                    # Connect without database to create it
                    cnx = mysql.connector.connect(
                        host=self.host,
                        user=self.user,
                        password=self.password,
                        charset="utf8mb4",
                        use_unicode=True,
                        allow_local_infile=True
                    )
                    cursor = cnx.cursor()
                    
                    # Create database
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
                    print(f'Database {self.database} created successfully.')
                    
                    # Try to set global local_infile
                    try:
                        cursor.execute("SET GLOBAL local_infile = 1")
                        print('Global local_infile set to 1.')
                    except mysql.connector.Error as e:
                        print(f'Warning: Could not set global local_infile: {e}')
                    
                    cursor.close()
                    cnx.close()
                    
                    # Retry connection
                    self.connection = mysql.connector.connect(
                        host=self.host,
                        user=self.user,
                        password=self.password,
                        database=self.database,
                        charset="utf8mb4",
                        use_unicode=True,
                        allow_local_infile=True
                    )
                    self.cursor = self.connection.cursor()
                    print('Connected to the database after creation.')
                    
                except mysql.connector.Error as create_err:
                    print(f'Error creating database: {create_err}')
                    raise
            elif err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print('Error: Access denied. Please check your username and password.')
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
        # 使用 CREATE OR REPLACE VIEW 强制更新视图，防止因底层表结构变更导致的 Error 1356
        query = f'''
        CREATE OR REPLACE ALGORITHM = UNDEFINED DEFINER=`root`@`%` SQL SECURITY DEFINER VIEW {view_name} AS 
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
        print(f'View {view_name} updated (recreated).')

    def index_exists(self, table_name, index_name):
        """检查索引是否存在"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"SHOW INDEX FROM {table_name} WHERE Key_name = '{index_name}'")
            result = cursor.fetchone()
            # 确保读取所有剩余结果
            cursor.fetchall()
            return result is not None
        except mysql.connector.Error:
            return False
        finally:
            cursor.close()

    def create_performance_indexes(self, metadata_table_name):
        """为性能优化创建必要的索引"""
        indexes = [
            {
                'name': 'idx_filename_fieldid',
                'sql': f'CREATE INDEX idx_filename_fieldid ON {metadata_table_name} (FILENAME, FIELDID)',
                'description': '支持 WHERE FILENAME + IN FIELDID 过滤'
            },
            {
                'name': 'idx_filename_rownum_subjid',
                'sql': f'CREATE INDEX idx_filename_rownum_subjid ON {metadata_table_name} (FILENAME, ROWNUM, SUBJID)',
                'description': '支持 GROUP BY 和 ORDER BY ROWNUM'
            },
            {
                'name': 'idx_rownum',
                'sql': f'CREATE INDEX idx_rownum ON {metadata_table_name} (ROWNUM)',
                'description': '支持排序优化'
            },
            {
                'name': 'idx_filename_fieldid_formval',
                'sql': f'CREATE INDEX idx_filename_fieldid_formval ON {metadata_table_name} (FILENAME, FIELDID, FORMVAL(100))',
                'description': '支持非空值过滤的三列复合索引（FORMVAL前100字符）'
            }
        ]
        
        created_count = 0
        for index in indexes:
            if not self.index_exists(metadata_table_name, index['name']):
                try:
                    self.execute_query(index['sql'])
                    print(f"✓ 创建索引 {index['name']}: {index['description']}")
                    created_count += 1
                except mysql.connector.Error as e:
                    if 'WHERE' in index['sql']:
                        # 尝试创建不带WHERE条件的索引
                        simple_sql = index['sql'].split(' WHERE')[0]
                        try:
                            self.execute_query(simple_sql)
                            print(f"✓ 创建简化索引 {index['name']}: {index['description']}")
                            created_count += 1
                        except mysql.connector.Error as e2:
                            print(f"✗ 创建索引 {index['name']} 失败: {e2}")
                    else:
                        print(f"✗ 创建索引 {index['name']} 失败: {e}")
            else:
                pass  # 索引已存在，静默跳过
        
        return created_count

    def analyze_query_performance(self, query):
        """分析查询性能（执行EXPLAIN）"""
        cursor = self.connection.cursor()
        try:
            explain_query = f"EXPLAIN {query}"
            cursor.execute(explain_query)
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            print("=== EXPLAIN 分析结果 ===")
            for i, row in enumerate(results):
                print(f"步骤 {i+1}:")
                for j, col in enumerate(columns):
                    if row[j] is not None:
                        print(f"  {col}: {row[j]}")
            
            # 检查是否有性能问题
            issues = []
            for row in results:
                if 'Using temporary' in str(row):
                    issues.append("使用临时表")
                if 'Using filesort' in str(row):
                    issues.append("使用文件排序")
                if 'ALL' in str(row):
                    issues.append("全表扫描")
            
            if issues:
                print(f"⚠️ 性能问题: {', '.join(issues)}")
            else:
                print("✓ 查询计划良好")
                
            return results, issues
            
        except mysql.connector.Error as e:
            print(f"EXPLAIN 执行失败: {e}")
            return None, []
        finally:
            # 确保游标正确关闭
            try:
                cursor.close()
            except:
                pass

    def create_temp_table_for_file(self, table_name, view_name, filename):
        """为特定文件创建优化的工作表"""
        from VC_OP04_format import ENABLE_WORK_TABLE_PERSISTENCE
        
        work_table_name = f"work_{filename.lower().replace('-', '_')}"
        
        # 如果启用持久化且工作表已存在，直接复用
        if ENABLE_WORK_TABLE_PERSISTENCE:
            try:
                self.cursor.execute(f"SHOW TABLES LIKE '{work_table_name}'")
                if self.cursor.fetchone():
                    print(f"  → 复用现有工作表: {work_table_name}")
                    return work_table_name
            except mysql.connector.Error:
                pass
        
        # 如果不保留或工作表不存在，则删除重建
        try:
            self.execute_query(f"DROP TABLE IF EXISTS {work_table_name}")
        except:
            pass
        
        # 创建工作表（使用普通表而非临时表以避免重用问题）
        create_sql = f'''
        CREATE TABLE {work_table_name} AS
        SELECT * FROM {view_name} 
        WHERE FILENAME = '{filename}' AND FORMVAL IS NOT NULL
        '''
        
        try:
            self.execute_query(create_sql)
            
            # 为工作表创建索引
            index_sqls = [
                f"CREATE INDEX idx_{work_table_name}_fieldid ON {work_table_name} (FIELDID)",
                f"CREATE INDEX idx_{work_table_name}_rownum_subjid ON {work_table_name} (ROWNUM, SUBJID)",
                f"CREATE INDEX idx_{work_table_name}_rownum ON {work_table_name} (ROWNUM)"
            ]
            
            for idx_sql in index_sqls:
                try:
                    self.execute_query(idx_sql)
                except mysql.connector.Error:
                    pass  # 索引创建失败不影响主流程
            
            if ENABLE_WORK_TABLE_PERSISTENCE:
                print(f"  → 创建持久工作表: {work_table_name}")
            else:
                print(f"✓ 为文件 {filename} 创建优化工作表: {work_table_name}")
            return work_table_name
            
        except mysql.connector.Error as e:
            print(f"✗ 创建工作表失败: {e}")
            return None

    def cleanup_work_tables(self):
        """清理所有工作表（可配置是否保留）"""
        from VC_OP04_format import ENABLE_WORK_TABLE_PERSISTENCE
        
        if not ENABLE_WORK_TABLE_PERSISTENCE:
            cursor = self.connection.cursor()
            try:
                cursor.execute("SHOW TABLES LIKE 'work_%'")
                tables = cursor.fetchall()
                
                for (table_name,) in tables:
                    try:
                        self.execute_query(f"DROP TABLE IF EXISTS {table_name}")
                        print(f"✓ 清理工作表: {table_name}")
                    except:
                        pass
                        
            except mysql.connector.Error:
                pass
            finally:
                try:
                    cursor.close()
                except:
                    pass
        else:
            print("✓ 工作表已保留以供下次使用")
