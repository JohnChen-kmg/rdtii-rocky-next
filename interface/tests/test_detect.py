"""Detection of language and economy for hand-collected files, and the inbox that names economies by folder."""
import tempfile
import unittest
import zipfile
from pathlib import Path

from . import INTERFACE  # noqa: F401
from rdtii_ui import detect, jobs, settings as settings_mod
from rdtii_ui.pages import extract
from rdtii_ui.server import App

ZH = ("第一条 为了保障网络安全，维护网络空间主权和国家安全、社会公共利益，保护公民、法人和其他组织的合法权益，"
      "促进经济社会信息化健康发展，制定本法。第二条 在中华人民共和国境内建设、运营、维护和使用网络，以及网络安全的监督管理，适用本法。") * 2
LO = ("ມາດຕາ ໑ ຈຸດປະສົງ ກົດໝາຍສະບັບນີ້ ກໍານົດຫຼັກການ ລະບຽບການ ແລະ ມາດຕະການ ກ່ຽວກັບການຈັດຕັ້ງ ການເຄື່ອນໄຫວ ແລະ ການຄຸ້ມຄອງ "
      "ວຽກງານການປົກປ້ອງຂໍ້ມູນ ເອເລັກໂຕຣນິກ ເພື່ອຮັບປະກັນ ຄວາມປອດໄພ ຂອງຂໍ້ມູນ") * 2
PT = ("Artigo 1 A presente lei estabelece o regime jurídico da protecção de dados pessoais e aplica-se ao tratamento de "
      "dados que não sejam efectuados por pessoas singulares no exercício de actividades exclusivamente pessoais ou "
      "domésticas. O tratamento de dados pessoais deve processar-se de forma transparente e no estrito respeito pela "
      "reserva da vida privada, bem como pelos direitos, liberdades e garantias fundamentais. A entidade responsável "
      "pelo tratamento é a pessoa singular ou colectiva que determina as finalidades e os meios do tratamento dos dados.")
MS = ("Seksyen 1. Akta ini bolehlah dinamakan Akta Perlindungan Data Peribadi 2010 dan hendaklah mula berkuat kuasa pada "
      "tarikh yang ditetapkan oleh Menteri melalui pemberitahuan dalam Warta. Akta ini terpakai bagi mana-mana orang yang "
      "memproses dan mana-mana orang yang mempunyai kawalan ke atas atau membenarkan pemprosesan apa-apa data peribadi "
      "berkenaan dengan transaksi komersial. Akta ini tidak terpakai bagi Kerajaan Persekutuan dan Kerajaan Negeri.")
EN_SG = ("An Act to govern the collection, use and disclosure of personal data by organisations. Be it enacted by the "
         "President with the advice and consent of the Parliament of Singapore, as follows: This Act is the Personal Data "
         "Protection Act 2012 and shall be deemed to have come into operation on the date of its publication. In this Act, "
         "unless the context otherwise requires, the Commission means the Personal Data Protection Commission. Republic of "
         "Singapore Government Gazette Acts Supplement. Singapore Statutes Online. Printed by the Government Printer, Singapore.")
EN_PLAIN = ("An Act to provide for the regulation of the processing of personal data and for matters connected therewith. "
            "In this Act, unless the context otherwise requires, the following words shall have the meanings assigned to "
            "them. A person who processes data shall comply with the principles set out in this Part, and any person who "
            "contravenes this section commits an offence and is liable on conviction to a fine not exceeding the amount stated.")


class Language(unittest.TestCase):
    def test_scripts_and_stop_words(self):
        self.assertEqual(detect.detect_language(ZH), ("zho", "script"))
        self.assertEqual(detect.detect_language(LO), ("lao", "script"))
        self.assertEqual(detect.detect_language(PT), ("por", "stop words"))
        self.assertEqual(detect.detect_language(MS), ("msa", "stop words"))
        self.assertEqual(detect.detect_language(EN_SG)[0], "eng")
        self.assertIsNone(detect.detect_language("short")[0])

    def test_economy_follows_the_language_or_the_country_marks(self):
        self.assertEqual(detect.detect_economy(ZH, "zho"), ("CN", "the language"))
        self.assertEqual(detect.detect_economy(PT, "por"), ("TL", "the language"))
        self.assertEqual(detect.detect_economy(EN_SG, "eng"), ("SG", "country marks in the text"))
        self.assertIsNone(detect.detect_economy(EN_PLAIN, "eng")[0])


class Text(unittest.TestCase):
    def test_html_docx_and_native_pdf_are_read(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "a.html").write_text(f"<html><head><style>p{{}}</style></head><body><p>{PT}</p></body></html>", encoding="utf-8")
            with zipfile.ZipFile(root / "b.docx", "w") as z:
                z.writestr("word/document.xml", f"<w:document><w:body><w:p><w:r><w:t>{MS}</w:t></w:r></w:p></w:body></w:document>")
            pdf = (b"%PDF-1.4\n1 0 obj << /Length 80 >> stream\nBT /F1 12 Tf (" + EN_SG.encode("latin-1", "replace")
                   + b") Tj ET\nendstream\nendobj\n%%EOF")
            (root / "c.pdf").write_bytes(pdf)
            (root / "d.pdf").write_bytes(b"%PDF-1.4\n1 0 obj << /Type /XObject /Subtype /Image >> stream\n\x00\x01\x02\nendstream\nendobj")
            files = [detect.detect_file(root / n) for n in ("a.html", "b.docx", "c.pdf", "d.pdf")]
            self.assertEqual([f["language"] for f in files], ["por", "msa", "eng", None])
            self.assertEqual([f["economy"] for f in files], ["TL", "MY", "SG", None])
            self.assertIn("no readable text layer", files[3]["basis"])


class Folder(unittest.TestCase):
    def test_suggestion_and_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for i in range(3):
                (root / f"zh{i}.html").write_text(f"<p>{ZH}</p>", encoding="utf-8")
            (root / "lo.html").write_text(f"<p>{LO}</p>", encoding="utf-8")
            files = sorted(root.iterdir())
            free = detect.detect_folder(files)
            self.assertEqual(free["suggested_economy"], None)   # 3 of 4 is below the four-in-five bar
            self.assertEqual(free["by_language"], {"zho": 3, "lao": 1})
            declared = detect.detect_folder(files, declared="CN")
            self.assertEqual(declared["mismatch"], 1)
            self.assertEqual(declared["mismatch_files"], ["lo.html (Lao)"])
            self.assertEqual(detect.detect_folder(files[1:], declared="CN")["mismatch"], 0)

    def test_malaysia_accepts_english_and_malay(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "en.html").write_text(f"<p>{EN_PLAIN}</p>", encoding="utf-8")
            (root / "ms.html").write_text(f"<p>{MS}</p>", encoding="utf-8")
            self.assertEqual(detect.detect_folder(sorted(root.iterdir()), declared="MY")["mismatch"], 0)
            self.assertEqual(detect.detect_folder(sorted(root.iterdir()), declared="SG")["mismatch"], 1)


class Inbox(unittest.TestCase):
    def _settings(self, root: Path):
        return settings_mod.load({"RDTII_RUNS_ROOT": str(root / "outputs"), "RDTII_INBOX_DIR": str(root / "inbox")})

    def test_inbox_folders_name_the_economy_and_the_root_holds_every_economy(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "inbox" / "CN").mkdir(parents=True)
            (root / "inbox" / "LA").mkdir(parents=True)
            (root / "inbox" / "SG").mkdir(parents=True)          # empty: not listed
            (root / "inbox" / "CN" / "csl.html").write_text(f"<p>{ZH}</p>", encoding="utf-8")
            (root / "inbox" / "LA" / "law.html").write_text(f"<p>{LO}</p>", encoding="utf-8")
            s = self._settings(root)
            inputs = [i for i in extract.list_inputs(s) if i["origin"].startswith("inbox")]
            by_name = {i["name"]: i for i in inputs}
            self.assertEqual(set(by_name), {"CN", "LA", "inbox"})
            self.assertEqual(by_name["CN"]["economy"], "CN")
            self.assertEqual(by_name["CN"]["detected"]["by_language"], {"zho": 1})
            self.assertEqual(by_name["CN"]["detected"]["mismatch"], 0)
            self.assertTrue(by_name["inbox"]["per_subfolder"])
            self.assertEqual(by_name["inbox"]["by_economy"], {"CN": 1, "LA": 1})
            from rdtii_ui.pages import scrape as sc
            hand = [f for f in sc.list_crawl_folders(s) if f["kind"] == "hand-collected"]
            self.assertEqual([(f["name"], f["rows"]) for f in hand], [("CN", 1), ("LA", 1)])

    def test_check_and_plan_take_the_economy_from_the_folder(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "inbox" / "CN").mkdir(parents=True)
            (root / "inbox" / "LA").mkdir(parents=True)
            (root / "inbox" / "CN" / "csl.html").write_text(f"<p>{ZH}</p>", encoding="utf-8")
            (root / "inbox" / "CN" / "odd.html").write_text(f"<p>{LO}</p>", encoding="utf-8")
            (root / "inbox" / "LA" / "law.html").write_text(f"<p>{LO}</p>", encoding="utf-8")
            s = self._settings(root)
            app = App(s)
            app.jobs = jobs.JobManager()
            checks = extract.precheck(app, {"input": str(root / "inbox" / "CN")})
            levels = {c["check"]: c["level"] for c in checks}
            self.assertNotIn("fail", levels.values())
            self.assertEqual(levels["economy"], "ok")
            self.assertEqual(levels["detection"], "warn")
            self.assertIn("odd.html (Lao)", next(c["text"] for c in checks if c["check"] == "detection"))
            rows = extract.build_manifest_rows(root / "inbox", "")
            self.assertEqual(sorted(r["economy"] for r in rows), ["CN", "CN", "LA"])
            self.assertTrue(all(r["doc_id"].startswith(r["economy"].lower() + "-") for r in rows))
            job = extract.plan_extract(app, {"input": str(root / "inbox")})
            runs = [st.argv for st in job.steps if "run" in st.argv]
            sel = {(a[a.index("--economy") + 1], a[a.index("--default-language") + 1]) for a in runs}
            self.assertEqual(sel, {("CN", "zho"), ("LA", "lao")})

    def test_a_batch_is_an_input_of_its_own_with_the_economy_from_its_parent(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            batch = root / "inbox" / "CN" / "2026-09-30_101522"
            batch.mkdir(parents=True)
            (batch / "csl.html").write_text(f"<p>{ZH}</p>", encoding="utf-8")
            (root / "inbox" / "CN" / "loose.html").write_text(f"<p>{ZH}</p>", encoding="utf-8")
            s = self._settings(root)
            inputs = {i["origin"]: i for i in extract.list_inputs(s) if i["origin"].startswith("inbox")}
            self.assertEqual(inputs["inbox"]["rows"], 2)
            b = inputs["inbox batch"]
            self.assertEqual((b["economy"], b["batch"], b["rows"], b["out_name"]), ("CN", "2026-09-30_101522", 1, "CN_2026-09-30_101522"))
            rows = extract.build_manifest_rows(root / "inbox" / "CN", "")
            notes = {r["local_path"]: r["crawl_notes"] for r in rows}
            self.assertIn("batch 2026-09-30_101522", notes["2026-09-30_101522/csl.html"])
            self.assertNotIn("batch", notes["loose.html"])
            m = extract.write_manifest(s, root / "inbox" / "CN", rows)
            import csv as _csv
            with open(m.parent / "law_table.csv", encoding="utf-8-sig", newline="") as f:
                lt = {r["doc_id"]: r["batch"] for r in _csv.DictReader(f)}
            self.assertEqual(sorted(lt.values()), ["", "2026-09-30_101522"])

    def test_free_folder_gets_a_suggestion_and_needs_confirmation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "loose").mkdir()
            (root / "loose" / "a.html").write_text(f"<p>{PT}</p>", encoding="utf-8")
            s = self._settings(root)
            app = App(s)
            desc = extract.describe_input(root / "loose", "typed")
            self.assertIsNone(desc["economy"])
            self.assertEqual(desc["detected"]["suggested_economy"], "TL")
            checks = extract.precheck(app, {"input": str(root / "loose")})
            econ = next(c for c in checks if c["check"] == "economy")
            self.assertEqual(econ["level"], "fail")
            self.assertIn("Timor-Leste", econ["text"])
            checks = extract.precheck(app, {"input": str(root / "loose"), "economy": "TL"})
            self.assertFalse([c for c in checks if c["level"] == "fail"])


if __name__ == "__main__":
    unittest.main()
