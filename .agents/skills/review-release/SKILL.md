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

## Companion Artifact: Release Log

This stage also produces `iteration/v{major}.{minor}/05-review-release/v{major}.{minor}-release-log.md` via the `release-log` skill. The two artifacts have distinct contracts:

- `v{major}.{minor}-review-release.md`: requires `status: Approved`; this skill owns it.
- `v{major}.{minor}-release-log.md`: existence-only gate (frontmatter `status` does **not** block the validate check); the `release-log` skill owns it.

Draft the release log after the review-release artifact reaches Approved. Use `workflow-governance` to run `validate --stage 05-review-release` once both files exist; the gate confirms presence of the release log without requiring its `status` to be `Approved`.

## Review Checks

Before handoff, verify that:

- the documented scope matches the approved plan and implementation evidence;
- every acceptance criterion has passing evidence, an explicit exception, or a release-blocking decision;
- known limitations and ISSUE IDs are reflected consistently;
- data changes have a recovery path where their failure would be material;
- the release recommendation is consistent with observed tests, review findings, and remaining risk.

Use `workflow-governance` to run `index` after artifact changes. Before submitting the release artifact, draft the release log via the `release-log` skill (`iteration/v{major}.{minor}/05-review-release/v{major}.{minor}-release-log.md`, existence-only contract). The instance root `README.md` is the project-owned product document. A successful `validate --stage 05-review-release` atomically replaces the entire root README using the target Approved requirement's product name and complete `README 模块摘要` catalog, plus only user-visible release-log §7 limits. Every active FR/BR must be covered exactly once; missing, duplicate, deprecated, or unknown IDs block generation. The cumulative FR/BR replay remains the coverage authority. Freshness validation compares the complete rendered file. This generated README has no separate approval step; the existing Approved `review-release.md` gate remains required. `workspace/README.md` remains static workspace guidance. Submit `review-release.md` and the release log for the existing review and approval flow; do not set `status: Approved` on `review-release.md`. After human approval, use `workflow-governance` to run `validate --stage 05-review-release` under the `stage-gate` policy. `manage-iteration` then revalidates and refreshes the predecessor README before archiving it.
## Instance document ownership

The instance root `README.md` is a fully generated product document. After the 05-review-release gate, the CLI replaces the entire file with current product overview, module-level capability summaries, version, and user-visible limits. It contains no workflow instructions or per-requirement ID listing. Keep `workspace/README.md` as static workspace guidance. The root `AGENTS.md` is created once during initialization and is not synchronized afterwards.

This ownership rule supersedes any earlier wording in this skill that describes `workspace/README.md` as the release-functionality destination or the root `README.md` as framework-owned.
