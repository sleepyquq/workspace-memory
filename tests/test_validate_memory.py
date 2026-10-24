"""使用隔离记忆图验证公共 CLI 与只读边界。"""

from pathlib import Path
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_memory.py"


class MemoryCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.memory = self.root / ".workspace-memory"
        self.write("AGENTS.md", "## Workspace Memory\n\nStatus: enabled\n"
                   "Root: `.workspace-memory/`\nEntry: `.workspace-memory/state.md`\n"
                   "Router: `.workspace-memory/index.md`\n")
        self.note("state.md", "# Current State\nLast updated: 2026-10-24\n")
        self.note("index.md", "# Index\n[[topics/alpha]]\n")
        self.knowledge("alpha")

    def write(self, path, text):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding="utf-8")
        return file

    def note(self, path, text):
        return self.write(".workspace-memory/" + path, text)

    def knowledge(self, name, kind="topic", status="active", extra="", body=""):
        folder = "topics" if kind == "topic" else "decisions"
        return self.note(f"{folder}/{name}.md", f"---\nid: {name}\ntype: {kind}\n"
                         f"status: {status}\nsummary: Example.\nupdated: 2026-10-24\n"
                         f"{extra}---\n\n# Example\n{body}\n## Related\n")

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), str(self.root), *args],
                              capture_output=True, text=True, encoding="utf-8")

    def assertRejected(self, text=None):
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        if text:
            self.assertIn(text, result.stderr)

    def load_validator(self):
        spec = importlib.util.spec_from_file_location("memory_validator", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def assertOnlyAgentsRead(self):
        module = self.load_validator()
        original = Path.read_text
        reads = []

        def record(path, *args, **kwargs):
            reads.append(path.resolve())
            return original(path, *args, **kwargs)

        with patch.object(Path, "read_text", record), patch.object(module.os, "scandir", side_effect=AssertionError("memory enumerated")):
            errors, _, _ = module.validate(self.root)
        self.assertTrue(errors)
        self.assertEqual(reads, [(self.root / "AGENTS.md").resolve()])

    def test_valid_legacy_graph(self):
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_explicit_wrong_directory_is_not_basename_fallback(self):
        self.note("index.md", "[[missing-folder/alpha]]\n")
        self.assertRejected()

    def test_escaping_link_is_not_basename_fallback(self):
        self.note("index.md", "[[../../alpha]]\n")
        self.assertRejected()

    def test_type_specific_status(self):
        self.knowledge("alpha", status="superseded")
        self.assertRejected()

    def test_disabled_does_not_read_notes(self):
        agents = self.root / "AGENTS.md"
        agents.write_text(agents.read_text().replace("enabled", "disabled"))
        # 捕获读取与枚举，而非仅凭退出码推断门禁生效。
        self.assertOnlyAgentsRead()

    def test_repository_entry_templates_preserve_disabled_boundary(self):
        skill = (SCRIPT.parents[1] / "SKILL.md").read_text(encoding="utf-8")
        template = skill.split("## AGENTS.md Index\n", 1)[1].split("```markdown\n", 1)[1].split("```", 1)[0]
        example = (SCRIPT.parents[1] / "examples/editor-workspace/AGENTS.md").read_text(encoding="utf-8")
        for entry in (template, example):
            with self.subTest(entry=entry):
                self.write("AGENTS.md", entry)
                self.assertEqual(self.cli().returncode, 0)
                self.write("AGENTS.md", entry.replace("\nStatus: enabled\n", "\nStatus: disabled\n"))
                before = {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
                self.assertOnlyAgentsRead()
                self.assertRejected("memory not read")
                after = {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
                self.assertEqual(before, after)

    def test_unclosed_comments_never_enable_or_read_memory(self):
        original = (self.root / "AGENTS.md").read_text()
        for text in ("<!--\n" + original,
                     original.replace("Status: enabled", "<!--\nStatus: enabled"),
                     "<!--\n```\n" + original,
                     original.replace("Status: enabled", "Status: <!-- hidden -->enabled")):
            with self.subTest(text=text):
                self.write("AGENTS.md", text)
                self.assertOnlyAgentsRead()

    def test_comment_markers_in_examples_do_not_hide_real_gate(self):
        original = (self.root / "AGENTS.md").read_text()
        for prefix in ("```html\n<!--\n```\n", "~~~html\n<!--\n~~~\n",
                       "Example: `<!--`\n", "<!--\n```\n-->\n"):
            with self.subTest(prefix=prefix):
                self.write("AGENTS.md", prefix + original)
                self.assertEqual(self.cli().returncode, 0)

    def test_invalid_gates_do_not_scan_memory(self):
        agents = self.root / "AGENTS.md"
        original = agents.read_text()
        cases = [original + "\nStatus: disabled\n",
                 original + "\nStatus:enabled\n",
                 original + "\n## Workspace Memory\nStatus: enabled\n",
                 original.replace("Status: enabled", "Status: enabled "),
                 "```markdown\n" + original + "```\n",
                 "<!--\n" + original + "-->\n",
                 original.replace("Status: enabled", "# Other\nStatus: enabled"),
                 original.replace("Status: enabled", "## Other\nStatus: enabled")]
        for text in cases:
            with self.subTest(text=text):
                agents.write_text(text)
                self.assertOnlyAgentsRead()

    def test_fenced_examples_do_not_duplicate_real_gate(self):
        agents = self.root / "AGENTS.md"
        original = agents.read_text()
        agents.write_text("```markdown\n" + original + "```\n" + original)
        self.assertEqual(self.cli().returncode, 0)

    def test_invalid_index_does_not_read_notes(self):
        agents = self.root / "AGENTS.md"
        original = agents.read_text()
        self.write("outside.md", "not memory")
        replacements = [("Root: `.workspace-memory/`", "Root: `../outside/`"),
                        ("Entry: `.workspace-memory/state.md`", "Entry: `outside.md`"),
                        ("Entry: `.workspace-memory/state.md`", "Entry: `.workspace-memory/missing.md`"),
                        ("Router: `.workspace-memory/index.md`", "Router: `.workspace-memory/state.md`"),
                        ("Root: `.workspace-memory/`", "Root: `C:/data/memory`"),
                        ("Root: `.workspace-memory/`", "Root: `.workspace-memory/`\nRoot:bad")]
        for old, new in replacements:
            with self.subTest(new=new):
                agents.write_text(original.replace(old, new))
                self.assertOnlyAgentsRead()

    def test_valid_non_default_root(self):
        (self.root / "docs").mkdir()
        self.memory.rename(self.root / "docs" / "memory")
        agents = self.root / "AGENTS.md"
        agents.write_text(agents.read_text().replace(".workspace-memory", "docs/memory"))
        self.assertEqual(self.cli().returncode, 0)

    def test_existing_dot_prefixed_index_paths(self):
        agents = self.root / "AGENTS.md"
        agents.write_text(agents.read_text().replace("`.workspace-memory", "`./.workspace-memory"))
        self.assertEqual(self.cli().returncode, 0)

    def test_bom_crlf(self):
        for path in self.root.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            path.write_bytes(b"\xef\xbb\xbf" + text.replace("\n", "\r\n").encode())
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_absolute_and_malformed_links(self):
        for target in ["/topics/alpha", "C:/topics/alpha", "C:alpha", "\\\\server\\alpha",
                       "topics\\alpha", "topics//alpha", "topics/../alpha", "https://host/alpha"]:
            with self.subTest(target=target):
                self.note("index.md", f"[[{target}]]")
                self.assertRejected("unsafe wiki link")

    def test_short_links_extensions_aliases_and_fragments(self):
        for target in ["alpha", "topics/alpha.md", "topics/alpha#Current Model|模型", "topics/alpha#^block-id"]:
            with self.subTest(target=target):
                self.note("index.md", f"[[{target}]]")
                self.assertEqual(self.cli().returncode, 0)

    def test_relative_paths_stay_supported(self):
        self.knowledge("beta", body="[[./alpha]]")
        self.knowledge("alpha", body="[[./beta.md|Beta]] [[#Example]]")
        self.assertEqual(self.cli().returncode, 0)
        self.knowledge("alpha", body="[[./missing/beta]]")
        self.assertRejected("broken wiki link")

    def test_ambiguous_basename_rejected_but_exact_path_works(self):
        self.note("other/alpha.md", "# Another alpha")
        self.note("index.md", "[[alpha]]")
        self.assertRejected("ambiguous wiki link")
        self.note("index.md", "[[topics/alpha]]")
        self.assertEqual(self.cli().returncode, 0)

    def test_code_and_comments_are_not_graph_edges(self):
        self.note("index.md", "[[topics/alpha]]\n```md\n[[missing]]\n```\n"
                  "~~~\n[[missing-too]]\n~~~\n`[[inline]]`\n<!-- [[comment]] -->")
        self.assertEqual(self.cli().returncode, 0)
        self.note("index.md", "`[[topics/alpha]]`")
        self.assertRejected("orphaned note")

    def test_unclosed_comments_do_not_create_graph_edges(self):
        self.note("index.md", "[[topics/alpha]]\n<!--\n[[missing]]\n```\n[[missing-too]]")
        self.assertEqual(self.cli().returncode, 0)
        self.note("index.md", "<!--\n[[topics/alpha]]")
        self.assertRejected("orphaned note")

    def test_reciprocity_and_orphans(self):
        self.knowledge("beta")
        self.assertRejected("orphaned note")
        self.knowledge("alpha", body="[[topics/beta]]")
        self.assertRejected("non-reciprocal")
        self.knowledge("beta", body="[[topics/alpha]]")
        self.assertEqual(self.cli().returncode, 0)

    def test_navigation_does_not_need_backlinks_or_english_heading(self):
        alpha = self.memory / "topics" / "alpha.md"
        alpha.write_text(alpha.read_text().replace("## Related", "## 相关"), encoding="utf-8")
        self.assertEqual(self.cli().returncode, 0)

    def test_decision_dormant_rejected(self):
        self.knowledge("choice", kind="decision", status="dormant", body="[[topics/alpha]]")
        self.knowledge("alpha", body="[[decisions/choice]]")
        self.assertRejected("unsupported decision status")

    def test_metadata_constraints(self):
        alpha = self.memory / "topics" / "alpha.md"
        original = alpha.read_text()
        for old, new, message in [("id: alpha", "id: beta", "filename stem"),
                                  ("updated: 2026-10-24", "updated: 2026-02-30", "real YYYY-MM-DD"),
                                  ("summary: Example.", "summary:", "missing frontmatter"),
                                  ("status: active", "status: active\nstatus: archived", "duplicate frontmatter")]:
            with self.subTest(new=new):
                alpha.write_text(original.replace(old, new))
                self.assertRejected(message)

    def test_multiline_summary(self):
        alpha = self.memory / "topics" / "alpha.md"
        alpha.write_text(alpha.read_text().replace("summary: Example.", "summary: >-\n  Long summary\n  continued here."))
        self.assertEqual(self.cli().returncode, 0)

    def test_malformed_required_scalars_are_rejected(self):
        module = self.load_validator()
        alpha = self.memory / "topics/alpha.md"
        original = alpha.read_text()
        cases = [("id: alpha", 'id: "alpha'),
                 ("id: alpha", "id: 'alpha\""),
                 ("summary: Example.", 'summary: "unclosed'),
                 ("summary: Example.", 'summary: "closed" trailing'),
                 ("summary: Example.", "summary: [not, a, sentence]"),
                 ("summary: Example.", "summary: {key: value}"),
                 ("summary: Example.", "summary:\n  - a list item"),
                 ("summary: Example.", "summary:\n  nested: mapping"),
                 ("summary: Example.", "summary: null")]
        for old, new in cases:
            with self.subTest(value=new):
                alpha.write_text(original.replace(old, new), encoding="utf-8")
                errors, _, _ = module.validate(self.root)
                self.assertTrue(errors, new)
                self.assertTrue(any("scalar" in error or "missing frontmatter" in error for error in errors), errors)
        alpha.write_text(original.replace("id: alpha", 'id: "alpha'), encoding="utf-8")
        self.assertRejected("scalar")

    def test_supported_scalar_forms_remain_valid(self):
        module = self.load_validator()
        alpha = self.memory / "topics/alpha.md"
        original = alpha.read_text().replace("id: alpha", "id: 'alpha'").replace("type: topic", 'type: "topic"')
        for summary, expected in [("'Teacher''s editor.'", "Teacher's editor."),
                                  ('"Quoted \\"text\\"."', 'Quoted "text".'),
                                  (">-\n  Long summary\n  continued here.", "Long summary continued here."),
                                  ("First line\n  continued here.", "First line continued here."),
                                  ('"[a list-looking sentence]"', "[a list-looking sentence]")]:
            with self.subTest(summary=summary):
                text = original.replace("summary: Example.", "summary: " + summary).replace("---\n\n", "tags: [editor, memory]\n---\n\n")
                alpha.write_text(text, encoding="utf-8")
                errors, _, _ = module.validate(self.root)
                self.assertEqual(errors, [])
                self.assertEqual(module.parse_frontmatter("alpha", text, [])["summary"], expected)

    def test_duplicate_ids(self):
        self.knowledge("alpha", kind="decision")
        self.assertRejected("duplicate id")

    def replacement_pair(self, status="partially_superseded"):
        self.knowledge("old", kind="decision", status=status,
                       extra='superseded_by: "[[decisions/new]]"\n', body="[[topics/alpha]]")
        self.knowledge("new", kind="decision", extra='supersedes: "[[decisions/old]]"\n', body="[[topics/alpha]]")
        self.knowledge("alpha", body="[[decisions/old]] [[decisions/new]]")

    def test_full_and_partial_replacements(self):
        for status in ("superseded", "partially_superseded"):
            with self.subTest(status=status):
                self.replacement_pair(status)
                result = self.cli()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("WARNING", result.stderr)

    def test_unpaired_typed_replacement_is_error(self):
        self.replacement_pair()
        self.knowledge("new", kind="decision", body="[[decisions/old]] [[topics/alpha]]")
        self.assertRejected("lacks reciprocal supersedes")

    def test_active_old_decision_with_replacement_is_error(self):
        self.replacement_pair("active")
        self.assertRejected("conflicts with status")

    def test_new_partial_status_requires_replacement(self):
        self.knowledge("choice", kind="decision", status="partially_superseded")
        self.assertRejected("requires superseded_by")

    def test_legacy_supersession_is_warning_not_migration_prerequisite(self):
        self.knowledge("old", kind="decision", status="superseded", body="[[decisions/new]]")
        self.knowledge("new", kind="decision", body="[[decisions/old]]")
        self.note("index.md", "[[topics/alpha]] [[decisions/new]]")
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("legacy superseded", result.stderr)

    def test_replacement_cycle(self):
        self.replacement_pair("superseded")
        self.knowledge("old", kind="decision", status="superseded",
                       extra='superseded_by: "[[decisions/new]]"\nsupersedes: "[[decisions/new]]"\n',
                       body="[[topics/alpha]]")
        self.knowledge("new", kind="decision", status="superseded",
                       extra='supersedes: "[[decisions/old]]"\nsuperseded_by: "[[decisions/old]]"\n',
                       body="[[topics/alpha]]")
        self.assertRejected("cycle detected")

    def test_relationship_target_must_be_other_decision(self):
        for target in ("topics/alpha", "decisions/old"):
            with self.subTest(target=target):
                self.knowledge("old", kind="decision", status="superseded",
                               extra=f'superseded_by: "[[{target}]]"\n')
                self.note("index.md", "[[topics/alpha]] [[decisions/old]]")
                self.assertRejected("must target another decision")

    def test_relation_lists_and_multiple_replacements(self):
        self.replacement_pair("superseded")
        self.knowledge("older", kind="decision", status="superseded", extra='superseded_by: "[[decisions/new]]"\n')
        for value in ['["[[decisions/old]]", "[[decisions/older]]"]',
                      '\n  - "[[decisions/old]]"\n  - "[[decisions/older]]"']:
            with self.subTest(value=value):
                self.knowledge("new", kind="decision", extra=f"supersedes: {value}\n", body="[[topics/alpha]]")
                result = self.cli()
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_malformed_relation_quotes_and_lists_are_rejected(self):
        self.replacement_pair()
        module = self.load_validator()
        for value in ('"[[decisions/old]]', '[[decisions/old]]',
                      '["[[decisions/old]]"', '["[[decisions/old]]",,]',
                      "\n  - '[[decisions/old]]"):
            with self.subTest(value=value):
                self.knowledge("new", kind="decision", extra=f"supersedes: {value}\n", body="[[topics/alpha]]")
                errors, _, _ = module.validate(self.root)
                self.assertTrue(any("quoted wiki links" in error for error in errors), errors)

    def test_state_warning_is_not_failure_or_truncation(self):
        state = "# Current State\nLast updated: 2026-10-15\n2026-10-20 local only, not deployed\n" + ("x" * 6100)
        path = self.note("state.md", state)
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("state is", result.stderr)
        self.assertIn("newer than Last updated", result.stderr)
        self.assertEqual(path.read_text(), state)
        self.note("state.md", "# Current State\nLast updated: 2026-10-24\n" + "item\n" * 81)
        self.assertIn("state is", self.cli().stderr)

    def test_invalid_utf8_has_diagnostic_not_traceback(self):
        (self.memory / "topics" / "alpha.md").write_bytes(b"\xff")
        result = self.cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("cannot validate graph", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_external_symlink_is_never_read(self):
        with tempfile.TemporaryDirectory() as outside:
            external = Path(outside) / "private.md"
            external.write_text("DO NOT READ")
            link = self.memory / "escape.md"
            try:
                link.symlink_to(external)
            except OSError as exc:
                self.skipTest(f"symlink unavailable: {exc}")
            module = self.load_validator()
            original = Path.read_text

            def guarded(path, *args, **kwargs):
                self.assertNotEqual(path.resolve(), external.resolve())
                return original(path, *args, **kwargs)

            with patch.object(Path, "read_text", guarded):
                errors, _, _ = module.validate(self.root)
            self.assertTrue(any("escapes memory Root" in error for error in errors))

    def test_resolved_external_file_is_rejected_before_read(self):
        # 不依赖 Windows 创建符号链接权限，直接验证解析后边界与读取顺序。
        link = self.note("escape.md", "not allowed to read")
        external = self.root.parent / "outside-memory.md"
        module = self.load_validator()
        original_resolve = Path.resolve
        original_read = Path.read_text

        def redirected(path, *args, **kwargs):
            return external if path == link else original_resolve(path, *args, **kwargs)

        def guarded(path, *args, **kwargs):
            self.assertNotEqual(path, link)
            return original_read(path, *args, **kwargs)

        with patch.object(Path, "resolve", redirected), patch.object(Path, "read_text", guarded):
            errors, _, _ = module.validate(self.root)
        self.assertTrue(any("escapes memory Root" in error for error in errors))

    def test_resolved_internal_note_file_remains_supported(self):
        alpha = self.memory / "topics" / "alpha.md"
        target = self.memory / "alpha-source.txt"
        target.write_text(alpha.read_text())
        module = self.load_validator()
        original = Path.resolve

        def redirected(path, *args, **kwargs):
            return target if path == alpha else original(path, *args, **kwargs)

        with patch.object(Path, "resolve", redirected):
            errors, _, _ = module.validate(self.root)
        self.assertEqual(errors, [])

    def test_external_directory_is_not_enumerated(self):
        link = self.memory / "escape"
        link.mkdir()
        module = self.load_validator()
        original_resolve = Path.resolve
        original_scan = module.os.scandir

        def redirected(path, *args, **kwargs):
            return self.root.parent if path == link else original_resolve(path, *args, **kwargs)

        def guarded(path):
            self.assertNotEqual(path, link)
            return original_scan(path)

        with patch.object(Path, "resolve", redirected), patch.object(module.os, "scandir", guarded):
            errors, _, _ = module.validate(self.root)
        self.assertTrue(any("escapes memory Root" in error for error in errors))

    def test_example_workspace(self):
        result = subprocess.run([sys.executable, str(SCRIPT), str(SCRIPT.parents[1] / "examples" / "editor-workspace")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_cli_is_read_only(self):
        before = {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(self.cli().returncode, 0)
        after = {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
