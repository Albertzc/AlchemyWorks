"""Stable-ID registry — answers 'what's the next available FR-NNN?' without LLM.

Walks all artifacts under iteration/{ver}/ and groups every stable ID
(FR/FS/BR/NFR/API/TBL/TASK/AC/ISSUE) by prefix. Reports the highest
issued number per prefix and the next available number.

Usage:
    python .workflow/scripts/id_registry.py --iteration v1.0
    python .workflow/scripts/id_registry.py --iteration v1.0 --prefix FR
    python .workflow/scripts/id_registry.py --iteration v1.0 --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

THIS = Path(__file__).resolve()
sys.path.insert(0, str(THIS.parents[1]))

from workflow import ID_RE, discover_iteration, is_real_id, load_artifacts  # noqa: E402

PREFIXES = ("FR", "FS", "BR", "NFR", "API", "TBL", "TASK", "AC", "ISSUE")


def collect(iteration: str) -> dict[str, dict]:
    artifacts = load_artifacts(iteration)
    by_prefix: dict[str, set[int]] = {p: set() for p in PREFIXES}
    for item in artifacts:
        text = (THIS.parents[2] / item.path).read_text(encoding="utf-8")
        for m in ID_RE.findall(text):
            if not is_real_id(m):
                continue
            prefix, _, rest = m.partition("-")
            if prefix not in by_prefix:
                continue
            # Last segment must be the sequence number; preceding segments are
            # the namespace (e.g. TASK-API-010 → prefix=TASK, ns=API, num=10).
            parts = rest.split("-")
            if not parts:
                continue
            num_str = parts[-1]
            if not num_str.isdigit():
                continue
            by_prefix[prefix].add(int(num_str))
    summary: dict[str, dict] = {}
    for prefix, nums in by_prefix.items():
        if not nums:
            summary[prefix] = {"max": None, "next": 1, "count": 0, "gaps": []}
            continue
        sorted_nums = sorted(nums)
        max_n = sorted_nums[-1]
        expected = set(range(1, max_n + 1))
        gaps = sorted(expected - nums)
        summary[prefix] = {
            "max": max_n,
            "next": max_n + 1,
            "count": len(nums),
            "gaps": gaps[:10],  # cap to first 10 gaps to keep output readable
        }
    return summary


def render_text(data: dict[str, dict], prefixes: tuple[str, ...]) -> str:
    out = ["StableID Registry", ""]
    out.append(f"  {'PREFIX':<8} {'COUNT':>6} {'MAX':>5} {'NEXT':>6}  GAPS (≤10)")
    out.append("  " + "-" * 60)
    for p in prefixes:
        d = data[p]
        if d["max"] is None:
            out.append(f"  {p:<8} {0:>6} {'—':>5} {1:>6}  (none issued)")
            continue
        gap_str = ",".join(str(g) for g in d["gaps"]) if d["gaps"] else "—"
        out.append(f"  {p:<8} {d['count']:>6} {d['max']:>5} {d['next']:>6}  {gap_str}")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iteration", default=discover_iteration())
    parser.add_argument("--prefix", choices=PREFIXES, help="filter to one prefix")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args()
    data = collect(args.iteration)
    prefixes = (args.prefix,) if args.prefix else PREFIXES
    if args.json:
        print(json.dumps({p: data[p] for p in prefixes}, ensure_ascii=False, indent=2))
    else:
        print(render_text(data, prefixes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())