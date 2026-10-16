# Framework Repository Version and CI Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Manage the AlchemyWorks framework version in `pyproject.toml` and use repository-level CI to validate commits and publish framework release tags without changing instance-project version management.

**Architecture:** `pyproject.toml` is the framework's single version source. The workflow CLI only reads that value for display and synchronization provenance; it does not calculate or advance versions. GitHub Actions runs tests on changes and uses release automation to prepare a release PR, update the version, create `vMAJOR.MINOR.PATCH`, and publish the framework release.

**Tech Stack:** Python standard library, `unittest`, `pyproject.toml`, GitHub Actions, Conventional Commits.

**Spec:** User-approved repository-level version and CI approach from the conversation on 2026-10-16.

## Global Constraints

- Framework version source: `pyproject.toml` under `[project].version`.
- Framework release tags: `vMAJOR.MINOR.PATCH`.
- `fix` maps to PATCH, `feat` maps to MINOR, and `!` or `BREAKING CHANGE` maps to MAJOR.
- The workflow CLI must not manage or advance instance `iteration/v{major}.{minor}` versions.
- `.aw/workflow-version.yaml` remains synchronization provenance only.
- CI has read-only contents permission; release automation has write permission only in the release workflow.

## Tasks

### Task 1: Add framework metadata and read-only integration

**Files:** `pyproject.toml`, `.workflow/workflow.py`, `.workflow/tests/test_workflow.py`

- [x] Add the framework project metadata and initial version `0.1.0`.
- [x] Make the workflow CLI read the source repository version and fall back to instance synchronization metadata without managing versions.
- [x] Add a regression test that the CLI version matches `pyproject.toml`.

### Task 2: Add repository CI and release automation

**Files:** `.github/workflows/ci.yml`, `.github/workflows/release.yml`

- [x] Add read-only CI for version validation and the workflow regression suite.
- [x] Add release automation triggered by pushes to `main`, using Conventional Commits and a release PR before Tag publication.
- [x] Configure repository permissions and concurrency to prevent overlapping releases.

### Task 3: Document boundaries and verify

**Files:** `AGENTS.md`, `README.md`, `.workflow/README.md`, `.workflow/workflow-file-inventory.md`

- [x] Document that framework releases and instance iterations are separate systems.
- [x] Register repository-only metadata and CI in the workflow inventory.
- [ ] Run the full regression suite, syntax/configuration checks, and `verify-workflow` after committing the maintenance change.

