# Remove Workspace README from Workflow Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `workspace/README.md` instance-owned by removing it from workflow initialization, synchronization, and the authoritative workflow skeleton inventory while preserving the archive freshness check.

**Architecture:** Keep `workspace/README.md` as a project-owned input validated by the release/archive workflow. Remove only skeleton ownership and automatic copying; do not remove the existing freshness contract.

**Tech Stack:** PowerShell synchronization script, Python stdlib workflow CLI, Markdown documentation, Python `unittest`.

**Spec:** User request: remove `workspace/README.md` from the workflow skeleton file list; each instance project manages it from its actual current functionality.

## Global Constraints

- Do not modify product implementation files or instance-owned workspace content.
- Keep `workspace/README.md` freshness validation before archiving.
- Keep the workflow inventory aligned with the synchronization script.
- Do not set any artifact status to `Approved`.

---

### Task 1: Remove workflow ownership of the workspace README

**Files:**
- Modify: `.workflow/scripts/sync-workflow.ps1`
- Modify: `.workflow/workflow.py`
- Modify: `.workflow/workflow-file-inventory.md`
- Modify: `.workflow/tests/test_workflow.py`
- Modify: `.workflow/README.md`
- Modify: `README.md`
- Modify: `.agents/skills/manage-iteration/SKILL.md`

**Interfaces:**
- Preserve `check_workspace_readme_freshness(iteration, errors)` and all archive checks.
- `init_project()` must create the intake directories but must not create `workspace/README.md`.
- Synchronization must not copy `workspace/README.md`.

- [x] Remove `workspace/README.md` from the sync item list and workflow inventory.
- [x] Stop `init_project()` from generating the instance README.
- [x] Update tests and documentation to describe the file as instance-owned.
- [x] Run the workflow regression suite and core verification.
- [x] Inspect the diff for unrelated changes.
