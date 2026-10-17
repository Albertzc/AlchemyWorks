---
name: iterate-implementation
description: "04 stage write code source-code.md tests."
---

# Iterate Implementation

## Purpose

Land the 03-planning TASK DAG as actual code: source, configuration, and tests, and record the implementation process structurally in three core documents under `iteration/v{N}/04-implementation/`.

This skill covers exactly one full iteration's 04 stage (for example `v1` or `v2+`). For frontend / backend separated projects, split by workspace subdirectory.

## Inputs (preconditions)

Before entering 04, confirm:

1. `iteration/v{N}/03-planning/v{N}-task-plan-dag.md` `status: Approved`.
2. `iteration/v{N}/03-planning/v{N}-validation-plan.md` has fixed the verification commands.
3. The `iteration/v{N}/02-design/` trio (`architecture-design.md` / `api-spec.md` / `database-dictionary.md`) is complete.
4. `iteration/v{N}/01-product/v{N}-requirement.md`, the applicable `baseline/decisions/`, and `baseline/03-tech-stack-decision.md` exist.
5. The user has confirmed scope, data environment, priority, and verification commands, or these decisions are explicit in the approved upstream artifacts.

## Output Artifacts

| File | Path | Required |
|---|---|---|
| Actual code | `workspace/{backend,frontend,...}/` | ✅ |
| Implementation main record | `iteration/v{N}/04-implementation/v{N}-source-code.md` | ✅ |
| Test results | `iteration/v{N}/04-implementation/v{N}-test-results.md` | ✅ |
| Issue fixes (v1.0 only) | `iteration/v1.0/04-implementation/v1.0-issue-fixes.md` | legacy compatibility |
| Stage navigation | `iteration/v{N}/04-implementation/README.md` | recommended |

## Scope and Environment Resolution

Implementation scope, dependent services, data environment, execution order, and verification commands must come from the approved product requirement, tech-stack decision, TASK DAG, and validation plan. If any of these inputs are missing or contradictory, stop and request a human decision; do not default to a specific project's framework, database, or command.

| Decision point | Source |
|---|---|
| Implementation scope | Approved TASK list and linked AC |
| Data / external services | `baseline/03-tech-stack-decision.md` and design artifacts |
| Priority | TASK DAG dependency graph |
| Verification commands | Approved validation plan and the project's actual scripts |

## Workflow

```text
0. User confirms the four-tuple (implementation scope / DB / priority / verification).
1. Create the `iteration/v{N}/04-implementation/` directory skeleton.
2. Actually write code into `workspace/{sub-project}/`.
3. Write `v{N}-source-code.md` main record (structure per "Artifact 3" in `templates/implementation.md`).
4. Placeholder `v{N}-test-results.md` (fill real data after the first test run).
5. Record known issues in `v{N}-source-code.md` §5; v1.0 also maintains `v1.0-issue-fixes.md` for legacy compatibility.
6. Write `README.md` (how to run tests / start the dev server).
7. Run the static-check or build commands appropriate to the project's language and toolchain.
8. Record the actually executable install, start, and test commands in the README and the delivery message.
9. Keep 04-stage artifacts as `draft` or `In Review`, list every required artifact together with test / verification evidence, and hand off to a human for review. Agents MUST NOT write or change any artifact's `status` to `Approved`; after human approval, run `validate --stage 04-implementation` before entering stage 05.
```

## Context Budget Rules (HARD)

> **Core principle**: load context **per TASK-XXX slice**; **forbid** loading the entire upstream document as a single prompt input.

### Project Context Pack integration

Before starting a task, run from the project root:

```powershell
python .aw/.workflow/workflow.py index --iteration vN
python .aw/.workflow/workflow.py context --iteration vN --task TASK-XXX-NNN
```

Use the generated `.aw/.workflow/context-packs/vN-TASK-XXX-NNN.md` as the task context. The Context Pack is authoritative for the selected excerpts; load a full source artifact only when a required detail is absent and record that exception in the implementation log.

### Task completion report

After each TASK's code and verification work, run:

```powershell
python .aw/.workflow/workflow.py task-finished --iteration vN --task TASK-XXX-NNN --result succeeded
```

Default behaviour (matches the unit test `test_task_finished_records_result_and_refreshes_dashboard`): the call appends one JSON record to `.aw/.workflow/task-runs/` and prints the conclusion. It does **not** re-render the dashboard — that was made explicit default-off to keep repeated `task-finished` calls O(1) instead of O(N_artifacts). When operating from the framework source repository, use the corresponding `.workflow/` paths.

To see the new task on the dashboard afterwards, run **one** of:

```powershell
python .aw/.workflow/workflow.py task-finished ... --refresh-dashboard
# or separately:
python .aw/.workflow/workflow.py dashboard --iteration vN
```

Use `failed` when verification fails and `blocked` when a required decision or dependency prevents completion. Do not report the TASK as complete until the task-run JSON has been written and the printed conclusion has been confirmed.

### Per-Prompt Budget Red Lines

| Item | Red line |
|---|---|
| Input-side tokens | **≤ 16k** (leave 50% for output + tool responses under mainstream 8B-model windows) |
| TASK count per prompt | **= 1** (strictly forbid "TASK-001..005 in one go") |
| Upstream document loading | Whole-document loading is forbidden; load only the section tied to the stable IDs in scope |

### ❌ Forbidden Anti-Patterns

1. Stuffing **any one whole document** of `v{N}-requirement.md` / `architecture-design.md` / `api-spec.md` / `database-dictionary.md` / `task-plan-dag.md` / `validation-plan.md` into a single prompt.
2. Re-reading **every previously-written section** of `v{N}-source-code.md` into the current prompt (even "just in case").
3. Feeding the entire git diff (**>2k lines**) to the reviewer subagent in one shot.
4. Opening multiple non-essential `read_file` / `search_files` calls in parallel (merge independent reads into one batch).

### ✅ Correct Context-Loading Flow (30 Seconds Before Each TASK Starts)

```text
1. Lock onto the single TASK-XXX ID (from v{N}-task-plan-dag.md).
2. Extract that TASK's one-line summary plus its "depends_on" / "AC refs" from task-plan-dag.md.
3. List every stable ID the TASK touches (FS-XXX / API-XXX / TBL-XXX / AC-XXX); for each, use
   search_files + offset / limit to pull just the section that mentions it (not the whole file).
4. List the source files the TASK will modify; read_file only as needed (do not pre-read every related file).
5. For existing test files, grep the relevant symbols on demand.
6. Historical context: session_search the most recent related implementation record first; only load if needed.
```

### Threshold-Breach Handling (Decision Table)

| Signal | Action |
|---|---|
| Tempted to load the whole `source-code.md` | **Switch to** grepping the TASK's section (head + tail, 100 lines each, is enough). |
| Tempted to load the whole `api-spec.md` | **Switch to** grepping the 1–3 endpoint lines the TASK touches. |
| A TASK spans 3+ tables across modules | **Split the TASK** (re-cut granularity in `task-plan-dag.md`). |
| A single TASK truly needs >16k tokens (large module refactor) | **Spawn an isolated sub-session via `delegate_task`**; the main session keeps only the summary. |
| Input-side prompt approaches 16k | **Stop immediately**; split the prompt or split the TASK — do not cram. |

### Plan-and-Execute Alternative Pattern

When a TASK intrinsically needs 30k+ tokens (complex module refactor, large change spanning 3+ files):

1. In the main session, **keep only the plan** (5–10 lines: goal / input slice / acceptance).
2. Spawn an **isolated sub-session** via `delegate_task(goal=..., context=<minimum context>)`.
3. The sub-session returns **patched code + the additional `source-code.md` section entries for that TASK** (not the whole file).
4. The main session **receives a summary** (≤2k tokens) and appends it to `source-code.md`.

This rule overrides any scope preference: if the current TASK would breach the budget, narrow or split the scope first.

### Frontend Vue 3 Multi-Batch Delivery (only when baseline matches)

> Lesson: when the user fills 10+ view pages, writing them all at once makes the prompt context explode, generates hundreds of `vue-tsc` errors that cannot be localized, and the rewrite cost is high. **Force batching + per-batch type-check validation**.

**Mandatory rules**:

1. **2–4 views per batch, 5 maximum.** Split if exceeded.
2. **Each batch must end with `vue-tsc --noEmit`**, looking only at errors introduced by this batch plus errors already corrected by previous batches; filter expected missing pieces with `grep -v "Cannot find module '@/views/"`.
3. **Batch partition principle**:
   - List / CRUD pages (lightweight, independently verifiable) — same batch.
   - Detail pages with business components + timeline + error diagnosis — their own batch.
   - Edge pages (404 / empty state) — last batch.
4. **Cross-batch side-effect fixes**: type re-exports / schema completion corrected in batch A must be consumable by batch B; do not defer "to-fix" items to the end.
5. **Before writing a new component, `read_file` the existing component's prop definition.** Guessing component signatures blindly (especially whether `PipelineStageTimeline` is for Run or Pipeline) hits a type wall.

Before closing the iteration, run type-check, lint, unit tests, and a dev-server smoke test per the approved validation plan and the project's actual scripts; specific commands follow the project's own toolchain.

### Context-Bloat Discipline (applies to any large task)

User-original quote: "When the context gets too large, what can solve it?" → This is a **class-level** workflow problem, not a single complaint.

**5 tool-level levers** (use by priority):

| Priority | Tool | Usage |
|---|---|---|
| 1 | `search_files` / `search_content` | Find the key lines instead of reading whole files; save 80%+ tokens |
| 2 | `read_file offset=N limit=M` | Page through large files (default 200 lines/page), read on demand |
| 3 | `patch` 5–30 lines | Avoid `write_file` full-page overwrites; avoid re-loading the same context |
| 4 | `delegate_task` | Offload exploratory or aggregation sub-tasks to an isolated-context sub-agent; get a summary back |
| 5 | `open_preview` + `read_preview` + vision | View the rendered state in the browser instead of reading static HTML (prototype / UI phases) |

**Absolutely never**:

- Pull 100KB+ in a single `read_file` call.
- Copy long documents into my reply (use grep to extract the relevant lines).
- Stuff "to-fix" lists into the prompt and let it grow longer and longer.

The above constraints apply to every large implementation task; prefer the project's exact-search, partial-read, and small-edit capabilities first.

## Companion Documents Structure

`v{N}-source-code.md` 8-section structure (see "Artifact 3" in `templates/implementation.md`):

1. Delivery scope (per `task-plan-dag` list, each marked ✅ / ⚠️ / ❌).
2. Key design decisions (implementation layer, with ADR references).
3. File manifest (tree form).
4. AC acceptance matrix (tests ↔ AC).
5. Known limits and follow-up work (clearly deferred items + reason).
6. Frontend / other sub-projects (if not implemented, note target version or pending reason).
7. How to run (project's actual install, start, and test commands).
8. Change log.

## Validation Checklist (before reporting done)

- [ ] Ran the static check, build, or type-check appropriate to the current language and project toolchain.
- [ ] `v{N}-source-code.md` has all 8 sections.
- [ ] `v{N}-test-results.md` includes at least the AC matrix (real data may be pending).
- [ ] v1.0's `v1.0-issue-fixes.md` carries the current known leftovers; v1.1+ known issues are recorded in `v{N}-source-code.md` §5.
- [ ] `README.md` contains the project's actual install, start, and test steps.
- [ ] `v{N}-source-code.md` §5 explicitly lists "known limits".
- [ ] The delivery message gives clear follow-up commands, or states there are no follow-up commands.
