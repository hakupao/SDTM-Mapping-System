# COSMOS_GC 文档体系模板套件 — 设计 spec

| 项目 | 内容 |
|---|---|
| 日付 | 2026-05-19 |
| 作成者 | 張　泊江 + Claude (brainstorming) |
| 状态 | Draft — 待用户审阅 |
| 关联 guide | `studySpecific/COSMOS_GC/20_Doc/_BACKGROUND_INTERNAL.md`、`_BC05_TO_DOCS_AGENT_GUIDE.md` |

---

## 1. 问题陈述

当前 `studySpecific/COSMOS_GC/20_Doc/` 已经有两份对齐文件：

- **`_BACKGROUND_INTERNAL.md`**：回答「为什么」——A/B 比对、双重身份、代码 vs config 契约、业务意图 vs 实装等硬约束的动机
- **`_BC05_TO_DOCS_AGENT_GUIDE.md`**：回答「怎么做」——通用工程作业书，规定抽取规则、ID 体系、分层、禁词、验收清单

但用 agent 只凭 code + 这两份 guide 生成 00-06 文档时，会有以下问题：

1. **章节结构不稳定**：agent 自行决定章节顺序，导致 7 份文档结构每次不同
2. **风险点露空**：代码 vs config 归属、R-xx 业务意图、字段名禁出现地等高风险点没有强制护栏
3. **研究特异信息缺口**：业务背景叙事、字段日英对照、人员、`{OPERATION_CONF}` 文件名等无法纯从 code 推出，必须由 protocol + config Excel 提供
4. **跨文档 ID 不一致**：7 份文档若分别生成，FR/F/R/TC/EV/TR 编号容易错位

设计目标：**通过模板 + 输入档案，加上既有两份 guide，形成三层约束体系，把 00-06 文档生成稳定到「同样输入 → 同样输出」**。

---

## 2. 已对齐的设计决策

| 决策点 | 选择 |
|---|---|
| 套件范围 | 模板 + 输入档案（不含独立的抽取工作表） |
| 输入档案格式 | 纯 Markdown |
| 全部文件位置 | `studySpecific/COSMOS_GC/20_Doc/` |
| 占位符语法 | `{{IDENTIFIER}}` + `<!-- BEGIN: block_name -->...<!-- END: block_name -->` |
| 行内护栏 | `<!-- RULE-GUARD §x.y: 一句话约束 -->` 引用既有 guide 章节号 |

---

## 3. 文件清单

总共 **9 个新文件**，全部置于 `studySpecific/COSMOS_GC/20_Doc/`，文件名带 `_` 前缀以与现存 00-06 区分。

| 角色 | 文件 |
|---|---|
| 输入档案 | `_STUDY_INPUT_PROFILE.md` |
| 模板 README | `_TEMPLATES_README.md` |
| 模板 00 | `_TEMPLATE_00_文書統制計画書.md` |
| 模板 01 | `_TEMPLATE_01_要件定義書.md` |
| 模板 02 | `_TEMPLATE_02_基本設計書.md` |
| 模板 03 | `_TEMPLATE_03_詳細設計書.md` |
| 模板 04 | `_TEMPLATE_04_テスト実施記録.md` |
| 模板 05 | `_TEMPLATE_05_トレーサビリティマトリクス.md` |
| 模板 06 | `_TEMPLATE_06_文書統制報告書.md` |

---

## 4. 三层约束体系

```
┌───────────────────────────────────────────────────────────────┐
│ _BACKGROUND_INTERNAL.md     回答「为什么」                      │
│   ── A/B 比对、双重身份、代码 vs config、业务意图 vs 実装        │
│ _BC05_TO_DOCS_AGENT_GUIDE.md 回答「怎么做」                    │
│   ── 抽取规则、ID 体系、分层、禁词、验收清单                    │
│ _TEMPLATE_*.md              回答「长什么样」                    │
│   ── 章节固定、占位符、行内护栏（引用上两份 §x.y）              │
└───────────────────────────────────────────────────────────────┘
        ↓ 三层叠加，缺一不可
  _STUDY_INPUT_PROFILE.md（研究特异数据）→ 7 份 00-06 文档
```

模板**不复述**两份 guide 的规则，只在风险点用 `<!-- RULE-GUARD §x.y -->` 引用章节号。这样三份文件各司其职，guide 修订后模板无需同步改动。

---

## 5. `_STUDY_INPUT_PROFILE.md` 结构（8 节）

每节顶部有 `<!-- SOURCE: ... -->` 注释，标明 agent 应从哪里抽取。

| 节 | 内容 | 来源 |
|---|---|---|
| §1 Identifiers | `STUDY_ID`、`PROCESS_NAME`、`OPERATION_CONF`、`FUNCTION_MODULE`、`FUNCTION_MODULE_PATH` | code module path + 命名约定 |
| §2 People | 作成者 / レビュー者 / 承認者 | 用户输入 |
| §3 Dates | 作成日、最終更新日 | 系统日期 + 用户确认 |
| §4 Study background | 1 段中性叙事（不含医院名/主导方等敏感背景） | protocol §背景或目的 |
| §5 F-* sources | `F-XXX` → 业务释义 + 字段日英对照（仅 BD/DD 用） | protocol 字段定义 + code 抽取的字段集 |
| §6 公开函数表 | 函数名、引数、引数指定形式、戻り値型、对応 FR | code 直接抽取 |
| §7 R-xx 业务规则 | 业务意图、A 组现行实装、A/B 差分预测（三列并排） | protocol 业务讨论 + code 实装行为 |
| §8 代表症例 sample | DD §4 サンプルデータ用脱敏样例 | protocol 代表症例 + 脱敏 |

§7 是稳定 A/B 比对的关键——agent 填写时若发现业务意图与现行实装不一致，必须**在「业务意图」列写意图、在「A 组实装」列写实装、在「A/B 差分预测」列写检知点**，由模板 BD/DD/TE 各取所需。

---

## 6. 占位符规约

| 语法 | 用途 | 示例 |
|---|---|---|
| `{{IDENTIFIER}}` | 单值替换 | `{{STUDY_ID}}` → `COSMOS_GC` |
| `<!-- BEGIN: block_name -->`...`<!-- END: block_name -->` | 可重复块 | F-* 数据源表行、公开函数表行、R-xx 规则块 |
| `<!-- RULE-GUARD §x.y: 一句话 -->` | 规则护栏 | `<!-- RULE-GUARD §5.2: 不写文件名/保存先/格式 -->` |
| `<!-- HINT: ... -->` | 填写提示 | 仅在 agent 易踩坑的位置 |

模板的章节结构、表头、变更履历首行格式都是**硬编码**的，agent 只能填占位符——这是稳定性的核心机制。

---

## 7. 生成流程（由 `_TEMPLATES_README.md` 规定）

```
Step 0  读取 _BACKGROUND_INTERNAL.md（理解约束动机）
Step 1  读取 _BC05_TO_DOCS_AGENT_GUIDE.md（理解抽取/分层规则）
Step 2  读取 _TEMPLATES_README.md（理解占位符与流程）

Step 3  抽取阶段：
        ├─ protocol PDF/Word → §4 背景、§5 F-* 释义、§7 R-xx 业务意图
        ├─ {OPERATION_CONF}.xlsx → §1 OPERATION_CONF 文件名、调用规约
        └─ {FUNCTION_MODULE}.py → §1 STUDY_ID、§6 公开函数、§7 现行实装行为

Step 4  把抽取结果填入 _STUDY_INPUT_PROFILE.md（不直接写 00-06）

Step 5  用 input profile 填充 7 份模板 → 输出 00-06 到 MarkDown/

Step 6  运行 guide §10 验收清单（自动化验证）
```

抽取阶段（Step 3-4）和填充阶段（Step 5）**严格分离**——这保证 input profile 可以独立审阅、修改、复核，而不会污染 00-06 的章节结构。

---

## 8. 稳定性保证机制

| 风险 | 对应护栏 |
|---|---|
| Agent 把文件名写成代码契约 | RD §1.3 / BD §1 / DD §0 顶部 `<!-- RULE-GUARD §5.2 -->` |
| BD R-xx 按 A 组实装反推 | R-xx 表头 `<!-- RULE-GUARD §7: 業務意図のみ -->` |
| RD 误用字段名 | RD 章节顶部 `<!-- RULE-GUARD §5.3: フィールド名禁止 -->` |
| 章节漏写或顺序错 | 模板固定章节，agent 只能填占位符 |
| 跨文档 ID 不一致 | 7 份模板均从同一 input profile 取值 |
| 禁词混入 | 模板预先不含禁词；agent 验收阶段跑 guide §11 命令 |

---

## 9. YAGNI 取舍（实施期再定）

| 项 | 倾向 | 理由 |
|---|---|---|
| DD Mermaid 流程图 | 保留占位 mermaid 块 | 现存 DD §2.5/§3.4 都有 mermaid，agent 需要骨架引导 |
| 変更履歴 Git Commit 列 | 保留（值 `-`） | 与现存一致，未来填实际 commit hash |
| 行内 `<!-- HINT -->` 数量 | 仅高风险章节 ~10-15 处 | 全章节加注释会让模板比成品文档还长，反成噪音 |

---

## 10. Scope 边界

**In scope**：
- 9 个新文件（input profile + readme + 7 模板）
- 文件全部置于 `studySpecific/COSMOS_GC/20_Doc/`
- 模板内引用既有两份 guide，但不修改它们

**Out of scope**（本设计**不**包含）：
- 自动化生成脚本（不写 Python/Shell 把 input profile 填进模板的代码）
- 抽取 protocol/config Excel 的自动化（由 agent 在生成时手工读取）
- 现存 00-06 文档的回写（不用新模板重新生成现存 v1.0 文档）
- 跨研究的通用化（模板留在 COSMOS_GC 目录下，未来再决定是否上提）

---

## 11. 未决问题

| 问题 | 决议方式 |
|---|---|
| Mermaid 块在模板里用 placeholder 还是固定一份示意？ | 实施时按 DD §2.5 现存最长流程为参考，写一份带 `{{...}}` 节点名的可改样板 |
| 模板默认 `{{AUTHOR}}` 是匿名占位符还是 `張　泊江`？ | 用占位符 `{{AUTHOR}}`，由 input profile 提供 |
| `_TEMPLATES_README.md` 是否要嵌入禁词命令的可执行块？ | 是。把 guide §11 三条 rg 命令完整抄入，方便复制运行 |

---

## 12. 验收标准（spec 落地后）

- [ ] 9 个文件全部存在于 `studySpecific/COSMOS_GC/20_Doc/`
- [ ] 任何模板的占位符都能在 `_STUDY_INPUT_PROFILE.md` 找到对应字段
- [ ] 每个 `<!-- RULE-GUARD -->` 都能反查到 `_BACKGROUND_INTERNAL.md` 或 `_BC05_TO_DOCS_AGENT_GUIDE.md` 的真实章节号
- [ ] 把 COSMOS_GC 现存事实手工填入 input profile，用模板能复现现存 00-06 的章节结构（不要求文字完全一致，但章节与表头需一致）
- [ ] 模板里没有禁词（研究/病院/主導/医療機関/機能群）
- [ ] 模板里没有 `.csv` 后缀（除非显式带归属语）
