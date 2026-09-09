---
name: planning-validation
description: Create or review the 03-planning TASK DAG and validation plan from approved product and design artifacts.
---

# Planning Validation

Use this skill when creating, revising, or reviewing the `03-planning` artifacts for one iteration. It makes the implementation plan executable; it does not replace task-scoped Context Packs during 04 implementation.

## Inputs

Confirm that `02-design` has passed its gate. Read the relevant approved requirement and design sections plus `templates/implementation.md`. Preserve the stable IDs already assigned upstream.

## Required Outputs

Create or update these `draft` or `In Review` artifacts under `iteration/v{major}.{minor}/03-planning/`:

- `v{major}.{minor}-task-plan-dag.md`: independently executable TASK IDs, scope, dependencies, touched areas, related stable IDs, sequencing, and completion evidence.
- `v{major}.{minor}-validation-plan.md`: acceptance criteria mapped to validation layers, test cases or checks, commands, test data/environment needs, and release-critical checks.

Split work when one TASK would span unrelated responsibilities or cannot be verified independently. Do not invent implementation tasks for out-of-scope requirements.

## Planning Review Checks

Before handoff, check that:

- every in-scope AC is mapped to at least one TASK and at least one validation activity;
- DAG dependencies are explicit, acyclic, and permit a sensible execution order;
- each TASK has bounded scope, defined completion evidence, and references only existing upstream IDs;
- validation includes relevant success, failure, boundary, authorization, integration, and migration cases;
- commands are actual project commands where known; unknown commands stay explicitly marked for human decision rather than fabricated.

Use `workflow-governance` to run `index` after artifact changes. Submit both artifacts for human review; do not set `status: Approved`. After human approval, use `workflow-governance` to run `validate --stage 03-planning` under the `stage-gate` policy.
