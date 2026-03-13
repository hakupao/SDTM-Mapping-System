# テスト実施記録
## VC_BC05_studyFunctions

| 項目 | 内容 |
|-----|------|
| 文書番号 | TE-ENSEMBLE-001 |
| 版数 | 1.1 |
| 作成日 | 2026年02月18日 |
| 最終更新日 | 2026年03月13日 |
| 作成者 | 張　泊江（Group A） |
| 実施者 | 張　泊江（Group A） |
| レビュー者 | QA |
| 承認者 | PM |
| 対応設計書 | DD-ENSEMBLE-001 |
| 対応マトリクス | TM-ENSEMBLE-001 |

---

## 1. 実施概要

| 項目 | 記録 |
|-----|------|
| 実施日 | 2026-03-13 |
| 実施環境 | Python 3.11.9 / pandas 3.0.1 / openpyxl 3.1.5 |
| 対象モジュール | `studySpecific/ENSEMBLE/VC_BC05_studyFunctions.py` |
| 関連連携 | `VC_BC04_operateType.py` |
| 実施結果サマリ | 10件中 10 Pass / 0 Fail (証跡: studySpecific/ENSEMBLE/Doc/testEvidence/CombineProcess/evidence-20260313-155453/summary_ja.md) |

## 2. テスト結果詳細

| TC-ID | 対応要件ID | 期待結果 | 実測結果 | 判定 | 証跡ID | 証跡ファイル/URL | 備考 |
|------|-----------|---------|---------|------|-------|------------------|------|
| TC-01 | FR-05, FR-06 | RFENDAT=LSVDAT, DTHFLG=空 | NE-EN-0001: LSVDAT=2025-11-10, DTHDAT=<空欄>, RFENDAT=2025-11-10, DTHFLG=<空欄> | Pass | EV-TC-001 | studySpecific/ENSEMBLE/Doc/testEvidence/CombineProcess/evidence-20260313-155453/EV-TC-001.md | 実データの対象症例: NE-EN-0001 |
| TC-02 | FR-05, FR-06 | RFENDAT=DTHDAT, DTHFLG=Y | NE-EN-0015: LSVDAT=<空欄>, DTHDAT=2025-10-31, RFENDAT=2025-10-31, DTHFLG=Y | Pass | EV-TC-002 | studySpecific/ENSEMBLE/Doc/testEvidence/CombineProcess/evidence-20260313-155453/EV-TC-002.md | 実データの対象症例: NE-EN-0015 |
| TC-03 | FR-05, FR-06, FR-07 | DTHDAT優先 + 警告通知 | 擬似症例 TEST-BOTH: RFENDAT=2025-10-31, DTHFLG=Y, 警告出力=あり | Pass | EV-TC-003 | studySpecific/ENSEMBLE/Doc/testEvidence/CombineProcess/evidence-20260313-155453/EV-TC-003.md | 1 行の擬似データセットで確認。 |
| TC-04 | FR-05, FR-06, FR-07 | RFENDAT/DTHFLG空 + 警告通知 | 擬似症例 TEST-NONE: RFENDAT=<空欄>, DTHFLG=<空欄>, 警告出力=あり | Pass | EV-TC-004 | studySpecific/ENSEMBLE/Doc/testEvidence/CombineProcess/evidence-20260313-155453/EV-TC-004.md | 1 行の擬似データセットで確認。 |
| TC-05 | FR-01, FR-02, FR-03 | 条件抽出/全空列除去/文字列型 | 実データ抽出行数=200; 擬似データ列=['EventId', 'KEEP', 'FLAG']; 擬似データ型=['str', 'str', 'str'] | Pass | EV-TC-005 | studySpecific/ENSEMBLE/Doc/testEvidence/CombineProcess/evidence-20260313-155453/EV-TC-005.md | 実データの TME と擬似 DataFrame を組み合わせて確認。 |
| TC-06 | FR-01 | KeyError発生 | 存在しないフィールド指定により KeyError が発生。 | Pass | EV-TC-006 | studySpecific/ENSEMBLE/Doc/testEvidence/CombineProcess/evidence-20260313-155453/EV-TC-006.md | 実データの TME に存在しないフィールドを指定して確認。 |
| TC-07 | FR-08 | 上位工程連携（実装: `VC_BC04_operateType.py`）で呼び出し成功 | VC_BC04_operateType から研究固有関数を呼び出し、DM 形状=(200, 7) を取得。 | Pass | EV-TC-007 | studySpecific/ENSEMBLE/Doc/testEvidence/CombineProcess/evidence-20260313-155453/EV-TC-007.md | 関数公開状態と DM の実呼び出しを確認。 |
| TC-08 | FR-09 | トレース漏れ0件 | トレーサビリティ上の不整合は検出されませんでした。 | Pass | EV-TC-008 | studySpecific/ENSEMBLE/Doc/testEvidence/CombineProcess/evidence-20260313-155453/EV-TC-008.md | Markdown 文書を機械照合して確認。 |
| TC-09 | NFR-01 | 性能要件(3秒以内) | 10000 行を 0.664589 秒で処理し、出力形状は (10000, 7) でした。 | Pass | EV-PERF-001 | studySpecific/ENSEMBLE/Doc/testEvidence/CombineProcess/evidence-20260313-155453/EV-PERF-001.md | 擬似データのみ使用し、セットアップ時間は測定対象外。 |
| TC-10 | NFR-04, NFR-05 | セキュリティ/監査性 | DM 列=['SUBJID', 'SEXCD', 'AGE', 'LSVDAT', 'DTHDAT', 'RFENDAT', 'DTHFLG']; 想定外列=なし; TE/TM に変更履歴セクションが存在。 保存後証跡リンク確認: EV-SEC-001[TE=True,TM=True], EV-AUD-001[TE=True,TM=True] | Pass | EV-SEC-001, EV-AUD-001 | studySpecific/ENSEMBLE/Doc/testEvidence/CombineProcess/evidence-20260313-155453/EV-SEC-001.md<br>studySpecific/ENSEMBLE/Doc/testEvidence/CombineProcess/evidence-20260313-155453/EV-AUD-001.md | DM 出力は保存前に確認し、TE/TM の証跡リンクは保存後に確認。 |

## 3. 不具合・課題記録

| 課題ID | 起票日 | 概要 | 影響範囲 | 対応方針 | 状態 |
|-------|-------|------|---------|---------|------|
| DEF-001 | 2026-03-13 | なし | - | - | Closed |

## 4. 判定基準

1. 必須TC (TC-01〜TC-08) がすべて Pass であること。
2. 証跡IDがトレーサビリティマトリクスと一致すること。
3. Reviewer/Approver サインが完了していること。

## 5. 承認記録

| 役割 | 氏名 | 署名/記名 | 日付 | 判定 |
|-----|------|----------|------|------|
| 実施者 |  |  |  |  |
| レビュー者 |  |  |  |  |
| 承認者 |  |  |  |  |

## 6. 変更履歴

| 版数 | 日付 | 変更内容 | 担当者 | Git Commit |
|-----|------|---------|--------|------------|
| 1.0 | 2026/02/20 | 新規作成、Git履歴参照に基づく版管理補完、FR-08表現統一（上位工程連携）およびTC-07更新を統合 | 張　泊江（Group A） | `96985d9` |
| 1.1 | 2026/03/13 | CombineProcess の試験実施および証跡保存を反映 | 張　泊江（Group A） | b4b9fd1 |
