"""Mapping's Output lists its runs with when each began, when it last ran and how it stands.

What must hold: all of it is read, never written; a run counts as complete only when it wrote its rows; and
a run folder with no rows is listed, so a run is never just missing, but cannot be examined."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from . import INTERFACE
from rdtii_ui import settings as settings_mod
from rdtii_ui.pages import mapping

FIXTURE_ROWS = INTERFACE / "fixtures" / "submission" / "records_SG.csv"


class _Jobs:
    def __init__(self, *jobs):
        self._jobs = list(jobs)

    def all(self):
        return self._jobs


def _job(folder, status):
    return SimpleNamespace(out_dir=folder, status=status, stage="p3")


class Times(unittest.TestCase):
    def test_began_is_the_stamp_the_run_folders_name_starts_with(self):
        self.assertEqual(mapping.run_times("20261005-021700_A", {})[0], "2026-10-05 02:17")
        self.assertEqual(mapping.run_times("20261005-0217_A_quick", {})[0], "2026-10-05 02:17")
        self.assertEqual(mapping.run_times("20261005-021700", {})[0], "2026-10-05 02:17")

    def test_without_a_stamp_it_is_the_manifests_own_start(self):
        manifest = {"created": "2026-09-27T04:33:19", "entries": [{"at": "2026-09-27T04:33:19"}, {"at": "2026-09-29T17:57:26"}, {"at": "2026-09-28T06:20:16"}]}
        self.assertEqual(mapping.run_times("fixtures (real rows from run_2026-09-27)", manifest), ("2026-09-27 04:33", "2026-09-29 17:57"))

    def test_nothing_recorded_gives_nothing(self):
        self.assertEqual(mapping.run_times("filed submission (frozen)", {}), ("", ""))
        self.assertEqual(mapping.run_times("20269999-9999_A", {"created": "soon", "entries": [{"stage": "ingest"}, "x"]}), ("", ""))


class State(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.run = Path(self.tmp.name) / "20261005-021700_A"
        self.run.mkdir()

    def test_a_run_is_complete_only_when_it_wrote_its_rows(self):
        self.assertEqual(mapping.run_state(self.run, True), "complete")
        self.assertEqual(mapping.run_state(self.run, False), "not complete")

    def test_this_sessions_runs_say_running_and_stopped(self):
        self.assertEqual(mapping.run_state(self.run, False, _Jobs(_job(self.run, "running"))), "running")
        self.assertEqual(mapping.run_state(self.run, True, _Jobs(_job(self.run, "queued"))), "running")
        self.assertEqual(mapping.run_state(self.run, True, _Jobs(_job(self.run, "cancelled"))), "stopped")
        self.assertEqual(mapping.run_state(self.run, False, _Jobs(_job(self.run, "failed"))), "not complete")
        self.assertEqual(mapping.run_state(self.run, True, _Jobs(_job(self.run.parent / "another", "running"))), "complete")


class Listed(unittest.TestCase):
    def _root(self, root: Path) -> settings_mod.Settings:
        done = root / "map" / "20261005-021700_A" / "out"
        (done / "submission").mkdir(parents=True)
        (done / "submission" / "records_SG.csv").write_bytes(FIXTURE_ROWS.read_bytes())
        (done / "run_manifest.json").write_text(json.dumps({"created": "2026-10-05T02:17:03", "entries": [{"stage": "verify", "at": "2026-10-05T03:02:11"}]}), encoding="utf-8")
        half = root / "map" / "20261005-031500_B" / "out"
        half.mkdir(parents=True)
        (half / "run_manifest.json").write_text(json.dumps({"entries": [{"stage": "ingest", "at": "2026-10-05T03:15:30"}]}), encoding="utf-8")
        (root / "map" / "20261004-101010_C").mkdir()
        return settings_mod.load({"RDTII_RUNS_ROOT": str(root)})

    def test_finished_runs_carry_their_times_and_state(self):
        with tempfile.TemporaryDirectory() as d:
            s = self._root(Path(d))
            run = next(r for r in mapping.list_runs(s) if r["name"] == "20261005-021700_A")
            self.assertEqual((run["began"], run["last_run"], run["run_state"]), ("2026-10-05 02:17", "2026-10-05 03:02", "complete"))
            self.assertTrue(run["selectable"] and run["made_here"] and run["rows"] > 0)
            self.assertEqual(Path(run["dir"]), Path(d) / "map" / "20261005-021700_A")
            for other in mapping.list_runs(s):
                self.assertIn("run_state", other, other["id"])
                self.assertEqual(other["made_here"], other["name"] == "20261005-021700_A", other["id"])

    def test_a_run_folder_with_no_rows_is_listed_and_cannot_be_examined(self):
        with tempfile.TemporaryDirectory() as d:
            s = self._root(Path(d))
            names = [r["name"] for r in mapping.list_runs(s)]
            self.assertNotIn("20261005-031500_B", names)                 # the list of runs to examine is unchanged
            rest = mapping.list_unfinished(s)
            self.assertEqual([r["name"] for r in rest], ["20261005-031500_B", "20261004-101010_C"])      # newest first
            half, empty = rest
            self.assertEqual((half["began"], half["last_run"], half["run_state"], half["rows"], half["selectable"]), ("2026-10-05 03:15", "2026-10-05 03:15", "not complete", 0, False))
            self.assertEqual((empty["began"], empty["last_run"], empty["run_state"]), ("2026-10-04 10:10", "", "not complete"))
            self.assertEqual(Path(empty["dir"]), Path(d) / "map" / "20261004-101010_C")
            running = mapping.list_unfinished(s, _Jobs(_job(Path(d) / "map" / "20261005-031500_B", "running")))
            self.assertEqual(running[0]["run_state"], "running")

    def test_reading_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            s = self._root(Path(d))
            before = sorted(str(p.relative_to(d)) for p in Path(d).rglob("*"))
            mapping.list_runs(s, _Jobs())
            mapping.list_unfinished(s, _Jobs())
            self.assertEqual(sorted(str(p.relative_to(d)) for p in Path(d).rglob("*")), before)

    def test_the_default_list_is_what_it_was(self):
        runs = mapping.list_runs(settings_mod.load({}))
        self.assertEqual(runs[0]["id"], "interface/fixtures")
        self.assertEqual((runs[0]["began"], runs[0]["run_state"], runs[0]["made_here"]), ("2026-09-27 04:33", "complete", False))


if __name__ == "__main__":
    unittest.main()
