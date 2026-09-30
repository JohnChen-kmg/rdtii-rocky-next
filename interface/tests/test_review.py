"""Review decisions and the export: append-only, guarded corrections, 14 columns, no column O, no gloss."""
import csv
import tempfile
import unittest
import zipfile
from pathlib import Path
import re

from . import INTERFACE  # noqa: F401
from rdtii_ui import readers, review, settings as settings_mod
from rdtii_ui.pages import mapping
from rdtii_ui.server import ApiError


class Decisions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.s = settings_mod.load({"RDTII_RUNS_ROOT": str(Path(self.tmp.name) / "outputs")})
        self.run = mapping.list_runs(self.s)[0]
        self.rows, _ = mapping.build_rows(self.run, self.s)
        order = readers.parse_indicator_order(self.s.instrument_dir / "indicator_order.yaml")
        self.in_scope = {it["id"] for it in order["indicators"] if it["status"] == "in_scope"}

    def tearDown(self):
        self.tmp.cleanup()

    def _row(self, econ, glossed=True):
        for r in self.rows:
            if r["_econ"] == econ and (r["_gloss"] if glossed else True) and r["_kind"] == "scored":
                return mapping.row_detail(self.run, r["_i"], self.s)
        raise AssertionError("no such row")

    def test_reject_needs_a_reason_and_latest_wins(self):
        row = self._row("CN")
        with self.assertRaises(ApiError):
            review.record_decision(self.s, self.run, row, {"verdict": "reject"}, self.in_scope)
        review.record_decision(self.s, self.run, row, {"verdict": "reject", "reason": "wrong indicator", "reviewer": "Judge 3"}, self.in_scope)
        review.record_decision(self.s, self.run, row, {"verdict": "accept", "reviewer": "Judge 3"}, self.in_scope)
        latest, lines = review.load_decisions(self.s, self.run["id"])
        self.assertEqual(len(lines), 2)
        self.assertEqual(latest[review.row_key(row)]["verdict"], "accept")
        self.assertEqual(lines[0]["reviewer"], "Judge 3")
        self.assertEqual(set(lines[0]["prior"]), set(readers.HOST_COLUMNS))

    def test_snippet_correction_is_guarded(self):
        row = self._row("CN")
        gloss = row["_gloss"]["english"]
        with self.assertRaises(ApiError):  # the translation can never become the snippet
            review.record_decision(self.s, self.run, row, {"verdict": "correct", "corrections": {"Verbatim Snippet": gloss}}, self.in_scope)
        with self.assertRaises(ApiError):  # nor text that is not in the source
            review.record_decision(self.s, self.run, row, {"verdict": "correct", "corrections": {"Verbatim Snippet": "made up words"}}, self.in_scope)
        shorter = row["Verbatim Snippet"][:8]
        d = review.record_decision(self.s, self.run, row, {"verdict": "correct", "corrections": {"Verbatim Snippet": shorter, "Indicator ID": "6.2"}}, self.in_scope)
        self.assertEqual(d["corrections"], {"Verbatim Snippet": shorter, "Indicator ID": "6.2"})
        with self.assertRaises(ApiError):
            review.record_decision(self.s, self.run, row, {"verdict": "correct", "corrections": {"Indicator ID": "6.5"}}, self.in_scope)
        with self.assertRaises(ApiError):
            review.record_decision(self.s, self.run, row, {"verdict": "correct", "corrections": {"Economy": "X"}}, self.in_scope)

    def test_frozen_submission_is_refused(self):
        frozen = next((r for r in mapping.list_runs(self.s) if r["kind"] == "frozen"), None)
        if not frozen:
            self.skipTest("no filed submission in this checkout")
        rows, _ = mapping.build_rows(frozen, self.s)
        row = mapping.row_detail(frozen, rows[0]["_i"], self.s)
        with self.assertRaises(ApiError) as cm:
            review.record_decision(self.s, frozen, row, {"verdict": "accept"}, self.in_scope)
        self.assertEqual(cm.exception.status, 403)


class Export(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.s = settings_mod.load({"RDTII_RUNS_ROOT": str(Path(self.tmp.name) / "outputs")})
        self.run = mapping.list_runs(self.s)[0]
        self.rows, _ = mapping.build_rows(self.run, self.s)
        order = readers.parse_indicator_order(self.s.instrument_dir / "indicator_order.yaml")
        self.in_scope = {it["id"] for it in order["indicators"] if it["status"] == "in_scope"}

    def tearDown(self):
        self.tmp.cleanup()

    def test_csv_and_xlsx_apply_decisions_and_keep_14_columns(self):
        cn = [r for r in self.rows if r["_econ"] == "CN"]
        reject = mapping.row_detail(self.run, cn[0]["_i"], self.s)
        fix = mapping.row_detail(self.run, cn[1]["_i"], self.s)
        review.record_decision(self.s, self.run, reject, {"verdict": "reject", "reason": "out of scope"}, self.in_scope)
        review.record_decision(self.s, self.run, fix, {"verdict": "correct", "corrections": {"Notes": "checked by hand"}}, self.in_scope)
        res = review.export(self.s, self.run, self.rows, "CN", "csv")
        self.assertEqual((res["rows"], res["rejected"], res["corrected"]), (len(cn) - 1, 1, 1))
        with open(res["path"], encoding="utf-8-sig", newline="") as f:
            data = list(csv.reader(f))
        self.assertEqual(tuple(data[0]), readers.HOST_COLUMNS)
        self.assertTrue(all(len(r) == 14 for r in data))
        self.assertNotIn(reject["Verbatim Snippet"], [r[8] for r in data[1:]])
        self.assertIn("checked by hand", [r[12] for r in data[1:]])
        self.assertTrue(Path(res["review_log"]).is_file())
        with open(res["review_log"], encoding="utf-8-sig", newline="") as f:
            log = list(csv.reader(f))
        self.assertEqual(len(log), 3)  # header + two decisions, the rejection kept
        res2 = review.export(self.s, self.run, self.rows, "CN", "xlsx")
        with zipfile.ZipFile(res2["path"]) as z:
            sheet = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
            self.assertIn("[Content_Types].xml", z.namelist())
        self.assertNotIn('r="O', sheet)
        self.assertEqual(sheet.count("<row "), len(cn))  # header + rows minus the rejected one
        self.assertIn('t="inlineStr"', sheet)
        self.assertNotIn(reject["_gloss"]["english"][:30], sheet)

    def test_decimal_ids_survive_the_xlsx_as_text(self):
        rows = [{c: "" for c in readers.HOST_COLUMNS} | {"Indicator ID": "6.10", "Economy": "X"},
                {c: "" for c in readers.HOST_COLUMNS} | {"Indicator ID": "4.01", "Economy": "X"}]
        path = Path(self.tmp.name) / "t.xlsx"
        review.write_xlsx(rows, path)
        with zipfile.ZipFile(path) as z:
            sheet = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
        cells = re.findall(r'<c r="E(\d)" t="inlineStr"><is><t xml:space="preserve">([^<]*)</t>', sheet)
        self.assertEqual(cells, [("1", "Indicator ID"), ("2", "6.10"), ("3", "4.01")])


if __name__ == "__main__":
    unittest.main()
