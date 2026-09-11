"""
研究（Study）选择与设定的解決モジュール。

程序目录只描述「这台机器」（project.local.json），研究目录只描述「这个研究」
（<STUDIES_ROOT>/<STUDY_ID>/study.json）。运行时通过命令行 / 环境变量指定研究，
不再需要为每个研究修改 project.local.json。

解析顺序（研究 ID）:
    1. 显式参数（sdtm <STUDY> / run_pipeline.py --study <STUDY>）
    2. 环境变量 SDTM_STUDY
    3. project.local.json 的 DEFAULT_STUDY
    4. project.local.json 的 STUDY_ID（旧格式，向后兼容）
    5. 研究根目录下只有一个研究时自动选它
    6. 以上都没有 → StudyNotFoundError（附可选研究列表）

该模块不依赖 pandas / mysql 等重型库，控制台工具可在选定研究之前安全导入。
"""

import json
import os

STUDY_ENV = 'SDTM_STUDY'
PROJECT_CONFIG_ENV = 'PROJECT_CONFIG_PATH'
PROJECT_CONFIG_FILENAME = 'project.local.json'
STUDY_SETTINGS_FILENAME = 'study.json'
STUDIES_DIRNAME = 'studySpecific'
OPERATION_CONF_SUFFIX = '_OperationConf.xlsx'
DEFAULT_RAW_DATA_DIR = '01_RawData'

# 子进程流水线约定（原先定义在 VC_BC02_baseUtils，移到此处以便轻量导入）
PROGRESS_MARKER = '@@PG@@'
PIPELINE_ENV_KEY = 'VAPORCONE_PIPELINE'

# project.local.json 中程序层可识别的键
MACHINE_CONFIG_KEYS = ('STUDIES_ROOT_PATH', 'DEFAULT_STUDY', 'ROOT_PATH')
# 旧格式：研究层设定也写在 project.local.json 里
LEGACY_STUDY_KEYS = (
    'STUDY_ID',
    'CODELIST_TABLE_NAME',
    'METADATA_TABLE_NAME',
    'TRANSDATA_VIEW_NAME',
    'M5_PROJECT_NAME',
    'RAW_DATA_ROOT_PATH',
)
# study.json 中研究层可识别的键
STUDY_SETTING_KEYS = (
    'M5_PROJECT_NAME',
    'RAW_DATA_DIR',
    'RAW_DATA_ROOT_PATH',
    'CODELIST_TABLE_NAME',
    'METADATA_TABLE_NAME',
    'TRANSDATA_VIEW_NAME',
)


class StudyNotFoundError(RuntimeError):
    """无法确定研究，或研究目录不存在。"""

    def __init__(self, message, available=None):
        super().__init__(message)
        self.available = list(available or [])


def program_root():
    """程序目录（本文件所在目录）。"""
    return os.path.dirname(os.path.abspath(__file__))


def project_config_path(base_dir=None):
    return os.getenv(PROJECT_CONFIG_ENV) or os.path.join(
        base_dir or program_root(), PROJECT_CONFIG_FILENAME
    )


def load_project_config(base_dir=None):
    """读取 project.local.json；不存在或损坏时返回空 dict。"""
    path = project_config_path(base_dir)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError) as exc:
        print(f'[sdtm_study] Failed to load {path}: {exc}. Using defaults.')
        return {}
    return data if isinstance(data, dict) else {}


def get_studies_root(base_dir=None, config=None):
    """研究根目录。STUDIES_ROOT_PATH > <ROOT_PATH or 程序目录>/studySpecific。"""
    if config is None:
        config = load_project_config(base_dir)
    root = config.get('STUDIES_ROOT_PATH')
    if root:
        return os.path.normpath(root)
    parent = config.get('ROOT_PATH') or base_dir or program_root()
    return os.path.normpath(os.path.join(parent, STUDIES_DIRNAME))


def is_study_dir(path):
    """含 <ID>_OperationConf.xlsx 或 study.json 的目录才算研究目录。"""
    if not os.path.isdir(path):
        return False
    study_id = os.path.basename(path)
    return (
        os.path.isfile(os.path.join(path, study_id + OPERATION_CONF_SUFFIX))
        or os.path.isfile(os.path.join(path, STUDY_SETTINGS_FILENAME))
    )


def list_studies(base_dir=None, config=None):
    """列出研究根目录下的研究 ID（按名称排序）。"""
    root = get_studies_root(base_dir, config)
    if not os.path.isdir(root):
        return []
    return sorted(
        name for name in os.listdir(root)
        if not name.startswith(('.', '_')) and is_study_dir(os.path.join(root, name))
    )


def match_study_id(candidate, available):
    """大小写不敏感地匹配研究 ID；无匹配返回 None。"""
    if not candidate:
        return None
    lowered = candidate.lower()
    for study_id in available:
        if study_id.lower() == lowered:
            return study_id
    return None


def resolve_study_id(explicit=None, base_dir=None, config=None):
    """按解析顺序确定研究 ID。失败时抛出 StudyNotFoundError。"""
    if config is None:
        config = load_project_config(base_dir)
    available = list_studies(base_dir, config)
    root = get_studies_root(base_dir, config)

    candidates = [
        ('参数', explicit),
        ('环境变量 ' + STUDY_ENV, os.getenv(STUDY_ENV)),
        ('project.local.json DEFAULT_STUDY', config.get('DEFAULT_STUDY')),
        ('project.local.json STUDY_ID', config.get('STUDY_ID')),
    ]
    for source, value in candidates:
        if not value:
            continue
        matched = match_study_id(value, available)
        if matched:
            return matched
        raise StudyNotFoundError(
            f'研究 "{value}"（来源: {source}）在研究根目录中不存在: {root}',
            available,
        )

    if len(available) == 1:
        return available[0]

    if not available:
        raise StudyNotFoundError(
            f'研究根目录中没有任何研究: {root}\n'
            f'请在 project.local.json 中设置 STUDIES_ROOT_PATH，或在该目录下创建 <STUDY_ID>/<STUDY_ID>_OperationConf.xlsx',
            available,
        )
    raise StudyNotFoundError(
        '未指定研究。请使用 sdtm <STUDY>、run_pipeline.py --study <STUDY>、'
        f'环境变量 {STUDY_ENV}，或在 project.local.json 中设置 DEFAULT_STUDY',
        available,
    )


def format_available(available):
    if not available:
        return '  （无可用研究）'
    return '\n'.join(f'  - {s}' for s in available)


def load_study_settings(study_id, base_dir=None, config=None):
    """
    汇总某个研究的全部设定（含推导默认值）。

    返回 dict:
        STUDY_ID, STUDIES_ROOT_PATH, STUDY_PATH, ROOT_PATH,
        CODELIST_TABLE_NAME, METADATA_TABLE_NAME, TRANSDATA_VIEW_NAME,
        M5_PROJECT_NAME, RAW_DATA_ROOT_PATH, STUDY_SETTINGS_PATH
    优先级: study.json > project.local.json 旧格式（仅当其 STUDY_ID 与本研究一致） > 推导默认值
    """
    if config is None:
        config = load_project_config(base_dir)
    studies_root = get_studies_root(base_dir, config)
    study_path = os.path.join(studies_root, study_id)

    settings = {
        'STUDY_ID': study_id,
        'STUDIES_ROOT_PATH': studies_root,
        'STUDY_PATH': study_path,
        'ROOT_PATH': config.get('ROOT_PATH') or base_dir or program_root(),
        'CODELIST_TABLE_NAME': f'VC05_{study_id}_CODELIST',
        'METADATA_TABLE_NAME': f'VC05_{study_id}_METADATA',
        'TRANSDATA_VIEW_NAME': f'VC05_{study_id}_TRANSDATA',
        'M5_PROJECT_NAME': study_id,
        'RAW_DATA_ROOT_PATH': os.path.join(study_path, DEFAULT_RAW_DATA_DIR),
        'STUDY_SETTINGS_PATH': os.path.join(study_path, STUDY_SETTINGS_FILENAME),
    }

    # 旧格式 project.local.json（只在它描述的就是本研究时采用）
    if (config.get('STUDY_ID') or '').lower() == study_id.lower():
        for key in LEGACY_STUDY_KEYS:
            if key != 'STUDY_ID' and config.get(key):
                settings[key] = config[key]

    # 研究目录内的 study.json
    study_file = settings['STUDY_SETTINGS_PATH']
    if os.path.isfile(study_file):
        try:
            with open(study_file, 'r', encoding='utf-8') as f:
                overrides = json.load(f)
        except (OSError, ValueError) as exc:
            print(f'[sdtm_study] Failed to load {study_file}: {exc}. Ignoring.')
            overrides = {}
        if isinstance(overrides, dict):
            for key in STUDY_SETTING_KEYS:
                if overrides.get(key):
                    settings[key] = overrides[key]
            if overrides.get('RAW_DATA_DIR') and not overrides.get('RAW_DATA_ROOT_PATH'):
                settings['RAW_DATA_ROOT_PATH'] = os.path.normpath(
                    os.path.join(study_path, overrides['RAW_DATA_DIR'])
                )

    settings.pop('RAW_DATA_DIR', None)
    return settings
