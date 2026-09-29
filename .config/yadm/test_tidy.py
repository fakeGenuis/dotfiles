"""Interactive tidy tests; pacman changes are mocked."""

from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pkgdecl import main


class TidyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.config = self.folder / "packages.toml"
        self.private = self.folder / "private/packages.toml"
        self.private.parent.mkdir()
        self.config.write_text('profiles={desktop=2,wsl=1}\n[tools]\npackages=[]\n'
                               '[private]\ndirectory="private"\n')
        self.private.write_text('# private\n[tools]\npackages=[]\n')
        self.before = {p: p.read_text() for p in (self.config, self.private)}
        self.installed = {name: dict(name=name, installed=True, reason="explicit",
                                    description="Example", provides=[], required_by=[], optional_for=[])
                          for name in ("alpha", "beta")}

    def run_tidy(self, answers, pacman_code=0):
        output = StringIO()
        with patch("pkgdecl.installed_packages", return_value=self.installed), \
                patch("builtins.input", side_effect=answers), \
                patch("pkgdecl.subprocess.run") as run, \
                redirect_stdout(output), redirect_stderr(output):
            run.return_value.returncode = pacman_code
            code = main(["tidy", "--file", str(self.config), "--profile", "wsl"])
        return code, output.getvalue(), run

    def test_adopt_private_and_mark_dependency_after_confirmation(self):
        code, output, run = self.run_tidy(["1", "a", "2", "2", "1", "d", "y"])
        self.assertEqual(code, 0, output)
        self.assertIn('"alpha:01"', self.private.read_text())
        self.assertEqual(self.config.read_text(), self.before[self.config])
        self.assertIn("Mark as dependencies: beta", output)
        run.assert_called_once_with(["sudo", "pacman", "-D", "--asdeps", "beta"])

    def test_decline_writes_nothing(self):
        code, output, run = self.run_tidy(["1", "a", "2", "2", "1", "d", "n"])
        self.assertEqual(code, 0, output)
        for path, text in self.before.items():
            self.assertEqual(path.read_text(), text)
        run.assert_not_called()

    def test_multiple_batches_accumulate_in_one_file(self):
        code, output, run = self.run_tidy(["1", "a", "1", "2", "1", "a", "1", "2", "y"])
        self.assertEqual(code, 0, output)
        self.assertIn('"alpha:01"', self.config.read_text())
        self.assertIn('"beta:01"', self.config.read_text())
        run.assert_not_called()

    def test_skip_and_interruption_have_no_effects(self):
        for answers in (["1,2", "s"], ["1", "a", EOFError()]):
            code, output, run = self.run_tidy(answers)
            self.assertIn(code, (0, 130), output)
            for path, text in self.before.items():
                self.assertEqual(path.read_text(), text)
            run.assert_not_called()

    def test_pacman_failure_reports_partial_completion(self):
        code, output, _ = self.run_tidy(["1", "a", "2", "2", "1", "d", "y"], pacman_code=1)
        self.assertEqual(code, 1)
        self.assertIn("pacman failed", output)
        self.assertIn('"alpha:01"', self.private.read_text())
        self.assertNotIn("Done.", output)


if __name__ == "__main__":
    unittest.main()
