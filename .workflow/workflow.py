#!/usr/bin/env python3
"""Deterministic governance, indexing, traceability, and Context Pack tooling."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import html
import io
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".workflow"
STAGES = ["01-product", "02-design", "03-planning", "04-implementation", "05-pull-request", "06-rc-review-release"]
BASELINE_FILES = [
    "baseline/01-product-vision.md",
    "baseline/02-product-charter.md",
    "baseline/03-tech-stack-decision.md",
    "baseline/04-glossary.md",
]
ID_RE = re.compile(r"\b(?:FR|BR|NFR|FS|API|TBL|TASK|AC|ISSUE)(?:-[A-Z0-9]+)+\b")
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|XXX)\b|\[待确认\]|\[未提供\]|占位", re.IGNORECASE)


@dataclass(frozen=True)
class Artifact:
    path: str
    stage: str
    status: str
    ids: tuple[str, ...]
    sha256: str
    lines: int
    frontmatter: bool


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if text.startswith("---\n") or text.startswith("---\r\n"):
        lines = text.splitlines()
        try:
            end = lines.index("---", 1)
        except ValueError:
            return {}, text
        values: dict[str, str] = {}
        for line in lines[1:end]:
            match = re.match(r"^([A-Za-z_][\w-]*):\s*(.*?)\s*$", line)
            if match:
                values[match.group(1)] = match.group(2).strip("'\"")
        return values, "\n".join(lines[end + 1 :])
    # Fallback: HTML comment-style frontmatter for HTML artifacts.
    # Format: <!-- key: value --> on one or more leading lines before any other content.
    # Supported because HTML cannot start with `---` (would break the doctype).
    if text.startswith("<!--"):
        lines = text.splitlines()
        values: dict[str, str] = {}
        consumed = 0
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if not stripped.startswith("<!--"):
                break
            inner = stripped[4:]
            if inner.endswith("-->"):
                inner = inner[:-3]
            inner = inner.strip()
            match = re.match(r"^([A-Za-z_][\w-]*):\s*(.*?)\s*$", inner)
            if match:
                values[match.group(1)] = match.group(2).strip("'\"")
                consumed += 1
            else:
                # not a kv line — stop scanning if we already collected some
                if values:
                    break
                # else: tolerate non-kv comment and keep scanning
                continue
        if values:
            rest_start = consumed
            while rest_start < len(lines) and not lines[rest_start].strip():
                rest_start += 1
            return values, "\n".join(lines[rest_start:])
        return {}, text
    return {}, text


def iteration_number(iteration: str) -> tuple[int, int]:
    """Parse a semantic iteration id like `v1.0`, `v2.3` into (major, minor).

    Plain integers such as `v1` are still accepted for backward compatibility
    and treated as `(N, 0)`. Returns a tuple so callers can compare versions
    by tuple ordering instead of string compares.
    """
    match = re.fullmatch(r"v(\d+)(?:\.(\d+))?", iteration)
    if not match:
        raise ValueError(f"invalid iteration: {iteration}")
    major = int(match.group(1))
    minor = int(match.group(2)) if match.group(2) is not None else 0
    return major, minor


def discover_iteration() -> str:
    versions: list[tuple[int, int]] = []
    directory = ROOT / "iteration"
    if directory.exists():
        for path in directory.iterdir():
            match = re.fullmatch(r"v(\d+)(?:\.(\d+))?", path.name)
            if path.is_dir() and match:
                versions.append((int(match.group(1)), int(match.group(2) or 0)))
    if not versions:
        return "v1.0"
    major, minor = max(versions)
    return f"v{major}.{minor}" if minor is not None and minor >= 0 else f"v{major}"


def artifact_paths(iteration: str) -> Iterable[tuple[str, str]]:
    for relative in BASELINE_FILES:
        yield relative, "00-baseline"
    base = ROOT / "iteration" / iteration
    if not base.exists():
        return
    for stage in STAGES:
        directory = base / stage
        if directory.exists():
            for path in sorted(directory.rglob("*")):
                if path.is_file() and path.suffix.lower() in {".md", ".html", ".json"}:
                    yield path.relative_to(ROOT).as_posix(), stage


def load_artifacts(iteration: str) -> list[Artifact]:
    result = []
    for relative, stage in artifact_paths(iteration):
        path = ROOT / relative
        if not path.exists():
            # Bootstrap / non-existent files report as 'missing' rather
            # than raising — so fresh projects can run `validate` and
            # see a structured error list instead of a stack trace.
            result.append(
                Artifact(
                    path=relative,
                    stage=stage,
                    status="missing",
                    ids=(),
                    sha256="",
                    lines=0,
                    frontmatter=False,
                )
            )
            continue
        text = path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(text)
        result.append(
            Artifact(
                path=relative,
                stage=stage,
                status=frontmatter.get("status", "unknown"),
                ids=tuple(sorted({identifier for identifier in ID_RE.findall(text) if is_real_id(identifier)})),
                sha256=sha256(path),
                lines=len(text.splitlines()),
                frontmatter=bool(frontmatter),
            )
        )
    return result


def is_real_id(identifier: str) -> bool:
    return not any(part in {"XXX", "NNN"} for part in identifier.split("-"))


def required_inputs(iteration: str, stage: str) -> list[str]:
    iteration_number(iteration)  # validates iteration format; result unused.
    if stage == "01-product":
        return BASELINE_FILES
    if stage == "02-design":
        return [
            f"iteration/{iteration}/01-product/{iteration}-requirement.md",
            f"iteration/{iteration}/01-product/{iteration}-feature-specification.md",
            f"iteration/{iteration}/01-product/{iteration}-prototype.html",
        ]
    if stage == "03-planning":
        return [
            f"iteration/{iteration}/02-design/{iteration}-architecture-design.md",
            f"iteration/{iteration}/02-design/{iteration}-api-spec.md",
            f"iteration/{iteration}/02-design/{iteration}-database-dictionary.md",
        ]
    if stage == "04-implementation":
        return [
            f"iteration/{iteration}/03-planning/{iteration}-task-plan-dag.md",
            f"iteration/{iteration}/03-planning/{iteration}-validation-plan.md",
        ]
    if stage == "05-pull-request":
        return [f"iteration/{iteration}/04-implementation"]
    if stage == "06-rc-review-release":
        return [f"iteration/{iteration}/05-pull-request"]
    raise ValueError(f"unknown stage: {stage}; iteration={n}")


def path_artifact(artifacts: list[Artifact], relative: str) -> Artifact | None:
    return next((item for item in artifacts if item.path == relative), None)


def check_readme_freshness(iteration: str, errors: list[str]) -> None:
    """RC sign-off requires README.md to reference the current state.

    Triggered only on stage 06-rc-review-release. Reports three classes of
    staleness: missing README, missing current-iteration mention, and
    missing current skill / script mention. Does not modify files.

    All three classes are checked independently so callers get a
    complete picture even when README is absent.
    """
    readme = ROOT / "README.md"
    if not readme.exists():
        errors.append("README.md missing; required for RC sign-off")
        # Continue checking skills / scripts against an empty string so
        # callers see every missing reference, not just the first.
        text = ""
    else:
        text = readme.read_text(encoding="utf-8")
    # 1) README must mention the current iteration (e.g. "v1.0")
    if iteration not in text:
        errors.append(
            f"README.md does not mention iteration '{iteration}'; "
            f"may be out of date"
        )
    # 2) README must mention all current skills
    skills_dir = ROOT / ".agents" / "skills"
    if skills_dir.exists():
        current_skills = {p.name for p in skills_dir.iterdir() if p.is_dir()}
        missing = sorted(s for s in current_skills if s not in text)
        if missing:
            errors.append(
                f"README.md does not mention {len(missing)} current skill(s): "
                f"{', '.join(missing)}"
            )
    # 3) README must mention all current scripts
    scripts_dir = ROOT / ".workflow" / "scripts"
    if scripts_dir.exists():
        current_scripts = {p.stem for p in scripts_dir.glob("*.py")}
        missing = sorted(s for s in current_scripts if s not in text)
        if missing:
            errors.append(
                f"README.md does not mention {len(missing)} current script(s): "
                f"{', '.join(missing)}"
            )


def validate(iteration: str, stage: str | None) -> int:
    artifacts = load_artifacts(iteration)
    by_path = {item.path: item for item in artifacts}
    errors: list[str] = []
    warnings: list[str] = []

    for relative in BASELINE_FILES:
        item = by_path.get(relative)
        if not item:
            errors.append(f"missing baseline artifact: {relative}")
        elif item.status != "Approved":
            errors.append(f"baseline is not Approved: {relative} ({item.status})")

    target = stage or "all"
    stages = [stage] if stage else STAGES
    checked_paths: set[str] = set(BASELINE_FILES)
    for current in stages:
        for required in required_inputs(iteration, current):
            if required.endswith("-implementation") or required.endswith("-pull-request"):
                directory = ROOT / required
                if not directory.exists() or not any(directory.iterdir()):
                    errors.append(f"required stage output is missing: {required}")
                continue
            item = by_path.get(required)
            if not item:
                errors.append(f"missing input for {current}: {required}")
            elif item.status != "Approved":
                if required not in checked_paths:
                    errors.append(f"input for {current} is not Approved: {required} ({item.status})")
            checked_paths.add(required)

    for item in artifacts:
        if item.path.startswith("templates/"):
            continue
        if item.status == "missing":
            # Already flagged as a missing-input error above; skip the
            # placeholder / frontmatter scans which would otherwise raise
            # FileNotFoundError on the (non-existent) read.
            continue
        text = (ROOT / item.path).read_text(encoding="utf-8")
        if item.stage != "00-baseline" and item.frontmatter is False and item.path.endswith(".html"):
            warnings.append(f"artifact has no frontmatter status: {item.path}")
        if PLACEHOLDER_RE.search(text) and item.status == "Approved":
            errors.append(f"Approved artifact contains unresolved placeholder: {item.path}")

    # D3: RC sign-off freshness check (only at the final stage)
    if "06-rc-review-release" in stages:
        check_readme_freshness(iteration, errors)

    print(f"workflow validate: iteration={iteration}, target={target}")
    for warning in warnings:
        print(f"WARNING {warning}")
    for error in errors:
        print(f"ERROR {error}")
    print(f"result: {'PASS' if not errors else 'BLOCKED'} ({len(errors)} errors, {len(warnings)} warnings)")
    return 0 if not errors else 1


def sections(text: str) -> list[tuple[str, str, int]]:
    lines = text.splitlines()
    headings = [(index, line) for index, line in enumerate(lines) if re.match(r"^#{1,6}\s+", line)]
    output = []
    for position, (start, heading) in enumerate(headings):
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        output.append((heading.strip(), "\n".join(lines[start:end]).strip(), start + 1))
    return output


def traceability(iteration: str, artifacts: list[Artifact]) -> dict:
    nodes: dict[str, dict] = {}
    edges: dict[tuple[str, str], dict] = {}
    for item in artifacts:
        if not item.path.startswith(f"iteration/{iteration}/"):
            continue
        text = (ROOT / item.path).read_text(encoding="utf-8")
        for identifier in item.ids:
            nodes.setdefault(identifier, {"id": identifier, "artifacts": []})["artifacts"].append(item.path)
        current_heading = "(document)"
        for line_number, line_text in enumerate(text.splitlines(), start=1):
            if re.match(r"^#{1,6}\s+", line_text):
                current_heading = line_text.strip()
            ids = sorted({identifier for identifier in ID_RE.findall(line_text) if is_real_id(identifier)})
            primary = [identifier for identifier in ids if identifier.split("-")[0] in primary_prefixes(item.path)]
            secondary = [identifier for identifier in ids if identifier not in primary]
            for left in primary:
                for right in secondary:
                    key = (left, right)
                    edge = edges.setdefault(key, {"from": left, "to": right, "evidence": []})
                    evidence = {"path": item.path, "line": line_number, "section": current_heading}
                    if evidence not in edge["evidence"]:
                        edge["evidence"].append(evidence)
    return {
        "schema_version": "1",
        "generated_at": now(),
        "iteration": iteration,
        "nodes": sorted(nodes.values(), key=lambda value: value["id"]),
        "edges": sorted(edges.values(), key=lambda value: (value["from"], value["to"])),
    }


def primary_prefixes(path: str) -> set[str]:
    if "requirement" in path:
        return {"FR", "BR", "NFR", "AC"}
    if "feature-specification" in path:
        return {"FS"}
    if "api-spec" in path:
        return {"API"}
    if "database-dictionary" in path:
        return {"TBL"}
    if "task-plan" in path:
        return {"TASK"}
    if "validation-plan" in path:
        return {"TASK", "AC"}
    if "implementation" in path:
        return {"TASK", "ISSUE"}
    return set()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_manifest(iteration: str, artifacts: list[Artifact]) -> None:
    lines = [
        "schema_version: '1'",
        f"generated_at: '{now()}'",
        f"iteration: '{iteration}'",
        "stages:",
    ]
    for stage in ["00-baseline", *STAGES]:
        stage_items = [item for item in artifacts if item.stage == stage]
        lines.append(f"  {stage}:")
        if not stage_items:
            lines.append("    artifacts: []")
        else:
            lines.append("    artifacts:")
            for item in stage_items:
                lines.extend([
                    f"      - path: '{item.path}'",
                    f"        status: '{item.status}'",
                    f"        sha256: '{item.sha256}'",
                    f"        lines: {item.lines}",
                    f"        frontmatter: {str(item.frontmatter).lower()}",
                ])
    WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
    (WORKFLOW_DIR / "manifest.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def index(iteration: str) -> int:
    artifacts = load_artifacts(iteration)
    write_manifest(iteration, artifacts)
    write_json(WORKFLOW_DIR / "traceability.json", traceability(iteration, artifacts))
    cache = {"schema_version": "1", "generated_at": now(), "iteration": iteration, "files": {item.path: item.sha256 for item in artifacts}}
    write_json(WORKFLOW_DIR / "cache" / "index.json", cache)
    print(f"workflow index: {len(artifacts)} artifacts indexed for {iteration}")
    print(f"manifest: {(WORKFLOW_DIR / 'manifest.yaml').relative_to(ROOT)}")
    print(f"traceability: {(WORKFLOW_DIR / 'traceability.json').relative_to(ROOT)}")
    print(f"cache entries: {len(artifacts)}")
    return 0


def find_task(iteration: str, task_id: str, artifacts: list[Artifact]) -> tuple[str, str, int]:
    plan_path = ROOT / "iteration" / iteration / "03-planning" / f"{iteration}-task-plan-dag.md"
    if not plan_path.exists():
        raise ValueError(f"task plan not found: {plan_path.relative_to(ROOT)}")
    text = plan_path.read_text(encoding="utf-8")
    parsed = sections(text)
    matches = [section for section in parsed if task_id in section[0]]
    if not matches:
        matches = [section for section in parsed if task_id in section[1]]
    if not matches:
        raise ValueError(f"task not found: {task_id}")
    return matches[0][1], plan_path.relative_to(ROOT).as_posix(), matches[0][2]


def context_pack(iteration: str, task_id: str) -> int:
    artifacts = load_artifacts(iteration)
    task_text, task_path, task_line = find_task(iteration, task_id, artifacts)
    identifiers = sorted(set(ID_RE.findall(task_text)))
    selected: list[tuple[str, str, int]] = []
    for item in artifacts:
        if item.stage in {"00-baseline", "05-pull-request", "06-rc-review-release"}:
            continue
        text = (ROOT / item.path).read_text(encoding="utf-8")
        for heading, content, line in sections(text):
            if any(identifier in content for identifier in identifiers):
                selected.append((item.path, content, line))
    source_hashes = {item.path: item.sha256 for item in artifacts if item.path in {path for path, _, _ in selected} or item.path == task_path}
    key_material = json.dumps({"iteration": iteration, "task": task_id, "identifiers": identifiers, "source_hashes": source_hashes}, sort_keys=True)
    cache_key = hashlib.sha256(key_material.encode("utf-8")).hexdigest()
    output = WORKFLOW_DIR / "context-packs" / f"{iteration}-{task_id}.md"
    cache_path = WORKFLOW_DIR / "cache" / "context-packs.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    if output.exists() and cache.get(str(output.relative_to(ROOT))) == cache_key:
        print(f"context cache hit: {output.relative_to(ROOT)}")
        return 0
    lines = [
        f"# Context Pack: {task_id}",
        "",
        f"- iteration: `{iteration}`",
        f"- generated_at: `{now()}`",
        f"- task_source: `{task_path}:{task_line}`",
        f"- context_key: `{cache_key}`",
        "",
        "## Task Definition",
        "",
        task_text,
        "",
        "## Related Stable IDs",
        "",
        ", ".join(f"`{identifier}`" for identifier in identifiers) or "None found",
        "",
        "## Relevant Contract Excerpts",
        "",
    ]
    for path, content, line in selected:
        lines.extend([f"### `{path}:{line}`", "", content, ""])
    lines.extend(["## Loading Rules", "", "This pack is task-scoped. Load the full upstream artifact only when a required detail is absent here.", ""])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache[str(output.relative_to(ROOT))] = cache_key
    write_json(cache_path, cache)
    print(f"context pack written: {output.relative_to(ROOT)}")
    print(f"selected excerpts: {len(selected)}, identifiers: {len(identifiers)}")
    return 0


def task_records(iteration: str) -> list[dict]:
    directory = WORKFLOW_DIR / "task-runs"
    records = []
    if not directory.exists():
        return records
    for path in sorted(directory.glob(f"{iteration}-*.json"), reverse=True):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        records.append(record)
    return records


def gate_code(iteration: str) -> int:
    # Capture diagnostics so dashboard generation remains a data-producing operation.
    with contextlib.redirect_stdout(io.StringIO()):
        return validate(iteration, None)


def dashboard_data(iteration: str) -> dict:
    artifacts = load_artifacts(iteration)
    records = task_records(iteration)
    by_stage: dict[str, list[dict]] = {stage: [] for stage in ["00-baseline", *STAGES]}
    for item in artifacts:
        by_stage[item.stage].append({"path": item.path, "status": item.status, "lines": item.lines, "sha256": item.sha256})
    stages = []
    overall_gate = gate_code(iteration)
    for stage, items in by_stage.items():
        if not items:
            status = "empty"
        elif stage == "00-baseline" and all(item["status"] == "Approved" for item in items):
            status = "approved" if overall_gate == 0 else "blocked"
        elif stage != "00-baseline" and all(item["status"] == "Approved" for item in items):
            status = "approved"
        else:
            status = "in_progress"
        stages.append({"name": stage, "status": status, "artifact_count": len(items), "artifacts": items})
    return {
        "schema_version": "1",
        "iteration": iteration,
        "generated_at": now(),
        "gate_status": "passed" if overall_gate == 0 else "blocked",
        "stages": stages,
        "tasks": records,
        "traceability_path": ".workflow/traceability.json",
        "manifest_path": ".workflow/manifest.yaml",
    }


def dashboard(iteration: str) -> int:
    template_path = WORKFLOW_DIR / "dashboard" / "template.html"
    if not template_path.exists():
        raise ValueError(f"dashboard template not found: {template_path.relative_to(ROOT)}")
    data = dashboard_data(iteration)
    serialized = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    fallback = static_dashboard_fallback(data)
    page = template_path.read_text(encoding="utf-8").replace("__DASHBOARD_DATA__", serialized).replace("__DASHBOARD_FALLBACK__", fallback)
    output = WORKFLOW_DIR / "dashboard" / "index.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding="utf-8")
    print(f"dashboard written: {output.relative_to(ROOT)}")
    print(f"gate: {data['gate_status']}, tasks: {len(data['tasks'])}")
    return 0


def static_dashboard_fallback(data: dict) -> str:
    stages = "".join(
        f'<article class="card stage"><div class="stage-head"><strong>{html.escape(stage["name"])}</strong>'
        f'<span class="badge {html.escape(stage["status"])}">{html.escape(stage["status"])}</span></div>'
        f'<p class="muted">{stage["artifact_count"]} 个产物</p></article>'
        for stage in data["stages"]
    )
    tasks = "".join(
        f'<div class="task-row"><code>{html.escape(task.get("task_id", ""))}</code>'
        f'<span class="badge {html.escape(task.get("result", ""))}">{html.escape(task.get("result", ""))}</span></div>'
        for task in data["tasks"]
    ) or '<p class="muted">暂无任务执行记录</p>'
    return (
        '<div data-dashboard-fallback><section class="summary"><header><div><h1>Software Workshop 项目执行视图</h1>'
        f'<p class="muted">迭代 {html.escape(data["iteration"])} · 更新时间 {html.escape(data["generated_at"])}</p>'
        f'</div><span class="badge {html.escape(data["gate_status"])}">门禁：{html.escape(data["gate_status"])}</span></header>'
        f'<div class="summary-grid"><section class="summary-item"><h2>最近任务结论</h2>{tasks}</section>'
        f'<section class="summary-item"><h2>数据来源</h2><p class="muted"><code>.workflow/manifest.yaml</code></p><p class="muted"><code>.workflow/traceability.json</code></p></section>'
        f'<section class="summary-item"><h2>使用方式</h2><p class="muted">任务完成后运行 <code>task-finished</code> 刷新本视图，并提交任务结论。</p></section></div></section>'
        f'<section class="stage-list">{stages}</section></div>'
    )


def task_finished(iteration: str, task_id: str, result: str, *, refresh_index: bool = False, refresh_dashboard: bool = False) -> int:
    """Record a TASK outcome and print a short conclusion.

    By default this is a cheap append-only operation: it does NOT re-index
    artifacts or re-render the dashboard. Pass `refresh_index=True` to also
    re-run `index` (e.g. when artifact frontmatter / content changed in the
    same task), and `refresh_dashboard=True` to also re-render the static
    dashboard. The two flags default to False because most task finishes do
    not change artifact state — the previous behaviour of doing both on every
    finish made `task-finished` O(N_artifacts) per call.
    """
    if result not in {"succeeded", "failed", "blocked"}:
        raise ValueError("result must be succeeded, failed, or blocked")
    if refresh_index:
        artifacts = load_artifacts(iteration)
        find_task(iteration, task_id, artifacts)
        index(iteration)
    record = {
        "iteration": iteration,
        "task_id": task_id,
        "result": result,
        "recorded_at": now(),
        "context_pack": f".workflow/context-packs/{iteration}-{task_id}.md",
        "context_pack_present": (WORKFLOW_DIR / "context-packs" / f"{iteration}-{task_id}.md").exists(),
        "gate_status": "passed" if gate_code(iteration) == 0 else "blocked",
    }
    path = WORKFLOW_DIR / "task-runs" / f"{iteration}-{task_id}.json"
    write_json(path, record)
    if refresh_dashboard:
        dashboard(iteration)
    print(f"task conclusion: {task_id}={result}; gate={record['gate_status']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("index", "validate"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--iteration", default=discover_iteration())
        if name == "validate":
            sub.add_argument("--stage", choices=STAGES)
    context = subparsers.add_parser("context")
    context.add_argument("--iteration", default=discover_iteration())
    context.add_argument("--task", required=True)
    dashboard_parser = subparsers.add_parser("dashboard")
    dashboard_parser.add_argument("--iteration", default=discover_iteration())
    finished = subparsers.add_parser("task-finished")
    finished.add_argument("--iteration", default=discover_iteration())
    finished.add_argument("--task", required=True)
    finished.add_argument("--result", choices=["succeeded", "failed", "blocked"], required=True)
    finished.add_argument("--refresh-index", action="store_true", help="Also re-run `index` after writing the task record. Off by default; only enable when the task changed artifact state.")
    finished.add_argument("--refresh-dashboard", action="store_true", help="Also re-render the static dashboard after writing the task record. Off by default; run `python .workflow/workflow.py dashboard` separately when needed.")
    args = parser.parse_args(argv)
    try:
        if args.command == "index":
            return index(args.iteration)
        if args.command == "validate":
            return validate(args.iteration, args.stage)
        if args.command == "context":
            return context_pack(args.iteration, args.task)
        if args.command == "dashboard":
            return dashboard(args.iteration)
        return task_finished(args.iteration, args.task, args.result, refresh_index=args.refresh_index, refresh_dashboard=args.refresh_dashboard)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
