<!-- INPUT PROFILE: single source of truth for study-specific data feeding all 7 document templates. -->
<!-- Constraints: see _BACKGROUND_INTERNAL.md (why) and _BC05_TO_DOCS_AGENT_GUIDE.md (how). -->
<!-- Do NOT add chapters. Do NOT remove placeholders. Only fill values. -->

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
| IF-01 | `left_join_on_SUBJID` | `main_file`, `sub_file`, `fields` | `main_file`/`sub_file`: 連携設定では整形済テーブル名、プログラム呼び出しでは DataFrame も許容。`fields`: 副テーブル保持列の単一/複数指定または未指定 | `pandas.DataFrame` | FR-01, FR-03, FR-04 |
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
