# Workflow Control Layer

This directory contains the standard-library CLI and workflow source definitions. When the CLI is run with `--project-root`, generated state is written to the selected instance project instead of this framework source directory.

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

When the CLI is run from the framework source repository, pass `--project-root` before the subcommand. The selected instance project is then the only root used for product documents and generated `workspace/workflow` state plus `.workflow` runtime data; the framework source tree is used only for framework code, templates, Skills, and protection checks. When the workflow CLI has been synchronized into an instance project, omitting `--project-root` keeps the existing local-root behavior.

`workspace/README.md` is an automatically generated instance artifact. A successful `validate --stage 05-review-release` replaces it with the current iteration's approved requirement body, prefixed by the iteration marker and `## 当前系统功能说明`; it is not manually maintained. The root `README.md` documents the shared workflow framework and is checked only for current Skills and scripts. Archive policy: `v1.0` has no predecessor. For a later version, `init-version` first validates the active predecessor through `05-review-release`, which regenerates the workspace README, checks its marker, creates the successor skeleton, and only then moves that predecessor to `iteration/archive/`. A failed predecessor gate or README generation/check removes the empty successor skeleton and leaves the predecessor and archive unchanged.

Generated files:

- `workspace/workflow/manifest.yaml` — discovered artifacts, status, line count, and content hash. This is instance-project state and is committed to Git.
- `workspace/workflow/traceability.json` — stable IDs and evidence-backed co-occurrence edges. This is instance-project state and is committed to Git.
- `workspace/workflow/current-state.json` — derived recovery checkpoint: current stage, blockers, next action, latest gate, and reusable Context Pack. This is instance-project state and is committed to Git.
- `.workflow/cache/`, `.workflow/context-packs/`, `.workflow/task-runs/`, and `.workflow/dashboard/index.html` — local runtime and audit data, ignored in instance projects.
- `.workflow/cache/context-packs.json` — Context Pack cache keys.
- `.workflow/context-packs/` — compact task-specific context for implementation agents.
- `.workflow/task-runs/` — task completion conclusions and gate/context metadata. This is local instance-project audit evidence and is ignored by default; commit selected records manually when needed.
- `.workflow/task-runs/history/` — immutable task completion history. This is local instance-project audit evidence and is ignored by default; commit selected records manually when needed.
- `.workflow/dashboard/index.html` — static project execution view.

## Generated-state retention

Context Packs and `cache/context-packs.json` are rebuildable implementation caches. Once a version has been moved to `iteration/archive/`, run `cleanup --iteration v{major}.{minor}` to preview its removable packs; add `--execute` to remove them and their cache keys. The command refuses active versions and never removes `task-runs/` or `task-runs/history/`, which are retained as audit evidence.

## Prototype gates

The `00-baseline` gate requires the four baseline documents plus `baseline/05-core-user-flow-prototype.html`, approved by a human. The baseline prototype may be low fidelity, but must make the core roles, key task closure, principal states, and permission differences reviewable.

Each iteration's product requirement must include the flat frontmatter decision `prototype_required: true|false`. A `true` decision makes `iteration/v{major}.{minor}/01-product/v{major}.{minor}-prototype.html` a required Approved input to the 01-product gate. A `false` decision permits that artifact to be omitted, but requires nonempty `prototype_baseline` and `prototype_rationale` frontmatter for human review.

Every HTML prototype, including the baseline prototype, must preserve the HTML-comment frontmatter from `templates/Prototype.html`: `status`, `review_decision`, `reviewer`, `reviewed_at`, and `review_notes`. A generated prototype starts as `status: draft` / `review_decision: pending`; an Approved prototype must have `review_decision: approved` plus a nonempty reviewer, timestamp, and review conclusion. `validate` treats missing or incomplete prototype review metadata as a blocking error.

All generated timestamps use the local timezone of the Codex client that runs the command and include an ISO 8601 offset (for example, `+08:00`). They do not use Codex server time or a misleading UTC `Z` suffix.

The gate validates the complete upstream chain through the requested stage, including the required implementation and combined review-release artifact.

## Workflow core protection

During product development, the workflow core is read-only. `AGENTS.md`, the root workflow documentation, `.workflow/workflow.py`, workflow scripts/tests, `.agents/skills/`, and `templates/` are protected definitions; `baseline/`, `iteration/`, and `workspace/` remain project-owned inputs and outputs. `index`, `validate`, `init-version`, `refresh`, `context`, `task-finished`, and other operational commands stop when a protected file has uncommitted changes. Run `python .workflow/workflow.py verify-workflow` to inspect the guard. Workflow maintainers may edit the protected files in a dedicated maintenance change, run the workflow tests, and commit the change before resuming product workflow commands.

## Synchronizing this workflow to another project

The Python CLI is the single implementation for instance initialization and synchronization:

```text
python .workflow/workflow.py init-instance --name "Product A" --directory "E:\path\to\product-a"
python .workflow/workflow.py sync --directory "E:\path\to\target-project"
```

Use `--dry-run` to preview either operation and `--allow-dirty` only after reviewing intentional target overlap. The `.ps1` files below remain Windows compatibility wrappers only.

The Python CLI is the single implementation for instance initialization and synchronization. To create a new instance with an instance name and directory, run:

```text
python .workflow/workflow.py init-instance --name "Product A" --directory "E:\path\to\product-a"
```

Use `--dry-run` to preview the initialization. The command creates the instance Git repository, instance `README.md`, `baseline/`, `iteration/`, `workspace/`, and `.aw/workflow.lock`, then synchronizes the workflow definition.

Run `.\.workflow\scripts\sync-workflow.ps1 -TargetRoot '<target-project-root>'` from this repository to copy the workflow definition to a target Git working tree. The script copies only the items governed by `workflow-file-inventory.md`: shared rules, CLI, templates, scaffold READMEs, and Skills. It does not copy `baseline/` deliverables, `iteration/` deliverables, `workspace/` business code, or generated workflow state.

The script permits unrelated target changes, but rejects uncommitted changes that overlap a synchronized workflow path. After reviewing an intentional overlap, use `-AllowDirtyTarget`; use PowerShell's `-WhatIf` to preview the copy. The target `.gitignore` receives an idempotent managed block for `.workflow/`, `.agents/`, `templates/`, synchronized scaffold files, and `.aw/runtime/`; `workspace/workflow/` remains visible to Git. Invoke the framework CLI with `--project-root '<target-project-root>'` to write state to the target instance.

Every completed TASK must use `context` first, then `task-finished`. The latter validates that the task exists in the current task plan, requires the Context Pack, writes the latest conclusion plus an immutable history record, refreshes the recovery checkpoint, and prints a concise result. `index`, `validate`, `context`, and `task-finished` all refresh the checkpoint. It is a cache only: artifact frontmatter and gate results remain authoritative. Use `--refresh-index` or `--refresh-dashboard` when those generated views must also be refreshed.
