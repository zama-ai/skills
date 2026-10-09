import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from translate_for_cursor import translate


class RemovedReferenceTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        manifest = self.root / ".claude-plugin" / "plugin.json"
        manifest.parent.mkdir()
        manifest.write_text(json.dumps({"name": "zama-protocol"}))
        skill = self.root / "skills" / "example"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: example\ndescription: Example skill\n---\n# Example\n")
        self.reference = skill / "references" / "removed.md"
        self.reference.parent.mkdir()
        self.reference.write_text("# Reference\n")
        self.output = self.root / ".cursor" / "rules"
        self.output.mkdir(parents=True)
        self.run_generator()
        self.reference.unlink()
        self.obsolete = self.output / "zama-protocol-example--removed.mdc"

    def run_generator(self, **options):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return translate(self.root, self.output, dry_run=options.get("dry_run", False),
                             check=options.get("check", False))

    def test_check_rejects_removed_reference_without_mutating_files(self):
        before = {p.name: p.read_text() for p in self.output.iterdir()}
        self.assertFalse(self.run_generator(check=True))
        self.assertEqual(before, {p.name: p.read_text() for p in self.output.iterdir()})

    def test_generation_removes_obsolete_rule_and_preserves_project_rules(self):
        unrelated = self.output / "project-style.mdc"
        same_prefix = self.output / "zama-protocol-team-notes.mdc"
        for rule in (unrelated, same_prefix):
            rule.write_text("Project rules\n")
        self.assertTrue(self.run_generator())
        self.assertFalse(self.obsolete.exists())
        for rule in (unrelated, same_prefix):
            self.assertEqual("Project rules\n", rule.read_text())
        self.assertTrue(self.run_generator(check=True))

    def test_generation_replaces_symlinked_rules_without_touching_their_target(self):
        rule = self.output / "zama-protocol-example.mdc"
        target = self.root / "other-checkout.mdc"
        target.write_text(rule.read_text())
        rule.unlink()
        rule.symlink_to(target)
        (self.output / "zama-protocol-example--dangling.mdc").symlink_to(self.root / "missing.mdc")
        self.assertTrue(self.run_generator())
        self.assertFalse(rule.is_symlink())
        self.assertEqual(target.read_text(), rule.read_text())
        self.assertFalse((self.output / "zama-protocol-example--dangling.mdc").is_symlink())

    def test_dry_run_preserves_obsolete_rule(self):
        before = self.obsolete.read_text()
        self.assertTrue(self.run_generator(dry_run=True))
        self.assertEqual(before, self.obsolete.read_text())


if __name__ == "__main__":
    unittest.main()
