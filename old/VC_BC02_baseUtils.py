from VC_BC01_constant import *

###
#
# 共通方法
#
###
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
    cell_value = row[idx]
    if cell_value is None:
        return ''
    return str(cell_value).strip()

def create_directory(*paths):
    current_time = datetime.now()
    current_time_str = current_time.strftime('%Y%m%d%H%M%S')
    folder = 'sdtm_dataset'
    return_path = ''
    for path in paths:
        if folder in path:
            path = path.replace(folder,f'{folder}-{current_time_str}')
            return_path = path
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            print(f'Error: {e}')
            sys.exit(1)
    return return_path

def try_convert_to_int(value):
    try:
        return int(value)
    except ValueError:
        return value
    
def make_format_value(tMETAVAL, isDateType, field_param, row, codeDict4other):
    logger = create_logger(os.path.join(SPECIFIC_PATH, 'log_file.log'), log_level=logging.DEBUG)

    tFORMVAL = None

    # replace_dict = {'1':'8','2':'1','3':'6','4':'7','5':'0','6':'4','7':'2','8':'3','9':'5','0':'9',
    #                 'A':'V','B':'a','C':'O','D':'l','E':'C','F':'W','G':'J','H':'p','I':'N','J':'e',
    #                 'K':'Q','L':'K','M':'R','N':'I','O':'d','P':'F','Q':'H','R':'i','S':'f','T':'Y',
    #                 'U':'k','V':'y','W':'U','X':'G','Y':'r','Z':'L','a':'X','b':'S','c':'z','d':'T',
    #                 'e':'M','f':'E','g':'j','h':'c','i':'v','j':'u','k':'x','l':'B','m':'o','n':'w',
    #                 'o':'A','p':'m','q':'b','r':'s','s':'t','t':'q','u':'h','v':'Z','w':'D','x':'g',
    #                 'y':'P','z':'n'
    #                 }

    regex_patterns = [
        '\d{4}-\d{1,2}-\d{1,2}$',
        '\d{4}-\d{1,2}(-\D*\d*)?',
        '\d{4}(-\D*\d*){0,2}'
    ]
    tMETAVAL = tMETAVAL.strip()
    if isDateType:
        formatted_date = ''
        if tMETAVAL:
            tMETAVAL = tMETAVAL.replace('/', '-')
            year, month, day = tMETAVAL.split('-')
            if year == '9999':
                year = ''
            if month == '99':
                month = ''
            if day == '99':
                day = ''
            tMETAVAL = '-'.join([year, month, day])
            for idx, regex_pattern in enumerate(regex_patterns, start=1):
                match = re.match(regex_pattern, tMETAVAL)
                if match:
                    if idx == 1:
                        parsed_date = parser.parse(tMETAVAL)
                        formatted_date = parsed_date.strftime('%Y-%m-%d')
                        break
                    elif idx == 2:
                        if len(tMETAVAL) > 6:
                            tMETAVAL = tMETAVAL[:7]
                            if not tMETAVAL[-1].isdigit():
                                tMETAVAL = tMETAVAL[:6]
                        parsed_date = parser.parse(tMETAVAL)
                        formatted_date = parsed_date.strftime('%Y-%m')
                        break
                    elif idx == 3:
                        if len(tMETAVAL) > 4:
                            tMETAVAL = tMETAVAL[:4]
                        parsed_date = parser.parse(tMETAVAL)
                        formatted_date = parsed_date.strftime('%Y')
                        break
                    else:
                        print(f'Date:[{tMETAVAL}] is wrong')
        tFORMVAL = formatted_date  
    # elif field_param[COL_CODELISTNAME]:
    #     tFORMVAL = tMETAVAL
    else:
        tFORMVAL = tMETAVAL
        if tMETAVAL == field_param[COL_OTHERVAL]:
            othValField_codelist = field_param[COL_CODELISTNAME] + SUFFIX_4OTHER
            if othValField_codelist in codeDict4other:
                other_details_val = row[field_param[COL_OTHERDETAILSFIELD]].strip()
                if other_details_val in codeDict4other[othValField_codelist]:
                    tFORMVAL = codeDict4other[othValField_codelist][other_details_val]
                else:
                    print(f'Other Details:[{other_details_val}] is untranslated')
                    logger.info(f'Other Details:[{other_details_val}] is untranslated')
            else:
                print(f'CodeListName:[{othValField_codelist}] is not existed')
                logger.info(f'CodeListName:[{othValField_codelist}] is not existed')
    # else:
    #     tFORMVAL = tMETAVAL

    return tFORMVAL

###
#
# 数据库工具
#
###
class DatabaseManager:
    def __init__(self):
        self.host = DB_HOST
        self.user = DB_USER
        self.password = DB_PASSWORD
        self.database = DB_DATABASE
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset="utf8mb4",
                use_unicode=True
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
