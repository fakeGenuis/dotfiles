"""Tests for previewing and writing declarations."""

from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from pkgdecl import insert_packages, load_tree, main, project


class AdoptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.config = self.folder / "packages.toml"
        self.write('[tools]\npackages = ["old"] # keep this\n')
        self.installed = {name: dict(name=name, installed=True, reason="explicit",
                                    description="", provides=[], required_by=[], optional_for=[])
                          for name in ("foo", "bar")}

    def write(self, text):
        self.config.write_text('profiles = {desktop=2, wsl=1}\n' + text)

    def adopt(self, *options):
        output, errors = StringIO(), StringIO()
        with patch("pkgdecl.installed_packages", return_value=self.installed), \
                redirect_stdout(output), redirect_stderr(errors):
            code = main(["adopt", "--file", str(self.config), "--profile", "wsl", *options])
        return code, output.getvalue(), errors.getvalue()

    def test_preview_batch_write_and_idempotence(self):
        before = self.config.read_text()
        code, output, error = self.adopt("foo", "bar", "--node", "tools")
        self.assertEqual(code, 0, error)
        self.assertIn('+packages = ["foo:01", "bar:01", "old"] # keep this', output)
        self.assertEqual(self.config.read_text(), before)
        code, _, error = self.adopt("foo", "bar", "--node", "tools", "--write")
        self.assertEqual(code, 0, error)
        root = load_tree(self.config)
        self.assertEqual({p["name"] for p in project(root, "wsl")}, {"old", "foo", "bar"})
        self.assertEqual({p["name"] for p in project(root, "desktop")}, {"old"})
        after = self.config.read_text()
        code, output, _ = self.adopt("foo", "--node", "tools", "--write")
        self.assertEqual(code, 0)
        self.assertIn("No changes", output)
        self.assertEqual(self.config.read_text(), after)

    def test_private_optional_file_stays_external(self):
        self.write('[private]\ndirectory="private"\noptional=true\non=1\n')
        before = self.config.read_text()
        target = self.folder / "private/packages.toml"
        options = ["foo", "--target", str(target), "--node", "tools"]
        code, _, error = self.adopt(*options)
        self.assertEqual(code, 0, error)
        self.assertFalse(target.exists())
        code, _, error = self.adopt(*options, "--write")
        self.assertEqual(code, 0, error)
        self.assertEqual(tomllib.loads(target.read_text())["tools"]["packages"], ["foo"])
        self.assertEqual(self.config.read_text(), before)

    def test_mask_choice_and_new_subtree(self):
        code, _, error = self.adopt("foo", "--node", "tools.extra", "--on", "11", "--write")
        self.assertEqual(code, 0, error)
        self.assertEqual(tomllib.loads(self.config.read_text())["tools"]["extra"]["packages"], ["foo"])
        self.assertIn("foo", {p["name"] for p in project(load_tree(self.config), "desktop")})

    def test_excluded_existing_declaration_is_not_duplicated(self):
        self.write('[tools]\npackages=["foo:10"]\n')
        before = self.config.read_text()
        code, _, error = self.adopt("foo", "--node", "other", "--write")
        self.assertEqual(code, 1)
        self.assertIn("edit its mask", error)
        self.assertEqual(self.config.read_text(), before)

    def test_dependencies_are_checked_before_writing(self):
        self.write('[tools]\non=0\ndepends_on=["service"]\n[service]\non=0\n')
        before = self.config.read_text()
        code, _, error = self.adopt("foo", "--node", "tools", "--write")
        self.assertEqual(code, 1)
        self.assertIn("dependency excluded", error)
        self.assertEqual(self.config.read_text(), before)

    def test_non_explicit_packages_and_unmounted_files_are_rejected(self):
        self.installed["foo"]["reason"] = "dependency"
        code, _, error = self.adopt("foo", "--node", "tools")
        self.assertEqual(code, 1)
        self.assertIn("Not explicitly installed", error)
        code, _, error = self.adopt("bar", "--node", "tools", "--target", str(self.folder / "other.toml"))
        self.assertEqual(code, 1)
        self.assertIn("not mounted", error)

    def test_multiline_comments_and_other_tables_are_preserved(self):
        before = '# header\n[tools]\npackages = [ # tools\n  "old", # retained\n]\n[other]\non=0\n'
        after = insert_packages(before, "tools", ["foo:01"])
        self.assertEqual(after, before.replace('  "old"', '  "foo:01",\n  "old"'))
        for before, node in [("packages=[]", ""), ("[tools]", "tools"),
                             ('["tools"]\npackages=["old"]\n', "tools"),
                             ('[tools.child]\npackages=[]\n', "tools")]:
            after = insert_packages(before, node, ["foo"])
            table = tomllib.loads(after)
            if node:
                table = table[node]
            self.assertEqual(table["packages"][0], "foo")


if __name__ == "__main__":
    unittest.main()
