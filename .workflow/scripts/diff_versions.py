"""Cross-version diff — answers 'what changed between v1.0 and v1.1?' without LLM.

Compares two iterations by:
  - collecting every stable ID (FR/FS/BR/NFR/API/TBL/TASK/AC/ISSUE) found in
    artifacts of each side
  - reading `change_set.deprecated` from the `to` iteration's frontmatter (if
    present) to mark deprecated IDs explicitly
  - computing added/modified-by-location/removed/deprecated buckets

Limitations:
  - "modified" is detected only by location: an ID appearing in a new file in
    `to` that was not in the same file in `from` counts as a modification in
    that file. Body-level semantic diffs are out of scope (no .md content
    comparison). Use a separate `git diff` for full prose change review.
  - When `from` does not exist on disk (e.g. v1.0 archived), the script still
    runs but every artifact is "added".

Usage:
    python .workflow/scripts/diff_versions.py --from v1.0 --to v1.1
    python .workflow/scripts/diff_versions.py --from v1.0 --to v1.1 --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

THIS = Path(__file__).resolve()
sys.path.insert(0, str(THIS.parents[1]))

from workflow import (  # noqa: E402
    ID_RE,
    canonical_iteration,
    discover_iteration,
    is_real_id,
    parse_change_set,
)

REPO_ROOT = THIS.parents[2]


def _iteration_root(iteration: str) -> Path:
    active = REPO_ROOT / "iteration" / iteration
    if active.exists():
        return active
    return REPO_ROOT / "iteration" / "archive" / iteration


def _artifact_paths(iteration: str) -> list[Path]:
    paths = [REPO_ROOT / relative for relative in (
        "baseline/01-product-vision.md",
        "baseline/02-product-charter.md",
        "baseline/03-tech-stack-decision.md",
        "baseline/04-glossary.md",
    )]
    root = _iteration_root(iteration)
    if root.exists():
        paths.extend(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in {".md", ".html", ".json"})
    return [path for path in paths if path.exists()]


def _ids_in(iteration: str) -> dict[str, set[str]]:
    """Return mapping id -> set of artifact paths that contain it.

    Excludes templates/ and the workflow CLI itself; iterates only artifacts
    load_artifacts() reports (baseline + iteration/*/).
    """
    out: dict[str, set[str]] = {}
    root = _iteration_root(iteration)
    for path in _artifact_paths(iteration):
        text = path.read_text(encoding="utf-8")
        try:
            path.relative_to(root)
            under_version_root = True
        except ValueError:
            under_version_root = False
        if under_version_root and root != REPO_ROOT / "iteration" / iteration:
            relative = f"iteration/{iteration}/{path.relative_to(root).as_posix()}"
        else:
            relative = path.relative_to(REPO_ROOT).as_posix()
        for identifier in ID_RE.findall(text):
            if not is_real_id(identifier):
                continue
            out.setdefault(identifier, set()).add(relative)
    return out


def _deprecated_in(iteration: str) -> set[str]:
    """Read `change_set.deprecated` from a top-level 01-product artifact.

    Delegates to workflow.parse_change_set so the parsing logic lives
    in one place; any future consumer (e.g. a normalize-requirement
    checker) can reuse the same helper instead of duplicating regex.
    """
    base = _iteration_root(iteration) / "01-product"
    candidates = (
        base / f"{iteration}-requirement.md",
        base / f"{iteration}-iteration-changelog.md",
    )
    deprecated: set[str] = set()
    for path in candidates:
        if not path.exists():
            continue
        try:
            change_set = parse_change_set(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        deprecated.update(change_set.get("deprecated", []))
    return deprecated


def collect(from_iter: str, to_iter: str) -> dict:
    """Compute the three diff buckets plus explicit deprecations."""
    from_ids = _ids_in(from_iter) if _iteration_root(from_iter).exists() else {}
    to_ids = _ids_in(to_iter) if _iteration_root(to_iter).exists() else {}
    deprecated = _deprecated_in(to_iter)

    from_set = set(from_ids)
    to_set = set(to_ids)

    added = sorted(to_set - from_set)
    removed = sorted(from_set - to_set)
    common = from_set & to_set

    # Modified = ID existed in both, but the set of artifact paths differs.
    # This catches moves, additions within already-present artifacts, and
    # renames. Bodies are not compared.
    modified: list[dict] = []
    for identifier in sorted(common):
        from_paths = from_ids[identifier]
        to_paths = to_ids[identifier]
        if from_paths != to_paths:
            modified.append({
                "id": identifier,
                "added_in": sorted(to_paths - from_paths),
                "removed_from": sorted(from_paths - to_paths),
            })

    return {
        "from": from_iter,
        "to": to_iter,
        "added": added,
        "removed": removed,
        "modified": modified,
        "deprecated": sorted(deprecated),
        "totals": {
            "from_ids": len(from_set),
            "to_ids": len(to_set),
            "added": len(added),
            "removed": len(removed),
            "modified": len(modified),
            "deprecated": len(deprecated),
        },
    }


def render_text(data: dict) -> str:
    out = [f"Cross-version diff: {data['from']} → {data['to']}", ""]
    totals = data["totals"]
    out.append(
        f"  from={totals['from_ids']} ids · to={totals['to_ids']} ids · "
        f"+{totals['added']} added · ~{totals['modified']} modified · "
        f"-{totals['removed']} removed · !{totals['deprecated']} deprecated"
    )
    out.append("")

    def bucket(title: str, items: Iterable, formatter) -> None:
        items = list(items)
        if not items:
            return
        out.append(f"  {title} ({len(items)})")
        for item in items:
            out.append(formatter(item))
        out.append("")

    bucket("Added", data["added"], lambda x: f"    + {x}")
    bucket("Removed", data["removed"], lambda x: f"    - {x}")
    bucket("Deprecated", data["deprecated"], lambda x: f"    ! {x}")

    for entry in data["modified"]:
        out.append(f"    ~ {entry['id']}")
        for p in entry["added_in"]:
            out.append(f"        + in {p}")
        for p in entry["removed_from"]:
            out.append(f"        - from {p}")
        out.append("")

    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from", dest="from_iter", required=True,
                        help="source iteration (e.g. v1.0)")
    parser.add_argument("--to", dest="to_iter", required=True,
                        help="target iteration (e.g. v1.1)")
    parser.add_argument("--json", action="store_true",
                        help="emit JSON instead of text")
    args = parser.parse_args()
    args.from_iter = canonical_iteration(args.from_iter)
    args.to_iter = canonical_iteration(args.to_iter)
    data = collect(args.from_iter, args.to_iter)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(render_text(data))
    # Non-zero exit only when deprecated list is non-empty (so CI can flag
    # unconfirmed retirements across versions). Removed-only is informational.
    return 0 if not data["deprecated"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
