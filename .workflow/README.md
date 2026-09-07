# Workflow Control Layer

This directory contains generated workflow state and the standard-library CLI that reads the project documents.

## Commands

Run from the project root:

```powershell
python .workflow/workflow.py init
python .workflow/workflow.py init-version
python .workflow/workflow.py index --iteration v1
python .workflow/workflow.py route-requirement
python .workflow/workflow.py validate --iteration v1 --stage 00-baseline
python .workflow/workflow.py validate --iteration v1 --stage 01-product
python .workflow/workflow.py validate --iteration v1
python .workflow/workflow.py context --iteration v1 --task TASK-API-010
python .workflow/workflow.py dashboard --iteration v1
python .workflow/workflow.py task-finished --iteration v1 --task TASK-API-010 --result succeeded
```

`init` creates only the non-versioned intake directories, including `iteration/raw-requirement/README.md`. `init-version` creates the next version skeleton only after the baseline gate passes, and refreshes `manifest.yaml`. `route-requirement` determines where newly received, unstructured user requirements are archived. With an empty baseline it returns the baseline intake directory; otherwise it uses the `iteration` in `manifest.yaml` when available, falling back to version discovery, and returns that target version with the centralized `iteration/raw-requirement/` directory. Except for its README, this directory contains user-owned source material only: Agents must not modify, rename, or delete its files. `validate` is the `stage-gate` controller: a nonzero exit code means the requested formal stage cannot proceed. Raw requirements are source material, not approved stage artifacts. `index` writes the artifact manifest and stable-ID traceability graph. `context` creates a task-scoped pack under `context-packs/` and reuses it when its input fingerprint is unchanged.

Generated files:

- `manifest.yaml` — discovered artifacts, status, line count, and content hash.
- `traceability.json` — stable IDs and evidence-backed co-occurrence edges.
- `cache/context-packs.json` — Context Pack cache keys.
- `context-packs/` — compact task-specific context for implementation agents.
- `task-runs/` — task completion conclusions and gate/context metadata.
- `task-runs/history/` — immutable task completion history.
- `dashboard/index.html` — static project execution view.

The gate validates the complete upstream chain through the requested stage, including the required implementation and combined review-release artifact.

Every completed TASK must use `context` first, then `task-finished`. The latter validates that the task exists in the current task plan, requires the Context Pack, writes the latest conclusion plus an immutable history record, and prints a concise result. Use `--refresh-index` or `--refresh-dashboard` when those generated views must also be refreshed.
