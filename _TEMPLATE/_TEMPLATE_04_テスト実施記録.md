<!-- TEMPLATE: replace {{...}} placeholders from _STUDY_INPUT_PROFILE.md. -->
<!-- Constraints: see _BACKGROUND_INTERNAL.md (why) and _BC05_TO_DOCS_AGENT_GUIDE.md (how). -->
<!-- RULE-GUARD §5.2: TC 期待結果でファイル生成を断言する場合は「連携設定経由」帰属を明示。 -->
<!-- RULE-GUARD guide §10.4: 禁词「機能群」「研究」「病院」「主導」「医療機関」 -->

# テスト実施記録
## {{FUNCTION_MODULE}}

| 項目 | 内容 |
|-----|------|
| 文書番号 | TE-{{STUDY_ID}}-001 |
| 版数 | 1.0 |
| 作成日 | {{CREATE_DATE_JP}} |
| 最終更新日 | {{UPDATE_DATE_JP}} |
| 作成者 | {{AUTHOR}}（Group A） |
| 実施者 | {{AUTHOR}}（Group A） |
| レビュー者 | {{REVIEWER}} |
| 承認者 | {{APPROVER}} |
| 文書ステータス | Draft (レビュー待ち) |
| 対応設計書 | DD-{{STUDY_ID}}-001 |
| 対応マトリクス | TM-{{STUDY_ID}}-001 |

---

## 1. 実施概要

| 項目 | 記録 |
|-----|------|
| 実施日 | 未実施（初版作成時点） |
| 実施環境（予定） | Python 3.11.x / pandas 2.x / openpyxl 3.x |
| 対象モジュール | `{{FUNCTION_MODULE_PATH}}` |
| 関連連携 | 上位工程からのスタディ固有関数呼び出し経路 |
| 検証データ | 検証用整形済データ ({{PROCESS_NAME}} 入力 F-*) + 擬似データ |
| 実施結果サマリー | 試験計画策定済。実施は次版にて反映予定。 |

## 2. テスト結果詳細

<!-- BEGIN: test_cases -->
| TC-ID | 対応要件ID | 期待結果 | 実測結果 | 判定 | 証跡ID | 証跡ファイル/URL | 備考 |
|------|-----------|---------|---------|------|-------|------------------|------|
| TC-01 | FR-01, FR-03, FR-04 | 主テーブル (F-COHORT) に副テーブル (F-IE の REGDTC) を指定列として左結合し、コホート情報と登録日が症例単位で結合された DataFrame として返される。NaN は空文字列、全列文字列型である | 未実施 | Pending | EV-TC-001 | studySpecific/{{STUDY_ID}}/20_Doc/testEvidence/{{PROCESS_NAME}}/（次回試験実施時に記録） | テーブル名指定パターン。戻り値 DataFrame は連携設定で `F-COHORTREG.csv` として保存される。 |
| TC-02 | FR-01, FR-03 | DataFrame 入力で左結合が成立し、列名衝突時は接尾辞が付与される | 未実施 | Pending | EV-TC-002 | （次回試験実施時に記録） | DataFrame 直接指定パターン。 |
| TC-03 | FR-01 | None 入力で ValueError、未知テーブル名で KeyError、SUBJID 欠落で KeyError が発生する | 未実施 | Pending | EV-TC-003 | （次回試験実施時に記録） | 異常系まとめて確認。 |
| TC-04 | FR-02, FR-05, NFR-02 | F-DEMOGRAPHIC が F-PAT/F-IE/F-COHORT/F-TUMRECUR/F-DS/F-TRTINFO から統合され、相互排他前提のもと値を持つコホート分類が COHORT_ALL として採用される | 未実施 | Pending | EV-TC-004 | （次回試験実施時に記録） | 代表症例パターン SUBJID=1 (GASTRIC CANCER COHORT) と SUBJID=4 (GASTRIC GIST COHORT B) を擬似データで確認予定。 |
| TC-05 | FR-06, NFR-02 | DS が存在する症例では DS 由来行が代表行として採用され、DS が存在しない症例では TUMRECUR 内順位に基づく代表行が採用される (R-02)。代表行の DSSSDTC/DEATHDTC のうち値を持つ方が RFENDTC として採用される (R-03 業務意図)。R-02 で代表行が一意化されている前提のもと、DSSSDTC と DEATHDTC は同時には値を持たないことを確認する | 未実施 | Pending | EV-TC-005 | （次回試験実施時に記録） | DS ありパターンと DS なし TUMRECUR 代表行パターンで確認予定。両者同時値ケースは TC-12 (前提違反検知) で確認。 |
| TC-06 | FR-07, NFR-02 | 同一 SUBJID に複数 PRSEQ がある場合、SUBJID/PRSEQ/PRSTDTC 昇順で先頭行のみ保持される | 未実施 | Pending | EV-TC-006 | （次回試験実施時に記録） | 複数投与症例で確認予定。 |
| TC-07 | FR-08, NFR-02 | CSTAGE 有り = GASTRIC CANCER、CSTAGE 無し かつ CSTAGE2 有り = GASTROINTESTINAL STROMAL TUMOR、両方空 = 空文字列 で CANCER が判定される | 未実施 | Pending | EV-TC-007 | （次回試験実施時に記録） | 3 ケースを擬似データで確認予定。 |
| TC-08 | FR-09 | 上位工程からスタディ固有関数の呼び出しが成功し、戻り値 DataFrame が連携設定経由で F-COHORTREG / F-DEMOGRAPHIC / F-TUMDATA として保存される（連携設定の責務） | 未実施 | Pending | EV-TC-008 | （次回試験実施時に記録） | 連携設定経由の保存挙動を確認予定。 |
| TC-09 | FR-10 | RD→BD→DD→Code→TC の対応漏れがないこと | 未実施 | Pending | EV-TC-009 | （次回試験実施時に記録） | Markdown 文書を機械照合する予定。 |
| TC-10 | NFR-01 | 1 万件擬似データを 3 秒以内で処理し、出力形状が想定どおり | 未実施 | Pending | EV-PERF-001 | （次回試験実施時に記録） | 擬似データのみ使用予定。 |
| TC-11 | NFR-04, NFR-05 | 出力項目が戻り値仕様に必要な最小範囲であること、TE/TM に変更履歴セクションが存在すること | 未実施 | Pending | EV-SEC-001, EV-AUD-001 | （次回試験実施時に記録） | 出力列リストおよび文書整合を確認予定。 |
| TC-12 | FR-06, NFR-02, NFR-03 | 代表行で DSSSDTC と DEATHDTC が同時に値を持つ擬似データ (R-03 前提違反データ) を投入した場合、現行 A 組実装では RFENDTC が連結文字列となる挙動を確認し、業務意図 (いずれか採用) との差分を検知ポイントとして記録する | 未実施 | Pending | EV-TC-012 | （次回試験実施時に記録） | A/B 比対観点。B 組が coalesce 実装の場合、本ケースで結果が異なることを期待する。 |
| TC-13 | FR-05, NFR-02, NFR-03 | COHORT/COHORTA/COHORTB が同時に値を持つ擬似データ (R-01 前提違反データ) を投入した場合、現行 A 組実装では COHORT_ALL が連結文字列となる挙動を確認し、業務意図 (相互排他前提で唯一の非空値を採用) との差分を検知ポイントとして記録する | 未実施 | Pending | EV-TC-013 | （次回試験実施時に記録） | A/B 比対観点。B 組が前提違反検知または唯一の非空値採用で実装した場合、本ケースで差分または不整合が検知されることを期待する。 |
<!-- END: test_cases -->

## 3. 不具合・課題記録

| 課題ID | 起票日 | 概要 | 影響範囲 | 対応方針 | 状態 |
|-------|-------|------|---------|---------|------|
| DEF-001 | - | （未起票） | - | - | Open |

## 4. 判定基準

1. 必須 TC （TC-01〜TC-13）がすべて Pass または差分検知記録済であること。
2. 証跡 ID がトレーサビリティマトリクスと一致すること。
3. 戻り値データと関数連携が確認できていること。
4. Reviewer/Approver サインが完了していること。

## 5. 承認記録

| 役割 | 氏名 | 署名/記名 | 日付 | 判定 |
|-----|------|----------|------|------|
| 実施者 |  |  |  |  |
| レビュー者 |  |  |  |  |
| 承認者 |  |  |  |  |

## 6. 変更履歴

| 版数 | 日付 | 変更内容 | 担当者 | Git Commit |
|-----|------|---------|--------|------------|
| 1.0 | {{TODAY_SLASH}} | 新規作成。{{STUDY_ID}} スタディ固有関数に対する TC-01〜TC-13 の試験計画、期待結果、判定欄、証跡 ID、および承認記録欄を整備。 | {{AUTHOR}}（Group A） | - |
