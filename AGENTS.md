# AGENTS.md

## 1. Purpose

This file defines the general collaboration rules for AI agents and developers working in this software project.

The goal is to produce maintainable, testable, secure, and production-ready software with the smallest reasonable change.

## 1.1 Workflow directory layout

The AlchemyWorks source repository keeps its framework source files at the repository root for maintainability. When initialized or synchronized into an instance project, workflow execution files are placed under `.aw/`; the instance-maintained default templates remain at the project root:

```text
.aw/README.md
.aw/.workflow/
.aw/.agents/
templates/
.aw/workflow-version.yaml
```

The instance root `AGENTS.md` is created once from the framework rules and is then owned by the instance project. It is not synchronized afterwards, so workflow upgrades must be merged into it deliberately. In a synchronized instance, use `python .aw/.workflow/workflow.py ...` for local commands; when operating from the framework source repository, use the source-repository path `python .workflow/workflow.py ...` with `--project-root` for an external instance.

Directory ownership is intentionally different between the framework source repository and an initialized instance:

| Concern | Framework source repository | Instance project |
|---|---|---|
| Workflow CLI and definitions | `.workflow/` | `.aw/.workflow/` |
| Agent Skills | `.agents/skills/` | `.aw/.agents/skills/` |
| Workflow entry README | root `README.md` | `.aw/README.md` |
| Instance-owned templates | root `templates/` | root `templates/` |
| Product and generated project state | not applicable | `baseline/`, `iteration/`, `workspace/`, `workspace/workflow/` |

The framework source directories are tracked and released with the framework. The synchronized `.aw/` directory is an instance-local copy and is ignored by the instance project's Git configuration; instance-owned templates and product state remain tracked.

## 2. Source of Truth

Use the following priority order when information conflicts:

```text
Explicit User Requirement
        ↓
Approved Baseline Product Vision & Charter
        ↓
Approved Baseline Tech Stack Decision
        ↓
Approved Product Specification (current version)
        ↓
Approved Architecture Decision (current version)
        ↓
Approved Implementation Plan (current version)
        ↓
Existing Code Conventions
        ↓
Individual Implementation Preference
```

Notes:

- "Current version" = the latest approved version in `iteration/v{N}/` (or the version explicitly named by the task).
- Cross-version references must use stable IDs (FR-XXX, FS-XXX, API-XXX-XXX, TBL-XXX-XXX, TASK-XXX-XXX, AC-XXX).
- Do not silently resolve a conflict by guessing. State the conflict and ask for clarification, or record a clearly labeled assumption.

## 3. Understand Before Modifying

Before changing code, the agent MUST:

1. Read the relevant baseline documents in `baseline/` first.
2. Read the latest approved version's artifacts in `iteration/v{N}/` (latest `N` with `status: Approved`).
3. Inspect the existing repository structure and affected modules.
4. Search for existing patterns before creating new modules, services, components, utilities, or database models.
5. Identify affected files, dependencies, tests, and documentation.
6. Explain the intended approach for significant changes before implementation.

Do not make broad changes when a focused change is sufficient.

## 4. Standard Task Workflow

For every significant task, follow this sequence:

```text
Understand
    ↓
Analyze Impact (which versions, which stages)
    ↓
Plan
    ↓
Implement
    ↓
Test and Verify
    ↓
Review
    ↓
Update Documentation
    ↓
Report
```

**Version awareness**:

- For a **new project (v1)**: preserve the user-provided raw requirement under `baseline/raw-requirement/`, use it to draft baseline artifacts (including the core user-flow prototype), and confirm the five required baseline artifacts are `status: Approved` before generating `iteration/v1/` artifacts.
- For an **iteration (v2+)**: use `normalize-requirement` to route, archive, and normalize the raw requirement, then use `manage-iteration` to create or archive the target version; read the latest approved version's artifacts as the baseline.
- **Iteration scope rule**: each task targets exactly one version. If a request affects multiple versions, split the work or escalate.

### Workflow Governance

The project-level workflow control layer is implemented by the workflow CLI and the `workflow-governance` Skill. In this framework source repository the CLI is `.workflow/workflow.py`; in a synchronized instance project it is `.aw/.workflow/workflow.py`. These controls are mandatory for versioned workflow work:

The authoritative inventory of workflow-owned files and directories is `.workflow/workflow-file-inventory.md` in the framework source repository and `.aw/.workflow/workflow-file-inventory.md` in a synchronized instance. Any change to the workflow itself (including its CLI, scripts, Skills, templates, governance documents, scaffold, tests, or generated-state ignore rules) MUST update that inventory in the same change.

1. **Before starting or resuming a stage**, refresh the artifact index:
   `python .aw/.workflow/workflow.py index --iteration v{N}`
2. **At every stage handoff**, after the current stage's required outputs have been reviewed by a human, run its gate:
   `python .aw/.workflow/workflow.py validate --iteration v{N} --stage <completed-stage>`
3. A nonzero gate result is a hard stop: the next stage cannot start. Do not bypass missing, draft, unapproved, or unresolved-placeholder inputs.
4. **Human approval is required for every stage handoff.** An agent must create or update artifacts with `status: draft` or `status: In Review`, list every required artifact and its verification evidence for human review, and wait for a human to set each artifact's frontmatter to `status: Approved`. An agent must never add, replace, or otherwise change an artifact's `status` to `Approved`.
5. **Before implementing a TASK**, create and use exactly one task-scoped Context Pack:
   `python .aw/.workflow/workflow.py context --iteration v{N} --task TASK-XXX-NNN`
6. The Context Pack is the default implementation context. Load complete upstream documents only when the pack lacks a required detail, and record that exception in the implementation record.
7. **After changing workflow artifacts**, rerun `index` so `workspace/workflow/manifest.yaml`, `workspace/workflow/traceability.json`, and the local hash/runtime caches reflect the new content.
8. **After completing every TASK**, run:
   `python .aw/.workflow/workflow.py task-finished --iteration v{N} --task TASK-XXX-NNN --result <succeeded|failed|blocked>`
9. Do not report a TASK as complete until this command has written the task record and printed the task conclusion for human confirmation. Refresh the dashboard separately when needed.

The Context Pack contains the selected TASK definition, related stable IDs, relevant contract excerpts, and input hashes. It reduces repeated full-document loading; it does not replace human approval or alter the source-of-truth priority.

When these rules are executed from the framework source repository, replace `.aw/.workflow/` in the commands above with `.workflow/`; when operating on an external instance from the framework source repository, use the source CLI with `--project-root <instance-root>`.

### Workflow Core Protection

During product development, the workflow core is read-only. Do not modify `AGENTS.md`, the root workflow `README.md`, `.gitignore`, the source workflow paths `.workflow/workflow.py`, `.workflow/README.md`, `.workflow/workflow-file-inventory.md`, `.workflow/scripts/`, `.workflow/tests/`, the source `.agents/skills/`, or `templates/` as part of a product or iteration task. In synchronized instances, the corresponding execution paths are `.aw/.workflow/` and `.aw/.agents/`; the instance `.aw/` copy is ignored by default. The workflow CLI blocks operational commands when these paths have uncommitted changes. Changes to them require a dedicated workflow-maintenance change, updated inventory/documentation/tests, and a clean commit before product work resumes. Project artifacts under `baseline/`, `iteration/`, and `workspace/` are not protected by this guard.

The final report should summarize:

- What changed.
- Why it changed.
- Which version and stages are affected.
- Which files (with absolute path under `iteration/v{N}/`) were modified.
- Which tests and checks were run.
- Any remaining risks, assumptions, or follow-up work.

### Documentation Language

Framework documents fall into two layers, each with a single working language. The split is intentional and is not changed instance-by-instance.

**Governance & Execution Layer (English):**

- `AGENTS.md` (this file, including §1–§17).
- Framework source paths: `.workflow/` — CLI, scripts, README, inventory, tests; `.agents/skills/` — `SKILL.md` frontmatter and bodies.
- Synchronized instance paths: `.aw/.workflow/` — CLI, scripts, README, inventory; `.aw/.agents/skills/` — `SKILL.md` frontmatter and bodies. The instance copy does not include framework regression tests.
- Stable identifiers: `FR-XXX`, `FS-XXX`, `BR-XXX`, `NFR-XXX`, `AC-XXX`, `TASK-XXX-XXX`, `API-XXX-XXX`, `TBL-XXX-XXX`, `ISSUE-XXX`.
- CLI flags, Python sources, JSON files, and HTML templates.

Rationale: governance text and runtime behavior must be auditable by any agent or operator regardless of locale. English matches the stable-ID convention and the existing CLI vocabulary.

**Template, Entry, and Product Layer (Chinese):**

- `README.md` at the framework root — entry guide for instance projects (intentionally Chinese; no English mirror is published).
- `templates/*.md` — product, design, implementation, release-log, prototype design system.
- Every artifact produced under `iteration/v{major}.{minor}/` by following the templates, including `requirement.md`, `architecture-design.md`, `api-spec.md`, `database-dictionary.md`, `task-plan-dag.md`, `validation-plan.md`, `source-code.md`, `test-results.md`, `review-release.md`, `release-log.md`, and HTML prototypes.

Rationale: templates and the artifacts they produce are read by instance teams during requirement, design, implementation, and release review. Keeping them in Chinese maximizes readability for Chinese-first teams without forcing translation overhead.

**Override and Synchronization Contract:**

- Instance projects may document their own product-layer language preference in `baseline/04-glossary.md`. The framework does not enforce a single product-layer language; the choice above is the default.
- `templates/` is copied once by `init-instance` and is never overwritten by `sync`. A framework language change does not retroactively update already-synchronized instances; instance templates remain as previously copied.
- The framework root `README.md` is intentionally Chinese; operators needing an English entry point may use `.workflow/README.md` plus this file's §1–§17 as a substitute.

**Translation Discipline:**

When the governance layer references a template-layer artifact by path or section, the reference uses the file's English-stable identifier (for example `01-product`, `requirement.md`) and the section number, never the Chinese heading text. This keeps cross-layer linking stable across language changes and avoids accidental drift when a Chinese heading is revised.

## 5. Minimal Change and Existing Patterns

- Prefer the smallest complete change that satisfies the specification.
- Preserve existing behavior unless a change is explicitly required.
- Follow existing naming, directory, error-handling, logging, and testing patterns.
- Do not perform unrelated refactoring.
- Do not introduce a new framework or dependency without explaining the reason and trade-offs.
- Do not reformat unrelated files.
- Keep each change focused on one feature, fix, or documented purpose.
- **Version-scope rule**: do not modify an artifact of version `v{N}` when the active task targets `v{N+1}`. If you discover an issue in `v{N}`, file it as a follow-up rather than silently fixing across versions.

## 6. Architecture Rules

Respect the project's layer boundaries. Unless the approved architecture states otherwise, use a structure similar to:

```text
Presentation Layer
        ↓
Application Layer
        ↓
Domain Layer
        ↓
Infrastructure Layer
```

General rules:

- Keep UI components focused on presentation and interaction.
- Keep controllers and route handlers thin.
- Keep business rules in domain or service modules.
- Keep database access in repository or infrastructure modules.
- Do not bypass authentication or authorization boundaries.
- Avoid circular dependencies and hidden global state.
- Keep external integrations behind explicit interfaces.

## 7. Requirements and Documentation

Important behavior must be represented in durable project artifacts, not only in chat history.

Keep the following chain synchronized:

```text
Raw Requirement (user-provided, unstructured)
    ↓
Baseline (baseline/, first-project intake only)
    ↓
Raw Requirement Library (iteration/raw-requirement/, user-owned and read-only; route-requirement returns target version)
    ↓
Product Requirement  (iteration/v{N}/01-product/v{N}-requirement.md)   # 需求 + 功能规格（FS 作为 FR 子项内嵌）
    ↓
Prototype Decision   (`prototype_required: true|false` in the requirement frontmatter)
    ↓ (only when true)
HTML Prototype       (iteration/v{N}/01-product/v{N}-prototype.html)
    ↓
Architecture Design   (iteration/v{N}/02-design/v{N}-architecture-design.md)
+
API Spec              (iteration/v{N}/02-design/v{N}-api-spec.md)
+
Database Dictionary   (iteration/v{N}/02-design/v{N}-database-dictionary.md)
    ↓
Task Plan DAG         (iteration/v{N}/03-planning/v{N}-task-plan-dag.md)
+
Validation Plan       (iteration/v{N}/03-planning/v{N}-validation-plan.md)
    ↓
Source Code           (iteration/v{N}/04-implementation/v{N}-source-code.md)   # 实施主记录 + ISSUE 列表
+
Test Results          (iteration/v{N}/04-implementation/v{N}-test-results.md)
    ↓
Review & Release      (iteration/v{N}/05-review-release/v{N}-review-release.md)   # 评审、合并、发布决定与 release notes
    ↓
Release Log           (iteration/v{N}/05-review-release/v{N}-release-log.md)    # 封档说明,RC 完成后产出（仅需存在,无需 Approved）
```

Update documentation when implementation changes:

- Product behavior.
- API contracts.
- Data models.
- Configuration.
- User workflows.
- Deployment or operational behavior.
- Known limitations.

Do not document behavior that the code does not actually provide.

**Templates are shared across versions.** Any modification to `templates/` must be evaluated against in-flight versions before applying.

## 8. Coding Standards

- Use clear, intention-revealing names.
- Keep functions and classes focused on one responsibility.
- Prefer simple, explicit implementations over premature abstraction.
- Handle expected errors explicitly.
- Do not silently swallow exceptions or failures.
- Add comments only when they explain why a non-obvious decision exists.
- Preserve type safety and strict compiler settings when the project supports them.
- Do not leave debug output, temporary files, or experimental code in production paths.

## 9. Testing and Verification

Code is not complete until it has been verified.

For behavior changes, add or update appropriate tests, including where relevant:

- Happy paths.
- Error cases.
- Boundary conditions.
- Authentication and authorization cases.
- Data validation.
- Regression cases.
- Integration behavior.
- End-to-end user flows.

Run the project's actual commands rather than assuming a tool or framework. Typical checks may include:

```text
Format Check
Lint
Type Check
Unit Tests
Integration Tests
End-to-End Tests
Build
Security Scan
```

Never claim that a test, build, or check passed unless it was actually run and its result was observed.

## 10. Definition of Done

A task is complete only when all applicable conditions are satisfied:

### Functional

- The requested behavior is implemented.
- Approved acceptance criteria are satisfied.
- Error and boundary cases are handled.

### Technical

- The project builds or starts successfully.
- Relevant tests pass.
- No obvious regression is introduced.
- Code follows existing architecture and conventions.

### Documentation

- The relevant artifacts under `iteration/v{N}/<stage>/` are updated.
- The baseline core user-flow prototype is present and approved for a new project; each iteration records whether an additional prototype is required and why.
- The relevant baseline document (`baseline/`) is updated if scope changes affect project-level constants.
- API or user documentation is updated when behavior changes.
- Configuration or migration instructions are documented when needed.

### Review

- The diff has been self-reviewed.
- Unrelated changes are removed.
- Security and performance impact has been considered.
- Remaining risks and assumptions are reported.

## 11. Security and Privacy

Always consider:

- Authentication.
- Authorization.
- Input validation.
- Output encoding.
- Secret management.
- Sensitive data exposure.
- Dependency vulnerabilities.
- Auditability.

Never:

- Commit passwords, API keys, tokens, private keys, or production credentials.
- Print secrets or sensitive user data in logs.
- Disable security checks to make tests pass.
- Weaken authentication or authorization without explicit approval.
- Send project or user data to an external service without authorization.

Use placeholders and environment-based configuration in examples.

## 12. Database and Data Changes

- Treat production data as sensitive and potentially irreversible.
- Use migrations for schema changes.
- Do not rewrite an applied migration unless explicitly authorized.
- Review destructive operations carefully.
- Consider backward compatibility and rollback behavior.
- Preserve tenant, user, and authorization scopes where applicable.
- Add tests for constraints, indexes, validation, and migration behavior when relevant.

## 13. Performance and Reliability

Do not optimize based only on assumptions. Measure when performance matters.

Pay attention to:

- Excessive database queries.
- Unbounded memory usage.
- Unnecessary network requests.
- Missing pagination or batching.
- Race conditions.
- Timeouts and retries.
- Idempotency.
- Resource cleanup.
- Observability and actionable error messages.

## 14. Git and Change Management

- Keep changes focused and reviewable.
- Inspect the diff before committing.
- Do not rewrite shared history without explicit approval.
- Do not force-push or delete branches unless authorized.
- Use one branch or worktree per significant feature or fix when practical.
- Keep generated artifacts separate from unrelated source changes.

When this workflow is synchronized into an instance project, the instance owns its
root `AGENTS.md`, root `README.md`, `.gitignore`, and `templates/`. The synchronized
workflow copy (`.aw/.workflow/`, `.aw/.agents/`, and `.aw/README.md`) may exist
locally for execution but is ignored by the instance Git configuration. The instance commits
its `baseline/`, `iteration/`, `workspace/`, and `workspace/workflow/` state instead.

Commit messages should explain the change and its purpose. Use the project's existing convention; otherwise prefer:

```text
<type>: <short description>
```

Examples:

```text
feat: add production order status workflow
fix: reject invalid connector configuration
test: add pipeline execution regression cases
docs: update local development instructions
```

### Framework release versioning

The AlchemyWorks framework repository manages its own release version in
`pyproject.toml` under `[project].version`, using SemVer `MAJOR.MINOR.PATCH`.
Framework releases are represented by Git tags named `vMAJOR.MINOR.PATCH` and
are automated by the repository-level GitHub Actions workflows. Conventional
Commit messages determine the intended bump (`fix` for PATCH, `feat` for
MINOR, and `!` or `BREAKING CHANGE` for MAJOR).

This framework release process is separate from instance product iterations.
It must not modify or advance `iteration/v{major}.{minor}` in an instance
project. An instance's `.aw/workflow-version.yaml` records only the framework
source ref and commit used for synchronization.

## 15. AI Agent Behavior

The agent MUST:

- Read applicable rules and project context before acting.
- Check `baseline/`, the relevant user-provided raw requirement, and the latest approved `iteration/v{N}/` before any artifact change.
- Keep assumptions explicit.
- Ask for clarification when ambiguity can materially change the result.
- Prefer reversible operations.
- Preserve user changes.
- Use existing tools and patterns before inventing new ones.
- Stop and report when a required dependency, permission, or decision is missing.
- Report verification evidence accurately.
- Use stable IDs across versions to enable traceability.

The agent MUST NOT:

- Pretend that requirements are clearer than they are.
- Hide failed checks or unresolved risks.
- Remove tests to make a build pass.
- Make unrelated architectural changes.
- Use destructive commands without explicit authorization.
- Claim completion without verification.
- Modify an artifact under `iteration/v{N}/` when the task targets `v{N+1}` (cross-version contamination).
- Skip the `stage-gate` check before creating `iteration/v1/`, or normalize a user-provided raw requirement without preserving its source and routing decision.
- Add or change any artifact frontmatter value to `status: Approved`. The agent must instead hand off the draft or `In Review` artifacts, their paths, and validation evidence for human review.

## 16. Project-Specific Overrides

Projects should extend this file with concrete values for:

- Technology stack (must agree with `baseline/03-tech-stack-decision.md`).
- Directory structure (must follow the `baseline/ + iteration/ + templates/ + workspace/` convention).
- Package manager.
- Build command.
- Lint and type-check commands.
- Unit, integration, and end-to-end test commands.
- Deployment process.
- Database migration process.
- Required security checks.
- Commit and pull-request conventions.

Project-specific rules should be precise, executable, and consistent with the approved architecture and baseline.

## 17. Versioning and Archive Rules

Iterations use a two-segment identifier **`v{major}.{minor}`** (e.g. `v1.0`, `v1.1`, `v2.0`). The major segment changes on baseline-level shifts (new project, architecture reset, tech-stack swap, major feature sets); the minor segment changes on incremental work (additive features, bug fixes, experience refinements) on top of the same baseline.

- **Format**: `v{major}.{minor}`. Plain `v{N}` is accepted as a backward-compatibility alias for `v{N}.0`.
- **Monotonic**: within the same major, minor numbers are monotonic integers; major numbers are monotonic integers. Never reuse a pair.
- **Directory layout**:
  - Active versions live under `iteration/v{major}.{minor}/`.
  - All versioned artifacts use the `v{major}.{minor}-` filename prefix.
  - Cross-version references in frontmatter must point to a real existing iteration (e.g. `base_version: v1.0`).
- **RC-complete** is reached only when the release log has been drafted, `iteration/v{major}.{minor}/05-review-release/v{major}.{minor}-review-release.md` has `status: Approved`, and `iteration/v{major}.{minor}/05-review-release/v{major}.{minor}-release-log.md` exists. The release log is an existence-only gate: its frontmatter `status` is not required to be `Approved`. In the framework source repository, the related Skill is `.agents/skills/release-log/SKILL.md`; in an instance, it is `.aw/.agents/skills/release-log/SKILL.md`.
- After `05-review-release` passes, the workflow automatically regenerates the marked current-system-functionality section in the instance root `README.md` from the current iteration's `iteration/v{major}.{minor}/05-review-release/v{major}.{minor}-release-log.md`. The release-log §2.1-§2.4 (delivery list), §3 (closed-issue list), and §7 (limits / assumptions) are extracted into that section, and the `<!-- workflow:current-system-functionality-version: v{major}.{minor} -->` marker is refreshed. Other root README content remains instance-owned. `workspace/README.md` only explains workspace conventions and does not carry system functionality.
- When the next consecutive version is successfully created, archive that completed predecessor to `iteration/archive/v{major}.{minor}/`. The predecessor must first pass the `05-review-release` gate and the instance root README refresh check; the first version (`v1.0`) has no predecessor to archive.
- Never skip a version number — `v1.1` cannot jump to `v1.3`.
- **Discovery**: `discover_iteration()` returns the numerically highest `(major, minor)` pair present under `iteration/`. When no directory exists yet, it returns `v1.0`.
- **Archived versions are read-only**; any correction must be done in a new version.
- **The `baseline/` is not versioned**; changes go through ADR.
