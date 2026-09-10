---
name: workflow-governance
description: Run this project’s deterministic stage gates, artifact index, traceability graph, cache, and task-scoped Context Pack commands.
---

# Workflow Governance

Use this project skill when starting or reviewing a versioned workflow stage.

## Required commands

Run from the project root:

```powershell
python .workflow/workflow.py init
python .workflow/workflow.py init-version
python .workflow/workflow.py index --iteration v1.0
python .workflow/workflow.py state --iteration v1.0 --refresh
python .workflow/workflow.py verify-workflow
python .workflow/workflow.py validate --iteration v1.0 --stage 00-baseline
python .workflow/workflow.py validate --iteration v1.0 --stage <stage>
python .workflow/workflow.py context --iteration v1.0 --task TASK-XXX-NNN
python .workflow/workflow.py cleanup --iteration v1.0
python .workflow/workflow.py cleanup --iteration v1.0 --execute
python .workflow/workflow.py dashboard --iteration v1.0
python .workflow/workflow.py task-finished --iteration v1.0 --task TASK-XXX-NNN --result succeeded
```

The `--iteration` flag accepts either `v{major}.{minor}` (e.g. `v1.0`, `v1.1`) or the legacy short form `v{N}` (treated as `v{N}.0`). Omit the flag to let `discover_iteration()` pick the highest existing version.

This Skill is the sole operational owner of workflow CLI commands. Apply `stage-gate`'s approval policy at every formal handoff: after a human has approved the required artifacts, run `validate --stage <completed-stage>`; a nonzero result is a hard stop. Use `state --refresh` when resuming, `index` after artifact changes, and `task-finished` after every TASK with exactly one result: `succeeded`, `failed`, or `blocked`. `task-finished` writes a task-run record and prints the conclusion; use `--refresh-dashboard` or `dashboard` when the static Dashboard must be refreshed. These commands never approve artifacts automatically.

## Context Pack rule

Implementation work must consume one TASK-scoped Context Pack. The pack contains the task definition, referenced stable IDs, relevant contract sections, and source hashes. Do not load complete requirement, architecture, API, database, planning, or historical implementation documents unless the pack explicitly lacks a required detail.

## Outputs

- `.workflow/manifest.yaml`
- `.workflow/traceability.json`
- `.workflow/current-state.json`
- `.workflow/cache/context-packs.json`
- `.workflow/context-packs/<iteration>-<task>.md`
- `.workflow/task-runs/<iteration>-<task>.json`
- `.workflow/task-runs/history/<iteration>-<task>-<timestamp>.json`
- `.workflow/dashboard/index.html`

These are generated state, not approval records. Human approval remains represented by artifact frontmatter and must be explicit.

`cleanup --iteration <version>` is a dry run that lists generated Context Packs and cache keys for an archived version. Add `--execute` to remove only those packs and keys. It never removes `task-runs` or their immutable history.

Generated timestamps use the local timezone of the Codex client running the command and include the ISO 8601 offset; do not reinterpret them as Codex server time.

Before resuming work, run `state --refresh` to refresh the manifest, traceability graph, and recovery checkpoint, then use its current-stage, blocker, next-action, and active-Context-Pack fields to load only the required inputs. The checkpoint is invalidated by a changed source fingerprint and must never override artifact frontmatter or a stage gate.

The stage gate validates the complete upstream chain through the requested stage. `task-finished` requires a pre-generated Context Pack and preserves both the latest task record and an immutable history record.
