# Workflow Required Files and Directories

> This file is the authoritative directory inventory of the AlchemyWorks workflow itself. It describes the workflow's definitions, execution capabilities, and initialization scaffold. It does not describe deliverables produced by a specific project or iteration.

## 1. Maintenance Rules

- When any workflow file or directory listed in the tables below is modified, added, moved, or deleted, this inventory MUST be updated in the same change.
- When workflow behavior changes, this inventory must be updated together with any affected documentation, Skills, templates, tests, or `.gitignore` rules.
- A new entry must first clarify its purpose, whether it is required, and whether it is reproducible runtime state. Reproducible state MUST NOT be added to the "required" entries of this inventory.
- Code review and workflow self-checks must treat "implementation change matches this inventory" as a review item.

### 1.1 Core Scaffold Protection

- The workflow definitions, Skills, templates, governance rules, scripts, and tests registered in the tables below are treated as a read-only core scaffold during product development.
- Project deliverables under `baseline/`, `iteration/`, and `workspace/` are not part of the core scaffold. The `manifest.yaml`, `traceability.json`, and `current-state.json` files under `workspace/workflow/` are reproducible instance-project state and must be managed by the instance project's Git. The synchronized `.aw/` directory is a local workflow copy that is ignored by default.
- `python .workflow/workflow.py verify-workflow` checks whether the framework source core scaffold has uncommitted modifications; in a synchronized instance use `python .aw/.workflow/workflow.py verify-workflow`. Product workflow CLI commands block when such modifications are detected.
- The core scaffold may only be modified through a dedicated workflow-maintenance change. That change must update this inventory, the affected documentation, tests, and sync scripts in the same change, and must be committed cleanly before product workflow commands resume.

### 1.2 Source and instance ownership

- The framework source repository tracks `.workflow/`, `.agents/`, `templates/`, `AGENTS.md`, and its root `README.md` as release inputs.
- An initialized instance receives synchronized copies at `.aw/.workflow/`, `.aw/.agents/`, and `.aw/README.md`; the instance Git configuration ignores `.aw/`.
- Instance-owned `AGENTS.md`, root `README.md`, `templates/`, `baseline/`, `iteration/`, `workspace/`, and `workspace/workflow/` remain outside the synchronized `.aw/` copy and are tracked by the instance project.
- `sync` must not be used to make framework source paths and instance paths interchangeable: the source-to-instance mapping is intentional and is defined by `WORKFLOW_SYNC_ITEMS`.

### 1.3 Rule Ownership Map

The same rule must have one authoritative owner. Other layers may summarize or
link to it, but must not introduce a competing interpretation:

| Rule category | Authoritative owner | Role of the other layers |
|---|---|---|
| Source priority, approval boundary, version scope, security, and agent conduct | `AGENTS.md` | Skills and README explain the application; CLI may reject objectively invalid states. |
| Version parsing/discovery, stage validation, required paths, archive preconditions, README marker checks, generated state, and protected-core dirty checks | `.workflow/workflow.py` plus regression tests | `AGENTS.md` states the invariant; `workflow-governance` and `manage-iteration` document how to invoke it. |
| Stage procedure, raw-requirement handling, artifact authoring, review evidence, and human decision checklists | `.agents/skills/*/SKILL.md` | `AGENTS.md` keeps only the non-negotiable boundary and links to the Skill. |
| Command reference, examples, synchronization walkthroughs, and troubleshooting | `.workflow/README.md` and root `README.md` | `AGENTS.md` points to the relevant reference and does not duplicate the command manual. |
| Workflow-owned path inventory and source-to-instance mapping | This inventory | `AGENTS.md` and README use the mapping; sync code follows `WORKFLOW_SYNC_ITEMS`. |

When a rule changes, update its authoritative owner and the dependent summary,
tests, and synchronization inputs in the same workflow-maintenance change.

## 2. Required Top-Level Governance Files

| Path | Type | Purpose |
|---|---|---|
| `AGENTS.md` | Governance rules | Defines collaboration, approval, versioning, change, and security constraints. |
| `README.md` | Framework source entry and usage guide | The framework source README is synchronized into instance `.aw/README.md`. `init-instance` creates a separate project-owned root `README.md`; `sync` never overwrites or ignores it. |
| `.gitignore` | Version-control rules | The source repository normally tracks workflow source files; the sync script only idempotently appends a managed block that ignores `.aw/` into instance projects. It never overwrites existing instance rules and never excludes instance state under `workspace/workflow/`. |

## 2.1 Framework Repository Release Metadata and CI

These files belong only to the AlchemyWorks framework repository. They are not
synchronized into instance projects and do not manage instance iteration
versions.

| Path | Type | Purpose |
|---|---|---|
| `pyproject.toml` | Framework release metadata | Single source of truth for the framework's SemVer version. |
| `.github/workflows/ci.yml` | Repository CI | Validates the framework version format and runs framework regression tests. |
| `.github/workflows/release.yml` | Repository release automation | Uses repository commits to prepare framework releases, update `pyproject.toml`, create `vMAJOR.MINOR.PATCH`, and publish the release. |

## 3. Required Workflow Execution and Verification Directories

| Path | Required contents | Purpose |
|---|---|---|
| `.aw/.workflow/` (source repo: `.workflow/`) | `workflow.py`, `README.md` | Workflow CLI (including baseline core-flow prototype and per-iteration prototype gates, the `refresh` command run after document changes, automatic maintenance of the instance root `README.md` current-system-functionality section from the release log after `05-review-release` passes, version-archive validation, and Context Pack cache cleanup for archived versions) and its operating documentation. The instance copy of this directory does not include regression tests. |
| `.aw/.workflow/scripts/` (source repo: `.workflow/scripts/`) | `stage_status.py`, `id_registry.py`, `query_id.py`, `check_links.py`, `diff_versions.py` | State, ID, link, and version-comparison utilities callable by agents and maintainers. |
| `.aw/.workflow/dashboard/` | `template.html` | Workflow dashboard source template; dashboard pages are generated on demand. |
| `.workflow/tests/` (source repo only) | `test_workflow.py` | Regression tests for the workflow CLI; not copied into instance projects at initialization. |

## 4. Required Agent Capability Directories

| Path | Required contents | Purpose |
|---|---|---|
| `.aw/.agents/skills/stage-gate/` (source repo: `.agents/skills/stage-gate/`) | `SKILL.md` | Stage-start, handoff, and review gate policy: stage order, required artifacts, and human-approval conditions. |
| `.aw/.agents/skills/normalize-requirement/` | `SKILL.md` | Raw-requirement routing and normalization rules. |
| `.aw/.agents/skills/manage-iteration/` | `SKILL.md` | Rules for creating, discovering, and archiving iterations; archives an RC-complete previous version after the next version is created successfully. |
| `.aw/.agents/skills/prototype-design-system/` | `SKILL.md` | Prototype visual, interaction, and design-token constraints. The Skill references `templates/design-tokens.json` as the authoritative source; the historical `references/design-tokens.json` duplicate was removed. |
| `.aw/.agents/skills/design-specification/` | `SKILL.md` | 02-design architecture, API, and database-dictionary artifact and consistency-check rules. |
| `.aw/.agents/skills/planning-validation/` | `SKILL.md` | 03-planning TASK DAG, acceptance-coverage, and validation-plan constraints. |
| `.aw/.agents/skills/iterate-implementation/` | `SKILL.md` | Implementation-stage code, tests, and record constraints; v1.0 keeps a standalone `issue-fixes.md`, v1.1+ merges ISSUE records into `source-code.md`. |
| `.aw/.agents/skills/review-release/` | `SKILL.md` | 05-review-release review evidence, risks, rollback, and release-decision constraints. |
| `.aw/.agents/skills/release-log/` | `SKILL.md` | 05-review-release closing artifact (`v{major}.{minor}-release-log.md`); existence-only contract, no `status: Approved` check. |
| `.aw/.agents/skills/workflow-governance/` | `SKILL.md` | Sole operational entry point for the workflow CLI: index, state, validate, traceability, Context Pack, and task-finished commands. |

## 5. Required Cross-Project Template Directory

| Path | Required contents | Purpose |
|---|---|---|
| `templates/` | `README.md`, `product.md`, `design.md`, `implementation.md`, `release-log.md` | Copied into instance project roots at initialization as the default templates maintainable by the instance project. |
| `templates/` | `Prototype.html`, `prototype-design-system.md`, `design-tokens.json` | Prototype baseline, visual specification, and machine-readable design tokens; prototype review uses `status` as the only review-conclusion field. |

## 6. Required Initialization Scaffold Directories

These directories belong to instance projects, not to the AlchemyWorks source repository. `init-instance` creates the directories and their README files; `sync` does not synchronize these directories.

| Path | Required contents | Purpose |
|---|---|---|
| `baseline/` | `README.md`, `raw-requirement/README.md` | Baseline, required core-flow prototype, and raw-requirement intake for first-time project setup. |
| `iteration/` | created at instance initialization | Entry point for versioned deliverables and later raw requirements. |
| `workspace/` | `README.md` | Real business code, tests, and configuration for the instance project, plus a static README describing workspace operating conventions. System functionality is documented in the instance root `README.md`, not here. |

## 7. Explicitly Out of Scope for Required Workflow Items

The following content is input to, produced by, or cached by a project that uses the workflow. It must not be mistaken for part of the workflow definition.

| Path pattern | Classification | Handling rule |
|---|---|---|
| Content under `baseline/` other than the README and the raw-requirement intake | Project baseline deliverables | Maintained by the specific project. |
| Files under `baseline/raw-requirement/` other than `README.md` | User-supplied raw input, grouped by intake batch | Preserved byte-for-byte; not modified by agents. |
| Files under `iteration/raw-requirement/` other than `README.md` | User-supplied raw input, grouped by intake batch | Preserved byte-for-byte; not modified by agents. |
| `iteration/v{major}.{minor}/`, `iteration/archive/` | Versioned deliverables | Belong to the specific project and version; follow stage-approval and archive rules. |
| Content under `workspace/` | Business implementation and workspace documentation | Belongs to the product code, tests, configuration, and workspace operating conventions. |
| `workspace/workflow/manifest.yaml`, `traceability.json`, `current-state.json` | Instance-project state and audit index | Not part of the workflow source definition; generated for the selected instance-project root and committed under that instance project's version control, not managed by `.gitignore`. |
| `workspace/workflow/raw-requirement-index.yaml` | Instance-project raw-intake source index | Generated by `archive-requirement`; records intake batch, baseline/iteration scope, target version, source paths, hashes, and sizes; committed with instance-project state. |
| `.aw/` | Synchronized framework files and local reproducible runtime state | May exist in the instance directory for local execution but is not part of the instance project's business commits; the sync script adds it to the instance `.gitignore` by default. |
| `.aw/workflow-version.yaml` | Synchronization version metadata | Written by `init-instance` / `sync`; records the workflow ref and commit; not committed by the instance project. |
| Instance root `README.md` | Instance-owned functionality document | Created by `init-instance`, committed by the instance project, and updated only in its marked current-system-functionality section after `05-review-release`; never overwritten by `sync`. |

## 8. Consistency Checks

Before every workflow change is considered complete, confirm at least the following:

1. Every required path touched by the change is correctly registered in this inventory.
2. This inventory does not misclassify project input, versioned deliverables, business code, or reproducible state as required workflow items.
3. The ignore block appended by the sync script excludes only `.aw/`; `README.md`, `templates/`, `baseline/`, `iteration/`, `workspace/`, and `workspace/workflow/` remain committable.
4. The workflow tests pass and clean their project-local scratch directory: `python .workflow/tests/test_workflow.py`.
5. New instance root READMEs continue to point at `.aw/.workflow/workflow.py`; `workspace/README.md` remains static workspace guidance; the synchronized `workflow-governance` Skill in the instance uses the `.aw/.workflow/` command path.
6. After `sync`, `.aw/README.md` is byte-equivalent to the framework source root `README.md`; the instance root `README.md` and `AGENTS.md` remain untouched.
7. Framework release metadata and CI are repository-only and must not be added to `WORKFLOW_SYNC_ITEMS` or used to advance `iteration/v{major}.{minor}`.
