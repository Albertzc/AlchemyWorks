# AGENTS.md

## 1. Purpose

This file defines the general collaboration rules for AI agents and developers working in this software project.

The goal is to produce maintainable, testable, secure, and production-ready software with the smallest reasonable change.

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
Approved Iteration Changelog (current version)
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

- For a **new project (v1)**: confirm `baseline/` is fully `status: Approved` before generating `iteration/v1/` artifacts.
- For an **iteration (v2+)**: use `normalize-iteration-requirement` to detect and create the new version; read the latest approved version's artifacts as the baseline.
- **Iteration scope rule**: each task targets exactly one version. If a request affects multiple versions, split the work or escalate.

### Workflow Governance

The project-level workflow control layer is implemented by `.workflow/workflow.py` and the `workflow-governance` Skill. These controls are mandatory for versioned workflow work:

1. **Before starting or resuming a stage**, refresh the artifact index:
   `python .workflow/workflow.py index --iteration v{N}`
2. **Before consuming a stage's inputs**, run its gate:
   `python .workflow/workflow.py validate --iteration v{N} --stage <stage>`
3. A nonzero gate result is a hard stop. Do not bypass missing, draft, unapproved, or unresolved-placeholder inputs, and do not change approval metadata to force progress.
4. **Before implementing a TASK**, create and use exactly one task-scoped Context Pack:
   `python .workflow/workflow.py context --iteration v{N} --task TASK-XXX-NNN`
5. The Context Pack is the default implementation context. Load complete upstream documents only when the pack lacks a required detail, and record that exception in the implementation record.
6. **After changing workflow artifacts**, rerun `index` so `.workflow/manifest.yaml`, `.workflow/traceability.json`, and hash caches reflect the new content.
7. **After completing every TASK**, run:
   `python .workflow/workflow.py task-finished --iteration v{N} --task TASK-XXX-NNN --result <succeeded|failed|blocked>`
8. Do not report a TASK as complete until this command has refreshed `.workflow/dashboard/index.html` and printed the task conclusion for human confirmation.

The Context Pack contains the selected TASK definition, related stable IDs, relevant contract excerpts, and input hashes. It reduces repeated full-document loading; it does not replace human approval or alter the source-of-truth priority.

The final report should summarize:

- What changed.
- Why it changed.
- Which version and stages are affected.
- Which files (with absolute path under `iteration/v{N}/`) were modified.
- Which tests and checks were run.
- Any remaining risks, assumptions, or follow-up work.

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
Baseline (baseline/)
    ↓
Product Requirement  (iteration/v{N}/01-product/v{N}-requirement.md)   # 需求 + 功能规格（FS 作为 FR 子项内嵌）
    ↓
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
Pull Request          (iteration/v{N}/05-pull-request/v{N}-pull-request.md)
    ↓
Release Notes         (iteration/v{N}/06-rc-review-release/v{N}-release-notes.md)   # 合并自原 3 份 RC 文档
    ↓
Iteration Changelog   (iteration/v{N}/01-product/v{N}-iteration-changelog.md)    # 封档说明，RC 完成后产出
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

## 15. AI Agent Behavior

The agent MUST:

- Read applicable rules and project context before acting.
- Check `baseline/` and the latest approved `iteration/v{N}/` before any artifact change.
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
- Skip the `baseline-gate` check before creating `iteration/v1/`.

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
- **RC-complete** is reached only when `iteration/v{major}.{minor}/06-rc-review-release/v{major}.{minor}-release-notes.md` has `status: Approved`.
- Upon RC completion of `v{major}.{minor}`:
  1. Move the previous version's directory to `iteration/archive/v{major}.{minor-1}/` (within the same major). When the version is the first minor of a new major, archive the previous major to `iteration/archive/v{prev_major}.0/`.
  2. Create `iteration/v{major}.{minor}/01-product/v{major}.{minor}-iteration-changelog.md` summarizing the cycle.
  3. Update the active version reference (latest approved iteration) used by all skills.
  4. Never skip a version number — `v1.1` cannot jump to `v1.3`.
- **Discovery**: `discover_iteration()` returns the numerically highest `(major, minor)` pair present under `iteration/`. When no directory exists yet, it returns `v1.0`.
- **Archived versions are read-only**; any correction must be done in a new version.
- **The `baseline/` is not versioned**; changes go through ADR.
