# 詳細設計書
## VC_BC05_studyFunctions

| 項目 | 内容 |
|-----|------|
| 文書番号 | DD-ENSEMBLE-001 |
| 版数 | 1.3 |
| 作成日 | 2026年02月02日 |
| 最終更新日 | 2026年02月20日 |
| 作成者 | 張　泊江（Group A） |
| レビュー者 | QA |
| 承認者 | PM |
| 文書ステータス | Draft (レビュー待ち) |
| 対象システム | SDTM_ENSEMBLE マッピング仕様書 |
| 対象モジュール | VC_BC05_studyFunctions.py |
| 参照文書 | 要件定義書 (RD-ENSEMBLE-001), 基本設計書 (BD-ENSEMBLE-001) |

---

## 0. 実装方針 (Technical Approach)
本モジュールは Python + pandas を用いて実装する。
**Group A 開発担当者への指示**:
- データの結合は必ず `pd.merge` の `how='left'` を使用すること。
- 日付比較ロジックでは、`pd.isnull()` や `fillna('')` を適切に使用し、NaN の伝播を防ぐこと。
- 警告出力は `print` または標準の `logging` モジュールを使用すること。
- 文書粒度ルールとして、RD/BD は実装非依存（関数名中心）とし、本DD以降でモジュール名・ファイル名を管理すること。

---

## 1. filter_df_by_field 関数

### 1.1 機能概要

指定された条件でDataFrameをフィルタリングし、全空列を除去した結果を返却する汎用関数。

**対応要件ID:** FR-01, FR-02, FR-03

### 1.2 関数シグネチャ

```python
def filter_df_by_field(source, **filters) -> pd.DataFrame
```

### 1.3 入力仕様

| パラメータ名 | 型 | 必須 | 説明 |
|------------|---|-----|------|
| source | str, pd.DataFrame | ○ | テーブル名文字列またはDataFrame |
| **filters | dict | ○ | フィルタリング条件（1つのみ指定可能） |

#### filters の例
```python
filter_df_by_field('TME', EventId='AT REGISTRATION')
filter_df_by_field(tme_df, EventId='AT REGISTRATION')
```

### 1.4 出力仕様

| 戻り値 | 型 | 説明 |
|-------|---|------|
| filtered_df | pd.DataFrame | フィルタリング済み、全列が文字列型 |

### 1.5 処理フロー

```mermaid
flowchart TD
    A["開始"] --> B{"sourceの型判定"}
    B -->|文字列| C["getFormatDataset()でDataFrame取得"]
    B -->|DataFrame| D["sourceをコピー"]
    C --> E["filters検証<br/>(1つのみ許可)"]
    D --> E
    E --> F{"フィールド存在確認"}
    F -->|存在しない| G["KeyError発生"]
    F -->|存在する| H["値でフィルタリング"]
    H --> I{"結果が空か?"}
    I -->|空| J["空のDataFrame返却"]
    I -->|非空| K["全空列を削除"]
    K --> L["全列を文字列型に変換"]
    L --> M["終了"]
    J --> M
```

### 1.6 例外処理

| 例外 | 発生条件 |
|-----|---------|
| ValueError | source が None、または filters が1つでない |
| TypeError | source が DataFrame でも文字列でもない |
| KeyError | 指定フィールドが存在しない、またはテーブル名が見つからない |

---

## 2. DM 関数

### 2.1 機能概要

臨床試験の症例統計情報（DM）データセットを生成する。複数のデータソースを結合し、研究終了日と死亡フラグを導出する。

**対応要件ID:** FR-04, FR-05, FR-06, FR-07, FR-08

### 2.2 関数シグネチャ

```python
def DM() -> pd.DataFrame
```

### 2.3 データソース仕様

#### RGST（症例登録）- 主テーブル

| フィールドID | 日本語名 | データ型 | 例 |
|-------------|---------|---------|-----|
| SUBJID | 症例ID | 文字列 | NE-EN-0001 |
| SEXCD | 性別コード | 文字列 | M / F |
| AGE | 同意取得時年齢 | 数値 | 34 |

#### LSVDAT（最終生存確認日）

| フィールドID | 日本語名 | データ型 | 例 |
|-------------|---------|---------|-----|
| SUBJID | 症例ID | 文字列 | NE-EN-0001 |
| LSVDAT | 最終生存確認日 | 日付 | 2025/11/10 |

#### OC（転帰）

| フィールドID | 日本語名 | データ型 | 例 |
|-------------|---------|---------|-----|
| SUBJID | 症例ID | 文字列 | NE-EN-0001 |
| DTHDAT | 死亡日 | 日付 | 2025/10/31 |

### 2.4 出力フィールド仕様

| No. | フィールドID | 日本語名 | データ型 | 導出ロジック |
|-----|-------------|---------|---------|-------------|
| 1 | SUBJID | 症例ID | 文字列 | RGSTから継承 |
| 2 | SEXCD | 性別コード | 文字列 | RGSTから継承 |
| 3 | AGE | 同意取得時年齢 | 文字列 | RGSTから継承 |
| 4 | LSVDAT | 最終生存確認日 | 文字列 | LSVDATから結合 |
| 5 | DTHDAT | 死亡日 | 文字列 | OCから結合 |
| 6 | RFENDAT | 研究終了日 | 文字列 | **導出**（下記参照） |
| 7 | DTHFLG | 死亡フラグ | 文字列 | **導出**（下記参照） |

### 2.5 処理フロー

```mermaid
flowchart TD
    A["開始"] --> B["getFormatDataset()で<br/>LSVDAT, OC, RGST取得"]
    B --> C["LSVDAT: SUBJID, LSVDAT抽出"]
    B --> D["OC: SUBJID, DTHDAT抽出"]
    B --> E["RGST: 全列コピー"]
    C --> F["RGST + LSVDAT<br/>左結合 on SUBJID"]
    D --> F
    E --> F
    F --> G["NaNを空文字列に変換"]
    G --> H["データ品質チェック①<br/>LSVDAT と DTHDAT 両方存在"]
    H --> I["データ品質チェック②<br/>LSVDAT と DTHDAT 両方空"]
    I --> J["RFENDAT導出"]
    J --> K["DTHFLG導出"]
    K --> L["全列を文字列型に変換"]
    L --> M["終了"]
```

### 2.6 導出ロジック詳細

#### RFENDAT（研究終了日）

```python
RFENDAT = DTHDAT if DTHDAT != '' else LSVDAT
```

| 条件 | RFENDAT値 |
|-----|----------|
| DTHDATが存在する | DTHDAT |
| DTHDATが空、LSVDATが存在する | LSVDAT |
| 両方空 | 空文字列 |

> [!IMPORTANT]
> **優先順位**: DTHDAT > LSVDAT

#### DTHFLG（死亡フラグ）

```python
DTHFLG = 'Y' if DTHDAT != '' else ''
```

| 条件 | DTHFLG値 |
|-----|---------|
| DTHDATが存在する | Y |
| DTHDATが空 | 空文字列 |

### 2.7 データ品質チェック

| No. | チェック内容 | 警告メッセージ例 |
|-----|------------|-----------------|
| 1 | LSVDATとDTHDATが両方存在 | `[DM] 警告: X 名の症例に LSVDAT と DTHDAT が同時に存在します` |
| 2 | LSVDATとDTHDATが両方空 | `[DM] 警告: X 名の症例の LSVDAT と DTHDAT が共に空です` |

### 2.8 結合仕様

| 結合順序 | 左テーブル | 右テーブル | キー | 結合方式 |
|---------|----------|----------|-----|---------|
| 1 | RGST | LSVDAT | SUBJID | LEFT JOIN |
| 2 | 結果1 | OC | SUBJID | LEFT JOIN |

---

## 3. サンプルデータ

### 3.1 入力データ例

**RGST.csv**
| SUBJID | SEXCD | AGE |
|--------|-------|-----|
| NE-EN-0001 | M | 34 |
| NE-EN-0015 | M | 49 |
| NE-EN-0027 | M | 52 |

**LSVDAT.csv**
| SUBJID | LSVDAT |
|--------|--------|
| NE-EN-0001 | 2025/11/10 |
| NE-EN-0027 | - |

**OC.csv**
| SUBJID | DTHDAT |
|--------|--------|
| NE-EN-0015 | 2025/10/31 |
| NE-EN-0027 | 2025/10/20 |

### 3.2 出力データ例

**F-DM.csv**
| SUBJID | SEXCD | AGE | LSVDAT | DTHDAT | RFENDAT | DTHFLG |
|--------|-------|-----|--------|--------|---------|--------|
| NE-EN-0001 | M | 34 | 2025-11-10 | | 2025-11-10 | |
| NE-EN-0015 | M | 49 | | 2025-10-31 | 2025-10-31 | Y |
| NE-EN-0027 | M | 52 | | 2025-10-20 | 2025-10-20 | Y |

---

## 4. テスト仕様

| TC-ID | 対応要件ID | テストケース | 入力条件 | 期待結果 | 証跡ID | 実施結果 |
|------|-----------|------------|---------|---------|-------|---------|
| TC-01 | FR-05, FR-06 | LSVDATのみ存在する症例 | DTHDAT空, LSVDAT有り | RFENDAT = LSVDAT, DTHFLG = 空 | EV-TC-001 | 未実施 |
| TC-02 | FR-05, FR-06 | DTHDATのみ存在する症例 | DTHDAT有り, LSVDAT空 | RFENDAT = DTHDAT, DTHFLG = Y | EV-TC-002 | 未実施 |
| TC-03 | FR-05, FR-06, FR-07 | LSVDAT と DTHDAT 両方存在 | DTHDAT有り, LSVDAT有り | RFENDAT = DTHDAT, DTHFLG = Y, 警告出力 | EV-TC-003 | 未実施 |
| TC-04 | FR-05, FR-06, FR-07 | LSVDAT と DTHDAT 両方空 | DTHDAT空, LSVDAT空 | RFENDAT = 空, DTHFLG = 空, 警告出力 | EV-TC-004 | 未実施 |
| TC-05 | FR-01, FR-02, FR-03 | filter 正常系 | 既存フィールドで1条件抽出 | 条件一致行のみ、全空列削除、全列文字列型 | EV-TC-005 | 未実施 |
| TC-06 | FR-01 | filter 異常系 | 存在しないフィールド指定 | KeyError 発生 | EV-TC-006 | 未実施 |
| TC-07 | FR-08 | 上位工程連携確認 | `VC_BC04_operateType.py` から研究固有関数呼出 | 関数呼び出しが成功し結果が返る | EV-TC-007 | 未実施 |
| TC-08 | FR-09 | トレーサビリティ確認 | RD/BD/DD/Code/Test を照合 | 対応漏れ0件 | EV-TC-008 | 未実施 |
| TC-09 | NFR-01 | 性能検証 | 擬似データ(1万件)処理 | 3秒以内に完了 | EV-PERF-001 | 未実施 |
| TC-10 | NFR-04, NFR-05 | セキュリティ・監査性確認 | ログおよび出力結果確認 | 個人情報非表示、版数記録有 | EV-SEC-001, EV-AUD-001 | 未実施 |

---

## 5. 要件-設計-実装-試験トレーサビリティ

| 要件ID | 詳細設計の対応節 | 実装対応 | テストID |
|-------|------------------|---------|---------|
| FR-01 | 1.1-1.6 | `VC_BC05_studyFunctions.py` `filter_df_by_field` | TC-05, TC-06 |
| FR-02 | 1.1, 1.5 | `VC_BC05_studyFunctions.py` 全空列削除処理 | TC-05 |
| FR-03 | 1.4, 1.5 | `VC_BC05_studyFunctions.py` 文字列型統一返却 | TC-05 |
| FR-04 | 2.3, 2.8 | `VC_BC05_studyFunctions.py` RGST/LSVDAT/OC 結合 | TC-01, TC-02 |
| FR-05 | 2.6 | `VC_BC05_studyFunctions.py` RFENDAT導出 | TC-01, TC-02, TC-03, TC-04 |
| FR-06 | 2.6 | `VC_BC05_studyFunctions.py` DTHFLG導出 | TC-01, TC-02, TC-03, TC-04 |
| FR-07 | 2.7 | `VC_BC05_studyFunctions.py` 品質チェック通知 | TC-03, TC-04 |
| FR-08 | 0章, 2章 | `VC_BC04_operateType.py` 研究固有関数連携 | TC-07 |
| FR-09 | 4章, 5章 | トレーサビリティマトリクス/テスト実施記録 | TC-08 |
| NFR-01 | 0章 | pandas 処理実装 (ベクトル化) | TC-09 |
| NFR-02..05 | 2.7, 4章 | 品質チェック、ログ出力、個人情報保護 | TC-03, TC-04, TC-10 |

---

## 6. 変更履歴

| 版数 | 日付 | 変更内容 | 担当者 | Git Commit |
|-----|------|---------|--------|------------|
| 0.1 | 2026/02/02 | VC_BC05 コード初版作成 (機能起点) | 張　泊江（Group A） | `09ffaf8` |
| 0.2 | 2026/02/02 | VC_BC05 コード追補 | 張　泊江（Group A） | `8c60da9` |
| 1.0 | 2026/02/13 | 設計文書初版作成 (RD/BD/DD) | 張　泊江（Group A） | `c8d9201` |
| 1.1 | 2026/02/13 | VC_BC05 モジュール連動に合わせ文書更新 | 張　泊江（Group A） | `01d23e6` |
| 1.2 | 2026/02/13 | 設計文書リファクタリング | 張　泊江（Group A） | `e449ccc` |
| 1.3 | 2026/02/20 | メタ情報/要件対応ID/TC-ID/証跡ID/要件-実装-試験トレーサビリティ整備に加え、RD/BD実装非依存方針に合わせたDD粒度ルール明記とFR-08/TC-07表現統一を反映してWIP変更を統合 | 張　泊江（Group A） | `WIP` |
