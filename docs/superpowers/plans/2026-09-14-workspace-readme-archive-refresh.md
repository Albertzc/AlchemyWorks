# Workspace README Archive Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make version archiving require a refreshed `workspace/README.md` that incorporates the completed version’s system functionality before the predecessor is archived.

**Architecture:** Keep business-function writing human-authored, because the workflow cannot reliably infer a useful product manual from arbitrary artifacts. Add a deterministic freshness check to the workflow CLI, keyed by an explicit version marker in `workspace/README.md`; run it at the 05-review-release gate and again immediately before archive mutation. Document the handoff in the iteration-management and release skills.

**Tech Stack:** Python standard library, Markdown, unittest.

**Spec:** User request: when a version is completed and the predecessor is archived, refresh `workspace/README.md` by merging the new version’s functionality into the current system-function documentation.

## Global Constraints

- Do not auto-approve artifacts or invent business functionality.
- Preserve the existing archive ordering: create successor skeleton first, then archive predecessor.
- Update `workflow-file-inventory.md` whenever workflow-owned files or behavior change.
- Keep `workspace/README.md` project-owned and human-editable; the CLI only validates its refresh contract.

---

### Task 1: Add the workspace README refresh contract and archive guard

**Files:**
- Modify: `.workflow/workflow.py`
- Test: `.workflow/tests/test_workflow.py`

**Interfaces:**
- Add `check_workspace_readme_freshness(iteration: str, errors: list[str]) -> None`.
- The check requires `workspace/README.md`, the exact marker `<!-- workflow:workspace-readme-version: {iteration} -->`, and the heading `## 当前系统功能说明`.
- Call the check during `05-review-release` validation and before `archive_iteration` mutates the predecessor.

- [ ] Add failing tests for a missing marker/heading and for successful validation during archive.
- [ ] Run the focused tests and confirm they fail before implementation.
- [ ] Implement the check and call sites without changing the existing root README freshness rule.
- [ ] Run the focused tests and the full workflow test suite.

### Task 2: Update workflow documentation and skills

**Files:**
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `.workflow/README.md`
- Modify: `.agents/skills/manage-iteration/SKILL.md`
- Modify: `.agents/skills/review-release/SKILL.md`
- Modify: `.workflow/workflow-file-inventory.md`

**Interfaces:**
- Document the marker and required heading as the handoff contract.
- State that the completed version’s functionality must be merged into the current system description before archive.
- State that archive stops without changing either version when the workspace README check fails.

- [ ] Update the archive flow, command behavior, and human-review responsibilities in all affected documents.
- [ ] Keep the docs consistent with the CLI’s actual validation behavior.
- [ ] Run link/text consistency checks and inspect the diff.

### Task 3: Verify the workflow-maintenance change

**Files:**
- Modify: none beyond Tasks 1–2.

- [ ] Run `python .workflow/tests/test_workflow.py`.
- [ ] Run `python .workflow/workflow.py verify-workflow` and record the expected dirty-core result while this maintenance change is uncommitted.
- [ ] Run `git diff --check` and review the complete diff for unrelated changes.
- [ ] Report the required dedicated workflow-maintenance commit boundary before normal product commands resume.
