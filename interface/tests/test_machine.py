"""What belongs to this machine: which Python runs each stage, kept in a file of its own, and whether that
Python holds the stage's packages. Also the Mac rule for a closed window."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from . import INTERFACE, REAL_PROBE_IMPORTS  # noqa: F401
from rdtii_ui import jobs, lifecycle, machine, probes, settings as settings_mod
from rdtii_ui.pages import extract
from rdtii_ui.server import ApiError, App


class Kept(unittest.TestCase):
    def test_the_file_holds_only_the_names_it_is_for(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "state" / "machine.json"
            self.assertEqual(settings_mod.read_machine(f), {})                       # no file yet
            settings_mod.write_machine({"RDTII_PYTHON_P2": "/opt/p2/bin/python", "RDTII_RUNS_ROOT": "/elsewhere", "RDTII_PYTHON_P1": ""}, f)
            self.assertEqual(json.loads(f.read_text(encoding="utf-8")), {"settings": {"RDTII_PYTHON_P2": "/opt/p2/bin/python"}})
            self.assertEqual(settings_mod.read_machine(f), {"RDTII_PYTHON_P2": "/opt/p2/bin/python"})
            f.write_text("not json", encoding="utf-8")
            self.assertEqual(settings_mod.read_machine(f), {})                       # a damaged file is no file

    def test_the_environment_wins_then_the_machine_then_the_default(self):
        here = sys.executable                                    # an absolute path on whatever system runs the test
        kept = {"RDTII_PYTHON_P2": here}
        s = settings_mod.load({}, machine=kept)
        self.assertEqual((s.python_for("p2"), s.python_source("p2")), (here, "RDTII_PYTHON_P2, kept for this machine"))
        self.assertEqual(s.source["RDTII_PYTHON_P2"], "machine")
        s = settings_mod.load({"RDTII_PYTHON_P2": "python-from-env"}, machine=kept)
        self.assertEqual((s.python_for("p2"), s.python_source("p2")), ("python-from-env", "RDTII_PYTHON_P2"))
        self.assertEqual(settings_mod.load({}).source["RDTII_PYTHON_P2"], "default")   # a caller's own environment reads no file
        s = settings_mod.load({}, machine={"RDTII_RUNS_ROOT": "/elsewhere"})           # not a machine setting
        self.assertEqual(s.source["RDTII_RUNS_ROOT"], "default")

    def test_a_python_is_looked_at_before_it_is_kept(self):
        self.assertEqual(machine.check_python(f'"{sys.executable}"'), sys.executable)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ApiError) as cm:
                machine.check_python(str(Path(d) / "nowhere" / "python.exe"))
            self.assertIn("is not a file on this machine", str(cm.exception))
            fake = Path(d) / "python.txt"
            fake.write_text("not a program", encoding="utf-8")
            with self.assertRaises(ApiError):
                machine.check_python(str(fake))

    def test_set_from_the_page_it_takes_effect_at_once(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "machine.json"
            app = App(settings_mod.load({}))
            app.jobs = jobs.JobManager()
            with mock.patch.object(settings_mod, "machine_file", return_value=f), mock.patch.dict("os.environ", {}, clear=False):
                import os
                os.environ.pop("RDTII_PYTHON_P2", None)
                machine.set_python(app, "RDTII_PYTHON_P2", sys.executable)
                self.assertEqual(settings_mod.read_machine(f), {"RDTII_PYTHON_P2": sys.executable})
                self.assertEqual(app.settings.python_for("p2"), sys.executable)
                row = next(r for r in machine.describe(app)["stages"] if r["stage"] == "p2")
                self.assertEqual((row["label"], row["kept"], row["chosen_by"]), ("Extraction", sys.executable, "RDTII_PYTHON_P2, kept for this machine"))
                machine.set_python(app, "RDTII_PYTHON_P2", "")                       # blank forgets it
                self.assertEqual(settings_mod.read_machine(f), {})
                self.assertNotEqual(app.settings.python_source("p2"), "RDTII_PYTHON_P2, kept for this machine")
                with self.assertRaises(ApiError):
                    machine.set_python(app, "RDTII_RUNS_ROOT", "/x")                 # only the three interpreters


class Packages(unittest.TestCase):
    def test_what_the_import_test_prints_is_read(self):
        class Out:
            def __init__(self, text): self.stdout, self.stderr = text, ""

        with tempfile.TemporaryDirectory() as d:
            ok = REAL_PROBE_IMPORTS("py-ok", Path(d), "a, b", run=lambda *a, **k: Out("imports ok"))
            self.assertEqual(ok, {"ok": True, "missing": ""})
            calls = []

            def run(argv, **kw):
                calls.append(kw.get("env", {}).get("PYTHONPATH"))
                return Out("Traceback (most recent call last):\nModuleNotFoundError: No module named 'pytesseract'")
            bad = REAL_PROBE_IMPORTS("py-bad", Path(d), "rdtii_p2.cli, pytesseract", pythonpath="src", run=run)
            self.assertEqual(bad, {"ok": False, "missing": "pytesseract"})
            REAL_PROBE_IMPORTS("py-bad", Path(d), "rdtii_p2.cli, pytesseract", pythonpath="src", run=run)
            self.assertEqual(calls, ["src"])                                         # asked once, then remembered

    def test_extraction_check_says_before_start_that_its_python_lacks_the_packages(self):
        # 4 October: started by double-click, Extraction failed at its first step on "No module named pytesseract"
        with tempfile.TemporaryDirectory() as d:
            app = App(settings_mod.load({"RDTII_RUNS_ROOT": str(Path(d) / "outputs")}))
            with mock.patch.object(probes, "probe_imports", return_value={"ok": False, "missing": "pytesseract"}):
                checks = {c["check"]: c for c in extract.precheck(app, {"input": "demo_data/mini_raw"})}
            self.assertEqual(checks["interpreter"]["level"], "fail")
            self.assertIn("pytesseract is missing", checks["interpreter"]["text"])
            self.assertIn("Appendix, This machine", checks["interpreter"]["text"])
            ok = {c["check"]: c for c in extract.precheck(app, {"input": "demo_data/mini_raw"})}
            self.assertIn("the stage's packages import", ok["interpreter"]["text"])


class MacWindow(unittest.TestCase):
    """On macOS an application stays running when its last window is closed, so the browser process says nothing."""

    def decide(self, **kw):
        base = {"window_alive": True, "present": 0, "ever_present": True, "busy": False, "quiet_ticks": 0, "age_ticks": 100, "mac": True}
        return lifecycle.decide(**{**base, **kw})

    def test_the_page_going_away_is_the_signal(self):
        G, B = lifecycle.GRACE_TICKS, lifecycle.MAC_BUSY_TICKS
        self.assertEqual(self.decide(quiet_ticks=G - 1), "run")              # a reload reconnects inside the grace
        self.assertEqual(self.decide(quiet_ticks=G), "stop")                 # closed: five seconds, not the two minutes of an orphan
        self.assertEqual(self.decide(present=1, quiet_ticks=10 ** 6), "run")
        self.assertEqual(self.decide(busy=True, quiet_ticks=G), "run")       # a run survives a reloading page
        self.assertEqual(self.decide(busy=True, quiet_ticks=B), "stop")      # and is stopped half a minute after its window is closed
        self.assertEqual(self.decide(ever_present=False, age_ticks=10 ** 6), "run")   # still loading its first page
        self.assertEqual(lifecycle.decide(window_alive=True, present=0, ever_present=True, busy=False, quiet_ticks=G, age_ticks=100), "run")  # elsewhere the process tells

    def test_the_watch_applies_it(self):
        class Proc:
            def poll(self): return None                                      # the browser never exits on a Mac

        app = App(settings_mod.load({}))
        app.presence = lifecycle.Presence()
        app.jobs = None
        ticks = []

        def sleep(_t):
            ticks.append(1)
            if len(ticks) == 2:
                app.presence.enter()
            if len(ticks) == 4:
                app.presence.leave()
        self.assertEqual(lifecycle.watch(app, Proc(), sleep=sleep, mac=True), "the window was closed")
        self.assertEqual(len(ticks), 3 + lifecycle.GRACE_TICKS)


if __name__ == "__main__":
    unittest.main()
