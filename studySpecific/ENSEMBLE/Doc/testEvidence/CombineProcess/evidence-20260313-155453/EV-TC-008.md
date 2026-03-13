# EV-TC-008

- テストID: `TC-08`
- テストケース: トレーサビリティ照合
- 対応要件: FR-09
- 実施日: 2026-03-13
- 実行モード: 保存実行
- 判定: **Pass**

## 期待結果
RD/BD/DD/TE/TM の要件ID、TC-ID、証跡ID が相互に整合していること。

## 実測結果
トレーサビリティ上の不整合は検出されませんでした。

## 備考
Markdown 文書を機械照合して確認。

## 照合した集合
```json
{
  "rd_requirements": [
    "FR-01",
    "FR-02",
    "FR-03",
    "FR-04",
    "FR-05",
    "FR-06",
    "FR-07",
    "FR-08",
    "FR-09",
    "NFR-01",
    "NFR-02",
    "NFR-03",
    "NFR-04",
    "NFR-05"
  ],
  "bd_requirements": [
    "FR-01",
    "FR-02",
    "FR-03",
    "FR-04",
    "FR-05",
    "FR-06",
    "FR-07",
    "FR-08",
    "FR-09"
  ],
  "tm_requirements": [
    "FR-01",
    "FR-02",
    "FR-03",
    "FR-04",
    "FR-05",
    "FR-06",
    "FR-07",
    "FR-08",
    "FR-09",
    "NFR-01",
    "NFR-02",
    "NFR-03",
    "NFR-04",
    "NFR-05"
  ],
  "dd_tc_ids": [
    "TC-01",
    "TC-02",
    "TC-03",
    "TC-04",
    "TC-05",
    "TC-06",
    "TC-07",
    "TC-08",
    "TC-09",
    "TC-10"
  ],
  "te_tc_ids": [
    "TC-01",
    "TC-02",
    "TC-03",
    "TC-04",
    "TC-05",
    "TC-06",
    "TC-07",
    "TC-08",
    "TC-09",
    "TC-10"
  ],
  "tm_tc_ids": [
    "TC-01",
    "TC-02",
    "TC-03",
    "TC-04",
    "TC-05",
    "TC-06",
    "TC-07",
    "TC-08",
    "TC-09",
    "TC-10"
  ],
  "dd_evidence_ids": [
    "EV-AUD-001",
    "EV-PERF-001",
    "EV-SEC-001",
    "EV-TC-001",
    "EV-TC-002",
    "EV-TC-003",
    "EV-TC-004",
    "EV-TC-005",
    "EV-TC-006",
    "EV-TC-007",
    "EV-TC-008"
  ],
  "te_evidence_ids": [
    "EV-AUD-001",
    "EV-PERF-001",
    "EV-SEC-001",
    "EV-TC-001",
    "EV-TC-002",
    "EV-TC-003",
    "EV-TC-004",
    "EV-TC-005",
    "EV-TC-006",
    "EV-TC-007",
    "EV-TC-008"
  ],
  "tm_evidence_ids": [
    "EV-AUD-001",
    "EV-PERF-001",
    "EV-SEC-001",
    "EV-TC-001",
    "EV-TC-002",
    "EV-TC-003",
    "EV-TC-004",
    "EV-TC-005",
    "EV-TC-006",
    "EV-TC-007",
    "EV-TC-008"
  ]
}
```
