# EV-AUD-001

- テストID: `TC-10`
- テストケース: 監査観点の証跡リンク確認
- 対応要件: NFR-05
- 実施日: 2026-03-13
- 実行モード: 保存実行
- 判定: **Pass**

## 期待結果
TE/TM に変更履歴セクションと保存済み証跡リンクが保持されること。

## 実測結果
DM 列=['SUBJID', 'SEXCD', 'AGE', 'LSVDAT', 'DTHDAT', 'RFENDAT', 'DTHFLG']; 想定外列=なし; TE/TM に変更履歴セクションが存在。 保存後証跡リンク確認: EV-SEC-001[TE=True,TM=True], EV-AUD-001[TE=True,TM=True]

## 備考
DM 出力は保存前に確認し、TE/TM の証跡リンクは保存後に確認。

## 証跡リンク確認結果
```json
[
  {
    "evidence_id": "EV-SEC-001",
    "in_te": true,
    "in_tm": true
  },
  {
    "evidence_id": "EV-AUD-001",
    "in_te": true,
    "in_tm": true
  }
]
```
