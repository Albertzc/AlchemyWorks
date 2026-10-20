---
name: normalize-requirement
description: Use whenever a user provides an unstructured requirement. Routes it to baseline intake or the manifest-selected iteration, then normalizes it into the appropriate draft artifacts.
---

# Normalize Requirement

## Purpose

Take a user-supplied raw requirement, which may arrive in inconsistent formats, route and archive it first, then normalize it into either the baseline draft or `iteration/v{major}.{minor}/01-product/v{major}.{minor}-requirement.md` draft.

## Route First

Before normalizing, resolve the route and archive the input as one intake batch:

```powershell
python .aw/.workflow/workflow.py route-requirement
python .aw/.workflow/workflow.py archive-requirement --source <file> --iteration <target-version>
```

Use `--iteration` only when `route-requirement` returns `mode: iteration`; omit it for `mode: baseline`. The archive command output and index record are authoritative for the target selected at intake time.

The command emits the archive location for the raw requirement according to these rules:

1. When `baseline/` is empty apart from `README.md`: return `mode: baseline` and `baseline/raw-requirement/`. This is the baseline-requirement path for a first-time project; preserve the user's original wording, and draft the four baseline documents and one core-flow prototype from explicit facts in the original material, all kept as `status: draft`.
2. When the baseline has already been initialized: return `mode: iteration`. Prefer the `iteration` field of `workspace/workflow/manifest.yaml`; if the manifest does not exist or has no valid version, fall back to directory discovery. `archive-requirement` stores the user's original material verbatim under an `intake-<name>/` batch directory and records the target version in `workspace/workflow/raw-requirement-index.yaml`.

Raw material is not a gate artifact and does not require frontmatter or `status: Approved`. Material under `iteration/raw-requirement/` is user-owned and read-only: agents MUST NOT modify, rename, or delete the raw files. The normalized artifact MUST record the intake batch, raw file path, and the target version returned by `route-requirement` in its frontmatter or "Source Traceability" section; only the normalized artifact enters human review.

## Pre-flight

| Version | Required prior call |
|---|---|
| baseline route | Archive raw requirement; draft the four `baseline/` documents and the core-flow prototype; after human review run `validate --stage 00-baseline`. |
| `v1.0` (first project) | After `00-baseline` passes, call `manage-iteration` to create the skeleton, archive the iteration snapshot of the same raw requirement, then normalize into the product requirement. |
| `v{major}.{minor}` (initialized project) | Use the version resolved by `route-requirement`; if the directory does not exist, call `manage-iteration` to create the skeleton first. |

## Required References

Under the iteration route, the following MUST be read before conversion:

- `baseline/01-product-vision.md`
- `baseline/02-product-charter.md`
- `baseline/04-glossary.md`
- All raw requirement batches listed in `workspace/workflow/raw-requirement-index.yaml` for the target version returned by `route-requirement`.
- `iteration/{previous approved version}/01-product/{previous version}-requirement.md` (for diff and inheritance).
- `iteration/{previous approved version}/05-review-release/{previous version}-release-log.md` (when present; records the predecessor's closing scope, ISSUE closure, and hand-off items).
- `templates/product.md` (the merged unified template).

The template is the sole authoritative source of output structure. Do not invent a separate Product Requirement structure.

## Input

Raw material comes from the user and may be a direct description, Markdown, plain text, email, meeting notes, or any other readable file. Read every piece of material in full before normalizing; do not infer the requirement from filename, summary, or chat memory alone.

Under the baseline route, draft the baseline documents from explicit facts in the raw material only; any missing tech-stack or other details MUST remain `draft` "to be confirmed" items and may not be filled in by the agent. Under the iteration route, generate the product-requirement draft from the approved baseline plus the iteration's raw material.

## Conversion Rules

### 1. Extract Facts First, Then Organize Structure

Classify the input into:

- **Explicit fact**: goals, users, features, or constraints directly expressed in the original text.
- **Reasonable inference**: content derived from context.
- **Missing information**: content that cannot be determined from the input.
- **Conflicting information**: descriptions in the input that contradict each other.

Only explicit facts may be written into the requirement body verbatim. Inferences, missing items, and conflicts MUST be marked in the body and aggregated into "Assumptions and Open Questions".

Recommended markers:

- `[待确认]`: needs Product Owner confirmation. (Convention kept in original form for cross-team consistency — see the stable marker list below.)
- `[推断]`: inferred from context; not yet confirmed by the user.
- `[未提供]`: no relevant information in the input.
- `[冲突]`: contradictory descriptions exist.

Do not fabricate users, metrics, permissions, technical solutions, data models, or business rules just to make the document look complete.

> Note: the four markers above are deliberately retained in their Chinese form because downstream `stage-gate` checks and template tooling match them as stable tokens. Translation Discipline (AGENTS.md §4 Documentation Language) permits this exception because they are string-literal anchors, not narrative headings.

### 2. Express in Product Language

Translate colloquial speech, complaints, and scattered ideas into product-requirement language. **Reuse the terminology from `baseline/glossary`**.

Do not write technical implementation into the product requirement. For example:

- Do not write "a REST API is needed" as an FR unless the user explicitly proposed an API as a product capability.
- Do not invent database tables, fields, caches, message queues, or framework choices.

### 3. Requirement Numbering

Generate stable IDs for items that can be verified independently:

- Functional requirements: `FR-001`, `FR-002`, …
- Business rules: `BR-001`, `BR-002`, …
- Non-functional requirements: `NFR-001`, `NFR-002`, …
- Acceptance criteria: `AC-001`, `AC-002`, …

A single ID describes only one judoleable requirement. If existing documents already use IDs, prefer to keep them. **In an iteration scenario, continue numbering after the predecessor's largest ID; never reuse a deprecated ID.**

### 4. Preserve Product Boundaries

The following MUST be distinguished:

- Required for MVP.
- Out of MVP scope for now.
- Candidate for a later version.
- Non-goal.

### 5. Iteration-Scenario Additional Requirements (v{major}.{minor}, minor ≥ 1)

On top of §1–§4, the following are **also** required:

#### 5.1 Increment Identification

Clearly distinguish:

- **Added requirements**: `FR` / `BR` / `NFR` / `AC` introduced this round.
- **Modified requirements**: existing IDs modified this round (keep the ID, update the content).
- **Deprecated requirements**: IDs explicitly deprecated this round (annotate as deprecated in the preface; do not delete).
- **Unchanged requirements**: do not list them again.

#### 5.2 Cross-Version Traceability

Every added / modified / deprecated requirement MUST be tagged in the preface:

```yaml
change_set:
  added: [FR-100, FR-101]
  modified: [FR-010, FR-022]
  deprecated: [FR-005]
```

… and reflected in the document body.

#### 5.3 Do Not Break the Predecessor

Do not modify any file under `iteration/v{major}.{minor-1}/`. If the predecessor has an error, open a new iteration and cover it with a "modified" entry.

### 6. Prototype Decision and Required Information

Extract page and interaction cues from the requirement, complete the prototype-trigger evaluation, and write the result into "Prototype Decision and Generation Requirements". The frontmatter of every iteration output MUST include `prototype_required: true` or `prototype_required: false`: `true` for new pages, complex / cross-page flows, business-result-impacting interactions, experience-critical work, multi-device adaptation, or experience disagreements; `false` for pure technical changes, lightweight changes that reuse existing interaction patterns, or changes that can be expressed unambiguously by spec and acceptance criteria. When `false`, the frontmatter MUST also carry non-empty `prototype_baseline` and `prototype_rationale`.

### 7. Acceptance Criteria

Prefer converting explicit business outcomes into `Given / When / Then`.

## Output Contract

### Baseline route

When `route-requirement` returns `mode: baseline`, the output is the following 5 `status: draft` artifacts:

```text
baseline/01-product-vision.md
baseline/02-product-charter.md
baseline/03-tech-stack-decision.md
baseline/04-glossary.md
baseline/05-core-user-flow-prototype.html
```

Every document MUST identify the raw-requirement source. Missing technology, metrics, or terminology MUST NOT be fabricated; keep them as "to be confirmed" items and wait for human review. Only after `validate --stage 00-baseline` passes may `iteration/v1.0/` be created.

The core-flow prototype may be a low-fidelity wireframe, click-through flow, or structured HTML, but MUST cover the core roles, key task closure, principal states, and permission differences; a high-fidelity visual is not required. When generating HTML prototypes, the `prototype-design-system` tool routing still applies.

### Iteration route

Output file path:

```text
iteration/v{major}.{minor}/01-product/v{major}.{minor}-requirement.md
```

The frontmatter MUST include:

```yaml
---
document_type: product-requirement
version: 1.0.0
status: draft
product_name: <product name>
base_version: <previous approved iteration, e.g. v1.0>
prototype_required: <true|false>
prototype_baseline: <required when prototype_required is false>
prototype_rationale: <required when prototype_required is false>
change_set:                  # iteration scenarios only
  added: [FR-XXX, ...]
  modified: [FR-XXX, ...]
  deprecated: [FR-XXX, ...]
baseline_ref:
  - baseline/01-product-vision.md
  - baseline/02-product-charter.md
owner: Product Owner
last_updated: YYYY-MM-DDTHH:MM:SS±HH:MM # Codex client local time
---
```

Output requirements:

1. Use the YAML frontmatter and section order from the template.
2. The document title, product name, and version stay consistent with the input; when not provided, use `[未提供]` (kept as the stable placeholder).
3. Functional requirements, business rules, non-functional requirements, and acceptance criteria use stable IDs.
4. Every uncertain item is explicitly marked.
5. Retain "Assumptions and Open Questions" at the end of the document.
6. Do not output API, database dictionary, system architecture, or implementation tasks.

> Note: `[未提供]` is the stable placeholder literal in the template (`templates/product.md`); it is kept verbatim to match the template parser.

## Human Review Gate

After conversion, the agent MUST keep `status: draft` or `status: In Review`, list every stage artifact pending review together with verification evidence, and request human confirmation; it MUST NOT change the status to `Approved`, nor directly feed the result into the next stage as a formal input. After human review passes, the human manually changes every required artifact to `status: Approved`, then runs `validate --stage 01-product`. Review focus:

- Product goals and user roles are accurate (consistent with the baseline).
- MVP scope is not over- or under-sized.
- Functional requirements are complete and have not been silently expanded.
- Key flows and acceptance criteria meet expectations.
- Marked items have been resolved.
- (Iteration) the `change_set` is accurate (added / modified / deprecated).

## Validation Checklist

- [ ] Archived the input with `archive-requirement`, confirmed its batch and target-version index record, and ran `route-requirement`.
- [ ] Under the baseline route, drafted the full baseline; under the iteration route, read the approved baseline.
- [ ] Read the standard template and the baseline.
- [ ] Every explicit fact in the raw input is findable in the output.
- [ ] No inference has been written as a confirmed fact.
- [ ] No unrequested technical design was introduced.
- [ ] Each functional requirement expresses only one verifiable goal.
- [ ] MVP scope, non-goals, and open questions are explicit.
- [ ] The frontmatter declares `prototype_required: true|false`; when `false`, also carries non-empty `prototype_baseline` and `prototype_rationale`.
- [ ] When `true`, the page, key interactions, and mock-data requirements are sufficient to support prototype generation.
- [ ] When generating the HTML prototype, the review frontmatter (`status`, `reviewer`, `reviewed_at`, `review_notes`) from `templates/Prototype.html` is preserved.
- [ ] Output filename equals `v{major}.{minor}-requirement.md`.
- [ ] (Iteration) `change_set` lists every change in this round completely.
- [ ] (Iteration) no file under `iteration/v{major}.{minor-1}/` has been modified.
