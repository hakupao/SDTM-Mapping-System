# EV-TC-003

- テストID: `TC-03`
- テストケース: LSVDAT と DTHDAT が両方存在する警告ケース
- 対応要件: FR-05, FR-06, FR-07
- 実施日: 2026-03-13
- 実行モード: 保存実行
- 判定: **Pass**

## 期待結果
RFENDAT は DTHDAT を優先し、DTHFLG は Y、かつ警告が出力されること。

## 実測結果
擬似症例 TEST-BOTH: RFENDAT=2025-10-31, DTHFLG=Y, 警告出力=あり

## 備考
1 行の擬似データセットで確認。

## 確認データ行
```csv
SUBJID,SEXCD,AGE,LSVDAT,DTHDAT,RFENDAT,DTHFLG
TEST-BOTH,M,34,2025-11-10,2025-10-31,2025-10-31,Y
```

## 取得した警告
```text
[DM] 警告: 1 名受试者同时存在 LSVDAT 和 DTHDAT:
   SUBJID     LSVDAT     DTHDAT
TEST-BOTH 2025-11-10 2025-10-31
```
