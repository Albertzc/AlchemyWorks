"""Markdown cross-reference validator — answers 'are all .md links resolvable?'

Scans every .md file under iteration/{ver}/ and validates local relative
links. External (http://, https://) and anchor-only (#…) links are skipped.

Usage:
    python .workflow/scripts/check_links.py --iteration v1.0
    python .workflow/scripts/check_links.py --iteration v1.0 --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

THIS = Path(__file__).resolve()
sys.path.insert(0, str(THIS.parents[1]))

from workflow import discover_iteration, load_artifacts  # noqa: E402

# Matches [label](path) — path may include anchor #…; capture group 1 = path
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
EXTERNAL_RE = re.compile(r"^(?:https?://|mailto:|#)")


def extract_local_links(text: str) -> list[tuple[str, str]]:
    """Return list of (link_target, raw) for every local markdown link."""
    out = []
    for m in LINK_RE.finditer(text):
        target = m.group(1).strip()
        # strip anchor
        target = target.split("#", 1)[0]
        if not target:
            continue
        if EXTERNAL_RE.match(target):
            continue
        out.append((target, m.group(1)))
    return out


def check(iteration: str) -> dict:
    artifacts = load_artifacts(iteration)
    errors: list[dict] = []
    warnings: list[dict] = []
    scanned = 0
    link_count = 0
    for item in artifacts:
        if not item.path.endswith(".md"):
            continue
        scanned += 1
        path = THIS.parents[2] / item.path
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for target, raw in extract_local_links(text):
            link_count += 1
            # Resolve relative to source file's directory
            resolved = (path.parent / target).resolve()
            # Allow reference to a file in the same iteration under different
            # naming (e.g. .md ↔ -README.md); try the basename too.
            if not resolved.exists():
                # Heuristic — try replacing "v1.0" with "v1" or vice versa
                candidates = []
                alt = target.replace("v1.0-", "v1-")
                if alt != target:
                    candidates.append((path.parent / alt).resolve())
                alt2 = target.replace("v1-", "v1.0-")
                if alt2 != target:
                    candidates.append((path.parent / alt2).resolve())
                if not any(c.exists() for c in candidates):
                    errors.append({
                        "source": item.path,
                        "target": target,
                        "raw_link": raw,
                    })
                else:
                    warnings.append({
                        "source": item.path,
                        "target": target,
                        "hint": "resolved via v1 ↔ v1.0 name variant",
                    })
    return {
        "iteration": iteration,
        "files_scanned": scanned,
        "links_total":link_count,
        "errors": errors,
        "warnings": warnings,
    }


def render_text(data: dict) -> str:
    out = [f"Link Validation — iteration {data['iteration']}", ""]
    out.append(f"  Scanned {data['files_scanned']} .md file(s); checked {data['links_total']} local link(s)")
    if data["errors"]:
        out.append(f"  ❌ {len(data['errors'])} broken link(s):")
        for e in data["errors"]:
            out.append(f"    - {e['source']}")
            out.append(f"        → {e['target']}  (link: {e['raw_link']})")
    if data["warnings"]:
        out.append(f"  ⚠  {len(data['warnings'])} warning(s):")
        for w in data["warnings"]:
            out.append(f"    - {w['source']} → {w['target']}  ({w['hint']})")
    if not data["errors"] and not data["warnings"]:
        out.append("  ✅ all local links resolve")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iteration", default=discover_iteration())
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args()
    data = check(args.iteration)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(render_text(data))
    return 0 if not data["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())