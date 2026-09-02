---
name: baseline-gate
description: Use when an agent is about to create iteration/v1/ or run the iteration pipeline for the first time. Validates that baseline/ contains all required baseline documents with status:Approved.
---

# Baseline Gate

## Purpose

在首次创建 `iteration/v1/` 或运行迭代流水线之前，校验 `baseline/` 是否完整、全部 `status: Approved`。

任何未通过本门禁的请求，必须先完成 baseline，不得直接进入版本化产物生成。

## Required Baseline Artifacts

`baseline/` 下必须存在以下四个文件，且 frontmatter `status: Approved`：

| # | 文件 | 校验点 |
|---|---|---|
| 1 | `baseline/01-product-vision.md` | 存在 + `status: Approved` |
| 2 | `baseline/02-product-charter.md` | 存在 + `status: Approved` |
| 3 | `baseline/03-tech-stack-decision.md` | 存在 + `status: Approved` |
| 4 | `baseline/04-glossary.md` | 存在 + `status: Approved` |

## Validation Process

1. 逐个检查上述四个文件是否存在。
2. 读取每个文件的 frontmatter，校验 `status: Approved`。
3. 可选：校验 `baseline/decisions/` 下是否存在与本次迭代相关的 ADR（如有 ADR 必填项声明）。
4. 输出校验报告：✅ 通过 / ❌ 缺失项列表。
5. 任何 ❌ 项必须由用户修复后再重试。

## Output

校验报告（chat 内简短输出即可）：

```text
baseline-gate report
  ✅ baseline/01-product-vision.md  status: Approved
  ✅ baseline/02-product-charter.md  status: Approved
  ✅ baseline/03-tech-stack-decision.md  status: Approved
  ✅ baseline/04-glossary.md  status: Approved
→ Baseline gate PASSED. Safe to create iteration/v1/.
```

或失败时列出缺失项。

## Failure Handling

- 不要试图自动填充或修改 baseline 文件。
- 不要跳过门禁。
- 报告缺失项并明确告诉用户："请完成 X 文件并将 status 改为 Approved 后重试"。

## Notes

- 本门禁**仅在创建 `iteration/v1/` 时生效**；`iteration/v2/` 及之后的迭代由 `manage-iteration` 处理，不再走 baseline-gate。
- Baseline 变更后所有未归档的迭代产物可能需要同步更新；变更流程见 `baseline/README.md`。
