#!/usr/bin/env python3
"""Deterministic governance, indexing, traceability, and Context Pack tooling."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import html
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tarfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


_WORKFLOW_SOURCE_FILE = Path(__file__).resolve()
if (
    _WORKFLOW_SOURCE_FILE.parent.name == ".workflow"
    and _WORKFLOW_SOURCE_FILE.parent.parent.name == ".aw"
):
    # The synchronized instance layout is `.aw/.workflow/workflow.py`.
    FRAMEWORK_ROOT = _WORKFLOW_SOURCE_FILE.parents[2]
    FRAMEWORK_WORKFLOW_DIR = FRAMEWORK_ROOT / ".aw" / ".workflow"
else:
    # The framework repository keeps its source layout at the repository root.
    FRAMEWORK_ROOT = _WORKFLOW_SOURCE_FILE.parents[1]
    FRAMEWORK_WORKFLOW_DIR = FRAMEWORK_ROOT / ".workflow"
ROOT = FRAMEWORK_ROOT
WORKFLOW_DIR = FRAMEWORK_WORKFLOW_DIR
BASELINE_STAGE = "00-baseline"
STAGES = [
    "01-product",
    "02-design",
    "03-planning",
    "04-implementation",
    "05-review-release",
]
# Canonical display order used by `write_manifest`, `dashboard_data`, and
# `stage_status`. Use this instead of repeating ["00-baseline", *STAGES].
ALL_STAGES = (BASELINE_STAGE, *STAGES)
GATE_STAGES = ALL_STAGES
# Stages whose artifacts are NEVER used as context sources by
# `context_pack()`. Baseline is config (not task input); review/release is
# post-execution summaries produced only after tasks are finished.
CONTEXT_PACK_EXCLUDED_STAGES = frozenset(
    {BASELINE_STAGE, "05-review-release"}
)
BASELINE_FILES = [
    "baseline/01-product-vision.md",
    "baseline/02-product-charter.md",
    "baseline/03-tech-stack-decision.md",
    "baseline/04-glossary.md",
    "baseline/05-core-user-flow-prototype.html",
]
WORKFLOW_SYNC_ITEMS = (
    ("AGENTS.md", ".aw/AGENTS.md"),
    ("README.md", ".aw/README.md"),
    (".workflow/README.md", ".aw/.workflow/README.md"),
    (".workflow/workflow.py", ".aw/.workflow/workflow.py"),
    (".workflow/workflow-file-inventory.md", ".aw/.workflow/workflow-file-inventory.md"),
    (".workflow/dashboard/template.html", ".aw/.workflow/dashboard/template.html"),
    (".workflow/scripts/stage_status.py", ".aw/.workflow/scripts/stage_status.py"),
    (".workflow/scripts/id_registry.py", ".aw/.workflow/scripts/id_registry.py"),
    (".workflow/scripts/query_id.py", ".aw/.workflow/scripts/query_id.py"),
    (".workflow/scripts/check_links.py", ".aw/.workflow/scripts/check_links.py"),
    (".workflow/scripts/diff_versions.py", ".aw/.workflow/scripts/diff_versions.py"),
    ("templates", "templates"),
    (".agents/skills/stage-gate", ".aw/.agents/skills/stage-gate"),
    (".agents/skills/normalize-requirement", ".aw/.agents/skills/normalize-requirement"),
    (".agents/skills/manage-iteration", ".aw/.agents/skills/manage-iteration"),
    (".agents/skills/prototype-design-system", ".aw/.agents/skills/prototype-design-system"),
    (".agents/skills/design-specification", ".aw/.agents/skills/design-specification"),
    (".agents/skills/planning-validation", ".aw/.agents/skills/planning-validation"),
    (".agents/skills/iterate-implementation", ".aw/.agents/skills/iterate-implementation"),
    (".agents/skills/review-release", ".aw/.agents/skills/review-release"),
    (".agents/skills/workflow-governance", ".aw/.agents/skills/workflow-governance"),
)
WORKFLOW_IGNORE_START = "# BEGIN ALCHEMYWORKS WORKFLOW (managed)"
WORKFLOW_IGNORE_END = "# END ALCHEMYWORKS WORKFLOW (managed)"
WORKFLOW_IGNORE_LINES = (
    WORKFLOW_IGNORE_START,
    ".aw/",
    WORKFLOW_IGNORE_END,
)
# These are workflow definitions and governance controls, not product
# artifacts. Product-stage CLI commands refuse to run while any of them has
# uncommitted changes, so a product task cannot silently alter its own gates.
SOURCE_WORKFLOW_PROTECTED_PATHS = (
    "AGENTS.md",
    "README.md",
    ".gitignore",
    ".workflow/workflow.py",
    ".workflow/README.md",
    ".workflow/workflow-file-inventory.md",
    ".workflow/dashboard/template.html",
    ".workflow/scripts/",
    ".workflow/tests/",
    ".agents/skills/",
    "templates/",
)
INSTANCE_WORKFLOW_PROTECTED_PATHS = (
    ".aw/AGENTS.md",
    ".aw/README.md",
    ".aw/.workflow/",
    ".aw/.agents/skills/",
)
ID_RE = re.compile(r"\b(?:FR|BR|NFR|FS|API|TBL|TASK|AC|ISSUE)(?:-[A-Z0-9]+)+\b")
TASK_ID_RE = re.compile(r"^TASK(?:-[A-Z0-9]+)+$")
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|XXX)\b|\[待确认\]|\[未提供\]|占位", re.IGNORECASE)
MANIFEST_ITERATION_RE = re.compile(
    r"^iteration:\s*['\"]?(v\d+(?:\.\d+)?)['\"]?\s*$", re.MULTILINE
)


def _is_workflow_protected_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    protected_paths = workflow_protected_paths()
    return any(
        normalized == protected.rstrip("/")
        or normalized.startswith(protected)
        for protected in protected_paths
    )


def workflow_protected_paths() -> tuple[str, ...]:
    """Return protected paths for the active source or synchronized layout."""
    if (FRAMEWORK_ROOT / ".aw" / ".workflow").exists():
        return INSTANCE_WORKFLOW_PROTECTED_PATHS
    return SOURCE_WORKFLOW_PROTECTED_PATHS


def configure_project_root(project_root: str | Path | None = None) -> Path:
    """Select the instance project whose documents and state are processed.

    The framework source tree remains the default when the CLI is copied into
    an instance project. An external framework invocation must pass
    ``--project-root`` so generated state is written to the instance instead
    of the framework source tree.
    """
    global ROOT, WORKFLOW_DIR
    selected = FRAMEWORK_ROOT if project_root is None else Path(project_root).expanduser()
    selected = selected.resolve()
    if not selected.is_dir():
        raise ValueError(f"project root does not exist or is not a directory: {selected}")
    ROOT = selected
    WORKFLOW_DIR = framework_workflow_dir(ROOT)
    return ROOT


def framework_workflow_dir(root: Path) -> Path:
    """Return the workflow source/runtime directory for a project root."""
    synchronized = root / ".aw" / ".workflow"
    if root != FRAMEWORK_ROOT or synchronized.exists():
        return synchronized
    return root / ".workflow"


def framework_skills_dir() -> Path:
    """Return the Skills directory for either source or synchronized layout."""
    if (FRAMEWORK_ROOT / ".aw" / ".agents" / "skills").exists():
        return FRAMEWORK_ROOT / ".aw" / ".agents" / "skills"
    return FRAMEWORK_ROOT / ".agents" / "skills"


def project_state_dir() -> Path:
    """Return the Git-managed workflow state directory for the instance."""
    return ROOT / "workspace" / "workflow"


def workflow_changed_paths() -> list[str]:
    """Return modified or untracked workflow-definition paths in this Git tree."""
    try:
        result = subprocess.run(
            ["git", "-C", str(FRAMEWORK_ROOT), "status", "--porcelain=v1", "--untracked-files=all"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    changed: set[str] = set()
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:  # rename status; protect the destination path
            path = path.rsplit(" -> ", 1)[1]
        path = path.replace("\\", "/")
        if _is_workflow_protected_path(path):
            changed.add(path)
    return sorted(changed)


def workflow_protection_errors() -> list[str]:
    """Return blockers when workflow definitions are dirty during product work."""
    changed = workflow_changed_paths()
    if not changed:
        return []
    return [
        "workflow core files have uncommitted changes; product workflow commands are blocked: "
        + ", ".join(changed)
        + ". Complete and commit a dedicated workflow-maintenance change first."
    ]


def _workflow_ref_commit(workflow_version: str | None = None) -> str:
    ref = workflow_version or "HEAD"
    result = subprocess.run(
        ["git", "-C", str(FRAMEWORK_ROOT), "rev-parse", f"{ref}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    commit = result.stdout.strip()
    if result.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError(f"could not resolve workflow version: {ref}")
    return commit


@contextlib.contextmanager
def _workflow_source_snapshot(workflow_version: str | None = None):
    """Yield the source root and commit for the requested framework ref."""
    if not workflow_version:
        yield FRAMEWORK_ROOT, _workflow_ref_commit()
        return
    commit = _workflow_ref_commit(workflow_version)
    with tempfile.TemporaryDirectory(prefix="alchemyworks-workflow-") as temp:
        result = subprocess.run(
            ["git", "-C", str(FRAMEWORK_ROOT), "archive", "--format=tar", workflow_version],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            message = result.stderr.decode(errors="replace").strip()
            raise ValueError(f"could not export workflow version {workflow_version}: {message}")
        with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:") as archive:
            archive.extractall(temp)
        yield Path(temp), commit


def _git_status_paths(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"could not read Git status: {root}")
    paths: set[str] = set()
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.rsplit(" -> ", 1)[1]
        paths.add(path.replace("\\", "/"))
    return sorted(paths)


def _ensure_workflow_ignore_block(target: Path, *, dry_run: bool = False) -> None:
    path = target / ".gitignore"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    suffix = "\n".join(WORKFLOW_IGNORE_LINES) + "\n"
    if WORKFLOW_IGNORE_START in existing:
        start = existing.index(WORKFLOW_IGNORE_START)
        end_marker = existing.find(WORKFLOW_IGNORE_END, start)
        if end_marker >= 0:
            end = end_marker + len(WORKFLOW_IGNORE_END)
            prefix = existing[:start].rstrip("\r\n")
            content = (prefix + "\n" if prefix else "") + suffix + existing[end:].lstrip("\r\n")
        else:
            content = existing[:start].rstrip("\r\n") + "\n" + suffix
    else:
        content = suffix if not existing else existing.rstrip("\r\n") + "\n" + suffix
    if content == existing:
        return
    if dry_run:
        print(f"would update: {path}")
    else:
        path.write_text(content, encoding="utf-8")


def _write_workflow_version(target: Path, *, source_ref: str, source_commit: str, dry_run: bool = False) -> None:
    path = target / ".aw" / "workflow-version.yaml"
    content = (
        "schema_version: 1\n"
        "framework: AlchemyWorks\n"
        f"source_ref: {source_ref}\n"
        f"source_commit: {source_commit}\n"
    )
    if dry_run:
        print(f"would update: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def sync_workflow(
    target_root: str | Path,
    *,
    allow_dirty: bool = False,
    dry_run: bool = False,
    workflow_version: str | None = None,
) -> int:
    """Synchronize workflow definitions into an existing instance Git tree."""
    target = Path(target_root).expanduser().resolve()
    source = FRAMEWORK_ROOT.resolve()
    if source == target:
        raise ValueError("the workflow source and target must be different directories")
    if not target.is_dir():
        raise ValueError(f"target directory does not exist: {target}")
    if not (target / ".git").exists():
        raise ValueError(f"target is not a Git working tree: {target}")

    if not allow_dirty:
        changed = _git_status_paths(target)
        overlaps = []
        for changed_path in changed:
            for _, target_relative in WORKFLOW_SYNC_ITEMS:
                if target_relative == "templates":
                    continue
                normalized = target_relative.rstrip("/")
                if changed_path == normalized or changed_path.startswith(normalized + "/"):
                    overlaps.append(changed_path)
                    break
        if overlaps:
            joined = ", ".join(sorted(set(overlaps)))
            raise ValueError(
                "target has uncommitted changes that overlap synchronized workflow paths: "
                f"{joined}. Commit or stash them first, or use --allow-dirty."
            )

    _ensure_workflow_ignore_block(target, dry_run=dry_run)
    with _workflow_source_snapshot(workflow_version) as snapshot:
        source, source_commit = snapshot
        for source_relative, target_relative in WORKFLOW_SYNC_ITEMS:
            source_item = source / source_relative
            target_item = target / target_relative
            if not source_item.exists():
                raise ValueError(f"workflow source item is missing: {source_item}")
            if dry_run:
                print(f"would copy: {source_relative} -> {target_relative}")
                continue
            if source_item.is_dir() and target_relative == "templates":
                for child in source_item.rglob("*"):
                    relative = child.relative_to(source_item)
                    destination = target_item / relative
                    if child.is_dir():
                        destination.mkdir(parents=True, exist_ok=True)
                    elif not destination.exists():
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(child, destination)
            elif source_item.is_dir():
                shutil.copytree(source_item, target_item, dirs_exist_ok=True)
            else:
                target_item.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_item, target_item)
        _write_workflow_version(
            target,
            source_ref=workflow_version or "HEAD",
            source_commit=source_commit,
            dry_run=dry_run,
        )
    print(f"workflow synchronized: {source} -> {target}")
    return 0


def init_instance(
    instance_name: str | None,
    directory: str | Path,
    *,
    dry_run: bool = False,
    workflow_version: str | None = None,
) -> int:
    """Create a named instance and pin it to the current workflow commit."""
    target = Path(directory).expanduser().resolve()
    resolved_name = instance_name if instance_name is not None else target.name
    if not resolved_name.strip() or "\n" in resolved_name or "\r" in resolved_name:
        raise ValueError("instance name must be non-empty and single-line")
    if target.exists() and any(target.iterdir()):
        raise ValueError(f"target directory must be missing or empty: {target}")
    commit = _workflow_ref_commit(workflow_version)
    if dry_run:
        print(f"would initialize instance: {resolved_name}")
        print(f"would create target: {target}")
        print(f"would pin workflow commit: {commit}")
        print("would create: baseline/, iteration/, workspace/, README.md, AGENTS.md, templates/")
        print("would synchronize workflow definitions")
        return 0

    target.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(["git", "-C", str(target), "init", "--quiet"], check=False)
    if result.returncode != 0:
        raise ValueError(f"could not initialize Git repository: {target}")
    for relative in ("baseline/raw-requirement", "iteration/raw-requirement", "workspace"):
        (target / relative).mkdir(parents=True, exist_ok=True)
    (target / "README.md").write_text(f"# {resolved_name}\n", encoding="utf-8")
    write_project_scaffold_readmes(target)
    sync_workflow(target, workflow_version=workflow_version)
    # The root rule file is intentionally project-editable, but starts as an
    # exact copy of the synchronized workflow rule file.
    shutil.copy2(target / ".aw" / "AGENTS.md", target / "AGENTS.md")
    print(f"instance initialized: {resolved_name}")
    print(f"target: {target}")
    print(f"workflow version: {target / '.aw' / 'workflow-version.yaml'}")
    return 0


def verify_workflow() -> int:
    errors = workflow_protection_errors()
    print("workflow verify-workflow")
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        print("result: BLOCKED")
        return 1
    print("result: PASS (workflow core is clean)")
    return 0


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
    """Return the local time of the Codex client running this command."""
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def local_filename_timestamp() -> str:
    """Create a filesystem-safe local timestamp without falsely claiming UTC."""
    return datetime.now().astimezone().strftime("%Y%m%dT%H%M%S.%f%z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


# Captures a YAML block scalar under a `change_set:` key.
# Frontmatter block example:
#     change_set:
#       added: [FR-100, FR-101]
#       modified: [FR-010]
#       deprecated: [FR-005]
# parse_frontmatter() collapses this to {"change_set": ""} because its kv
# parser does not understand nested maps. Any consumer that needs the
# sub-keys MUST use this helper instead of parse_frontmatter()["change_set"].
_CHANGE_SET_BLOCK_RE = re.compile(
    r"^change_set:\s*\n(?:(?:[ \t]+[A-Za-z_][\w-]*:\s*\[.*?\]\s*(?:\n|$))+)",
    re.MULTILINE,
)

_CHANGE_SET_LINE_RE = re.compile(
    r"^\s+(added|modified|deprecated):\s*\[(.+?)\]", re.MULTILINE | re.DOTALL
)


def parse_change_set(text: str) -> dict[str, list[str]]:
    """Return {"added": [...], "modified": [...], "deprecated": [...]}.

    Only IDs that survive is_real_id() are returned (placeholders like
    FR-XXX are filtered). Missing keys return an empty list. Frontmatter
    is searched at the start of the text; nested keys under change_set
    outside of that block are not parsed.
    """
    out: dict[str, list[str]] = {"added": [], "modified": [], "deprecated": []}
    if not (text.startswith("---\n") or text.startswith("---\r\n")):
        return out
    lines = text.splitlines()
    try:
        end = lines.index("---", 1)
    except ValueError:
        return out
    block = _CHANGE_SET_BLOCK_RE.search("\n".join(lines[1:end]))
    if not block:
        return out
    for match in _CHANGE_SET_LINE_RE.finditer(block.group(0)):
        key = match.group(1)
        ids = [token for token in match.group(2).replace(",", " ").split() if is_real_id(token)]
        out[key] = ids
    return out


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
    # Supports both one-line and multi-line leading comments.
    if text.startswith("<!--"):
        end = text.find("-->", 4)
        if end < 0:
            return {}, text
        values = {}
        inner = text[4:end]
        for line in inner.splitlines():
            match = re.match(r"^\s*([A-Za-z_][\w-]*):\s*(.*?)\s*$", line)
            if match:
                values[match.group(1)] = match.group(2).strip("'\"")
        if values:
            return values, text[end + 3 :].lstrip("\r\n")
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


def canonical_iteration(iteration: str) -> str:
    """Return the on-disk iteration spelling, including the legacy vN alias."""
    major, minor = iteration_number(iteration)
    return f"v{major}.{minor}"


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
    return f"v{major}.{minor}"


def baseline_is_empty() -> bool:
    """Return true when baseline has no formal artifact.

    Raw user material is intake evidence, rather than a baseline artifact, so
    files under ``baseline/raw-requirement`` do not make the baseline ready for
    an iteration route.
    """
    directory = ROOT / "baseline"
    if not directory.exists():
        return True
    return not any(
        path.is_file()
        and path.name != "README.md"
        and "raw-requirement" not in path.relative_to(directory).parts
        for path in directory.rglob("*")
    )


def manifest_iteration() -> str | None:
    """Read the iteration recorded by the generated manifest, if valid."""
    path = project_state_dir() / "manifest.yaml"
    if not path.exists():
        return None
    match = MANIFEST_ITERATION_RE.search(path.read_text(encoding="utf-8"))
    if not match:
        return None
    try:
        return canonical_iteration(match.group(1))
    except ValueError:
        return None


def requirement_route(iteration: str | None = None) -> dict[str, str | None]:
    """Resolve where a newly received, unstructured requirement is archived.

    A project without baseline artifacts treats its first raw requirement as
    baseline input. Otherwise an explicit iteration wins, then the last
    indexed manifest iteration, and finally normal version discovery.
    """
    if baseline_is_empty():
        return {
            "mode": "baseline",
            "iteration": None,
            "raw_requirement_dir": "baseline/raw-requirement",
            "version_source": None,
        }
    resolved = canonical_iteration(iteration) if iteration else manifest_iteration() or discover_iteration()
    source = "explicit" if iteration else "manifest" if manifest_iteration() else "discovery"
    return {
        "mode": "iteration",
        "iteration": resolved,
        "raw_requirement_dir": "iteration/raw-requirement",
        "version_source": source,
        "raw_requirement_access": "user-owned-read-only",
    }


def next_iteration() -> str:
    """Return the next in-major iteration without creating it."""
    directory = ROOT / "iteration"
    pairs: list[tuple[int, int]] = []
    if directory.exists():
        for path in directory.iterdir():
            match = re.fullmatch(r"v(\d+)(?:\.(\d+))?", path.name)
            if path.is_dir() and match:
                pairs.append((int(match.group(1)), int(match.group(2) or 0)))
    if not pairs:
        return "v1.0"
    major, minor = max(pairs)
    return f"v{major}.{minor + 1}"


def project_scaffold_readmes() -> dict[str, str]:
    return {
        "baseline/README.md": (
            "# Baseline\n\n"
            "> `baseline/` 保存项目级基线、核心流程原型、原始需求和 ADR；这些内容不随迭代版本化。\n\n"
            "首次创建版本前，必须完成并人工批准以下基线产物：\n\n"
            "- `01-product-vision.md`：产品愿景\n"
            "- `02-product-charter.md`：项目章程\n"
            "- `03-tech-stack-decision.md`：技术选型决议\n"
            "- `04-glossary.md`：术语表\n"
            "- `05-core-user-flow-prototype.html`：核心用户流程原型\n\n"
            "用户原始需求请放入 `raw-requirement/`；不要将业务代码或迭代交付物放入本目录。\n"
        ),
        "baseline/raw-requirement/README.md": (
            "# 原始需求输入\n\n"
            "存放用户提供的原始需求材料，保留原文件格式与原文。baseline 尚未初始化时，"
            "normalize-requirement 以此目录为输入起草 baseline 文档。\n"
        ),
        "iteration/README.md": (
            "# Iterations\n\n"
            "存放版本化交付物。不要手工创建版本目录；baseline 门禁通过后使用 "
            "`python .workflow/workflow.py init-version` 创建下一个版本。\n\n"
            "`raw-requirement/` 仅存放用户提供的原始需求。运行 "
            "`python .workflow/workflow.py route-requirement` 确定该输入对应的版本；"
            "Agent 仅可读取，不得修改、重命名或删除其中的文件。\n"
        ),
        "iteration/raw-requirement/README.md": (
            "# 迭代原始需求输入\n\n"
            "本目录保存用户提供的迭代原始需求，保留文件格式、文件名与原文。运行 "
            "`python .workflow/workflow.py route-requirement` 确定当前输入对应的目标版本。\n\n"
            "除本说明文件外，目录中的原始需求归用户所有且只读：Agent 不得修改、"
            "重命名或删除。归一化产物必须记录所读取的原始文件路径和目标版本。\n"
        ),
        "workspace/README.md": (
            "# Workspace\n\n"
            "本目录承载实例项目的业务代码、测试和配置。\n\n"
            "本文件只说明 workspace 的目录职责、代码组织和运行约定；当前版本的用户可见功能说明"
            "由实例项目根目录 `README.md` 维护，并在 05-review-release 通过后由工作流更新。\n"
        ),
    }


def write_project_scaffold_readmes(root: Path) -> None:
    for relative, content in project_scaffold_readmes().items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(content, encoding="utf-8")


def init_project() -> int:
    """Create the non-versioned project directories required for intake."""
    created = []
    for relative in ("baseline/raw-requirement", "iteration/raw-requirement", "workspace"):
        path = ROOT / relative
        if not path.exists():
            path.mkdir(parents=True)
            created.append(relative)
    write_project_scaffold_readmes(ROOT)
    print(f"workflow init: created {len(created)} directory(s)")
    for relative in created:
        print(f"  created: {relative}")
    print("next: archive a user requirement, then draft and approve the baseline before running init-version")
    return 0


def init_version(iteration: str | None = None) -> int:
    """Create the next skeleton, then archive the completed predecessor."""
    expected = next_iteration()
    target = canonical_iteration(iteration) if iteration else expected
    if target != expected:
        raise ValueError(f"version must be the next iteration {expected}; received {target}")
    if validate(target, BASELINE_STAGE) != 0:
        raise ValueError(f"baseline gate blocked; version {target} was not initialized")
    root = ROOT / "iteration" / target
    if root.exists():
        raise ValueError(f"iteration already exists: iteration/{target}")
    predecessor = previous_active_iteration(target)
    if predecessor and validate(predecessor, "05-review-release") != 0:
        raise ValueError(
            f"previous iteration {predecessor} has not passed the 05-review-release gate; "
            f"version {target} was not initialized"
        )
    archive_target = ROOT / "iteration" / "archive" / predecessor if predecessor else None
    if archive_target and archive_target.exists():
        raise ValueError(f"archive destination already exists: {archive_target.relative_to(ROOT).as_posix()}")
    for stage in STAGES:
        (root / stage).mkdir(parents=True)
    if predecessor:
        workspace_errors: list[str] = []
        check_instance_readme_freshness(predecessor, workspace_errors)
        if workspace_errors:
            # Roll back only the newly created empty successor skeleton. The
            # predecessor has not been moved yet, so archive state is intact.
            shutil.rmtree(root)
            raise ValueError(
                "instance README refresh required before archiving "
                f"{predecessor}: " + "; ".join(workspace_errors)
            )
        archive_iteration(predecessor, target)
    index(target)
    print(f"version initialized: iteration/{target}")
    if predecessor:
        print(f"archived completed predecessor: iteration/{predecessor} -> iteration/archive/{predecessor}")
    return 0


def previous_active_iteration(target: str) -> str | None:
    """Return the highest active iteration immediately preceding ``target``."""
    target_number = iteration_number(target)
    candidates: list[tuple[tuple[int, int], str]] = []
    directory = ROOT / "iteration"
    if directory.exists():
        for path in directory.iterdir():
            if not path.is_dir():
                continue
            try:
                number = iteration_number(path.name)
            except ValueError:
                continue
            if number < target_number:
                candidates.append((number, canonical_iteration(path.name)))
    return max(candidates)[1] if candidates else None


def archive_iteration(predecessor: str, successor: str) -> None:
    """Move a completed predecessor into the immutable archive after successor creation."""
    source = ROOT / "iteration" / predecessor
    destination = ROOT / "iteration" / "archive" / predecessor
    if not source.is_dir():
        raise ValueError(f"completed predecessor is missing: iteration/{predecessor}")
    if destination.exists():
        raise ValueError(f"archive destination already exists: {destination.relative_to(ROOT).as_posix()}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))
    (destination / "ARCHIVED.md").write_text(
        f"# Archive: {predecessor}\n\n"
        f"- archived_at: {now()}\n"
        f"- superseded_by: {successor}\n"
        f"- rc_artifact: iteration/{predecessor}/05-review-release/{predecessor}-review-release.md\n"
        f"- note: 此目录只读，不得修改。\n",
        encoding="utf-8",
    )


def artifact_paths(iteration: str) -> Iterable[tuple[str, str]]:
    for relative in BASELINE_FILES:
        yield relative, BASELINE_STAGE
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


def stage_outputs(iteration: str, stage: str) -> list[str]:
    iteration_number(iteration)
    outputs = {
        "01-product": [
            f"iteration/{iteration}/01-product/{iteration}-requirement.md",
        ],
        "02-design": [
            f"iteration/{iteration}/02-design/{iteration}-architecture-design.md",
            f"iteration/{iteration}/02-design/{iteration}-api-spec.md",
            f"iteration/{iteration}/02-design/{iteration}-database-dictionary.md",
        ],
        "03-planning": [
            f"iteration/{iteration}/03-planning/{iteration}-task-plan-dag.md",
            f"iteration/{iteration}/03-planning/{iteration}-validation-plan.md",
        ],
        "04-implementation": [
            f"iteration/{iteration}/04-implementation/{iteration}-source-code.md",
            f"iteration/{iteration}/04-implementation/{iteration}-test-results.md",
        ],
        "05-review-release": [
            f"iteration/{iteration}/05-review-release/{iteration}-review-release.md",
        ],
    }
    if stage not in outputs:
        raise ValueError(f"unknown stage: {stage}; iteration={iteration}")
    if stage == "04-implementation" and issue_fixes_required(iteration):
        outputs[stage].append(
            f"iteration/{iteration}/04-implementation/{iteration}-issue-fixes.md"
        )
    if stage == "01-product" and prototype_required(iteration):
        outputs[stage].append(
            f"iteration/{iteration}/01-product/{iteration}-prototype.html"
        )
    return outputs[stage]


def issue_fixes_required(iteration: str) -> bool:
    """Keep the standalone issue log only for the legacy v1.0 artifact set.

    The implementation template merges issue tracking into source-code.md from
    v1.1 onward, so incremental iterations must not be blocked by the obsolete
    file.
    """
    return iteration_number(iteration) == (1, 0)


def prototype_decision(iteration: str) -> str | None:
    """Read the product-stage prototype decision from requirement frontmatter.

    The decision is intentionally a flat frontmatter value so the workflow can
    audit it without interpreting free-form product prose.  ``None`` means the
    requirement is missing the decision or uses an unsupported value.
    """
    requirement = ROOT / f"iteration/{iteration}/01-product/{iteration}-requirement.md"
    if not requirement.exists():
        return None
    frontmatter, _ = parse_frontmatter(requirement.read_text(encoding="utf-8"))
    decision = frontmatter.get("prototype_required", "").lower()
    return decision if decision in {"true", "false"} else None


def prototype_required(iteration: str) -> bool:
    """Return whether this iteration must submit a product-stage prototype."""
    return prototype_decision(iteration) == "true"


def prototype_policy_errors(iteration: str) -> list[str]:
    """Return auditable policy errors for the product-stage prototype choice."""
    requirement = ROOT / f"iteration/{iteration}/01-product/{iteration}-requirement.md"
    if not requirement.exists():
        return []  # The required-input check reports a missing requirement.
    frontmatter, _ = parse_frontmatter(requirement.read_text(encoding="utf-8"))
    decision = frontmatter.get("prototype_required", "").lower()
    if decision not in {"true", "false"}:
        return [
            f"invalid or missing prototype_required decision in {requirement.relative_to(ROOT).as_posix()}; "
            "use true or false"
        ]
    if decision == "false":
        missing = [
            field for field in ("prototype_baseline", "prototype_rationale")
            if not policy_text_is_supplied(frontmatter.get(field, ""))
        ]
        if missing:
            return [
                f"prototype_required is false in {requirement.relative_to(ROOT).as_posix()} but missing "
                f"frontmatter: {', '.join(missing)}"
            ]
    return []


def prototype_review_policy_errors(iteration: str, item: Artifact) -> list[str]:
    """Require explicit, auditable human review metadata for HTML prototypes."""
    if not item.path.endswith("-prototype.html") and item.path != "baseline/05-core-user-flow-prototype.html":
        return []
    path = ROOT / item.path
    if not path.exists():
        return []
    frontmatter, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    required = ["status", "reviewer", "reviewed_at", "review_notes"]
    missing = [field for field in required if field not in frontmatter]
    errors: list[str] = []
    if missing:
        errors.append(
            f"prototype is missing review frontmatter in {item.path}: {', '.join(missing)}"
        )
        return errors
    if item.status == "Approved":
        for field in ("reviewer", "reviewed_at", "review_notes"):
            if not policy_text_is_supplied(frontmatter.get(field, "")):
                errors.append(
                    f"Approved prototype has empty review frontmatter '{field}': {item.path}"
                )
    return errors


def policy_text_is_supplied(value: str) -> bool:
    """Reject empty or template-placeholder values in gate-controlled fields."""
    stripped = value.strip()
    return bool(stripped) and not stripped.startswith("<") and not PLACEHOLDER_RE.search(stripped)


def required_inputs(iteration: str, stage: str) -> list[str]:
    iteration_number(iteration)
    if stage not in STAGES:
        raise ValueError(f"unknown stage: {stage}; iteration={iteration}")
    end = STAGES.index(stage) + 1
    return [path for current in STAGES[:end] for path in stage_outputs(iteration, current)]


def path_artifact(artifacts: list[Artifact], relative: str) -> Artifact | None:
    return next((item for item in artifacts if item.path == relative), None)


def check_task_id_consistency(iteration: str, errors: list[str]) -> None:
    """For stage 04: every TASK-* ID referenced in 04-implementation
    artifacts must be defined in the task plan (task-plan-dag.md).

    Without this check, an implementation file can reference
    TASK-API-999 even when the plan only lists TASK-API-001..010,
    and the gate never notices. Catches typos, copy-paste leftovers,
    and forgotten plans.
    """
    plan_rel = f"iteration/{iteration}/03-planning/{iteration}-task-plan-dag.md"
    plan_path = ROOT / plan_rel
    if not plan_path.exists():
        return  # already flagged by required_inputs; nothing to verify
    plan_text = plan_path.read_text(encoding="utf-8")
    defined_tasks = {
        identifier for identifier in ID_RE.findall(plan_text)
        if is_real_id(identifier) and identifier.startswith("TASK-")
    }
    impl_dir = ROOT / f"iteration/{iteration}/04-implementation"
    if not impl_dir.exists():
        return
    implementation_files = sorted(impl_dir.rglob("*.md"))
    referenced_tasks: set[str] = set()
    for path in implementation_files:
        text = path.read_text(encoding="utf-8")
        referenced = {
            identifier for identifier in ID_RE.findall(text)
            if is_real_id(identifier) and identifier.startswith("TASK-")
        }
        referenced_tasks.update(referenced)
        unknown = referenced - defined_tasks
        for unknown_id in sorted(unknown):
            errors.append(
                f"TASK ID referenced in {path.relative_to(ROOT).as_posix()} "
                f"but not defined in {plan_rel}: {unknown_id}"
            )
    if implementation_files:
        for missing_id in sorted(defined_tasks - referenced_tasks):
            errors.append(
                f"TASK ID defined in {plan_rel} but not referenced by "
                f"04-implementation artifacts: {missing_id}"
            )


def check_readme_freshness(errors: list[str]) -> None:
    """Check that the workflow framework README covers current tooling.

    The root README documents the shared workflow framework, not the active
    product iteration. Product-version freshness is checked separately by
    ``check_instance_readme_freshness`` against the instance root ``README.md``.
    Triggered only on the final 05-review-release stage. Does not modify files.
    """
    readme = FRAMEWORK_ROOT / ".aw" / "README.md"
    if not readme.exists():
        readme = FRAMEWORK_ROOT / "README.md"
    if not readme.exists():
        errors.append("README.md missing; required for RC sign-off")
        # Continue checking skills / scripts against an empty string so
        # callers see every missing reference, not just the first.
        text = ""
    else:
        text = readme.read_text(encoding="utf-8")
    # README must mention all current skills.
    skills_dir = framework_skills_dir()
    if skills_dir.exists():
        current_skills = {p.name for p in skills_dir.iterdir() if p.is_dir()}
        missing = sorted(s for s in current_skills if s not in text)
        if missing:
            errors.append(
                f"README.md does not mention {len(missing)} current skill(s): "
                f"{', '.join(missing)}"
            )
    # README must mention all current scripts.
    scripts_dir = framework_workflow_dir(FRAMEWORK_ROOT) / "scripts"
    if scripts_dir.exists():
        current_scripts = {p.stem for p in scripts_dir.glob("*.py")}
        missing = sorted(s for s in current_scripts if s not in text)
        if missing:
            errors.append(
                f"README.md does not mention {len(missing)} current script(s): "
                f"{', '.join(missing)}"
            )


def check_instance_readme_freshness(iteration: str, errors: list[str]) -> None:
    """Require the generated instance README to include ``iteration``."""
    iteration = canonical_iteration(iteration)
    readme = ROOT / "README.md"
    if not readme.exists():
        errors.append("README.md missing; required before version archive")
        return
    text = readme.read_text(encoding="utf-8")
    marker = f"<!-- workflow:workspace-readme-version: {iteration} -->"
    if marker not in text:
        errors.append(
            f"README.md is not refreshed for {iteration}; "
            f"add marker '{marker}' after merging the version functionality"
        )
    if "## 当前系统功能说明" not in text:
        errors.append("README.md missing required heading: ## 当前系统功能说明")


def generate_instance_readme(iteration: str) -> None:
    """Generate the instance functionality manual from the approved requirement."""
    requested_iteration = iteration
    iteration = canonical_iteration(iteration)
    requirement = ROOT / f"iteration/{iteration}/01-product/{iteration}-requirement.md"
    if not requirement.exists() and requested_iteration != iteration:
        requirement = ROOT / f"iteration/{requested_iteration}/01-product/{requested_iteration}-requirement.md"
    if not requirement.exists():
        raise ValueError(f"instance README source missing: {requirement.relative_to(ROOT)}")
    _, body = parse_frontmatter(requirement.read_text(encoding="utf-8"))
    content = (
        f"<!-- workflow:workspace-readme-version: {iteration} -->\n\n"
        "## 当前系统功能说明\n\n"
        f"{body.strip()}\n"
    )
    write_text_atomic(ROOT / "README.md", content)


def validation_report(iteration: str, stage: str | None, artifacts: list[Artifact] | None = None) -> tuple[list[Artifact], list[str], list[str]]:
    artifacts = artifacts if artifacts is not None else load_artifacts(iteration)
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
    stages = [] if stage == BASELINE_STAGE else [stage] if stage else STAGES
    checked_paths: set[str] = set()
    for current in stages:
        for required in required_inputs(iteration, current):
            if required in checked_paths:
                continue
            checked_paths.add(required)
            item = by_path.get(required)
            if not item:
                errors.append(f"missing input for {current}: {required}")
            elif item.status != "Approved":
                errors.append(f"input for {current} is not Approved: {required} ({item.status})")

    if "01-product" in stages:
        errors.extend(prototype_policy_errors(iteration))

    for item in artifacts:
        if item.path.startswith("templates/"):
            continue
        if item.status == "missing":
            # Already flagged as a missing-input error above; skip the
            # placeholder / frontmatter scans which would otherwise raise
            # FileNotFoundError on the (non-existent) read.
            continue
        text = (ROOT / item.path).read_text(encoding="utf-8")
        if item.stage != BASELINE_STAGE and item.frontmatter is False and item.path.endswith(".html"):
            if item.path.endswith("-prototype.html"):
                errors.append(f"prototype artifact has no frontmatter: {item.path}")
            else:
                warnings.append(f"artifact has no frontmatter status: {item.path}")
        if item.path.endswith(".html"):
            errors.extend(prototype_review_policy_errors(iteration, item))
        if PLACEHOLDER_RE.search(text) and item.status == "Approved":
            errors.append(f"Approved artifact contains unresolved placeholder: {item.path}")

    # S4: TASK-ID cross-artifact consistency (only at stage 04)
    if "04-implementation" in stages:
        check_task_id_consistency(iteration, errors)

    # D3: review/release sign-off checks (only at the final stage)
    if "05-review-release" in stages:
        check_readme_freshness(errors)

    return artifacts, errors, warnings


def validate(iteration: str, stage: str | None, *, record_state: bool = True) -> int:
    artifacts, errors, warnings = validation_report(iteration, stage)
    target = stage or "all"
    if not errors and target == "05-review-release":
        try:
            generate_instance_readme(iteration)
            print(f"instance README generated: README.md ({iteration})")
        except (OSError, ValueError) as error:
            errors.append(str(error))
    if record_state:
        write_current_state(
            iteration,
            artifacts,
            gate={
                "target": target,
                "result": "passed" if not errors else "blocked",
                "errors": errors,
                "warnings": warnings,
                "checked_at": now(),
            },
        )
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


def write_text_atomic(path: Path, text: str) -> None:
    """Write a UTF-8 text file atomically, preserving concurrent readers."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def write_json(path: Path, value: object) -> None:
    write_text_atomic(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_json_atomic(path: Path, value: object) -> None:
    """Write JSON atomically via a sibling temp file + rename.

    Concurrent readers either see the old content or the new content,
    never a half-written file. Used for `cache/context-packs.json`,
    which is read by `context_pack()` on every call and could be
    written from concurrent agents / CI jobs. Cost is one extra
    rename per write; this is fine for state files written O(once)
    per TASK.
    """
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    write_text_atomic(path, payload)


def write_manifest(iteration: str, artifacts: list[Artifact]) -> None:
    lines = [
        "schema_version: '1'",
        f"generated_at: '{now()}'",
        f"iteration: '{iteration}'",
        "stages:",
    ]
    for stage in ALL_STAGES:
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
    state_dir = project_state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)
    write_text_atomic(state_dir / "manifest.yaml", "\n".join(lines) + "\n")


def index(iteration: str) -> int:
    artifacts = load_artifacts(iteration)
    write_manifest(iteration, artifacts)
    state_dir = project_state_dir()
    write_json_atomic(state_dir / "traceability.json", traceability(iteration, artifacts))
    write_current_state(iteration, artifacts)
    # NOTE: per-artifact sha256 hashes are already in manifest.yaml. There
    # is intentionally no cache/index.json: it was never read by any
    # consumer and only duplicated manifest content. See S2 in audit.
    print(f"workflow index: {len(artifacts)} artifacts indexed for {iteration}")
    print(f"manifest: {(state_dir / 'manifest.yaml').relative_to(ROOT)}")
    print(f"traceability: {(state_dir / 'traceability.json').relative_to(ROOT)}")
    return 0


def find_task(iteration: str, task_id: str, artifacts: list[Artifact]) -> tuple[str, str, int]:
    if not TASK_ID_RE.fullmatch(task_id) or not is_real_id(task_id):
        raise ValueError(f"invalid task id: {task_id}")
    plan_path = ROOT / "iteration" / iteration / "03-planning" / f"{iteration}-task-plan-dag.md"
    if not plan_path.exists():
        raise ValueError(f"task plan not found: {plan_path.relative_to(ROOT)}")
    text = plan_path.read_text(encoding="utf-8")
    parsed = sections(text)
    token = re.compile(rf"(?<![A-Z0-9-]){re.escape(task_id)}(?![A-Z0-9-])")
    matches = [section for section in parsed if token.search(section[0])]
    if not matches:
        matches = [section for section in parsed if token.search(section[1])]
    if not matches:
        raise ValueError(f"task not found: {task_id}")
    return matches[0][1], plan_path.relative_to(ROOT).as_posix(), matches[0][2]


def context_pack(
    iteration: str,
    task_id: str,
    *,
    compact: bool = False,
    max_chars: int = 24000,
    max_sections: int = 40,
) -> int:
    """Build a bounded, task-scoped context pack locally.

    The old behaviour remains the default for API compatibility.  Compact
    mode deduplicates identical excerpts, caps the number of sections and
    truncates the generated body before any content is handed to an agent.
    """
    if max_chars < 1000:
        raise ValueError("max_chars must be at least 1000")
    if max_sections < 1:
        raise ValueError("max_sections must be positive")
    artifacts = load_artifacts(iteration)
    task_text, task_path, task_line = find_task(iteration, task_id, artifacts)
    identifiers = sorted(set(ID_RE.findall(task_text)))
    selected: list[tuple[str, str, int]] = []
    for item in artifacts:
        if item.stage in CONTEXT_PACK_EXCLUDED_STAGES:
            continue
        text = (ROOT / item.path).read_text(encoding="utf-8")
        for heading, content, line in sections(text):
            if any(identifier in content for identifier in identifiers):
                selected.append((item.path, content, line))
    # Prefer one copy of a section even when the same contract is repeated in
    # several documents.  This is the main token-saving path for compact mode.
    unique: list[tuple[str, str, int]] = []
    seen_content: set[str] = set()
    for entry in selected:
        key = hashlib.sha256(entry[1].strip().encode("utf-8")).hexdigest()
        if key in seen_content:
            continue
        seen_content.add(key)
        unique.append(entry)
    selected = unique[:max_sections] if compact else unique
    source_hashes = {item.path: item.sha256 for item in artifacts if item.path in {path for path, _, _ in selected} or item.path == task_path}
    key_material = json.dumps({
        "iteration": iteration,
        "task": task_id,
        "identifiers": identifiers,
        "source_hashes": source_hashes,
        "compact": compact,
        "max_chars": max_chars,
        "max_sections": max_sections,
    }, sort_keys=True)
    cache_key = hashlib.sha256(key_material.encode("utf-8")).hexdigest()
    output = WORKFLOW_DIR / "context-packs" / f"{iteration}-{task_id}.md"
    cache_path = WORKFLOW_DIR / "cache" / "context-packs.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    if output.exists() and cache.get(str(output.relative_to(ROOT))) == cache_key:
        write_current_state(
            iteration,
            artifacts,
            active_context={
                "task_id": task_id,
                "path": output.relative_to(ROOT).as_posix(),
                "context_key": cache_key,
            },
        )
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
    if compact:
        rendered = "\n".join(lines)
        if len(rendered) > max_chars:
            suffix = "\n\n[TRUNCATED locally: load only the missing section from the authoritative source.]\n"
            rendered = rendered[: max_chars - len(suffix)] + suffix
        output_text = rendered
    else:
        output_text = "\n".join(lines)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(output_text, encoding="utf-8")
    cache[str(output.relative_to(ROOT))] = cache_key
    write_json_atomic(cache_path, cache)
    write_current_state(
        iteration,
        artifacts,
        active_context={
            "task_id": task_id,
            "path": output.relative_to(ROOT).as_posix(),
            "context_key": cache_key,
        },
    )
    print(f"context pack written: {output.relative_to(ROOT)}")
    print(f"selected excerpts: {len(selected)}, identifiers: {len(identifiers)}, chars: {len(output_text)}")
    return 0


def cleanup_context_packs(iteration: str, *, execute: bool = False) -> int:
    """Preview or remove generated Context Packs for an archived iteration.

    Task-run records are audit evidence and are intentionally outside this
    operation.  Requiring an archived iteration and an explicit execute flag
    prevents cleanup from removing an active implementation task's context.
    """
    resolved = canonical_iteration(iteration)
    archive = ROOT / "iteration" / "archive" / resolved
    if not archive.is_dir():
        raise ValueError(
            f"cleanup requires an archived iteration: iteration/archive/{resolved}"
        )
    packs_dir = WORKFLOW_DIR / "context-packs"
    packs = sorted(packs_dir.glob(f"{resolved}-*.md")) if packs_dir.exists() else []
    cache_path = WORKFLOW_DIR / "cache" / "context-packs.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    prefix = f".workflow/context-packs/{resolved}-"
    cache_keys = sorted(key for key in cache if key.startswith(prefix))

    mode = "execute" if execute else "dry-run"
    print(
        f"cleanup {mode}: iteration={resolved}; context_packs={len(packs)}; "
        f"cache_keys={len(cache_keys)}; task_runs=preserved"
    )
    for pack in packs:
        print(f"  context-pack: {pack.relative_to(ROOT).as_posix()}")
    if not execute:
        print("next: re-run with --execute to remove the listed generated Context Packs and cache keys")
        return 0

    for pack in packs:
        pack.unlink()
    if cache_keys:
        for key in cache_keys:
            del cache[key]
        write_json_atomic(cache_path, cache)
    print(f"cleanup complete: removed_context_packs={len(packs)}; removed_cache_keys={len(cache_keys)}; task_runs=preserved")
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


def state_source_fingerprint(artifacts: list[Artifact], records: list[dict]) -> str:
    """Fingerprint every authoritative input represented by the checkpoint."""
    payload = {
        "artifacts": [
            {"path": item.path, "status": item.status, "sha256": item.sha256}
            for item in artifacts
        ],
        "tasks": records,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def stage_blockers(iteration: str, stage: str, by_path: dict[str, Artifact]) -> list[dict]:
    expected = BASELINE_FILES if stage == BASELINE_STAGE else stage_outputs(iteration, stage)
    blockers = []
    for path in expected:
        item = by_path.get(path)
        status = item.status if item else "missing"
        if status != "Approved":
            blockers.append({"path": path, "status": status})
    if stage == "01-product":
        requirement = f"iteration/{iteration}/01-product/{iteration}-requirement.md"
        if by_path.get(requirement) and prototype_policy_errors(iteration):
            blockers.append({"path": f"{requirement}#prototype_required", "status": "invalid"})
    return blockers


def derive_current_stage(iteration: str, artifacts: list[Artifact], gate: dict | None) -> dict:
    by_path = {item.path: item for item in artifacts}
    for stage in ALL_STAGES:
        blockers = stage_blockers(iteration, stage, by_path)
        if blockers:
            missing = [item for item in blockers if item["status"] == "missing"]
            return {
                "name": stage,
                "status": "blocked" if missing else "in_progress",
                "blocking_artifacts": blockers,
                "reason": (
                    f"{len(missing)} required artifact(s) are missing"
                    if missing else f"{len(blockers)} required artifact(s) are not Approved"
                ),
                "next_action": (
                    f"Create the required {stage} artifacts" if missing
                    else f"Review and approve {stage} artifacts, then run validate --stage {stage}"
                ),
            }
    if gate and gate["result"] == "blocked":
        return {
            "name": gate["target"],
            "status": "blocked",
            "blocking_artifacts": [],
            "reason": "Latest gate validation is blocked",
            "next_action": "Resolve the latest gate errors and validate again",
        }
    return {
        "name": "05-review-release",
        "status": "ready_for_next_iteration",
        "blocking_artifacts": [],
        "reason": "All required stage artifacts are Approved",
        "next_action": "Create the next iteration; its creation archives this completed predecessor",
    }


def write_current_state(
    iteration: str,
    artifacts: list[Artifact],
    *,
    gate: dict | None = None,
    active_context: dict | None = None,
    last_task: dict | None = None,
) -> dict:
    """Write the derived recovery checkpoint; never treat it as approval authority."""
    records = task_records(iteration)
    fingerprint = state_source_fingerprint(artifacts, records)
    previous: dict = {}
    state_path = project_state_dir() / "current-state.json"
    if state_path.exists():
        try:
            previous = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = {}
    same_inputs = previous.get("iteration") == iteration and previous.get("source_fingerprint") == fingerprint
    if gate is None and same_inputs:
        gate = previous.get("latest_gate")
    if active_context is None and same_inputs:
        candidate = previous.get("active_context")
        if candidate and (ROOT / candidate.get("path", "")).exists():
            active_context = candidate
    state = {
        "schema_version": "1",
        "generated_at": now(),
        "iteration": iteration,
        "source_fingerprint": fingerprint,
        "authority": "Derived cache only. Artifact frontmatter and gate validation remain authoritative.",
        "current_stage": derive_current_stage(iteration, artifacts, gate),
        "latest_gate": gate,
        "active_context": active_context,
        "last_task": last_task or (records[0] if records else None),
        "available_context_packs": [
            path.relative_to(ROOT).as_posix()
            for path in sorted((WORKFLOW_DIR / "context-packs").glob(f"{iteration}-*.md"))
        ] if (WORKFLOW_DIR / "context-packs").exists() else [],
        "sources": {
            "manifest": "workspace/workflow/manifest.yaml",
            "traceability": "workspace/workflow/traceability.json",
            "task_runs": ".workflow/task-runs/",
        },
    }
    write_json_atomic(state_path, state)
    return state


def state(iteration: str, *, refresh: bool = False) -> int:
    path = project_state_dir() / "current-state.json"
    artifacts = load_artifacts(iteration)
    records = task_records(iteration)
    fingerprint = state_source_fingerprint(artifacts, records)
    if refresh or not path.exists():
        write_manifest(iteration, artifacts)
        write_json_atomic(project_state_dir() / "traceability.json", traceability(iteration, artifacts))
        data = write_current_state(iteration, artifacts)
        mode = "refreshed"
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("iteration") != iteration or data.get("source_fingerprint") != fingerprint:
            write_manifest(iteration, artifacts)
            write_json_atomic(project_state_dir() / "traceability.json", traceability(iteration, artifacts))
            data = write_current_state(iteration, artifacts)
            mode = "refreshed"
        else:
            mode = "cached"
    current = data["current_stage"]
    print(f"workflow state: {mode}; iteration={data['iteration']}")
    print(f"current stage: {current['name']} ({current['status']})")
    print(f"next action: {current['next_action']}")
    if current["blocking_artifacts"]:
        print("blockers:")
        for blocker in current["blocking_artifacts"]:
            print(f"  - {blocker['path']} ({blocker['status']})")
    if data["active_context"]:
        print(f"active context: {data['active_context']['task_id']} -> {data['active_context']['path']}")
    return 0


def refresh(iteration: str, stage: str | None) -> int:
    """Synchronize workflow artifacts and run the requested stage gate.

    This is the standard post-document-edit sequence: rebuild the artifact
    index and traceability graph, refresh the recovery checkpoint, then run
    validation. The first non-zero result stops the sequence.
    """
    print(f"workflow refresh: iteration={iteration}, stage={stage or 'all'}")
    result = index(iteration)
    if result != 0:
        return result
    result = state(iteration, refresh=True)
    if result != 0:
        return result
    return validate(iteration, stage)


def active_iteration() -> str | None:
    """Return the highest active iteration, or None after archival cleanup."""
    directory = ROOT / "iteration"
    if not directory.exists():
        return None
    candidates = []
    for path in directory.iterdir():
        match = re.fullmatch(r"v(\d+)(?:\.(\d+))?", path.name)
        if path.is_dir() and match:
            candidates.append((int(match.group(1)), int(match.group(2) or 0), path.name))
    if not candidates:
        return None
    major, minor, _ = max(candidates)
    return f"v{major}.{minor}"


def resume_data(iteration: str | None = None) -> dict:
    """Return the smallest local recovery payload for a new agent turn."""
    resolved = canonical_iteration(iteration) if iteration else active_iteration()
    if resolved is None:
        return {
            "status": "NO_ACTIVE_ITERATION",
            "iteration": None,
            "current_stage": None,
            "next_action": "Route a new raw requirement, then initialize the baseline.",
            "blocking_artifacts": [],
            "recommended_reads": [],
            "gate_command": None,
        }
    artifacts = load_artifacts(resolved)
    records = task_records(resolved)
    fingerprint = state_source_fingerprint(artifacts, records)
    state_path = project_state_dir() / "current-state.json"
    data = None
    if state_path.exists():
        try:
            candidate = json.loads(state_path.read_text(encoding="utf-8"))
            if candidate.get("iteration") == resolved and candidate.get("source_fingerprint") == fingerprint:
                data = candidate
        except json.JSONDecodeError:
            data = None
    if data is None:
        write_manifest(resolved, artifacts)
        write_json_atomic(project_state_dir() / "traceability.json", traceability(resolved, artifacts))
        data = write_current_state(resolved, artifacts)
    current = data["current_stage"]
    reads = [item["path"] for item in current.get("blocking_artifacts", [])]
    if data.get("active_context"):
        reads.append(data["active_context"]["path"])
    return {
        "status": "READY",
        "iteration": resolved,
        "current_stage": current,
        "latest_gate": data.get("latest_gate"),
        "active_context": data.get("active_context"),
        "last_task": data.get("last_task"),
        "next_action": current["next_action"],
        "blocking_artifacts": current.get("blocking_artifacts", []),
        "recommended_reads": list(dict.fromkeys(reads)),
        "gate_command": f"python .workflow/workflow.py validate --iteration {resolved} --stage {current['name']}",
        "source_fingerprint": data["source_fingerprint"],
        "generated_at": data["generated_at"],
    }


def resume(iteration: str | None = None, *, as_json: bool = False) -> int:
    payload = resume_data(iteration)
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"workflow resume: {payload['status']}")
        if payload["iteration"]:
            print(f"iteration: {payload['iteration']}")
            print(f"current stage: {payload['current_stage']['name']} ({payload['current_stage']['status']})")
            print(f"next action: {payload['next_action']}")
            for path in payload["recommended_reads"]:
                print(f"read: {path}")
        else:
            print(f"next action: {payload['next_action']}")
    return 0


def task_dag_report(iteration: str) -> dict:
    plan = ROOT / "iteration" / iteration / "03-planning" / f"{iteration}-task-plan-dag.md"
    if not plan.exists():
        return {"status": "missing", "tasks": [], "edges": [], "cycles": [], "errors": [str(plan.relative_to(ROOT))]}
    text = plan.read_text(encoding="utf-8")
    task_sections = [(heading, content) for heading, content, _ in sections(text) if re.search(r"\bTASK-[A-Z0-9-]+\b", heading)]
    tasks = sorted({task for heading, _ in task_sections for task in ID_RE.findall(heading) if task.startswith("TASK-") and is_real_id(task)})
    edges: list[dict[str, str]] = []
    graph: dict[str, set[str]] = {task: set() for task in tasks}
    for heading, content in task_sections:
        current_ids = [task for task in ID_RE.findall(heading) if task.startswith("TASK-") and is_real_id(task)]
        if not current_ids:
            continue
        current = current_ids[0]
        prerequisite = re.search(r"(?:前置|depends_on|depends on)\s*\|?\s*([^\n]+)", content, re.IGNORECASE)
        if not prerequisite:
            continue
        for dependency in ID_RE.findall(prerequisite.group(1)):
            if dependency.startswith("TASK-") and is_real_id(dependency):
                graph.setdefault(current, set()).add(dependency)
                edges.append({"from": dependency, "to": current})
    cycles: list[list[str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, path: list[str]) -> None:
        if node in visiting:
            cycles.append(path[path.index(node):] + [node])
            return
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph.get(node, set()):
            if dependency in graph:
                visit(dependency, path + [dependency])
        visiting.remove(node)
        visited.add(node)

    for task in tasks:
        visit(task, [task])
    unknown = sorted({edge["from"] for edge in edges if edge["from"] not in graph})
    return {"status": "passed" if not cycles and not unknown else "failed", "tasks": tasks, "edges": edges, "cycles": cycles, "unknown_dependencies": unknown, "errors": []}


def coverage_report(iteration: str) -> dict:
    plan = ROOT / "iteration" / iteration / "03-planning" / f"{iteration}-task-plan-dag.md"
    validation = ROOT / "iteration" / iteration / "03-planning" / f"{iteration}-validation-plan.md"
    requirement = ROOT / "iteration" / iteration / "01-product" / f"{iteration}-requirement.md"
    plan_text = plan.read_text(encoding="utf-8") if plan.exists() else ""
    validation_text = validation.read_text(encoding="utf-8") if validation.exists() else ""
    requirement_text = requirement.read_text(encoding="utf-8") if requirement.exists() else ""
    tasks = sorted({i for i in ID_RE.findall(plan_text) if i.startswith("TASK-") and is_real_id(i)})
    validation_tasks = sorted({i for i in ID_RE.findall(validation_text) if i.startswith("TASK-") and is_real_id(i)})
    acs = sorted({i for i in ID_RE.findall(requirement_text) if i.startswith("AC-") and is_real_id(i)})
    validation_acs = sorted({i for i in ID_RE.findall(validation_text) if i.startswith("AC-") and is_real_id(i)})
    missing_tasks = sorted(set(tasks) - set(validation_tasks))
    missing_acs = sorted(set(acs) - set(validation_acs))
    return {
        "tasks": {"defined": len(tasks), "validated": len(set(tasks) - set(missing_tasks)), "missing_validation": missing_tasks},
        "acceptance": {"defined": len(acs), "validated": len(set(acs) - set(missing_acs)), "missing_validation": missing_acs},
        "status": "passed" if not missing_tasks and not missing_acs else "warning",
    }


def preflight(iteration: str | None = None, *, as_json: bool = False) -> int:
    resolved = canonical_iteration(iteration) if iteration else active_iteration()
    if resolved is None:
        payload = resume_data(None)
        payload["preflight"] = "NO_ACTIVE_ITERATION"
        if as_json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print("preflight: NO_ACTIVE_ITERATION")
        return 0
    artifacts, errors, warnings = validation_report(resolved, None)
    dag = task_dag_report(resolved)
    coverage = coverage_report(resolved)
    payload = {"status": "passed" if not errors and dag["status"] == "passed" else "blocked", "iteration": resolved, "errors": errors, "warnings": warnings, "dag": dag, "coverage": coverage, "artifact_count": len(artifacts), "generated_at": now()}
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"preflight: {payload['status']}; iteration={resolved}; artifacts={len(artifacts)}")
        for error in errors:
            print(f"ERROR {error}")
        if dag["status"] != "passed":
            print(f"ERROR task DAG: {dag.get('cycles') or dag.get('unknown_dependencies')}")
        if coverage["status"] != "passed":
            print(f"WARNING coverage: {coverage}")
    return 0 if payload["status"] == "passed" else 1


def review_pack(iteration: str | None = None, stage: str | None = None, *, as_json: bool = False) -> int:
    resolved = canonical_iteration(iteration) if iteration else active_iteration()
    if resolved is None:
        return resume(None, as_json=as_json)
    artifacts, errors, warnings = validation_report(resolved, stage)
    target = stage or "all"
    required = required_inputs(resolved, stage) if stage else []
    by_path = {item.path: item for item in artifacts}
    payload = {
        "iteration": resolved,
        "stage": target,
        "status": "blocked" if errors else "ready_for_human_review",
        "artifacts": [{"path": path, "status": by_path.get(path).status if by_path.get(path) else "missing", "lines": by_path.get(path).lines if by_path.get(path) else 0} for path in required],
        "errors": errors,
        "warnings": warnings,
        "review_commands": [f"python .workflow/workflow.py validate --iteration {resolved} --stage {target}"],
        "note": "This is evidence for human review; it does not approve artifacts.",
    }
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"review-pack: {payload['status']}; iteration={resolved}; stage={target}")
        for item in payload["artifacts"]:
            print(f"  {item['status']:<9} {item['path']}")
        for error in errors:
            print(f"ERROR {error}")
    return 0 if not errors else 1


def gate_code(iteration: str) -> int:
    # Capture diagnostics so dashboard generation remains a data-producing operation.
    with contextlib.redirect_stdout(io.StringIO()):
        return validate(iteration, None, record_state=False)


def dashboard_data(iteration: str) -> dict:
    artifacts = load_artifacts(iteration)
    records = task_records(iteration)
    by_stage: dict[str, list[dict]] = {stage: [] for stage in ALL_STAGES}
    for item in artifacts:
        by_stage[item.stage].append({"path": item.path, "status": item.status, "lines": item.lines, "sha256": item.sha256})
    stages = []
    overall_gate = gate_code(iteration)
    checkpoint = write_current_state(iteration, artifacts)
    for stage, items in by_stage.items():
        if not items:
            status = "empty"
        elif stage == BASELINE_STAGE and all(item["status"] == "Approved" for item in items):
            status = "approved" if overall_gate == 0 else "blocked"
        elif stage != BASELINE_STAGE and all(item["status"] == "Approved" for item in items):
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
        "current_stage": checkpoint["current_stage"],
        "traceability_path": "workspace/workflow/traceability.json",
        "manifest_path": "workspace/workflow/manifest.yaml",
    }


def dashboard(iteration: str) -> int:
    template_path = framework_workflow_dir(FRAMEWORK_ROOT) / "dashboard" / "template.html"
    if not template_path.exists():
        raise ValueError(f"dashboard template not found: {template_path.relative_to(ROOT)}")
    data = dashboard_data(iteration)
    serialized = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    fallback = static_dashboard_fallback(data)
    page = template_path.read_text(encoding="utf-8").replace("__DASHBOARD_DATA__", serialized).replace("__DASHBOARD_FALLBACK__", fallback)
    output = WORKFLOW_DIR / "dashboard" / "index.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    write_text_atomic(output, page)
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
        '<div data-dashboard-fallback><section class="summary"><header><div><h1>Alchemy Works (AW) 软件开发工作流 · 项目执行视图</h1>'
        f'<p class="muted">迭代 {html.escape(data["iteration"])} · 当前阶段 {html.escape(data["current_stage"]["name"])} · 更新时间 {html.escape(data["generated_at"])}</p>'
        f'</div><span class="badge {html.escape(data["gate_status"])}">门禁：{html.escape(data["gate_status"])}</span></header>'
        f'<div class="summary-grid"><section class="summary-item"><h2>下一步</h2><p><strong>{html.escape(data["current_stage"]["name"])}</strong> · {html.escape(data["current_stage"]["status"])}</p><p class="muted">{html.escape(data["current_stage"]["next_action"])}</p></section><section class="summary-item"><h2>最近任务结论</h2>{tasks}</section>'
        f'<section class="summary-item"><h2>数据来源</h2><p class="muted"><code>workspace/workflow/manifest.yaml</code></p><p class="muted"><code>workspace/workflow/traceability.json</code></p></section>'
        f'<section class="summary-item"><h2>使用方式</h2><p class="muted">恢复工作时运行 <code>state --refresh</code>；TASK 完成后运行 <code>task-finished</code>。</p></section></div></section>'
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
    # Always verify the task is referenced in the task plan, regardless of
    # refresh_index. Without this guard, a typo'd task_id silently writes
    # a phantom succeeded/failed/blocked record into .workflow/task-runs/
    # and pollutes the dashboard. find_task raises ValueError -> main() exits 2.
    artifacts = load_artifacts(iteration)
    find_task(iteration, task_id, artifacts)
    if refresh_index:
        index(iteration)
    context_path = WORKFLOW_DIR / "context-packs" / f"{iteration}-{task_id}.md"
    if not context_path.exists():
        raise ValueError(
            f"context pack missing for {task_id}; run `workflow.py context --iteration {iteration} --task {task_id}` first"
        )
    record = {
        "schema_version": "2",
        "iteration": iteration,
        "task_id": task_id,
        "result": result,
        "recorded_at": now(),
        "context_pack": f".workflow/context-packs/{iteration}-{task_id}.md",
        "context_pack_present": True,
        "project_gate_status": "passed" if gate_code(iteration) == 0 else "blocked",
    }
    path = WORKFLOW_DIR / "task-runs" / f"{iteration}-{task_id}.json"
    write_json_atomic(path, record)
    history_stamp = local_filename_timestamp()
    history_path = WORKFLOW_DIR / "task-runs" / "history" / f"{iteration}-{task_id}-{history_stamp}.json"
    write_json_atomic(history_path, record)
    write_current_state(iteration, artifacts, last_task=record)
    if refresh_dashboard:
        dashboard(iteration)
    print(f"task conclusion: {task_id}={result}; gate={record['project_gate_status']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        help="Instance project root whose documents and .workflow state are read and written.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("index", "validate"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--iteration", default=None)
        if name == "validate":
            sub.add_argument("--stage", choices=GATE_STAGES)
    context = subparsers.add_parser("context")
    context.add_argument("--iteration", default=None)
    context.add_argument("--task", required=True)
    context.add_argument("--compact", action="store_true", help="Deduplicate and bound excerpts before handing the pack to an agent.")
    context.add_argument("--max-chars", type=int, default=24000)
    context.add_argument("--max-sections", type=int, default=40)
    cleanup = subparsers.add_parser(
        "cleanup",
        help="Preview or remove generated Context Packs for an archived iteration; task-run audit records are preserved.",
    )
    cleanup.add_argument("--iteration", required=True)
    cleanup.add_argument(
        "--execute",
        action="store_true",
        help="Perform deletion. Without this flag cleanup is a dry run.",
    )
    dashboard_parser = subparsers.add_parser("dashboard")
    dashboard_parser.add_argument("--iteration", default=None)
    state_parser = subparsers.add_parser("state", help="Show the derived workflow recovery checkpoint.")
    state_parser.add_argument("--iteration", default=None)
    state_parser.add_argument("--refresh", action="store_true", help="Rebuild manifest, traceability, and checkpoint before showing state.")
    refresh_parser = subparsers.add_parser(
        "refresh",
        help="Run index, state --refresh, and stage validation after document changes.",
    )
    refresh_parser.add_argument("--iteration", default=None)
    refresh_parser.add_argument("--stage", choices=GATE_STAGES)
    resume_parser = subparsers.add_parser("resume", help="Emit the smallest local recovery payload for a new agent turn.")
    resume_parser.add_argument("--iteration", default=None)
    resume_parser.add_argument("--json", action="store_true")
    preflight_parser = subparsers.add_parser("preflight", help="Run local gate, DAG, and coverage checks without an LLM.")
    preflight_parser.add_argument("--iteration", default=None)
    preflight_parser.add_argument("--json", action="store_true")
    review_parser = subparsers.add_parser("review-pack", help="Build a compact human-review evidence summary.")
    review_parser.add_argument("--iteration", default=None)
    review_parser.add_argument("--stage", choices=GATE_STAGES)
    review_parser.add_argument("--json", action="store_true")
    subparsers.add_parser(
        "verify-workflow",
        help="Verify that workflow core files are clean before product workflow commands run.",
    )
    finished = subparsers.add_parser("task-finished")
    finished.add_argument("--iteration", default=None)
    finished.add_argument("--task", required=True)
    finished.add_argument("--result", choices=["succeeded", "failed", "blocked"], required=True)
    finished.add_argument("--refresh-index", action="store_true", help="Also re-run `index` after writing the task record. Off by default; only enable when the task changed artifact state.")
    finished.add_argument("--auto-refresh", action="store_true", help="Refresh the local index when completing a task; keeps hashes and checkpoint metadata consistent.")
    finished.add_argument("--refresh-dashboard", action="store_true", help="Also re-render the static dashboard after writing the task record. Off by default; run `python .workflow/workflow.py dashboard` separately when needed.")
    route = subparsers.add_parser("route-requirement", help="Resolve the archive location for a newly received raw requirement.")
    route.add_argument("--iteration", help="Override the version recorded in manifest.yaml.")
    subparsers.add_parser("init", help="Create the non-versioned project directory skeleton.")
    init_instance_parser = subparsers.add_parser("init-instance", help="Create an instance project and pin its workflow source commit.")
    init_instance_parser.add_argument("--name", help="Instance name; defaults to the target directory name.")
    init_instance_parser.add_argument("--directory", required=True)
    init_instance_parser.add_argument("--workflow-version", help="Git ref (tag, branch, or commit) for the workflow source.")
    init_instance_parser.add_argument("--dry-run", action="store_true")
    sync_parser = subparsers.add_parser("sync", help="Synchronize workflow definitions into an existing instance Git tree.")
    sync_parser.add_argument("--directory", required=True)
    sync_parser.add_argument("--workflow-version", help="Git ref (tag, branch, or commit) for the workflow source.")
    sync_parser.add_argument("--allow-dirty", action="store_true")
    sync_parser.add_argument("--dry-run", action="store_true")
    version = subparsers.add_parser("init-version", help="Create the next iteration skeleton after the baseline gate passes.")
    version.add_argument("--iteration", help="Use the expected next version explicitly.")
    args = parser.parse_args(argv)
    configure_project_root(args.project_root)
    if args.command in {"index", "validate", "context", "dashboard", "state", "refresh", "task-finished"} and args.iteration is None:
        args.iteration = discover_iteration()
    # Normalize legacy short form (v1) to canonical v1.0 so path lookups
    # stay consistent with discover_iteration() and the on-disk directory
    # naming. Without this, --iteration v1 would search iteration/v1/...
    # even when only iteration/v1.0/ exists, producing misleading
    # "missing input" errors instead of resolving the real directory.
    if getattr(args, "iteration", None) is not None:
        try:
            args.iteration = canonical_iteration(args.iteration)
        except (AttributeError, TypeError, ValueError):
            pass  # leave as-is for error reporting downstream
    try:
        if args.command == "verify-workflow":
            return verify_workflow()
        if args.command == "init-instance":
            return init_instance(
                args.name,
                args.directory,
                dry_run=args.dry_run,
                workflow_version=args.workflow_version,
            )
        if args.command == "sync":
            return sync_workflow(
                args.directory,
                allow_dirty=args.allow_dirty,
                dry_run=args.dry_run,
                workflow_version=args.workflow_version,
            )
        protection_errors = workflow_protection_errors()
        if protection_errors:
            for error in protection_errors:
                print(f"ERROR {error}", file=sys.stderr)
            return 2
        if args.command == "init":
            return init_project()
        if args.command == "init-version":
            return init_version(args.iteration)
        if args.command == "index":
            return index(args.iteration)
        if args.command == "validate":
            return validate(args.iteration, args.stage)
        if args.command == "context":
            return context_pack(args.iteration, args.task, compact=args.compact, max_chars=args.max_chars, max_sections=args.max_sections)
        if args.command == "cleanup":
            return cleanup_context_packs(args.iteration, execute=args.execute)
        if args.command == "dashboard":
            return dashboard(args.iteration)
        if args.command == "state":
            return state(args.iteration, refresh=args.refresh)
        if args.command == "refresh":
            return refresh(args.iteration, args.stage)
        if args.command == "resume":
            return resume(args.iteration, as_json=args.json)
        if args.command == "preflight":
            return preflight(args.iteration, as_json=args.json)
        if args.command == "review-pack":
            return review_pack(args.iteration, args.stage, as_json=args.json)
        if args.command == "route-requirement":
            print(json.dumps(requirement_route(args.iteration), ensure_ascii=False, indent=2))
            return 0
        return task_finished(args.iteration, args.task, args.result, refresh_index=args.refresh_index or args.auto_refresh, refresh_dashboard=args.refresh_dashboard)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
