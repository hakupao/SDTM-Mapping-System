# EV-TC-001

- テストID: `TC-01`
- テストケース: LSVDAT のみ存在する症例
- 対応要件: FR-05, FR-06
- 実施日: 2026-03-13
- 実行モード: 保存実行
- 判定: **Pass**

## 期待結果
RFENDAT が LSVDAT と一致し、DTHFLG は空欄のままであること。

## 実測結果
NE-EN-0001: LSVDAT=2025-11-10, DTHDAT=<空欄>, RFENDAT=2025-11-10, DTHFLG=<空欄>

## 備考
実データの対象症例: NE-EN-0001

## 確認データ行
```csv
SUBJID,SEXCD,AGE,LSVDAT,DTHDAT,RFENDAT,DTHFLG
NE-EN-0001,M,34,2025-11-10,,2025-11-10,
```
