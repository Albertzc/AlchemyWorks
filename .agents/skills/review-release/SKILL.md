---
name: review-release
description: Create or review the 05-review-release decision, evidence, risks, rollback plan, and release notes for a completed iteration.
---

# Review Release

Use this skill when preparing or reviewing the `05-review-release` artifact for one iteration. It prepares an evidence-backed release decision; it does not authorize deployment, merge, or approval by itself.

## Inputs

Confirm that `04-implementation` has passed its gate. Read the approved product/design/planning artifacts through their stable-ID references, implementation records, observed test results, known issues, and the actual diff. Do not claim checks passed unless their output was observed.

## Required Output

Create or update `iteration/v{major}.{minor}/05-review-release/v{major}.{minor}-review-release.md` as `draft` or `In Review`. It must record:

- scope and completed TASK/AC evidence;
- review findings, unresolved issues, security/privacy and operational risks;
- validation commands actually run and their observed results;
- migration, compatibility, rollout, monitoring, and rollback decisions when applicable;
- a clear release recommendation: release, hold, or release with accepted risks;
- user-facing release notes proportional to the delivered change.

For a hold decision, state the owner and condition needed to resume. Do not hide failed checks or turn an unresolved risk into an approval.

## Review Checks

Before handoff, verify that:

- the documented scope matches the approved plan and implementation evidence;
- every acceptance criterion has passing evidence, an explicit exception, or a release-blocking decision;
- known limitations and ISSUE IDs are reflected consistently;
- data changes have a recovery path where their failure would be material;
- the release recommendation is consistent with observed tests, review findings, and remaining risk.

Use `workflow-governance` to run `index` after artifact changes. Submit the artifact for human review; do not set `status: Approved`. After human approval, use `workflow-governance` to run `validate --stage 05-review-release` under the `stage-gate` policy. The next version creation then archives the completed predecessor according to `manage-iteration`.
