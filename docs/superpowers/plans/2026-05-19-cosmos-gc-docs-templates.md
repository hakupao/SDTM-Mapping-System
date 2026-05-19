# COSMOS_GC 文档体系模板套件 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `studySpecific/COSMOS_GC/20_Doc/` 造出 9 个文件（1 输入档案 + 1 模板 README + 7 模板），与既有 `_BACKGROUND_INTERNAL.md` / `_BC05_TO_DOCS_AGENT_GUIDE.md` 组成三层约束，让 agent 凭 protocol+config+code 稳定生成 00-06 文档。

**Architecture:** 三层约束 = 「为什么」(背景) + 「怎么做」(guide) + 「长什么样」(templates)。输入档案是 study-specific 单一事实源；7 份模板各对应一份交付物，含固定章节 + 占位符 + 行内护栏。

**Tech Stack:** Markdown 模板 + `{{...}}` 占位符 + `<!-- BEGIN/END -->` 块标记 + `<!-- RULE-GUARD §x.y -->` 护栏 + ripgrep 做验收。

**Git commit policy:** 首次 commit 前必须征得用户明确同意；同意后同一会话内可连续 commit；每个 task 末尾的 commit 步骤如未获批可跳过，最后一次性合并提交。

---

## File Structure

全部置于 `studySpecific/COSMOS_GC/20_Doc/`：

| # | 文件 | 角色 | 单一职责 |
|---|---|---|---|
| F1 | `_STUDY_INPUT_PROFILE.md` | 输入档案 | 研究特异数据的唯一来源（agent 抽取后填入） |
| F2 | `_TEMPLATES_README.md` | 模板 README | 占位符规约、生成流程、验收命令 |
| F3 | `_TEMPLATE_00_文書統制計画書.md` | 模板 00 | DP 文档骨架 |
| F4 | `_TEMPLATE_01_要件定義書.md` | 模板 01 | RD 文档骨架 |
| F5 | `_TEMPLATE_02_基本設計書.md` | 模板 02 | BD 文档骨架 |
| F6 | `_TEMPLATE_03_詳細設計書.md` | 模板 03 | DD 文档骨架（Group A/B 通用） |
| F7 | `_TEMPLATE_04_テスト実施記録.md` | 模板 04 | TE 文档骨架 |
| F8 | `_TEMPLATE_05_トレーサビリティマトリクス.md` | 模板 05 | TM 文档骨架 |
| F9 | `_TEMPLATE_06_文書統制報告書.md` | 模板 06 | DR 文档骨架 |

---

## Shared Reference Tables（被多个 Task 引用）

### Table A — 模板占位符与 input profile 字段映射

| 模板占位符 | input profile 字段 | 例 |
|---|---|---|
| `{{STUDY_ID}}` | §1.STUDY_ID | `COSMOS_GC` |
| `{{STUDY_LONG_NAME}}` | §4 一句话中性概要 | `血中循環腫瘍 DNA (ctDNA) 統合解析、胃癌および消化管間質腫瘍対象の独立スタディ` |
| `{{PROCESS_NAME}}` | §1.PROCESS_NAME | `CombineProcess` |
| `{{OPERATION_CONF}}` | §1.OPERATION_CONF | `COSMOS_GC_OperationConf.xlsx` |
| `{{FUNCTION_MODULE}}` | §1.FUNCTION_MODULE | `VC_BC05_studyFunctions` |
| `{{FUNCTION_MODULE_PATH}}` | §1.FUNCTION_MODULE_PATH | `studySpecific/COSMOS_GC/VC_BC05_studyFunctions.py` |
| `{{AUTHOR}}` | §2.AUTHOR | `張　泊江` |
| `{{REVIEWER}}` | §2.REVIEWER | `QA` |
| `{{APPROVER}}` | §2.APPROVER | `PM` |
| `{{CREATE_DATE_JP}}` | §3.CREATE_DATE_JP | `2026年04月15日` |
| `{{UPDATE_DATE_JP}}` | §3.UPDATE_DATE_JP | `2026年05月19日` |
| `{{TODAY_SLASH}}` | §3.TODAY_SLASH | `2026/05/19` |
| `{{STUDY_BACKGROUND_PARAGRAPH}}` | §4 段落原文 | RD §1.1 / BD §1 / DP §1 用 |

可重复块占位（`<!-- BEGIN: name --> ... <!-- END: name -->`）：

| 块名 | 引用源 | 出现位置 |
|---|---|---|
| `f_sources` | §5 F-* sources 表 | BD §4.3, DD §2.3 |
| `output_fields` | §5 派生字段 + §7 R 引用 | BD §4.3 出力, DD §2.4 |
| `public_funcs` | §6 公开函数表 | BD §3.3, DD §1/§2/§3 |
| `rules` | §7 R-xx 业务规则 | BD §5, DD 派生逻辑各处, TE 期待结果 |
| `sample_input` | §8 代表症例输入 | DD §4.1 |
| `sample_output` | §8 代表症例输出 | DD §4.2 |

### Table B — 行内 RULE-GUARD 与既有 guide 章节映射

| RULE-GUARD 内容 | 引用 | 出现位置 |
|---|---|---|
| `<!-- RULE-GUARD §5.2: 不写文件名/保存先/格式，必要时归属に明示 -->` | `_BACKGROUND_INTERNAL.md §5.2` | RD §1.3, RD §4.2 序言, BD §1, DD §0 |
| `<!-- RULE-GUARD §5.3: RD はフィールド名・函数名・算法を書かない -->` | `_BACKGROUND_INTERNAL.md §5.3` | RD §3, RD §4.2 |
| `<!-- RULE-GUARD §7: R-xx は業務意図のみ。実装手段は DD/コードへ -->` | `_BACKGROUND_INTERNAL.md §7` | BD §5 R-xx 表头 |
| `<!-- RULE-GUARD guide §10.4: 禁词「機能群」「研究」「病院」「主導」「医療機関」 -->` | `_BC05_TO_DOCS_AGENT_GUIDE.md §10.4` | 模板首行 |
| `<!-- RULE-GUARD §5.1: 業務術語には必ず代码侧アンカー（F-XXX/関数名）を併記 -->` | `_BACKGROUND_INTERNAL.md §5.1` | RD §2.2 |
| `<!-- RULE-GUARD guide §8: 初版必ず 1.0、変更履歴は 1 行のみ -->` | `_BC05_TO_DOCS_AGENT_GUIDE.md §8` | 全模板の変更履歴节 |

### Table C — 全模板共通の冒頭護欄

每份模板首行（`#` 之前）固定写：

```markdown
<!--
This is a template. Replace {{...}} placeholders using _STUDY_INPUT_PROFILE.md.
Constraints inherited from:
  - _BACKGROUND_INTERNAL.md (why)
  - _BC05_TO_DOCS_AGENT_GUIDE.md (how)
Do NOT rename chapters. Do NOT add free-form sections. Only fill placeholders and BEGIN/END blocks.
RULE-GUARD §10.4: 禁词扫描必经 → guide §11 ripgrep 命令
-->
```

---

## Task 1: 写 `_STUDY_INPUT_PROFILE.md`

**Files:**
- Create: `studySpecific/COSMOS_GC/20_Doc/_STUDY_INPUT_PROFILE.md`

**说明：** 此文件是 study-specific 实例（含 COSMOS_GC 真实值），不是抽象模板。后续 7 份模板从这里读取所有占位符值。

- [ ] **Step 1: 验证文件不存在**

Run:
```bash
test ! -f studySpecific/COSMOS_GC/20_Doc/_STUDY_INPUT_PROFILE.md && echo "OK: file does not exist"
```
Expected: `OK: file does not exist`

- [ ] **Step 2: 写入完整内容**

Write `studySpecific/COSMOS_GC/20_Doc/_STUDY_INPUT_PROFILE.md` with:

````markdown
<!--
This file is the SINGLE SOURCE OF TRUTH for study-specific data feeding all 7 document templates.
Constraints inherited from _BACKGROUND_INTERNAL.md and _BC05_TO_DOCS_AGENT_GUIDE.md.
Do NOT add chapters. Do NOT remove placeholders. Only fill values.
-->

# {{STUDY_ID}} スタディ固有処理 — 文書生成用 Input Profile

| 項目 | 内容 |
|---|---|
| 適用テンプレート | `_TEMPLATE_00..06_*.md` |
| 最終更新日 | 2026/05/19 |
| 担当 | 張　泊江 + AI |

---

## §1. Identifiers

<!-- SOURCE: code module path + 命名約定 -->

| キー | 値 |
|---|---|
| STUDY_ID | `COSMOS_GC` |
| PROCESS_NAME | `CombineProcess` |
| OPERATION_CONF | `COSMOS_GC_OperationConf.xlsx` |
| FUNCTION_MODULE | `VC_BC05_studyFunctions` |
| FUNCTION_MODULE_PATH | `studySpecific/COSMOS_GC/VC_BC05_studyFunctions.py` |

## §2. People

<!-- SOURCE: ユーザー入力 -->

| 役割 | 氏名 |
|---|---|
| AUTHOR | `張　泊江` |
| REVIEWER | `QA` |
| APPROVER | `PM` |

## §3. Dates

<!-- SOURCE: システム日付 + ユーザー確認 -->

| キー | 値 |
|---|---|
| CREATE_DATE_JP | `2026年04月15日` |
| UPDATE_DATE_JP | `2026年05月19日` |
| TODAY_SLASH | `2026/05/19` |

## §4. Study Background

<!-- SOURCE: protocol §背景/目的、機関名・主導方は中性化 -->
<!-- RULE-GUARD guide §10.4: 禁词「研究」「病院」「主導」「医療機関」 -->

**STUDY_LONG_NAME**（1 句概要）:

> 血中循環腫瘍 DNA (ctDNA) 統合解析、胃癌および消化管間質腫瘍 (GIST: Gastrointestinal Stromal Tumor) 対象の独立スタディ

**STUDY_BACKGROUND_PARAGRAPH**（RD §1.1 / BD §1 / DP §1 で利用）:

> COSMOS_GC は、血中循環腫瘍 DNA (ctDNA) のゲノム・エピゲノム統合解析における、胃癌 (Gastric Cancer) および消化管間質腫瘍 (GIST: Gastrointestinal Stromal Tumor) を対象とした独立スタディである。EDC (COSMOS Form 群) から取得した症例データは、整形工程を経て後続工程へ引き渡される。本工程の途中段階において、設定ファイル (`{{OPERATION_CONF}}`) のみでは表現できないスタディ固有の業務ロジックが存在し、後続工程へ引き渡すデータ品質を確保するために本処理で補完する。

## §5. F-* Sources

<!-- SOURCE: protocol 字段定义 + code 抽取 -->
<!-- 業務概念のみは RD では使ってよい。フィールド名は BD/DD のみ。-->

| F-ID | 業務名 | キー | 主な業務項目（日英対照） |
|---|---|---|---|
| F-PAT | 症例基本情報 | 症例 ID (SUBJID) | 年齢 (AGE)、性別 (SEX)、施設名 (STNAME) |
| F-IE | 同意・登録情報 | 症例 ID (SUBJID) | 登録日 (REGDTC)、同意取得日 (RFICDTC)、同意取得者 (ICINVNAM)、同意書版数 (ICFVER) |
| F-COHORT | コホート情報（相互排他前提） | 症例 ID (SUBJID) | 主コホート (COHORT)、コホート A (COHORTA)、コホート B (COHORTB) |
| F-TUMRECUR | 腫瘍再発・転帰 | 症例 ID (SUBJID) | フォロー番号 (FLWNUM)、転帰 (OUTCOME)、判定日 (DSSSDTC)、死亡日 (DEATHDTC) |
| F-DS | スタディ中止・終了 | 症例 ID (SUBJID) | 転帰 (OUTCOME)、判定日 (DSSSDTC)、死亡日 (DEATHDTC)、試験終了日 (DSENDTC) |
| F-TRTINFO | 投与情報 | 症例 ID (SUBJID) | 投与開始日 (PRSTDTC)、投与順番 (PRSEQ) |
| F-TUMDATA | 腫瘍データ | 症例 ID (SUBJID) | 臨床ステージ主要分類 (CSTAGE)、補助分類 (CSTAGE2) |

### §5.1 派生フィールド一覧

| 派生フィールド | 由来 | 派生規則 ID |
|---|---|---|
| COHORT_ALL | F-COHORT 3 列 | R-01 |
| ORDER | F-TUMRECUR / F-DS（内部優先キー） | R-02 |
| RFENDTC | 転帰代表行の DSSSDTC / DEATHDTC | R-03 |
| 投与代表行 (PRSTDTC, PRSEQ) | F-TRTINFO | R-04 |
| CANCER | F-TUMDATA の CSTAGE / CSTAGE2 | R-05 |

## §6. 公開処理インタフェース

<!-- SOURCE: VC_BC05_studyFunctions.py のシグネチャを直接抽出 -->

| IF-ID | 関数名 | 引数 | 引数の指定形式 | 戻り値 | 対応 FR |
|---|---|---|---|---|---|
| IF-01 | `left_join_on_SUBJID` | `main_file`, `sub_file`, `fields` | `main_file`/`sub_file`: 連携設定では整形済テーブル名、プログラム呼び出しでは DataFrame も許容。`fields`: 副表保持列の単一/複数指定または未指定 | `pandas.DataFrame` | FR-01, FR-03, FR-04 |
| IF-02 | `get_DEMOGRAPHIC_Data` | なし | 連携設定から引数なしで呼び出す | `pandas.DataFrame` | FR-02, FR-05, FR-06, FR-07 |
| IF-03 | `TUMDATA_process` | なし | 連携設定から引数なしで呼び出す | `pandas.DataFrame` | FR-08 |

### §6.1 共通戻り値契約

- 戻り値は `pandas.DataFrame`
- 欠損値は空文字列
- 出力項目は一貫した文字列形式
- 保存先・ファイル名・ファイル形式は `{{OPERATION_CONF}}` の責務（本書 §5.2 / RULE-GUARD）

## §7. R-xx 業務ルール（業務意図 / A 組実装 / A-B 差分予測 三列並記）

<!-- SOURCE: protocol 業務討論 + code 実装行為 -->
<!-- RULE-GUARD §7: BD には「業務意図」列のみ転載。「A 組実装」「差分予測」は DD/TE 専用 -->

### R-01 コホート統合値 (COHORT_ALL)

| 列 | 内容 |
|---|---|
| 業務意図 | COHORT/COHORTA/COHORTB は相互排他前提。COHORT_ALL は値を持つ唯一の項目を採用。全空なら空欄。複数同時値は前提違反として R-06 に従う。 |
| A 組実装 | `cohort_df[['COHORT','COHORTA','COHORTB']].agg(''.join, axis=1)` (3 列文字列結合) |
| A-B 差分予測 | B 組が「coalesce」「唯一非空値採用」「前提違反検知」で実装すると、複数同時値データで A=連結文字列、B=単一値 or 検知エラーとなり差分が出る。これは R-01 前提違反検知ポイント。 |

### R-02 転帰代表行採用

| 列 | 内容 |
|---|---|
| 業務意図 | F-DS 由来行を最優先、F-DS が無い症例では F-TUMRECUR 由来行の内部順位（フォロー番号上位優先）で代表 1 件を採用。試験終了日 (DSENDTC) は F-DS のみ採用。 |
| A 組実装 | TUMRECUR の ORDER = FLWNUM 上 2 桁、DS の ORDER = '99' 固定。SUBJID 昇順 + ORDER 降順で並び替え → drop_duplicates。 |
| A-B 差分予測 | FLWNUM 上 2 桁 ≥ '99' の異常データで A 組の DS 優先が破綻。B 組がソース flag で実装した場合は差分が出る（境界例）。 |

### R-03 スタディ終了日 (RFENDTC)

| 列 | 内容 |
|---|---|
| 業務意図 | 転帰代表行確定後、判定日 (DSSSDTC) と死亡日 (DEATHDTC) のうち値を持つ方を採用。R-02 で代表行一意化済の前提のもと、両者同時値は業務上想定しない（前提違反は R-06）。両者空は空欄。 |
| A 組実装 | `outcome_df[['DSSSDTC','DEATHDTC']].agg(''.join, axis=1)` (2 列文字列結合) |
| A-B 差分予測 | B 組が coalesce で実装すると、両者同時値データで A=連結文字列、B=先頭採用となり差分が出る。これは R-03 前提違反検知ポイント。 |

### R-04 初回投与情報

| 列 | 内容 |
|---|---|
| 業務意図 | F-TRTINFO の同一症例複数件から、投与順番 (PRSEQ) と投与開始日 (PRSTDTC) 昇順で先頭 1 件を採用。 |
| A 組実装 | `sort_values(['SUBJID','PRSEQ','PRSTDTC'], ascending=[True,True,True]).drop_duplicates(['SUBJID'])` |
| A-B 差分予測 | 業務意図が実装と一対一対応に近いため、通常データで差分は出にくい。同 PRSEQ 重複データで差分が出る可能性。 |

### R-05 癌種判定

| 列 | 内容 |
|---|---|
| 業務意図 | CSTAGE 有り → GASTRIC CANCER、CSTAGE 空かつ CSTAGE2 有り → GASTROINTESTINAL STROMAL TUMOR、両者空 → 空欄。CSTAGE > CSTAGE2 の優先順位。 |
| A 組実装 | `loc[cstage_has_value,'CANCER']='GASTRIC CANCER'`; `loc[~cstage_has_value & cstage2_has_value,'CANCER']='GASTROINTESTINAL STROMAL TUMOR'` |
| A-B 差分予測 | 業務意図と実装が一致しているため通常データで差分なし。 |

### R-06 データ不整合時挙動 / R-07 連携ルール

| ルール | 業務意図 |
|---|---|
| R-06 | 欠損・前提違反があっても処理停止せず、業務上利用可能な値を出力。重大不整合はテスト証跡または出力確認で検知可能。 |
| R-07 | 上位工程から呼び出され、生成結果を後続工程へ引き渡す。変更時は RD/DD/TM を同時更新。 |

## §8. 代表症例サンプル（DD §4 用）

<!-- SOURCE: protocol 代表症例 + 脱敏 -->
<!-- 個人情報は含まない -->

### §8.1 入力サンプル

**F-PAT**
| SUBJID | AGE | SEX | STNAME |
|---|---|---|---|
| 1 | 39 | M | 実施施設 |
| 4 | 72 | M | 実施施設 |

**F-COHORT**
| SUBJID | COHORT | COHORTA | COHORTB |
|---|---|---|---|
| 1 | GASTRIC CANCER COHORT | | |
| 4 | | | GASTRIC GIST COHORT B |

**F-TUMRECUR**
| SUBJID | FLWNUM | OUTCOME | DSSSDTC | DEATHDTC |
|---|---|---|---|---|
| 1 | 04-001 | UNKNOWN | 2022-11-04 | |
| 4 | 03-001 | DEAD | | 2023-02-11 |

### §8.2 出力サンプル

**F-DEMOGRAPHIC (主要列抜粋)**
| SUBJID | AGE | SEX | COHORT_ALL | ORDER | OUTCOME | RFENDTC | PRSTDTC |
|---|---|---|---|---|---|---|---|
| 1 | 39 | M | GASTRIC CANCER COHORT | 04 | UNKNOWN | 2022-11-04 | 2020-10-15 |
| 4 | 72 | M | GASTRIC GIST COHORT B | 03 | DEAD | 2023-02-11 | 2017-09-11 |

**F-TUMDATA 処理後 (主要列抜粋)**
| SUBJID | CSTAGE | CSTAGE2 | CANCER |
|---|---|---|---|
| 1 | I | | GASTRIC CANCER |
| 2 | IIB | | GASTRIC CANCER |
| (GIST 症例) | | Localized | GASTROINTESTINAL STROMAL TUMOR |
````

- [ ] **Step 3: 验证无禁词**

Run:
```bash
rg -n "機能群|医療機関|主導|病院" studySpecific/COSMOS_GC/20_Doc/_STUDY_INPUT_PROFILE.md
```
Expected: no matches (exit code 1)

- [ ] **Step 4: 验证关键 identifiers 全部出现**

Run:
```bash
rg -c "STUDY_ID|PROCESS_NAME|OPERATION_CONF|FUNCTION_MODULE|AUTHOR|REVIEWER|APPROVER" studySpecific/COSMOS_GC/20_Doc/_STUDY_INPUT_PROFILE.md
```
Expected: ≥ 7 matches

- [ ] **Step 5: 用户批准后 commit**

```bash
git add studySpecific/COSMOS_GC/20_Doc/_STUDY_INPUT_PROFILE.md
git commit -m "feat(docs): add _STUDY_INPUT_PROFILE.md as single source of truth for template generation"
```

---

## Task 2: 写 `_TEMPLATES_README.md`

**Files:**
- Create: `studySpecific/COSMOS_GC/20_Doc/_TEMPLATES_README.md`

- [ ] **Step 1: 验证文件不存在**

Run: `test ! -f studySpecific/COSMOS_GC/20_Doc/_TEMPLATES_README.md && echo OK`
Expected: `OK`

- [ ] **Step 2: 写入完整内容**

Write `studySpecific/COSMOS_GC/20_Doc/_TEMPLATES_README.md` with:

````markdown
# 文書テンプレート利用ガイド

本ディレクトリの 9 ファイル（本 README + 入力プロファイル + 7 テンプレート）は、`MarkDown/0X_*.md` 文書群を**安定して**生成するための支援ファイル群である。

> **三層約束**：本ファイル群だけでは不十分。次の 2 ファイルと併せて使うこと。
> - `_BACKGROUND_INTERNAL.md`（なぜ — A/B 比対、契約境界、業務意図 vs 実装）
> - `_BC05_TO_DOCS_AGENT_GUIDE.md`（どう — 抽出規則、ID 体系、分層、禁词、受入チェック）

---

## 1. ファイル構成

| 役割 | ファイル |
|---|---|
| 入力プロファイル | `_STUDY_INPUT_PROFILE.md` |
| テンプレート | `_TEMPLATE_00_文書統制計画書.md` 〜 `_TEMPLATE_06_文書統制報告書.md` |
| 出力先 | `MarkDown/00_..._06_...md` |

---

## 2. プレースホルダ規約

| 構文 | 用途 | 例 |
|---|---|---|
| `{{IDENTIFIER}}` | 単値置換 | `{{STUDY_ID}}` → `COSMOS_GC` |
| `<!-- BEGIN: block_name -->` ... `<!-- END: block_name -->` | 繰り返しブロック | F-* データ源行、R-xx ルール、TC など |
| `<!-- RULE-GUARD §x.y: 一句 -->` | 規則護欄 | `_BACKGROUND_INTERNAL.md` / `_BC05_TO_DOCS_AGENT_GUIDE.md` の章節番号を参照 |
| `<!-- HINT: ... -->` | 記入ヒント | agent が踏みやすい所のみ配置 |

**章節タイトル・表ヘッダ・変更履歴の初版行は HARD-CODED**。agent はプレースホルダのみ填筆し、章節を勝手に追加・順序変更しないこと。

---

## 3. 生成パイプライン（agent が実行する手順）

```
Step 0  _BACKGROUND_INTERNAL.md を読む（約束の動機を理解）
Step 1  _BC05_TO_DOCS_AGENT_GUIDE.md を読む（抽取・分層・禁词規則を理解）
Step 2  本 README を読む（プレースホルダ規約と流れを理解）

Step 3  抽取ステップ：
        ├─ protocol PDF/Word → §4 背景、§5 F-* 釈義、§7 R-xx 業務意図
        ├─ {{OPERATION_CONF}} → §1 OPERATION_CONF 名、呼び出し規約
        └─ {{FUNCTION_MODULE_PATH}} → §1 STUDY_ID、§6 公開関数、§7 現行実装挙動

Step 4  _STUDY_INPUT_PROFILE.md を更新（00-06 は触らない）

Step 5  各 _TEMPLATE_0X_*.md について：
        ├─ {{...}} を input profile 値で置換
        ├─ <!-- BEGIN/END --> ブロックを §5/§6/§7/§8 から展開
        └─ <!-- RULE-GUARD --> と <!-- HINT --> はそのまま残すか削除（最終出力では削除推奨）
        → MarkDown/0X_<ProcessName>.md として出力

Step 6  受入チェック（次節）
```

**抽取（Step 3-4）と填筆（Step 5）は厳密に分離**：input profile は独立にレビュー・修正・再利用できるべき。00-06 を直書きしないこと。

---

## 4. 受入チェック（コピペで実行可）

### 4.1 禁词スキャン（`_BC05_TO_DOCS_AGENT_GUIDE.md §11` 由来）

```bash
# 機能群 / 機関名 / 主導表現の有無
rg -n "機能群|医療機関|主導|病院" studySpecific/COSMOS_GC/20_Doc/MarkDown/
# 期待：no matches
```

```bash
# .csv 後缀（帰属注釈なし）
rg -n "F-[A-Z]+\.csv" studySpecific/COSMOS_GC/20_Doc/MarkDown/ | rg -v "連携設定|責務|OperationConf"
# 期待：no matches（残ったら帰属注を付けるか削除）
```

```bash
# プレースホルダ漏れ
rg -n "\{\{[A-Z_]+\}\}|<!-- BEGIN:|<!-- END:" studySpecific/COSMOS_GC/20_Doc/MarkDown/
# 期待：no matches（残っていたら未展開）
```

### 4.2 ID 体系整合

```bash
# FR-xx, F-xx, R-xx, TC-xx, TR-xx, EV-xx が 5 ファイル横断で一致しているか
for prefix in FR F R TC TR EV; do
  echo "=== $prefix ==="
  rg -oh "${prefix}-[0-9]+" studySpecific/COSMOS_GC/20_Doc/MarkDown/ | sort -u
done
```

### 4.3 初版バージョン規約

```bash
rg -n "^\| 版数 \| 1\.0 \|" studySpecific/COSMOS_GC/20_Doc/MarkDown/
# 期待：7 ファイル全て命中
```

---

## 5. テンプレート別の役割

| テンプレート | 対応文書 | 主な記載粒度 |
|---|---|---|
| `_TEMPLATE_00_文書統制計画書.md` | DP | A/B 共通、文書統制方針 |
| `_TEMPLATE_01_要件定義書.md` | RD | 業務要件（WHAT）。フィールド名・関数名・算法を**書かない** |
| `_TEMPLATE_02_基本設計書.md` | BD | 外部仕様（I/O 責務 + R-xx 業務意図 + 公開 IF 契約）。内部算法を**書かない** |
| `_TEMPLATE_03_詳細設計書.md` | DD | 内部仕様（関数シグネチャ、データ構造、アルゴリズム、TC 設計） |
| `_TEMPLATE_04_テスト実施記録.md` | TE | TC 期待結果 / 実測結果 / 証跡 ID |
| `_TEMPLATE_05_トレーサビリティマトリクス.md` | TM | FR → BD/DD/Code/TC/EV の対応表 |
| `_TEMPLATE_06_文書統制報告書.md` | DR | 統制状況・残課題・是正方針 |

---

## 6. 変更管理

- テンプレート自体の修正は `_BACKGROUND_INTERNAL.md` または `_BC05_TO_DOCS_AGENT_GUIDE.md` の改訂と整合させること
- input profile の §1-§8 構成は固定。新項目を増やす場合は本 README に追記
- 7 テンプレートは独立改訂可（各 v1.0 から開始）
````

- [ ] **Step 3: 验证关键章节存在**

Run:
```bash
rg -n "^## " studySpecific/COSMOS_GC/20_Doc/_TEMPLATES_README.md | head -10
```
Expected: 6 sections（ファイル構成 / プレースホルダ規約 / 生成パイプライン / 受入チェック / テンプレート別の役割 / 変更管理）

- [ ] **Step 4: 用户批准后 commit**

```bash
git add studySpecific/COSMOS_GC/20_Doc/_TEMPLATES_README.md
git commit -m "feat(docs): add _TEMPLATES_README.md describing template usage and verification"
```

---

## Task 3: 写 `_TEMPLATE_00_文書統制計画書.md`

**Files:**
- Create: `studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_00_文書統制計画書.md`
- Reference: `studySpecific/COSMOS_GC/20_Doc/MarkDown/00_文書統制計画書_CombineProcess.md`

**变换规则：**
1. 把 `COSMOS_GC` → `{{STUDY_ID}}`
2. 把 `CombineProcess` → `{{PROCESS_NAME}}`
3. 把 `張　泊江` → `{{AUTHOR}}`
4. 把 `QA` → `{{REVIEWER}}`、`PM` → `{{APPROVER}}`
5. 把 `2026/05/19` → `{{TODAY_SLASH}}`
6. 把背景段落整段 → `{{STUDY_BACKGROUND_PARAGRAPH}}`
7. 把 `COSMOS_GC_OperationConf.xlsx` → `{{OPERATION_CONF}}`
8. 把 `VC_BC05_studyFunctions.py` → `{{FUNCTION_MODULE_PATH}}`
9. 変更履歴ブロック → v1.0 一行のみ

- [ ] **Step 1: 验证文件不存在**

Run: `test ! -f studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_00_文書統制計画書.md && echo OK`

- [ ] **Step 2: 写入完整内容**

````markdown
<!--
This is a template. Replace {{...}} placeholders using _STUDY_INPUT_PROFILE.md.
Constraints inherited from _BACKGROUND_INTERNAL.md and _BC05_TO_DOCS_AGENT_GUIDE.md.
Do NOT rename chapters. Do NOT add free-form sections.
RULE-GUARD guide §10.4: 禁词「機能群」「研究」「病院」「主導」「医療機関」
-->

# 文書統制計画書
## スタディ固有処理（A/B 共通）

| 項目 | 内容 |
|-----|------|
| 文書番号 | DP-{{STUDY_ID}}-001 |
| 版数 | 1.0 |
| 作成日 | {{CREATE_DATE_JP}} |
| 作成者 | {{AUTHOR}} |
| レビュー者 | {{REVIEWER}} |
| 承認者 | {{APPROVER}} |
| 文書ステータス | Draft (レビュー待ち) |
| 対象システム | {{STUDY_ID}} スタディ固有処理 |
| 対象領域 | スタディ固有処理 (上位工程からの呼び出しと戻り値 DataFrame 生成) |

---

## 1. 目的
本計画書は、{{STUDY_ID}} スタディ ({{STUDY_LONG_NAME}}) におけるスタディ固有処理に関する文書の作成・改訂・レビュー・承認・保管の運用を統制し、要件から試験証跡までの追跡可能性を維持することを目的とする。

## 2. 背景
<!-- HINT: protocol §背景 から 3-4 行に圧縮。OPERATION_CONF を必ず引用 -->
- {{STUDY_ID}} スタディでは、設定ファイル (`{{OPERATION_CONF}}`) のみでは表現しきれないスタディ固有ロジック (DEMOGRAPHIC（人口統計学的情報）統合・癌種判定等) が存在する。
- 整形済データ (F-*) をスタディ固有処理で統合・派生し、後続工程へ引き渡せる形で再現性・追跡性を確保する必要がある。
- A/B グループ相互レビューを運用するため、文書体系と版管理の統一が必要である。
- 将来の監査・引継ぎ・再検証に備え、計画段階で文書統制ルールを定義する。

## 3. 適用範囲
- 対象機能: スタディ固有の症例単位データ統合・派生・判定処理 (共通 RD/BD と実装別 DD/TE)
- 対象工程: 上位工程からのスタディ固有関数呼び出し、および戻り値 DataFrame 生成
- 対象成果物:
  1. `要件定義書_{{PROCESS_NAME}}.md` (RD-{{STUDY_ID}}-001)
  2. `基本設計書_{{PROCESS_NAME}}.md` (BD-{{STUDY_ID}}-001)
  3. `詳細設計書_{{PROCESS_NAME}}.md` (DD-{{STUDY_ID}}-001)
  4. `トレーサビリティマトリクス_{{PROCESS_NAME}}.md` (TM-{{STUDY_ID}}-001)
  5. `テスト実施記録_{{PROCESS_NAME}}.md` (TE-{{STUDY_ID}}-001)

## 4. 文書体系と責務

| 文書 | 主責任 | 副責任 | 主な役割 |
|-----|--------|--------|---------|
| 要件定義書 | {{AUTHOR}} | {{REVIEWER}}/{{APPROVER}} | 業務 FR/NFR/AC の定義、受入基準の維持 |
| 基本設計書 | {{AUTHOR}} | {{REVIEWER}}/{{APPROVER}} | 共通外部仕様 (機能責務・I/O・業務ルール) 定義 |
| 詳細設計書 | Group A/B（分担） | 相互レビュー担当グループ | 実装別の関数シグネチャ・実装仕様・TC 設計 |
| トレーサビリティマトリクス | {{AUTHOR}} | {{REVIEWER}}/{{APPROVER}} | 要件から試験までの追跡管理 |
| テスト実施記録 | Group A/B（分担） | 相互レビュー担当グループ | 実行結果・証跡・判定 |

## 5. 命名・版管理ルール
<!-- RULE-GUARD guide §8: 初版必ず 1.0、変更履歴は 1 行のみ -->
1. 文書名は `<文書種別>_{{PROCESS_NAME}}.md` を原則とする。
2. 版数は `major.minor` 形式 (例: "1.0") とし、以下で更新する。
   - minor: 文言修正、誤記修正、非本質変更
   - major: 要件追加、判定基準変更、工程変更
3. 変更履歴には原則として「日付」「内容」「担当者」「Git Commit」を記載する。
4. 実装変更を伴う場合は、当日中に 5 文書すべての整合確認を実施する。
5. 記載粒度ルール (日本 IT 業界 V 字モデル準拠):
   - **RD**: 業務要件 (WHAT) のみ。関数名・型・コード式を記述しない。
   - **BD**: 外部仕様 (ブラックボックス I/O + 業務ルール R-xx) のみ。
   - **DD**: 内部仕様 (関数シグネチャ、アルゴリズム、データ構造、TC) を記述。
   - **TM/TE/DR**: 運用上必要な範囲で実装識別情報を記載。

## 6. レビュー・承認ゲート

| ゲート | 対象 | 判定条件 | 出力 |
|-------|------|---------|------|
| G1 要件レビュー | RD | FR/NFR/AC が合意 | RD 承認 |
| G2 設計レビュー | BD/DD | RD と設計の整合が取れている | BD/DD 承認 |
| G3 実装レビュー | Code | DD 記載仕様との一致 | 差分レビュー記録 |
| G4 試験レビュー | TM/TE | TC と証跡 ID が一致し、要件から試験までの追跡漏れがない | TM/TE 承認 |

## 7. トレーサビリティ運用
1. 要件 ID: `FR-xx`, `NFR-xx`, `AC-xx`
2. 設計 ID: `F-xx`, `R-xx`, `TC-xx`
3. 証跡 ID: `EV-xxxx`
4. 戻り値/連携観点: 戻り値データ名または関数連携観点を記載する。
5. 追跡確認ポイント:
   - FR 全件に BD/DD/TC のリンクがあること
   - TC 全件に TE の実施記録があること
   - EV の参照先が実在すること
   - 戻り値データまたは関数連携との接続が明示されていること

## 8. スケジュール（運用サイクル）

| フェーズ | 作業 | 目安 |
|---------|------|------|
| 計画 | 本計画書更新 | 変更着手前 |
| 設計 | RD/BD/DD 改訂 | 実装前 |
| 実装 | スタディ固有処理 ({{FUNCTION_MODULE_PATH}}) の改修 | 設計承認後 |
| 試験 | TC 実施・証跡採取 | 実装完了後 |
| 報告 | 報告書更新・承認 | 試験完了後 |

## 9. 変更管理
1. 変更起票時に影響文書を 5 文書から選定する。
2. 変更実施後、TM で要件から試験までの追跡漏れを点検する。
3. TE に実測結果・証跡を登録し、判定を確定する。
4. 最終的に本計画書と報告書の版を更新する。

### 9.1 作成体制ルール
1. 共同作成対象: RD/BD/DP/DR は Group A・Group B が共同で改訂する。
2. 分担作成対象: DD/TE は Group A/B が担当範囲を分担し、相互レビューで整合を確保する。
3. 同日未リリースの更新は、変更履歴を 1 行に統合して記録する。

## 10. リスクと対策

| リスク | 影響 | 対策 |
|-------|------|------|
| 文書更新漏れ | 監査時に説明不能 | 実装 PR チェック項目に文書更新を追加 |
| 証跡 ID 不一致 | 追跡性欠落 | TM/TE 相互照合を必須化 |
| レビュー未実施 | 品質低下 | G1-G4 の承認印欄を必須化 |
| 戻り値データ不整合 | 後続工程への引き渡し失敗 | TM の戻り値/連携観点列の定期点検 |

## 11. 完了判定
本計画の完了は、以下をすべて満たした時点とする。
1. 5 管理対象文書が最新版として整合している。
2. TM で要件から試験までの追跡漏れがない。
3. TE で必須 TC が判定済み。
4. G1-G4 の承認が完了している。

## 12. 変更履歴

| 版数 | 日付 | 変更内容 | 担当者 | Git Commit |
|-----|------|---------|--------|------------|
| 1.0 | {{TODAY_SLASH}} | 新規作成。{{STUDY_ID}} スタディ固有処理の文書統制方針を確立。A/B 共通運用体制、命名規約、レビュー承認ゲート、要件から試験までのトレーサビリティ運用を整備。 | {{AUTHOR}} | - |
````

- [ ] **Step 3: 验证占位符 + 禁词扫描**

Run:
```bash
rg -c "\{\{[A-Z_]+\}\}" studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_00_文書統制計画書.md
```
Expected: ≥ 8

```bash
rg -n "機能群|医療機関|主導|病院" studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_00_文書統制計画書.md
```
Expected: no matches

- [ ] **Step 4: commit**

```bash
git add studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_00_文書統制計画書.md
git commit -m "feat(docs): add _TEMPLATE_00 for 文書統制計画書"
```

---

## Task 4: 写 `_TEMPLATE_01_要件定義書.md`

**Files:**
- Create: `studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_01_要件定義書.md`
- Reference: `MarkDown/01_要件定義書_CombineProcess.md`

**变换规则：**
1. 标识符 + 人员 + 日期占位符化（同 Task 3）
2. §1.1 背景 → `{{STUDY_BACKGROUND_PARAGRAPH}}`
3. §1.3 / §4.2 序文 → 必須加 `<!-- RULE-GUARD §5.2 -->`
4. §3 各章 → 加 `<!-- RULE-GUARD §5.3: フィールド名禁止 -->`
5. §2.2 業務術語列 → 加 `<!-- RULE-GUARD §5.1: 代码侧アンカー併記 -->`
6. 変更履歴 → v1.0 一行

- [ ] **Step 1: 验证不存在**

Run: `test ! -f studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_01_要件定義書.md && echo OK`

- [ ] **Step 2: 写入完整内容**

````markdown
<!--
This is a template. Replace {{...}} placeholders using _STUDY_INPUT_PROFILE.md.
Constraints inherited from _BACKGROUND_INTERNAL.md and _BC05_TO_DOCS_AGENT_GUIDE.md.
Do NOT rename chapters. Do NOT add fields/functions/algorithms.
RULE-GUARD §5.3: RD はフィールド名・関数名・算法を書かない。
RULE-GUARD §5.2: 文件名・保存先・形式は連携設定の責務、本書の対象外。
-->

# 要件定義書
## スタディ固有データ統合・派生処理

| 項目 | 内容 |
|-----|------|
| 文書番号 | RD-{{STUDY_ID}}-001 |
| 版数 | 1.0 |
| 作成日 | {{CREATE_DATE_JP}} |
| 最終更新日 | {{UPDATE_DATE_JP}} |
| 作成者 | {{AUTHOR}} |
| レビュー者 | {{REVIEWER}} |
| 承認者 | {{APPROVER}} |
| 文書ステータス | Draft (レビュー待ち) |
| 対象システム | {{STUDY_ID}} スタディ固有処理 |
| 対象機能 | スタディ固有データ統合・派生処理 |
| 参照文書 | 基本設計書 (BD-{{STUDY_ID}}-001), トレーサビリティマトリクス (TM-{{STUDY_ID}}-001) |

---

## 1. はじめに

### 1.1 背景
{{STUDY_BACKGROUND_PARAGRAPH}}

### 1.2 目的
本書は、整形済データ取得後・後続工程へ引き渡す前に実施すべきスタディ固有のデータ統合・派生処理に対する業務要件を定義する。
本書および基本設計書は複数実装で共用する上位資料であり、特定の関数名、呼び出し方式、引数、内部アルゴリズムを前提としない。
具体的な実装方式は、実装単位の詳細設計書およびコードで定義する。

### 1.3 適用範囲
<!-- RULE-GUARD §5.2: 文件名・保存先は本書では仕様化しない -->
- 対象工程: 整形済データ生成後、後続工程へ引き渡す前に実行されるスタディ固有処理。本書の対象は、入力データに業務ルールを適用し、呼び出し元へ戻り値 (DataFrame) として返すまでである。戻り値を保存する際のファイル名・保存先・ファイル形式は連携設定 (`{{OPERATION_CONF}}`) で定義され、本書では仕様化しない。
- 汎用症例 ID 統合: 症例 ID 相当のキーを持つ整形済中間データを対象とする。具体的な入力データおよび保持項目は利用箇所で指定する。
- {{STUDY_ID}} 固有データ生成:
  - DEMOGRAPHIC 統合の入力データ: <!-- BEGIN: rd_demographic_sources -->`F-PAT`, `F-IE`, `F-COHORT`, `F-TUMRECUR`, `F-DS`, `F-TRTINFO`<!-- END: rd_demographic_sources -->
  - 癌種判定の入力データ: `F-TUMDATA`
- 汎用症例 ID 統合の代表的な利用例: コホート情報と登録日を症例単位で結合する。汎用症例 ID 統合そのものの入力・出力を本利用例に限定しない。
- 対象外: 設定ファイルで完結する通常整形、後続工程での用途・処理仕様、戻り値を保存する際のファイル名・保存先・ファイル形式 (連携設定の責務)、`F-TUMDATA` の癌種以外の各展開処理

---

## 2. 業務要件

### 2.1 処理単位
本処理は、整形工程で生成された中間データ (F-* 形式) を入力とし、以下の独立した呼び出し口を提供する。各処理は結果を戻り値 (DataFrame) として返す。処理の実行有無・呼び出し順序・戻り値の保存形態は、連携設定 (`{{OPERATION_CONF}}`) で定義される。

<!-- BEGIN: rd_process_units -->
#### (a) 症例単位データ統合
- 入力: `F-PAT` / `F-IE` / `F-COHORT` / `F-TUMRECUR` / `F-DS` / `F-TRTINFO` の 6 表。
- 処理: 症例 ID (`SUBJID`) で統合し、業務ルール (基本設計書 §5) に従って派生項目 (コホート統合値、スタディ終了日、初回投与情報) を付与する。

#### (b) 癌種判定
- 入力: `F-TUMDATA`。
- 処理: 臨床ステージに基づき、業務ルール (基本設計書 §5) に従って癌種列を付与する。

#### (c) 汎用症例 ID 統合 (補助)
- 入力: 症例 ID 列を持つ任意の整形済データ 2 件 + 副表からの抽出項目指定。
- 処理: 症例 ID をキーとした左結合を実行する。
- 位置付け: (a) の内部部品であり、連携設定からの独立呼び出しにも対応する (例: コホート情報と登録日の結合)。
<!-- END: rd_process_units -->

### 2.2 解決すべき業務課題
<!-- RULE-GUARD §5.1: 業務術語に必ず代码侧アンカー（F-XXX）を併記 -->
- 症例の DEMOGRAPHIC（人口統計学的情報）が複数 EDC フォーム (PAT・IE・COHORT・TUMRECUR・DS・TRTINFO) に分散しており、後続工程へ引き渡す前に症例単位で統合する必要がある。
- コホート情報と登録日を症例単位で結合した派生データセットが、利用シナリオとして要求される。
- 転帰情報は腫瘍再発記録 (TUMRECUR) とスタディ中止・終了記録 (DS) の 2 フォームに分散し、スタディ終了日決定に統一ルールが必要である。
- 同一症例に複数件の投与情報 (TRTINFO) が存在し、初回投与日特定に統一ルールが必要である。
- 腫瘍データ (TUMDATA) の臨床ステージから癌種 (胃癌・消化管間質腫瘍) を業務ルールで判定する必要がある。
- 要件・設計・実装・試験の対応関係を文書で追跡できる必要がある (A/B グループ相互レビュー前提)。

---

## 3. 機能要件
<!-- RULE-GUARD §5.3: フィールド名・関数名・算法を書かない -->

### 3.1 症例単位データ統合機能

| 要件ID | 機能名称 | 概要 | 優先度 |
|-------|----------|------|-------|
| FR-01 | 症例 ID 統合 | 複数の整形済中間データを症例 ID により統合できること。 | 高 |
| FR-02 | DEMOGRAPHIC 統合 | 症例基本情報・同意登録・コホート・転帰・投与情報を症例単位で統合し、戻り値データを構築できること。 | 高 |
| FR-03 | 統合結果の品質統一 | 統合結果は欠損値を空欄として一貫した形式 (文字列型) で出力できること。 | 高 |
| FR-04 | コホート × 登録日 結合 | 汎用症例 ID 統合 (FR-01) の利用例として、コホート情報と登録日を症例単位で結合し、戻り値データを構築できること。 | 高 |

### 3.2 症例情報の派生・判定機能

| 要件ID | 機能名称 | 概要 | 優先度 |
|-------|----------|------|-------|
| FR-05 | コホート統合値の派生 | 相互排他前提のコホート分類を統合した値を派生できること。 | 高 |
| FR-06 | スタディ終了日の決定 | 症例ごとに、転帰情報 (TUMRECUR + DS) からスタディ終了日を業務ルールに従って決定できること。 | 高 |
| FR-07 | 初回投与情報の特定 | 症例ごとに、投与情報 (TRTINFO) の中から初回投与情報を業務ルールに従って特定できること。 | 高 |
| FR-08 | 癌種判定 | 腫瘍データ (TUMDATA) から、症例の癌種 (胃癌または消化管間質腫瘍) を業務ルールに従って判定できること。 | 高 |

### 3.3 連携・追跡要件

| 要件ID | 機能名称 | 概要 | 優先度 |
|-------|----------|------|-------|
| FR-09 | 工程連携 | 上位工程からスタディ固有処理が定義された連携方式で実行され、生成データが後続工程へ引き渡せること。 | 高 |
| FR-10 | 追跡可能性 | 要件 → 設計 → 実装 → 試験の対応関係を文書で追跡できること。 | 高 |

---

## 4. データ要件

### 4.1 入力データ (整形工程出力 F-*)

| データ名称 | 必須 | 概要 | キー項目 |
|-----------|-----|------|--------|
<!-- BEGIN: rd_input_data -->
| F-PAT | ○ | 症例基本情報 | 症例 ID |
| F-IE | ○ | 同意・登録情報 | 症例 ID |
| F-COHORT | ○ | コホート情報 (相互排他前提) | 症例 ID |
| F-TUMRECUR | ○ | 腫瘍再発・転帰情報 | 症例 ID |
| F-DS | ○ | スタディ中止・終了情報 | 症例 ID |
| F-TRTINFO | ○ | 投与情報 | 症例 ID |
| F-TUMDATA | ○ | 腫瘍データ (臨床ステージを含む) | 症例 ID |
<!-- END: rd_input_data -->

各データの詳細フィールド (項目名・型・例) は基本設計書 §4 を参照。

### 4.2 出力データ (戻り値)
<!-- RULE-GUARD §5.2: 保存ファイル名は本書対象外 -->

> 本節はスタディ固有処理が戻り値として返す DataFrame の論理構成を定義する。フィールド名・由来元・派生手順の詳細は基本設計書 §4 に従う。
> 戻り値を保存する際のファイル名・保存先・ファイル形式 (`F-COHORTREG`, `F-DEMOGRAPHIC`, `F-TUMDATA` 等) は連携設定 (`{{OPERATION_CONF}}`) で定義され、本書の対象外とする。

#### 4.2.1 コホート × 登録日 結合結果 (汎用症例 ID 統合の利用例)
症例単位で、コホート情報のコホート分類と同意・登録情報の登録日を結合した内容。

#### 4.2.2 統合 DEMOGRAPHIC 情報
症例単位で、症例基本情報・同意登録情報・コホート情報・転帰情報・投与情報を統合し、業務ルールに従って派生項目 (コホート統合値、スタディ終了日、初回投与情報) を付与した内容。

#### 4.2.3 癌種判定済 腫瘍情報
整形済腫瘍データに、業務ルールに従って判定した癌種を付与した内容。

---

## 5. 非機能要件

| 要件ID | 区分 | 要件 |
|-------|------|------|
| NFR-01 | 性能 | 数千件規模の症例データに対して実務上許容できる時間で処理が完了すること。 |
| NFR-02 | 品質 | 派生・判定結果が定義された業務ルールに一致し、後続工程へ引き渡し可能であること。 |
| NFR-03 | 堅牢性 | 入力データに欠損があっても処理が継続し、業務上の検知が可能であること。 |
| NFR-04 | セキュリティ | 出力項目は関数の戻り値仕様に必要な最小範囲に限定すること。氏名等の個人情報を含む項目は、仕様上必要な項目に限り利用すること。 |
| NFR-05 | 監査性 | 変更履歴・試験結果・承認状態を文書で確認できること。 |

---

## 6. 受入基準

| 受入ID | 対象要件 | 受入条件 |
|-------|---------|---------|
| AC-01 | FR-01, FR-03 | F-* 整形済データが症例 ID で統合され、欠損値は一貫した空欄として出力されること。 |
| AC-02 | FR-02 | 6 種類の F-* データから統合 DEMOGRAPHIC 情報が構築され、戻り値データとして必要な主要列をカバーできること。 |
| AC-03 | FR-04 | コホート情報と登録日が症例単位で結合され、生成データとして利用可能であること。 |
| AC-04 | FR-05 | 相互排他前提のコホート分類が単一のコホート統合値として派生されること。 |
| AC-05 | FR-06 | TUMRECUR + DS の転帰情報からスタディ終了日が業務ルールに従い決定されること。 |
| AC-06 | FR-07 | TRTINFO の中から初回投与情報が業務ルールに従い特定されること。 |
| AC-07 | FR-08 | F-TUMDATA から癌種 (胃癌または消化管間質腫瘍) が判定され、生成データとして利用可能であること。 |
| AC-08 | FR-09, FR-10 | スタディ固有処理の生成結果が後続工程へ引き渡されること。全要件がトレーサビリティマトリクスで追跡できること。 |

---

## 7. トレーサビリティ運用ルール

1. 要件IDは `FR-xx`, `NFR-xx`, `AC-xx` で管理する。
2. 基本設計では `F-xx`, `R-xx` を使用し、要件 ID を併記する。
3. 詳細設計では `TC-xx` を定義し、FR と 1 対多で紐づける。
4. 実装または連携設定変更時は、同日に詳細設計書・トレーサビリティマトリクス・テスト実施記録を更新する。
5. Group A/B 相互レビューで、追跡切れ行がないことをリリース条件とする。

---

## 8. レビュー/承認

| ゲート | 目的 | 完了条件 |
|-------|------|---------|
| G1 要件レビュー | 業務要件妥当性確認 | FR/NFR/AC が承認済 |
| G2 設計レビュー | 要件-設計整合確認 | BD/DD と FR の対応が承認済 |
| G3 実装レビュー | 設計-コード整合確認 | 差分レビュー完了 |
| G4 試験レビュー | 試験証跡確認 | TC 結果と証跡 ID が承認済 |

---

## 9. 変更履歴

| 版数 | 日付 | 変更内容 | 担当者 | Git Commit |
|-----|------|---------|--------|------------|
| 1.0 | {{TODAY_SLASH}} | 新規作成。{{STUDY_ID}} スタディ ({{STUDY_LONG_NAME}}) におけるスタディ固有データ統合・派生処理に対する業務要件・データ要件・非機能要件・受入基準を整備。 | {{AUTHOR}} | - |
````

- [ ] **Step 3: 验证占位符 + 禁词 + RULE-GUARD**

Run:
```bash
rg -c "RULE-GUARD" studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_01_要件定義書.md
```
Expected: ≥ 4

```bash
rg -n "機能群|医療機関|主導|病院" studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_01_要件定義書.md
```
Expected: no matches

- [ ] **Step 4: commit**

```bash
git add studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_01_要件定義書.md
git commit -m "feat(docs): add _TEMPLATE_01 for 要件定義書 with §5.2/§5.3 rule guards"
```

---

## Task 5: 写 `_TEMPLATE_02_基本設計書.md`

**Files:**
- Create: `studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_02_基本設計書.md`
- Reference: `MarkDown/02_基本設計書_CombineProcess.md`

**变换规则：**
1. 标识符占位符化
2. §3.3 公開処理インタフェース → `<!-- BEGIN: public_funcs -->...<!-- END: public_funcs -->`
3. §4.3 F-* sources 表 → `<!-- BEGIN: f_sources -->...<!-- END: f_sources -->`
4. §5 各 R-xx → `<!-- BEGIN: rules -->...<!-- END: rules -->`，每条 R-xx 前加 `<!-- RULE-GUARD §7 -->`
5. §1 / §3.3 共通契約 → `<!-- RULE-GUARD §5.2 -->`

- [ ] **Step 1: 验证不存在**

Run: `test ! -f studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_02_基本設計書.md && echo OK`

- [ ] **Step 2: 写入完整内容**

````markdown
<!--
This is a template. Replace {{...}} placeholders using _STUDY_INPUT_PROFILE.md.
Constraints inherited from _BACKGROUND_INTERNAL.md and _BC05_TO_DOCS_AGENT_GUIDE.md.
Do NOT rename chapters. Do NOT include internal algorithms (those belong to DD).
RULE-GUARD §5.2: 戻り値 DataFrame の保存先・ファイル名・ファイル形式は連携設定の責務、本書の対象外。
RULE-GUARD §7: R-xx は業務意図のみ。実装手段は DD/コードへ。
-->

# 基本設計書
## スタディ固有データ統合・派生処理

| 項目 | 内容 |
|-----|------|
| 文書番号 | BD-{{STUDY_ID}}-001 |
| 版数 | 1.0 |
| 作成日 | {{CREATE_DATE_JP}} |
| 最終更新日 | {{UPDATE_DATE_JP}} |
| 作成者 | {{AUTHOR}} |
| レビュー者 | {{REVIEWER}} |
| 承認者 | {{APPROVER}} |
| 文書ステータス | Draft (レビュー待ち) |
| 対象システム | {{STUDY_ID}} スタディ固有処理 |
| 対象機能群 | スタディ固有データ統合・派生処理 |
| 参照文書 | 要件定義書 (RD-{{STUDY_ID}}-001), 詳細設計書 (DD-{{STUDY_ID}}-001) |

---

## 1. 概要
<!-- RULE-GUARD §5.2: 戻り値 DataFrame の保存先は本書対象外 -->
本処理は、{{STUDY_ID}} スタディ ({{STUDY_LONG_NAME}}) におけるスタディ固有データ前処理を担う。
整形工程で生成された中間データ (`F-*`) を入力として、後続工程へ引き渡す前に以下の業務ロジックを実行する。

- 症例 ID をキーとする汎用データ統合
- コホート情報と登録日の症例単位結合
- 6 種類の整形済データを統合した症例単位 DEMOGRAPHIC（人口統計学的情報）データ生成 (派生フィールド付与)
- 腫瘍データへの癌種列付与

本書は複数実装で共用する基本設計として、ブラックボックス視点で機能単位の入出力責務と処理ルールを定義する。
本処理の責務は入力データに業務ルールを適用し、戻り値 (DataFrame) として返すまでである。返された DataFrame の保存先・ファイル名・ファイル形式は連携設定 (`{{OPERATION_CONF}}`) で定義され、本書の対象外とする。
連携設定から呼び出すために必要な関数名、引数名、引数の指定形式、および戻り値型は、本書の外部インタフェース契約として定義する。内部アルゴリズム、代表行選択の内部条件、データ構造、および設定シート上の具体的な記述方法は詳細設計書 (DD-{{STUDY_ID}}-001) または連携設定の責務とする。

---

## 2. 機能一覧

| No. | 機能ID | 機能名 | 対応要件ID | 概要 |
|-----|-------|-------|-----------|------|
<!-- BEGIN: bd_function_list -->
| 1 | F-01 | 汎用症例 ID 統合 | FR-01, FR-03 | 任意の整形済データを症例 ID で統合した DataFrame を返し、結果の品質を統一する。 |
| 2 | F-02 | コホート × 登録日 結合 | FR-04 | コホート情報と登録日を症例 ID で統合した症例単位 DataFrame を返す。 |
| 3 | F-03 | DEMOGRAPHIC 統合 | FR-02, FR-05, FR-06, FR-07 | F-PAT/F-IE/F-COHORT/F-TUMRECUR/F-DS/F-TRTINFO を統合し、派生フィールドを付与した症例単位 DataFrame を返す。 |
| 4 | F-04 | 癌種判定 | FR-08 | F-TUMDATA に癌種列 (CANCER) を付与した DataFrame を返す。 |
| 5 | F-05 | 工程連携・追跡 | FR-09, FR-10 | スタディ固有処理の実行結果を後続工程へ引き渡せる状態にし、要件から試験まで追跡可能にする。 |
<!-- END: bd_function_list -->

---

## 3. 外部インタフェース設計

### 3.1 機能公開方針
本処理は以下の処理機能を提供する。

| 公開機能 | 対応機能 ID | 主たる役割 |
|---------|-----------|----------|
| 汎用症例 ID 統合機能 | F-01 | 任意の整形済データを症例 ID で統合した DataFrame を返す。 |
| コホート × 登録日 結合機能 | F-02 | コホート情報と登録日を統合した症例単位 DataFrame を返す。 |
| DEMOGRAPHIC 統合機能 | F-03 | 6 整形済ソースを統合した症例単位 DataFrame を返す。 |
| 癌種判定機能 | F-04 | F-TUMDATA に癌種列を付与した DataFrame を返す。 |

### 3.2 呼び出し責務
- 呼び出し元は、定義された連携仕様に従ってスタディ固有処理を実行する責務を持つ。
- 本処理は症例単位の統合・派生・判定の業務責務を持つ。
- 生成データは後続工程が利用可能な統合データセットとする。

### 3.3 公開処理インタフェース

以下の関数名、引数名、引数の指定形式、および戻り値型は、連携設定から呼び出すための外部インタフェース契約として扱う。各実装は内部処理方式を問わないが、本表の呼び出し契約と戻り値契約を満たす必要がある。

| IF-ID | 対応機能 | 関数名 | 引数 | 引数の指定形式 | 戻り値 |
|-------|----------|--------|------|----------------|--------|
<!-- BEGIN: public_funcs -->
| IF-01 | F-01 / F-02 | `left_join_on_SUBJID` | `main_file`, `sub_file`, `fields` | `main_file` / `sub_file`: 連携設定では整形済テーブル名を指定する。プログラム内呼び出しでは DataFrame 直接指定も許容する。`fields`: 副表から保持する項目名の単一指定、複数指定、または未指定。 | `pandas.DataFrame` |
| IF-02 | F-03 | `get_DEMOGRAPHIC_Data` | なし | 連携設定から引数なしで呼び出す。 | `pandas.DataFrame` |
| IF-03 | F-04 | `TUMDATA_process` | なし | 連携設定から引数なしで呼び出す。 | `pandas.DataFrame` |
<!-- END: public_funcs -->

共通戻り値契約:
- 戻り値は `pandas.DataFrame` とする。
- 欠損値は空文字列として扱う。
- 出力項目は一貫した文字列形式とする。
- 戻り値 DataFrame の保存先、ファイル名、ファイル形式は連携設定 (`{{OPERATION_CONF}}`) の責務とする。

---

## 4. 入出力仕様

### 4.1 汎用症例 ID 統合 (F-01)

**入力:**
- 主データ: 症例 ID 列を持つ整形済表データ。
- 副データ: 症例 ID 列を持つ整形済表データ。
- 抽出項目: 副データから保持する項目の指定 (省略時は副データ全項目)。

**出力:**
- 統合結果データ: 主データに副データの指定項目を症例 ID で結合した表データ。
  - **処理要件**: 欠損値は空欄として扱うこと。
  - **形式制約**: 出力項目は一貫した文字列形式とすること。
  - **項目名衝突**: 主・副で項目名が衝突する場合、副側に識別可能な接尾辞を付与すること。

### 4.2 コホート × 登録日 結合 (F-02)

**入力:**
- コホート情報: 症例 ID とコホート分類を持つ整形済表データ。
- 登録情報: 症例 ID と登録日を持つ整形済表データ。

**出力 (DataFrame):**
- 症例単位の結合 DataFrame: コホート分類と登録日を含む。
  - **処理要件**: 症例 ID ごとにコホート分類と登録日を対応付けること。
  - **形式制約**: 出力項目は一貫した文字列形式とすること。

### 4.3 DEMOGRAPHIC 統合 (F-03)

**入力:**
本機能は以下の 6 整形済データを入力とする。

| ソース | キー | 主な業務項目 |
|-------|-----|------------|
<!-- BEGIN: f_sources -->
| F-PAT (症例基本情報) | 症例 ID | 年齢、性別、施設名 |
| F-IE (同意・登録情報) | 症例 ID | 登録日 (REGDTC)、同意取得日 (RFICDTC)、同意取得者 (ICINVNAM)、同意書版数 (ICFVER) |
| F-COHORT (コホート情報) | 症例 ID | COHORT, COHORTA, COHORTB (相互排他) |
| F-TUMRECUR (腫瘍再発・転帰) | 症例 ID | フォロー番号 (FLWNUM)、転帰 (OUTCOME)、判定日 (DSSSDTC)、死亡日 (DEATHDTC) |
| F-DS (スタディ中止・終了) | 症例 ID | 転帰 (OUTCOME)、判定日 (DSSSDTC)、死亡日 (DEATHDTC)、試験終了日 (DSENDTC) |
| F-TRTINFO (投与情報) | 症例 ID | 投与開始日 (PRSTDTC)、投与順番 (PRSEQ) |
<!-- END: f_sources -->

**出力 (DataFrame):**
症例単位で以下を含む単一の統合 DataFrame を返す。

| 出力項目 | 定義 |
|---------|------|
<!-- BEGIN: output_fields -->
| 症例 ID | 症例識別子 |
| 年齢、性別、施設名 | F-PAT より継承 |
| 登録日、同意取得日、同意取得者、同意書版数 | F-IE より継承 |
| COHORT, COHORTA, COHORTB | F-COHORT より継承 |
| **COHORT_ALL** | **派生項目** (ルール R-01 参照) |
| 転帰、判定日、死亡日、試験終了日 | 転帰代表行から確定 (ルール R-02 参照) |
| **スタディ終了日 (RFENDTC)** | **派生項目** (ルール R-03 参照) |
| 投与開始日、投与順番 | 初回投与から確定 (ルール R-04 参照) |
<!-- END: output_fields -->

### 4.4 癌種判定 (F-04)

**入力:**
- F-TUMDATA: 整形済腫瘍データ。臨床ステージ (CSTAGE, CSTAGE2) を判定基準項目として含む。

**出力 (DataFrame):**
- 判定結果データ: 入力 F-TUMDATA に **癌種 (CANCER)** 列を付与した DataFrame。
  - **処理要件**: 既存項目の値を保持すること。
  - **形式制約**: 出力項目は一貫した文字列形式とすること。

---

## 5. 処理ルール
<!-- RULE-GUARD §7: 各 R-xx は業務意図のみ。実装手段（拼接・ソート方法など）は DD/コードへ -->

以下のルールは、内部実装に関わらず、入力と出力の関係として満たす必要がある。
内部アルゴリズム・実装手段は詳細設計書 (DD-{{STUDY_ID}}-001) で規定する。

<!-- BEGIN: rules -->
### R-01: コホート統合値 (COHORT_ALL) の派生ルール
1. COHORT、COHORTA、COHORTB は相互排他前提で運用される。
2. COHORT_ALL は、上記 3 項目のうち値を持つ項目の値を採用する。
3. いずれも空欄の場合、COHORT_ALL は空欄とする。
4. 複数項目が同時に値を持つ場合は相互排他前提違反として扱い、R-06 のデータ不整合時挙動に従う。

### R-02: 転帰代表行採用ルール
1. 転帰情報は F-TUMRECUR (腫瘍再発・転帰) と F-DS (スタディ中止・終了) の 2 ソースから供給される。
2. 同一症例に複数の転帰行が存在する場合、業務優先順位に従い代表行を 1 件採用する。
3. 業務優先順位は、F-DS 由来行を最優先し、F-DS が存在しない症例では F-TUMRECUR 由来行の内部順位に従って代表行を採用する。
4. 試験終了日 (DSENDTC) は F-DS の値を採用し、F-TUMRECUR 由来の場合は空欄とする。

### R-03: スタディ終了日 (RFENDTC) の派生ルール
1. 転帰代表行確定後、判定日 (DSSSDTC) と死亡日 (DEATHDTC) のうち値を持つ方をスタディ終了日として採用する。
2. R-02 により症例単位で代表行が一意化されている前提のもと、同一代表行において DSSSDTC と DEATHDTC が同時に値を持つことは業務上想定しない。両者が同時に値を持つ場合は前提違反として扱い、R-06 のデータ不整合時挙動に従う。
3. 両者が空欄の場合、スタディ終了日は空欄とする。

### R-04: 初回投与情報の特定ルール
1. F-TRTINFO は同一症例に複数件存在し得る。
2. 投与順番 (PRSEQ) および投与開始日 (PRSTDTC) の昇順に基づき、症例単位で初回投与情報 1 件を採用する。

### R-05: 癌種判定ルール
1. 臨床ステージ (CSTAGE。主要分類) が記録されている場合、癌種を「GASTRIC CANCER (胃癌)」とする。
2. CSTAGE が記録されておらず、補助分類 (CSTAGE2) が記録されている場合、癌種を「GASTROINTESTINAL STROMAL TUMOR (消化管間質腫瘍)」とする。
3. いずれも記録されていない場合、癌種は空欄とする。
4. 入力 F-TUMDATA は、癌種判定前のデータとして CANCER 列を持たないことを前提とする。既存 CANCER 列が存在する場合の堅牢性挙動は詳細設計書で確認する。

### R-06: データ不整合時の挙動
- 入力データに欠損または相互排他前提違反などの不整合がある場合でも、処理は停止せず、業務ルール上利用可能な値を出力すること。
- 重大な不整合は、テスト証跡または出力データ確認で検知可能であること。

### R-07: 連携ルール
- 本処理は上位工程から呼び出され、生成結果を後続工程へ引き渡すスタディ固有拡張点として利用される。
- 変更時は要件定義書・詳細設計書・トレーサビリティマトリクスを同時更新する。
<!-- END: rules -->

---

## 6. 要件トレーサビリティ

| 要件ID | 基本設計対応 | ルール | 受入観点 |
|-------|-------------|-------|---------|
| FR-01 | F-01 | - | 症例 ID 統合が成立する |
| FR-02 | F-03 | - | 6 整形済ソースから症例単位の統合 DataFrame が構築され戻り値として利用可能 |
| FR-03 | F-01, F-02, F-03, F-04 | - | 欠損値が空欄として一貫した形式で出力される |
| FR-04 | F-02 | - | コホート分類と登録日の症例単位結合 DataFrame が戻り値として利用可能 |
| FR-05 | F-03 | R-01 | コホート統合値が業務ルールに従い派生される |
| FR-06 | F-03 | R-02, R-03 | スタディ終了日 (RFENDTC) が業務ルールに従い決定される |
| FR-07 | F-03 | R-04 | 初回投与情報 (PRSTDTC/PRSEQ) が業務ルールに従い特定される |
| FR-08 | F-04 | R-05 | 癌種判定が業務ルールに一致し生成データとして利用可能 |
| FR-09 | F-05 | R-07 | スタディ固有処理の生成結果が後続工程へ引き渡せる |
| FR-10 | F-05 | R-07 | 文書間追跡が欠落しない |

---

## 7. 設計レビュー観点

1. **要件整合**: 全 FR が機能 ID またはルールに紐づくこと。
2. **責務分離**: 整形工程側の実行責務と本処理の業務責務が混在しないこと。
3. **データ契約**: 各機能の戻り値 DataFrame の出力項目と派生規則が一貫し、後続工程で利用可能であること。戻り値 DataFrame の保存先・ファイル名・ファイル形式は連携設定 (`{{OPERATION_CONF}}`) の責務であり、本書の対象外であること。
4. **追跡性**: 詳細設計書および試験 ID へ遷移可能であること。
5. **相互排他前提**: F-COHORT の COHORT/COHORTA/COHORTB 相互排他前提が明示されていること。
6. **不整合運用**: 検知手段が定義されていること。

---

## 8. 変更履歴

| 版数 | 日付 | 変更内容 | 担当者 | Git Commit |
|-----|------|---------|--------|------------|
| 1.0 | {{TODAY_SLASH}} | 新規作成。F-01〜F-05 の機能定義、公開処理インタフェース、入出力仕様、R-01〜R-07 の業務ルール、および要件トレーサビリティを整備。 | {{AUTHOR}} | - |
````

- [ ] **Step 3: 验证 RULE-GUARD §7 在 R-xx 表头**

Run:
```bash
rg -B 2 "^### R-01" studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_02_基本設計書.md | rg "RULE-GUARD §7"
```
Expected: at least 1 match（R-01 表头之前 2 行内有 §7 护栏）

- [ ] **Step 4: commit**

```bash
git add studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_02_基本設計書.md
git commit -m "feat(docs): add _TEMPLATE_02 for 基本設計書 with §5.2/§7 rule guards"
```

---

## Task 6: 写 `_TEMPLATE_03_詳細設計書.md`

**Files:**
- Create: `studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_03_詳細設計書.md`
- Reference: `MarkDown/03_詳細設計書_CombineProcess.md`

**变换规则：**
1. §0 实装方针 → 顶部加 `<!-- RULE-GUARD §5.2 -->`，列出文件名时显式归属语
2. §1.1 / §2.1 / §3.1 各函数概要 → 引用公开函数表（来自 input profile §6）
3. §2.6.1 / §2.6.3 派生ロジック → 业务意图 + A 组实装二层表记
4. §4 サンプルデータ → **去掉 `.csv` 后缀**，改为「主要列抜粋」
5. §5 TC 表 → 包含 R-01/R-03 前提违反检知 TC-12/TC-13

- [ ] **Step 1: 验证不存在**

Run: `test ! -f studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_03_詳細設計書.md && echo OK`

- [ ] **Step 2: 写入完整内容**

由于 DD 模板较长（~450 行，含 mermaid），完整内容见 `_TEMPLATE_03_詳細設計書.md` 的最终形态。核心结构如下，**实施时**按 `MarkDown/03_詳細設計書_CombineProcess.md` 现行 v1.0 内容做以下替换：

| 现行片段 | 替换为 |
|---|---|
| `COSMOS_GC` (出现 ~10 处) | `{{STUDY_ID}}` |
| `studySpecific/COSMOS_GC/VC_BC05_studyFunctions.py` | `{{FUNCTION_MODULE_PATH}}` |
| `COSMOS_GC_OperationConf.xlsx` | `{{OPERATION_CONF}}` |
| `張　泊江（Group A）` | `{{AUTHOR}}（Group A）` |
| `2026年04月15日` | `{{CREATE_DATE_JP}}` |
| `2026年05月19日` | `{{UPDATE_DATE_JP}}` |
| `2026/05/19` | `{{TODAY_SLASH}}` |
| §4.1 / §4.2 各 `**F-XXX.csv**` 表头 | `**F-XXX（主要列抜粋）**`（去 .csv） |
| §7 変更履歴の v1.1〜v1.4 行 | 削除し、v1.0 一行のみ残す |
| §4.2 表内 `(GIST 症例)` | 残（脱敏済み） |

**模板顶部加：**
```markdown
<!--
This is a template. Replace {{...}} placeholders using _STUDY_INPUT_PROFILE.md.
Constraints inherited from _BACKGROUND_INTERNAL.md and _BC05_TO_DOCS_AGENT_GUIDE.md.
DD records internal specs (signatures, algorithms, data structures, TCs).
RULE-GUARD §5.2: §0 ファイル名列挙は必ず「連携設定の責務」帰属注付き。
RULE-GUARD §7: §2.6.1 / §2.6.3 派生は「業務意図」と「A 組実装」を二層で記す。
-->
```

**§0 实装方针的关键归属语保留：**
```markdown
- 本モジュールの関数は上位工程から連携設定に基づいて実行される。戻り値 DataFrame の保存先・ファイル名・ファイル形式 (`F-COHORTREG.csv` / `F-DEMOGRAPHIC.csv` / `F-TUMDATA.csv` 等) は連携設定 (`{{OPERATION_CONF}}`) で定義され、本 DD の対象外とする (本 DD は戻り値 DataFrame の内部仕様までを規定する)。
```

**§2.6.1 / §2.6.3 派生ロジックの二層表记保持原状（已在现行 v1.0 中正确）：**
- 业务意图（BD R-xx 参照）
- A 组现行实装（带代码块）
- 真值表带「業務意図との一致」列
- A/B 比対観点 IMPORTANT block

**§4 サンプルデータ转换：**

Before:
```markdown
**F-PAT.csv**
| SUBJID | AGE | SEX | STNAME |
```

After:
```markdown
**F-PAT（主要列抜粋）**
| SUBJID | AGE | SEX | STNAME |
```

适用于 F-PAT, F-COHORT, F-TUMRECUR, F-DEMOGRAPHIC, F-TUMDATA 5 处。

**§7 変更履歴：**
```markdown
| 版数 | 日付 | 変更内容 | 担当者 | Git Commit |
|-----|------|---------|--------|------------|
| 1.0 | {{TODAY_SLASH}} | 新規作成。{{FUNCTION_MODULE_PATH}} の 3 関数（`left_join_on_SUBJID`, `get_DEMOGRAPHIC_Data`, `TUMDATA_process`）のシグネチャ・I/O・派生ロジック・処理フロー・代表パターンに基づくサンプル・TC-01〜TC-13・要件-設計-実装-試験のトレーサビリティ構造を整備。COHORT_ALL/RFENDTC は業務意図と A 組現行実装の二層表記。R-01/R-03 前提違反検知 TC-12/TC-13 を含む。 | {{AUTHOR}}（Group A） | - |
```

- [ ] **Step 3: 验证 .csv 已无（除归属语注的 §0 / §1.3 外）**

Run:
```bash
rg -n "\.csv" studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_03_詳細設計書.md | rg -v "連携設定|責務|{{OPERATION_CONF}}|F-COHORTREG\.csv は"
```
Expected: no matches outside §0 / §1.3 attribution context

- [ ] **Step 4: 验证 R-01/R-03 二层表记**

Run:
```bash
rg -c "業務意図.*A 組" studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_03_詳細設計書.md
```
Expected: ≥ 2

- [ ] **Step 5: commit**

```bash
git add studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_03_詳細設計書.md
git commit -m "feat(docs): add _TEMPLATE_03 for 詳細設計書 with §5.2/§7 rule guards and .csv removed from samples"
```

---

## Task 7: 写 `_TEMPLATE_04_テスト実施記録.md`

**Files:**
- Create: `studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_04_テスト実施記録.md`
- Reference: `MarkDown/04_テスト実施記録_CombineProcess.md`

**变换规则：**
1. 标识符占位符化
2. §2 测试结果表 → `<!-- BEGIN: test_cases -->...<!-- END: test_cases -->`，包含 TC-01〜TC-13
3. TC-08 期待結果改写为「連携設定経由で...保存される」
4. TC-12 / TC-13 保持 A/B 比対観点

- [ ] **Step 1: 验证不存在**

Run: `test ! -f studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_04_テスト実施記録.md && echo OK`

- [ ] **Step 2: 写入完整内容**

以 `MarkDown/04_テスト実施記録_CombineProcess.md` 现行 v1.0 为基底，做以下转换：

| 现行片段 | 替换为 |
|---|---|
| `COSMOS_GC` | `{{STUDY_ID}}` |
| `studySpecific/COSMOS_GC/VC_BC05_studyFunctions.py` | `{{FUNCTION_MODULE_PATH}}` |
| `張　泊江（Group A）` | `{{AUTHOR}}（Group A）` |
| 日期 | `{{CREATE_DATE_JP}}` / `{{UPDATE_DATE_JP}}` / `{{TODAY_SLASH}}` |
| §1 実施環境 | 保持 `Python 3.11.x / pandas 2.x / openpyxl 3.x`（与 code 一致） |
| §2 TC-08 期待結果 | 改写：「戻り値 DataFrame が連携設定経由で F-COHORTREG / F-DEMOGRAPHIC / F-TUMDATA として保存される（連携設定の責務）」 |
| §6 変更履歴 v1.1〜v1.4 | 删除，只保留 v1.0 一行 |
| TC 表外包 | `<!-- BEGIN: test_cases -->` / `<!-- END: test_cases -->` |

**模板顶部：**
```markdown
<!--
This is a template. Replace {{...}} placeholders using _STUDY_INPUT_PROFILE.md.
Constraints inherited from _BACKGROUND_INTERNAL.md and _BC05_TO_DOCS_AGENT_GUIDE.md.
RULE-GUARD §5.2: TC 期待結果でファイル生成を断言する場合は「連携設定経由」帰属を明示。
-->
```

**§6 変更履歴：**
```markdown
| 版数 | 日付 | 変更内容 | 担当者 | Git Commit |
|-----|------|---------|--------|------------|
| 1.0 | {{TODAY_SLASH}} | 新規作成。{{STUDY_ID}} スタディ固有関数 3 件に対する試験計画 (TC-01〜TC-13) を整備。実測結果は試験実施完了後の次版にて反映する。 | {{AUTHOR}}（Group A） | - |
```

- [ ] **Step 3: 验证 TC-08 已改写**

Run:
```bash
rg "TC-08.*連携設定経由" studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_04_テスト実施記録.md
```
Expected: at least 1 match

- [ ] **Step 4: commit**

```bash
git add studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_04_テスト実施記録.md
git commit -m "feat(docs): add _TEMPLATE_04 for テスト実施記録 with §5.2 attribution rewrite"
```

---

## Task 8: 写 `_TEMPLATE_05_トレーサビリティマトリクス.md`

**Files:**
- Create: `studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_05_トレーサビリティマトリクス.md`
- Reference: `MarkDown/05_トレーサビリティマトリクス_CombineProcess.md`

- [ ] **Step 1: 验证不存在**

Run: `test ! -f studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_05_トレーサビリティマトリクス.md && echo OK`

- [ ] **Step 2: 写入完整内容**

以 `MarkDown/05_トレーサビリティマトリクス_CombineProcess.md` 现行 v1.0 为基底，做转换：

| 现行片段 | 替换为 |
|---|---|
| `COSMOS_GC` | `{{STUDY_ID}}` |
| `studySpecific/COSMOS_GC/VC_BC05_studyFunctions.py` | `{{FUNCTION_MODULE_PATH}}` |
| `張　泊江（Group A）` | `{{AUTHOR}}（Group A）` |
| 日期 | `{{...}}` |
| §2 对应表外包 | `<!-- BEGIN: traceability -->...<!-- END: traceability -->` |
| §5 変更履歴 v1.1〜v1.4 | 删除，只保留 v1.0 一行 |

**模板顶部：**
```markdown
<!--
This is a template. Replace {{...}} placeholders using _STUDY_INPUT_PROFILE.md.
Constraints inherited from _BACKGROUND_INTERNAL.md and _BC05_TO_DOCS_AGENT_GUIDE.md.
TM tracks FR → BD/DD/Code/TC/EV correspondence. Update on every requirement change.
-->
```

**§5 変更履歴：**
```markdown
| 版数 | 日付 | 変更内容 | 担当者 | Git Commit |
|-----|------|---------|--------|------------|
| 1.0 | {{TODAY_SLASH}} | 新規作成。{{STUDY_ID}} スタディ固有処理 3 関数に対する TR-001〜TR-017 を定義。FR/NFR 全件を試験まで追跡。R-01/R-03 前提違反検知 TR-016/TR-017 を含む。状態は試験未実施のため Open を初期値とする。 | {{AUTHOR}}（Group A） | - |
```

- [ ] **Step 3: 验证 TR ID 完整**

Run:
```bash
rg -oh "TR-[0-9]+" studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_05_トレーサビリティマトリクス.md | sort -u | wc -l
```
Expected: 17（TR-001〜TR-017）

- [ ] **Step 4: commit**

```bash
git add studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_05_トレーサビリティマトリクス.md
git commit -m "feat(docs): add _TEMPLATE_05 for トレーサビリティマトリクス"
```

---

## Task 9: 写 `_TEMPLATE_06_文書統制報告書.md`

**Files:**
- Create: `studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_06_文書統制報告書.md`
- Reference: `MarkDown/06_文書統制報告書_CombineProcess.md`

- [ ] **Step 1: 验证不存在**

Run: `test ! -f studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_06_文書統制報告書.md && echo OK`

- [ ] **Step 2: 写入完整内容**

以 `MarkDown/06_文書統制報告書_CombineProcess.md` 现行 v1.0 (实为 1.5，但模板降为 1.0) 为基底，做转换：

| 现行片段 | 替换为 |
|---|---|
| `COSMOS_GC` | `{{STUDY_ID}}` |
| 日期 | `{{...}}` |
| `張　泊江` | `{{AUTHOR}}` |
| §3 成果物バージョン (1.5, 1.4 等) | 全部 → `1.0`（首版） |
| §6 Git 履歴 | 保留空白，待 commit 后填 |
| §10 変更履歴 v1.1〜v1.5 | 删除，只保留 v1.0 一行 |

**模板顶部：**
```markdown
<!--
This is a template. Replace {{...}} placeholders using _STUDY_INPUT_PROFILE.md.
Constraints inherited from _BACKGROUND_INTERNAL.md and _BC05_TO_DOCS_AGENT_GUIDE.md.
DR is the umbrella status report. Update when any of RD/BD/DD/TM/TE changes.
-->
```

**§10 変更履歴：**
```markdown
| 版数 | 日付 | 変更内容 | 担当者 | Git Commit |
|-----|------|---------|--------|------------|
| 1.0 | {{TODAY_SLASH}} | 新規作成。{{STUDY_ID}} スタディ固有処理に対する文書体系・ID 体系・要件から試験までの追跡構造の初版整備状況を報告。試験実施は次版にて反映予定。 | {{AUTHOR}} | - |
```

- [ ] **Step 3: 验证全部成果物状態が「Draft Baseline」**

Run:
```bash
rg "Draft Baseline Established|初版整備済" studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_06_文書統制報告書.md
```
Expected: at least 1 match

- [ ] **Step 4: commit**

```bash
git add studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_06_文書統制報告書.md
git commit -m "feat(docs): add _TEMPLATE_06 for 文書統制報告書"
```

---

## Task 10: 跨模板校验（最终把关）

**Files:** read-only across all 9 new files

- [ ] **Step 1: 所有占位符在 input profile 都能找到映射**

Run:
```bash
# 提取所有模板中出现的 {{...}} placeholder
rg -oh "\{\{[A-Z_]+\}\}" studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_*.md | sort -u > /tmp/placeholders.txt
# 检查 input profile 是否每个都覆盖
while read p; do
  key="${p#\{\{}"; key="${key%\}\}}"
  if ! rg -q "$key" studySpecific/COSMOS_GC/20_Doc/_STUDY_INPUT_PROFILE.md; then
    echo "MISSING: $p"
  fi
done < /tmp/placeholders.txt
```
Expected: no `MISSING:` lines

- [ ] **Step 2: 所有 RULE-GUARD § 引用都能反查到原文章节**

Run:
```bash
# 提取所有 RULE-GUARD §x.y 引用
rg -oh "RULE-GUARD [^:]+:" studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_*.md studySpecific/COSMOS_GC/20_Doc/_STUDY_INPUT_PROFILE.md | sort -u
```
Expected output (the unique guard tags) — 人工反查到 `_BACKGROUND_INTERNAL.md` / `_BC05_TO_DOCS_AGENT_GUIDE.md`

- [ ] **Step 3: 禁词全套扫描**

Run:
```bash
rg -n "機能群|医療機関|主導|病院" studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_*.md studySpecific/COSMOS_GC/20_Doc/_STUDY_INPUT_PROFILE.md studySpecific/COSMOS_GC/20_Doc/_TEMPLATES_README.md
```
Expected: no matches

- [ ] **Step 4: 全部 v1.0 検証**

Run:
```bash
rg "^\| 1\.0 \|" studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_*.md | wc -l
```
Expected: 7（每模板各 1 行 v1.0 履歴）

- [ ] **Step 5: 用现存 COSMOS_GC 数据手工渲染 RD，对比章节结构**

Run:
```bash
# 提取模板章节
rg "^## " studySpecific/COSMOS_GC/20_Doc/_TEMPLATE_01_要件定義書.md > /tmp/tpl_01_sections.txt
# 提取现存 RD 章节
rg "^## " studySpecific/COSMOS_GC/20_Doc/MarkDown/01_要件定義書_CombineProcess.md > /tmp/cur_01_sections.txt
diff /tmp/tpl_01_sections.txt /tmp/cur_01_sections.txt
```
Expected: empty diff（章节标题 1-9 必须完全一致）

如有差异 → 立即回到 Task 4 修正模板。

- [ ] **Step 6: commit final validation**

```bash
git commit --allow-empty -m "chore(docs): cross-validation passed for template suite v1.0"
```

---

## Self-Review Checklist（写完模板后自审）

- [ ] 每个模板的章节结构与对应 `MarkDown/0X_*.md` v1.0 一致
- [ ] 每个 `{{PLACEHOLDER}}` 都能在 `_STUDY_INPUT_PROFILE.md` 找到对应字段
- [ ] 每个 `<!-- RULE-GUARD §x.y -->` 都能反查到 `_BACKGROUND_INTERNAL.md` 或 `_BC05_TO_DOCS_AGENT_GUIDE.md` 的真实章节
- [ ] 没有禁词（機能群 / 医療機関 / 主導 / 病院）
- [ ] DD §4 サンプルデータ全部使用「主要列抜粋」格式，无 `.csv` 后缀
- [ ] TE TC-08 期待结果使用「連携設定経由」措辞
- [ ] 全部模板変更履歴 = v1.0 一行
- [ ] BD §5 R-xx 只含业务意图，不含拼接/排序等实装细节
- [ ] DD §2.6.1 / §2.6.3 含「业务意图 + A 组实装」二层
- [ ] 9 个文件全部置于 `studySpecific/COSMOS_GC/20_Doc/`

---

## 实施完成后的下一步

1. 把这套模板试用一次：用 `_STUDY_INPUT_PROFILE.md` 的 COSMOS_GC 值手工填充 7 模板 → 生成 7 个 `.md.draft` → 与现存 `MarkDown/0X_*.md` 做章节级 diff，确认覆盖
2. 若覆盖完整，把模板套件标记为 v1.0 baseline
3. 后续如有新研究复用，把模板上提到 `studySpecific/_templates/` 并参数化掉 COSMOS_GC 特异值

---

## 出现问题时回退策略

- 单文件错了：`git revert HEAD` 撤销该 commit，回到上一任务
- 多文件冲突：跳到 Task 10 跑全套验证找到第一个失败处
- 整套节奏不对：保留 input profile + README，重做模板 03-06（最大风险区）
