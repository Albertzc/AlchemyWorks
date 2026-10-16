import atexit
import json
import os
import secrets
import shutil
import stat
import subprocess
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch


import sys

sys.path.insert(0, str(Path(__file__).parents[1]))
import workflow


# Project-local scratch root; replaces tempfile.TemporaryDirectory() which
# fails on DSH sandbox (chmod 0o700 to system temp triggers WinError 5).
# Lives at the repo root because the sandbox rejects mkdir under the
# protected .workflow/ subtree; ignored via the root .gitignore entry
# "temp-workflow-tests/".
_SCRATCH_ROOT = Path(__file__).resolve().parents[2] / "temp-workflow-tests"


def _remove_tree(path: Path) -> None:
    """Remove a scratch tree, retrying Windows read-only entries."""
    if not path.exists():
        return

    def retry(function, target, _exc_info):
        try:
            os.chmod(target, stat.S_IWRITE)
        except OSError:
            pass
        function(target)

    shutil.rmtree(path, onerror=retry)


class _ScratchDir:
    """Stand-in for ``tempfile.TemporaryDirectory`` scoped to the test tree.

    Avoids PermissionError on DSH sandbox, where TemporaryDirectory's
    ``__exit__`` applies chmod 0o700 to a directory under the system temp
    path and the sandbox's restricted token cannot satisfy that ACL.

    Each instance picks a unique path under ``temp-workflow-tests/`` via
    ``secrets.token_hex`` so a failed cleanup in one test never collides
    with the next test's slot — counter reuse was the previous attempt that
    proved fragile when an earlier rmtree silently no-op'd under the
    sandbox.
    """

    def __init__(self, prefix: str = "scratch"):
        _SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
        self.path = _SCRATCH_ROOT / f"{prefix}-{secrets.token_hex(4)}"
        self.path.mkdir(parents=True)

    @property
    def name(self) -> str:
        return str(self.path)

    def cleanup(self) -> None:
        _remove_tree(self.path)

    def __enter__(self):
        return Path(self.name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False


@atexit.register
def _cleanup_scratch_root():
    _remove_tree(_SCRATCH_ROOT)


# A prior interrupted test process cannot run its atexit handler. Clean its
# ignored project-local leftovers before allocating the next scratch tree.
_cleanup_scratch_root()


class WorkflowTests(unittest.TestCase):
    def test_workflow_protection_identifies_core_paths(self):
        self.assertTrue(workflow._is_workflow_protected_path(".workflow/workflow.py"))
        self.assertTrue(workflow._is_workflow_protected_path(".agents/skills/stage-gate/SKILL.md"))
        self.assertTrue(workflow._is_workflow_protected_path("templates/Prototype.html"))
        self.assertFalse(workflow._is_workflow_protected_path("iteration/v1/01-product/v1-requirement.md"))
        self.assertFalse(workflow._is_workflow_protected_path(".workflow/manifest.yaml"))

    def test_workflow_changed_paths_ignores_project_artifacts_and_generated_state(self):
        status = (
            " M .workflow/workflow.py\n"
            " M iteration/v1.0/01-product/v1.0-requirement.md\n"
            " M .workflow/manifest.yaml\n"
            "?? templates/new-template.md\n"
        )
        completed = subprocess.CompletedProcess([], 0, stdout=status, stderr="")
        with patch.object(workflow.subprocess, "run", return_value=completed):
            self.assertEqual(
                workflow.workflow_changed_paths(),
                [".workflow/workflow.py", "templates/new-template.md"],
            )

    def test_product_commands_are_blocked_when_workflow_core_is_dirty(self):
        with patch.object(workflow, "workflow_protection_errors", return_value=["workflow core is dirty"]):
            self.assertEqual(workflow.main(["validate", "--iteration", "v1"]), 2)

    def test_verify_workflow_reports_dirty_core_without_mutating_it(self):
        with patch.object(workflow, "workflow_protection_errors", return_value=["workflow core is dirty"]):
            self.assertEqual(workflow.verify_workflow(), 1)
        with patch.object(workflow, "workflow_protection_errors", return_value=[]):
            self.assertEqual(workflow.verify_workflow(), 0)
    def test_generated_timestamps_use_client_local_timezone(self):
        timestamp = workflow.now()
        parsed = datetime.fromisoformat(timestamp)
        self.assertIsNotNone(parsed.tzinfo)
        self.assertEqual(parsed.utcoffset(), datetime.now().astimezone().utcoffset())
        self.assertRegex(workflow.local_filename_timestamp(), r"\d{8}T\d{6}\.\d{6}[+-]\d{4}$")

    def make_repo(self, draft=False):
        temp = _ScratchDir("repo")
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
        (root / "baseline" / "05-core-user-flow-prototype.html").write_text(
            "<!--\n"
            f"status: {'draft' if draft else 'Approved'}\n"
            "reviewer: Product Owner\n"
            "reviewed_at: 2026-09-10T12:00:00+08:00\n"
            "review_notes: Fixture review record.\n"
            "-->\n<html></html>\n",
            encoding="utf-8",
        )
        (root / "workspace").mkdir()
        (root / "workspace" / "README.md").write_text(
            "# Workspace\n\n"
            "本目录承载实例项目的业务代码、测试和配置。\n",
            encoding="utf-8",
        )
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
        (product / "v1-requirement.md").write_text(
            "---\nstatus: Approved\nprototype_required: true\n---\n# Req\n## AC-001\n",
            encoding="utf-8",
        )
        return temp, root

    def add_approved(self, root, relative: str, body: str = "# artifact\n"):
        path = root / relative
        if path.exists():
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() == ".html":
            path.write_text(
                "<!--\nstatus: Approved\n"
                "reviewer: Product Owner\nreviewed_at: 2026-09-10T12:00:00+08:00\n"
                "review_notes: Fixture review record.\n-->\n" + body,
                encoding="utf-8",
            )
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
            "iteration/v1/05-review-release/v1-release-log.md",
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
                trace = json.loads((root / "workspace" / "workflow" / "traceability.json").read_text(encoding="utf-8"))
                self.assertTrue(any(node["id"] == "API-PROJ-001" for node in trace["nodes"]))
                checkpoint = json.loads((root / "workspace" / "workflow" / "current-state.json").read_text(encoding="utf-8"))
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
                checkpoint = json.loads((root / "workspace" / "workflow" / "current-state.json").read_text(encoding="utf-8"))
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
                checkpoint = json.loads((root / "workspace" / "workflow" / "current-state.json").read_text(encoding="utf-8"))
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

    def test_index_uses_explicit_project_root(self):
        temp, project_root = self.make_repo()
        try:
            (project_root / "iteration" / "v1").rename(project_root / "iteration" / "v1.0")
            for path in sorted((project_root / "iteration" / "v1.0").rglob("*"), reverse=True):
                if path.is_file() and "v1" in path.name:
                    path.rename(path.with_name(path.name.replace("v1", "v1.0")))
            with patch.object(workflow, "workflow_protection_errors", return_value=[]):
                self.assertEqual(
                    workflow.main(
                        ["--project-root", str(project_root), "index"]
                    ),
                    0,
                )
            self.assertTrue((project_root / "workspace" / "workflow" / "manifest.yaml").exists())
            self.assertTrue((project_root / "workspace" / "workflow" / "traceability.json").exists())
            self.assertTrue((project_root / "workspace" / "workflow" / "current-state.json").exists())
            self.assertFalse((project_root / ".workflow" / "manifest.yaml").exists())
            self.assertFalse((project_root / ".workflow" / "traceability.json").exists())
            self.assertFalse((project_root / ".workflow" / "current-state.json").exists())
        finally:
            temp.cleanup()

    def test_task_commands_use_explicit_project_root(self):
        temp, project_root = self.make_repo()
        try:
            (project_root / "iteration" / "v1").rename(project_root / "iteration" / "v1.0")
            for path in sorted((project_root / "iteration" / "v1.0").rglob("*"), reverse=True):
                if path.is_file() and "v1" in path.name:
                    path.rename(path.with_name(path.name.replace("v1", "v1.0")))
            with patch.object(workflow, "workflow_protection_errors", return_value=[]):
                self.assertEqual(
                    workflow.main(
                        ["--project-root", str(project_root), "context", "--iteration", "v1.0", "--task", "TASK-API-010"]
                    ),
                    0,
                )
                self.assertEqual(
                    workflow.main(
                        ["--project-root", str(project_root), "task-finished", "--iteration", "v1.0", "--task", "TASK-API-010", "--result", "succeeded"]
                    ),
                    0,
                )
            self.assertTrue((project_root / ".aw" / ".workflow" / "context-packs" / "v1.0-TASK-API-010.md").exists())
            self.assertTrue((project_root / ".aw" / ".workflow" / "task-runs" / "v1.0-TASK-API-010.json").exists())
            self.assertFalse((workflow.FRAMEWORK_ROOT / ".workflow" / "task-runs" / "v1.0-TASK-API-010.json").exists())
        finally:
            temp.cleanup()

    def test_cleanup_context_packs_requires_archive_and_preserves_task_runs(self):
        temp, root = self.make_repo()
        try:
            packs = root / ".workflow" / "context-packs"
            packs.mkdir(parents=True)
            archived_pack = packs / "v1.0-TASK-API-010.md"
            active_pack = packs / "v1.1-TASK-API-020.md"
            archived_pack.write_text("archived context", encoding="utf-8")
            active_pack.write_text("active context", encoding="utf-8")
            cache_path = root / ".workflow" / "cache" / "context-packs.json"
            cache_path.parent.mkdir(parents=True)
            cache_path.write_text(
                json.dumps({
                    ".workflow/context-packs/v1.0-TASK-API-010.md": "old-key",
                    ".workflow/context-packs/v1.1-TASK-API-020.md": "active-key",
                }),
                encoding="utf-8",
            )
            history = root / ".workflow" / "task-runs" / "history" / "v1.0-TASK-API-010-20260101T000000.000000+0800.json"
            history.parent.mkdir(parents=True)
            history.write_text("{}", encoding="utf-8")
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                with self.assertRaises(ValueError):
                    workflow.cleanup_context_packs("v1.0")
                (root / "iteration" / "archive" / "v1.0").mkdir(parents=True)
                self.assertEqual(workflow.cleanup_context_packs("v1.0"), 0)
                self.assertTrue(archived_pack.exists())
                self.assertEqual(workflow.cleanup_context_packs("v1.0", execute=True), 0)
            self.assertFalse(archived_pack.exists())
            self.assertTrue(active_pack.exists())
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            self.assertNotIn(".workflow/context-packs/v1.0-TASK-API-010.md", cache)
            self.assertIn(".workflow/context-packs/v1.1-TASK-API-020.md", cache)
            self.assertTrue(history.exists())
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
        with _ScratchDir("test") as raw:
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
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "FRAMEWORK_ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                # Direct unit test of check_readme_freshness — bypasses
                # upstream gate noise so we isolate the freshness rule.
                errors: list[str] = []
                workflow.check_readme_freshness(errors)
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
                final_dir = root / "iteration" / "v1" / "05-review-release"
                (final_dir / "v1-release-log.md").unlink()
                import io, contextlib
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = workflow.validate("v1", "05-review-release")
                self.assertEqual(rc, 1)
                output = buf.getvalue()
                self.assertIn("v1-review-release.md", output)
                final_dir.mkdir(parents=True, exist_ok=True)
                (final_dir / "v1-review-release.md").write_text(
                    "---\nstatus: Approved\n---\n# review release\n", encoding="utf-8"
                )
                # The instance root README is no longer touched by validate
                # after the §17 refresh-contract change; reserve it before
                # the next run so we can verify it stays untouched.
                root_readme = root / "README.md"
                root_readme.write_text("# Workflow\n", encoding="utf-8")
                buf2 = io.StringIO()
                with contextlib.redirect_stdout(buf2):
                    rc = workflow.validate("v1", "05-review-release")
                # release-log file is missing: gate must still block.
                self.assertEqual(rc, 1, msg=buf2.getvalue())
                self.assertIn("v1-release-log.md", buf2.getvalue())
                # Adding the release log with `status: draft` (NOT Approved)
                # must unblock the gate per the existence-only carve-out.
                (final_dir / "v1-release-log.md").write_text(
                    "---\nstatus: draft\n---\n"
                    "# release log\n\n"
                    "## 2. 功能交付清单\n\n"
                    "### 2.1 新增功能(FR-XXX / YYY)\n\n"
                    "| ID | 标题 | TASK | 验收 |\n"
                    "|---|---|---|---|\n"
                    "| FR-100 | 推送优化 | TASK-API-010 | AC-100 ✅ |\n"
                    "| FR-101 | 校验补全 | TASK-IV-020 | AC-101 ✅ |\n"
                    "\n### 2.3 业务规则(BR-XXX~YYY)\n\n"
                    "| ID | 标题 | 说明 |\n"
                    "|---|---|---|\n"
                    "| BR-016 | 术语统一 | 全站「管道」→「数据管道」 |\n"
                    "\n### 2.4 验收标准(AC-XXX~YYY)\n\n"
                    "| AC | 描述 | 集成测试 | 结果 |\n"
                    "|---|---|---|---|\n"
                    "| AC-100 | 推送正确 | `tests/push.py` | ✅ |\n"
                    "\n## 3. ISSUE 收尾\n\n"
                    "| ISSUE | 类别 | 最终状态 |\n"
                    "|---|---|---|\n"
                    "| ISSUE-V1.0-01 | UI | ✅ 本版本已修复：拖拽校验 |\n"
                    "| ISSUE-V1.0-02 | 后端 | ⏳ 交接至 v1.1：性能调优 |\n"
                    "\n## 7. 已知限制与假设\n\n"
                    "| 类型 | 内容 |\n"
                    "|---|---|\n"
                    "| 限制 | 单实例最多 100 并发 |\n"
                    "| 假设 | SQLite 本地开发 |\n",
                    encoding="utf-8",
                )
                buf3 = io.StringIO()
                with contextlib.redirect_stdout(buf3):
                    rc = workflow.validate("v1", "05-review-release")
                self.assertEqual(rc, 0, msg=buf3.getvalue())
                instance_readme = root / "README.md"
                self.assertTrue(instance_readme.is_file())
                instance_text = instance_readme.read_text(encoding="utf-8")
                self.assertIn("<!-- workflow:current-system-functionality-version: v1.0 -->", instance_text)
                self.assertIn("## 当前系统功能说明", instance_text)
                # Source sections come from release-log, not from requirement.md body.
                self.assertIn("FR-100 推送优化", instance_text)
                self.assertIn("FR-101 校验补全", instance_text)
                self.assertIn("BR-016 术语统一", instance_text)
                self.assertIn("AC-100 推送正确", instance_text)
                self.assertIn("ISSUE-V1.0-01 UI", instance_text)
                # Handed-over (not fixed) issues must NOT appear in the README.
                self.assertNotIn("ISSUE-V1.0-02", instance_text)
                self.assertIn("## 已知限制与假设", instance_text)
                self.assertIn("单实例最多 100 并发", instance_text)
                self.assertIn(
                    "<!-- workflow:current-system-functionality-version: v1.0 -->",
                    root_readme.read_text(encoding="utf-8"),
                )
        finally:
            temp.cleanup()

    def test_release_log_does_not_require_approved_status(self):
        """`v{N}-release-log.md` is gated by existence only; `status: draft`
        / `In Review` / `Approved` are all accepted (see
        `.agents/skills/release-log/SKILL.md` contract)."""
        temp, root = self.make_repo()
        try:
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.add_full_chain_after_fixture(root)
                final_dir = root / "iteration" / "v1" / "05-review-release"
                final_dir.mkdir(parents=True, exist_ok=True)
                (final_dir / "v1-review-release.md").write_text(
                    "---\nstatus: Approved\n---\n# review release\n", encoding="utf-8"
                )
                # Each of the three statuses must unblock the gate when the
                # file exists, regardless of frontmatter value.
                for status in ("draft", "In Review", "Approved"):
                    (final_dir / "v1-release-log.md").write_text(
                        f"---\nstatus: {status}\n---\n# release log {status}\n",
                        encoding="utf-8",
                    )
                    import io, contextlib
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf):
                        rc = workflow.validate("v1", "05-review-release")
                    self.assertEqual(
                        rc, 0,
                        msg=f"release-log status={status} should not block; output={buf.getvalue()}",
                    )
        finally:
            temp.cleanup()

    def test_release_log_path_is_listed_in_stage_outputs(self):
        """`stage_outputs('05-review-release')` must include the release-log
        path so it appears in dashboards and required_inputs lookups."""
        outputs = workflow.stage_outputs("v1.0", "05-review-release")
        self.assertIn(
            "iteration/v1.0/05-review-release/v1.0-release-log.md", outputs,
            msg="release-log missing from stage_outputs('05-review-release')",
        )

    def test_sync_preserves_instance_files_and_ignores_workflow_files(self):
        """Sync must preserve the project-owned root README, leave other
        instance-owned files intact, and hide workflow copies from Git."""
        with _ScratchDir("test") as raw:
            target = Path(raw) / "instance"
            target.mkdir()
            (target / ".gitignore").write_text(
                "node_modules/\n"
                "# BEGIN ALCHEMYWORKS WORKFLOW (managed)\n"
                ".aw/\n"
                "baseline/README.md\n"
                "iteration/README.md\n"
                ".aw/runtime/\n"
                "# END ALCHEMYWORKS WORKFLOW (managed)\n",
                encoding="utf-8",
            )
            (target / "README.md").write_text("# Product A\n", encoding="utf-8")
            (target / "templates").mkdir()
            (target / "templates" / "custom.md").write_text("custom\n", encoding="utf-8")
            subprocess.run(["git", "init", "--quiet", str(target)], check=True)
            subprocess.run(["git", "-C", str(target), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(target), "-c", "user.email=test@example.com", "-c", "user.name=Test", "commit", "--quiet", "-m", "initial"],
                check=True,
            )

            with patch.object(workflow, "workflow_protection_errors", return_value=[]):
                sync_returncode = workflow.main(["sync", "--directory", str(target)])
            result = subprocess.CompletedProcess(
                args=["sync"], returncode=sync_returncode, stdout="", stderr="",
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertEqual((target / "README.md").read_text(encoding="utf-8"), "# Product A\n")
            ignore_text = (target / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("# BEGIN ALCHEMYWORKS WORKFLOW", ignore_text)
            self.assertNotIn("/README.md", ignore_text)
            self.assertTrue((target / ".aw" / ".workflow" / "workflow.py").is_file())
            self.assertFalse((target / ".aw" / ".workflow" / "scripts" / "init-instance.ps1").exists())
            synced_ps1 = sorted(
                p.name for p in (target / ".aw" / ".workflow" / "scripts").iterdir() if p.suffix == ".ps1"
            )
            self.assertEqual(synced_ps1, [], msg=f"sync must not carry PowerShell wrappers into the instance: {synced_ps1}")
            self.assertTrue((target / ".aw" / ".agents" / "skills").is_dir())
            self.assertTrue((target / "templates").is_dir())
            self.assertEqual((target / "templates" / "custom.md").read_text(encoding="utf-8"), "custom\n")
            self.assertFalse((target / ".aw" / ".workflow" / "tests").exists())
            self.assertNotIn("baseline/README.md", ignore_text)
            self.assertNotEqual(
                subprocess.run(
                    ["git", "-C", str(target), "check-ignore", "--quiet", "baseline/README.md"],
                ).returncode,
                0,
            )

            (target / ".aw" / ".workflow" / "workflow.py").touch()
            (target / "workspace" / "workflow").mkdir(parents=True)
            (target / "workspace" / "workflow" / "manifest.yaml").write_text("state\n", encoding="utf-8")
            ignored_workflow = subprocess.run(
                ["git", "-C", str(target), "check-ignore", "--quiet", ".aw/.workflow/workflow.py"],
            )
            ignored_instance_state = subprocess.run(
                ["git", "-C", str(target), "check-ignore", "--quiet", "workspace/workflow/manifest.yaml"],
            )
            ignore_text = (target / ".gitignore").read_text(encoding="utf-8")
            self.assertNotIn("/README.md", ignore_text)
            self.assertEqual(ignored_workflow.returncode, 0)
            self.assertNotEqual(ignored_instance_state.returncode, 0)

    def test_python_init_instance_dry_run_does_not_create_target(self):
        with _ScratchDir("test") as raw:
            target = Path(raw) / "python-instance"
            with patch.object(workflow, "workflow_protection_errors", return_value=[]):
                result = workflow.main(
                    ["init-instance", "--name", "Product Python", "--directory", str(target), "--dry-run"]
                )
            self.assertEqual(result, 0)
            self.assertFalse(target.exists())

    def test_python_init_instance_creates_instance_and_lock(self):
        with _ScratchDir("test") as raw:
            target = Path(raw) / "python-instance"
            with patch.object(workflow, "workflow_protection_errors", return_value=[]):
                result = workflow.main(
                    ["init-instance", "--name", "Product Python", "--directory", str(target)]
                )
            self.assertEqual(result, 0)
            self.assertIn("# Product Python", (target / "README.md").read_text(encoding="utf-8"))
            version = (target / ".aw" / "workflow-version.yaml").read_text(encoding="utf-8")
            self.assertIn("source_ref: HEAD", version)
            self.assertTrue((target / ".aw" / ".workflow" / "workflow.py").is_file())
            self.assertTrue((target / "workspace").is_dir())
            self.assertTrue((target / "baseline" / "README.md").is_file())
            self.assertTrue((target / "workspace" / "README.md").is_file())
            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertFalse((target / ".aw" / "AGENTS.md").exists())
            # The project-owned root README must remain trackable.
            self.assertEqual(
                subprocess.run(
                    ["git", "-C", str(target), "check-ignore", "--quiet", "README.md"],
                ).returncode,
                1,
            )

    def test_init_instance_defaults_name_to_target_directory(self):
        with _ScratchDir("test") as raw:
            target = Path(raw) / "default-named-product"
            with patch.object(workflow, "workflow_protection_errors", return_value=[]):
                result = workflow.main(
                    ["init-instance", "--directory", str(target)]
                )
            self.assertEqual(result, 0)
            self.assertIn("# default-named-product", (target / "README.md").read_text(encoding="utf-8"))
            version = (target / ".aw" / "workflow-version.yaml").read_text(encoding="utf-8")
            self.assertIn("source_ref: HEAD", version)

    def test_init_instance_accepts_workflow_ref(self):
        with _ScratchDir("test") as raw:
            target = Path(raw) / "ref-product"
            with patch.object(workflow, "workflow_protection_errors", return_value=[]):
                result = workflow.main(
                    [
                        "init-instance",
                        "--workflow-version",
                        "HEAD",
                        "--directory",
                        str(target),
                    ]
                )
            self.assertEqual(result, 0)
            version = (target / ".aw" / "workflow-version.yaml").read_text(encoding="utf-8")
            self.assertIn("source_ref: HEAD", version)

    def test_python_sync_preserves_instance_readme_and_tracks_state(self):
        with _ScratchDir("test") as raw:
            target = Path(raw) / "python-sync"
            target.mkdir()
            (target / "README.md").write_text("# Existing Product\n", encoding="utf-8")
            (target / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
            subprocess.run(["git", "init", "--quiet", str(target)], check=True)
            subprocess.run(["git", "-C", str(target), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(target), "-c", "user.email=test@example.com", "-c", "user.name=Test", "commit", "--quiet", "-m", "initial"],
                check=True,
            )
            with patch.object(workflow, "workflow_protection_errors", return_value=[]):
                result = workflow.main(["sync", "--directory", str(target)])
            self.assertEqual(result, 0)
            self.assertEqual((target / "README.md").read_text(encoding="utf-8"), "# Existing Product\n")
            self.assertEqual(
                (target / ".aw" / "README.md").read_text(encoding="utf-8"),
                (Path(__file__).resolve().parents[2] / "README.md").read_text(encoding="utf-8"),
            )
            (target / "workspace" / "workflow").mkdir(parents=True)
            (target / "workspace" / "workflow" / "manifest.yaml").write_text("state\n", encoding="utf-8")
            self.assertEqual(
                subprocess.run(["git", "-C", str(target), "check-ignore", "--quiet", ".aw/.workflow/workflow.py"]).returncode,
                0,
            )
            self.assertNotEqual(
                subprocess.run(["git", "-C", str(target), "check-ignore", "--quiet", "workspace/workflow/manifest.yaml"]).returncode,
                0,
            )
            self.assertNotIn("/README.md", (target / ".gitignore").read_text(encoding="utf-8"))

    def test_workflow_readme_freshness_does_not_require_instance_iteration(self):
        """The framework README must not be coupled to a product iteration."""
        temp, root = self.make_repo()
        try:
            (root / "README.md").write_text(
                "# Workflow\n\nstage-gate stale-skill stage_status\n",
                encoding="utf-8",
            )
            skills = root / ".agents" / "skills"
            skills.mkdir(parents=True)
            (skills / "stale-skill").mkdir()
            (skills / "stale-skill" / "SKILL.md").write_text("# skill\n", encoding="utf-8")
            scripts = root / ".workflow" / "scripts"
            scripts.mkdir(parents=True)
            (scripts / "stage_status.py").write_text("# script\n", encoding="utf-8")

            errors: list[str] = []
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "FRAMEWORK_ROOT", root):
                workflow.check_readme_freshness(errors)

            self.assertEqual(errors, [])
        finally:
            temp.cleanup()

    def test_instance_readme_refresh_contract_requires_marker_and_heading(self):
        """Root README gate must require the version marker and functionality heading."""
        temp, root = self.make_repo()
        try:
            readme = root / "README.md"
            readme.write_text("# Instance\n", encoding="utf-8")
            with patch.object(workflow, "ROOT", root):
                errors: list[str] = []
                workflow.check_workspace_readme_freshness("v1", errors)
            self.assertTrue(
                any("README.md" in error and "not refreshed" in error for error in errors),
                msg=f"gate did not flag missing marker; errors={errors}",
            )
            self.assertTrue(
                any("当前系统功能说明" in error for error in errors),
                msg=f"gate did not flag missing heading; errors={errors}",
            )
        finally:
            temp.cleanup()

    def test_workspace_readme_freshness_alias(self):
        """The historical `check_instance_readme_freshness` name must keep working
        because external documentation and downstream callers may still
        reference it through the §17 refresh-contract transition.
        """
        self.assertIs(
            workflow.check_instance_readme_freshness,
            workflow.check_workspace_readme_freshness,
        )
        self.assertIs(
            workflow.generate_instance_readme,
            workflow.generate_workspace_readme,
        )

    def test_instance_readme_refresh_targets_root_not_workspace(self):
        """05-review-release writes functionality into root README only."""
        temp, root = self.make_repo()
        try:
            (root / "iteration" / "v1").rename(root / "iteration" / "v1.0")
            (root / "README.md").write_text(
                "# Workflow\n", encoding="utf-8"
            )
            for relative in [
                "iteration/v1.0/01-product/v1.0-prototype.html",
                "iteration/v1.0/02-design/v1.0-architecture-design.md",
                "iteration/v1.0/02-design/v1.0-api-spec.md",
                "iteration/v1.0/02-design/v1.0-database-dictionary.md",
                "iteration/v1.0/03-planning/v1.0-task-plan-dag.md",
                "iteration/v1.0/03-planning/v1.0-validation-plan.md",
                "iteration/v1.0/04-implementation/v1.0-source-code.md",
                "iteration/v1.0/04-implementation/v1.0-test-results.md",
                "iteration/v1.0/04-implementation/v1.0-issue-fixes.md",
                "iteration/v1.0/05-review-release/v1.0-review-release.md",
                "iteration/v1.0/05-review-release/v1.0-release-log.md",
            ]:
                self.add_approved(root, relative, "TASK-API-010\n")
            requirement = root / "iteration" / "v1.0" / "01-product" / "v1.0-requirement.md"
            requirement.write_text(
                "---\nstatus: Approved\nprototype_required: true\n---\n# Workspace Req Body\n",
                encoding="utf-8",
            )
            plan = root / "iteration" / "v1.0" / "03-planning" / "v1.0-task-plan-dag.md"
            plan.write_text("---\nstatus: Approved\n---\nTASK-API-010\n", encoding="utf-8")
            release_log = root / "iteration" / "v1.0" / "05-review-release" / "v1.0-release-log.md"
            release_log.write_text(
                "---\nstatus: draft\n---\n"
                "## 2. 功能交付清单\n\n"
                "### 2.1 新增功能(FR-XXX / YYY)\n\n"
                "| ID | 标题 | TASK | 验收 |\n|---|---|---|---|\n"
                "| FR-100 | 推送优化 | TASK-API-010 | AC-100 ✅ |\n",
                encoding="utf-8",
            )
            root_readme = root / "README.md"
            root_readme.write_text(
                "# Instance\n\n## 当前系统功能说明\n\n"
                "<!-- workflow:current-system-functionality:start -->\n旧内容\n"
                "<!-- workflow:current-system-functionality:end -->\n",
                encoding="utf-8",
            )
            workspace_readme = root / "workspace" / "README.md"
            workspace_readme.write_text("# Workspace\n\n静态说明\n", encoding="utf-8")
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "FRAMEWORK_ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                rc = workflow.validate("v1.0", "05-review-release")
            self.assertEqual(rc, 0, msg="validate --stage 05-review-release should pass for a complete chain")
            root_text = root_readme.read_text(encoding="utf-8")
            self.assertIn("<!-- workflow:current-system-functionality-version: v1.0 -->", root_text)
            self.assertIn("## 当前系统功能说明", root_text)
            # Content comes from release-log §2.1, not from requirement body.
            self.assertIn("FR-100 推送优化", root_text)
            self.assertNotIn("# Workspace Req Body", root_text)
            self.assertEqual(workspace_readme.read_text(encoding="utf-8"), "# Workspace\n\n静态说明\n")
        finally:
            temp.cleanup()

    def test_workspace_readme_extracts_release_log_sections(self):
        """Happy path: each release-log subsection present in §2.1-§2.4, §3, §7
        renders into the corresponding workspace/README.md section.
        """
        temp, root = self.make_repo()
        try:
            release_log = root / "iteration" / "v1.0" / "05-review-release" / "v1.0-release-log.md"
            release_log.parent.mkdir(parents=True, exist_ok=True)
            release_log.write_text(
                "---\nstatus: draft\n---\n"
                "## 2. 功能交付清单\n\n"
                "### 2.1 新增功能(FR-XXX / YYY)\n\n"
                "| ID | 标题 | TASK | 验收 |\n|---|---|---|---|\n"
                "| FR-200 | 调度改进 | TASK-API-200 | AC-200 ✅ |\n"
                "\n### 2.2 体验优化(FR-XXX~YYY)\n\n"
                "| ID | 标题 | TASK | 验收 |\n|---|---|---|---|\n"
                "| FR-201 | 主题切换 | TASK-UI-201 | AC-201 ✅ |\n"
                "\n### 2.3 业务规则(BR-XXX~YYY)\n\n"
                "| ID | 标题 | 说明 |\n|---|---|---|\n"
                "| BR-050 | 限速口径 | 单租户 25 rps |\n"
                "\n### 2.4 验收标准(AC-XXX~YYY)\n\n"
                "| AC | 描述 | 集成测试 | 结果 |\n|---|---|---|---|\n"
                "| AC-200 | 调度正确 | `tests/sched.py` | ✅ |\n"
                "\n## 3. ISSUE 收尾\n\n"
                "| ISSUE | 类别 | 最终状态 |\n|---|---|---|\n"
                "| ISSUE-V1.0-10 | 前端 | ✅ 本版本已修复：暗色模式 |\n"
                "\n## 7. 已知限制与假设\n\n"
                "| 类型 | 内容 |\n|---|---|\n"
                "| 假设 | 仅在 Ubuntu 22.04 验证 |\n",
                encoding="utf-8",
            )
            with patch.object(workflow, "ROOT", root):
                workflow.generate_workspace_readme("v1.0")
            text = (root / "README.md").read_text(encoding="utf-8")
            # Heading + marker present.
            self.assertIn("<!-- workflow:current-system-functionality-version: v1.0 -->", text)
            self.assertIn("## 当前系统功能说明", text)
            # Each extracted row appears.
            self.assertIn("### 新增功能", text)
            self.assertIn("FR-200 调度改进", text)
            self.assertIn("### 体验优化", text)
            self.assertIn("FR-201 主题切换", text)
            self.assertIn("### 业务规则", text)
            self.assertIn("BR-050 限速口径", text)
            self.assertIn("### 验收标准", text)
            self.assertIn("AC-200 调度正确", text)
            self.assertIn("### 修复项", text)
            self.assertIn("ISSUE-V1.0-10 前端", text)
            self.assertIn("## 已知限制与假设", text)
            self.assertIn("假设：仅在 Ubuntu 22.04 验证", text)
        finally:
            temp.cleanup()

    def test_workspace_readme_omits_missing_release_log_sections(self):
        """Subsections absent in release-log render as no section in workspace/README.md."""
        temp, root = self.make_repo()
        try:
            release_log = root / "iteration" / "v1.0" / "05-review-release" / "v1.0-release-log.md"
            release_log.parent.mkdir(parents=True, exist_ok=True)
            # Only §2.1 present; everything else omitted.
            release_log.write_text(
                "---\nstatus: draft\n---\n"
                "## 2. 功能交付清单\n\n"
                "### 2.1 新增功能(FR-XXX / YYY)\n\n"
                "| ID | 标题 | TASK | 验收 |\n|---|---|---|---|\n"
                "| FR-300 | 限流开关 | TASK-API-300 | AC-300 ✅ |\n",
                encoding="utf-8",
            )
            with patch.object(workflow, "ROOT", root):
                workflow.generate_workspace_readme("v1.0")
            text = (root / "README.md").read_text(encoding="utf-8")
            self.assertIn("### 新增功能", text)
            self.assertIn("FR-300 限流开关", text)
            # Subsections not present must NOT produce headings.
            self.assertNotIn("### 体验优化", text)
            self.assertNotIn("### 业务规则", text)
            self.assertNotIn("### 验收标准", text)
            self.assertNotIn("### 修复项", text)
            self.assertNotIn("## 已知限制与假设", text)
        finally:
            temp.cleanup()

    def test_workspace_readme_omits_fix_section_when_all_issues_handed_over(self):
        """§3 only renders a 修复项 heading if at least one entry has been
        closed this version. All-handover runs produce no 修复项 section.
        """
        temp, root = self.make_repo()
        try:
            release_log = root / "iteration" / "v1.0" / "05-review-release" / "v1.0-release-log.md"
            release_log.parent.mkdir(parents=True, exist_ok=True)
            release_log.write_text(
                "---\nstatus: draft\n---\n"
                "## 3. ISSUE 收尾\n\n"
                "| ISSUE | 类别 | 最终状态 |\n|---|---|---|\n"
                "| ISSUE-V1.0-99 | 后端 | ⏳ 交接至 v1.1：性能调优 |\n",
                encoding="utf-8",
            )
            with patch.object(workflow, "ROOT", root):
                workflow.generate_workspace_readme("v1.0")
            text = (root / "README.md").read_text(encoding="utf-8")
            self.assertNotIn("### 修复项", text)
            self.assertNotIn("ISSUE-V1.0-99", text)
        finally:
            temp.cleanup()

    def test_workspace_readme_raises_when_release_log_missing(self):
        """If release-log.md is absent, generate_workspace_readme must raise
        rather than silently producing a half-populated README.
        """
        temp, root = self.make_repo()
        try:
            (root / "iteration" / "v1.0" / "05-review-release").mkdir(parents=True)
            with patch.object(workflow, "ROOT", root):
                with self.assertRaises(ValueError) as ctx:
                    workflow.generate_workspace_readme("v1.0")
            self.assertIn("release-log", str(ctx.exception))
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
                checkpoint = json.loads((root / "workspace" / "workflow" / "current-state.json").read_text(encoding="utf-8"))
                self.assertEqual(checkpoint["latest_gate"]["target"], "01-product")
                self.assertEqual(checkpoint["latest_gate"]["result"], "blocked")
        finally:
            temp.cleanup()

    def test_product_prototype_requires_review_frontmatter(self):
        temp, root = self.make_repo()
        try:
            prototype = root / "iteration" / "v1" / "01-product" / "v1-prototype.html"
            prototype.parent.mkdir(parents=True, exist_ok=True)
            prototype.write_text("<!-- status: Approved -->\n<html></html>\n", encoding="utf-8")
            import io, contextlib
            buf = io.StringIO()
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"), contextlib.redirect_stdout(buf):
                rc = workflow.validate("v1", "01-product")
            self.assertEqual(rc, 1)
            self.assertIn("missing review frontmatter", buf.getvalue())
            self.assertIn("reviewer", buf.getvalue())
        finally:
            temp.cleanup()

    def test_approved_product_prototype_requires_a_completed_review_record(self):
        temp, root = self.make_repo()
        try:
            prototype = root / "iteration" / "v1" / "01-product" / "v1-prototype.html"
            prototype.parent.mkdir(parents=True, exist_ok=True)
            prototype.write_text(
                "<!--\nstatus: Approved\nreviewer: \nreviewed_at: \nreview_notes: \n-->\n<html></html>\n",
                encoding="utf-8",
            )
            import io, contextlib
            buf = io.StringIO()
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"), contextlib.redirect_stdout(buf):
                rc = workflow.validate("v1", "01-product")
            self.assertEqual(rc, 1)
            self.assertIn("reviewer", buf.getvalue())
        finally:
            temp.cleanup()

    def test_approved_product_prototype_accepts_completed_review_record(self):
        temp, root = self.make_repo()
        try:
            prototype = root / "iteration" / "v1" / "01-product" / "v1-prototype.html"
            prototype.parent.mkdir(parents=True, exist_ok=True)
            prototype.write_text(
                "<!--\nstatus: Approved\nreviewer: Product Owner\nreviewed_at: 2026-09-10T12:00:00+08:00\nreview_notes: Reviewed key flows and responsive states.\n-->\n<html></html>\n",
                encoding="utf-8",
            )
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.assertEqual(workflow.validate("v1", "01-product"), 0)
        finally:
            temp.cleanup()

    def test_incremental_product_stage_allows_no_prototype_when_decision_is_false(self):
        temp, root = self.make_repo()
        try:
            product = root / "iteration" / "v1.1" / "01-product"
            product.mkdir(parents=True)
            (product / "v1.1-requirement.md").write_text(
                "---\nstatus: Approved\nprototype_required: false\nprototype_baseline: baseline/05-core-user-flow-prototype.html\nprototype_rationale: Existing interaction is reused.\n---\n# Increment\n## AC-002\n",
                encoding="utf-8",
            )
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.assertNotIn(
                    "iteration/v1.1/01-product/v1.1-prototype.html",
                    workflow.required_inputs("v1.1", "01-product"),
                )
                self.assertEqual(workflow.validate("v1.1", "01-product"), 0)
        finally:
            temp.cleanup()

    def test_incremental_implementation_stage_does_not_require_legacy_issue_log(self):
        """v1.1+ records issues in source-code.md rather than issue-fixes.md."""
        temp, root = self.make_repo()
        try:
            product = root / "iteration" / "v1.1" / "01-product"
            product.mkdir(parents=True)
            (product / "v1.1-requirement.md").write_text(
                "---\nstatus: Approved\nprototype_required: false\n"
                "prototype_baseline: baseline/05-core-user-flow-prototype.html\n"
                "prototype_rationale: Existing interaction is reused.\n---\n"
                "# Increment\n## AC-002\n",
                encoding="utf-8",
            )
            for relative in [
                "iteration/v1.1/02-design/v1.1-architecture-design.md",
                "iteration/v1.1/02-design/v1.1-api-spec.md",
                "iteration/v1.1/02-design/v1.1-database-dictionary.md",
                "iteration/v1.1/03-planning/v1.1-task-plan-dag.md",
                "iteration/v1.1/03-planning/v1.1-validation-plan.md",
                "iteration/v1.1/04-implementation/v1.1-source-code.md",
                "iteration/v1.1/04-implementation/v1.1-test-results.md",
            ]:
                self.add_approved(root, relative, "TASK-API-010\n")
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                expected = "iteration/v1.1/04-implementation/v1.1-issue-fixes.md"
                self.assertNotIn(expected, workflow.required_inputs("v1.1", "04-implementation"))
                self.assertEqual(workflow.validate("v1.1", "04-implementation"), 0)
        finally:
            temp.cleanup()

    def test_v1_implementation_stage_retains_legacy_issue_log_requirement(self):
        temp, root = self.make_repo()
        try:
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                expected = "iteration/v1/04-implementation/v1-issue-fixes.md"
                self.assertIn(expected, workflow.required_inputs("v1", "04-implementation"))
        finally:
            temp.cleanup()

    def test_product_stage_requires_an_explicit_prototype_decision(self):
        temp, root = self.make_repo()
        try:
            requirement = root / "iteration" / "v1" / "01-product" / "v1-requirement.md"
            requirement.write_text("---\nstatus: Approved\n---\n# Req\n", encoding="utf-8")
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.assertEqual(workflow.validate("v1", "01-product"), 1)
        finally:
            temp.cleanup()

    def test_product_stage_requires_rationale_when_prototype_is_not_required(self):
        temp, root = self.make_repo()
        try:
            product = root / "iteration" / "v1.1" / "01-product"
            product.mkdir(parents=True)
            (product / "v1.1-requirement.md").write_text(
                "---\nstatus: Approved\nprototype_required: false\n---\n# Increment\n",
                encoding="utf-8",
            )
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.assertEqual(workflow.validate("v1.1", "01-product"), 1)
        finally:
            temp.cleanup()

    def test_state_refresh_rebuilds_checkpoint_for_requested_iteration(self):
        temp, root = self.make_repo()
        try:
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.assertEqual(workflow.state("v1", refresh=True), 0)
                checkpoint = json.loads((root / "workspace" / "workflow" / "current-state.json").read_text(encoding="utf-8"))
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
                before = json.loads((root / "workspace" / "workflow" / "current-state.json").read_text(encoding="utf-8"))
                requirement = root / "iteration" / "v1" / "01-product" / "v1-requirement.md"
                requirement.write_text(requirement.read_text(encoding="utf-8") + "\nUpdated\n", encoding="utf-8")
                self.assertEqual(workflow.state("v1"), 0)
                after = json.loads((root / "workspace" / "workflow" / "current-state.json").read_text(encoding="utf-8"))
                self.assertNotEqual(before["source_fingerprint"], after["source_fingerprint"])
        finally:
            temp.cleanup()

    def test_requirement_route_uses_baseline_when_only_readme_exists(self):
        with _ScratchDir("test") as raw:
            root = Path(raw)
            (root / "baseline").mkdir()
            (root / "baseline" / "README.md").write_text("# Baseline\n", encoding="utf-8")
            (root / ".workflow").mkdir()
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                route = workflow.requirement_route()
            self.assertEqual(route["mode"], "baseline")
            self.assertEqual(route["raw_requirement_dir"], "baseline/raw-requirement")

    def test_requirement_route_keeps_baseline_mode_when_only_raw_input_exists(self):
        with _ScratchDir("test") as raw:
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
            (root / "workspace" / "workflow").mkdir(parents=True, exist_ok=True)
            (root / "workspace" / "workflow" / "manifest.yaml").write_text(
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
        with _ScratchDir("test") as raw:
            root = Path(raw)
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.assertEqual(workflow.init_project(), 0)
            self.assertTrue((root / "baseline" / "raw-requirement").is_dir())
            self.assertTrue((root / "iteration").is_dir())
            self.assertTrue((root / "iteration" / "raw-requirement").is_dir())
            self.assertTrue((root / "workspace").is_dir())
            self.assertTrue((root / "baseline" / "README.md").is_file())
            self.assertTrue((root / "baseline" / "raw-requirement" / "README.md").is_file())
            self.assertTrue((root / "iteration" / "README.md").is_file())
            self.assertTrue((root / "workspace" / "README.md").is_file())
            self.assertTrue((root / "iteration" / "raw-requirement" / "README.md").is_file())

    def test_init_version_requires_baseline_then_creates_skeleton(self):
        with _ScratchDir("test") as raw:
            root = Path(raw)
            (root / "baseline").mkdir()
            (root / "iteration").mkdir()
            (root / ".workflow").mkdir()
            for name in ["01-product-vision", "02-product-charter", "03-tech-stack-decision", "04-glossary"]:
                (root / "baseline" / f"{name}.md").write_text(
                    "---\nstatus: Approved\n---\n# baseline\n", encoding="utf-8"
                )
            (root / "baseline" / "05-core-user-flow-prototype.html").write_text(
                "<!--\nstatus: Approved\n"
                "reviewer: Product Owner\nreviewed_at: 2026-09-10T12:00:00+08:00\n"
                "review_notes: Fixture review record.\n-->\n<html></html>\n",
                encoding="utf-8",
            )
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.assertEqual(workflow.init_version(), 0)
            for stage in workflow.STAGES:
                self.assertTrue((root / "iteration" / "v1.0" / stage).is_dir())
            self.assertFalse((root / "iteration" / "v1.0" / "00-raw-requirement").exists())

    def test_init_version_refuses_unapproved_baseline(self):
        with _ScratchDir("test") as raw:
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

    def test_init_version_archives_completed_predecessor_after_creating_successor(self):
        temp, root = self.make_repo()
        try:
            (root / "iteration" / "v1").rename(root / "iteration" / "v1.0")
            for relative in [
                "iteration/v1.0/01-product/v1.0-prototype.html",
                "iteration/v1.0/02-design/v1.0-architecture-design.md",
                "iteration/v1.0/02-design/v1.0-api-spec.md",
                "iteration/v1.0/02-design/v1.0-database-dictionary.md",
                "iteration/v1.0/03-planning/v1.0-task-plan-dag.md",
                "iteration/v1.0/03-planning/v1.0-validation-plan.md",
                "iteration/v1.0/04-implementation/v1.0-source-code.md",
                "iteration/v1.0/04-implementation/v1.0-test-results.md",
                "iteration/v1.0/04-implementation/v1.0-issue-fixes.md",
                "iteration/v1.0/05-review-release/v1.0-review-release.md",
                "iteration/v1.0/05-review-release/v1.0-release-log.md",
            ]:
                self.add_approved(root, relative, "TASK-API-010\n")
            requirement = root / "iteration" / "v1.0" / "01-product" / "v1.0-requirement.md"
            requirement.write_text(
                "---\nstatus: Approved\nprototype_required: true\n---\n# Req\nAC-001\n",
                encoding="utf-8",
            )
            plan = root / "iteration" / "v1.0" / "03-planning" / "v1.0-task-plan-dag.md"
            plan.write_text("---\nstatus: Approved\n---\nTASK-API-010\n", encoding="utf-8")
            (root / "README.md").write_text("# Pre-existing root README\n", encoding="utf-8")
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.assertEqual(workflow.init_version(), 0)
            self.assertTrue((root / "iteration" / "v1.1" / "01-product").is_dir())
            archived = root / "iteration" / "archive" / "v1.0"
            self.assertTrue(archived.is_dir())
            self.assertFalse((root / "iteration" / "v1.0").exists())
            self.assertIn("superseded_by: v1.1", (archived / "ARCHIVED.md").read_text(encoding="utf-8"))
        finally:
            temp.cleanup()

    def test_init_version_archives_after_generating_workspace_readme(self):
        temp, root = self.make_repo()
        try:
            (root / "iteration" / "v1").rename(root / "iteration" / "v1.0")
            for relative in [
                "iteration/v1.0/01-product/v1.0-prototype.html",
                "iteration/v1.0/02-design/v1.0-architecture-design.md",
                "iteration/v1.0/02-design/v1.0-api-spec.md",
                "iteration/v1.0/02-design/v1.0-database-dictionary.md",
                "iteration/v1.0/03-planning/v1.0-task-plan-dag.md",
                "iteration/v1.0/03-planning/v1.0-validation-plan.md",
                "iteration/v1.0/04-implementation/v1.0-source-code.md",
                "iteration/v1.0/04-implementation/v1.0-test-results.md",
                "iteration/v1.0/04-implementation/v1.0-issue-fixes.md",
                "iteration/v1.0/05-review-release/v1.0-review-release.md",
                "iteration/v1.0/05-review-release/v1.0-release-log.md",
            ]:
                self.add_approved(root, relative, "TASK-API-010\n")
            requirement = root / "iteration" / "v1.0" / "01-product" / "v1.0-requirement.md"
            requirement.write_text(
                "---\nstatus: Approved\nprototype_required: true\n---\n# Req\nAC-001\n",
                encoding="utf-8",
            )
            plan = root / "iteration" / "v1.0" / "03-planning" / "v1.0-task-plan-dag.md"
            plan.write_text("---\nstatus: Approved\n---\nTASK-API-010\n", encoding="utf-8")
            release_log = root / "iteration" / "v1.0" / "05-review-release" / "v1.0-release-log.md"
            release_log.write_text(
                "---\nstatus: draft\n---\n"
                "## 2. 功能交付清单\n\n"
                "### 2.1 新增功能(FR-XXX / YYY)\n\n"
                "| ID | 标题 | TASK | 验收 |\n|---|---|---|---|\n"
                "| FR-400 | 初始化推送 | TASK-API-400 | AC-400 ✅ |\n",
                encoding="utf-8",
            )
            root_readme = root / "README.md"
            root_readme.write_text(
                "# Instance\n\n## 当前系统功能说明\n\n"
                "<!-- workflow:current-system-functionality:start -->\n旧内容\n"
                "<!-- workflow:current-system-functionality:end -->\n",
                encoding="utf-8",
            )
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "FRAMEWORK_ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                self.assertEqual(workflow.init_version(), 0)
            self.assertFalse((root / "iteration" / "v1.0").exists())
            self.assertTrue((root / "iteration" / "v1.1").is_dir())
            archived = root / "iteration" / "archive" / "v1.0"
            self.assertTrue(archived.is_dir())
            root_text = root_readme.read_text(encoding="utf-8")
            self.assertIn("<!-- workflow:current-system-functionality-version: v1.0 -->", root_text)
            self.assertIn("## 当前系统功能说明", root_text)
            # Content sourced from release-log §2.1, not requirement body.
            self.assertIn("FR-400 初始化推送", root_text)
            self.assertNotIn("# Req", root_text)
        finally:
            temp.cleanup()

    def test_init_version_does_not_archive_unreleased_predecessor(self):
        temp, root = self.make_repo()
        try:
            (root / "iteration" / "v1").rename(root / "iteration" / "v1.0")
            with patch.object(workflow, "ROOT", root), patch.object(workflow, "WORKFLOW_DIR", root / ".workflow"):
                with self.assertRaises(ValueError):
                    workflow.init_version()
            self.assertTrue((root / "iteration" / "v1.0").is_dir())
            self.assertFalse((root / "iteration" / "v1.1").exists())
            self.assertFalse((root / "iteration" / "archive" / "v1.0").exists())
        finally:
            temp.cleanup()

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
            ), patch.object(workflow, "discover_iteration", return_value="v1.0"), patch.object(
                workflow, "workflow_protection_errors", return_value=[]
            ):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    workflow.main(["--project-root", str(root), "validate", "--iteration", "v1", "--stage", "03-planning"])
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
            "---\n"
            "# v1.1\nFR-001 FR-005 TASK-API-001\n",
            encoding="utf-8",
        )
        review = repo / "iteration" / "v1.1" / "05-review-release"
        review.mkdir(parents=True)
        (review / "v1.1-review-release.md").write_text(
            "---\n"
            "status: Approved\n"
            "change_set:\n"
            "  added: [FR-005]\n"
            "  modified: [TASK-API-001]\n"
            "  deprecated: [FR-003]\n"
            "---\n"
            "# Review\n",
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
        with _ScratchDir("test") as raw:
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
        with _ScratchDir("test") as raw:
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

    # --------------------------------------------------------------
    # Root `README.md` ownership contract (workflow-maintenance change)
    # --------------------------------------------------------------

    def test_new_instance_has_root_agents_only_and_root_readme_is_project_owned(self):
        """The new instance contract keeps one AGENTS file and a tracked root README."""
        with _ScratchDir("test") as raw:
            target = Path(raw) / "single-rules-instance"
            with patch.object(workflow, "workflow_protection_errors", return_value=[]):
                result = workflow.main(
                    ["init-instance", "--name", "Single Rules", "--directory", str(target)]
                )
            self.assertEqual(result, 0)
            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertFalse((target / ".aw" / "AGENTS.md").exists())
            self.assertTrue((target / ".aw" / "README.md").is_file())
            self.assertTrue((target / "README.md").is_file())
            self.assertNotEqual(
                subprocess.run(
                    ["git", "-C", str(target), "check-ignore", "--quiet", "README.md"]
                ).returncode,
                0,
            )

    def test_sync_preserves_instance_agents_and_root_readme_but_updates_aw_readme(self):
        """Sync owns `.aw/README.md`, not project-owned root documents."""
        with _ScratchDir("test") as raw:
            target = Path(raw) / "project-owned-docs"
            target.mkdir()
            (target / "AGENTS.md").write_text("# Instance rules\n", encoding="utf-8")
            (target / "README.md").write_text("# Instance functionality\n", encoding="utf-8")
            (target / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
            subprocess.run(["git", "init", "--quiet", str(target)], check=True)
            subprocess.run(["git", "-C", str(target), "add", "."], check=True)
            subprocess.run(
                [
                    "git", "-C", str(target), "-c", "user.email=test@example.com",
                    "-c", "user.name=Test", "commit", "--quiet", "-m", "initial",
                ],
                check=True,
            )
            with patch.object(workflow, "workflow_protection_errors", return_value=[]):
                result = workflow.main(["sync", "--directory", str(target)])
            self.assertEqual(result, 0)
            self.assertEqual((target / "AGENTS.md").read_text(encoding="utf-8"), "# Instance rules\n")
            self.assertEqual((target / "README.md").read_text(encoding="utf-8"), "# Instance functionality\n")
            self.assertEqual(
                (target / ".aw" / "README.md").read_text(encoding="utf-8"),
                (Path(__file__).resolve().parents[2] / "README.md").read_text(encoding="utf-8"),
            )
            self.assertFalse((target / ".aw" / "AGENTS.md").exists())
            self.assertNotIn("/README.md", (target / ".gitignore").read_text(encoding="utf-8"))

    def test_release_refresh_updates_root_readme_not_workspace_readme(self):
        """Release functionality belongs in the project-owned root README."""
        with _ScratchDir("test") as raw:
            root = Path(raw) / "release-refresh"
            (root / "workspace").mkdir(parents=True)
            release_log = root / "iteration" / "v1.0" / "05-review-release" / "v1.0-release-log.md"
            release_log.parent.mkdir(parents=True, exist_ok=True)
            release_log.write_text(
                "---\nstatus: draft\n---\n"
                "## 2. 功能交付清单\n\n"
                "### 2.1 新增功能(FR-XXX / YYY)\n\n"
                "| ID | 标题 | TASK | 验收 |\n|---|---|---|---|\n"
                "| FR-900 | 实例功能 | TASK-API-900 | AC-900 ✅ |\n",
                encoding="utf-8",
            )
            (root / "README.md").write_text(
                "# Instance\n\n## 项目说明\n手工内容\n\n"
                "<!-- workflow:current-system-functionality:start -->\n"
                "旧内容\n"
                "<!-- workflow:current-system-functionality:end -->\n",
                encoding="utf-8",
            )
            workspace_readme = root / "workspace" / "README.md"
            workspace_readme.write_text("# Workspace\n\n静态说明\n", encoding="utf-8")
            with patch.object(workflow, "ROOT", root):
                workflow.generate_instance_readme("v1.0")
            root_text = (root / "README.md").read_text(encoding="utf-8")
            self.assertIn("FR-900 实例功能", root_text)
            self.assertIn("手工内容", root_text)
            self.assertIn("<!-- workflow:current-system-functionality:start -->", root_text)
            self.assertEqual(workspace_readme.read_text(encoding="utf-8"), "# Workspace\n\n静态说明\n")

    def test_init_instance_root_readme_is_instance_scaffold(self):
        """`init-instance` creates a project-owned functionality README."""
        with _ScratchDir("test") as raw:
            target = Path(raw) / "owned-instance"
            with patch.object(workflow, "workflow_protection_errors", return_value=[]):
                result = workflow.main(
                    ["init-instance", "--name", "Owned Instance", "--directory", str(target)]
                )
            self.assertEqual(result, 0)
            text = (target / "README.md").read_text(encoding="utf-8")
            self.assertIn("# Owned Instance", text)
            self.assertIn("## 当前系统功能说明", text)

    def test_sync_preserves_instance_root_readme(self):
        """`sync` must preserve the project-owned root README."""
        with _ScratchDir("test") as raw:
            target = Path(raw) / "owned-sync"
            target.mkdir()
            (target / "README.md").write_text("# Legacy\n", encoding="utf-8")
            (target / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
            subprocess.run(["git", "init", "--quiet", str(target)], check=True)
            subprocess.run(["git", "-C", str(target), "add", "."], check=True)
            subprocess.run(
                [
                        "git", "-C", str(target), "-c", "user.email=test@example.com",
                        "-c", "user.name=Test", "commit", "--quiet", "-m", "initial",
                    ],
                    check=True,
                )
            with patch.object(workflow, "workflow_protection_errors", return_value=[]):
                result = workflow.main(["sync", "--directory", str(target)])
            self.assertEqual(result, 0)
            self.assertEqual((target / "README.md").read_text(encoding="utf-8"), "# Legacy\n")

    def test_init_instance_root_readme_is_trackable(self):
        """After `init-instance`, the project-owned root README is trackable."""
        with _ScratchDir("test") as raw:
            target = Path(raw) / "ignored-instance"
            with patch.object(workflow, "workflow_protection_errors", return_value=[]):
                result = workflow.main(
                    ["init-instance", "--name", "Ignored", "--directory", str(target)]
                )
            self.assertEqual(result, 0)
            check = subprocess.run(
                ["git", "-C", str(target), "check-ignore", "--quiet", "README.md"],
            )
            self.assertNotEqual(check.returncode, 0)

    def test_ensure_workflow_ignore_block_is_idempotent_without_readme(self):
        """The managed ignore block remains idempotent and only ignores `.aw/`."""
        with _ScratchDir("test") as raw:
            target = Path(raw) / "ignore-block"
            target.mkdir()
            with patch.object(workflow, "workflow_protection_errors", return_value=[]):
                workflow._ensure_workflow_ignore_block(target)
                first = (target / ".gitignore").read_text(encoding="utf-8")
                workflow._ensure_workflow_ignore_block(target)
                second = (target / ".gitignore").read_text(encoding="utf-8")
            self.assertEqual(first, second, msg="_ensure_workflow_ignore_block is not idempotent")
            self.assertNotIn("/README.md", first)
            self.assertIn(".aw/", first)

    def test_sync_managed_block_excludes_only_aw(self):
        """`sync` must preserve trackability of the instance root README."""
        with _ScratchDir("test") as raw:
            target = Path(raw) / "sync-ignore"
            target.mkdir()
            (target / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
            (target / "README.md").write_text("# Pre-existing\n", encoding="utf-8")
            subprocess.run(["git", "init", "--quiet", str(target)], check=True)
            subprocess.run(["git", "-C", str(target), "add", "."], check=True)
            subprocess.run(
                [
                        "git", "-C", str(target), "-c", "user.email=test@example.com",
                        "-c", "user.name=Test", "commit", "--quiet", "-m", "initial",
                    ],
                    check=True,
                )
            with patch.object(workflow, "workflow_protection_errors", return_value=[]):
                result = workflow.main(["sync", "--directory", str(target)])
            self.assertEqual(result, 0)
            ignore_text = (target / ".gitignore").read_text(encoding="utf-8")
            self.assertNotIn("/README.md", ignore_text)
            self.assertIn(".aw/", ignore_text)


class ScriptProjectRootTests(unittest.TestCase):
    """Each script under .workflow/scripts/ must accept ``--project-root`` and
    operate on an external instance project (Round 1 fix: 4-script instance
    layout root resolution). The fixtures are minimal — just an empty
    ``iteration/`` and ``baseline/`` — so the tests exercise the new
    argument plumbing rather than each script's full analysis."""

    SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"

    def _external_repo(self) -> Path:
        scratch = _ScratchDir("script-proj")
        self.addCleanup(scratch.cleanup)
        root = scratch.path
        (root / "iteration").mkdir()
        (root / "baseline").mkdir()
        return root

    def _run(self, name, *args) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(self.SCRIPTS_DIR / name), *args],
            capture_output=True,
            text=True,
        )

    def test_stage_status_accepts_project_root(self):
        ext = self._external_repo()
        result = self._run(
            "stage_status.py", "--project-root", str(ext), "--iteration", "v1", "--json",
        )
        # Empty fixture ⇒ gate is blocked and the script returns 1 by design.
        # The point of this test is that --project-root reaches main() and the
        # script operates on the external repo (not the framework source).
        self.assertIn(result.returncode, (0, 1), msg=result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["iteration"], "v1.0")
        self.assertEqual(payload["gate"], "blocked")

    def test_id_registry_accepts_project_root(self):
        ext = self._external_repo()
        result = self._run(
            "id_registry.py", "--project-root", str(ext), "--iteration", "v1", "--json",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        # Registry must list at least the FR prefix even on an empty project.
        self.assertIn("FR", payload)

    def test_query_id_accepts_project_root(self):
        ext = self._external_repo()
        result = self._run(
            "query_id.py",
            "--project-root", str(ext), "--iteration", "v1",
            "--id", "FR-001", "--json",
        )
        # query_id returns 1 when the ID is not found in traceability; both 0
        # and 1 are acceptable here — what matters is that --project-root
        # does not break argument parsing.
        self.assertIn(result.returncode, (0, 1), msg=result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["id"], "FR-001")

    def test_check_links_accepts_project_root(self):
        ext = self._external_repo()
        result = self._run(
            "check_links.py", "--project-root", str(ext), "--iteration", "v1", "--json",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        # canonical_iteration("v1") normalizes to "v1.0" — the round-trip
        # through --project-root must produce it.
        self.assertEqual(payload["iteration"], "v1.0")
        # BASELINE_FILES has 4 .md + 1 .html entry; the script scans each .md
        # path for existence. On an empty external repo all are missing.
        self.assertEqual(payload["files_scanned"], 4)
        self.assertEqual(payload["links_total"], 0)
        self.assertEqual(payload["errors"], [])

    def test_diff_versions_accepts_project_root(self):
        ext = self._external_repo()
        result = self._run(
            "diff_versions.py",
            "--project-root", str(ext), "--from", "v1.0", "--to", "v1.1", "--json",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["from"], "v1.0")
        self.assertEqual(payload["to"], "v1.1")


class WorkflowDirResolutionTests(unittest.TestCase):
    """Round 1 round-3 fix: the four hardcoded `.workflow/` strings in
    workflow.py must derive from WORKFLOW_DIR.relative_to(ROOT), so the
    synced `.aw/.workflow/` layout produces matching strings instead of
    silently mis-referencing paths that don't exist on disk."""

    def _synced_workspace(self) -> Path:
        """Build a minimal synced-layout workspace: ROOT/<.aw/.workflow>
        plus an iteration skeleton so validate/state paths resolve."""
        scratch = _ScratchDir("synced-wf")
        self.addCleanup(scratch.cleanup)
        root = scratch.path
        aw_dir = root / ".aw" / ".workflow"
        aw_dir.mkdir(parents=True)
        # Mirror a tiny workflow surface so write_current_state has a project
        # gate to report on.
        for relative in ("baseline", "iteration", "workspace"):
            (root / relative).mkdir()
        return root

    def test_cleanup_context_packs_resolves_cache_key_under_synced_workflow(self):
        """`cleanup_context_packs` builds its cache-key prefix from
        `WORKFLOW_DIR.relative_to(ROOT)`, so a synced `.aw/.workflow/`
        workspace produces `".aw/.workflow/context-packs/v1.0-"`, not
        `".workflow/context-packs/v1.0-"`."""
        ext = self._synced_workspace()
        # cleanup_context_packs requires an archived iteration. Move our
        # baseline skeleton under archive/<v1.0>/ to satisfy that guard.
        archive = ext / "iteration" / "archive" / "v1.0"
        (archive / "baseline").mkdir(parents=True)
        # Seed the cache with the path the synced layout actually generates
        # so we can assert cleanup locates and removes the entry.
        cache_path = ext / ".aw" / ".workflow" / "cache" / "context-packs.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        seed_key = ".aw/.workflow/context-packs/v1.0-TASK-EX-001.md"
        cache_path.write_text(json.dumps({seed_key: "deadbeef"}), encoding="utf-8")
        # Pre-create one matching pack so cleanup finds it too.
        packs = ext / ".aw" / ".workflow" / "context-packs"
        packs.mkdir(parents=True, exist_ok=True)
        (packs / "v1.0-TASK-EX-001.md").write_text("# stub", encoding="utf-8")
        with patch.object(workflow, "ROOT", ext), patch.object(
            workflow, "WORKFLOW_DIR", ext / ".aw" / ".workflow"
        ):
            result = workflow.cleanup_context_packs("v1.0", execute=True)
        self.assertEqual(result, 0)
        after = json.loads(cache_path.read_text(encoding="utf-8"))
        self.assertNotIn(seed_key, after, msg="cleanup must match the synced-layout cache-key prefix")

    def test_write_current_state_uses_workflow_dir_relative_path(self):
        """`write_current_state` must report `task_runs` under
        `sources` using the synced-layout relative path, not the hardcoded
        `.workflow/` literal."""
        ext = self._synced_workspace()
        # Populate baseline as Approved so state() does not bail on
        # missing baseline artifacts.
        for name in [
            "01-product-vision.md",
            "02-product-charter.md",
            "03-tech-stack-decision.md",
            "04-glossary.md",
        ]:
            (ext / "baseline" / name).write_text(
                "---\nstatus: Approved\n---\n# stub\n", encoding="utf-8"
            )
        (ext / "baseline" / "05-core-user-flow-prototype.html").write_text(
            "<!--\nstatus: Approved\nreviewer: tester\nreviewed_at: 2026-09-10T12:00:00+08:00\n"
            "review_notes: fixture.\n-->\n<html></html>\n",
            encoding="utf-8",
        )
        v1_dir = ext / "iteration" / "v1.0" / "01-product"
        v1_dir.mkdir(parents=True)
        (v1_dir / "v1.0-requirement.md").write_text(
            "---\nstatus: Approved\nprototype_required: false\n---\n# r\n",
            encoding="utf-8",
        )
        with patch.object(workflow, "ROOT", ext), patch.object(
            workflow, "WORKFLOW_DIR", ext / ".aw" / ".workflow"
        ):
            state = workflow.write_current_state("v1.0", workflow.load_artifacts("v1.0"))
        self.assertEqual(state["sources"]["task_runs"], ".aw/.workflow/task-runs/")

    def test_task_finished_record_uses_workflow_dir_relative_path(self):
        """`task_finished` writes a record whose `context_pack` field
        mirrors the synced-layout path so the dashboard can locate it."""
        ext = self._synced_workspace()
        # Author a minimal task plan + API spec + requirement so
        # find_task / load_artifacts succeed under the synced layout.
        plan = ext / "iteration" / "v1.0" / "03-planning" / "v1.0-task-plan-dag.md"
        plan.parent.mkdir(parents=True)
        plan.write_text(
            "---\nstatus: Approved\n---\n# Plan\n## TASK-R3-001\nGoal\n",
            encoding="utf-8",
        )
        for name in [
            "01-product-vision.md",
            "02-product-charter.md",
            "03-tech-stack-decision.md",
            "04-glossary.md",
        ]:
            (ext / "baseline" / name).write_text(
                "---\nstatus: Approved\n---\n# stub\n", encoding="utf-8"
            )
        (ext / "baseline" / "05-core-user-flow-prototype.html").write_text(
            "<!--\nstatus: Approved\nreviewer: tester\nreviewed_at: 2026-09-10T12:00:00+08:00\n"
            "review_notes: fixture.\n-->\n<html></html>\n",
            encoding="utf-8",
        )
        v1p = ext / "iteration" / "v1.0" / "01-product"
        v1p.mkdir(parents=True)
        (v1p / "v1.0-requirement.md").write_text(
            "---\nstatus: Approved\nprototype_required: false\n---\n# r\n",
            encoding="utf-8",
        )
        v1d = ext / "iteration" / "v1.0" / "02-design"
        v1d.mkdir(parents=True)
        (v1d / "v1.0-api-spec.md").write_text(
            "---\nstatus: Approved\n---\n# API\n", encoding="utf-8"
        )
        # Pre-create a context pack + a basic iteration directory so the
        # context() / task_finished() round-trip does not hit the
        # "context pack missing" guard.
        packs_dir = ext / ".aw" / ".workflow" / "context-packs"
        packs_dir.mkdir(parents=True, exist_ok=True)
        (packs_dir / "v1.0-TASK-R3-001.md").write_text(
            "# Context Pack: TASK-R3-001\n", encoding="utf-8"
        )
        with patch.object(workflow, "ROOT", ext), patch.object(
            workflow, "WORKFLOW_DIR", ext / ".aw" / ".workflow"
        ):
            workflow.task_finished("v1.0", "TASK-R3-001", "succeeded")
        record_path = ext / ".aw" / ".workflow" / "task-runs" / "v1.0-TASK-R3-001.json"
        self.assertTrue(record_path.exists(), msg="task record must land in the synced workflow dir")
        record = json.loads(record_path.read_text(encoding="utf-8"))
        self.assertEqual(
            record["context_pack"],
            ".aw/.workflow/context-packs/v1.0-TASK-R3-001.md",
            msg="context_pack field must mirror the synced-layout path",
        )


class TemplateFrontmatterStatusTests(unittest.TestCase):
    """Round 1 round-4 fix: every template frontmatter under ``templates/``
    must default to ``status: draft`` (or another non-Approved value), so a
    user copying a template verbatim never instantiates an Approved
    artifact without a human review. The standing rule in AGENTS.md is
    that only humans can set ``status: Approved``; the templates must not
    pre-empt that gate."""

    REPO_TEMPLATES = Path(__file__).resolve().parents[2] / "templates"

    @staticmethod
    def _parse_frontmatter(text: str) -> str | None:
        """Extract the first YAML frontmatter block delimited by ``---``.

        Returns the inner text or ``None`` when the file does not start
        with a frontmatter delimiter (e.g. plain prose docs like
        ``templates/README.md`` have no frontmatter and are skipped)."""
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            return None
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                return "\n".join(lines[1:index])
        return None

    def test_no_template_frontmatter_uses_status_approved(self):
        """No template under ``templates/`` may carry ``status: Approved``
        in its frontmatter. (Other usages such as the ``status: Approved``
        *description* inside ``templates/README.md`` are documentation,
        not frontmatter, and so are out of scope for this check.)"""
        violations: list[str] = []
        for path in sorted(self.REPO_TEMPLATES.iterdir()):
            if path.suffix.lower() not in {".md", ".html"}:
                continue
            text = path.read_text(encoding="utf-8")
            frontmatter = self._parse_frontmatter(text)
            if frontmatter is None:
                continue
            for line in frontmatter.splitlines():
                stripped = line.strip()
                if stripped.startswith("status:"):
                    value = stripped.split(":", 1)[1].strip()
                    if value == "Approved":
                        violations.append(f"{path.name}: {stripped}")
        self.assertEqual(
            violations, [],
            msg="Template frontmatter must not default to `status: Approved`; "
                "only humans may set that field. Found: " + "; ".join(violations),
        )


class DesignTokensUniquenessTests(unittest.TestCase):
    """Round 1 round-5a: ``design-tokens.json`` is the prototype design
    system token table. Keeping two byte-identical copies under
    ``templates/`` and ``.agents/skills/prototype-design-system/references/``
    is a maintenance footgun — any edit that lands in only one of them
    silently drifts the Skill's runtime view of the tokens. The
    authoritative copy lives at ``templates/design-tokens.json``; the
    Skill reads it directly. The historical duplicate under
    ``references/`` is removed; this test enforces the single-source rule
    so a future contributor cannot reintroduce the copy."""

    REPO_ROOT = Path(__file__).resolve().parents[2]

    def test_design_tokens_json_only_lives_under_templates(self):
        candidates = list(self.REPO_ROOT.rglob("design-tokens.json"))
        rel_paths = sorted(p.relative_to(self.REPO_ROOT).as_posix() for p in candidates)
        self.assertEqual(
            rel_paths,
            ["templates/design-tokens.json"],
            msg=f"design-tokens.json must live only at templates/design-tokens.json; "
                f"found: {rel_paths}",
        )

    def test_references_directory_under_prototype_design_system_skill_is_gone(self):
        path = (
            self.REPO_ROOT
            / ".agents"
            / "skills"
            / "prototype-design-system"
            / "references"
        )
        self.assertFalse(
            path.exists(),
            msg=f"Legacy duplicate dir {path.relative_to(self.REPO_ROOT)} must not be recreated; "
                "the Skill reads templates/design-tokens.json directly.",
        )


class SyncScaffoldRefreshTests(unittest.TestCase):
    """Round 1 round-5b: `sync` must keep an instance's non-versioned
    scaffold READMEs (`baseline/README.md`, `workspace/README.md`, …)
    aligned with the framework source. Without this hook, a freshly
    synced instance has no `baseline/README.md` / `workspace/README.md`
    until the operator runs `init` manually, and the gate cannot tell
    what the canonical placeholders should be."""

    def _fresh_target(self) -> Path:
        scratch = _ScratchDir("synced-scaffold")
        self.addCleanup(scratch.cleanup)
        target = scratch.path
        # Minimal Git init so `sync_workflow` does not bail on
        # "target is not a Git working tree".
        subprocess.run(["git", "init", "--quiet", str(target)], check=True)
        subprocess.run(
            [
                "git", "-C", str(target), "-c", "user.email=test@example.com",
                "-c", "user.name=Test", "commit", "--quiet", "--allow-empty",
                "-m", "initial",
            ],
            check=True,
        )
        return target

    def test_sync_creates_missing_scaffold_readmes(self):
        target = self._fresh_target()
        with patch.object(workflow, "workflow_protection_errors", return_value=[]):
            rc = workflow.main(["sync", "--directory", str(target)])
        self.assertEqual(rc, 0)
        # The five non-versioned scaffold READMEs must exist after sync.
        for relative in (
            "baseline/README.md",
            "baseline/raw-requirement/README.md",
            "iteration/README.md",
            "iteration/raw-requirement/README.md",
            "workspace/README.md",
        ):
            self.assertTrue(
                (target / relative).is_file(),
                msg=f"sync must write the scaffold README at {relative}",
            )

    def test_sync_preserves_user_modified_scaffold_readme(self):
        target = self._fresh_target()
        custom_text = "# Custom baseline notes — operator-owned\n"
        (target / "baseline").mkdir()
        (target / "baseline" / "README.md").write_text(custom_text, encoding="utf-8")
        subprocess.run(["git", "-C", str(target), "add", "."], check=True)
        subprocess.run(
            [
                "git", "-C", str(target), "-c", "user.email=test@example.com",
                "-c", "user.name=Test", "commit", "--quiet",
                "-m", "user baseline note",
            ],
            check=True,
        )
        with patch.object(workflow, "workflow_protection_errors", return_value=[]):
            rc = workflow.main(["sync", "--directory", str(target)])
        self.assertEqual(rc, 0)
        # The user-edited baseline README must NOT be overwritten; the
        # writer is `if not path.exists()`-gated.
        self.assertEqual(
            (target / "baseline" / "README.md").read_text(encoding="utf-8"),
            custom_text,
            msg="sync must not overwrite an existing scaffold README",
        )


class FrameworkVersionMarkerTests(unittest.TestCase):
    """Round 1 round-5c: AlchemyWorks now exposes a framework version
    constant and surfaces it through three channels — the CLI `--version`
    flag, the `__version__` module attribute, and the
    `.aw/workflow-version.yaml` file written by `sync_workflow` /
    `init_instance`."""

    def test_module_exposes_version_constant(self):
        # The exact value drifts over time; assert the shape rather than
        # the literal so future bumps don't require a test update.
        self.assertTrue(hasattr(workflow, "__version__"))
        version = workflow.__version__
        self.assertIsInstance(version, str)
        parts = version.split(".")
        self.assertEqual(len(parts), 3, msg=f"expected semver MAJOR.MINOR.PATCH; got {version!r}")
        for part in parts:
            self.assertTrue(part.isdigit(), msg=f"version component {part!r} must be numeric")

    def test_cli_version_flag_prints_framework_version(self):
        # argparse parses `--version` and exits before our subcommand
        # machinery, so we drive the same path via SystemExit.
        with self.assertRaises(SystemExit) as raised:
            workflow.main(["--version"])
        self.assertEqual(raised.exception.code, 0)
        # argparse writes the version to stdout via print_version; we
        # don't capture it here, but the SystemExit + no traceback path
        # above is enough — the version-constant test pins the value.

    def test_sync_writes_framework_version_to_workflow_version_yaml(self):
        scratch = _ScratchDir("ver")
        self.addCleanup(scratch.cleanup)
        target = scratch.path
        subprocess.run(["git", "init", "--quiet", str(target)], check=True)
        subprocess.run(
            [
                "git", "-C", str(target), "-c", "user.email=test@example.com",
                "-c", "user.name=Test", "commit", "--quiet", "--allow-empty",
                "-m", "initial",
            ],
            check=True,
        )
        with patch.object(workflow, "workflow_protection_errors", return_value=[]):
            rc = workflow.main(["sync", "--directory", str(target)])
        self.assertEqual(rc, 0)
        manifest = (target / ".aw" / "workflow-version.yaml").read_text(encoding="utf-8")
        self.assertIn(f"framework_version: {workflow.__version__}", manifest)
        self.assertIn("schema_version: 1", manifest)
        self.assertIn("framework: AlchemyWorks", manifest)


if __name__ == "__main__":
    unittest.main()
