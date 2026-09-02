# Workflow Control Layer

This directory contains generated workflow state and the standard-library CLI that reads the project documents.

## Commands

Run from the project root:

```powershell
python .workflow/workflow.py index --iteration v1
python .workflow/workflow.py validate --iteration v1 --stage 01-product
python .workflow/workflow.py validate --iteration v1
python .workflow/workflow.py context --iteration v1 --task TASK-API-010
python .workflow/workflow.py dashboard --iteration v1
python .workflow/workflow.py task-finished --iteration v1 --task TASK-API-010 --result succeeded
```

`validate` is a gate: a nonzero exit code means the requested stage cannot proceed. It never changes document approval status. `index` writes the artifact manifest, stable-ID traceability graph, and SHA-256 file cache. `context` creates a task-scoped pack under `context-packs/` and reuses it when its input fingerprint is unchanged.

Generated files:

- `manifest.yaml` — discovered artifacts, status, line count, and content hash.
- `traceability.json` — stable IDs and evidence-backed co-occurrence edges.
- `cache/index.json` — artifact fingerprints.
- `cache/context-packs.json` — Context Pack cache keys.
- `context-packs/` — compact task-specific context for implementation agents.
- `task-runs/` — task completion conclusions and gate/context metadata.
- `dashboard/index.html` — static project execution view.

The current change intentionally does not implement stage 2 or generate pull-request/release artifacts for stages 05/06.

Every completed TASK must use `task-finished`. It refreshes the index and static Dashboard, then prints a concise conclusion for human confirmation.
