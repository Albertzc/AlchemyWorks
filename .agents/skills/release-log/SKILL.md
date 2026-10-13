---
name: release-log
description: Create the post-RC release log at 05-review-release stage. Existence-only contract; no human approval gate.
---

# Release Log

Use this skill when drafting the `v{major}.{minor}-release-log.md` closing memo for a completed iteration. It records what shipped, what issues closed, the final quality-gate state, hand-off items to the next version, and known limits or assumptions.

## Inputs

Confirm that the `05-review-release` review-release.md has been `status: Approved`. Read the approved product, design, and planning artifacts through their stable-ID references, the implementation record, observed test results, the review-release decision, and the actual diff. Do not claim checks passed unless their output was observed.

Required reading before drafting:

- `iteration/v{major}.{minor}/05-review-release/v{major}.{minor}-review-release.md` — Approved.
- `iteration/v{major}.{minor}/01-product/v{major}.{minor}-requirement.md` — Approved, with `change_set`.
- `iteration/v{major}.{minor}/04-implementation/v{major}.{minor}-source-code.md` — contains the ISSUE list.
- `iteration/v{major}.{minor}/04-implementation/v{major}.{minor}-test-results.md` — observed test data.
- `iteration/v{major}.{minor}/03-planning/v{major}.{minor}-task-plan-dag.md` — TASK list.
- `iteration/v{major}.{minor}/03-planning/v{major}.{minor}-validation-plan.md` — AC coverage.
- The actual `git diff` and CI output (when applicable).

## Required Output

Create or update `iteration/v{major}.{minor}/05-review-release/v{major}.{minor}-release-log.md` with the following 8 sections:

1. **Scope Overview** — a five-dimension table covering business, workflow, module, database, and compatibility.
2. **Delivery List** — four sub-tables for added features, experience refinements, business rules, and acceptance criteria (keyed by `FR` / `BR` / `AC`, referencing `TASK` IDs).
3. **ISSUE Closure** — `ISSUE-ID` table plus whether any carry-over was added.
4. **Key Engineering Changes** — module-level changes with an impact column.
5. **Quality Gate Final State** — three-column table of check, command, and result; the trailing row covers the `preflight` workflow-consistency check.
6. **Next-Version Hand-off** — table of priority and source.
7. **Known Limits and Assumptions** — categories for limits and assumptions, including §7.1 the version-relation and archive-path subsection (archive timing per AGENTS.md §17).
8. **Closing Checklist** — checkbox list reconciling the `status: Approved` state of every 01–05 stage artifact; the trailing row marks this file as "existence-only, no `Approved` required".

Frontmatter:

```yaml
---
document_type: release-log
version: <v{major}.{minor}.0>
status: draft                  # this artifact does not participate in the Approved gate; draft / In Review are both fine as long as the file exists
owner: Tech Lead
last_updated: <ISO 8601>
base_version: <previous approved iteration>
change_set:
  deprecated: [FR-XXX, ...]    # only the deprecated sub-key is read by diff_versions.py; added/modified live in requirement.md
baseline_ref:
  - baseline/03-tech-stack-decision.md
---
```

Template: `templates/release-log.md`.

## Approval Contract

**Release log is not gated by `status: Approved`.** The `validate --stage 05-review-release` step requires the file to exist; the frontmatter `status` value (`draft` / `In Review` / `Approved`) does not block the gate. This is implemented as a carve-out in `validation_report()` matching paths ending with `{iteration}-release-log.md`. See `.workflow/tests/test_workflow.py` for the existence-only contract tests.

Implications for the agent:

- After drafting, keep `status: draft` (or `In Review`); do not ask a human to change `status` to `Approved`.
- In §8 Closing Checklist, the "this file" row uses `[x]` instead of `[ ]` because file existence counts as delivery.
- A separate human-review round is no longer required. The technical accuracy of the closing memo and the evidence consistency with `source-code.md` and `test-results.md` are guaranteed by the other checks in `validate --stage 05-review-release` together with the `status: Approved` state of `review-release.md`.

## Review Checks

Before handoff, verify that:

- Every `FR` / `BR` / `AC` ID in the §2 sub-tables exists in `requirement.md` and `validation-plan.md`; every referenced `TASK` ID exists in `task-plan-dag.md`.
- Every `ISSUE-ID` in the §3 ISSUE table appears in the ISSUE list of `source-code.md`, or is explicitly tagged "identified during implementation".
- The §5 Quality Gate commands and results are the actual output of running them (each row records the source or run time at the end); do not paraphrase the second-hand data from `review-release.md`.
- The source column in §6 Hand-off items (identified during implementation / preflight hint / business-side feedback) is traceable; do not insert work that has already been completed in this round.
- §7 Known Limits / Assumptions covers every carry-over identified during implementation and is consistent with the §5 Known Limits of `source-code.md`.
- §7.1 Version-relation subsection describes an archive path that matches the description in the `manage-iteration` skill.
- Every checkbox in §8 Closing Checklist agrees with the frontmatter `status` of the corresponding stage artifact; the "this file" row uses `[x]`.

## Workflow Hooks

After drafting, use `workflow-governance` to run `index` so the new artifact appears in `workspace/workflow/manifest.yaml`. Run `validate --stage 05-review-release` once the file exists to confirm the existence-only gate passes; this gate does **not** require `status: Approved` on this artifact. The next iteration's creation then archives this release log into `iteration/archive/v{major}.{minor}/05-review-release/v{major}.{minor}-release-log.md` per `manage-iteration`.
