import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


import sys

sys.path.insert(0, str(Path(__file__).parents[1]))
import workflow


class WorkflowTests(unittest.TestCase):
    def make_repo(self, draft=False):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / ".workflow" / "dashboard").mkdir(parents=True)
        (root / ".workflow" / "dashboard" / "template.html").write_text(
            "<html><body><main>__DASHBOARD_FALLBACK__</main><script>const data = __DASHBOARD_DATA__;</script></body></html>",
            encoding="utf-8",
        )
        (root / "baseline").mkdir()
        for name in ["01-product-vision", "02-product-charter", "03-tech-stack-decision", "04-glossary"]:
            status = "draft" if draft else "Approved"
            (root / "baseline" / f"{name}.md").write_text(f"---\nstatus: {status}\n---\n# {name}\n", encoding="utf-8")
        plan = root / "iteration" / "v1" / "03-planning"
        plan.mkdir(parents=True)
        (plan / "v1-task-plan-dag.md").write_text(
            "---\nstatus: Approved\n---\n# Plan\n## TASK-API-010\nGoal\nRelated: API-PROJ-001 AC-001\n",
            encoding="utf-8",
        )
        api = root / "iteration" / "v1" / "02-design"
        api.mkdir(parents=True)
        (api / "v1-api-spec.md").write_text(
            "---\nstatus: Approved\n---\n# API\n## API-PROJ-001\nRelated AC-001\n", encoding="utf-8"
        )
        product = root / "iteration" / "v1" / "01-product"
        product.mkdir(parents=True)
        (product / "v1-requirement.md").write_text("---\nstatus: Approved\n---\n# Req\n## AC-001\n", encoding="utf-8")
        return temp, root

    def test_parse_frontmatter_and_gate(self):
        temp, root = self.make_repo(draft=True)
        try:
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.assertNotEqual(workflow.validate("v1", "01-product"), 0)
        finally:
            temp.cleanup()

    def test_index_writes_traceability_and_hashes(self):
        temp, root = self.make_repo()
        try:
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.assertEqual(workflow.index("v1"), 0)
                trace = json.loads((root / ".workflow" / "traceability.json").read_text(encoding="utf-8"))
                self.assertTrue(any(node["id"] == "API-PROJ-001" for node in trace["nodes"]))
                self.assertTrue((root / ".workflow" / "cache" / "index.json").exists())
        finally:
            temp.cleanup()

    def test_context_pack_reuses_cache(self):
        temp, root = self.make_repo()
        try:
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.assertEqual(workflow.context_pack("v1", "TASK-API-010"), 0)
                output = root / ".workflow" / "context-packs" / "v1-TASK-API-010.md"
                first = output.stat().st_mtime_ns
                self.assertEqual(workflow.context_pack("v1", "TASK-API-010"), 0)
                self.assertEqual(first, output.stat().st_mtime_ns)
                self.assertIn("API-PROJ-001", output.read_text(encoding="utf-8"))
        finally:
            temp.cleanup()

    def test_dashboard_contains_stage_and_task_data(self):
        temp, root = self.make_repo()
        try:
            (root / ".workflow" / "task-runs").mkdir(parents=True)
            (root / ".workflow" / "task-runs" / "v1-TASK-API-010.json").write_text(
                json.dumps({"iteration": "v1", "task_id": "TASK-API-010", "result": "succeeded"}),
                encoding="utf-8",
            )
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.assertEqual(workflow.dashboard("v1"), 0)
                html = (root / ".workflow" / "dashboard" / "index.html").read_text(encoding="utf-8")
                self.assertIn("TASK-API-010", html)
                self.assertIn("01-product", html)
                self.assertIn("data-dashboard-fallback", html)
        finally:
            temp.cleanup()

    def test_task_finished_records_result_and_refreshes_dashboard(self):
        temp, root = self.make_repo()
        try:
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                # default path: cheap append-only, no dashboard re-render
                self.assertEqual(workflow.task_finished("v1", "TASK-API-010", "succeeded"), 0)
                record = json.loads((root / ".workflow" / "task-runs" / "v1-TASK-API-010.json").read_text(encoding="utf-8"))
                self.assertEqual(record["result"], "succeeded")
                # dashboard should NOT have been written in the default path
                self.assertFalse((root / ".workflow" / "dashboard" / "index.html").exists())
                # opt-in: --refresh-dashboard flag triggers dashboard re-render
                self.assertEqual(
                    workflow.task_finished("v1", "TASK-API-010", "succeeded", refresh_dashboard=True),
                    0,
                )
                self.assertTrue((root / ".workflow" / "dashboard" / "index.html").exists())
        finally:
            temp.cleanup()

    def test_readme_freshness_check_at_rc_stage(self):
        """Stage 06 must verify README references current state.

        Stage 06 must block when README is missing or does not mention
        current skills / scripts. Earlier stages must not trigger this
        check (regression: D3 must be RC-stage-scoped only).
        """
        temp, root = self.make_repo()
        try:
            # Create a stale-state repo: README missing a current skill.
            skills = root / ".agents" / "skills"
            skills.mkdir(parents=True)
            (skills / "stale-skill").mkdir()
            (skills / "stale-skill" / "SKILL.md").write_text(
                "---\nname: stale-skill\n---\n# stale\n", encoding="utf-8"
            )
            # No README.md present in the temp repo
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                # Direct unit test of check_readme_freshness — bypasses
                # upstream gate noise so we isolate the freshness rule.
                errors: list[str] = []
                workflow.check_readme_freshness("v1", errors)
                self.assertTrue(
                    any("README.md" in e for e in errors),
                    msg=f"freshness check did not flag missing README; errors={errors}",
                )
                self.assertTrue(
                    any("stale-skill" in e for e in errors),
                    msg=f"freshness check did not flag missing skill; errors={errors}",
                )
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
