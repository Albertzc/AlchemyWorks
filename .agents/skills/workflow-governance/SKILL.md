---
name: workflow-governance
description: Run this project’s deterministic stage gates, artifact index, traceability graph, cache, and task-scoped Context Pack commands.
---

# Workflow Governance

Use this project skill when starting or reviewing a versioned workflow stage.

## Required commands

Run from the project root:

```powershell
python .workflow/workflow.py index --iteration v1.0
python .workflow/workflow.py validate --iteration v1.0 --stage <stage>
python .workflow/workflow.py context --iteration v1.0 --task TASK-XXX-NNN
python .workflow/workflow.py dashboard --iteration v1.0
python .workflow/workflow.py task-finished --iteration v1.0 --task TASK-XXX-NNN --result succeeded
```

The `--iteration` flag accepts either `v{major}.{minor}` (e.g. `v1.0`, `v1.1`) or the legacy short form `v{N}` (treated as `v{N}.0`). Omit the flag to let `discover_iteration()` pick the highest existing version.

Run `validate` before using a stage. A nonzero result is a hard stop: do not change approval metadata or bypass the missing/draft dependency. Use `index` after artifact changes so hashes and stable-ID evidence are current. After every TASK, run `task-finished` with exactly one result: `succeeded`, `failed`, or `blocked`. This writes a task-run record, refreshes the static Dashboard, and prints the task conclusion for human confirmation. It does not approve artifacts automatically.

## Context Pack rule

Implementation work must consume one TASK-scoped Context Pack. The pack contains the task definition, referenced stable IDs, relevant contract sections, and source hashes. Do not load complete requirement, architecture, API, database, planning, or historical implementation documents unless the pack explicitly lacks a required detail.

## Outputs

- `.workflow/manifest.yaml`
- `.workflow/traceability.json`
- `.workflow/cache/index.json`
- `.workflow/cache/context-packs.json`
- `.workflow/context-packs/<iteration>-<task>.md`
- `.workflow/task-runs/<iteration>-<task>.json`
- `.workflow/dashboard/index.html`

These are generated state, not approval records. Human approval remains represented by artifact frontmatter and must be explicit.

This skill covers the first, third, and fourth workflow improvements. Stage 2 and stages 05/06 remain out of scope for the current implementation.
