"""The traps the interface must not fall into, pinned against the fixtures and small synthetic files."""
import csv
import tempfile
import unittest
from pathlib import Path

from . import INTERFACE  # noqa: F401  (puts interface/ on sys.path)
from rdtii_ui import readers, settings as settings_mod
from rdtii_ui.pages import mapping

FIX = INTERFACE / "fixtures"


class CsvTraps(unittest.TestCase):
    def test_fixture_csv_has_the_14_host_columns_in_order(self):
        header, rows = readers.read_csv(FIX / "submission" / "records_CN.csv")
        self.assertEqual(tuple(header), readers.HOST_COLUMNS)
        self.assertEqual(len(rows), 8)

    def test_decimal_indicator_ids_stay_text(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "records_XX.csv"
            with open(p, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f)
                w.writerow(readers.HOST_COLUMNS)
                w.writerow(["X", "Law", "", "", "6.10", "s.1", "NEW", "", "q", "", "http://x", "0.9", "", "English"])
                w.writerow(["X", "Law", "", "", "4.01", "s.2", "", "", "No provision found", "", "http://x", "", "", "English"])
            _, rows = readers.read_csv(p)
            self.assertEqual([r["Indicator ID"] for r in rows], ["6.10", "4.01"])
            self.assertEqual(rows[1]["Discovery Tag"], "")
            self.assertEqual(rows[1]["Confidence"], "")

    def test_blank_discovery_tag_is_preserved_in_fixture(self):
        _, rows = readers.read_csv(FIX / "submission" / "records_LA.csv")
        blanks = [r for r in rows if r["Discovery Tag"] == ""]
        self.assertEqual(len(blanks), 1)
        self.assertEqual(blanks[0]["Article / Section"], "n/a")


class IndicatorOrder(unittest.TestCase):
    def test_parse_yields_61_in_scope_with_string_ids(self):
        order = readers.parse_indicator_order(settings_mod.REPO / "stages/p0-instrument/output/indicator_order.yaml")
        items = order["indicators"]
        self.assertEqual(order["meta"].get("listed"), 62)
        self.assertEqual(len(items), 62)
        in_scope = [i for i in items if i["status"] == "in_scope"]
        self.assertEqual(len(in_scope), 61)
        ids = {i["id"] for i in items}
        self.assertIn("1.4", ids)
        self.assertIn("12.4.4", ids)
        self.assertIn("6.5", ids)
        self.assertTrue(all(isinstance(i["id"], str) for i in items))
        self.assertTrue(all(isinstance(i["pillar"], int) for i in items))
        self.assertEqual(readers.automated_ids(order), ["6.1", "6.2", "6.3", "6.4", "7.1", "7.2", "7.3", "7.4", "7.5"])

    def test_multiline_names_are_joined(self):
        order = readers.parse_indicator_order(settings_mod.REPO / "stages/p0-instrument/output/indicator_order.yaml")
        first = order["indicators"][0]
        self.assertEqual(first["id"], "1.4")
        self.assertIn("United Nations region", first["name"])


class FixtureRun(unittest.TestCase):
    def setUp(self):
        self.s = settings_mod.load({})
        self.runs = mapping.list_runs(self.s)

    def test_fixture_run_is_listed_with_six_economies(self):
        self.assertTrue(self.runs)
        run = self.runs[0]
        self.assertEqual(run["kind"], "fixture")
        self.assertEqual(run["economies"], ["AU", "CN", "LA", "MY", "SG", "TL"])
        self.assertEqual(run["rows"], 52)

    def test_timor_leste_is_read_as_two_files_and_summed(self):
        rows, _ = mapping.build_rows(self.runs[0], self.s)
        tl = [r for r in rows if r["_econ"] == "TL"]
        self.assertEqual(len(tl), 12)
        self.assertEqual(sorted({r["_arm"] for r in tl}), ["", "pillars other"])

    def test_chinese_rows_get_an_english_gloss_beside_the_original(self):
        rows, _ = mapping.build_rows(self.runs[0], self.s)
        cn = [r for r in rows if r["_econ"] == "CN"]
        glossed = [r for r in cn if r["_gloss"]]
        self.assertGreaterEqual(len(glossed), 3)
        for r in glossed:
            self.assertNotEqual(r["Verbatim Snippet"], r["_gloss"]["english"])
            self.assertTrue(r["_gloss"]["model"])

    def test_scores_come_from_rollup_and_inverted_flag_is_set(self):
        rows, _ = mapping.build_rows(self.runs[0], self.s)
        cn71 = next(r for r in rows if r["_econ"] == "CN" and r["Indicator ID"] == "7.1")
        self.assertEqual(cn71["_score"], 0.0)
        self.assertTrue(cn71["_score_inverted"])

    def test_lao_not_literal_rate_is_reported_as_a_corpus_note(self):
        _, notes = mapping.build_rows(self.runs[0], self.s)
        self.assertIn("LA", notes)
        self.assertGreater(notes["LA"]["rate"], 0.5)

    def test_row_detail_carries_section_gloss_for_cn(self):
        rows, _ = mapping.build_rows(self.runs[0], self.s)
        cn = next(r for r in rows if r["_econ"] == "CN" and r["_gloss"])
        d = mapping.row_detail(self.runs[0], cn["_i"], self.s)
        self.assertIsNotNone(d["_section_gloss"])
        self.assertIn("english", d["_section_gloss"])


if __name__ == "__main__":
    unittest.main()
