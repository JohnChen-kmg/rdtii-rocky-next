"""The China subpage reads the crawler stage's own China material."""
import unittest

from . import INTERFACE  # noqa: F401
from rdtii_ui import settings as settings_mod
from rdtii_ui.pages import china


class China(unittest.TestCase):
    def setUp(self):
        self.s = settings_mod.load({})
        self.d = china.describe(self.s)

    def test_watchlist_is_grouped_and_complete(self):
        self.assertTrue(self.d["present"])
        self.assertEqual(self.d["watchlist_total"], 33)
        self.assertEqual(sum(len(g["rows"]) for g in self.d["watchlist"]), 33)
        kinds = [g["kind"] for g in self.d["watchlist"]]
        self.assertEqual(kinds[0], "layer-1")
        self.assertIn("manual-host", kinds)

    def test_shipped_folders_carry_their_counts(self):
        by = {f["name"]: f for f in self.d["folders"]}
        self.assertEqual(by["CN_ws_2026-09-21"]["manifest_rows"], 111)
        self.assertEqual(by["CN_layer2_2026-09-21"]["manifest_rows"], 6)
        self.assertGreaterEqual(by["CN_manual_2026-09-20"]["provenance_rows"], 5)
        corpus = by["CN_sources_2026-09-21"]
        sources = {x["source"]: x for x in corpus["sources"]}
        self.assertIn("npc-database", sources)
        self.assertIn("cac", sources)
        self.assertGreaterEqual(sources["miit"]["provenance_rows"], 30)
        self.assertGreaterEqual(corpus.get("deferred_sources", 0), 10)

    def test_notes_are_listed_for_reading(self):
        paths = {x["path"] for x in self.d["docs"]}
        self.assertIn("stages/p1-scrape/handoff1/CN/CN_corpus_plan.md", paths)
        self.assertIn("stages/p1-scrape/handoff1/CN/CN_sources_2026-09-21/README.md", paths)
        self.assertTrue(all(not p.split("/")[-2].startswith("_deferred") for p in paths))


if __name__ == "__main__":
    unittest.main()
