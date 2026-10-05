"""Scraping's Output says when a run began and how it stands.

What must hold: both are read, never written; a folder no run made says nothing; and a run counts as
complete only on the crawler's own word."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from . import INTERFACE  # noqa: F401
from rdtii_ui import settings as settings_mod
from rdtii_ui.pages import scrape


class _Jobs:
    """The two things the reader asks of the job layer: its runs, newest first."""

    def __init__(self, *jobs):
        self._jobs = list(jobs)

    def all(self):
        return self._jobs


def _job(folder, status, stage="p1"):
    return SimpleNamespace(out_dir=folder, status=status, stage=stage)


class Began(unittest.TestCase):
    def test_the_time_is_the_stamp_the_folders_name_ends_with(self):
        self.assertEqual(scrape.run_began("20261004-012901"), "2026-10-04 01:29")
        self.assertEqual(scrape.run_began("links_20261004-012226"), "2026-10-04 01:22")
        self.assertEqual(scrape.run_began("SG-MY_20260930-101010"), "2026-09-30 10:10")

    def test_a_name_without_a_stamp_or_with_no_real_time_gives_nothing(self):
        for name in ("mini_raw", "", "2026-09-21", "20269999-999999", "x20261004-012901"):
            self.assertEqual(scrape.run_began(name), "", name)


class State(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name) / "20261004-012901"
        self.folder.mkdir()

    def test_a_crawl_is_complete_only_on_the_crawlers_word(self):
        self.assertEqual(scrape.run_state(self.folder, "interface run", {"state": "done"}), "complete")
        for state in ("crawling", "starting", None, "anything else"):
            self.assertEqual(scrape.run_state(self.folder, "interface run", {"state": state}), "not complete", state)
        self.assertEqual(scrape.run_state(self.folder, "interface run", None), "not complete")       # the run made its folder and nothing else
        self.assertEqual(scrape.run_state(self.folder, "interface run", {"state": "throttle_suspected"}), "paused")

    def test_a_crawl_folder_with_no_status_file_has_no_record(self):
        (self.folder / "manifest.csv").write_text("doc_id", encoding="utf-8")
        self.assertEqual(scrape.run_state(self.folder, "interface run", None), "")                    # an older folder, or a copy
        self.assertEqual(scrape.run_state(self.folder, "interface run", {"state": "crawling"}), "not complete")
        self.assertEqual(scrape.run_state(self.folder, "interface run", None, _Jobs(_job(self.folder, "cancelled"))), "stopped")

    def test_this_sessions_runs_say_running_and_stopped(self):
        crawling = {"state": "crawling"}
        self.assertEqual(scrape.run_state(self.folder, "interface run", crawling, _Jobs(_job(self.folder, "running"))), "running")
        self.assertEqual(scrape.run_state(self.folder, "interface run", {"state": "done"}, _Jobs(_job(self.folder, "queued"))), "running")   # a second pass waits
        self.assertEqual(scrape.run_state(self.folder, "interface run", crawling, _Jobs(_job(self.folder, "cancelled"))), "stopped")
        self.assertEqual(scrape.run_state(self.folder, "interface run", crawling, _Jobs(_job(self.folder, "failed"))), "not complete")
        other = _Jobs(_job(self.folder.parent / "another", "running"))
        self.assertEqual(scrape.run_state(self.folder, "interface run", crawling, other), "not complete")                                    # another folder's run

    def test_a_link_list_is_complete_when_its_listing_was_written(self):
        self.assertEqual(scrape.run_state(self.folder, "link list", None), "not complete")
        self.assertEqual(scrape.run_state(self.folder, "link list", None, _Jobs(_job(self.folder.parent / "crawl", "running"))), "running")
        (self.folder / "catalogue_meta.json").write_text("{}", encoding="utf-8")
        self.assertEqual(scrape.run_state(self.folder, "link list", None), "complete")

    def test_a_folder_no_run_made_says_nothing(self):
        for kind in ("hand-collected", "hand-collected manifest", "shipped manifest", "HANDOFF1_DIR", ""):
            self.assertEqual(scrape.run_state(self.folder, kind, {"state": "done"}), "", kind)
        self.assertEqual(scrape.run_state(self.folder, "China tools run", None), "")                 # its tools leave no record
        self.assertEqual(scrape.run_state(self.folder, "China tools run", None, _Jobs(_job(self.folder, "running", "cn"))), "running")

    def test_reading_writes_nothing(self):
        (self.folder / "crawl_status.json").write_text(json.dumps({"state": "crawling"}), encoding="utf-8")
        before = sorted(p.name for p in self.folder.iterdir())
        scrape.run_state(self.folder, "interface run", {"state": "crawling"}, _Jobs(_job(self.folder, "cancelled")))
        self.assertEqual(sorted(p.name for p in self.folder.iterdir()), before)


class LastRun(unittest.TestCase):
    def test_the_crawlers_own_start_is_shown_in_this_machines_time(self):
        from datetime import datetime, timezone
        expected = datetime(2026, 10, 4, 6, 40, 16, tzinfo=timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
        self.assertEqual(scrape.local_time("2026-10-04T06:40:16Z"), expected)
        for bad in (None, "", "yesterday", 12, "2026-13-40T99:00:00Z"):
            self.assertEqual(scrape.local_time(bad), "", bad)

    def test_it_is_read_from_the_status_file_the_crawler_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "20261004-012901"
            folder.mkdir()
            (folder / "crawl_status.json").write_text(json.dumps({"state": "done", "started_at": "2026-10-04T06:40:16Z"}), encoding="utf-8")
            info = scrape.describe_crawl_folder(folder)
            self.assertEqual(info["crawl_state"]["started_at"], "2026-10-04T06:40:16Z")
            self.assertEqual(sorted(p.name for p in folder.iterdir()), ["crawl_status.json"])       # reading wrote nothing


class Listed(unittest.TestCase):
    def test_every_row_of_output_carries_both(self):
        folders = scrape.list_crawl_folders(settings_mod.load({}))
        self.assertTrue(folders)
        for f in folders:
            self.assertIn("began", f, f["id"])
            self.assertIn(f["run_state"], ("", "running", "complete", "paused", "stopped", "not complete"), f["id"])
        default = next(f for f in folders if f["kind"] == "HANDOFF1_DIR")
        self.assertEqual((default["began"], default["run_state"], default["last_run"]), ("", "", ""))       # the demo corpus is no run
        self.assertTrue(all("last_run" in f for f in folders))


if __name__ == "__main__":
    unittest.main()
