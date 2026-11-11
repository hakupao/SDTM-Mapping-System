"""
VAPORCONE 项目基础工具模块

该模块提供了项目中使用的基础工具函数和数据库管理类，包括：
- 日志记录器创建
- 统一控制台输出工具
- 数据处理工具函数
- 数据库操作管理类
"""

from VC_BC01_constant import *
try:
    import mysql.connector
    from mysql.connector import errorcode
except ImportError:  # sqlite 后端不需要 mysql-connector-python
    mysql = None
    errorcode = None
import traceback
import unicodedata
import time as _time
import sys as _sys
import os as _os


def _configure_console_encoding():
    """
    统一使用 UTF-8 输出控制台文本。

    VSCode Code Runner 和非中文 Windows 区域设置可能给 Python stdout
    分配 cp932 等编码，直接打印中文会触发 UnicodeEncodeError。
    """
    for stream in (_sys.stdout, _sys.stderr):
        if hasattr(stream, 'reconfigure'):
            try:
                stream.reconfigure(encoding='utf-8', errors='replace')
            except (OSError, ValueError):
                pass


_configure_console_encoding()

# ======================================================================
# 统一控制台输出规范
# ======================================================================
CONSOLE_WIDTH = 70


# ------ CJK 对齐工具 ------

def _display_width(s):
    """
    计算字符串在终端中的实际显示宽度。
    CJK 全角字符占 2 格，ASCII 占 1 格。
    """
    width = 0
    for ch in str(s):
        if unicodedata.east_asian_width(ch) in ('W', 'F'):
            width += 2
        else:
            width += 1
    return width


def cjk_ljust(s, width):
    """左对齐，CJK 感知。与 str.ljust 等效但按显示宽度计算。"""
    s = str(s)
    return s + ' ' * max(0, width - _display_width(s))


def cjk_rjust(s, width):
    """右对齐，CJK 感知。与 str.rjust 等效但按显示宽度计算。"""
    s = str(s)
    return ' ' * max(0, width - _display_width(s)) + s


# ------ 步骤横幅 ------

def print_step_header(step_id, step_name):
    """
    输出步骤开始横幅 (每个 VC_OP / VC_PS 入口统一调用)

    示例输出:
    ======================================================================
      ENSEMBLE | OP01 Cleaning | 开始处理
    ======================================================================
    """
    print()
    print('=' * CONSOLE_WIDTH)
    print(f'  {STUDY_ID} | {step_id} {step_name} | 开始处理')
    print('=' * CONSOLE_WIDTH)


def print_step_footer(step_id, step_name):
    """输出步骤结束横幅"""
    print()
    print('=' * CONSOLE_WIDTH)
    print(f'  {STUDY_ID} | {step_id} {step_name} | 处理完成')
    print('=' * CONSOLE_WIDTH)


# ------ 摘要输出 ------

def print_summary_header(title):
    """
    输出摘要表头

    示例输出:
    ======================================================================
      处理摘要 - Cleaning
    ======================================================================
    """
    print()
    print('=' * CONSOLE_WIDTH)
    print(f'  {title}')
    print('=' * CONSOLE_WIDTH)


def print_summary_kv(label, value):
    """输出摘要键值行，label 按 18 显示宽度左对齐"""
    print(f'  {cjk_ljust(label, 18)} {value}')


def print_summary_sep():
    """输出摘要分割线"""
    print('-' * CONSOLE_WIDTH)


# ------ 日志 + 控制台 ------

def log_and_print(logger, level, msg):
    """
    同时写日志文件和 stdout，统一 tag 前缀:
      [ERROR] / [WARN] / [SKIP] / [INFO]
    """
    print(f'[{level}] {msg}')
    if level == 'ERROR':
        logger.error(msg)
    elif level == 'WARN':
        logger.warning(msg)
    else:
        logger.info(msg)


# ------ 进度条 ------

from sdtm_study import PIPELINE_ENV_KEY, PROGRESS_MARKER  # noqa: E402  (共享常量)


def _enable_ansi():
    """在 Windows 上启用 ANSI/VT 终端控制序列。"""
    if _sys.platform == 'win32':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        except Exception:
            pass


def _bar_str(pct, width=20):
    filled = int(width * min(pct, 1.0))
    return '#' * filled + '-' * (width - filled)


def _fmt_elapsed(seconds):
    """格式化已用时间: 12s / 1m23s / 1h05m"""
    s = int(seconds)
    if s < 60:
        return f'{s}s'
    if s < 3600:
        return f'{s // 60}m{s % 60:02d}s'
    return f'{s // 3600}h{s % 3600 // 60:02d}m'


class ProgressReporter:
    """
    步骤内进度报告器。

    - 当 stdout 是终端 (TTY) 时，使用 \\r 内联刷新（单独运行某步骤时）。
    - 当 stdout 被管道捕获时（由 runner 调用），发送协议标记行
      供 PipelineProgress 解析。

    用法:
        progress = ProgressReporter(total=100, desc='Cleaning')
        for item in items:
            do_work(item)
            progress.update()
        progress.finish()
    """

    def __init__(self, total, desc='', width=CONSOLE_WIDTH):
        self.total = max(total, 1)
        self._desc = desc
        self._width = width
        self._desc_width = 14
        self.current = 0
        self._start = _time.time()
        self._last_render = 0
        self._is_tty = _sys.stdout.isatty()
        # 管道协议模式: 仅当 pipeline runner 设置了环境变量时才发送 @@PG@@ 标记
        self._is_pipeline = not self._is_tty and _os.environ.get(PIPELINE_ENV_KEY) == '1'
        # 动态步长: 将总量分为 ~100 次渲染，减少 I/O 开销
        self._render_every = max(1, self.total // 100)
        self._render()

    def update(self, n=1):
        """进度推进 n 步"""
        self.current = min(self.current + n, self.total)
        if self.current < self.total and self.current % self._render_every != 0:
            return
        now = _time.time()
        interval = 0.5 if not self._is_tty else 0.1
        if self.current >= self.total or (now - self._last_render) >= interval:
            self._render()
            self._last_render = now

    def _format_bar(self):
        """生成进度条文本行（TTY 和完成摘要共用）。"""
        pct = self.current / self.total
        elapsed = _time.time() - self._start

        if self.current > 0 and pct < 1.0:
            eta_s = int(elapsed / pct * (1.0 - pct))
            eta_str = f'ETA {eta_s // 60}m{eta_s % 60:02d}s' if eta_s >= 60 else f'ETA {eta_s}s'
        elif pct >= 1.0:
            eta_str = f'{elapsed:.1f}s'
        else:
            eta_str = '...'

        desc_r = cjk_ljust(self._desc, self._desc_width)
        cnt_str = f'{self.current}/{self.total}'
        pct_str = f'{pct * 100:5.1f}%'

        fixed = 2 + self._desc_width + 1 + 1 + len(cnt_str) + 1 + len(pct_str) + 1 + len(eta_str)
        bar_w = max(8, self._width - fixed - 2)
        filled = int(bar_w * pct)
        bar = '#' * filled + '-' * (bar_w - filled)

        return f'  {desc_r} [{bar}] {cnt_str} {pct_str} {eta_str}'

    def finish(self):
        """强制 100% 并换行"""
        self.current = self.total
        self._render()
        if self._is_tty:
            _sys.stdout.write('\n')
            _sys.stdout.flush()
        else:
            # 管道/静默模式: 输出一行完成摘要到滚动区，
            # 让父进程通过 print_line 显示，而非只更新 footer
            print(self._format_bar())

    def _render(self):
        if self._is_pipeline:
            # 管道协议模式: 仅 pipeline runner 消费
            _sys.stdout.write(f'{PROGRESS_MARKER}{self.current}/{self.total}/{self._desc}\n')
            _sys.stdout.flush()
            return
        if not self._is_tty:
            # 非 TTY 且非 pipeline (如 Code Runner): 静默，不输出噪音
            return

        # TTY 模式: \r 内联刷新
        line = self._format_bar()
        _sys.stdout.write(f'\r{line.ljust(self._width)}')
        _sys.stdout.flush()


class PipelineProgress:
    """
    使用 ANSI Scroll Region 实现的固定进度条。

    终端底部 3 行被排除在滚动区域外，永远固定不动:
      ──────────────────────────────────────────────────
        Pipeline  [####--------]  3/7  42.9%  OP03 元数据插入
        OP03      [########----]  5/9  55.6%  Build  ETA 8s

    步骤输出在上方自然滚动，与底部进度互不干扰。
    """

    FOOTER_LINES = 3

    def __init__(self, total_steps, steps_info):
        """
        参数:
            total_steps: 总步骤数
            steps_info: [(step_id, desc), ...] 每步的 ID 和中文描述
        """
        self.total_steps = total_steps
        self.steps_info = steps_info
        self.current_step = 0
        self.step_current = 0
        self.step_total = 0
        self.step_desc = ''
        self._pipeline_start = _time.time()
        self._step_start = 0
        self._last_footer_render = 0

        _enable_ansi()
        try:
            size = _os.get_terminal_size()
            self._rows = size.lines
            self._cols = size.columns
        except OSError:
            self._rows = 40
            self._cols = 80

        self._scroll_end = self._rows - self.FOOTER_LINES

        # 清屏并建立滚动区域
        _sys.stdout.write('\033[2J')                        # 清屏
        _sys.stdout.write(f'\033[1;{self._scroll_end}r')    # 设置滚动区域
        _sys.stdout.write('\033[1;1H')                      # 光标移到滚动区域顶部
        # 渲染初始 footer
        self._render_footer()
        # 光标回到滚动区域
        _sys.stdout.write(f'\033[1;1H')
        _sys.stdout.flush()

    def begin_step(self, step_index):
        """开始新步骤 (0-based index)"""
        self.current_step = step_index + 1
        self.step_current = 0
        self.step_total = 0
        self.step_desc = ''
        self._step_start = _time.time()
        self._update_footer()

    def parse_and_update(self, line):
        """解析进度协议标记。如果是标记行返回 True（不应打印）。"""
        if line.startswith(PROGRESS_MARKER):
            parts = line[len(PROGRESS_MARKER):].split('/', 2)
            try:
                self.step_current = int(parts[0])
                self.step_total = int(parts[1])
                self.step_desc = parts[2] if len(parts) > 2 else ''
            except (ValueError, IndexError):
                return True
            # 节流: 父进程快速消费管道数据，但限制 ANSI 重绘频率，
            # 避免 Windows 终端渲染过慢导致管道反压阻塞子进程
            now = _time.time()
            if self.step_current >= self.step_total or (now - self._last_footer_render) >= 0.1:
                self._update_footer()
                self._last_footer_render = now
            return True
        return False

    def print_line(self, line):
        """在滚动区域内打印一行输出。footer 不受影响。"""
        _sys.stdout.write(line + '\n')
        _sys.stdout.flush()

    def end_step(self):
        """步骤结束（footer 保留，等待下一步更新）。"""
        pass

    def cleanup(self):
        """流水线结束，重置滚动区域，光标移到 footer 之后。"""
        # 重置滚动区域为全屏
        _sys.stdout.write('\033[r')
        # 光标移到最后一行之后
        _sys.stdout.write(f'\033[{self._rows};1H\n')
        _sys.stdout.flush()

    def _update_footer(self):
        """在不影响滚动区域光标的情况下刷新 footer。"""
        _sys.stdout.write('\0337')  # DEC Save Cursor
        self._render_footer()
        _sys.stdout.write('\0338')  # DEC Restore Cursor
        _sys.stdout.flush()

    # 赤橙黄绿青蓝紫 — 每个步骤一种颜色
    _RAINBOW = [
        '\033[91m',           # 赤 bright red
        '\033[38;5;208m',     # 橙 orange (256-color)
        '\033[93m',           # 黄 bright yellow
        '\033[92m',           # 绿 bright green
        '\033[96m',           # 青 bright cyan
        '\033[94m',           # 蓝 bright blue
        '\033[95m',           # 紫 bright magenta
    ]
    _BRIGHT_YELLOW = '\033[93m'
    _RESET = '\033[0m'

    def _render_footer(self):
        """在固定区域 (scroll_end+1 ~ rows) 绘制 3 行 footer。"""
        base = self._scroll_end + 1
        W = min(self._cols, CONSOLE_WIDTH)

        sid, sdesc = ('', '')
        if self.current_step > 0:
            sid, sdesc = self.steps_info[self.current_step - 1]

        # Line 1: 分隔线
        _sys.stdout.write(f'\033[{base};1H\033[2K')
        _sys.stdout.write('\u2500' * W)

        # Line 2: Pipeline 总进度 (亮黄色)
        _sys.stdout.write(f'\033[{base + 1};1H\033[2K')
        if self.current_step > 0:
            p_pct = self.current_step / self.total_steps
            p_bar = _bar_str(p_pct)
            p_elapsed = _fmt_elapsed(_time.time() - self._pipeline_start)
            _sys.stdout.write(
                f'{self._BRIGHT_YELLOW}'
                f'  Pipeline  [{p_bar}] {self.current_step}/{self.total_steps}'
                f'  {p_pct * 100:5.1f}%  {p_elapsed}  {sid} {sdesc}'
                f'{self._RESET}'
            )

        # Line 3: 步骤内进度 (彩虹色，按步骤序号轮转)
        step_color = self._RAINBOW[(self.current_step - 1) % len(self._RAINBOW)] if self.current_step > 0 else ''
        _sys.stdout.write(f'\033[{base + 2};1H\033[2K')
        if self.step_total > 0:
            s_pct = self.step_current / self.step_total
            s_bar = _bar_str(s_pct)
            s_elapsed_raw = _time.time() - self._step_start
            s_elapsed = _fmt_elapsed(s_elapsed_raw)
            if self.step_current > 0 and s_pct < 1.0:
                eta_s = int(s_elapsed_raw / s_pct * (1.0 - s_pct))
                eta = f'ETA {eta_s}s' if eta_s < 60 else f'ETA {eta_s // 60}m{eta_s % 60:02d}s'
            else:
                eta = ''
            _sys.stdout.write(
                f'{step_color}'
                f'  {cjk_ljust(sid, 10)}[{s_bar}] {self.step_current}/{self.step_total}'
                f'  {s_pct * 100:5.1f}%  {s_elapsed}  {eta}'
                f'{self._RESET}'
            )
        elif self.current_step > 0:
            s_elapsed = _fmt_elapsed(_time.time() - self._step_start)
            _sys.stdout.write(f'{step_color}  {cjk_ljust(sid, 10)}{s_elapsed}  ...{self._RESET}')


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

class MySQLDatabaseManager:
    """
    数据库管理类，提供MySQL数据库的连接和操作功能
    """

    # GROUP BY 在 MySQL 5.7 下隐式按分组键排序
    implicit_group_order = True
    
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
        if mysql is None:
            print('未安装 mysql-connector-python，或在 project.local.json 设 DB_BACKEND=sqlite')
            sys.exit(2)
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset="utf8mb4",
                use_unicode=True,
                use_pure=True,
                allow_local_infile=True  # 启用LOCAL INFILE支持
            )
            self.cursor = self.connection.cursor()
            print(f'Connected to MySQL {self.host}/{self.database}')
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
                        use_pure=True,
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
                        use_pure=True,
                        allow_local_infile=True
                    )
                    self.cursor = self.connection.cursor()
                    print(f'Connected to MySQL {self.host}/{self.database} after creation.')
                    
                except mysql.connector.Error as create_err:
                    print(f'Error creating database: {create_err}')
                    raise
            elif err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print('Error: Access denied. Please check your username and password.')
                raise
            else:
                print(f'Error: {err}')
                raise

    def is_connected(self):
        return bool(self.connection and self.connection.is_connected())

    def disconnect(self):
        if self.cursor:
            try:
                self.cursor.close()
            except Exception:
                pass
            self.cursor = None
        if self.connection:
            self.connection.close()
            self.connection = None
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
        CREATE OR REPLACE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW {view_name} AS
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
            CASE WHEN `c`.`VALUE_EN` IS NULL THEN `m`.`FORMVAL` ELSE `c`.`VALUE_EN` END AS `TRANSVAL`,
            COALESCE(`c`.`VALUE_SDTM`, '') AS `SDTMVAL`,
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
            except Exception:
                pass

    def create_temp_table_for_file(self, view_name, filename):
        """为特定文件创建优化的工作表"""
        # ENABLE_WORK_TABLE_PERSISTENCE 已定义在 VC_BC01_constant 中，通过星号导入可用
        
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
        except Exception:
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
        # ENABLE_WORK_TABLE_PERSISTENCE 已定义在 VC_BC01_constant 中，通过星号导入可用
        
        if not ENABLE_WORK_TABLE_PERSISTENCE:
            cursor = self.connection.cursor()
            try:
                cursor.execute("SHOW TABLES LIKE 'work_%'")
                tables = cursor.fetchall()
                
                for (table_name,) in tables:
                    try:
                        self.execute_query(f"DROP TABLE IF EXISTS {table_name}")
                        print(f"✓ 清理工作表: {table_name}")
                    except Exception:
                        pass

            except mysql.connector.Error:
                pass
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass
        else:
            print("✓ 工作表已保留以供下次使用")

    # ------------------------------------------------------------------
    # 后端无关的接口（OP 脚本只使用这些）
    # ------------------------------------------------------------------
    # 没有预算键列：general_ci 排序规则下直接比较原列即可
    ci_key_columns = False

    def ci_col(self, name):
        """带预算键的列（TRANSVAL / FORMVAL / METAVAL，以及 CHK 查询的 CHKTYPE / CHKVALUE）
        做比较或排序时使用的列名。MySQL 原样返回。"""
        return name

    def ci(self, expr):
        """不区分大小写比较或排序时对表达式的包装。MySQL（general_ci 排序规则）原样返回。"""
        return expr

    def ci_literal(self, value):
        """生成与 ci(...) 比较用的 SQL 字面量（单引号翻倍转义）。"""
        return "'" + str(value).replace("'", "''") + "'"

    def insert_codelist_rows(self, table_name, rows):
        """逐行 INSERT IGNORE；返回 (inserted, duplicates)。"""
        count_inserted = 0
        count_duplicate = 0
        progress = ProgressReporter(total=len(rows), desc='CodeList')

        query_insert = (
            f'INSERT IGNORE INTO {table_name} '
            f'(`CODELISTID`, `CODE`, `VALUE_RAW`, `VALUE_EN`, `VALUE_SDTM`) '
            f'VALUES (%s, %s, %s, %s, %s);'
        )
        for row in rows:
            values_insert = [row[0], row[1], row[2], row[3], row[4]]
            self.cursor.execute(query_insert, values_insert)
            if self.cursor.rowcount > 0:
                count_inserted += 1
            else:
                count_duplicate += 1

            total = count_inserted + count_duplicate
            if total % 1000 == 0:
                self.connection.commit()
            progress.update()

        self.connection.commit()
        progress.finish()
        return count_inserted, count_duplicate

    def load_metadata_rows(self, table_name, rows):
        """
        经暂存表 + LOAD DATA 批量导入元数据；No 按顺序分配 1..n，返回最终行数。
        rows 为 11 元组 (FILENAME, ROWNUM, USUBJID, SUBJID, FIELDLBL, FIELDID,
        METAVAL, FORMVAL, DATETYPE, CODELISTID, CHKFIELDID)。
        """
        cursor = self.cursor
        connection = self.connection

        # 创建暂存表（使用AUTO_INCREMENT主键，无二级索引）
        staging_table_name = f"{table_name}_STAGING"
        staging_sql = f"""
        CREATE TABLE IF NOT EXISTS {staging_table_name} (
            No INT AUTO_INCREMENT PRIMARY KEY,
            FILENAME VARCHAR(100),
            ROWNUM INT,
            USUBJID VARCHAR(50),
            SUBJID VARCHAR(50),
            FIELDLBL VARCHAR(200),
            FIELDID VARCHAR(100),
            METAVAL TEXT,
            FORMVAL TEXT,
            DATETYPE BOOLEAN,
            CODELISTID VARCHAR(100),
            CHKFIELDID VARCHAR(100)
        ) ENGINE=InnoDB
        """
        cursor.execute(f"DROP TABLE IF EXISTS {staging_table_name}")
        cursor.execute(staging_sql)

        # 生成CSV文件用于LOAD DATA
        csv_file_path = os.path.join(SPECIFIC_PATH, f"{table_name}_staging.csv")
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            # 不写入表头，直接写入数据行（对应暂存表除了AUTO_INCREMENT主键外的所有列）
            for row in rows:
                # 转换DATETYPE为1/0（MySQL BOOLEAN）
                row_list = list(row)
                row_list[8] = 1 if row_list[8] else 0  # DATETYPE列
                csv_writer.writerow(row_list)

        # 使用LOAD DATA进行批量导入
        load_data_start = _time.perf_counter()

        # 性能优化设置（导入窗口内临时使用）
        optimization_settings = [
            "SET SESSION foreign_key_checks = 0",
            "SET SESSION unique_checks = 0",
            "SET SESSION sql_log_bin = 0",  # 如果不需要复制到从库
        ]

        for setting in optimization_settings:
            try:
                cursor.execute(setting)
            except Exception as e:
                print(f"⚠ 设置跳过: {setting}, 错误: {e}")

        # 执行LOAD DATA INFILE
        # 使用绝对路径并处理Windows路径分隔符
        csv_file_path_normalized = csv_file_path.replace('\\', '/')
        load_data_sql = f"""
        LOAD DATA LOCAL INFILE '{csv_file_path_normalized}'
        INTO TABLE {staging_table_name}
        FIELDS TERMINATED BY ','
        OPTIONALLY ENCLOSED BY '"'
        LINES TERMINATED BY '\\n'
        (FILENAME, ROWNUM, USUBJID, SUBJID, FIELDLBL, FIELDID, METAVAL, FORMVAL, DATETYPE, CODELISTID, CHKFIELDID)
        """

        cursor.execute(load_data_sql)
        connection.commit()

        # 检查导入结果
        cursor.execute(f"SELECT COUNT(*) FROM {staging_table_name}")
        imported_count = cursor.fetchone()[0]
        load_data_elapsed = _time.perf_counter() - load_data_start

        print(f"LOAD DATA完成: {imported_count} 条记录, 耗时: {load_data_elapsed:.3f}s")

        # 从暂存表转移数据到正式表（保持原有表结构和索引）
        transfer_start = _time.perf_counter()
        print("从暂存表转移数据到正式表...")

        # 清空正式表（如果需要）
        cursor.execute(f"TRUNCATE TABLE {table_name}")

        # 使用INSERT INTO ... SELECT 转移数据，手动分配顺序主键No
        # 分批转移数据以显示进度（同时手动分配No）
        cursor.execute(f"SELECT COUNT(*) FROM {staging_table_name}")
        total_staging_records = cursor.fetchone()[0]
        batch_size = 50000
        current_no = 1

        total_batches = (total_staging_records + batch_size - 1) // batch_size
        progress_transfer = ProgressReporter(total=total_batches, desc='Transfer')

        for offset in range(0, total_staging_records, batch_size):
            batch_sql = f"""
            INSERT INTO {table_name}
            (No, FILENAME, ROWNUM, USUBJID, SUBJID, FIELDLBL, FIELDID, METAVAL, FORMVAL, DATETYPE, CODELISTID, CHKFIELDID)
            SELECT
            @row_number := @row_number + 1 as No,
            FILENAME, ROWNUM, USUBJID, SUBJID, FIELDLBL, FIELDID, METAVAL, FORMVAL, DATETYPE, CODELISTID, CHKFIELDID
            FROM (SELECT @row_number := {current_no - 1}) r,
            (SELECT * FROM {staging_table_name} ORDER BY No LIMIT {batch_size} OFFSET {offset}) s
            """

            cursor.execute(batch_sql)
            current_no += batch_size
            progress_transfer.update()

        progress_transfer.finish()

        connection.commit()

        # 验证转移结果
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        final_count = cursor.fetchone()[0]
        transfer_elapsed = _time.perf_counter() - transfer_start

        print(f"数据转移完成: {final_count} 条记录, 耗时: {transfer_elapsed:.3f}s")

        # 清理暂存表和CSV文件
        try:
            cursor.execute(f"DROP TABLE {staging_table_name}")
            os.remove(csv_file_path)
        except Exception as e:
            print(f"⚠ 清理时出现警告: {e}")

        # 恢复优化设置
        restore_settings = [
            "SET SESSION foreign_key_checks = 1",
            "SET SESSION unique_checks = 1",
            "SET SESSION sql_log_bin = 1",
        ]

        for setting in restore_settings:
            try:
                cursor.execute(setting)
            except Exception as e:
                print(f"⚠ 恢复设置跳过: {setting}, 错误: {e}")

        return final_count


def DatabaseManager():
    """按 DB_BACKEND 返回数据库管理器实例（OP 脚本调用方式不变）。"""
    if DB_BACKEND_NOTICE:
        _sys.stderr.write(DB_BACKEND_NOTICE + '\n')
        _sys.stderr.flush()
    if DB_BACKEND == 'sqlite':
        from sdtm_sqlite import SQLiteDatabaseManager
        return SQLiteDatabaseManager(SQLITE_PATH, ENABLE_WORK_TABLE_PERSISTENCE)
    return MySQLDatabaseManager()
