---
name: release-log
description: Create the post-RC release log at 05-review-release stage. Existence-only contract; no human approval gate.
---

# Release Log

Use this skill when drafting the `v{major}.{minor}-release-log.md`封档说明 for a completed iteration. It records what shipped, what issues closed, the final quality-gate state, hand-off items to the next version, and known limits/assumptions.

## Inputs

Confirm that `05-review-release` review-release.md has been Approved. Read the approved product / design / planning artifacts through their stable-ID references, the implementation record, observed test results, the review-release decision, and the actual diff. Do not claim checks passed unless their output was observed.

Required reading before drafting:

- `iteration/v{major}.{minor}/05-review-release/v{major}.{minor}-review-release.md` — Approved
- `iteration/v{major}.{minor}/01-product/v{major}.{minor}-requirement.md` — Approved,含 change_set
- `iteration/v{major}.{minor}/04-implementation/v{major}.{minor}-source-code.md` — 含 ISSUE 列表
- `iteration/v{major}.{minor}/04-implementation/v{major}.{minor}-test-results.md` — 实际测试数据
- `iteration/v{major}.{minor}/03-planning/v{major}.{minor}-task-plan-dag.md` — TASK 列表
- `iteration/v{major}.{minor}/03-planning/v{major}.{minor}-validation-plan.md` — AC 覆盖
- 实际 git diff 与 CI 输出(如适用)

## Required Output

Create or update `iteration/v{major}.{minor}/05-review-release/v{major}.{minor}-release-log.md` with the following 8 sections:

1. **范围概览** — 业务 / 工作流 / 模块 / 数据库 / 兼容性五维度表。
2. **功能交付清单** — 新增功能 / 体验优化 / 业务规则 / 验收标准四个子表(以 FR/BR/AC 为主键,引用 TASK)。
3. **ISSUE 收尾** — ISSUE-ID 表 + 是否新增遗留。
4. **关键工程变更** — 模块维度的变更 + 影响列。
5. **质量门禁终态** — 检查 / 命令 / 结果三列表;末尾含 `preflight` 工作流一致性检查。
6. **下一版交接项** — 优先级 + 来源表。
7. **已知限制与假设** — 限制 / 假设分类,含 §7.1 版本关系与归档路径子段(按 AGENTS.md §17 描述归档时机)。
8. **封档清单** — checkbox 列表,逐件核对 01-05 各阶段产物 Approved 状态,末尾一行标注本文件"仅需存在,无需 Approved"。

frontmatter:

```yaml
---
document_type: release-log
version: <v{major}.{minor}.0>
status: draft                  # 本产物不参与 Approved gate;draft/In Review 均可,只要文件存在
owner: Tech Lead
last_updated: <ISO 8601>
base_version: <上一已批准迭代>
change_set:
  deprecated: [FR-XXX, ...]    # 仅 deprecated 子键被 diff_versions.py 读取;added/modified 见 requirement.md
baseline_ref:
  - baseline/03-tech-stack-decision.md
---
```

模板:`templates/release-log.md`。

## Approval Contract

**Release log is not gated by `status: Approved`.** The `validate --stage 05-review-release` step requires the file to exist; the frontmatter `status` value (`draft` / `In Review` / `Approved`) does not block the gate. This is implemented as a carve-out in `validation_report()` matching paths ending with `{iteration}-release-log.md`. See `.workflow/tests/test_workflow.py` for the existence-only contract tests.

Implication for the agent:

- 起草完成后保持 `status: draft`(或 `In Review`)即可,不要要求人工把 status 改为 `Approved`。
- §8 封档清单中的"本文件"一行使用 `[x]` 而非 `[ ]`,因为文件存在即视为已交付。
- 不再需要单独的人类审核回合;封档说明的技术准确性与 source-code/test-results 的证据一致性由 `validate --stage 05-review-release` 的其他检查 + review-release.md 的 Approved 状态保证。

## Review Checks

Before handoff, verify that:

- 每一行 §2 子表中的 FR/BR/AC 编号在 `requirement.md` 与 `validation-plan.md` 中存在;引用 TASK 编号在 `task-plan-dag.md` 中存在。
- §3 ISSUE 表中的每个 ISSUE-ID 在 `source-code.md` 的 ISSUE 列表中存在,或显式标注"实施期识别"。
- §5 质量门禁的命令与结果是实际执行的输出(每行末尾注明来源或运行时间),不要复述 review-release.md 中的二手数据。
- §6 交接项的来源列(实施期识别 / preflight 提示 / 业务方反馈)是可追溯的;不要塞入本轮已经完成的工作。
- §7 已知限制/假设覆盖了实施期识别的所有遗留事项,与 `source-code.md` §5 已知限制一致。
- §7.1 版本关系段描述的归档路径与 `manage-iteration` skill 中的描述一致。
- §8 封档清单中的每项 checkbox 与各阶段产物 frontmatter `status` 字段一致;本文件行使用 `[x]`。

## Workflow Hooks

After drafting, use `workflow-governance` to run `index` so the new artifact appears in `workspace/workflow/manifest.yaml`. Run `validate --stage 05-review-release` once the file exists to confirm the existence-only gate passes; this gate does **not** require `status: Approved` on this artifact. The next iteration's creation then archives this release log into `iteration/archive/v{major}.{minor}/05-review-release/v{major}.{minor}-release-log.md` per `manage-iteration`.
