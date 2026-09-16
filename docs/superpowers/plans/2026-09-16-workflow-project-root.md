# Workflow Project Root Separation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the workflow CLI read and write project artifacts and `.workflow` runtime state under an explicit instance-project root, so the framework source directory does not receive instance state when the framework operates on another project.

**Architecture:** Keep the framework source directory as the code root used for protection checks and bundled templates. Add a project-root execution context selected by a global `--project-root` option; all artifact/state paths use that context, while framework synchronization continues to copy definitions but not generated state. Preserve the existing copied-in-instance behavior by defaulting the project root to the directory containing `.workflow/workflow.py` when no override is provided.

**Tech Stack:** Python 3 standard library, PowerShell sync script, `unittest`.

**Spec:** User-approved workflow framework / instance-project separation decision in the conversation; current project workflow governance and `AGENTS.md`.

## Global Constraints

- Do not add third-party dependencies.
- Generated instance state belongs to the selected project root, not the framework source root.
- Framework core protection checks continue to inspect the framework source tree.
- Do not change approval semantics or automatically approve artifacts.
- Preserve existing CLI behavior when `--project-root` is omitted from a copied instance project.

---

### Task 1: Add project-root regression tests

**Files:**
- Modify: `.workflow/tests/test_workflow.py`
- Test: `.workflow/tests/test_workflow.py`

**Interfaces:**
- Consumes: `workflow.main()` and the test fixture's temporary project root.
- Produces: Failing tests proving an explicit project root receives generated state while the framework root does not.

- [x] **Step 1: Write the failing test**

Add a test that creates separate temporary framework and instance roots, invokes `workflow.main(["--project-root", str(instance), "index", "--iteration", "v1"])`, and asserts the three state files exist only under `instance/.workflow/`.

- [x] **Step 2: Run the focused test**

Run: `python -m unittest .workflow.tests.test_workflow.WorkflowTests.test_index_uses_explicit_project_root`

Expected: FAIL because the CLI does not yet accept `--project-root`.

### Task 2: Implement project-root execution context

**Files:**
- Modify: `.workflow/workflow.py`
- Test: `.workflow/tests/test_workflow.py`

**Interfaces:**
- Consumes: the global `--project-root` option and the existing path globals.
- Produces: `configure_project_root(path)`, project-root-aware `ROOT` / `WORKFLOW_DIR`, and framework-root-aware protection checks.

- [x] **Step 1: Add the minimal execution-context implementation**

Introduce a separate framework root constant, configure the project root after argument parsing, and add `--project-root` as a global CLI option. Keep no-argument execution compatible with a workflow copied into an instance project.

- [x] **Step 2: Run the focused test**

Run: `python -m unittest .workflow.tests.test_workflow.WorkflowTests.test_index_uses_explicit_project_root`

Expected: PASS, with generated state under the instance root only.

- [x] **Step 3: Add path-isolation coverage for state and task operations**

Cover `state`, `context`, and `task-finished` through the configured project root so no generated state is written under the framework root.

- [x] **Step 4: Run the complete workflow tests**

Run: `python .workflow/tests/test_workflow.py`

Expected: all tests pass.

### Task 3: Align synchronization and documentation

**Files:**
- Modify: `.workflow/scripts/sync-workflow.ps1`
- Modify: `.workflow/README.md`
- Modify: `README.md`
- Modify: `.workflow/workflow-file-inventory.md`

**Interfaces:**
- Consumes: the new `--project-root` CLI contract.
- Produces: documented framework-to-instance execution flow and synchronization behavior.

- [x] **Step 1: Document explicit project-root invocation**

Document running the framework CLI from the framework source against an instance project with `--project-root`, and explain that the state files are generated in the target instance.

- [x] **Step 2: Update synchronization comments and examples**

Keep generated state excluded from synchronization and show the explicit target-root relationship.

- [x] **Step 3: Run documentation consistency checks**

Run: `git diff --check` and search for stale claims that the framework root owns instance state.

### Task 4: Verify the maintenance change

**Files:**
- Modify: none beyond the files above.

**Interfaces:**
- Consumes: all implemented path separation behavior.
- Produces: test and workflow verification evidence.

- [x] **Step 1: Run the full workflow test suite**

Run: `python .workflow/tests/test_workflow.py`

- [x] **Step 2: Run workflow core verification**

Run: `python .workflow/workflow.py verify-workflow`

Expected before commit: blocked only because this dedicated workflow-maintenance change is uncommitted; after commit it should pass.

- [x] **Step 3: Inspect the final diff and status**

Run: `git status --short` and `git diff --stat`; confirm no generated state or unrelated product files were changed.
