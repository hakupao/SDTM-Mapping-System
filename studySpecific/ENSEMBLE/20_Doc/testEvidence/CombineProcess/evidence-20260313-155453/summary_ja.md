# 実施結果サマリー

- 実施日時: 2026-03-13T15:54:53.990166+09:00
- 実行モード: 保存実行
- 実施日: 2026-03-13
- 実施環境: Python 3.11.9 / pandas 3.0.1 / openpyxl 3.1.5
- 証跡フォルダ: studySpecific/ENSEMBLE/Doc/testEvidence/CombineProcess/evidence-20260313-155453
- 合計件数: 10
- Pass: 10
- Fail: 0
- 総合判定: Pass

## ケース別結果

### TC-01 LSVDAT のみ存在する症例
- 判定: Pass
- 実測結果: NE-EN-0001: LSVDAT=2025-11-10, DTHDAT=<空欄>, RFENDAT=2025-11-10, DTHFLG=<空欄>
- 備考: 実データの対象症例: NE-EN-0001

### TC-02 DTHDAT のみ存在する症例
- 判定: Pass
- 実測結果: NE-EN-0015: LSVDAT=<空欄>, DTHDAT=2025-10-31, RFENDAT=2025-10-31, DTHFLG=Y
- 備考: 実データの対象症例: NE-EN-0015

### TC-03 LSVDAT と DTHDAT が両方存在する警告ケース
- 判定: Pass
- 実測結果: 擬似症例 TEST-BOTH: RFENDAT=2025-10-31, DTHFLG=Y, 警告出力=あり
- 備考: 1 行の擬似データセットで確認。

### TC-04 LSVDAT と DTHDAT が両方空の警告ケース
- 判定: Pass
- 実測結果: 擬似症例 TEST-NONE: RFENDAT=<空欄>, DTHFLG=<空欄>, 警告出力=あり
- 備考: 1 行の擬似データセットで確認。

### TC-05 filter_df_by_field 正常系
- 判定: Pass
- 実測結果: 実データ抽出行数=200; 擬似データ列=['EventId', 'KEEP', 'FLAG']; 擬似データ型=['str', 'str', 'str']
- 備考: 実データの TME と擬似 DataFrame を組み合わせて確認。

### TC-06 filter_df_by_field 異常系
- 判定: Pass
- 実測結果: 存在しないフィールド指定により KeyError が発生。
- 備考: 実データの TME に存在しないフィールドを指定して確認。

### TC-07 VC_BC04_operateType からの上位工程連携
- 判定: Pass
- 実測結果: VC_BC04_operateType から研究固有関数を呼び出し、DM 形状=(200, 7) を取得。
- 備考: 関数公開状態と DM の実呼び出しを確認。

### TC-08 トレーサビリティ照合
- 判定: Pass
- 実測結果: トレーサビリティ上の不整合は検出されませんでした。
- 備考: Markdown 文書を機械照合して確認。

### TC-09 1万件擬似データによる性能試験
- 判定: Pass
- 実測結果: 10000 行を 0.664589 秒で処理し、出力形状は (10000, 7) でした。
- 備考: 擬似データのみ使用し、セットアップ時間は測定対象外。

### TC-10 セキュリティおよび監査性確認
- 判定: Pass
- 実測結果: DM 列=['SUBJID', 'SEXCD', 'AGE', 'LSVDAT', 'DTHDAT', 'RFENDAT', 'DTHFLG']; 想定外列=なし; TE/TM に変更履歴セクションが存在。 保存後証跡リンク確認: EV-SEC-001[TE=True,TM=True], EV-AUD-001[TE=True,TM=True]
- 備考: DM 出力は保存前に確認し、TE/TM の証跡リンクは保存後に確認。

## 保存後検証

- 判定: Pass
- 指摘: なし
