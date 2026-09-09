---
name: design-specification
description: Create or review the 02-design architecture, API, and database artifacts from approved product requirements and baseline decisions.
---

# Design Specification

Use this skill when creating, revising, or reviewing the `02-design` artifacts for one iteration. It defines design quality; `stage-gate` and `workflow-governance` remain responsible for approval, indexing, and gate execution.

## Inputs

Before drafting, confirm that `01-product` has passed its gate. Read the approved requirement, relevant baseline decisions (especially the technology stack and glossary), and `templates/design.md`. Read only the requirement sections and stable IDs that the design must cover.

Do not introduce a framework, integration, data store, or security model that contradicts the approved baseline. Record unresolved design choices as `[待确认]` rather than treating them as settled.

## Required Outputs

Create or update these `draft` or `In Review` artifacts under `iteration/v{major}.{minor}/02-design/`:

- `v{major}.{minor}-architecture-design.md`: boundaries, responsibilities, data flows, cross-cutting concerns, and ADR references.
- `v{major}.{minor}-api-spec.md`: endpoint/event contracts, callers, authorization, validation, errors, idempotency and compatibility where applicable.
- `v{major}.{minor}-database-dictionary.md`: tables, fields, constraints, indexes, relationships, tenant/audit scope, and migration/rollback implications where applicable.

Use stable IDs consistently: each designed capability must trace to relevant FR/FS/BR/NFR/AC IDs; API and table IDs must point to each other where they interact.

## Design Review Checks

Before handoff, check that:

- every in-scope requirement and acceptance criterion has a design location or a deliberate, documented non-applicability decision;
- architecture boundaries match the approved technology and authorization model;
- API inputs, outputs, validation, and error behavior are unambiguous enough to implement and test;
- persisted data has ownership, lifecycle, integrity constraints, and migration handling appropriate to the change;
- API, database, and architecture references do not contradict one another.

Use `workflow-governance` to run `index` after artifact changes. Submit the three artifacts for human review; do not set `status: Approved`. After human approval, use `workflow-governance` to run `validate --stage 02-design` under the `stage-gate` policy.
