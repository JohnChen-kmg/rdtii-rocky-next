"""The Extraction Start plan: the interface-written manifest, hash-based staging, and the step list."""
import csv
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from . import INTERFACE  # noqa: F401
from rdtii_ui import envbuild, jobs, settings as settings_mod
from rdtii_ui.pages import extract
from rdtii_ui.server import App

REPO = settings_mod.REPO


class HandCollectedManifest(unittest.TestCase):
    def test_rows_fill_every_required_column(self):
        rows = extract.build_manifest_rows(REPO / "demo_data", "MY")
        self.assertGreaterEqual(len(rows), 1)
        required = ("contract_version", "doc_id", "economy", "source_type", "local_path",
                    "law_name_guess", "retrieval_method", "content_type", "content_sha256", "byte_size")
        for r in rows:
            for col in required:
                self.assertNotEqual(r[col], "", f"{col} blank in {r['doc_id']}")
            if r["source_type"].startswith("pdf"):
                self.assertIn(r["pdf_is_scanned"], ("true", "false"))
            else:
                self.assertEqual(r["pdf_is_scanned"], "")
            self.assertTrue(extract.valid_doc_id(r["doc_id"]), r["doc_id"])
            self.assertEqual(r["retrieval_method"], "hand_collected")
            self.assertEqual(r["economy"], "MY")
            self.assertEqual(len(r["content_sha256"]), 64)
        scan = next(r for r in rows if r["local_path"] == "my-cma1998-001.pdf")
        self.assertEqual(scan["source_type"], "pdf_scanned")
        self.assertEqual(scan["content_sha256"], "3f01e2a123551e6c28bf446b7c35403b3e2e43c44f9c145585e0c74dd1455c2a")
        self.assertEqual(scan["page_count"], "144")

    def test_duplicate_stems_get_distinct_ids(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a").mkdir()
            (Path(d) / "b").mkdir()
            (Path(d) / "a" / "Law.pdf").write_bytes(b"%PDF-1.4 /Type /Page /Font\n")
            (Path(d) / "b" / "law.pdf").write_bytes(b"%PDF-1.4 /Type /Page\n")
            rows = extract.build_manifest_rows(Path(d), "SG")
            self.assertEqual([r["doc_id"] for r in rows], ["sg-law-001", "sg-law-002"])
            self.assertEqual([r["source_type"] for r in rows], ["pdf_native", "pdf_scanned"])

    def test_written_manifest_has_the_crawler_columns(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "outputs"
            s = settings_mod.load({"RDTII_RUNS_ROOT": str(root)})
            rows = extract.build_manifest_rows(REPO / "demo_data", "MY")
            path = extract.write_manifest(s, REPO / "demo_data", rows)
            with open(path, encoding="utf-8-sig", newline="") as f:
                header = next(csv.reader(f))
            self.assertEqual(header, extract.manifest_columns())
            self.assertTrue(str(path).startswith(str(root)))


class Staging(unittest.TestCase):
    def test_demo_folder_is_recoverable_by_hash_and_staged(self):
        demo = REPO / "demo_data" / "mini_raw"
        self.assertEqual(len(extract.missing_rows(demo)), 1)
        self.assertEqual(extract.recoverable_count(demo), 1)
        with tempfile.TemporaryDirectory() as d:
            s = settings_mod.load({"RDTII_RUNS_ROOT": str(Path(d) / "outputs")})
            staged = extract.stage_input(s, demo)
            self.assertEqual(staged.name, "mini_raw")
            self.assertEqual(extract.missing_rows(staged), [])
            self.assertTrue((staged / "manifest.csv").is_file())

    def test_shipped_manifest_without_bytes_is_refused(self):
        shipped = next((REPO / "stages" / "p1-scrape" / "handoff1" / "SG").glob("SG_corpus_*"))
        with tempfile.TemporaryDirectory() as d:
            s = settings_mod.load({"RDTII_RUNS_ROOT": str(Path(d) / "outputs")})
            with self.assertRaises(Exception) as cm:
                extract.stage_input(s, shipped)
            self.assertIn("Run the crawler", str(cm.exception))


FOUND = {"ok": True, "path": "/usr/bin/tesseract"}
MISSING = {"ok": False, "path": None, "hint": "install it"}


class Precheck(unittest.TestCase):
    """What the Check says about a folder. Whether this machine has Tesseract is not what is being tested, so
    the probe is given its answer."""

    @mock.patch("rdtii_ui.probes.probe_tesseract", return_value=FOUND)
    def test_demo_folder_passes_with_the_two_expected_warnings(self, _probe):
        with tempfile.TemporaryDirectory() as d:
            s = settings_mod.load({"RDTII_RUNS_ROOT": str(Path(d) / "outputs")})
            app = App(s)
            checks = extract.precheck(app, {"input": "demo_data/mini_raw"})
            levels = {c["check"]: c["level"] for c in checks}
            self.assertEqual(levels["stage"], "ok")
            self.assertEqual(levels["documents"], "warn")  # one committed copy restored by hash
            self.assertEqual(levels["language"], "ok")
            self.assertEqual(levels["output"], "ok")  # a fresh runs root: nothing to reuse
            self.assertNotIn("fail", levels.values())

    @mock.patch("rdtii_ui.probes.probe_tesseract", return_value=MISSING)
    def test_scanned_documents_without_tesseract_fail_the_check(self, _probe):
        with tempfile.TemporaryDirectory() as d:
            app = App(settings_mod.load({"RDTII_RUNS_ROOT": str(Path(d) / "outputs")}))
            ocr = next(c for c in extract.precheck(app, {"input": "demo_data/mini_raw"}) if c["check"] == "ocr")
            self.assertEqual(ocr["level"], "fail")
            self.assertIn("Tesseract was not found", ocr["text"])
            self.assertIn("RDTII_TESSERACT", ocr["text"])

    @mock.patch("rdtii_ui.probes.probe_tesseract", return_value=FOUND)
    def test_hand_collected_folder_needs_an_economy(self, _probe):
        with tempfile.TemporaryDirectory() as d:
            s = settings_mod.load({"RDTII_RUNS_ROOT": str(Path(d) / "outputs")})
            app = App(s)
            checks = extract.precheck(app, {"input": "demo_data"})
            fails = [c for c in checks if c["level"] == "fail"]
            self.assertEqual([c["check"] for c in fails], ["economy"])
            checks = extract.precheck(app, {"input": "demo_data", "economy": "MY"})
            self.assertFalse([c for c in checks if c["level"] == "fail"])
            self.assertIn("Malaysia", next(c["text"] for c in checks if c["check"] == "economy"))


class Languages(unittest.TestCase):
    def test_demo_has_no_recorded_language_and_reads_english(self):
        d = extract.describe_input(REPO / "demo_data" / "mini_raw", "t")
        self.assertEqual(d["languages"]["recorded"], {})
        self.assertEqual(d["languages"]["blank"], 5)
        self.assertEqual(dict(d["language_plan"]), {"AU": "eng", "MY": "eng", "SG": "eng"})
        self.assertFalse(d["languages"]["passes"])
        self.assertIn("none recorded", d["language_line"])

    def test_shipped_lao_corpus_records_lao_per_document(self):
        p = REPO / "stages" / "p1-scrape" / "handoff1" / "LA" / "LA_corpus_2026-09-21"
        if not p.is_dir():
            self.skipTest("corpus not shipped")
        d = extract.describe_input(p, "t")
        self.assertEqual(list(d["languages"]["recorded"]), ["lao"])
        self.assertEqual(d["languages"]["blank"], 0)

    def test_two_languages_mean_one_pass_per_economy(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            raw = root / "crawl"
            (raw / "raw").mkdir(parents=True)
            docs = [("la-a-001", "LA", "la_a.pdf"), ("tl-b-001", "TL", "tl_b.pdf"), ("tl-c-001", "TL", "tl_c.pdf")]
            with open(raw / "manifest.csv", "w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f)
                w.writerow(["doc_id", "economy", "source_type", "local_path", "content_sha256", "byte_size"])
                for doc, econ, name in docs:
                    (raw / "raw" / name).write_bytes(b"%PDF-1.4 stub")
                    w.writerow([doc, econ, "pdf_native", f"raw/{name}", "", "13"])
            s = settings_mod.load({"RDTII_RUNS_ROOT": str(root / "outputs")})
            app = App(s)
            app.jobs = jobs.JobManager()
            job = extract.plan_extract(app, {"input": str(raw)})
            runs = [st.argv for st in job.steps if "run" in st.argv]
            self.assertEqual(len(runs), 2)
            sel = {(a[a.index("--economy") + 1], a[a.index("--default-language") + 1]) for a in runs}
            self.assertEqual(sel, {("LA", "lao"), ("TL", "por")})
            labels = [st.label for st in job.steps]
            self.assertTrue(any("2 document(s) for TL in Portuguese" in x for x in labels), labels)
            self.assertIn("Lao, Portuguese", job.title)

    def test_hand_collected_law_table_carries_the_economy_language(self):
        with tempfile.TemporaryDirectory() as d:
            s = settings_mod.load({"RDTII_RUNS_ROOT": str(Path(d) / "outputs")})
            rows = extract.build_manifest_rows(REPO / "demo_data", "CN")
            m = extract.write_manifest(s, REPO / "demo_data", rows)
            with open(m.parent / "law_table.csv", encoding="utf-8-sig", newline="") as f:
                lt = list(csv.DictReader(f))
            self.assertEqual(len(lt), len(rows))
            self.assertEqual({r["language"] for r in lt}, {"zho"})


class Plan(unittest.TestCase):
    def test_demo_plan_has_import_check_ocr_and_run(self):
        with tempfile.TemporaryDirectory() as d:
            s = settings_mod.load({"RDTII_RUNS_ROOT": str(Path(d) / "outputs")})
            app = App(s)
            app.jobs = jobs.JobManager()
            job = extract.plan_extract(app, {"input": "demo_data/mini_raw"})
            labels = [st.label for st in job.steps]
            self.assertEqual(len(labels), 3)
            self.assertIn("imports", labels[0])
            self.assertIn("OCR", labels[1])
            run = job.steps[2]
            self.assertEqual(run.argv[1:4], ["-m", "rdtii_p2.cli", "run"])
            self.assertIn("--skip-tags", run.argv)
            self.assertEqual(run.env["PYTHONPATH"], "src;." if __import__("os").name == "nt" else "src:.")
            self.assertEqual(run.env["ANTHROPIC_API_KEY"], "")
            self.assertTrue(run.env["OUT_DIR"].endswith("demo"))
            self.assertTrue(job.sentences and "Staged" in job.sentences[0]["text"])

    def test_parser_turns_stage_lines_into_sentences(self):
        job = jobs.Job(stage="p2", title="t", steps=[])
        out = extract.parse_p2("[P2] Manifest OK: 5 rows, contract 0.3.0", job)
        self.assertEqual(out[0], "Manifest accepted: 5 documents.")
        job.bump(**out[1])
        out = extract.parse_p2("[P2] sg-pdpa2012-001: lane B (pdf_native)", job)
        self.assertEqual(out[0], "Reading 1 of 5: sg-pdpa2012-001 (native PDF).")
        job.bump(**out[1])
        self.assertEqual(job.progress["done"], 1)
        out = extract.parse_p2("ModuleNotFoundError: No module named 'pytesseract'", job)
        self.assertIn("pytesseract", out[0])
        self.assertIsNone(extract.parse_p2("some unknown line", job))



class DocumentsToCheck(unittest.TestCase):
    """A document that gave no provision is counted on its output, listed with what happened, and said at the end."""

    def _output(self, d: str) -> Path:
        import json
        out = Path(d) / "out"
        (out / "source_text").mkdir(parents=True)
        status = [{"doc_id": "tl-dl12003-001", "status": "ok", "n_provisions": 12, "lane": "B"},
                  {"doc_id": "tl-dp12023-001", "status": "zero_provisions", "n_provisions": 0, "lane": "B",
                   "reason": "parsed cleanly; no citable provision grounded"},
                  {"doc_id": "tl-dl22003-001", "status": "parse_failed", "n_provisions": 0, "lane": "D", "reason": "legacy .doc"}]
        laws = [{"doc_id": "tl-dp12023-001", "law_name": "Decreto do Presidente 1/2023", "law_name_en": "Presidential Decree 1/2023",
                 "source_url": "https://www.mj.gov.tl/jornal/x.pdf"}]
        (out / "doc_status.jsonl").write_text("".join(json.dumps(r) + "\n" for r in status), encoding="utf-8")
        (out / "laws.jsonl").write_text("".join(json.dumps(r) + "\n" for r in laws), encoding="utf-8")
        (out / "source_text" / "tl-dp12023-001.txt").write_text("um texto", encoding="utf-8")
        return out

    def test_the_output_counts_them_and_the_list_says_what_happened(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            out = self._output(d)
            self.assertEqual(extract.describe_output(out, "test")["to_check"], 2)
            got = extract.unread_documents(out)
            self.assertEqual((got["total"], len(got["documents"]), got["counts"]), (3, 2, {"parse_failed": 1, "zero_provisions": 1}))
            one = next(x for x in got["documents"] if x["status"] == "zero_provisions")
            self.assertEqual(one["title"], "Presidential Decree 1/2023")
            self.assertEqual(one["title_original"], "Decreto do Presidente 1/2023")
            self.assertIn("one piece of text", one["what"])
            self.assertEqual(one["text_file"], "source_text/tl-dp12023-001.txt")
            self.assertTrue(one["source_url"].startswith("https://"))
            failed = next(x for x in got["documents"] if x["status"] == "parse_failed")
            self.assertEqual((failed["what"], failed["reason"], failed["text_file"]), ("Could not be read.", "legacy .doc", ""))

    def test_the_run_says_so_at_the_end(self):
        import tempfile
        from rdtii_ui import jobs
        with tempfile.TemporaryDirectory() as d:
            out = self._output(d)
            job = jobs.Job(stage="p2", title="t", steps=[])
            extract._say_unread(out)(job, 0)
            said = job.sentences[-1]["text"]
            self.assertIn("2 of 3 document(s) gave no provisions", said)
            self.assertIn("1 could not be read", said)
            self.assertIn("1 with no article found", said)
            self.assertIn("to check", said)


if __name__ == "__main__":
    unittest.main()
