# Instance State Directory Separation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Store the three Git-managed instance workflow state files under `workspace/workflow/` while keeping `.workflow/` for framework source files and ignored runtime data.

**Architecture:** Keep `ROOT` as the selected instance project root, `FRAMEWORK_ROOT` as the framework source root, and split paths into `PROJECT_STATE_DIR = ROOT / workspace/workflow` for `manifest.yaml`, `traceability.json`, and `current-state.json`, plus `WORKFLOW_DIR = ROOT / .workflow` for caches, Context Packs, task-runs, dashboard output, and synchronized framework files. Framework-owned README, Skills, scripts, and dashboard template are read from `FRAMEWORK_ROOT`.

**Tech Stack:** Python 3 standard library, PowerShell synchronization script, `unittest`.

**Spec:** User-approved directory decision: `workspace/workflow/manifest.yaml`, `workspace/workflow/traceability.json`, and `workspace/workflow/current-state.json` are instance-project state; `.workflow/` is ignored framework/runtime content.

## Global Constraints

- Do not add third-party dependencies.
- Do not change stage approval semantics.
- Existing product artifacts remain under `baseline/`, `iteration/`, and `workspace/`.
- `task-runs/` remains ignored by default.
- The CLI must work both from a synchronized instance and from an external framework root using `--project-root`.

---

### Task 1: Add failing state-directory tests

**Files:**
- Modify: `.workflow/tests/test_workflow.py`

- [x] **Step 1: Write the failing assertions**

Update the state-output assertions to expect `workspace/workflow/` and add coverage that the old `.workflow/manifest.yaml`, `.workflow/traceability.json`, and `.workflow/current-state.json` paths are not written.

- [x] **Step 2: Run focused tests**

Run: `python .workflow/tests/test_workflow.py`

Expected: FAIL because the implementation still writes state to `.workflow/`.

### Task 2: Split project state and framework/runtime paths

**Files:**
- Modify: `.workflow/workflow.py`
- Test: `.workflow/tests/test_workflow.py`

- [x] **Step 1: Add `project_state_dir()`**

Resolve the instance state directory as `ROOT / "workspace" / "workflow"` and use it for manifest discovery and the three tracked state files.

- [x] **Step 2: Keep runtime outputs under `.workflow/`**

Leave cache, Context Packs, task-runs, and dashboard output under `WORKFLOW_DIR`, creating the directory when needed.

- [x] **Step 3: Read framework-owned resources from `FRAMEWORK_ROOT`**

Use the framework root for framework README freshness, Skills/scripts discovery, and dashboard template lookup.

- [x] **Step 4: Run focused tests**

Run: `python .workflow/tests/test_workflow.py`

Expected: PASS.

### Task 3: Migrate ignore rules, synchronization documentation, and output paths

**Files:**
- Modify: `.gitignore`
- Modify: `.workflow/scripts/sync-workflow.ps1`
- Modify: `.workflow/workflow-file-inventory.md`
- Modify: `.workflow/README.md`
- Modify: `README.md`

- [x] **Step 1: Ignore `.workflow/` for synchronized instances**

Add `.workflow/` to the ignore rules while leaving `workspace/workflow/` trackable.

- [x] **Step 2: Document the final directory layout**

Document that `.workflow/` contains framework/runtime content and `workspace/workflow/` contains the three instance state files.

- [x] **Step 3: Update sync guidance**

Document that synchronization does not copy or overwrite `workspace/workflow/` state.

### Task 4: Verify the framework maintenance change

**Files:**
- Modify: none beyond the files above.

- [x] **Step 1: Run tests and diff checks**

Run: `python .workflow/tests/test_workflow.py` and `git diff --check`.

- [x] **Step 2: Verify generated paths**

Run a temporary-project index/context/task flow and confirm the three state files are under `workspace/workflow/` and no corresponding files are created under `.workflow/`.

- [x] **Step 3: Inspect status and framework protection**

Run: `git status --short` and `python .workflow/workflow.py verify-workflow`.

The protection check is expected to remain blocked until this dedicated workflow-maintenance change is committed.
