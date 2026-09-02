"""ID lookup — answers 'where does FR-005 appear in artifacts?' without LLM.

Reads .workflow/traceability.json (already maintained by `index`) and
returns every artifact path + line range that mentions the requested ID.

Usage:
    python .workflow/scripts/query_id.py --id FR-005 --iteration v1.0
    python .workflow/scripts/query_id.py --id FR-005 --iteration v1.0 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

THIS = Path(__file__).resolve()
sys.path.insert(0, str(THIS.parents[1]))

from workflow import discover_iteration  # noqa: E402

TRACEABILITY = THIS.parents[1] / "traceability.json"


def load_edges(iteration: str) -> dict[str, list[dict]]:
    if not TRACEABILITY.exists():
        return {}
    data = json.loads(TRACEABILITY.read_text(encoding="utf-8"))
    if data.get("iteration") != iteration:
        return {}
    nodes = {n["id"]: n for n in data.get("nodes", [])}
    return nodes


def query(iteration: str, identifier: str) -> dict:
    nodes = load_edges(iteration)
    node = nodes.get(identifier)
    if not node:
        return {"id": identifier, "found": False, "artifacts": [], "edges_count": 0}
    artifacts = sorted(set(node.get("artifacts", [])))
    # Count co-occurrence edges (from/where this ID is the primary)
    edges_count = sum(
        1 for e in json.loads(TRACEABILITY.read_text(encoding="utf-8")).get("edges", [])
        if e.get("from") == identifier
    )
    return {
        "id": identifier,
        "found": True,
        "artifacts": artifacts,
        "edges_count": edges_count,
    }


def render_text(data: dict) -> str:
    if not data["found"]:
        return f"  ID {data['id']} not found in traceability graph."
    out = [f"  ID {data['id']} — found in {len(data['artifacts'])} artifact(s); {data['edges_count']} co-occurrence edge(s)"]
    for path in data["artifacts"]:
        out.append(f"    - {path}")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iteration", default=discover_iteration())
    parser.add_argument("--id", required=True, help="stable ID to query (e.g. FR-005, TASK-API-010)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args()
    data = query(args.iteration, args.id)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(render_text(data))
    return 0 if data["found"] else 1


if __name__ == "__main__":
    raise SystemExit(main())