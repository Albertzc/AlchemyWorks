# Workflow Control Layer

> 所有权：源仓库中的 `.workflow/` 是工作流执行层；同步到实例后，工作流执行文件位于 `.aw/`，Skills 位于 `.aw/.agents/`，实例可维护模板位于根目录 `templates/`。实例项目状态写入 `workspace/workflow/`。

This directory contains the standard-library CLI and workflow source definitions. When the CLI is run with `--project-root`, generated state is written to the selected instance project instead of this framework source directory.

`init-instance` creates a new instance Git tree, writes the instance-owned `README.md` with a visible `.aw/` workflow entry point, copies the complete workflow rules identically to root `AGENTS.md` and `.aw/AGENTS.md`, and writes ignored `.aw/workflow-version.yaml`. It creates `baseline/`, `iteration/`, `workspace/`, and root `templates/`, then calls `sync`. `sync` copies workflow definitions and Skills into `.aw/`, copies missing default template files into root `templates/`, and never overwrites instance templates, baseline/iteration/workspace content, instance README, root `AGENTS.md`, or instance `.gitignore`. `sync` maintains a marked ignore block containing only `.aw/` while `workspace/workflow/` remains committable.

Workflow-owned source files and required scaffold directories are authoritatively listed in [`workflow-file-inventory.md`](workflow-file-inventory.md). Keep that inventory synchronized with every workflow change.

## Commands

Run from the project root:

```powershell
python .workflow/workflow.py init
python .workflow/workflow.py init-version
python .workflow/workflow.py index --iteration v1
python .workflow/workflow.py --project-root 'E:\path\to\instance-project' index
python .workflow/workflow.py refresh --iteration v1 --stage 01-product
python .workflow/workflow.py route-requirement
python .workflow/workflow.py validate --iteration v1 --stage 00-baseline
python .workflow/workflow.py validate --iteration v1 --stage 01-product
python .workflow/workflow.py validate --iteration v1
python .workflow/workflow.py context --iteration v1 --task TASK-API-010
python .workflow/workflow.py context --iteration v1 --task TASK-API-010 --compact --max-chars 12000
python .workflow/workflow.py cleanup --iteration v1.0
python .workflow/workflow.py cleanup --iteration v1.0 --execute
python .workflow/workflow.py state --iteration v1 --refresh
python .workflow/workflow.py resume --json
python .workflow/workflow.py preflight --iteration v1 --json
python .workflow/workflow.py review-pack --iteration v1 --stage 03-planning --json
python .workflow/workflow.py dashboard --iteration v1
python .workflow/workflow.py task-finished --iteration v1 --task TASK-API-010 --result succeeded
python .workflow/workflow.py verify-workflow
.\.workflow\scripts\sync-workflow.ps1 -TargetRoot 'E:\path\to\target-project'
```

`init` creates only the non-versioned intake directories, including `iteration/raw-requirement/README.md`. `init-version` creates the next version skeleton only after the baseline gate passes, and refreshes `workspace/workflow/manifest.yaml`. `route-requirement` determines where newly received, unstructured user requirements are archived. With an empty baseline it returns the baseline intake directory; otherwise it uses the `iteration` in the instance state's `workspace/workflow/manifest.yaml` when available, falling back to version discovery, and returns that target version with the centralized `iteration/raw-requirement/` directory. Except for its README, this directory contains user-owned source material only: Agents must not modify, rename, or delete its files. `validate` is the `stage-gate` controller: a nonzero exit code means the requested formal stage cannot proceed. Raw requirements are source material, not approved stage artifacts. `index` writes the artifact manifest, stable-ID traceability graph, and derived recovery checkpoint. `state` compares the cached checkpoint's input fingerprint with current artifact and TASK metadata, rebuilding the manifest, traceability graph, and checkpoint when it is stale; `state --refresh` forces that same rebuild. `refresh` is the standard post-document-edit sequence: it runs `index`, then `state --refresh`, then `validate`; a nonzero result stops the sequence. `context` creates a task-scoped pack under `context-packs/` and reuses it when its input fingerprint is unchanged. `resume --json` is the preferred low-context startup command; it emits only the active iteration, current stage, blockers, next action, recommended reads and gate command. It returns `NO_ACTIVE_ITERATION` when no active version exists. `context --compact` deduplicates excerpts and enforces local character/section limits. `preflight` runs gate, DAG and coverage checks locally. `review-pack` emits human-review evidence without approving artifacts. `task-finished --auto-refresh` refreshes local indexes when a task changed artifact files.

When the CLI is run from the framework source repository, pass `--project-root` before the subcommand. The selected instance project is then the only root used for product documents and generated `workspace/workflow` state plus `.aw/.workflow` runtime data; the framework source tree is used only for framework code and Skills, while instance templates are read from root `templates/`. When the workflow CLI has been synchronized into an instance project, omitting `--project-root` uses the local `.aw/` layout.

`workspace/README.md` is an instance-owned workspace guide. It describes the workspace directory responsibilities, code organization, and runtime conventions; it is not replaced by release validation. A successful `validate --stage 05-review-release` replaces the instance root `README.md` with the current iteration's approved requirement body, prefixed by the iteration marker and `## 当前系统功能说明`. For a later version, `init-version` first validates the active predecessor through `05-review-release`, which regenerates and checks the root README, creates the successor skeleton, and only then moves that predecessor to `iteration/archive/`. A failed predecessor gate or README generation/check removes the empty successor skeleton and leaves the predecessor and archive unchanged.

Generated files:

- `.aw/workflow-version.yaml` — current synchronized workflow ref and commit; ignored by the instance project and refreshed by `init-instance` / `sync`.
- `workspace/workflow/manifest.yaml` — discovered artifacts, status, line count, and content hash. This is instance-project state and is committed to Git.
- `workspace/workflow/traceability.json` — stable IDs and evidence-backed co-occurrence edges. This is instance-project state and is committed to Git.
- `workspace/workflow/current-state.json` — derived recovery checkpoint: current stage, blockers, next action, latest gate, and reusable Context Pack. This is instance-project state and is committed to Git.
- `.aw/.workflow/cache/`, `.aw/.workflow/context-packs/`, `.aw/.workflow/task-runs/`, and `.aw/.workflow/dashboard/index.html` — local runtime and audit data, ignored in instance projects and created on demand.
- `.aw/.workflow/cache/context-packs.json` — Context Pack cache keys.
- `.aw/.workflow/context-packs/` — compact task-specific context for implementation agents.
- `.aw/.workflow/task-runs/` — task completion conclusions and gate/context metadata. This is local instance-project audit evidence and is ignored by default; commit selected records manually when needed.
- `.aw/.workflow/task-runs/history/` — immutable task completion history. This is local instance-project audit evidence and is ignored by default; commit selected records manually when needed.
- `.aw/.workflow/dashboard/index.html` — static project execution view.

## Generated-state retention

Context Packs and `cache/context-packs.json` are rebuildable implementation caches. Once a version has been moved to `iteration/archive/`, run `cleanup --iteration v{major}.{minor}` to preview its removable packs; add `--execute` to remove them and their cache keys. The command refuses active versions and never removes `task-runs/` or `task-runs/history/`, which are retained as audit evidence.

## Prototype gates

The `00-baseline` gate requires the four baseline documents plus `baseline/05-core-user-flow-prototype.html`, approved by a human. The baseline prototype may be low fidelity, but must make the core roles, key task closure, principal states, and permission differences reviewable.

Each iteration's product requirement must include the flat frontmatter decision `prototype_required: true|false`. A `true` decision makes `iteration/v{major}.{minor}/01-product/v{major}.{minor}-prototype.html` a required Approved input to the 01-product gate. A `false` decision permits that artifact to be omitted, but requires nonempty `prototype_baseline` and `prototype_rationale` frontmatter for human review.

Every HTML prototype, including the baseline prototype, must preserve the HTML-comment frontmatter from `templates/Prototype.html`: `status`, `reviewer`, `reviewed_at`, and `review_notes`. A generated prototype starts as `status: draft`; an Approved prototype must have a nonempty reviewer, timestamp, and review conclusion. `validate` treats missing or incomplete prototype review metadata as a blocking error.

All generated timestamps use the local timezone of the Codex client that runs the command and include an ISO 8601 offset (for example, `+08:00`). They do not use Codex server time or a misleading UTC `Z` suffix.

The gate validates the complete upstream chain through the requested stage, including the required implementation and combined review-release artifact.

## Workflow core protection

During product development, the workflow core is read-only. `AGENTS.md`, the root workflow documentation, `.workflow/workflow.py`, workflow scripts/tests, `.agents/skills/`, and source `templates/` are protected definitions; `baseline/`, `iteration/`, `workspace/`, and instance root `templates/` remain project-owned inputs and outputs. `index`, `validate`, `init-version`, `refresh`, `context`, `task-finished`, and other operational commands stop when a protected file has uncommitted changes. Run `python .workflow/workflow.py verify-workflow` to inspect the guard. Workflow maintainers may edit the protected files in a dedicated maintenance change, run the workflow tests, and commit the change before resuming product workflow commands.

## Synchronizing this workflow to another project

The Python CLI is the single implementation for instance initialization and synchronization:

```text
python .workflow/workflow.py init-instance --name "Product A" --directory "E:\path\to\product-a"
python .workflow/workflow.py sync --directory "E:\path\to\target-project"
```

Use `--dry-run` to preview either operation and `--allow-dirty` only after reviewing intentional target overlap. The `.ps1` files below remain Windows compatibility wrappers only.

The Python CLI is the single implementation for instance initialization and synchronization. The instance name is optional; when omitted, the final directory name is used:

```text
python .workflow/workflow.py init-instance --name "Product A" --directory "E:\path\to\product-a"
python .workflow/workflow.py init-instance --directory "E:\path\to\product-a"
```

Use `--dry-run` to preview the initialization. The command creates the instance Git repository, instance `README.md`, `AGENTS.md`, root `templates/`, `baseline/`, `iteration/`, `workspace/`, and ignored `.aw/workflow-version.yaml`, then synchronizes the workflow definition. Pass `--workflow-version '<tag|branch|commit>'` to initialize from a specific workflow ref.

Run `.\.workflow\scripts\sync-workflow.ps1 -TargetRoot '<target-project-root>'` from this repository to copy the workflow definition to a target Git working tree. The script copies only the items governed by `workflow-file-inventory.md`: shared rules, CLI, templates, scaffold READMEs, and Skills. It does not copy `baseline/` deliverables, `iteration/` deliverables, `workspace/` business code, or generated workflow state.

The script permits unrelated target changes, but rejects uncommitted changes that overlap a synchronized workflow path. Existing instance templates are preserved; use the Python CLI with `--workflow-version '<tag|branch|commit>'` when changing the source ref. After reviewing an intentional overlap, use `-AllowDirtyTarget`; use PowerShell's `-WhatIf` to preview the copy. The target `.gitignore` receives an idempotent managed block for `.aw/`; `workspace/workflow/` and `templates/` remain visible to Git. Invoke the framework CLI with `--project-root '<target-project-root>'` to write state to the target instance, or run `.aw/.workflow/workflow.py` locally after synchronization.

Every completed TASK must use `context` first, then `task-finished`. The latter validates that the task exists in the current task plan, requires the Context Pack, writes the latest conclusion plus an immutable history record, refreshes the recovery checkpoint, and prints a concise result. `index`, `validate`, `context`, and `task-finished` all refresh the checkpoint. It is a cache only: artifact frontmatter and gate results remain authoritative. Use `--refresh-index` or `--refresh-dashboard` when those generated views must also be refreshed.
