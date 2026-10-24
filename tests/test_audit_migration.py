"""保留原迁移审计入口和精确标识符行为。"""

import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_migration.py"
BUILD_REPORT = runpy.run_path(str(SCRIPT))["build_report"]


class AuditCase(unittest.TestCase):
    def test_identifier_substrings_do_not_count_as_preserved(self):
        for destination in ("`previous_task_id`", "`task_id_backup`", "`task_id2`"):
            with self.subTest(destination=destination):
                report = BUILD_REPORT("数据库字段 `task_id`。", destination, 1, None)
                self.assertEqual(report["anchors_missing"], 1)

    def test_identifiers_in_prose_and_qualified_fields_remain_supported(self):
        for destination in ("`task_id`", "字段task_id用于关联。", "The field is task_id.", "`runs.task_id`"):
            with self.subTest(destination=destination):
                report = BUILD_REPORT("数据库字段 `task_id`。", destination, 1, None)
                self.assertEqual(report["anchors_missing"], 0)

    def test_compound_anchor_substrings_do_not_count_as_preserved(self):
        cases = [("环境变量 `DATABASE_URL`", "`OLD_DATABASE_URL`"),
                 ("包名 `org.example.editor`", "`org.example.editor.beta`"),
                 ("协议 `editor-v1`", "`editor-v10`"),
                 ("路径 `backend/store.py`", "`old/backend/store.py`"),
                 ("路径 `backend/store.py`", "`backend/store.py.bak`"),
                 ("接口 `GET /api/drafts`", "`GET /api/drafts/history`"),
                 ("接口 `POST /api/drafts`", "`POST /api/drafts2`"),
                 ("命令 `npm test`", "`pnpm test`"),
                 ("命令 `npm test`", "`npm test:unit`")]
        for source, destination in cases:
            with self.subTest(source=source, destination=destination):
                report = BUILD_REPORT(source, destination, 1, None)
                self.assertEqual(report["anchor_candidates"], 1)
                self.assertEqual(report["anchors_missing"], 1)

    def test_compound_anchors_allow_normal_punctuation(self):
        for value in ("backend/store.py", "org.example.editor", "editor-v1", "GET /api/drafts", "npm test"):
            for destination in (f"`{value}`", f"Use {value}.", f"保留（{value}）。"):
                with self.subTest(value=value, destination=destination):
                    report = BUILD_REPORT(f"保留 `{value}`。", destination, 1, None)
                    self.assertEqual(report["anchor_candidates"], 1)
                    self.assertEqual(report["anchors_missing"], 0)

    def test_category_filter_does_not_change_matching(self):
        source = "接口 `GET /api/schema.json`。"
        for selected in (None, {"api"}, {"path"}):
            with self.subTest(selected=selected):
                report = BUILD_REPORT(source, "`GET /api/schema.json.backup`", 1, selected)
                self.assertEqual(report["anchor_candidates"], 1)
                self.assertEqual(report["anchors_missing"], 1)
        # 同时属于协议和字段的候选，不应因筛选为字段而放宽边界。
        report = BUILD_REPORT("数据库字段 `editor_v1`。", "`editor_v1.backup`", 1, {"schema"})
        self.assertEqual(report["anchors_missing"], 1)

    def test_regex_characters_are_literal_and_environment_values_stay_redacted(self):
        report = BUILD_REPORT("路径 `docs/a+b.md`。", "docs/ab.md", 1, None)
        self.assertEqual(report["anchors_missing"], 1)
        report = BUILD_REPORT("环境变量 `DATABASE_TOKEN=synthetic-value`。", "`OLD_DATABASE_TOKEN`", 1, None)
        self.assertEqual(report["missing"][0]["value"], "DATABASE_TOKEN")
        self.assertNotIn("synthetic-value", json.dumps(report))

    def test_sensitive_assignments_are_redacted_in_all_review_text(self):
        for assignment in ("TOKEN=synthetic-secret", "PASSWORD=synthetic-secret", "KEY=synthetic-secret",
                           "API_TOKEN = synthetic-secret", 'password = "synthetic-secret with spaces"',
                           "CREDENTIAL='synthetic-secret with spaces'", 'TOKEN="synthetic-secret unclosed'):
            with self.subTest(assignment=assignment):
                report = BUILD_REPORT(f"TODO: rotate `{assignment}`", "", 0, None)
                self.assertNotIn("synthetic-secret", json.dumps(report))
                self.assertIn("<redacted>", report["open_item_candidates"][0]["text"])
                self.assertTrue(report["sensitive_candidates"])
        report = BUILD_REPORT("环境变量 `API_TOKEN = synthetic-secret`", "API_TOKEN", 1, None)
        self.assertEqual(report["anchor_candidates"], 1)
        self.assertEqual(report["anchors_missing"], 0)

    def test_sensitive_commands_need_review_not_literal_preservation(self):
        for command in ("docker login --password synthetic-secret", "docker login --password=synthetic-secret",
                        'docker login --password "synthetic-secret with spaces"',
                        "python client.py --api-key 'synthetic-secret with spaces'",
                        "python client.py --verbose --token synthetic-secret",
                        "python client.py --password-stdin --token synthetic-secret",
                        "python client.py --token=--synthetic-secret",
                        "docker run -e TOKEN=synthetic-secret example"):
            with self.subTest(command=command):
                report = BUILD_REPORT(f"TODO: `{command}`", "", 0, None)
                self.assertNotIn("synthetic-secret", json.dumps(report))
                self.assertEqual(report["anchor_candidates"], 0)
                self.assertEqual(report["sensitive_candidates"][0]["source_line"], 1)
                self.assertIn("<redacted>", report["sensitive_candidates"][0]["text"])

    def test_safe_commands_and_identifiers_keep_exact_matching(self):
        for value in ("docker compose up -d", "python server.py --port 8080", "docker login --password-stdin",
                      "docker login --password-stdin --username example",
                      'docker login --password "$REGISTRY_TOKEN"',
                      'python client.py --token "${API_TOKEN}"',
                      'python client.py --token $env:API_TOKEN',
                      'python client.py --token %API_TOKEN%',
                      "API_TOKEN", "DATABASE_URL"):
            with self.subTest(value=value):
                report = BUILD_REPORT(f"保留 `{value}`", f"`{value}`", 1, None)
                self.assertEqual(report["anchor_candidates"], 1)
                self.assertEqual(report["anchors_missing"], 0)
                self.assertEqual(report["sensitive_candidates"], [])

    def test_cli_redacts_text_and_json_without_changing_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            memory = root / "memory"
            memory.mkdir()
            (memory / "topic.md").write_text("API_TOKEN", encoding="utf-8")
            source = root / "source.md"
            source.write_text('TODO: rotate PASSWORD=synthetic-secret\n'
                              '命令 `docker login --password "synthetic-secret with spaces"`\n'
                              '环境变量 `API_TOKEN = synthetic-secret`\n', encoding="utf-8")
            before = {p: p.read_bytes() for p in root.rglob("*.md")}
            for args in ([], ["--json"], ["--json", "--fail-on-missing"]):
                with self.subTest(args=args):
                    result = subprocess.run([sys.executable, str(SCRIPT), str(source), str(memory), *args],
                                            capture_output=True, text=True, encoding="utf-8")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertNotIn("synthetic-secret", result.stdout + result.stderr)
                    self.assertIn("<redacted>", result.stdout)
                    if "--json" in args:
                        self.assertEqual(len(json.loads(result.stdout)["sensitive_candidates"]), 3)
            self.assertEqual(before, {p: p.read_bytes() for p in root.rglob("*.md")})

    def test_fail_on_missing_rejects_identifier_substring_via_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "topic.md").write_text("`previous_task_id`", encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), "-", str(root), "--json", "--fail-on-missing"],
                                    input="数据库字段 `task_id`。", capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(json.loads(result.stdout)["missing"][0]["value"], "task_id")

    def test_missing_anchor_and_open_item_survive_compaction_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "topic.md").write_text("The durable field is `undo_snapshot`.\n", encoding="utf-8")
            source = "数据库字段 `undo_snapshot`。接口 `POST /api/drafts/revert` 尚未验证，未部署。\n"
            result = subprocess.run([sys.executable, str(SCRIPT), "-", str(root), "--json", "--fail-on-missing"],
                                    input=source, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 2, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["anchors_missing"], 1)
            self.assertEqual(report["missing"][0]["value"], "POST /api/drafts/revert")
            self.assertEqual(len(report["open_item_candidates"]), 1)
            self.assertIn("未部署", report["open_item_candidates"][0]["text"])

    def test_complete_exact_anchors_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = "接口 `POST /api/drafts/revert`；字段 `undo_snapshot`。\n"
            (root / "topic.md").write_text(source, encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), "-", str(root), "--fail-on-missing"],
                                    input=source, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
