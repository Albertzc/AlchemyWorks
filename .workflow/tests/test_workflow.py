import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch


import sys

sys.path.insert(0, str(Path(__file__).parents[1]))
import workflow


class WorkflowTests(unittest.TestCase):
    def test_generated_timestamps_use_client_local_timezone(self):
        timestamp = workflow.now()
        parsed = datetime.fromisoformat(timestamp)
        self.assertIsNotNone(parsed.tzinfo)
        self.assertEqual(parsed.utcoffset(), datetime.now().astimezone().utcoffset())
        self.assertRegex(workflow.local_filename_timestamp(), r"\d{8}T\d{6}\.\d{6}[+-]\d{4}$")

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

    def add_approved(self, root, relative: str, body: str = "# artifact\n"):
        path = root / relative
        if path.exists():
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() == ".html":
            path.write_text("<!-- status: Approved -->\n" + body, encoding="utf-8")
        else:
            path.write_text("---\nstatus: Approved\n---\n" + body, encoding="utf-8")

    def add_full_chain_after_fixture(self, root):
        for relative in [
            "iteration/v1/01-product/v1-prototype.html",
            "iteration/v1/02-design/v1-architecture-design.md",
            "iteration/v1/02-design/v1-database-dictionary.md",
            "iteration/v1/03-planning/v1-validation-plan.md",
            "iteration/v1/04-implementation/v1-source-code.md",
            "iteration/v1/04-implementation/v1-test-results.md",
            "iteration/v1/04-implementation/v1-issue-fixes.md",
        ]:
            self.add_approved(root, relative)

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
                checkpoint = json.loads((root / ".workflow" / "current-state.json").read_text(encoding="utf-8"))
                self.assertEqual(checkpoint["iteration"], "v1")
                self.assertEqual(checkpoint["current_stage"]["name"], "01-product")
                self.assertTrue(checkpoint["source_fingerprint"])
                # Per S2 audit, cache/index.json is no longer written (it was
                # never read by any consumer; manifest.yaml carries the same
                # per-artifact hashes).
                self.assertFalse((root / ".workflow" / "cache" / "index.json").exists())
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
                checkpoint = json.loads((root / ".workflow" / "current-state.json").read_text(encoding="utf-8"))
                self.assertEqual(checkpoint["active_context"]["task_id"], "TASK-API-010")
                self.assertIn("v1-TASK-API-010.md", checkpoint["active_context"]["path"])
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
                self.assertEqual(workflow.context_pack("v1", "TASK-API-010"), 0)
                # default path: cheap append-only, no dashboard re-render
                self.assertEqual(workflow.task_finished("v1", "TASK-API-010", "succeeded"), 0)
                record = json.loads((root / ".workflow" / "task-runs" / "v1-TASK-API-010.json").read_text(encoding="utf-8"))
                self.assertEqual(record["result"], "succeeded")
                self.assertEqual(record["project_gate_status"], "blocked")
                checkpoint = json.loads((root / ".workflow" / "current-state.json").read_text(encoding="utf-8"))
                self.assertEqual(checkpoint["last_task"]["task_id"], "TASK-API-010")
                history = list((root / ".workflow" / "task-runs" / "history").glob("*.json"))
                self.assertEqual(len(history), 1)
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

    def test_compact_context_pack_is_bounded(self):
        temp, root = self.make_repo()
        try:
            requirement = root / "iteration" / "v1" / "01-product" / "v1-requirement.md"
            requirement.write_text(
                "---\nstatus: Approved\n---\n# Req\n## AC-001\n" + ("API-PROJ-001 repeated contract text. " * 200),
                encoding="utf-8",
            )
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.assertEqual(workflow.context_pack("v1", "TASK-API-010", compact=True, max_chars=1200), 0)
                output = root / ".workflow" / "context-packs" / "v1-TASK-API-010.md"
                text = output.read_text(encoding="utf-8")
                self.assertLessEqual(len(text), 1200)
                self.assertIn("TRUNCATED locally", text)
        finally:
            temp.cleanup()

    def test_resume_reports_no_active_iteration(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "iteration" / "raw-requirement").mkdir(parents=True)
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                payload = workflow.resume_data()
            self.assertEqual(payload["status"], "NO_ACTIVE_ITERATION")
            self.assertIsNone(payload["iteration"])

    def test_preflight_and_review_pack_are_local_summaries(self):
        temp, root = self.make_repo()
        try:
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                dag = workflow.task_dag_report("v1")
                coverage = workflow.coverage_report("v1")
                self.assertEqual(dag["status"], "passed")
                self.assertEqual(coverage["status"], "warning")
                self.assertEqual(workflow.review_pack("v1", "03-planning", as_json=True), 1)
        finally:
            temp.cleanup()

    def test_task_lookup_does_not_accept_prefix_match(self):
        temp, root = self.make_repo()
        try:
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                with self.assertRaises(ValueError):
                    workflow.find_task("v1", "TASK-API-01", workflow.load_artifacts("v1"))
        finally:
            temp.cleanup()

    def test_readme_freshness_check_at_rc_stage(self):
        """The final review/release stage must verify README freshness.

        The final stage must block when README is missing or does not mention
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


    def test_task_finished_rejects_unknown_task_id(self):
        """Regression for B1: task-finished must verify the task is in the plan.

        Without find_task() being called in the default path, a typo'd or
        stale task_id silently wrote a phantom succeeded/failed/blocked
        record into .workflow/task-runs/ and polluted the dashboard.
        """
        temp, root = self.make_repo()
        try:
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                with self.assertRaises(ValueError) as ctx:
                    workflow.task_finished("v1", "TASK-NOPE", "succeeded")
                self.assertIn("task not found", str(ctx.exception))
                # No phantom record should be written to task-runs/.
                runs = root / ".workflow" / "task-runs"
                self.assertFalse((runs / "v1-TASK-NOPE.json").exists())
        finally:
            temp.cleanup()

    def test_validate_stage_05_requires_review_release_file(self):
        """The combined final stage requires its Approved review/release record."""
        temp, root = self.make_repo()
        try:
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.add_full_chain_after_fixture(root)
                import io, contextlib
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = workflow.validate("v1", "05-review-release")
                self.assertEqual(rc, 1)
                output = buf.getvalue()
                self.assertIn("v1-review-release.md", output)
                final_dir = root / "iteration" / "v1" / "05-review-release"
                final_dir.mkdir(parents=True, exist_ok=True)
                (final_dir / "v1-review-release.md").write_text(
                    "---\nstatus: Approved\n---\n# review release\n", encoding="utf-8"
                )
                (root / "README.md").write_text("# v1\n", encoding="utf-8")
                buf2 = io.StringIO()
                with contextlib.redirect_stdout(buf2):
                    rc = workflow.validate("v1", "05-review-release")
                self.assertEqual(rc, 0, msg=buf2.getvalue())
        finally:
            temp.cleanup()



    def test_validate_stage_04_reports_unknown_task_ids(self):
        """Regression for S4: TASK-IDs in 04 must be defined in 03 plan.

        Previously source-code.md / test-results.md / issue-fixes.md
        could mention TASK-API-999 and the gate stayed green because
        validate() only checked file existence + Approved, not
        cross-artifact ID consistency.
        """
        temp, root = self.make_repo()
        try:
            # Re-make baseline as Approved so the gate noise is minimal
            for name in [
                "01-product-vision", "02-product-charter",
                "03-tech-stack-decision", "04-glossary",
            ]:
                (root / "baseline" / f"{name}.md").write_text(
                    "---\nstatus: Approved\n---\n# body\n", encoding="utf-8"
                )
            # Plan defines TASK-API-001..003 (already in make_repo)
            plan = root / "iteration" / "v1" / "03-planning" / "v1-task-plan-dag.md"
            plan.write_text(
                "---\nstatus: Approved\n---\n# Plan\n## TASK-API-001\n## TASK-API-002\n## TASK-API-003\n",
                encoding="utf-8",
            )
            val = root / "iteration" / "v1" / "03-planning" / "v1-validation-plan.md"
            val.write_text("---\nstatus: Approved\n---\n# v\n", encoding="utf-8")

            # Build 04-implementation with a known + an unknown TASK ref
            impl = root / "iteration" / "v1" / "04-implementation"
            impl.mkdir(exist_ok=True)
            (impl / "v1-source-code.md").write_text(
                "---\nstatus: Approved\n---\n# sc\nRef TASK-API-001 and TASK-API-999.\n",
                encoding="utf-8",
            )
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                import io, contextlib
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = workflow.validate("v1", "04-implementation")
                output = buf.getvalue()
                self.assertEqual(rc, 1)
                self.assertIn("TASK-API-999", output)
                self.assertIn("not defined", output)
                self.assertNotIn("TASK-API-001", output)

                # Now fix the reference and the gate should be clean
                (impl / "v1-source-code.md").write_text(
                    "---\nstatus: Approved\n---\n# sc\nRef TASK-API-001, TASK-API-002, and TASK-API-003.\n",
                    encoding="utf-8",
                )
                self.add_full_chain_after_fixture(root)
                buf2 = io.StringIO()
                with contextlib.redirect_stdout(buf2):
                    rc = workflow.validate("v1", "04-implementation")
                self.assertEqual(rc, 0, msg=buf2.getvalue())
        finally:
            temp.cleanup()

    def test_stage_01_requires_product_outputs(self):
        temp, root = self.make_repo()
        try:
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.assertEqual(workflow.validate("v1", "01-product"), 1)
                self.assertIn("iteration/v1/01-product/v1-prototype.html", workflow.required_inputs("v1", "01-product"))
                checkpoint = json.loads((root / ".workflow" / "current-state.json").read_text(encoding="utf-8"))
                self.assertEqual(checkpoint["latest_gate"]["target"], "01-product")
                self.assertEqual(checkpoint["latest_gate"]["result"], "blocked")
        finally:
            temp.cleanup()

    def test_state_refresh_rebuilds_checkpoint_for_requested_iteration(self):
        temp, root = self.make_repo()
        try:
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.assertEqual(workflow.state("v1", refresh=True), 0)
                checkpoint = json.loads((root / ".workflow" / "current-state.json").read_text(encoding="utf-8"))
                self.assertEqual(checkpoint["iteration"], "v1")
                self.assertEqual(checkpoint["current_stage"]["name"], "01-product")
        finally:
            temp.cleanup()

    def test_refresh_runs_standard_document_sync_sequence(self):
        calls = []

        def record_index(iteration):
            calls.append(("index", iteration))
            return 0

        def record_state(iteration, *, refresh=False):
            calls.append(("state", iteration, refresh))
            return 0

        def record_validate(iteration, stage):
            calls.append(("validate", iteration, stage))
            return 0

        with patch.object(workflow, "index", side_effect=record_index), patch.object(
            workflow, "state", side_effect=record_state
        ), patch.object(workflow, "validate", side_effect=record_validate):
            self.assertEqual(workflow.refresh("v1", "01-product"), 0)

        self.assertEqual(
            calls,
            [
                ("index", "v1"),
                ("state", "v1", True),
                ("validate", "v1", "01-product"),
            ],
        )

    def test_refresh_stops_when_index_fails(self):
        with patch.object(workflow, "index", return_value=1) as index_mock, patch.object(
            workflow, "state"
        ) as state_mock, patch.object(workflow, "validate") as validate_mock:
            self.assertEqual(workflow.refresh("v1", "01-product"), 1)

        index_mock.assert_called_once_with("v1")
        state_mock.assert_not_called()
        validate_mock.assert_not_called()

    def test_state_rebuilds_when_artifact_fingerprint_changes(self):
        temp, root = self.make_repo()
        try:
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.assertEqual(workflow.state("v1", refresh=True), 0)
                before = json.loads((root / ".workflow" / "current-state.json").read_text(encoding="utf-8"))
                requirement = root / "iteration" / "v1" / "01-product" / "v1-requirement.md"
                requirement.write_text(requirement.read_text(encoding="utf-8") + "\nUpdated\n", encoding="utf-8")
                self.assertEqual(workflow.state("v1"), 0)
                after = json.loads((root / ".workflow" / "current-state.json").read_text(encoding="utf-8"))
                self.assertNotEqual(before["source_fingerprint"], after["source_fingerprint"])
        finally:
            temp.cleanup()

    def test_requirement_route_uses_baseline_when_only_readme_exists(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "baseline").mkdir()
            (root / "baseline" / "README.md").write_text("# Baseline\n", encoding="utf-8")
            (root / ".workflow").mkdir()
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                route = workflow.requirement_route()
            self.assertEqual(route["mode"], "baseline")
            self.assertEqual(route["raw_requirement_dir"], "baseline/raw-requirement")

    def test_requirement_route_keeps_baseline_mode_when_only_raw_input_exists(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "baseline" / "raw-requirement").mkdir(parents=True)
            (root / "baseline" / "raw-requirement" / "customer-note.txt").write_text(
                "用户原始需求", encoding="utf-8"
            )
            (root / ".workflow").mkdir()
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                route = workflow.requirement_route()
            self.assertEqual(route["mode"], "baseline")

    def test_requirement_route_prefers_manifest_iteration(self):
        temp, root = self.make_repo()
        try:
            (root / ".workflow" / "manifest.yaml").write_text(
                "schema_version: '1'\niteration: 'v1.1'\n", encoding="utf-8"
            )
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                route = workflow.requirement_route()
            self.assertEqual(route["mode"], "iteration")
            self.assertEqual(route["iteration"], "v1.1")
            self.assertEqual(route["version_source"], "manifest")
            self.assertEqual(route["raw_requirement_dir"], "iteration/raw-requirement")
            self.assertEqual(route["raw_requirement_access"], "user-owned-read-only")
        finally:
            temp.cleanup()

    def test_init_creates_project_intake_directories(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.assertEqual(workflow.init_project(), 0)
            self.assertTrue((root / "baseline" / "raw-requirement").is_dir())
            self.assertTrue((root / "iteration").is_dir())
            self.assertTrue((root / "iteration" / "raw-requirement").is_dir())
            self.assertTrue((root / "workspace").is_dir())
            self.assertTrue((root / "baseline" / "raw-requirement" / "README.md").is_file())
            self.assertTrue((root / "iteration" / "README.md").is_file())
            self.assertTrue((root / "workspace" / "README.md").is_file())
            self.assertTrue((root / "iteration" / "raw-requirement" / "README.md").is_file())

    def test_init_version_requires_baseline_then_creates_skeleton(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "baseline").mkdir()
            (root / "iteration").mkdir()
            (root / ".workflow").mkdir()
            for name in ["01-product-vision", "02-product-charter", "03-tech-stack-decision", "04-glossary"]:
                (root / "baseline" / f"{name}.md").write_text(
                    "---\nstatus: Approved\n---\n# baseline\n", encoding="utf-8"
                )
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.assertEqual(workflow.init_version(), 0)
            for stage in workflow.STAGES:
                self.assertTrue((root / "iteration" / "v1.0" / stage).is_dir())
            self.assertFalse((root / "iteration" / "v1.0" / "00-raw-requirement").exists())

    def test_init_version_refuses_unapproved_baseline(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "baseline").mkdir()
            (root / "iteration").mkdir()
            (root / ".workflow").mkdir()
            for name in ["01-product-vision", "02-product-charter", "03-tech-stack-decision", "04-glossary"]:
                (root / "baseline" / f"{name}.md").write_text(
                    "---\nstatus: draft\n---\n# baseline\n", encoding="utf-8"
                )
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                with self.assertRaises(ValueError):
                    workflow.init_version()
            self.assertFalse((root / "iteration" / "v1.0").exists())

    def test_frontmatter_supports_multiline_html_and_scopes_change_set(self):
        html = "<!--\nstatus: Approved\nowner: QA\n-->\n<html></html>"
        values, body = workflow.parse_frontmatter(html)
        self.assertEqual(values["status"], "Approved")
        self.assertEqual(values["owner"], "QA")
        self.assertEqual(body, "<html></html>")
        text = (
            "---\nchange_set:\n  deprecated: [FR-001]\n---\n"
            "change_set:\n  deprecated: [FR-999]\n"
        )
        self.assertEqual(workflow.parse_change_set(text)["deprecated"], ["FR-001"])

    def test_main_normalizes_short_iteration_literal(self):
        """Regression for S1: --iteration v1 must resolve to v1.0 paths.

        Previously the CLI accepted v1 as a legacy alias for v1.0
        but did not normalize the iteration literal before path
        lookups. Users got misleading 'missing input' errors when
        only iteration/v1.0/ existed on disk.
        """
        temp, root = self.make_repo()
        try:
            # The CLI must normalize v1 -> v1.0 before any path lookup.
            # Use a real v1.0 directory so the test distinguishes CLI
            # normalization from merely accepting the literal.
            import io, contextlib
            legacy = root / "iteration" / "v1"
            canonical = root / "iteration" / "v1.0"
            canonical.parent.mkdir(parents=True, exist_ok=True)
            legacy.rename(canonical)
            with patch.object(workflow, "ROOT", root), patch.object(
                workflow, "WORKFLOW_DIR", root / ".workflow"
            ), patch.object(workflow, "discover_iteration", return_value="v1.0"):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    workflow.main(["validate", "--iteration", "v1", "--stage", "03-planning"])
            self.assertIn("iteration=v1.0", output.getvalue())
            self.assertNotIn("iteration=v1/", output.getvalue())
            major, minor = workflow.iteration_number("v1")
            self.assertEqual(f"v{major}.{minor}", "v1.0")
            major, minor = workflow.iteration_number("v2")
            self.assertEqual(f"v{major}.{minor}", "v2.0")
            major, minor = workflow.iteration_number("v1.3")
            self.assertEqual(f"v{major}.{minor}", "v1.3")
        finally:
            temp.cleanup()


class DiffVersionsTests(unittest.TestCase):
    """End-to-end diff: a synthetic two-iteration repo driven through a
    subprocess call to the real script. Exercises the regex parser for
    `change_set.deprecated`, which the plain workflow pytest harness
    does not otherwise cover.
    """

    def _make_two_iter_repo(self, tmp: Path) -> tuple[Path, Path]:
        """Build a temp repo with v1.0 + v1.1, then return (sandbox, repo)."""
        sandbox = tmp / "sandbox"
        repo = sandbox / "repo"
        (repo / "baseline").mkdir(parents=True)
        (repo / ".workflow" / "dashboard").mkdir(parents=True)
        (repo / ".workflow" / "dashboard" / "template.html").write_text(
            "<x>__DASHBOARD_FALLBACK__</x>", encoding="utf-8"
        )
        for name in [
            "01-product-vision",
            "02-product-charter",
            "03-tech-stack-decision",
            "04-glossary",
        ]:
            (repo / "baseline" / f"{name}.md").write_text(
                f"---\nstatus: Approved\n---\n# {name}\n", encoding="utf-8"
            )

        v10 = repo / "iteration" / "v1.0" / "01-product"
        v10.mkdir(parents=True)
        (v10 / "v1.0-requirement.md").write_text(
            "---\nstatus: Approved\nproduct_name: demo\n---\n# v1.0\nFR-001 TASK-API-001\n",
            encoding="utf-8",
        )
        (v10 / "v1.0-feature-specification.md").write_text(
            "---\nstatus: Approved\n---\n# FS\nFR-003\n",
            encoding="utf-8",
        )

        v11 = repo / "iteration" / "v1.1" / "01-product"
        v11.mkdir(parents=True)
        (v11 / "v1.1-requirement.md").write_text(
            "---\n"
            "status: Approved\n"
            "product_name: demo\n"
            "product_version: v1.1\n"
            "change_set:\n"
            "  added: [FR-005]\n"
            "  modified: [TASK-API-001]\n"
            "  deprecated: [FR-003]\n"
            "---\n"
            "# v1.1\nFR-001 FR-005 TASK-API-001\n",
            encoding="utf-8",
        )

        # Copy the real workflow + the diff script into the sandbox so the
        # script's `from workflow import` resolves correctly under cwd.
        shutil.copytree(
            Path(__file__).resolve().parents[1],
            repo / ".workflow",
            dirs_exist_ok=True,
        )
        shutil.copy(
            Path(__file__).resolve().parents[1] / "scripts" / "diff_versions.py",
            repo / ".workflow" / "scripts" / "diff_versions.py",
        )
        return sandbox, repo

    def test_diff_marks_deprecated(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            sandbox, repo = self._make_two_iter_repo(tmp)
            try:
                result = subprocess.run(
                    [sys.executable, ".workflow/scripts/diff_versions.py",
                     "--from", "v1.0", "--to", "v1.1", "--json"],
                    cwd=repo, capture_output=True, text=True,
                )
                self.assertEqual(
                    result.returncode, 2,
                    msg=(
                        f"exit={result.returncode}\n"
                        f"stdout={result.stdout!r}\n"
                        f"stderr={result.stderr!r}"
                    ),
                )
                payload = json.loads(result.stdout)
                self.assertEqual(payload["deprecated"], ["FR-003"])
                self.assertIn("FR-005", payload["added"])
                # FR-001 exists in both but in different files → modified
                self.assertTrue(
                    any(m["id"] == "FR-001" for m in payload["modified"]),
                    msg=f"expected FR-001 in modified, got {payload['modified']!r}",
                )
            finally:
                shutil.rmtree(sandbox, ignore_errors=True)

    def test_diff_reads_archived_source_iteration(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            sandbox, repo = self._make_two_iter_repo(tmp)
            try:
                archive = repo / "iteration" / "archive"
                archive.mkdir(parents=True)
                shutil.move(str(repo / "iteration" / "v1.0"), str(archive / "v1.0"))
                result = subprocess.run(
                    [sys.executable, ".workflow/scripts/diff_versions.py",
                     "--from", "v1.0", "--to", "v1.1", "--json"],
                    cwd=repo, capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 2, msg=result.stderr)
                payload = json.loads(result.stdout)
                self.assertNotIn("FR-001", payload["added"])
                self.assertEqual(payload["deprecated"], ["FR-003"])
            finally:
                shutil.rmtree(sandbox, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
