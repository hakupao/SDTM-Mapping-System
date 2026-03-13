# EV-TC-002

- テストID: `TC-02`
- テストケース: DTHDAT のみ存在する症例
- 対応要件: FR-05, FR-06
- 実施日: 2026-03-13
- 実行モード: 保存実行
- 判定: **Pass**

## 期待結果
RFENDAT が DTHDAT と一致し、DTHFLG が Y になること。

## 実測結果
NE-EN-0015: LSVDAT=<空欄>, DTHDAT=2025-10-31, RFENDAT=2025-10-31, DTHFLG=Y

## 備考
実データの対象症例: NE-EN-0015

## 確認データ行
```csv
SUBJID,SEXCD,AGE,LSVDAT,DTHDAT,RFENDAT,DTHFLG
NE-EN-0015,M,49,,2025-10-31,2025-10-31,Y
```
