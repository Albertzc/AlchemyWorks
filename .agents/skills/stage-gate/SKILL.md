---
name: stage-gate
description: Use when starting, handing off, or reviewing any workflow stage. Enforces required inputs, human approval, and the gate that must pass before the next stage begins.
---

# Stage Gate

## Purpose

Centralize the stage-gate policy for the workflow. Every formal artifact stage (project baseline, 01-product through 05-review-release) requires human review. The next stage may start only after every required artifact of the current stage has reached `status: Approved` and its gate validation has passed.

## Stage Order

```text
Raw user requirement (unstructured input)
    ↓ normalize-requirement routes and archives
00-baseline (first project only)
    ↓
01-product → 02-design → 03-planning → 04-implementation → 05-review-release
```

## Required Inputs

### 00-baseline

The following project-level artifacts must exist and carry `status: Approved`:

1. `baseline/01-product-vision.md`
2. `baseline/02-product-charter.md`
3. `baseline/03-tech-stack-decision.md`
4. `baseline/04-glossary.md`
5. `baseline/05-core-user-flow-prototype.html` (a reviewable interactive prototype covering the core roles, key task closure, principal states, and permission differences; low fidelity is acceptable)

### 01-product Prototype Decision

Every iteration's `requirement.md` frontmatter MUST declare `prototype_required: true` or `prototype_required: false`. This is a human-reviewable, gate-checkable decision record:

- `true`: `v{major}.{minor}-prototype.html` becomes a required and Approved artifact for that iteration's 01-product gate. Applies to new pages, complex or cross-page flows, interactions that affect business outcomes, experience-critical changes, multi-device adaptations, or changes where reviewers have already raised interaction disagreements.
- `false`: the prototype is not a required artifact for that iteration's gate. The non-empty `prototype_baseline` and `prototype_rationale` frontmatter fields become required gate fields, and the requirement plus feature specification must record the inherited interaction baseline and the reason for not producing a prototype. Applies to backend-only or non-UI changes, lightweight UI changes that reuse existing patterns, and changes that can be expressed unambiguously through specification and acceptance criteria.

The baseline core-flow prototype is always required; page prototypes for functional iterations are produced on demand according to the decision above.

### HTML Prototype Review Record

Every HTML prototype MUST use an HTML-comment frontmatter that includes at least `status`, `reviewer`, `reviewed_at`, and `review_notes`. Generated prototypes use `status: draft`. When a human review passes, the human fills in the reviewer, timestamp, and conclusion, and sets `status: Approved`. `validate` treats missing or incomplete review metadata as a blocking gate error.

## Raw Requirement Intake

Raw requirements are user-supplied source material that may arrive as Markdown without frontmatter, plain text, email, meeting notes, or any other readable file. They are not stage artifacts that require `status: Approved`; agents MUST NOT rewrite their original text.

- When `baseline/` is empty apart from `README.md`: archive the raw material to `baseline/raw-requirement/`, and let `normalize-requirement` draft the baseline documents.
- When the baseline has already been initialized: run `python .workflow/workflow.py route-requirement`. That command prefers the `iteration` field of `.workflow/manifest.yaml` to determine the version, and emits the centralized raw-requirement library `iteration/raw-requirement/` together with the target version. That directory holds user input only and is read-only for agents.
- Normalized baseline or product requirements enter human review and `stage-gate`; raw requirements never do.

## Ownership Boundary

This skill defines only the **gate policy**: stage order, required artifacts, human approval, and the conditions that allow the next stage to begin. It does not define or duplicate the workflow CLI operating steps.

`workflow-governance` is the sole operational entry point for index, state-recovery, Context Pack, `validate`, and task-finished commands. When starting, handing off, or reviewing a stage, run those commands via that skill first; its `validate` result is the only executable evidence that this skill's policy has been satisfied.

## Handoff Policy

1. Agents create or update `draft` / `In Review` artifacts only, and list every required artifact path plus verification evidence for human review.
2. After human review, the human manually sets every required artifact of the current stage to `status: Approved`.
3. The next stage may start only when the corresponding stage validation run via `workflow-governance` returns zero; a non-zero result is a hard stop.

## Failure Handling

- Do not skip any stage, review, or gate.
- Do not let agents write or change `status: Approved`.
- Stop and request correction when raw requirements are missing, unreadable, or when a normalized artifact has lost its traceable source.

## Output

The report must list: the current stage, every required artifact, the status of each, the validation command and its result, and whether the next stage is permitted to start.
