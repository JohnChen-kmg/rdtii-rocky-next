"""The default set-up, pinned.

With no setting at all, every location, every source label and every id the pages show must stay exactly
what the judged release shipped. The working-folder work is built on top of this; if one of these
assertions has to change, the default behaviour has changed and that needs its own decision.
"""
import unittest

from . import INTERFACE  # noqa: F401
from rdtii_ui import settings as settings_mod
from rdtii_ui.pages import extract, inbox, mapping, scrape

REPO = settings_mod.REPO


class Locations(unittest.TestCase):
    def setUp(self):
        self.s = settings_mod.load({})

    def test_every_location_is_where_the_release_put_it(self):
        want = {"handoff1_dir": "demo_data/mini_raw", "handoff2_dir": "outputs/extract/demo",
                "out_dir": "interface/fixtures", "index_dir": "outputs/index/demo",
                "instrument_dir": "stages/p0-instrument/output", "runs_root": "outputs",
                "submission_dir": "submission", "inbox_dir": "inbox"}
        for name, rel in want.items():
            self.assertEqual(getattr(self.s, name), (REPO / rel).resolve(), name)
        self.assertEqual(self.s.out_dir_extra, ())
        self.assertEqual((self.s.baseline_path, self.s.baseline_r2_path), ("", ""))
        self.assertEqual((self.s.python_p1, self.s.python_p2, self.s.python_p3), ("", "", ""))
        self.assertEqual((self.s.host, self.s.port), ("127.0.0.1", 8765))

    def test_the_settings_panel_lists_the_same_eleven_rows_all_default(self):
        rows = settings_mod.describe(self.s)
        self.assertEqual([r["name"] for r in rows],
                         ["HANDOFF1_DIR", "HANDOFF2_DIR", "OUT_DIR", "RDTII_OUT_DIR_EXTRA", "INDEX_DIR", "INSTRUMENT_DIR",
                          "BASELINE_PATH", "BASELINE_R2_PATH", "RDTII_RUNS_ROOT", "RDTII_SUBMISSION_DIR", "RDTII_INBOX_DIR"])
        self.assertEqual({r["source"] for r in rows}, {"default"})

    def test_the_stages_are_found_inside_the_repository(self):
        self.assertEqual(self.s.stage_dirs, {"p1": REPO / "stages" / "p1-scrape", "p2": REPO / "stages" / "p2-extract",
                                             "p3": REPO / "stages" / "p3-map"})


class Ids(unittest.TestCase):
    """The ids the page uses for runs, inputs and inbox folders: repository-relative, forward slashes."""

    def setUp(self):
        self.s = settings_mod.load({})

    def test_mapping_runs(self):
        runs = mapping.list_runs(self.s)
        ids = [r["id"] for r in runs]
        self.assertEqual((runs[0]["id"], runs[0]["kind"]), ("interface/fixtures", "fixture"))
        self.assertIn("submission", ids)
        for i in ids:
            self.assertTrue(i in ("interface/fixtures", "submission") or i.startswith("outputs/map/"), i)

    def test_extraction_inputs(self):
        ids = [d["id"] for d in extract.list_inputs(self.s)]
        self.assertEqual(ids[0], "demo_data/mini_raw")
        shipped = [i for i in ids if i.startswith("stages/")]
        self.assertTrue(shipped and all(i.startswith("stages/p1-scrape/handoff1/") for i in shipped))

    def test_crawl_folders(self):
        folders = scrape.list_crawl_folders(self.s)
        # crawls made on this machine are listed first, so the default hand-off is found by its kind
        default = next(f for f in folders if f["kind"] == "HANDOFF1_DIR")
        self.assertEqual(default["id"], "demo_data/mini_raw")
        before = folders[:folders.index(default)]
        self.assertTrue(all(f["id"].startswith("outputs/scrape/") for f in before), [f["id"] for f in before])

    def test_inbox_folders(self):
        extract.ensure_inbox(self.s)
        ids = [e["id"] for e in inbox.describe(self.s)["economies"]][:6]
        self.assertEqual(ids, ["inbox/SG", "inbox/AU", "inbox/MY", "inbox/TL", "inbox/LA", "inbox/CN"])

    def test_no_id_carries_a_backslash_or_a_drive(self):
        ids = ([r["id"] for r in mapping.list_runs(self.s)] + [d["id"] for d in extract.list_inputs(self.s)]
               + [d["id"] for d in scrape.list_crawl_folders(self.s)]
               + [e["id"] for e in inbox.describe(self.s)["economies"]])
        for i in ids:
            self.assertNotIn("\\", i)
            self.assertNotRegex(i, r"^[A-Za-z]:")


if __name__ == "__main__":
    unittest.main()
