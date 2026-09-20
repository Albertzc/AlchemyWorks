# Instance Workflow Isolation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让实例项目可以使用工作流仓库同步的核心文件，但实例 Git 只提交实例内容、实例说明、Git 配置和可选的工作流版本锁定信息。

**Architecture:** 保留工作流仓库作为上游法规与工具源；同步脚本继续把可运行的工作流文件复制到实例目录，但在实例端将这些同步副本加入忽略规则。实例状态继续写入并提交 `workspace/workflow/`。新增实例初始化辅助能力只生成目录与忽略规则，不创建业务版本产物、不覆盖已有实例文件。

**Tech Stack:** Python 3 标准库、PowerShell 兼容包装器、`unittest`、Git ignore 规则。

**Spec:** `AGENTS.md` §4、§7、§14，以及 `README.md` §7.1。

## Global Constraints

- 工作流核心文件仍由工作流仓库维护，实例项目不得反向修改其源定义。
- `workspace/workflow/manifest.yaml`、`traceability.json`、`current-state.json` 必须保持可提交。
- 不覆盖实例项目已有的 `.gitignore`、`README.md` 或业务目录。
- 不执行真实实例项目初始化；本次只进行临时目录 dry-run 和回归测试。
- 不把 `status: Approved` 写入任何工作流产物。

## Review Focus

- 已存在实例文件：同步或初始化不能覆盖已有实例内容；由同步脚本的目标变更检查测试覆盖。
- 工作流文件可运行但不被提交：由 dry-run Git 状态测试覆盖。
- 实例状态仍可提交：由 ignore 规则测试覆盖 `workspace/workflow/`。
- 实例自有 README 与 Git 配置：同步不能覆盖 README，`.gitignore` 只能追加明确的工作流忽略规则。
- 版本可复现：由锁定文件内容和同步报告测试覆盖。

---

### Task 1: 锁定现状并添加隔离行为测试

**Files:**
- Modify: `.workflow/tests/test_workflow.py`

**Interfaces:**
- Consumes: existing `sync-workflow.ps1` item list and workflow-root/project-root separation.
- Produces: executable expectations for sync exclusion, ignore rules, and instance-owned files.

- [ ] **Step 1: Add failing tests**

  Add tests that assert the sync item list does not overwrite the instance `README.md` or `.gitignore`, and that the generated instance ignore policy ignores workflow source/runtime directories while not ignoring `workspace/workflow/`.

- [ ] **Step 2: Run the focused tests and verify the expected failure**

  Run: `python -m unittest .workflow.tests.test_workflow.WorkflowTests`

  Expected: FAIL because the current sync script still synchronizes root `README.md` and `.gitignore`, and no instance ignore-policy helper exists.

### Task 2: Implement non-destructive instance synchronization

**Files:**
- Modify: `.workflow/scripts/sync-workflow.ps1`
- Modify: `.workflow/workflow.py`
- Modify: `.workflow/workflow-file-inventory.md`
- Modify: `.workflow/README.md`
- Modify: `README.md`
- Modify: `AGENTS.md`

**Interfaces:**
- Consumes: `-TargetRoot`, `-AllowDirtyTarget`, and `--project-root` behavior.
- Produces: a synchronization flow that preserves instance `README.md` and `.gitignore`, creates a dedicated workflow ignore section when needed, and reports the selected framework version source.

- [ ] **Step 1: Implement the smallest synchronization change**

  Remove root `README.md` and `.gitignore` from the copied workflow item list. Keep the workflow source `AGENTS.md` available under the instance’s ignored framework/runtime area instead of treating the instance README as workflow-owned. Add an idempotent helper that adds only a marked workflow-ignore block to the instance `.gitignore`, preserving all other lines.

- [ ] **Step 2: Run focused tests and verify they pass**

  Run: `python -m unittest .workflow.tests.test_workflow.WorkflowTests`

  Expected: PASS for the new isolation tests and all existing workflow tests.

- [ ] **Step 3: Update documentation and inventory**

  Document the two-repository model, the non-destructive sync boundary, the committed instance state, and the optional workflow lock file. Keep the inventory aligned with the synchronization script.

### Task 3: Add dry-run coverage for a temporary instance

**Files:**
- Modify: `.workflow/tests/test_workflow.py`

**Interfaces:**
- Consumes: the updated synchronization script and instance ignore policy.
- Produces: a temporary-directory test that verifies copied workflow files are present, instance-owned files are preserved, and Git reports only instance-owned files as candidates for commit.

- [ ] **Step 1: Run the temporary-instance dry-run test**

  Run: `python -m unittest .workflow.tests.test_workflow.WorkflowTests.test_sync_preserves_instance_files_and_ignores_workflow_files`

  Expected: PASS with no writes outside a temporary directory.

- [ ] **Step 2: Run the complete workflow test suite**

  Run: `python .workflow/tests/test_workflow.py`

  Expected: exit code 0 with all tests passing.

- [ ] **Step 3: Run final read-only checks**

  Run: `git diff --check`; `python .workflow/workflow.py verify-workflow`; `git status --short`.

  Expected: no whitespace errors, workflow verification passes, and only the planned files are changed.

### Task 4: Initialize named instances and lock the workflow source

**Files:**
- Create: `.workflow/scripts/init-instance.ps1`
- Modify: `.workflow/scripts/sync-workflow.ps1`
- Modify: `.workflow/workflow-file-inventory.md`
- Modify: `.workflow/README.md`
- Modify: `README.md`
- Modify: `.workflow/tests/test_workflow.py`

**Interfaces:**
- Consumes: an instance name, a new or empty target directory, and the current workflow repository Git commit.
- Produces: a new instance Git repository with `README.md`, `baseline/`, `iteration/`, `workspace/`, `.aw/workflow.lock`, and synchronized workflow files.

- [x] **Step 1: Add failing tests**
- [x] **Step 2: Implement the initializer and lock file**
- [x] **Step 3: Run focused and complete tests**
- [x] **Step 4: Run initialization `-WhatIf` and verify the target is unchanged**
