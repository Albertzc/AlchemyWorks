# Workflow Test Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restore the workflow maintenance test suite to green without changing the governed stage sequence or approval rules.

**Architecture:** Keep production workflow behavior unchanged except for the root-only managed README ignore rule. Repair legacy v1.0 fixtures and release-stage diff fixtures to match the documented contracts, and keep all scratch work inside the project-local test directory.

**Tech Stack:** Python 3.14, unittest, Git, PowerShell-compatible project-local scratch directories.

**Spec:** User-approved five-item repair list from the preceding workflow diagnosis.

## Global Constraints

- Preserve the baseline → iteration → stage-gate → Context Pack → task-finished workflow.
- Do not change artifact approval semantics.
- Workflow-core changes must update `.workflow/workflow-file-inventory.md` in the same change.
- Do not modify the user-provided `AGENTS.md`.

## Review Focus

- Root-only README ignore must not hide scaffold READMEs.
- v1.0 must retain its standalone issue-fixes artifact requirement.
- v1.1+ must not regain the legacy issue-fixes requirement.
- Deprecation metadata must be read from review/release artifacts.
- Workflow-ref initialization tests must not depend on restricted system temp ACLs.

### Task 1: Root-only README ignore

**Files:**
- Modify: `.workflow/workflow.py`
- Test: `.workflow/tests/test_workflow.py`
- Modify: `.workflow/workflow-file-inventory.md`

- [ ] Add a regression assertion that nested scaffold READMEs remain visible to Git.
- [ ] Verify the assertion fails with the current unanchored pattern.
- [ ] Change the managed rule to `/README.md`.
- [ ] Run the focused sync/ignore tests.

### Task 2: Repair v1.0 fixtures

**Files:**
- Modify: `.workflow/tests/test_workflow.py`

- [ ] Add the required v1.0 `issue-fixes.md` to the shared full-chain fixture.
- [ ] Run the four affected gate/archive tests.
- [ ] Confirm v1.1+ still omits the legacy file.

### Task 3: Align cross-version diff fixtures

**Files:**
- Modify: `.workflow/tests/test_workflow.py`

- [ ] Move deprecation metadata in both diff fixtures to the v1.1 review/release artifact.
- [ ] Run both diff tests and verify exit code 2 with `FR-003`.

### Task 4: Stabilize workflow-ref test scratch space

**Files:**
- Modify: `.workflow/tests/test_workflow.py`

- [ ] Replace remaining system `TemporaryDirectory` use in workflow-ref tests with `_ScratchDir`.
- [ ] Run initialization/sync tests under the project-local scratch directory.

### Task 5: Full verification

**Files:**
- No additional production files.

- [ ] Run the complete workflow regression suite.
- [ ] Run `verify-workflow` and `git diff --check`.
- [ ] Review the diff for unrelated changes.

