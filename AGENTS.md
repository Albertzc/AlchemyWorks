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

- "Current version" = the latest approved version in `iteration/v{major}.{minor}/` (or the version explicitly named by the task).
- **Approval/discovery distinction**: `discover_iteration()` returns the numerically highest active iteration directory; it does not filter by approval status. When a rule requires the latest approved version, the agent must inspect the `05-review-release/<version>-review-release.md` status for the discovered versions and select the highest approved `(major, minor)` pair. If no version is approved, use the numerically highest active version only where the rule explicitly permits a draft working version.
- Cross-version references must use stable IDs (FR-XXX, FS-XXX, API-XXX-XXX, TBL-XXX-XXX, TASK-XXX-XXX, AC-XXX).
- Do not silently resolve a conflict by guessing. State the conflict and ask for clarification, or record a clearly labeled assumption.

## 3. Understand Before Modifying

Before changing code, the agent MUST:

1. Read the relevant baseline documents in `baseline/` first.
2. Read the latest approved version's artifacts in `iteration/v{major}.{minor}/` (the highest approved `(major, minor)` pair).
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

- For a **new project (v1.0)**: preserve the user-provided raw requirement under `baseline/raw-requirement/`, use it to draft baseline artifacts (including the core user-flow prototype), and confirm the five required baseline artifacts are `status: Approved` before generating `iteration/v1.0/` artifacts.
- For a **later iteration**: use `normalize-requirement` to route, archive, and normalize the raw requirement, then use `manage-iteration` to create or archive the target `v{major}.{minor}`; read the latest approved version's artifacts as the baseline.
- **Iteration scope rule**: each task targets exactly one version. If a request affects multiple versions, split the work or escalate.

### Workflow Governance

The CLI and `workflow-governance` Skill are the operational owners. Use the
framework source path `.workflow/workflow.py`, the synchronized instance path
`.aw/.workflow/workflow.py`, or the source CLI with
`--project-root <instance-root>` for an external instance. Do not copy command
details into this file; use the Skill and the source `.workflow/README.md` (or
instance `.aw/.workflow/README.md`) reference.

The following invariants remain mandatory:

- Refresh the index before starting or resuming a stage; a nonzero stage gate is
  a hard stop.
- Human approval is required at every stage handoff. Agents may create or edit
  `draft` / `In Review` artifacts but must never set `status: Approved`.
- Before implementing a TASK, create and use exactly one task-scoped Context
  Pack; after it, record the task result with `task-finished`.
- After workflow-artifact changes, refresh the index. Do not report a TASK as
  complete before its task record and conclusion exist.
- Use the workflow inventory as the authority for protected paths and update it
  with any workflow-maintenance change.

The Context Pack is the default implementation context; load complete upstream
documents only when it lacks a required detail and record that exception.

### Workflow Core Protection

During product development, the workflow core is read-only. In the framework
source repository this covers `AGENTS.md`, the framework root `README.md`,
`.gitignore`, `.workflow/`, `.agents/skills/`, and `templates/`. In a
synchronized instance it covers `.aw/README.md`, `.aw/.workflow/`, and
`.aw/.agents/`; the instance root `AGENTS.md`, root `README.md`, `.gitignore`,
and root `templates/` remain instance-owned. The workflow may update only the
marked current-system-functionality section of the instance root README after
`05-review-release` passes. The CLI blocks operational commands when protected
core paths are dirty. Core changes require a dedicated maintenance change,
updated inventory/documentation/tests, and a clean commit before product work
resumes. `baseline/`, `iteration/`, and `workspace/` are not protected by this
guard.

The final report should summarize:

- What changed.
- Why it changed.
- Which version and stages are affected.
- Which files (with absolute path under `iteration/v{major}.{minor}/`, when applicable) were modified.
- Which tests and checks were run.
- Any remaining risks, assumptions, or follow-up work.

### Documentation Language

The governance and execution layer is English: this file, `.workflow/`,
`.agents/skills/`, their synchronized `.aw/` copies, stable IDs, CLI flags,
source, JSON, and HTML control files. The template, entry, and product layer is
Chinese by default: root `README.md`, `templates/`, and artifacts under
`iteration/v{major}.{minor}/`. An instance may choose another product-layer
language in `baseline/04-glossary.md`.

`templates/` is copied once and is not overwritten by `sync`. The framework root
README remains Chinese; use `.workflow/README.md` or
`.aw/.workflow/README.md` as the English execution reference. Governance text
must refer to template artifacts by stable path/identifier and section number,
not by translated headings.

## 5. Minimal Change and Existing Patterns

- Prefer the smallest complete change that satisfies the specification.
- Preserve existing behavior unless a change is explicitly required.
- Follow existing naming, directory, error-handling, logging, and testing patterns.
- Do not perform unrelated refactoring.
- Do not introduce a new framework or dependency without explaining the reason and trade-offs.
- Do not reformat unrelated files.
- Keep each change focused on one feature, fix, or documented purpose.
- **Version-scope rule**: do not modify an artifact of one `v{major}.{minor}` when the active task targets another version. If you discover an issue in a different version, file it as a follow-up rather than silently fixing across versions.

## 6. Architecture Rules

Respect the approved layer boundaries. Unless the architecture says otherwise,
keep the flow `presentation → application → domain → infrastructure`.

- Keep UI, controllers, business rules, persistence, and external integrations
  in their respective layers.
- Keep authentication and authorization boundaries intact; avoid circular
  dependencies and hidden global state.

## 7. Requirements and Documentation

Important behavior must be represented in durable project artifacts, not only in chat history.

Keep durable project records synchronized through the stage sequence
`01-product → 02-design → 03-planning → 04-implementation →
05-review-release`. The exact artifact list and gate conditions belong to the
`stage-gate` Skill and the templates.

- For a new project, preserve the unstructured source in
  `baseline/raw-requirement/`, pass the baseline gate, then create `v1.0`.
- For an initialized project, preserve the source in
  `iteration/raw-requirement/`, use `normalize-requirement` to route and
  normalize it, then use `manage-iteration` for the target version.
- Every iteration records its product requirement, prototype decision, design,
  plan, implementation evidence, and release review under
  `iteration/v{major}.{minor}/`. A prototype is required only when its
  requirement frontmatter says so; the baseline core-flow prototype is always
  required for a new project.
- Release-log creation is the post-RC closing step and is an existence-only
  condition; it does not require `status: Approved`.

Update documentation when implementation changes:

- Product behavior.
- API contracts.
- Data models.
- Configuration.
- User workflows.
- Deployment or operational behavior.
- Known limitations.

Do not document behavior that the code does not actually provide.

**Templates are shared across versions.** Any modification to `templates/` must
be evaluated against in-flight versions before applying.

## 8. Coding Standards

Use clear names, focused functions, explicit error handling, and existing type
and compiler settings. Prefer simple implementations, explain non-obvious
decisions, and remove debug output or experimental code from production paths.

## 9. Testing and Verification

Code is incomplete until the project's actual checks have run. Cover applicable
happy paths, failures, boundaries, security, validation, regression,
integration, and end-to-end behavior. Never claim a check passed without
observed evidence; concrete framework commands are listed in §16.

## 10. Definition of Done

Complete only when the requested behavior and approved acceptance criteria are
implemented, relevant checks pass, architecture and documentation are current,
the diff is self-reviewed, and remaining risks or assumptions are reported.
For a new project, the approved baseline core-flow prototype is mandatory; each
iteration must record its prototype decision.

## 11. Security and Privacy

Consider authentication, authorization, validation, encoding, secrets,
dependency risk, sensitive data, and auditability. Never commit credentials,
print sensitive data, weaken security to pass tests, or send project data to an
external service without authorization. Use placeholders and environment-based
configuration in examples.

## 12. Database and Data Changes

Treat production data as sensitive and potentially irreversible. Use migrations,
do not rewrite an applied migration without authorization, review destructive
operations and rollback compatibility, preserve tenant/user scopes, and test
constraints and migration behavior when relevant.

## 13. Performance and Reliability

Measure before optimizing. Review query and network volume, memory bounds,
pagination, races, timeouts, retries, idempotency, cleanup, observability, and
actionable error messages.

## 14. Git and Change Management

- Keep changes focused and reviewable.
- Inspect the diff before committing.
- Do not rewrite shared history without explicit approval.
- Do not force-push or delete branches unless authorized.
- Use one branch or worktree per significant feature or fix when practical.
- Keep generated artifacts separate from unrelated source changes.

When synchronized into an instance, the instance owns root `AGENTS.md`, root
`README.md`, `.gitignore`, and `templates/`. The local execution copy
(`.aw/.workflow/`, `.aw/.agents/`, `.aw/README.md`) is ignored; the instance
commits `baseline/`, `iteration/`, `workspace/`, and `workspace/workflow/`.

Commit messages should explain the change and use the project's existing
convention; otherwise prefer:

```text
<type>: <short description>
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

- Read applicable rules, `baseline/`, the relevant raw requirement, and the
  latest approved `iteration/v{major}.{minor}/` before artifact changes.
- Keep assumptions explicit, ask when ambiguity can materially change the
  result, and preserve user changes with reversible operations.
- Reuse existing tools and patterns, stop when a required dependency or decision
  is missing, and report evidence accurately using stable IDs.

The agent MUST NOT:

- Pretend requirements are clear, hide failures or risks, remove tests to pass,
  make unrelated architectural changes, use destructive commands without
  authorization, or claim completion without verification.
- Modify an artifact in a different iteration from the task target, skip the
  baseline gate before creating `v1.0`, or normalize raw input without
  preserving its source and routing decision.
- Set or change any artifact frontmatter to `status: Approved`; hand off
  `draft` / `In Review` artifacts with paths and validation evidence for human
  review instead.

## 16. Project-Specific Overrides

The following values apply to the AlchemyWorks framework source repository:

- Technology stack: Python `>=3.11`; standard-library-only runtime; GitHub Actions for CI and framework releases.
- Directory structure: `.workflow/` for CLI, scripts, dashboard, and source-only regression tests; `.agents/skills/` for Skills; `templates/` for instance defaults; root `AGENTS.md` and `README.md` for framework governance and entry guidance.
- Package manager: none required by the framework; use the configured Python interpreter directly.
- Build command: not applicable; syntax verification is `python -m compileall -q .workflow`.
- Lint command: no linter is configured; run `git diff --check` for whitespace errors before commit.
- Type-check command: none configured for this standard-library Python framework.
- Unit, integration, and end-to-end test command: `python .workflow/tests/test_workflow.py` (the current suite is the framework's combined regression suite; separate unit/integration/e2e commands are not defined).
- Deployment process: no runtime deployment; framework releases are produced by `.github/workflows/release.yml` from versioned Git commits and tags.
- Database migration process: not applicable; the framework has no database schema or migration system.
- Required security checks: no automated security scan is configured; manually verify that credentials and private data are not committed and review workflow and dependency changes before merge.
- Commit and pull-request conventions: use `<type>: <short description>`; keep workflow-core changes in a dedicated maintenance change and require review before merging to `main`.

An initialized instance must replace or extend the instance-specific rows above with concrete values from its approved `baseline/03-tech-stack-decision.md`, architecture, and validation plan before implementation begins. At minimum, the instance root `AGENTS.md` must name its package manager, build/start command, lint/type-check command or explicit `not configured` value, test commands, deployment process, migration process or `not applicable`, required security checks, and commit/PR convention. Project-specific rules must be precise, executable, and consistent with the approved architecture and baseline.

## 17. Versioning and Archive Rules

Iterations use the two-segment identifier **`v{major}.{minor}`**. The major
segment changes only for a baseline-level shift; incremental work advances the
minor segment. The CLI and `manage-iteration` Skill own parsing, discovery,
creation, and archive mechanics; this section states the invariants:

- `v{N}` is accepted only as a CLI compatibility alias for `v{N}.0`; it must
  not appear in normative paths, filenames, or version arithmetic.
- The next consecutive version after `v{major}.{minor}` is
  `v{major}.{minor+1}`. A major bump to `v{major+1}.0` requires an explicit
  baseline-level shift. Never reuse or skip a pair.
- Active artifacts use `iteration/v{major}.{minor}/` and the same version prefix
  in filenames. Cross-version frontmatter references must point to an existing
  iteration. Archived versions under `iteration/archive/` are read-only.
- RC-complete requires an Approved `05-review-release` artifact and an existing
  release log. The release log is existence-only; its status need not be
  Approved. The detailed closing procedure belongs to `review-release` and
  `release-log`.
- After RC completion, the workflow refreshes only the marked functionality
  section of the instance root `README.md`. The next version is created before
  the completed predecessor is archived; `baseline/` is not versioned.
