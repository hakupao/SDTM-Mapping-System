# EV-TC-004

- テストID: `TC-04`
- テストケース: LSVDAT と DTHDAT が両方空の警告ケース
- 対応要件: FR-05, FR-06, FR-07
- 実施日: 2026-03-13
- 実行モード: 保存実行
- 判定: **Pass**

## 期待結果
RFENDAT と DTHFLG が空欄となり、警告が出力されること。

## 実測結果
擬似症例 TEST-NONE: RFENDAT=<空欄>, DTHFLG=<空欄>, 警告出力=あり

## 備考
1 行の擬似データセットで確認。

## 確認データ行
```csv
SUBJID,SEXCD,AGE,LSVDAT,DTHDAT,RFENDAT,DTHFLG
TEST-NONE,F,40,,,,
```

## 取得した警告
```text
[DM] 警告: 1 名受试者 LSVDAT 和 DTHDAT 均为空:
   SUBJID
TEST-NONE
```
