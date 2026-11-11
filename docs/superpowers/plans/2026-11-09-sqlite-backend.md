# SQLite 后端替换 MySQL 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** OP02/OP03/OP04 改用 Python 自带的 SQLite（可切回 MySQL），在所有现有研究上输出与 MySQL 逐字节一致。

**Architecture:** `DatabaseManager()` 变成工厂，按 `project.local.json` 的 `DB_BACKEND` 返回 `MySQLDatabaseManager`（现有类改名）或 `SQLiteDatabaseManager`（新文件 `pipeline/sdtm_sqlite.py`）。OP 脚本里直接写的 MySQL 专用 SQL（`INSERT IGNORE`、`LOAD DATA`、`SET SESSION`）收进管理器方法。MySQL `utf8mb4_general_ci` 的"不区分大小写 + 忽略末尾空格"用 Python 函数 `mysql_ci_key()` 复刻：大表上预先算好 `_K` 键列用于连接和非空判断，结果集排序与字面量比较用注册到 SQLite 的 `ci_key()` 函数。

**Tech Stack:** Python 3.11+ 标准库 `sqlite3`（实测 SQLite 3.50.4）、pandas、pytest；MySQL 5.7.44 仅作对照基准。

**Spec:** 无单独规格文档，决定来自 2026-11-09 的讨论，摘要见 memory `mysql-to-sqlite-migration.md`。要点：
- 换 SQLite（不选 DuckDB）；通过开关保留 MySQL；过渡期默认仍是 MySQL，对比全部通过后才切默认值。
- **完全复刻 MySQL 行为**：CODELIST 匹配不区分大小写（CIRCULATE 的 `COVAL`：FORMVAL `YES` 对 CODE `Yes`）；CHK 查询 `ORDER BY CHKTYPE, CHKVALUE` 按不区分大小写排序（`--SEQ` 用稳定排序，行序会影响结果）。
- 验收：DEMO、ENSEMBLE、ENSEMBLE2、COSMOS_GC、CIRCULATE 五个研究，两种后端 `run all` 的输出逐文件一致（`m5.zip` 比较成员内容）。

## Global Constraints

- MySQL 路径的输出在每个任务后都必须不变（DEMO 用 `tests/compare_runs.py` 对比上一轮）。
- `pipeline/` 保持扁平，不改现有模块名；新文件 `pipeline/sdtm_sqlite.py` 只依赖标准库，不 import 任何 `VC_*` 模块（避免循环依赖，与 `sdtm_study.py` 同类）。
- `mysql-connector-python` 在 SQLite 后端下不得被 import（最终变为可选依赖）。
- 配置键：`DB_BACKEND`（`"mysql"` | `"sqlite"`），`SQLITE_PATH`（可选，默认 `<STUDY_PATH>/<STUDY_ID>_work.sqlite`）。不写死研究 id 或路径。
- 字符串优先：从库里读出的值是 `str` 或 `None`，不做数值或日期转换；CSV 仍是 `utf-8-sig`。
- 测试不依赖 MySQL；需要 MySQL 的核对脚本做成普通脚本（同 `tests/test_opertypes.py` 的做法，文件名不以 `test_` 开头）。
- 本次**不修** MySQL 路径上的已知隐患（`CHKFIELDID` 末尾 `\r`、`LOAD DATA` 把 `\` 当转义符）；SQLite 路径上这两处自然正确。`CHKFIELDID` 未被任何查询使用，不影响对比。

## Review Focus

1. 同一 ROWNUM、同一 CHKTYPE 下有大小写混排的值（`Grade II` / `chylous ascites`）→ 行序与 MySQL 相同。测试在 Task 5。
2. FORMVAL 与 CODE 只差大小写或末尾空格（`YES` / `Yes `）→ 照样拿到翻译值；CODELIST 里只差大小写的两行 → 只保留第一行，和 MySQL 主键冲突时的结果一样。测试在 Task 4。
3. OTHERDETAILS 连接里，数据的 METAVAL 与工作簿 OTHERVAL 只差大小写 → 照样连上。测试在 Task 5。
4. `ENABLE_ORDER_BY = False` 时，SQLite 的 GROUP BY 不会自动排序 → 主查询行序仍按 ROWNUM 升序（与 MySQL 5.7 的隐式排序一致）。测试在 Task 5。
5. 值里含反斜杠、双引号、换行、emoji 等 BMP 以外的字符 → 装入 SQLite 后原样不变；BMP 以外字符的键与 MySQL 一样都视为相等（U+FFFD）。测试在 Task 2、Task 4。

---

### Task 1: 对比工具 + MySQL SQL 改成通用写法

**Files:**
- Create: `tests/compare_runs.py`
- Modify: `pipeline/VC_BC02_baseUtils.py:840-863`（`create_transdata_view`）
- Modify: `pipeline/VC_OP04_format.py:121-258`（两个查询构建函数）及 `:367-371`、`:411-414`（`max(if(...))` 片段）

**Interfaces:**
- Produces: `python tests/compare_runs.py <dirA> <dirB>` 和 `python tests/compare_runs.py --study <STUDY> [--root <STUDIES_ROOT>]`；全部一致退出码 0，否则打印差异文件清单并退出 1。

- [ ] **Step 1: 写 `tests/compare_runs.py`**
  - 两目录模式：递归比较两边所有 `*.csv`（逐字节）和 `*.zip`（成员名集合相同，且每个成员内容逐字节相同，忽略 zip 时间戳）；只在一边存在的文件也算差异。忽略 `*.log`。
  - `--study` 模式：对研究目录下 `02_Cleaning`…`06_Inputpackage` 每个阶段目录，取名字末尾时间戳（`-YYYYMMDDHHMMSS`）最新的两个子文件夹，用两目录模式比较；某阶段不足两个文件夹就报告并算失败。`--root` 缺省时从 `project.local.json`（或 `PROJECT_CONFIG_PATH`）的 `STUDIES_ROOT_PATH` 取。
  - 输出每个阶段一行 `OK` / `DIFF n files`，最后一行 `ALL IDENTICAL` 或 `DIFFERENCES FOUND`。

- [ ] **Step 2: 建立 DEMO 的 MySQL 基准**

```bash
python -c "import json;json.dump({'STUDIES_ROOT_PATH':'examples/studies'},open('C:/Temp/sdtm-demo.json','w'))"
PROJECT_CONFIG_PATH=C:/Temp/sdtm-demo.json python sdtm.py DEMO run all
```
Expected: 7 步全部成功，输出与 `examples/studies/DEMO/README.md` 所列一致。

- [ ] **Step 3: 改成通用 SQL（行为不变）**
  - 视图：`IF(ISNULL(c.VALUE_EN), m.FORMVAL, c.VALUE_EN)` → `CASE WHEN c.VALUE_EN IS NULL THEN m.FORMVAL ELSE c.VALUE_EN END`；`IF(ISNULL(c.VALUE_SDTM),'',c.VALUE_SDTM)` → `COALESCE(c.VALUE_SDTM, '')`。`CREATE OR REPLACE ... DEFINER ...` 保持不动（这是 MySQL 专用的 DDL，Task 3 起只留在 MySQL 类里）。
  - OP04 所有 `max(if((<cond>),<col>,NULL))` → `max(CASE WHEN <cond> THEN <col> END)`。

- [ ] **Step 4: 再跑 DEMO 并对比**

Run: `PROJECT_CONFIG_PATH=C:/Temp/sdtm-demo.json python sdtm.py DEMO run all && python tests/compare_runs.py --study DEMO --root examples/studies`
Expected: `ALL IDENTICAL`

- [ ] **Step 5: `pytest -q` 全绿后提交**

```bash
git add tests/compare_runs.py pipeline/VC_BC02_baseUtils.py pipeline/VC_OP04_format.py
git commit -m "refactor(db): portable CASE/COALESCE SQL; add run-folder comparison tool"
```

---

### Task 2: `mysql_ci_key()` 及其与 MySQL 的一致性核对

**Files:**
- Create: `pipeline/sdtm_sqlite.py`（本任务只放 `mysql_ci_key`）
- Create: `tests/test_sqlite_backend.py`
- Create: `tests/parity_mysql_ci.py`（普通脚本，需要 MySQL）

**Interfaces:**
- Produces: `mysql_ci_key(value: str | None) -> str | None`。两个字符串在 MySQL `utf8mb4_general_ci` 下相等，当且仅当它们的键相等；按键的码位顺序排序，等于 MySQL 的 `ORDER BY`（相等的值之间次序不保证）。

- [ ] **Step 1: 写失败测试 `tests/test_sqlite_backend.py`**

```python
from sdtm_sqlite import mysql_ci_key as k

def test_ci_key_case_and_trailing_space():
    assert k('Yes') == k('YES') == k('yes  ')
    assert k(None) is None
    assert k('   ') == k('') == ''
    assert k(' a') != k('a')            # 只忽略末尾空格，不忽略开头

def test_ci_key_latin_accents_fold():
    assert k('é') == k('E') and k('Ñ') == k('n')

def test_ci_key_japanese_not_folded():
    assert k('ガ') != k('カ')
    assert k('あ') != k('ア')

def test_ci_key_fullwidth_case_folds_but_not_width():
    assert k('ａ') == k('Ａ')
    assert k('Ａ') != k('A')

def test_ci_key_non_bmp_all_equal():
    assert k('😀') == k('😃')

def test_ci_key_order_matches_mysql():
    vals = ['chylous ascites', 'Grade II', 'anemia']
    assert sorted(vals, key=k) == ['anemia', 'chylous ascites', 'Grade II']
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest -q tests/test_sqlite_backend.py`
Expected: FAIL，`ModuleNotFoundError: sdtm_sqlite`

- [ ] **Step 3: 实现 `mysql_ci_key`**

算法（测试没有完全决定它，所以写在这里）：
1. `None` 原样返回；先 `rstrip(' ')`（只去空格，即 PAD SPACE）。
2. 逐字符：码位 > 0xFFFF → `'\uFFFD'`；码位在 U+00C0–U+024F（拉丁扩展）→ 取 `unicodedata.normalize('NFD', ch)[0]` 去掉重音；然后 `u = ch.upper()`，`len(u) == 1` 才用 `u`，否则保留原字符（如 `ß`）。
3. 不对其他区块（假名、汉字、全角）做 NFD，否则 `ガ` 会被折成 `カ`。

- [ ] **Step 4: 运行确认通过**

Run: `pytest -q tests/test_sqlite_backend.py`
Expected: PASS

- [ ] **Step 5: 写 `tests/parity_mysql_ci.py` 并在真实表上跑**

对数据库里每个 `vc05_*_metadata` 和 `vc05_*_codelist` 表，取 `FORMVAL`、`METAVAL`、`CODE`、`VALUE_EN`、`CODELISTID` 的全部不同值（`SELECT DISTINCT BINARY col`）：
- **分组核对**：用 MySQL 计算 `SELECT col, COUNT(DISTINCT BINARY col) ... GROUP BY col`，与按 `mysql_ci_key` 分组的结果比较，每组的成员集合必须完全相同。
- **排序核对**：把 MySQL `ORDER BY col` 的结果映射成键序列，必须是非降序。
- 连接参数从 BC01 的 `DB_*` 常量取；任何不一致打印前 20 例，最后退出 1。

Run: `python tests/parity_mysql_ci.py`
Expected: 每个表、每列都是 `OK`，最后一行 `PARITY OK`。如有不一致，修改 Step 3 的算法并补一条单元测试，直到通过。

- [ ] **Step 6: 提交**

```bash
git add pipeline/sdtm_sqlite.py tests/test_sqlite_backend.py tests/parity_mysql_ci.py
git commit -m "feat(db): mysql_ci_key reproducing utf8mb4_general_ci, with MySQL parity check"
```

---

### Task 3: 后端开关，MySQL 专用 SQL 收进管理器

**Files:**
- Modify: `pipeline/VC_BC01_constant.py:20`（删掉顶层 `import mysql.connector` / `errorcode`），`:69-72` 附近（加两个常量）
- Modify: `pipeline/VC_BC02_baseUtils.py:669-1060`（类改名 + 工厂 + 新方法）
- Modify: `pipeline/VC_OP02_insertCodeList.py:56-82`
- Modify: `pipeline/VC_OP03_insertMetadata.py:57-280`（建 staging 表、写 CSV、LOAD DATA、转移、恢复设置这一整段）

**Interfaces:**
- Produces (BC01):
  - `DB_BACKEND: str = (_PROJECT_CONFIG.get('DB_BACKEND') or 'mysql').lower()`，不是 `mysql`/`sqlite` 时报错并 `sys.exit(2)`
  - `SQLITE_PATH: str` = 配置的 `SQLITE_PATH`，缺省 `os.path.join(SPECIFIC_PATH, f'{STUDY_ID}_work.sqlite')`
- Produces (BC02)：`DatabaseManager() -> MySQLDatabaseManager | SQLiteDatabaseManager`（工厂函数，名字不变，OP 脚本的调用不用改）。两个类都提供以下公共接口，OP 脚本只能用这些：
  - 现有的：`connect()`、`disconnect()`、`connection`、`cursor`、`execute_query(sql, values=None)`、`create_codelist_table(name)`、`create_metadata_table(name)`、`create_transdata_view(view, md, cl)`、`create_performance_indexes(md) -> int`、`create_temp_table_for_file(view, filename) -> str | None`、`cleanup_work_tables()`
  - 新增 `insert_codelist_rows(table: str, rows: list[tuple[str, str, str, str, str]]) -> tuple[int, int]`：返回 `(inserted, duplicates)`；与主键冲突的行跳过（MySQL：现有 `INSERT IGNORE` 逻辑原样搬入）
  - 新增 `load_metadata_rows(table: str, rows: list[tuple]) -> int`：`rows` 就是 OP03 现在构造的 11 元组 `(FILENAME, ROWNUM, USUBJID, SUBJID, FIELDLBL, FIELDID, METAVAL, FORMVAL, DATETYPE, CODELISTID, CHKFIELDID)`；按顺序分配 `No = 1..n`，返回最终行数（MySQL：现有 staging CSV + `LOAD DATA` + 分批转移逻辑原样搬入，包括 CSV 的写法）
  - 新增 `ci_col(name: str) -> str`：视图里有预算键的列（`TRANSVAL`、`FORMVAL`）做比较时用的列名；MySQL 原样返回 `name`
  - 新增 `ci(expr: str) -> str`：任意表达式做不区分大小写比较或排序时的包装；MySQL 原样返回 `expr`
  - 新增 `ci_literal(value: str) -> str`：生成与 `ci(...)` 比较用的 SQL 字面量；MySQL 返回 `'<value>'`（单引号翻倍转义）
  - 新增属性 `implicit_group_order: bool`：MySQL 为 `True`

- [ ] **Step 1: 改 BC01/BC02**：现有类改名为 `MySQLDatabaseManager`，`mysql.connector` 和 `errorcode` 改在 BC02 里 `try: import ... except ImportError: mysql = None`；`MySQLDatabaseManager.connect()` 遇到 `mysql is None` 时报"未安装 mysql-connector-python，或在 project.local.json 设 DB_BACKEND=sqlite"并退出。工厂函数遇到 `sqlite` 时在函数内 `from sdtm_sqlite import SQLiteDatabaseManager`（本任务里这个类还不存在：先让工厂遇到 `sqlite` 时抛 `NotImplementedError`，Task 4 再接上）。

- [ ] **Step 2: OP02、OP03 改为调用 `insert_codelist_rows` 和 `load_metadata_rows`**：摘要输出（成功插入数、重复跳过数、LOAD DATA 行数和耗时）保持原样。

- [ ] **Step 3: 验证**

Run: `python -m py_compile sdtm.py app/*.py pipeline/*.py && pytest -q && PROJECT_CONFIG_PATH=C:/Temp/sdtm-demo.json python sdtm.py DEMO run all && python tests/compare_runs.py --study DEMO --root examples/studies`
Expected: 测试全绿，`ALL IDENTICAL`

- [ ] **Step 4: 提交**

```bash
git add pipeline/VC_BC01_constant.py pipeline/VC_BC02_baseUtils.py pipeline/VC_OP02_insertCodeList.py pipeline/VC_OP03_insertMetadata.py
git commit -m "refactor(db): DatabaseManager factory with DB_BACKEND; move MySQL-only SQL into the manager"
```

---

### Task 4: `SQLiteDatabaseManager`

**Files:**
- Modify: `pipeline/sdtm_sqlite.py`
- Modify: `pipeline/VC_BC02_baseUtils.py`（工厂接上 SQLite）
- Test: `tests/test_sqlite_backend.py`

**Interfaces:**
- Consumes: Task 2 的 `mysql_ci_key`；Task 3 的接口清单（必须一个不少地实现）。
- Produces: `SQLiteDatabaseManager(path: str, keep_work_tables: bool)`，`implicit_group_order = False`；`ci_col(n)` 返回 `f'{n}_K'`；`ci(e)` 返回 `f'ci_key({e})'`；`ci_literal(v)` 返回 `mysql_ci_key(v)` 的 SQL 字面量。工厂用 `SQLiteDatabaseManager(SQLITE_PATH, ENABLE_WORK_TABLE_PERSISTENCE)` 创建。

表结构（列名与 MySQL 相同，另加 `_K` 键列，装数据时用 `mysql_ci_key` 在 Python 里算好）：
- CODELIST：`CODELISTID, CODE, VALUE_RAW, VALUE_EN, VALUE_SDTM, CODELISTID_K, CODE_K, VALUE_EN_K`，`UNIQUE(CODELISTID_K, CODE_K)`，插入用 `INSERT OR IGNORE`（复刻 MySQL 主键在不区分大小写时的冲突）
- METADATA：MySQL 的 12 列（`ROWNUM`、`DATETYPE`、`No` 为 INTEGER），另加 `CODELISTID_K, FORMVAL_K, METAVAL_K`
- 视图 TRANSDATA：MySQL 视图的 12 列，另加 `FORMVAL_K`、`METAVAL_K` 和 `TRANSVAL_K = CASE WHEN c.VALUE_EN IS NULL THEN m.FORMVAL_K ELSE c.VALUE_EN_K END`；连接条件 `m.CODELISTID_K = c.CODELISTID_K AND m.FORMVAL_K = c.CODE_K`；每次先 `DROP VIEW IF EXISTS` 再建
- `connect()`：`sqlite3.connect(path)`，`PRAGMA journal_mode=OFF`、`synchronous=OFF`，注册 `create_function('ci_key', 1, mysql_ci_key, deterministic=True)`；`cursor` 是 `sqlite3.Cursor`（OP04 用到的 `execute` / `fetchall` / `description` 与 MySQL 的 cursor 用法相同）
- 索引：`create_performance_indexes` 建 `(FILENAME, FIELDID)`、`(FILENAME, ROWNUM, SUBJID)`、`(ROWNUM)`，返回新建的个数；工作表沿用 `work_<filename>` 命名，查询表名用 `sqlite_master`
- 运行结束不删库文件（OP02→OP03→OP04 是三个进程，靠这个文件传递数据）
- 不实现 `analyze_query_performance`：它是 MySQL 的 EXPLAIN 调试工具，仓库里没有调用方；`table_exists`、`index_exists` 只作为内部辅助

- [ ] **Step 1: 写失败测试**（都用 `tmp_path` 下的库文件）

```python
def _db(tmp_path):
    from sdtm_sqlite import SQLiteDatabaseManager
    db = SQLiteDatabaseManager(str(tmp_path / 'w.sqlite'), keep_work_tables=False); db.connect(); return db

def test_codelist_case_duplicate_ignored(tmp_path):
    db = _db(tmp_path); db.create_codelist_table('CL')
    assert db.insert_codelist_rows('CL', [('COVAL','Yes','','yes-en',''), ('COVAL','YES','','dup','')]) == (1, 1)

def test_view_translates_case_and_space_insensitively(tmp_path):
    db = _db(tmp_path); db.create_codelist_table('CL'); db.create_metadata_table('MD')
    db.insert_codelist_rows('CL', [('COVAL','Yes ','','YES-EN','Y')])
    db.load_metadata_rows('MD', [('F',1,'U1','S1','lbl','COVAL','YES','YES',0,'COVAL',''),
                                 ('F',2,'U1','S1','lbl','COVAL','No','No',0,'COVAL','')])
    db.create_transdata_view('TV','MD','CL')
    rows = db.cursor.execute('SELECT ROWNUM, TRANSVAL, SDTMVAL FROM TV ORDER BY ROWNUM').fetchall()
    assert rows == [(1,'YES-EN','Y'), (2,'No','')]

def test_metadata_values_round_trip(tmp_path):
    db = _db(tmp_path); db.create_metadata_table('MD')
    odd = 'a\\b "q", line1\nline2 😀'
    assert db.load_metadata_rows('MD', [('F',1,'U1','S1','l','X',odd,odd,0,'','')]) == 1
    assert db.cursor.execute('SELECT No, METAVAL, FORMVAL, CHKFIELDID FROM MD').fetchall() == [(1, odd, odd, '')]
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest -q tests/test_sqlite_backend.py`
Expected: 新增的 3 个测试 FAIL（`ImportError: SQLiteDatabaseManager`）

- [ ] **Step 3: 实现 `SQLiteDatabaseManager` 并接上工厂**

- [ ] **Step 4: 运行确认通过，并检查没有 import mysql**

Run: `pytest -q && python -c "import sys; sys.path.insert(0,'pipeline'); import sdtm_sqlite; assert 'mysql' not in sys.modules"`
Expected: 全绿，无输出

- [ ] **Step 5: 提交**

```bash
git add pipeline/sdtm_sqlite.py pipeline/VC_BC02_baseUtils.py tests/test_sqlite_backend.py
git commit -m "feat(db): SQLiteDatabaseManager replicating utf8mb4_general_ci matching"
```

---

### Task 5: OP04 查询改用方言钩子；DEMO 在两种后端下对比

**Files:**
- Modify: `pipeline/VC_OP04_format.py:121-258`（`build_optimized_chk_query`、`build_optimized_main_query`）
- Test: `tests/test_sqlite_backend.py`

**Interfaces:**
- Consumes: Task 3/4 的 `db.ci_col`、`db.ci`、`db.ci_literal`、`db.implicit_group_order`。
- Produces: `build_optimized_main_query(db, fileName, fields, transdata_source, enable_order_by=True) -> str`（**新增第一个参数 `db`**，调用处同步修改）；`build_optimized_chk_query` 签名不变（已有 `db`）。

改写规则（MySQL 下生成的 SQL 与 Task 1 后的结果在语义上完全相同）：
- `` `TRANSVAL` <> '' `` → `` {db.ci_col('TRANSVAL')} <> '' ``；`` `FORMVAL` <> '' `` → `` {db.ci_col('FORMVAL')} <> '' ``
- OTHERDETAILS 连接里的 `` t.`METAVAL` = '<otherVal>' `` → `` {db.ci('t.`METAVAL`')} = {db.ci_literal(otherVal)} ``
- CHK 的 `ORDER BY t.ROWNUM, t.CHKTYPE, t.CHKVALUE` → `` ORDER BY t.`ROWNUM`, {db.ci('t.`CHKTYPE`')}, {db.ci('t.`CHKVALUE`')} ``
- （2026-11-11 之后）上面两条在 SQLite 上已改为预算键列：子查询 `t` 带出 `CHKTYPE_K` / `CHKVALUE_K` / `METAVAL_K`，连接和排序用 `` t.`{db.ci_col(...)}` ``，OP04 不再调用 `db.ci`；MySQL 的查询文本不变
- 主查询：`enable_order_by` 为真 → `` ORDER BY `ROWNUM` ``；为假且 `not db.implicit_group_order` → `ORDER BY` 与 GROUP BY 相同的列；为假且是 MySQL → 不加
- `FIELDID = '<x>'` 不包装：两边都来自同一个工作簿的键，审计中没有只差大小写的 FIELDID

- [ ] **Step 1: 写失败测试**（复用 Task 4 的 `_db`；在库里造一个文件 `F`，含 CHK 字段，直接调用构建函数并执行生成的 SQL）

```python
def test_chk_order_case_insensitive(tmp_path): ...
    # ROWNUM=1 同一 CHKTYPE 下有 'chylous ascites' 和 'Grade II'
    # 断言 CHKVALUE 列顺序 == ['chylous ascites', 'Grade II']

def test_otherdetails_metaval_case_insensitive(tmp_path): ...
    # 工作簿 OTHERVAL='Other'，数据 METAVAL='OTHER' → OTHERDETAILS 列有值

def test_main_query_sorted_without_order_by(tmp_path): ...
    # 按 ROWNUM 3,1,2 的顺序装入；enable_order_by=False → 结果按 ROWNUM 1,2,3 排列
```
三个测试的参数（`select_fieldIDs`、`case_fieldIDs`、`other_fields`、`fieldID_otherVal`、`file_param`）照 `_run_format` 里组装它们的方式（`VC_OP04_format.py:330-385`）构造最小例子。

- [ ] **Step 2: 运行确认失败**

Run: `pytest -q tests/test_sqlite_backend.py -k "chk_order or otherdetails or without_order_by"`
Expected: FAIL（未经 `ci` 包装时排序和连接结果不对；`build_optimized_main_query` 也还没有 `db` 参数）

- [ ] **Step 3: 按上面的改写规则修改两个构建函数**

- [ ] **Step 4: 单元测试 + MySQL 路径不变**

Run: `pytest -q && PROJECT_CONFIG_PATH=C:/Temp/sdtm-demo.json python sdtm.py DEMO run all && python tests/compare_runs.py --study DEMO --root examples/studies`
Expected: 全绿，`ALL IDENTICAL`

- [ ] **Step 5: DEMO 用 SQLite 跑，并与刚才的 MySQL 结果对比**

```bash
python -c "import json;json.dump({'STUDIES_ROOT_PATH':'examples/studies','DB_BACKEND':'sqlite'},open('C:/Temp/sdtm-demo-sqlite.json','w'))"
PROJECT_CONFIG_PATH=C:/Temp/sdtm-demo-sqlite.json python sdtm.py DEMO run all
python tests/compare_runs.py --study DEMO --root examples/studies
```
Expected: `ALL IDENTICAL`；`examples/studies/DEMO/DEMO_work.sqlite` 生成，`git status` 里看不到它（已被 `*.sqlite` 忽略）。

- [ ] **Step 6: 提交**

```bash
git add pipeline/VC_OP04_format.py tests/test_sqlite_backend.py
git commit -m "feat(op04): dialect hooks for case-insensitive compare/order; SQLite output matches MySQL on DEMO"
```

---

### Task 6: 真实研究上的对比（不改代码）

**Files:** 无代码改动；结果追加到 memory `mysql-to-sqlite-migration.md`。

- [ ] **Step 1: 确认 SDTM-Studies 会忽略库文件**：`C:\Local\iTMS\SDTM-Studies\.gitignore` 若没有 `*.sqlite`，加上并在 SDTM-Studies 仓库里单独提交。

- [ ] **Step 2: 按顺序对 ENSEMBLE、ENSEMBLE2、COSMOS_GC、CIRCULATE 各做一轮**：用真实的 `project.local.json`，再准备一份临时配置（`DB_BACKEND=sqlite`，其余相同），每个研究依次执行：

```bash
python sdtm.py <S> run all                                    # MySQL
PROJECT_CONFIG_PATH=C:/Temp/sdtm-sqlite.json python sdtm.py <S> run all   # SQLite
python tests/compare_runs.py --study <S>
```
Expected: 每个研究都是 `ALL IDENTICAL`。记录每个研究两种后端 OP02–OP04 的耗时（CIRCULATE 预计 OP04 从约 48 秒降到 10 秒以内）。

- [ ] **Step 3: 出现差异时**：先确认差异是否只是"不区分大小写时相等的值之间的次序"（MySQL 本身对这种情况也不保证次序）。是 → 在 memory 里逐例记录并请用户确认可以接受；不是 → 回到相应任务补测试并修正，然后重跑这一步。

- [ ] **Step 4: 清理**：这次对比产生的时间戳输出文件夹按 memory `followups-2026-10-26` 中输出整理的约定处理，或交给用户决定是否删除；不要自行删除。

---

### Task 7: 默认值切到 SQLite，更新文档

**Files:**
- Modify: `pipeline/VC_BC01_constant.py`（`DB_BACKEND` 缺省值改为 `'sqlite'`）
- Modify: `requirements.txt`（删除 `mysql-connector-python`），Create: `requirements-mysql.txt`（`mysql-connector-python==9.4.0`）
- Modify: `README.md`、`README_CN.md`、`CLAUDE.md`、`docs/getting-started.md`、`docs/architecture.md`、`docs/configuration.md`、`docs/AGENT_KNOWLEDGE.md`、`examples/studies/DEMO/README.md`

- [ ] **Step 1: 改默认值和依赖**；`pip uninstall -y mysql-connector-python` 之后，跑 `pytest -q`，并在 SQLite 后端下跑一次 DEMO `run all`
Expected: 全绿；DEMO 成功（证明不装 MySQL 驱动也能跑通）。完成后再装回驱动。

- [ ] **Step 2: 改文档**：安装步骤里不再需要 MySQL；新增配置项 `DB_BACKEND` / `SQLITE_PATH` 的说明（写在 `docs/configuration.md`）；"如何切回 MySQL"一段（`pip install -r requirements-mysql.txt` + `"DB_BACKEND": "mysql"`）；CLAUDE.md 里"需要运行中的 MySQL"那句改成"默认 SQLite，无需数据库服务"，并把 "MySQL 5.7 compatibility" 一条改成"两种后端都必须保持 utf8mb4_general_ci 的匹配语义（见 `sdtm_sqlite.mysql_ci_key`）"。用 `grep -rn -i mysql` 确认剩下的提及都是关于可选 MySQL 后端的。

- [ ] **Step 3: 提交**

```bash
git add -A pipeline/VC_BC01_constant.py requirements.txt requirements-mysql.txt README.md README_CN.md CLAUDE.md docs examples/studies/DEMO/README.md
git commit -m "feat(db): default to SQLite; MySQL becomes optional"
```
- [ ] **Step 4: 更新 memory**：`mysql-to-sqlite-migration.md` 标为已完成；`demo-study-and-local-mysql.md` 改为"默认不需要 MySQL"。
