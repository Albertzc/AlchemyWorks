---
name: stage-gate
description: Use when starting, handing off, or reviewing any workflow stage. Enforces required inputs, human approval, and the gate that must pass before the next stage begins.
---

# Stage Gate

## Purpose

统一管理工作流的阶段门禁。所有正式产物阶段（项目基线、01-product 至 05-review-release）均须由人工审核；当前阶段的必需产物全部为 `status: Approved` 且校验通过后，才可进入下一阶段。

## Stage Order

```text
用户原始需求（非结构化输入）
    ↓ normalize-requirement 路由与归档
00-baseline（仅首次项目）
    ↓
01-product → 02-design → 03-planning → 04-implementation → 05-review-release
```

## Required Inputs

### 00-baseline

以下项目级产物必须存在且 `status: Approved`：

1. `baseline/01-product-vision.md`
2. `baseline/02-product-charter.md`
3. `baseline/03-tech-stack-decision.md`
4. `baseline/04-glossary.md`
5. `baseline/05-core-user-flow-prototype.html`（覆盖核心角色、关键任务闭环、关键状态和权限差异的可评审交互原型；低保真即可）

### 01-product 原型决策

每个版本的 `requirement.md` frontmatter 必须明确 `prototype_required: true` 或 `prototype_required: false`。这是人工可审阅、门禁可校验的决策记录：

- `true`：`v{major}.{minor}-prototype.html` 成为该版本 01-product 的必需且需 Approved 的产物。适用于新页面、复杂/跨页面流程、影响业务结果的交互、体验重点、多端适配或评审存在交互分歧的改动。
- `false`：原型不作为该版本门禁产物；frontmatter 中非空的 `prototype_baseline` 与 `prototype_rationale` 是必需门禁字段，需求与功能规格也必须记录沿用的交互基线和不制作原型的理由。适用于纯后端或非 UI 改动、复用既有模式的轻量 UI 改动，以及能由规格和验收标准无歧义表达的改动。

Baseline 核心流程原型始终必需；功能迭代的页面原型按上述决策按需生成。
## Raw Requirement Intake

原始需求是用户提供的来源材料，格式可以是不带 frontmatter 的 Markdown、文本、邮件、会议纪要或其他可读取文件。它不属于需要 `Approved` 的阶段产物，Agent 不得改写其原文。

- `baseline/` 除 `README.md` 外为空时：归档到 `baseline/raw-requirement/`，并由 `normalize-requirement` 起草 baseline 文档。
- baseline 已初始化时：运行 `python .workflow/workflow.py route-requirement`；该命令优先使用 `.workflow/manifest.yaml` 的 `iteration` 字段确定版本，并输出集中原始需求库 `iteration/raw-requirement/` 和目标版本。该目录仅保存用户输入，Agent 只读。
- 归一化后的 baseline 或产品需求才进入人工审核与 `stage-gate`。

## Ownership Boundary

本 Skill 只定义**门禁政策**：阶段顺序、必需产物、人工审批和允许进入下一阶段的条件。它不定义或重复工作流 CLI 的运行步骤。

`workflow-governance` 是索引、状态恢复、Context Pack、`validate` 和任务结论命令的唯一操作入口。开始、交接或审核阶段时，先使用该 Skill 执行命令；其 `validate` 结果是本 Skill 政策是否满足的唯一可执行证据。

## Handoff Policy

1. Agent 只创建或更新 `draft` / `In Review` 产物，并列出审核所需的路径与证据。
2. 人工审核后手动把本阶段全部必需产物设为 `Approved`。
3. 仅当 `workflow-governance` 执行的对应阶段校验返回 0 时，才可开始下一阶段；非零结果是硬性停止条件。

## Failure Handling

- 不得跳过任一阶段、审核或门禁。
- 不得由 Agent 写入或修改 `status: Approved`。
- 原始需求缺失、无法读取，或归一化产物未保留其可追溯来源时，停止并要求补正。

## Output

报告应列出：当前阶段、所有必需产物、每个产物的状态、校验命令与结果，以及下一步是否允许开始。
