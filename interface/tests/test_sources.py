"""Results are filed by economy, then source: the crawl output, the inbox, Extraction's inputs and Clear."""
import tempfile
import unittest
import zipfile
from pathlib import Path

from . import INTERFACE  # noqa: F401
from rdtii_ui import fsguard, jobs, readiness, settings as settings_mod, sources, weburl
from rdtii_ui.pages import cn_run, extract, inbox, scrape
from rdtii_ui.server import ApiError, App

BATCH = "2026-10-03_101522"
SAVED = (b"<!DOCTYPE html>\n<!-- saved from url=(0040)https://www.miit.gov.cn/zwgk/art/x.html -->\n"
         b"<html><body><p>\xe7\xac\xac\xe4\xb8\x80\xe6\x9d\xa1</p></body></html>")


def _settings(root: Path) -> settings_mod.Settings:
    return settings_mod.load({"RDTII_RUNS_ROOT": str(root / "outputs"), "RDTII_INBOX_DIR": str(root / "inbox")})


def _docx(path: Path, text: str = "Article 1. Text.") -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("word/document.xml", f"<w:document><w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>")


class Keys(unittest.TestCase):
    def setUp(self):
        self.s = settings_mod.load({})

    def test_a_key_is_made_from_the_address(self):
        self.assertEqual(sources.host_key("https://www.pdpc.gov.sg/"), "pdpc-gov-sg")
        self.assertEqual(sources.host_key("http://exportcontrol.mofcom.gov.cn/x?y=1"), "exportcontrol-mofcom-gov-cn")
        self.assertEqual(sources.slug("Jornal da Rep\u00fablica \u00b7 Diploma Ministerial"), "jornal-da-republica-diploma-ministerial")
        self.assertEqual(sources.slug("\u56fd\u5bb6\u6cd5\u5f8b"), "")

    def test_each_crawled_economy_has_one_portal_folder(self):
        got = {c: sources.crawl_source(self.s, c)["key"] for c in ("SG", "AU", "MY", "TL", "LA")}
        self.assertEqual(got, {"SG": "sso-agc-gov-sg", "AU": "legislation-gov-au", "MY": "lom-agc-gov-my",
                               "TL": "mj-gov-tl", "LA": "laoofficialgazette-gov-la"})

    def test_designated_sources_come_from_the_stages_own_lists(self):
        self.assertEqual([x["key"] for x in sources.designated(self.s, "CN")], ["npc-database", "miit", "customs"])
        for code in ("SG", "AU", "MY", "TL", "LA"):
            listed = sources.designated(self.s, code)
            wl = scrape.read_watchlist(scrape.watchlist_path(self.s, code))
            keys = [x["key"] for x in listed]
            self.assertEqual(len(listed), len(wl), code)
            self.assertEqual(len(set(keys)), len(keys), f"{code}: keys must be unique")
            for k in keys:
                self.assertRegex(k, r"^[a-z0-9][a-z0-9-]{0,63}$")
                self.assertNotRegex(k, r"^\d{4}-\d{2}-\d{2}_\d{6}$")
        sg = [x["key"] for x in sources.designated(self.s, "SG")]
        self.assertIn("pdpc-gov-sg", sg)
        self.assertEqual(len([k for k in sg if k.startswith("customs-gov-sg-")]), 3)     # one host, three sources
        self.assertEqual(sources.find(self.s, "CN", "miit")["host"], "miit.gov.cn")
        self.assertEqual(sources.find(self.s, "SG", "sso-agc-gov-sg")["mode"], "crawl")
        self.assertIsNone(sources.find(self.s, "SG", "nowhere"))

    def test_where_an_inbox_folder_sits(self):
        inbox_dir = Path("/x/inbox")
        f = lambda rel: sources.inbox_identity(inbox_dir / rel, inbox_dir)  # noqa: E731
        self.assertEqual(f("CN/miit"), {"economy": "CN", "source": "miit", "batch": "", "legacy": False})
        self.assertEqual(f(f"CN/miit/{BATCH}"), {"economy": "CN", "source": "miit", "batch": BATCH, "legacy": False})
        self.assertEqual(f(f"CN/{BATCH}"), {"economy": "CN", "source": "", "batch": BATCH, "legacy": True})
        self.assertEqual(f("CN")["legacy"], True)
        self.assertEqual(sources.inbox_identity(Path("/elsewhere/CN/miit"), inbox_dir), {})


class CrawlFolders(unittest.TestCase):
    def _app(self, root: Path) -> App:
        app = App(_settings(root))
        app.jobs = jobs.JobManager()
        return app

    def test_a_new_crawl_is_filed_under_its_economy_and_portal(self):
        with tempfile.TemporaryDirectory() as d:
            app = self._app(Path(d))
            job = scrape.plan_scrape(app, {"economies": ["SG"], "scope": "seed", "dry_run": True})
            rel = job.out_dir.relative_to(Path(d) / "outputs" / "scrape").parts
            self.assertEqual(rel[:2], ("SG", "sso-agc-gov-sg"))
            self.assertRegex(rel[2], r"^\d{8}-\d{6}$")
            self.assertEqual(job.steps[1].argv[job.steps[1].argv.index("--out") + 1], str(job.out_dir))

    def test_china_tools_runs_are_filed_under_cn(self):
        with tempfile.TemporaryDirectory() as d:
            app = self._app(Path(d))
            job = cn_run.plan_cn(app, {"cn_mode": "update", "dry_run": True})
            rel = job.out_dir.relative_to(Path(d) / "outputs" / "scrape").parts
            self.assertEqual(rel[:2], ("CN", "china-tools"))
            self.assertTrue(cn_run.is_run(job.out_dir))

    def test_both_layouts_are_listed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            s = _settings(root)
            new = root / "outputs" / "scrape" / "SG" / "sso-agc-gov-sg" / "20261003-101500"
            old = root / "outputs" / "scrape" / "SG_20260930-000323"
            hand = root / "outputs" / "scrape" / "CN" / "miit" / "hand_all_20261003-101500"
            for p in (new, old, hand):
                p.mkdir(parents=True)
                (p / "manifest.csv").write_text("doc_id,economy,source_type,local_path\nsg-a-001,SG,html,raw/a.html\n", encoding="utf-8")
            runs = dict((p.name, where) for p, where in sources.scrape_runs(s))
            self.assertEqual(runs["20261003-101500"], {"economy": "SG", "source": "sso-agc-gov-sg", "run": "20261003-101500"})
            self.assertEqual(runs["SG_20260930-000323"], {})
            by = {f["name"]: f for f in scrape.list_crawl_folders(s) if f["kind"] in ("interface run", "hand-collected manifest")}
            self.assertEqual((by["20261003-101500"]["economy"], by["20261003-101500"]["source"]), ("SG", "sso-agc-gov-sg"))
            self.assertIn("Singapore", by["20261003-101500"]["source_name"])
            self.assertEqual(by["SG_20260930-000323"]["economy"], "")
            self.assertEqual(by["hand_all_20261003-101500"]["kind"], "hand-collected manifest")
            empty = root / "outputs" / "scrape" / "SG" / "sso-agc-gov-sg" / "20261003-225523"      # a run the crawler skipped
            empty.mkdir()
            (empty / "manifest.csv").write_text("doc_id,economy,source_type,local_path", encoding="utf-8")     # a header and no row
            names = [i["name"] for i in extract.list_inputs(s) if i["origin"] == "interface crawl"]
            self.assertIn("20261003-101500", names)
            self.assertNotIn("20261003-225523", names)                       # nothing fetched, nothing to extract
            self.assertNotIn("hand_all_20261003-101500", names)              # its documents sit in the inbox
            desc = extract.describe_input(new, "interface crawl", s)
            self.assertEqual(desc["out_name"], "SG_sso-agc-gov-sg_20261003-101500")

    def test_clear_takes_a_run_folder_in_either_layout_and_nothing_wider(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "outputs"
            run = root / "scrape" / "SG" / "sso-agc-gov-sg" / "20261003-101500"
            (run / "raw").mkdir(parents=True)
            (root / "scrape" / "SG_old" / "raw").mkdir(parents=True)
            s = settings_mod.load({"RDTII_RUNS_ROOT": str(root)})
            self.assertEqual(fsguard.check_clearable(s, str(run), []), run.resolve())
            fsguard.check_clearable(s, str(run / "raw"), [])
            fsguard.check_clearable(s, str(root / "scrape" / "SG_old"), [])
            fsguard.check_clearable(s, str(root / "scrape" / "SG_old" / "raw"), [])
            (run / "notes").mkdir()
            for bad in (root / "scrape" / "SG", root / "scrape" / "SG" / "sso-agc-gov-sg", run / "notes"):
                with self.assertRaises(ApiError, msg=str(bad)):
                    fsguard.check_clearable(s, str(bad), [])


class HandCollected(unittest.TestCase):
    def test_the_drop_says_how_each_file_is_read_and_agrees_with_the_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            s = _settings(root)
            got = inbox.save(s, "CN", "miit", "catalogue.pdf", b"%PDF-1.4\n/Font", BATCH)
            self.assertEqual(got["reads"]["status"], "ready")
            self.assertIn("PDF", got["reads"]["method"])
            old = inbox.save(s, "CN", "miit", "old.doc", readiness.OLE2 + b"\x00" * 600, BATCH)
            self.assertEqual(old["reads"]["status"], "cannot_read")
            self.assertIn("Save As .docx", old["reads"]["action"])
            inbox.save(s, "CN", "miit", "rule.html", SAVED, BATCH)
            inbox.save(s, "CN", "miit", "bare.html", b"<html><body>no address in it</body></html>", BATCH)
            src = sources.find(s, "CN", "miit")
            folder = root / "inbox" / "CN" / "miit"
            listed = {f["name"]: (f["status"], f["method"], f["action"]) for f in inbox.list_files(folder, s, src)}
            rows = {r["local_path"]: (r["_status"], r["_method"], r["_action"]) for r in extract.build_manifest_rows(folder, "", s=s)}
            self.assertEqual(listed, rows)                       # one rule, shown in two places
            self.assertEqual(listed[f"{BATCH}/bare.html"][0], "ready")      # judged by its source's page
            self.assertNotIn("status", inbox.list_files(folder)[0])         # without a source nothing is judged

    def test_a_typed_address_changes_how_a_page_is_read(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            s = _settings(root)
            key = "pdpc-gov-sg"
            inbox.save(s, "SG", key, "act.html", b"<html><body>An Act</body></html>", BATCH)
            src = sources.find(s, "SG", key)
            folder = root / "inbox" / "SG" / key
            self.assertEqual(inbox.list_files(folder, s, src)[0]["status"], "cannot_read")
            inbox.set_address(s, "SG", key, BATCH, "act.html", "https://www.legislation.gov.au/C2004A03712/latest/text")
            self.assertEqual(inbox.list_files(folder, s, src)[0]["method"], "web page, the legislation.gov.au parser")

    def test_the_page_is_told_each_economys_crawl_folder(self):
        s = settings_mod.load({})
        by = {e["code"]: e for e in scrape.list_economies(s)}
        self.assertEqual(by["SG"]["source"], "sso-agc-gov-sg")
        self.assertEqual(by["CN"]["source"], "china-tools")
        self.assertTrue(all(e["source"] for e in by.values() if e["crawlable"]))

    def test_a_source_and_each_of_its_batches_are_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            s = _settings(root)
            inbox.save(s, "CN", "miit", "rule.html", SAVED, BATCH)
            inbox.save(s, "CN", "miit", "catalogue.pdf", b"%PDF-1.4\n/Font", "2026-10-04_090000")
            inputs = {i["origin"]: i for i in extract.list_inputs(s) if i["origin"].startswith(("hand", "inbox"))}
            src = inputs["hand-collected source"]
            self.assertEqual((src["economy"], src["source"], src["rows"], src["out_name"]), ("CN", "miit", 2, "CN_miit"))
            self.assertIn("MIIT", src["source_name"])
            batches = [i for i in extract.list_inputs(s) if i["origin"] == "hand-collected batch"]
            self.assertEqual(sorted(b["out_name"] for b in batches), [f"CN_miit_{BATCH}", "CN_miit_2026-10-04_090000"])
            self.assertEqual(inputs["inbox"]["rows"], 2)            # the economy's whole inbox, every source
            hand = [f for f in scrape.list_crawl_folders(s) if f["kind"] == "hand-collected"]
            self.assertEqual([(f["economy"], f["source"], f["rows"]) for f in hand], [("CN", "miit", 2)])

    def test_rows_carry_the_address_or_the_sources_page(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            s = _settings(root)
            inbox.save(s, "CN", "miit", "rule.html", SAVED, BATCH)
            inbox.save(s, "CN", "miit", "catalogue.pdf", b"%PDF-1.4\n/Font", BATCH)
            rows = {r["local_path"]: r for r in extract.build_manifest_rows(root / "inbox" / "CN" / "miit", "", s=s)}
            page, pdf = rows[f"{BATCH}/rule.html"], rows[f"{BATCH}/catalogue.pdf"]
            self.assertEqual((page["economy"], page["source_url"], page["_url_basis"]),
                             ("CN", "https://www.miit.gov.cn/zwgk/art/x.html", "the file's own address"))
            self.assertEqual((page["_status"], page["_method"]), ("ready", "web page, the miit.gov.cn parser"))
            self.assertEqual((pdf["source_url"], pdf["_url_basis"]), ("https://www.miit.gov.cn", "the source's page"))
            self.assertIn("source miit", pdf["crawl_notes"])
            self.assertIn("document's own was not recorded", pdf["crawl_notes"])
            self.assertEqual(pdf["retrieval_method"], "hand_collected")

    def test_what_cannot_be_read_is_left_out_and_listed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            s = _settings(root)
            app = App(s)
            app.jobs = jobs.JobManager()
            folder = root / "inbox" / "CN" / "miit" / BATCH
            inbox.save(s, "CN", "miit", "catalogue.pdf", b"%PDF-1.4\n/Font", BATCH)
            inbox.save(s, "CN", "miit", "old.doc", readiness.OLE2 + b"\x00" * 600, BATCH)
            inbox.save(s, "CN", "miit", "wrong.pdf", b"<html><body>404</body></html>", BATCH)
            _docx(folder / "renamed.doc")
            rows = {Path(r["local_path"]).name: r for r in extract.build_manifest_rows(folder, "", s=s)}
            self.assertEqual({k: v["_status"] for k, v in rows.items()},
                             {"catalogue.pdf": "ready", "old.doc": "cannot_read", "wrong.pdf": "cannot_read", "renamed.doc": "ready"})
            self.assertIn("Save As .docx", rows["old.doc"]["_action"])
            self.assertIn("web page", rows["wrong.pdf"]["_action"])
            checks = {c["check"]: c for c in extract.precheck(app, {"input": str(folder)})}
            self.assertEqual(checks["readiness"]["level"], "warn")
            self.assertIn("2 of 4", checks["readiness"]["text"])
            self.assertEqual(checks["economy"]["level"], "ok")
            job = extract.plan_extract(app, {"input": str(folder)})
            manifest = Path(next(st.argv[st.argv.index("--manifest") + 1] for st in job.steps if "--manifest" in st.argv))
            self.assertEqual(manifest.parent.parent.parent.name, "CN")              # filed like a crawl
            self.assertEqual(manifest.parent.parent.name, "miit")
            self.assertTrue(manifest.parent.name.startswith(f"hand_{BATCH}_"))
            body = manifest.read_text(encoding="utf-8-sig")
            self.assertIn("catalogue.pdf", body)
            self.assertNotIn("old.doc", body)
            left = (manifest.parent / "left_out.csv").read_text(encoding="utf-8-sig")
            self.assertIn("old.doc", left)
            self.assertIn("wrong.pdf", left)

    def test_a_page_from_a_site_with_no_parser_is_not_ready(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            s = _settings(root)
            key = "pdpc-gov-sg"
            inbox.save(s, "SG", key, "guide.html", b"<html><body>Guidelines</body></html>", BATCH)
            inbox.save(s, "SG", key, "guide.pdf", b"%PDF-1.4\n/Font", BATCH)
            rows = {Path(r["local_path"]).name: r for r in extract.build_manifest_rows(root / "inbox" / "SG" / key, "", s=s)}
            self.assertEqual(rows["guide.pdf"]["_status"], "ready")
            self.assertEqual(rows["guide.html"]["_status"], "cannot_read")
            self.assertIn("Print the page to PDF", rows["guide.html"]["_action"])
            self.assertIn("pdpc.gov.sg", rows["guide.html"]["_action"])

    def test_nothing_readable_stops_the_run(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            s = _settings(root)
            app = App(s)
            app.jobs = jobs.JobManager()
            inbox.save(s, "CN", "customs", "old.doc", readiness.OLE2 + b"\x00" * 600, BATCH)
            folder = root / "inbox" / "CN" / "customs" / BATCH
            checks = {c["check"]: c for c in extract.precheck(app, {"input": str(folder)})}
            self.assertEqual(checks["readiness"]["level"], "fail")
            with self.assertRaises(ApiError):
                extract.plan_extract(app, {"input": str(folder)})

    def test_the_inbox_has_one_hand_collected_folder_per_economy_and_none_per_source(self):
        with tempfile.TemporaryDirectory() as d:
            s = _settings(Path(d))
            extract.ensure_inbox(s)
            for code in extract.HAND_ECONOMIES:
                self.assertEqual([p.name for p in (Path(d) / "inbox" / code).iterdir()], ["Hand_collected"], code)

    def test_the_hand_collected_folder_is_filed_listed_and_extracted_like_a_source(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            s = _settings(root)
            app = App(s)
            app.jobs = jobs.JobManager()
            inbox.save(s, "SG", "", "guide.pdf", b"%PDF-1.4\n/Font", BATCH)
            inbox.save(s, "SG", "", "old.doc", readiness.OLE2 + b"\x00" * 600, BATCH)
            inbox.save(s, "SG", "", "act.html", b"<html><body>An Act</body></html>", "2026-10-05_090000")
            folder = root / "inbox" / "SG" / "Hand_collected"
            # its place says what it is
            self.assertEqual(sources.inbox_identity(folder, s.inbox_dir), {"economy": "SG", "source": "Hand_collected", "batch": "", "legacy": False})
            self.assertEqual(sources.inbox_identity(folder / BATCH, s.inbox_dir)["batch"], BATCH)
            self.assertEqual(sources.find(s, "SG", "Hand_collected")["name"], "Hand-collected")
            # Extraction offers the folder and each batch
            inputs = extract.list_inputs(s)
            whole = next(i for i in inputs if i["origin"] == "hand-collected source")
            self.assertEqual((whole["economy"], whole["source"], whole["rows"], whole["out_name"]), ("SG", "Hand_collected", 3, "SG_Hand_collected"))
            self.assertIn("hand-collected folder", whole["language_line"])
            self.assertEqual(sorted(i["out_name"] for i in inputs if i["origin"] == "hand-collected batch"),
                             [f"SG_Hand_collected_{BATCH}", "SG_Hand_collected_2026-10-05_090000"])
            # a file is read by what it is; with no source there is no page to cite, and a web page needs its address
            rows = {Path(r["local_path"]).name: r for r in extract.build_manifest_rows(folder, "", s=s)}
            self.assertEqual({k: v["_status"] for k, v in rows.items()}, {"guide.pdf": "ready", "old.doc": "cannot_read", "act.html": "cannot_read"})
            self.assertEqual((rows["guide.pdf"]["economy"], rows["guide.pdf"]["source_url"], rows["guide.pdf"]["_url_basis"]), ("SG", "", ""))
            self.assertIn("Type the page's address", rows["act.html"]["_action"])
            inbox.set_address(s, "SG", "", "2026-10-05_090000", "act.html", "https://www.legislation.gov.au/C2004A03712/latest/text")
            rows = {Path(r["local_path"]).name: r for r in extract.build_manifest_rows(folder, "", s=s)}
            self.assertEqual(rows["act.html"]["_method"], "web page, the legislation.gov.au parser")   # by its address, not by a source
            # the run leaves out what cannot be read, and its manifest is filed like a crawl
            job = extract.plan_extract(app, {"input": str(folder / BATCH)})
            manifest = Path(next(st.argv[st.argv.index("--manifest") + 1] for st in job.steps if "--manifest" in st.argv))
            self.assertEqual((manifest.parent.parent.parent.name, manifest.parent.parent.name), ("SG", "Hand_collected"))
            self.assertIn("old.doc", (manifest.parent / "left_out.csv").read_text(encoding="utf-8-sig"))
            # Scraping's Output lists the folder, and the manifest written for it
            listed = scrape.list_crawl_folders(s)
            hand = [f for f in listed if f["kind"] == "hand-collected"]
            self.assertEqual([(f["economy"], f["source"], f["source_name"], f["rows"]) for f in hand], [("SG", "Hand_collected", "Hand-collected", 3)])
            written = [f for f in listed if f["kind"] == "hand-collected manifest"]
            self.assertEqual([(f["economy"], f["source_name"]) for f in written], [("SG", "Hand-collected")])


class Judging(unittest.TestCase):
    def test_what_a_file_is(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "a.pdf").write_bytes(b"%PDF-1.7\n")
            (root / "b.doc").write_bytes(readiness.OLE2 + b"\x00" * 100)
            (root / "c.html").write_bytes(b"\xef\xbb\xbf<!DOCTYPE html><html></html>")
            (root / "d.rtf").write_bytes(b"{\\rtf1 hello}")
            (root / "e.bin").write_bytes(b"\x00\x01\x02")
            _docx(root / "f.docx")
            with zipfile.ZipFile(root / "g.zip", "w") as zf:
                zf.writestr("x.txt", "x")
            got = {p.name: readiness.sniff(p) for p in sorted(root.iterdir())}
            self.assertEqual(got, {"a.pdf": "pdf", "b.doc": "doc_ole", "c.html": "html", "d.rtf": "rtf", "e.bin": "other",
                                   "f.docx": "docx", "g.zip": "zip"})

    def test_the_stages_own_host_rule(self):
        hosts = ("legislation.gov.au", "cac.gov.cn", "miit.gov.cn", "gov.cn")
        self.assertEqual(readiness.match_host("www.miit.gov.cn", hosts), "miit.gov.cn")
        self.assertEqual(readiness.match_host("hca.miit.gov.cn", hosts), "miit.gov.cn")      # the longest wins
        self.assertEqual(readiness.match_host("www.customs.gov.cn", hosts), "gov.cn")
        self.assertIsNone(readiness.match_host("notgov.cn", hosts))
        self.assertIsNone(readiness.match_host("pdpc.gov.sg", hosts))

    def test_the_registered_hosts_are_read_from_the_stage(self):
        self.assertEqual(set(extract.html_hosts(settings_mod.load({}))), {"legislation.gov.au", "cac.gov.cn", "miit.gov.cn", "gov.cn"})


class SavedPages(unittest.TestCase):
    def test_the_address_is_found_in_the_file(self):
        self.assertEqual(weburl.recover_url(SAVED)[0], "https://www.miit.gov.cn/zwgk/art/x.html")
        self.assertEqual(weburl.recover_url(b'<html><head><link rel="canonical" href="https://www.pdpc.gov.sg/g/x"></head>'),
                         ("https://www.pdpc.gov.sg/g/x", "the page's canonical link"))
        self.assertEqual(weburl.recover_url(b'<meta property="og:url" content="https://example.org/a?b=1&amp;c=2">'),
                         ("https://example.org/a?b=1&c=2", "the page's og:url"))

    def test_only_web_addresses_are_accepted(self):
        self.assertEqual(weburl.recover_url(b"<!-- saved from url=(0016)file:///C:/x.html -->"), ("", ""))
        self.assertEqual(weburl.recover_url(b"<html><body>no address</body></html>"), ("", ""))
        for bad in ("javascript:alert(1)", "ftp://a.b/c", "https://a b.c/", "https://nodot", "", "x" * 3000):
            self.assertFalse(weburl.valid_url(bad), bad)
        self.assertTrue(weburl.valid_url("https://www.miit.gov.cn/zwgk/zcwj/art_1.html"))


if __name__ == "__main__":
    unittest.main()
