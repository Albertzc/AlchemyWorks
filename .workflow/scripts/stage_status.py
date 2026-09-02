"""Stage status reporter — answers 'can we move to the next stage?' without LLM.

Usage:
    python .workflow/scripts/stage_status.py --iteration v1.0
    python .workflow/scripts/stage_status.py --iteration v1.0 --json

Exit code: 0 if all stages Approved and overall gate PASS; 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

THIS = Path(__file__).resolve()
sys.path.insert(0, str(THIS.parents[1]))

from workflow import (  # noqa: E402
    STAGES,
    discover_iteration,
    gate_code,
    load_artifacts,
)


def collect(iteration: str) -> dict:
    artifacts = load_artifacts(iteration)
    by_stage: dict[str, list[dict]] = {s: [] for s in ["00-baseline", *STAGES]}
    for item in artifacts:
        by_stage[item.stage].append({
            "path": item.path,
            "status": item.status,
            "lines": item.lines,
            "sha256_short": item.sha256[:12],
        })
    gate_ok = gate_code(iteration) == 0
    return {"iteration": iteration, "gate": "passed" if gate_ok else "blocked", "stages": by_stage}


def render_text(data: dict) -> str:
    out = [f"Stage Status Report — iteration {data['iteration']}", ""]
    for stage, items in data["stages"].items():
        if not items:
            out.append(f"  {stage:<26}  (empty)")
            continue
        approved = sum(1 for i in items if i["status"] == "Approved")
        draft = sum(1 for i in items if i["status"] == "draft")
        unknown = sum(1 for i in items if i["status"] not in {"Approved", "draft"})
        total = len(items)
        if approved == total:
            mark, label = "✅", "approved"
        elif unknown > 0:
            mark, label = "❌", f"{unknown} unknown"
        elif draft > 0:
            mark, label = "⚠️ ", f"{draft} draft"
        else:
            mark, label = "❌", "blocked"
        out.append(f"  {mark} {stage:<24}  ({approved}/{total} Approved, {label})")
        for it in items:
            tag = "" if it["status"] == "Approved" else "  ⚠"
            out.append(f"     {tag} {it['status']:<10} {it['path']}  ({it['lines']} lines)")
    out.append("")
    gate = data["gate"]
    decision = "safe to proceed / archive" if gate == "passed" else "DO NOT advance; fix blockers first"
    out.append(f"  Overall gate: {gate}  →  {decision}")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iteration", default=discover_iteration())
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args()
    data = collect(args.iteration)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(render_text(data))
    return 0 if data["gate"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())