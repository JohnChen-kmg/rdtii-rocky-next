"""Path rules and tool discovery that must hold on Windows, macOS and Linux alike."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from . import INTERFACE  # noqa: F401
from rdtii_ui import envbuild, paths, probes, settings as settings_mod


def _make_venv(root: Path) -> Path:
    """A folder shaped like a virtual environment for the system the test runs on."""
    parts = ("Scripts", "python.exe") if os.name == "nt" else ("bin", "python")
    py = root.joinpath(*parts)
    py.parent.mkdir(parents=True)
    py.write_bytes(b"")
    return py


class VenvPython(unittest.TestCase):
    def test_both_layouts(self):
        with tempfile.TemporaryDirectory() as d:
            win = Path(d) / "w"
            (win / "Scripts").mkdir(parents=True)
            (win / "Scripts" / "python.exe").write_bytes(b"")
            posix = Path(d) / "p"
            (posix / "bin").mkdir(parents=True)
            (posix / "bin" / "python").write_bytes(b"")
            self.assertEqual(paths.venv_python(win, "nt"), win / "Scripts" / "python.exe")
            self.assertIsNone(paths.venv_python(win, "posix"))
            self.assertEqual(paths.venv_python(posix, "posix"), posix / "bin" / "python")
            self.assertIsNone(paths.venv_python(posix, "nt"))
            self.assertIsNone(paths.venv_python(Path(d) / "absent"))


class ChildPath(unittest.TestCase):
    def test_given_folders_first_and_nothing_twice(self):
        got = paths.child_path("/usr/bin:/bin:/opt/homebrew/bin", ["/opt/homebrew/bin", "/opt/x"], pathsep=":", case_sensitive=True)
        self.assertEqual(got, "/opt/homebrew/bin:/opt/x:/usr/bin:/bin")

    def test_windows_compares_without_case_and_trailing_slash(self):
        got = paths.child_path(r"C:\Windows;c:\program files\tesseract-ocr\\", [r"C:\Program Files\Tesseract-OCR"],
                               pathsep=";", case_sensitive=False)
        self.assertEqual(got, r"C:\Program Files\Tesseract-OCR;C:\Windows")

    def test_an_empty_path_stays_usable(self):
        self.assertEqual(paths.child_path("", [], pathsep=":"), "")
        self.assertEqual(paths.child_path("", ["/a"], pathsep=":"), "/a")


class Expand(unittest.TestCase):
    def test_home_is_expanded_and_bare_commands_are_recognised(self):
        self.assertEqual(paths.expand("~"), os.path.expanduser("~"))
        self.assertTrue(paths.is_bare_command("python3"))
        self.assertFalse(paths.is_bare_command(".venv/bin/python"))
        self.assertFalse(paths.is_bare_command(r".venv\Scripts\python.exe"))
        self.assertFalse(paths.is_bare_command(""))


class Tools(unittest.TestCase):
    def test_tesseract_candidates_per_system(self):
        win = probes.tesseract_candidates("win32", {"LOCALAPPDATA": r"C:\Users\x\AppData\Local"})
        self.assertIn(r"C:\Program Files\Tesseract-OCR\tesseract.exe", win)
        self.assertIn(r"C:\Users\x\AppData\Local\Programs\Tesseract-OCR\tesseract.exe", win)
        self.assertEqual(probes.tesseract_candidates("darwin", {})[0], "/opt/homebrew/bin/tesseract")
        self.assertIn("/usr/bin/tesseract", probes.tesseract_candidates("linux", {}))

    def test_install_hint_per_system(self):
        self.assertIn("winget", probes.install_hint("tesseract", "win32"))
        self.assertIn("brew", probes.install_hint("tesseract", "darwin"))
        self.assertIn("apt", probes.install_hint("tesseract", "linux"))
        self.assertIn("playwright", probes.install_hint("chromium", "darwin"))

    def test_the_setting_names_the_program_before_any_search(self):
        with tempfile.TemporaryDirectory() as d:
            exe = Path(d) / "tesseract-here"
            exe.write_bytes(b"")
            self.assertEqual(probes.probe_tesseract(str(exe)), {"ok": True, "path": str(exe)})

    def test_the_stage_environment_carries_a_path(self):
        eng = envbuild.EngineState(envbuild.load_engines(settings_mod.REPO / "stages" / "p3-map"))
        env, public = envbuild.build_env("p2", eng, envbuild.KeyHolder(), {}, with_engine=False)
        self.assertTrue(env.get("PATH"))
        self.assertNotIn("PATH", public)        # never shown on the run panel
        for d in probes.tool_path_dirs():
            self.assertIn(d, env["PATH"].split(os.pathsep))


class StagePython(unittest.TestCase):
    def test_a_relative_setting_is_made_absolute_and_a_bare_command_is_not(self):
        s = settings_mod.load({"RDTII_PYTHON_P2": ".venv/x/python", "RDTII_PYTHON_P3": "python3"})
        self.assertEqual(Path(s.python_for("p2")), settings_mod.REPO / ".venv" / "x" / "python")
        self.assertEqual(s.python_source("p2"), "RDTII_PYTHON_P2")
        self.assertEqual(s.python_for("p3"), "python3")

    def test_a_stage_venv_is_used_when_no_interpreter_is_named(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            py = _make_venv(root / "stages" / "p2-extract" / ".venv")
            repo_py = _make_venv(root / ".venv")
            with mock.patch.object(settings_mod, "REPO", root):
                s = settings_mod.load({})
                self.assertEqual(Path(s.python_for("p2")), py)
                self.assertIn(".venv", s.python_source("p2"))
                self.assertEqual(Path(s.python_for("p3")), repo_py)      # no stage venv: the repository's
                off = settings_mod.load({"RDTII_PYTHON_AUTO": "0"})
                self.assertNotEqual(Path(off.python_for("p2")), py)
                named = settings_mod.load({"RDTII_PYTHON_P2": "python3"})
                self.assertEqual(named.python_for("p2"), "python3")      # a named interpreter always wins


class FileSetting(unittest.TestCase):
    def test_a_relative_baseline_becomes_one_absolute_path(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "reference").mkdir()
            (root / "reference" / "baseline.xlsx").write_bytes(b"")
            (root / "stages" / "p3-map").mkdir(parents=True)
            (root / "stages" / "p3-map" / "only_here.xlsx").write_bytes(b"")
            with mock.patch.object(settings_mod, "REPO", root):
                s = settings_mod.load({"BASELINE_PATH": "reference/baseline.xlsx", "BASELINE_R2_PATH": "only_here.xlsx"})
                self.assertEqual(Path(s.baseline_path), root / "reference" / "baseline.xlsx")
                self.assertEqual(Path(s.baseline_r2_path), root / "stages" / "p3-map" / "only_here.xlsx")
                missing = settings_mod.load({"BASELINE_PATH": "nowhere.xlsx"})
                self.assertEqual(Path(missing.baseline_path), root / "nowhere.xlsx")
        self.assertEqual(settings_mod.load({}).baseline_path, "")


class Reviewer(unittest.TestCase):
    def test_a_name_is_always_there(self):
        self.assertEqual(settings_mod.load({"RDTII_REVIEWER": "Judge 3"}).reviewer, "Judge 3")
        self.assertTrue(settings_mod.load({}).reviewer)
        with mock.patch("getpass.getuser", side_effect=KeyError("no login")):
            self.assertEqual(settings_mod.load({}).reviewer, "reviewer")


if __name__ == "__main__":
    unittest.main()
