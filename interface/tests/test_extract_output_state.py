"""Extraction's Output says when a folder was first and last run and how it stands.

What must hold: all three are read, never written; "complete" needs the stage's own report, which it
writes only when a run ends; and a folder no run of the interface made says nothing when nothing says."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from . import INTERFACE  # noqa: F401
from rdtii_ui import settings as settings_mod
from rdtii_ui.pages import extract, scrape


class _Jobs:
    def __init__(self, *jobs):
        self._jobs = list(jobs)

    def all(self):
        return self._jobs


def _job(folder, status):
    return SimpleNamespace(out_dir=folder, status=status, stage="p2")


def _log(folder: Path, *stamps: str) -> None:
    with open(folder / "extract_log.jsonl", "a", encoding="utf-8") as f:
        for i, ts in enumerate(stamps):
            f.write(json.dumps({"ts": ts, "doc_id": f"sg-doc-{i:03d}", "stage": "route"}) + "\n")


def _report(folder: Path, when: str) -> None:
    (folder / "cost_report.json").write_text(json.dumps({"generated_at": when, "docs_processed": 2}), encoding="utf-8")


class Folder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "SG_run"
        self.out.mkdir()

    def test_the_first_and_the_latest_log_line_give_began_and_last_run(self):
        _log(self.out, "2026-10-04T11:30:57Z", "2026-10-04T11:31:05Z")
        _report(self.out, "2026-10-04T11:31:06Z")
        _log(self.out, "2026-10-05T02:10:00Z", "2026-10-05T02:10:04Z")           # a second run into the same folder
        _report(self.out, "2026-10-05T02:10:05Z")
        self.assertEqual(extract.log_span(self.out / "extract_log.jsonl"), ("2026-10-04T11:30:57Z", "2026-10-05T02:10:04Z"))
        d = extract.describe_output(self.out, "interface run")
        self.assertEqual((d["began"], d["last_run"]), (scrape.local_time("2026-10-04T11:30:57Z"), scrape.local_time("2026-10-05T02:10:04Z")))
        self.assertEqual(d["run_state"], "complete")

    def test_complete_needs_the_stages_report(self):
        self.assertEqual(extract.describe_output(self.out, "interface run")["run_state"], "not complete")   # a folder and nothing in it
        _log(self.out, "2026-10-04T11:30:57Z")
        self.assertEqual(extract.describe_output(self.out, "interface run")["run_state"], "not complete")   # logged, never reported
        _report(self.out, "2026-10-04T11:31:06Z")
        self.assertEqual(extract.describe_output(self.out, "interface run")["run_state"], "complete")
        _log(self.out, "2026-10-05T02:10:00Z")                                # a later run that stopped part of the way
        d = extract.describe_output(self.out, "interface run")
        self.assertEqual(d["run_state"], "complete")                          # the earlier run's whole output is still what the folder holds
        self.assertEqual(d["last_run"], scrape.local_time("2026-10-05T02:10:00Z"))

    def test_this_sessions_runs_say_running_and_stopped(self):
        _log(self.out, "2026-10-04T11:30:57Z")
        _report(self.out, "2026-10-04T11:31:06Z")
        self.assertEqual(extract.describe_output(self.out, "interface run", _Jobs(_job(self.out, "running")))["run_state"], "running")
        self.assertEqual(extract.describe_output(self.out, "interface run", _Jobs(_job(self.out, "cancelled")))["run_state"], "stopped")
        self.assertEqual(extract.describe_output(self.out, "interface run", _Jobs(_job(self.out, "done")))["run_state"], "complete")
        other = _Jobs(_job(self.out.parent / "another", "running"))
        self.assertEqual(extract.describe_output(self.out, "interface run", other)["run_state"], "complete")

    def test_a_folder_no_run_made_says_nothing_when_nothing_says(self):
        d = extract.describe_output(self.out, "HANDOFF2_DIR")
        self.assertEqual((d["began"], d["last_run"], d["run_state"]), ("", "", ""))
        (self.out / "cost_report.json").write_text(json.dumps({"run": "an older report with no time in it"}), encoding="utf-8")
        self.assertEqual(extract.describe_output(self.out, "HANDOFF2_DIR")["run_state"], "complete")           # its report is there

    def test_a_damaged_log_is_read_as_far_as_it_goes_and_nothing_is_written(self):
        (self.out / "extract_log.jsonl").write_text('{"ts": "2026-10-04T11:30:57Z"}\nnot json\n\n{"doc_id": "x"}\n{"ts": "2026-10-04T11:31:05Z"}\n', encoding="utf-8")
        self.assertEqual(extract.log_span(self.out / "extract_log.jsonl"), ("2026-10-04T11:30:57Z", "2026-10-04T11:31:05Z"))
        self.assertEqual(extract.log_span(self.out / "no_such_file.jsonl"), ("", ""))
        before = sorted(p.name for p in self.out.iterdir())
        extract.describe_output(self.out, "interface run", _Jobs(_job(self.out, "cancelled")))
        self.assertEqual(sorted(p.name for p in self.out.iterdir()), before)


class Listed(unittest.TestCase):
    def test_every_row_of_output_carries_the_three(self):
        folders = extract.list_outputs(settings_mod.load({}))
        for f in folders:
            self.assertIn("began", f, f["id"])
            self.assertIn("last_run", f, f["id"])
            self.assertIn(f["run_state"], ("", "running", "complete", "stopped", "not complete"), f["id"])


if __name__ == "__main__":
    unittest.main()
