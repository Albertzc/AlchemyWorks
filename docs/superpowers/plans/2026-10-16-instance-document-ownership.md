# Instance Document Ownership Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make instance `AGENTS.md` project-owned at the root, synchronize only `.aw/README.md`, and keep the instance root `README.md` as the current system-functionality document.

**Architecture:** The framework source continues to own the workflow rules and workflow README. `init-instance` copies the rules once into the instance root, while `sync` updates only the hidden workflow copy of the README and execution files. The release gate refreshes a marked current-functionality section in the tracked root README; `workspace/README.md` remains static workspace guidance.

**Tech Stack:** Python standard library, unittest, Markdown documentation, Git ignore rules.

**Spec:** User-approved instance document ownership decision in the conversation on 2026-10-16.

## Global Constraints

- Do not create or synchronize `.aw/AGENTS.md` in new instances.
- Do not overwrite instance root `AGENTS.md` or `README.md` during `sync`.
- Keep `.aw/README.md` synchronized from the framework source.
- Keep system functionality out of `workspace/README.md`.
- Update the workflow file inventory, documentation, and regression tests with behavior changes.

## Review Focus

- Existing instance edits to root `AGENTS.md` and `README.md` must survive `sync`.
- Root `README.md` must be tracked rather than ignored.
- 05-review-release and successor-archive checks must validate the root README.
- `workspace/README.md` must remain a static scaffold and must not receive release-log content.
- Fresh initialization must produce exactly one instance AGENTS file and both required README roles.

### Task 1: Update synchronization and initialization ownership

**Files:** `.workflow/workflow.py`, `.workflow/tests/test_workflow.py`

- [x] Add failing tests for no `.aw/AGENTS.md`, preserved root files, synchronized `.aw/README.md`, and tracked root README.
- [x] Remove the `.aw/AGENTS.md` sync mapping and root README sync mapping.
- [x] Keep root `AGENTS.md` initialization copy and create an instance README scaffold.
- [x] Update managed ignore rules and dirty-path handling.
- [x] Run focused initialization/sync tests.

### Task 2: Move release functionality refresh to root README

**Files:** `.workflow/workflow.py`, `.workflow/tests/test_workflow.py`

- [x] Add failing tests for root README refresh and untouched workspace README.
- [x] Refresh a marked functionality section in root README after 05-review-release.
- [x] Point freshness and archive checks at root README.
- [x] Keep `workspace/README.md` static.
- [x] Run focused release-refresh tests.

### Task 3: Update governance documentation and inventory

**Files:** `AGENTS.md`, `README.md`, `.workflow/README.md`, `.workflow/workflow-file-inventory.md`, `.agents/skills/*` references as needed

- [x] Document the final ownership model and migration behavior.
- [x] Remove contradictory statements about root README ownership and workspace functionality.
- [x] Update the authoritative inventory and command examples.

### Task 4: Verify the workflow maintenance change

- [x] Run the complete workflow regression suite.
- [x] Run `verify-workflow` and inspect the final diff.
- [x] Run a temporary instance initialization/sync/release-flow smoke test.

