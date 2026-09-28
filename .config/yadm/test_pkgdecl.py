"""Tests for declaration semantics and the read-only CLI."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from pkgdecl import DeclarationError, load_tree, project, summarize


SCRIPT = Path(__file__).with_name("pkgdecl.py")


class DeclarationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def write(self, text, name="packages.toml"):
        path = self.folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def names(self, root, profile="laptop"):
        return {entry.name for entry in project(root, profile)}

    def test_masks_and_leaf_overrides(self):
        root = load_tree(self.write('''
on = 0b111
[system]
on = 0b110
packages = ["base:111", "linux", "off:000"]
[system.tools]
on = 0b001
packages = ["wsl-tool"]
[system.tools.disabled]
on = 0b000
packages = ["disabled"]
[system.tools.disabled.restored]
on = 0b111
packages = ["restored"]
'''))
        self.assertEqual(self.names(root), {"base", "wsl-tool", "restored"})
        self.assertEqual(self.names(root, "personal"), {"base", "linux", "restored"})

    def test_mount_inherits_and_can_restore_selection(self):
        child = self.write('''
enable_default = true
[plain]
packages = ["inherited"]
[override]
on = 0b001
packages = ["restored"]
''', "private/packages.toml")
        path = self.write('''
[mount]
on = 0b110
directory = "private"
''')
        root = load_tree(path)
        self.assertEqual(self.names(root), {"restored"})
        self.assertEqual(self.names(root, "personal"), {"inherited"})
        entry = project(root, "laptop")[0]
        self.assertEqual(entry.source.file, child)
        self.assertEqual(entry.source.node, "mount.override")

    def test_duplicate_packages_keep_sources_and_groups_stay_symbolic(self):
        root = load_tree(self.write('''
[first]
packages = ["shared", "shared"]
groups = ["example-group"]
[second]
packages = ["shared", "hidden:000"]
'''))
        items = summarize(project(root, "laptop"))
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["kind"], "group")
        self.assertEqual([s["node"] for s in items[1]["sources"]], ["first", "second"])

    def test_dependencies_do_not_enable_nodes(self):
        root = load_tree(self.write('''
[app]
packages = ["app"]
depends_on = ["service"]
[service]
on = 0b110
packages = ["service"]
'''))
        with self.assertRaisesRegex(DeclarationError, "laptop: dependency excluded"):
            project(root, "laptop")
        self.assertEqual(self.names(root, "personal"), {"app", "service"})

    def test_restored_leaf_checks_ancestor_dependencies(self):
        root = load_tree(self.write('''
[app]
on = 0b000
depends_on = ["service"]
[app.child]
packages = ["restored:001"]
[service]
on = 0b000
'''))
        with self.assertRaisesRegex(DeclarationError, "dependency excluded"):
            project(root, "laptop")

    def test_mount_dependencies_use_source_file_scope(self):
        self.write('''
[app]
packages = ["app"]
depends_on = ["service"]
[service]
packages = ["service"]
''', "private/packages.toml")
        root = load_tree(self.write('''
[service]
on = 0b000
[private]
directory = "private"
'''))
        self.assertEqual(self.names(root), {"app", "service"})

    def test_dependency_cycles_and_unknown_targets(self):
        for text, error in [
            ('[a]\ndepends_on=["b"]\n[b]\ndepends_on=["a"]', "Dependency cycle"),
            ('[a]\ndepends_on=["missing"]', "Unknown dependency"),
        ]:
            with self.subTest(error=error):
                with self.assertRaisesRegex(DeclarationError, error):
                    load_tree(self.write(text))

    def test_file_cycles_and_missing_mounts(self):
        with self.assertRaisesRegex(DeclarationError, "File cycle"):
            load_tree(self.write('[loop]\ndirectory="."'))
        with self.assertRaises(DeclarationError):
            load_tree(self.write('[mount]\non=0\ndirectory="missing"'))
        root = load_tree(self.write('[mount]\ndirectory="missing"\noptional=true'))
        self.assertEqual(self.names(root), set())

    def test_repeated_mounts_are_not_cycles(self):
        self.write('packages=["shared"]', "private/packages.toml")
        root = load_tree(self.write('''
[a]
directory = "private"
[b]
directory = "private"
'''))
        self.assertEqual(len(summarize(project(root, "laptop"))[0]["sources"]), 2)

    def test_invalid_fields_and_suffixes(self):
        for text in (
            'on=true', 'on=8', 'on=-1', 'on="111"', 'on=[]',
            'packages="base"', 'packages=[1]', 'packages=["base:11"]',
            'packages=["base:0b111"]', 'packages=[":111"]',
            'packages=["base:foo:111"]', 'packages=["two names"]',
            'groups=["group:111"]', 'depends_on=[false]',
            'enabled=false', 'optional=true', 'directory=12',
            'directory="x"\noptional=1', 'enable_default=false',
        ):
            with self.subTest(text=text):
                with self.assertRaises(DeclarationError):
                    load_tree(self.write(text))

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              cwd=self.folder, text=True, capture_output=True)

    def test_cli_json_and_errors(self):
        path = self.write('packages=["base:111"]')
        result = self.run_cli("list", "--file", str(path), "--profile", "laptop", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)[0]["name"], "base")
        self.assertEqual(result.stderr, "")
        path.write_text('on=true')
        result = self.run_cli("check", "--file", str(path))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn(str(path), result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_defaults_to_all_profiles(self):
        path = self.write('packages=["base"]')
        result = self.run_cli("check", "--file", str(path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "Valid: personal, laboratory, laptop")
        result = self.run_cli("list", "--file", str(path))
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
