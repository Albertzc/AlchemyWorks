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
python .workflow/workflow.py validate --iteration v1.0 --stage 00-baseline
python .workflow/workflow.py validate --iteration v1.0 --stage <stage>
python .workflow/workflow.py context --iteration v1.0 --task TASK-XXX-NNN
python .workflow/workflow.py dashboard --iteration v1.0
python .workflow/workflow.py task-finished --iteration v1.0 --task TASK-XXX-NNN --result succeeded
```

The `--iteration` flag accepts either `v{major}.{minor}` (e.g. `v1.0`, `v1.1`) or the legacy short form `v{N}` (treated as `v{N}.0`). Omit the flag to let `discover_iteration()` pick the highest existing version.

At each formal stage handoff, leave every required artifact as `draft` or `In Review`, list its path and verification evidence for human review, and wait for a human to set its frontmatter to `status: Approved`; agents must never write or modify that value. A raw requirement is input material, not a formal stage artifact. Once the human review is complete, run `validate --stage <completed-stage>`. A nonzero result is a hard stop and the next stage must not start. Use `index` after artifact changes so hashes and stable-ID evidence are current. After every TASK, run `task-finished` with exactly one result: `succeeded`, `failed`, or `blocked`. This writes a task-run record and prints the task conclusion for human confirmation; use `--refresh-dashboard` or `dashboard` when the static Dashboard must be refreshed. It does not approve artifacts automatically.

## Context Pack rule

Implementation work must consume one TASK-scoped Context Pack. The pack contains the task definition, referenced stable IDs, relevant contract sections, and source hashes. Do not load complete requirement, architecture, API, database, planning, or historical implementation documents unless the pack explicitly lacks a required detail.

## Outputs

- `.workflow/manifest.yaml`
- `.workflow/traceability.json`
- `.workflow/cache/context-packs.json`
- `.workflow/context-packs/<iteration>-<task>.md`
- `.workflow/task-runs/<iteration>-<task>.json`
- `.workflow/task-runs/history/<iteration>-<task>-<timestamp>.json`
- `.workflow/dashboard/index.html`

These are generated state, not approval records. Human approval remains represented by artifact frontmatter and must be explicit.

The stage gate validates the complete upstream chain through the requested stage. `task-finished` requires a pre-generated Context Pack and preserves both the latest task record and an immutable history record.
