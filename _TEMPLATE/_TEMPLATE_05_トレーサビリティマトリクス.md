<!-- TEMPLATE: replace {{...}} placeholders from _STUDY_INPUT_PROFILE.md. -->
<!-- Constraints: see _BACKGROUND_INTERNAL.md (why) and _BC05_TO_DOCS_AGENT_GUIDE.md (how). -->
<!-- TM tracks FR → BD/DD/Code/TC/EV correspondence. Update on every requirement change. -->
<!-- RULE-GUARD guide §10.4: 禁词「機能群」「研究」「病院」「主導」「医療機関」 -->

# トレーサビリティマトリクス
## {{FUNCTION_MODULE}}

| 項目 | 内容 |
|-----|------|
| 文書番号 | TM-{{STUDY_ID}}-001 |
| 版数 | 1.0 |
| 作成日 | {{CREATE_DATE_JP}} |
| 最終更新日 | {{UPDATE_DATE_JP}} |
| 作成者 | {{AUTHOR}} |
| レビュー者 | {{REVIEWER}} |
| 承認者 | {{APPROVER}} |
| 文書ステータス | Draft (レビュー待ち) |
| 対象 | RD-{{STUDY_ID}}-001 / BD-{{STUDY_ID}}-001 / DD-{{STUDY_ID}}-001 / 実装 / 試験 |

---

## 1. 目的
本マトリクスは、要件定義 → 基本設計 → 詳細設計 → 実装 → 試験証跡の対応を一元管理し、
{{STUDY_ID}} スタディ ({{STUDY_LONG_NAME}}) におけるスタディ固有ロジックについて追跡切れを防止することを目的とする。

## 2. 対応表

<!-- BEGIN: traceability -->
| Trace ID | 要件ID | 要件概要 | 基本設計 | 詳細設計 | 実装 | テストID | 証跡ID | 戻り値/連携観点 | 状態 |
|---------|-------|---------|---------|---------|------|---------|-------|-----------|------|
| TR-001 | FR-01 | 症例 ID 統合 (整形済 F-* データ) | F-01 | 1.1-1.6 | `{{FUNCTION_MODULE_PATH}}` `left_join_on_SUBJID` | TC-01, TC-02, TC-03 | EV-TC-001, EV-TC-002, EV-TC-003 | (汎用) | Open |
| TR-002 | FR-02 | DEMOGRAPHIC 統合 (F-PAT/F-IE/F-COHORT/F-TUMRECUR/F-DS/F-TRTINFO を症例単位で統合した DataFrame を返す) | F-03 | 2.3, 2.7 | `{{FUNCTION_MODULE_PATH}}` `get_DEMOGRAPHIC_Data` | TC-04 | EV-TC-004 | F-DEMOGRAPHIC | Open |
| TR-003 | FR-03 | 統合結果型統一 (NaN→空文字列、全列文字列型) | F-01, F-02, F-03, F-04 | 1.4, 2.8, 3.3 | `{{FUNCTION_MODULE_PATH}}` 戻り値生成前 `fillna('').astype(str)` | TC-01, TC-02 | EV-TC-001, EV-TC-002 | (共通) | Open |
| TR-004 | FR-04 | コホート × 登録日 結合 (コホート情報と登録日を症例単位で結合した DataFrame を返す) | F-02 | 1.1-1.6 | `{{FUNCTION_MODULE_PATH}}` `left_join_on_SUBJID` | TC-01 | EV-TC-001 | F-COHORTREG | Open |
| TR-005 | FR-05 | コホート統合値 (COHORT_ALL) 派生 | F-03, R-01 | 2.6.1 | `{{FUNCTION_MODULE_PATH}}` COHORT_ALL 派生 (現行実装は連結、業務意図は唯一の非空値採用) | TC-04 | EV-TC-004 | F-DEMOGRAPHIC | Open |
| TR-006 | FR-06 | 転帰代表行採用 (R-02: DS 優先、DS なしは TUMRECUR 内順位) とスタディ終了日 (RFENDTC) 派生 (R-03: 業務意図 = 判定日/死亡日のいずれか採用) | F-03, R-02, R-03 | 2.6.2, 2.6.3 | `{{FUNCTION_MODULE_PATH}}` 転帰代表行採用・RFENDTC 派生 (RFENDTC 現行実装は連結) | TC-05 | EV-TC-005 | F-DEMOGRAPHIC | Open |
| TR-007 | FR-07 | 初回投与情報 (PRSTDTC/PRSEQ) 特定 | F-03, R-04 | 2.7 結合順序 6 | `{{FUNCTION_MODULE_PATH}}` TRTINFO ソート・代表行採用 | TC-06 | EV-TC-006 | F-DEMOGRAPHIC | Open |
| TR-008 | FR-08 | 癌種判定 (CSTAGE/CSTAGE2 → CANCER) | F-04, R-05 | 3.4, 3.5 | `{{FUNCTION_MODULE_PATH}}` `TUMDATA_process` | TC-07 | EV-TC-007 | F-TUMDATA | Open |
| TR-009 | FR-09 | 上位工程連携 | F-05, R-07 | 0 章, 2 章 | 上位工程からのスタディ固有処理呼び出し連携 | TC-08 | EV-TC-008 | 呼び出し連携 | Open |
| TR-010 | FR-10 | 文書追跡可能性 (要件→設計→実装→試験) | F-05, R-07 | 5 章, 6 章 | 本マトリクス + テスト実施記録 | TC-09 | EV-TC-009 | - | Open |
| TR-011 | NFR-01 | 性能要件 | 1 章概要, 7 章レビュー観点 | 0 章実装方針 | pandas 処理実装 (ベクトル化) | TC-10 | EV-PERF-001 | - | Open |
| TR-012 | NFR-02 | 品質要件 (派生・判定一致) | R-01〜R-05 | 2.6, 3.5 | COHORT_ALL / ORDER / RFENDTC / CANCER 派生実装 | TC-04, TC-05, TC-06, TC-07, TC-12, TC-13 | EV-TC-004, EV-TC-005, EV-TC-006, EV-TC-007, EV-TC-012, EV-TC-013 | 戻り値データ | Open |
| TR-013 | NFR-03 | 堅牢性 (欠損許容・前提違反検知) | R-06 | 2.8, 3.6 | 列存在確認・空の Series 補完・前提違反時の出力確認 | TC-04, TC-07, TC-12, TC-13 | EV-TC-004, EV-TC-007, EV-TC-012, EV-TC-013 | - | Open |
| TR-014 | NFR-04 | セキュリティ (必要最小限の項目出力) | 4 章入出力 | 2.3, 2.4 | 戻り値仕様に必要な出力項目の確認 | TC-11 | EV-SEC-001 | - | Open |
| TR-015 | NFR-05 | 監査性 (変更履歴・試験記録) | 6 章要件トレーサビリティ | 5 章, 6 章 | 本マトリクス/変更履歴/テスト記録 | TC-11 | EV-AUD-001 | - | Open |
| TR-016 | FR-06, NFR-03 | R-03 業務前提違反検知 (DSSSDTC/DEATHDTC 同時値による A/B 比対差分) | R-03, R-06 | 2.6.3, 2.8 | `{{FUNCTION_MODULE_PATH}}` RFENDTC 派生 (現行は連結) | TC-12 | EV-TC-012 | F-DEMOGRAPHIC | Open |
| TR-017 | FR-05, NFR-03 | R-01 業務前提違反検知 (COHORT/COHORTA/COHORTB 同時値による A/B 比対差分) | R-01, R-06 | 2.6.1, 2.8 | `{{FUNCTION_MODULE_PATH}}` COHORT_ALL 派生 (現行は連結) | TC-13 | EV-TC-013 | F-DEMOGRAPHIC | Open |
<!-- END: traceability -->

## 3. 運用ルール

1. 実装変更時は、同日に TR 行の状態と証跡 ID を更新する。
2. Draft Baseline として提出する場合は `Open` を許容する。正式リリースまたは Final Close では、少なくとも `Verified` を必須とする。
3. テスト実施記録の証跡 ID と本マトリクスの証跡 ID を一致させる。
4. A/B グループ相互レビューで `Trace ID` 欠番・重複がないことを確認する。
5. 戻り値データ仕様または関数連携仕様を変更する場合は、本マトリクスを更新すること。

## 4. ステータス定義

| ステータス | 意味 |
|-----------|------|
| Open | 定義済みだが証跡未登録 |
| In Progress | 試験またはレビュー実施中 |
| Verified | 試験証跡とレビューが完了 |
| Closed | 承認済みでベースライン固定 |

## 5. 変更履歴

| 版数 | 日付 | 変更内容 | 担当者 | Git Commit |
|-----|------|---------|--------|------------|
| 1.0 | {{TODAY_SLASH}} | 新規作成。TR-001〜TR-017 を定義し、FR/NFR から基本設計、詳細設計、実装、テスト ID、証跡 ID、戻り値/連携観点までの追跡構造を整備。 | {{AUTHOR}}（Group A） | - |
