"""Tests for installed-state classification and read-only queries."""

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pkgdecl import compare, expand_groups, installed_packages, main, pacman


SOURCE = dict(file="/private/packages.toml", node="mail", on="0b1")


def package(name, reason="explicit", provides=(), required=(), optional=()):
    return dict(name=name, installed=True, reason=reason, version="1",
                description="Mail utility", provides=list(provides),
                required_by=list(required), optional_for=list(optional))


class StateTests(unittest.TestCase):
    def test_providers_dependencies_and_orphans(self):
        installed = {p["name"]: p for p in [
            package("mail-fork", provides=["mail"]),
            package("lib", "dependency", required=["app"]),
            package("optional", "dependency", optional=["app"]),
            package("orphan", "dependency"),
            package("explicit-lib", required=["app"]),
        ]}
        rows = {r["name"]: r for r in compare({"mail": [SOURCE], "missing": [SOURCE]}, installed)}
        self.assertNotIn("mail", rows)
        self.assertEqual(rows["mail-fork"]["declarations"], ["mail"])
        self.assertEqual(rows["mail-fork"]["sources"], [SOURCE])
        self.assertFalse(rows["missing"]["installed"])
        self.assertEqual({n for n, r in rows.items() if r["orphan"]}, {"orphan"})
        self.assertFalse(rows["explicit-lib"]["declared"])

    def test_exact_package_takes_precedence_over_provider(self):
        installed = {"mail": package("mail"), "fork": package("fork", provides=["mail"])}
        rows = {r["name"]: r for r in compare({"mail": [SOURCE]}, installed)}
        self.assertTrue(rows["mail"]["declared"])
        self.assertFalse(rows["fork"]["declared"])

    @patch("pkgdecl.pacman", return_value="editors app\neditors new-app\n")
    def test_group_expansion_includes_uninstalled_members(self, query):
        entries = [dict(kind="group", name="editors", sources=[SOURCE]),
                   dict(kind="package", name="app", sources=[SOURCE])]
        result = expand_groups(entries)
        self.assertEqual(set(result), {"app", "new-app"})
        self.assertEqual(len(result["app"]), 2)
        self.assertEqual(result["new-app"][0]["group"], "editors")
        query.assert_called_once_with("-Sgg")
        with self.assertRaisesRegex(ValueError, "Unknown repository group"):
            expand_groups([dict(kind="group", name="absent", sources=[SOURCE])])

    @patch("pkgdecl.pacman", return_value="""Name : fork
Version : 1.0
Description : A mail utility
              with wrapped text
Provides : mail=1.0
Required By : app
              second-app
Optional For : None
Install Reason : Installed as a dependency for another package
""")
    def test_pacman_fields_and_wrapped_lines(self, query):
        item = installed_packages()["fork"]
        self.assertEqual(item["provides"], ["mail"])
        self.assertEqual(item["reason"], "dependency")
        self.assertEqual(item["required_by"], ["app", "second-app"])
        self.assertEqual(item["description"], "A mail utility with wrapped text")

    def test_cli_filters_search_and_names(self):
        installed = {"fork": package("fork", provides=["mail"]),
                     "lib": package("lib", "dependency", required=["fork"]),
                     "extra": package("extra")}
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / "packages.toml"
            config.write_text('profiles={wsl=1}\npackages=["mail", "missing"]')
            for command, options, expected in [
                ("missing", [], "missing\n"),
                ("dependencies", [], "lib\n"),
                ("undeclared", [], "extra\n"),
                ("undeclared", ["--all"], "extra\nlib\n"),
                ("installed", [], "extra\nfork\nlib\n"),
                ("orphans", [], ""),
                ("explain", ["mail"], "fork\n"),
                ("search", ["MAIL"], "extra\nfork\nlib\n"),
                ("search", [str(config)], "fork\nmissing\n"),
            ]:
                with self.subTest(command=command, options=options):
                    output = StringIO()
                    with patch("pkgdecl.installed_packages", return_value=installed), redirect_stdout(output):
                        code = main([command, *options, "--file", str(config), "--profile", "wsl", "--names"])
                    self.assertEqual(code, 0)
                    self.assertEqual(output.getvalue(), expected)

    @patch("pkgdecl.subprocess.run")
    def test_pacman_errors_are_not_empty_results(self, run):
        run.return_value.returncode = 1
        run.return_value.stderr = "database unavailable"
        with self.assertRaisesRegex(ValueError, "database unavailable"):
            pacman("-Qi")
        self.assertEqual(run.call_args.kwargs["env"]["LC_ALL"], "C")


if __name__ == "__main__":
    unittest.main()
