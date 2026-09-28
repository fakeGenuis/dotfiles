"""Regression tests for tree selection and dependencies."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from pkgdecl import load_tree, project


class DeclarationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def write(self, text, name="packages.toml", profiles="{personal=4, laboratory=2, laptop=1}"):
        path = self.folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text((f"profiles = {profiles}\n" if name == "packages.toml" else "") + text)
        return path

    def names(self, root, profile="laptop"):
        return {item["name"] for item in project(root, profile)}

    def test_overrides_and_configured_profiles(self):
        root = load_tree(self.write('''
[system]
on = 0b10
packages = ["base:11", "linux", "off:00"]
[system.tools]
on = 0b01
packages = ["wsl-tool"]
''', profiles="{workstation=2, wsl=1}"))
        self.assertEqual(self.names(root, "wsl"), {"base", "wsl-tool"})
        self.assertEqual(self.names(root, "workstation"), {"base", "linux"})

    def test_mounts_inherit_and_keep_local_dependency_scope(self):
        child = self.write('''
[app]
on = 0b001
packages = ["app"]
depends_on = ["service"]
[service]
on = 0b001
packages = ["service"]
[other]
packages = ["inherited"]
''', "private/packages.toml")
        root = load_tree(self.write('''
[service]
on = 0b000
[mount]
on = 0b110
directory = "private"
'''))
        self.assertEqual(self.names(root), {"app", "service"})
        self.assertEqual(self.names(root, "personal"), {"inherited"})
        self.assertEqual(project(root, "laptop")[0]["sources"][0],
                         dict(file=str(child), node="mount.app", on="0b001"))

    def test_duplicates_and_symbolic_groups(self):
        root = load_tree(self.write('''
[first]
packages = ["shared", "shared"]
groups = ["example-group"]
[second]
packages = ["shared", "hidden:000"]
'''))
        items = project(root, "laptop")
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["kind"], "group")
        self.assertEqual([s["node"] for s in items[1]["sources"]], ["first", "second"])

    def test_dependencies_do_not_enable_nodes(self):
        for mask in ("111", "000"):
            root = load_tree(self.write(f'''
[app]
on = 0b{mask}
depends_on = ["service"]
[app.child]
packages = ["restored:001"]
[service]
on = 0b110
'''))
            with self.assertRaisesRegex(ValueError, "dependency excluded"):
                project(root, "laptop")

    def test_cycles_and_missing_references(self):
        for text, error in [
            ('[a]\ndepends_on=["b"]\n[b]\ndepends_on=["a"]', "cycle"),
            ('[a]\ndepends_on=["missing"]', "unknown dependencies"),
            ('[loop]\ndirectory="."', "File cycle"),
        ]:
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, error):
                load_tree(self.write(text))

    def test_optional_and_repeated_mounts(self):
        self.write('packages=["shared"]', "private/packages.toml")
        root = load_tree(self.write('''
[a]
directory = "private"
[b]
directory = "private"
[missing]
directory = "absent"
optional = true
'''))
        self.assertEqual(len(project(root, "laptop")[0]["sources"]), 2)
        with self.assertRaises(FileNotFoundError):
            load_tree(self.write('[missing]\ndirectory="absent"'))

    def test_cli_and_bad_suffix(self):
        path = self.write('packages=["base:111"]')
        script = Path(__file__).with_name("pkgdecl.py")
        command = [sys.executable, str(script), "list", "--file", str(path),
                   "--profile", "laptop", "--json"]
        result = subprocess.run(command, cwd=self.folder, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)[0]["name"], "base")
        self.write('packages=["base:wrong"]')
        result = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("invalid package suffix", result.stderr)


if __name__ == "__main__":
    unittest.main()
