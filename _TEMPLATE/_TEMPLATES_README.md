# 文書テンプレート利用ガイド

本ディレクトリの 9 ファイル（本 README + 入力プロファイル + 7 テンプレート）は、`MarkDown/0X_*.md` 文書群を**安定して**生成するための支援ファイル群である。

> **三層約束**：本ファイル群だけでは不十分。次の 2 ファイルと併せて使うこと。
> - `_BACKGROUND_INTERNAL.md`（なぜ — A/B 比対、契約境界、業務意図 vs 実装）
> - `_BC05_TO_DOCS_AGENT_GUIDE.md`（どう — 抽取規則、ID 体系、分層、禁词、受入チェック）

---

## 1. ファイル構成

| 役割 | ファイル |
|---|---|
| 入力プロファイル | `_STUDY_INPUT_PROFILE.md` |
| テンプレート | `_TEMPLATE_00_文書統制計画書.md` 〜 `_TEMPLATE_06_文書統制報告書.md` |
| 出力先 | `MarkDown/00_..._06_...md` |

---

## 2. プレースホルダ規約

| 構文 | 用途 | 例 |
|---|---|---|
| `{{IDENTIFIER}}` | 単値置換 | `{{STUDY_ID}}` → `COSMOS_GC` |
| `<!-- BEGIN: block_name -->` ... `<!-- END: block_name -->` | 繰り返しブロック | F-* データ源行、R-xx ルール、TC など |
| `<!-- RULE-GUARD §x.y: 一句 -->` | 規則護欄 | `_BACKGROUND_INTERNAL.md` / `_BC05_TO_DOCS_AGENT_GUIDE.md` の章節番号を参照 |
| `<!-- HINT: ... -->` | 記入ヒント | agent が踏みやすい所のみ配置 |

**章節タイトル・表ヘッダ・変更履歴の初版行は HARD-CODED**。agent はプレースホルダのみ填筆し、章節を勝手に追加・順序変更しないこと。

---

## 3. 生成パイプライン（agent が実行する手順）

```
Step 0  _BACKGROUND_INTERNAL.md を読む（約束の動機を理解）
Step 1  _BC05_TO_DOCS_AGENT_GUIDE.md を読む（抽取・分層・禁词規則を理解）
Step 2  本 README を読む（プレースホルダ規約と流れを理解）

Step 3  抽取ステップ：
        ├─ protocol PDF/Word → §4 背景、§5 F-* 釈義、§7 R-xx 業務意図
        ├─ {{OPERATION_CONF}} → §1 OPERATION_CONF 名、呼び出し規約
        └─ {{FUNCTION_MODULE_PATH}} → §1 STUDY_ID、§6 公開関数、§7 現行実装挙動

Step 4  _STUDY_INPUT_PROFILE.md を更新（00-06 は触らない）

Step 5  各 _TEMPLATE_0X_*.md について：
        ├─ {{...}} を input profile 値で置換
        ├─ <!-- BEGIN/END --> ブロックを §5/§6/§7/§8 から展開
        └─ <!-- RULE-GUARD --> と <!-- HINT --> はそのまま残すか削除（最終出力では削除推奨）
        → MarkDown/0X_<ProcessName>.md として出力

Step 6  受入チェック（次節）
```

**抽取（Step 3-4）と填筆（Step 5）は厳密に分離**：input profile は独立にレビュー・修正・再利用できるべき。00-06 を直書きしないこと。

---

## 4. 受入チェック（コピペで実行可）

### 4.1 禁词スキャン（`_BC05_TO_DOCS_AGENT_GUIDE.md §11` 由来）

```bash
# 機関名・主導表現の有無（HTML コメント内のメタ言及は除外）
rg -n "機能群|医療機関|主導|病院" studySpecific/COSMOS_GC/20_Doc/MarkDown/ | rg -v "<!--"
# 期待：no matches
```

```bash
# .csv 後缀（帰属注釈なし）
rg -n "F-[A-Z]+\.csv" studySpecific/COSMOS_GC/20_Doc/MarkDown/ | rg -v "連携設定|責務|OperationConf"
# 期待：no matches（残ったら帰属注を付けるか削除）
```

```bash
# プレースホルダ漏れ
rg -n "\{\{[A-Z_]+\}\}|<!-- BEGIN:|<!-- END:" studySpecific/COSMOS_GC/20_Doc/MarkDown/
# 期待：no matches（残っていたら未展開）
```

### 4.2 ID 体系整合

```bash
# FR-xx, F-xx, R-xx, TC-xx, TR-xx, EV-xx が 5 ファイル横断で一致しているか
for prefix in FR F R TC TR EV; do
  echo "=== $prefix ==="
  rg -oh "${prefix}-[0-9]+" studySpecific/COSMOS_GC/20_Doc/MarkDown/ | sort -u
done
```

### 4.3 初版バージョン規約

```bash
rg -n "^\| 版数 \| 1\.0 \|" studySpecific/COSMOS_GC/20_Doc/MarkDown/
# 期待：7 ファイル全て命中
```

---

## 5. テンプレート別の役割

| テンプレート | 対応文書 | 主な記載粒度 |
|---|---|---|
| `_TEMPLATE_00_文書統制計画書.md` | DP | A/B 共通、文書統制方針 |
| `_TEMPLATE_01_要件定義書.md` | RD | 業務要件（WHAT）。フィールド名・関数名・算法を**書かない** |
| `_TEMPLATE_02_基本設計書.md` | BD | 外部仕様（I/O 責務 + R-xx 業務意図 + 公開 IF 契約）。内部算法を**書かない** |
| `_TEMPLATE_03_詳細設計書.md` | DD | 内部仕様（関数シグネチャ、データ構造、アルゴリズム、TC 設計） |
| `_TEMPLATE_04_テスト実施記録.md` | TE | TC 期待結果 / 実測結果 / 証跡 ID |
| `_TEMPLATE_05_トレーサビリティマトリクス.md` | TM | FR → BD/DD/Code/TC/EV の対応表 |
| `_TEMPLATE_06_文書統制報告書.md` | DR | 統制状況・残課題・是正方針 |

---

## 6. 変更管理

- テンプレート自体の修正は `_BACKGROUND_INTERNAL.md` または `_BC05_TO_DOCS_AGENT_GUIDE.md` の改訂と整合させること
- input profile の §1-§8 構成は固定。新項目を増やす場合は本 README に追記
- 7 テンプレートは独立改訂可（各 v1.0 から開始）
