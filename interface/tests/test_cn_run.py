"""China from the Scraping tab: the China tools as a job of their own, and their folders as Extraction inputs."""
import tempfile
import unittest
from pathlib import Path

from . import INTERFACE  # noqa: F401
from rdtii_ui import jobs, settings as settings_mod
from rdtii_ui.pages import cn_run, extract, scrape
from rdtii_ui.server import App

REPO = settings_mod.REPO


class Sources(unittest.TestCase):
    def setUp(self):
        self.s = settings_mod.load({})

    def test_china_is_offered_through_its_tools_not_the_engine(self):
        econs = {e["code"]: e for e in scrape.list_economies(self.s)}
        self.assertFalse(econs["CN"]["crawlable"])
        self.assertTrue(econs["CN"]["tools"])
        self.assertFalse(econs["SG"].get("tools"))

    def test_china_card_lists_the_permitted_publishers_and_the_hand_list(self):
        d = scrape.describe_sources(self.s, "CN")
        ports = d["portals"]
        self.assertEqual(len(ports), 8)
        self.assertEqual([p["layer"] for p in ports], [1, 2, 2, 2, 2, 2, 2, 2])
        by = {p["src"]: p for p in ports}
        self.assertEqual((by["npc-database"]["mode"], by["npc-database"]["held"]), ("hand", 945))
        self.assertEqual((by["cac"]["held"], by["links"]["held"], by["miit"]["held"], by["customs"]["held"]), (111, 6, 34, 0))
        self.assertEqual([p["src"] for p in ports if p["selectable"]], ["cac", "links", "samr", "mofcom", "oscca"])
        self.assertEqual([p["src"] for p in ports if p["deferred"]], ["samr", "mofcom", "oscca"])
        self.assertEqual((by["samr"]["set_aside"], by["mofcom"]["set_aside"], by["oscca"]["set_aside"]), (235, 160, 12))
        self.assertEqual(d["holdings_sub"], "(9.30 Finale Submission)")
        self.assertTrue(any(k == "Set aside" and "SAMR 235" in v for k, v in d["facts"]))
        self.assertEqual(d["holdings_label"], "What we hold today")
        self.assertTrue(d["tools_note"])
        self.assertEqual(len(d["watchlist"]), 33)
        self.assertEqual(d["counts"], {"all": 1096, "layer1": 945, "layer2": 151})
        self.assertEqual(d["facts"][0][0], "All")

    def test_china_documents_come_from_the_shipped_collection_by_layer(self):
        d = cn_run.list_documents(self.s, "layer2")
        self.assertEqual(d["total"], 151)
        kinds = {r["kind"].split(":")[0] for r in d["documents"]}
        self.assertEqual(kinds, {"CAC", "gov.cn", "MIIT"})
        self.assertTrue(all(r["url"] for r in d["documents"] if r["kind"].startswith("CAC")))
        l1 = cn_run.list_documents(self.s, "layer1")
        self.assertEqual(l1["total"], 945)
        self.assertTrue(all(r["url"] == "" for r in l1["documents"]))   # the national database is downloaded by hand
        self.assertEqual(scrape.list_documents.__module__, "rdtii_ui.pages.scrape")


class Check(unittest.TestCase):
    def setUp(self):
        self.app = App(settings_mod.load({}))

    def test_china_alone_skips_the_engine_checks(self):
        checks = scrape.precheck(self.app, {"economies": ["CN"], "cn_mode": "update", "dry_run": True})
        self.assertFalse([c for c in checks if c["level"] == "fail"], checks)
        self.assertTrue(any(c["check"] == "cn_baseline" for c in checks))
        self.assertFalse(any(c["check"] == "browser" for c in checks))

    def test_mixed_selection_checks_both(self):
        checks = scrape.precheck(self.app, {"economies": ["SG", "CN"], "cn_mode": "collect", "cn_sources": ["cac"], "scope": "all"})
        names = {c["check"] for c in checks}
        self.assertIn("browser", names)
        self.assertIn("cn_tools", names)
        econ = next(c for c in checks if c["check"] == "economies")
        self.assertIn("China through its tools", econ["text"])

    def test_bad_mode_fails(self):
        checks = scrape.precheck(self.app, {"economies": ["CN"], "cn_mode": "nonsense"})
        self.assertTrue(any(c["level"] == "fail" and c["check"] == "cn_mode" for c in checks))
        checks = scrape.precheck(self.app, {"economies": ["CN"], "cn_mode": "collect", "cn_sources": []})
        self.assertTrue(any(c["level"] == "fail" and "tick at least one" in c["text"] for c in checks))


class Plan(unittest.TestCase):
    def test_update_check_stages_the_baseline_and_runs_the_update_tool(self):
        with tempfile.TemporaryDirectory() as d:
            s = settings_mod.load({"RDTII_RUNS_ROOT": str(Path(d) / "outputs")})
            app = App(s)
            app.jobs = jobs.JobManager()
            job = cn_run.plan_cn(app, {"cn_mode": "update", "dry_run": True})
            step = job.steps[0]
            self.assertEqual(step.argv[1:], ["update.py", "--base", cn_run.BASELINE])
            self.assertTrue(step.cwd.name == "cn_npc")
            data = Path(step.env["HANDOFF1_DIR"])
            self.assertEqual(data.name, "data")
            self.assertTrue((data / "CN" / cn_run.BASELINE / "auto" / "cac" / "list.csv").is_file())
            self.assertFalse(list((data / "CN").rglob("raw")))       # index files only, never the bytes
            self.assertTrue(job.out_dir.name.startswith("CN_"))
            self.assertIn("(dry run)", job.title)
            job2 = cn_run.plan_cn(app, {"cn_mode": "update"})
            self.assertEqual(job2.steps[0].argv[-1], "--fetch")

    def test_collect_runs_the_collect_tool_with_the_links_staged(self):
        with tempfile.TemporaryDirectory() as d:
            s = settings_mod.load({"RDTII_RUNS_ROOT": str(Path(d) / "outputs")})
            app = App(s)
            app.jobs = jobs.JobManager()
            job = cn_run.plan_cn(app, {"cn_mode": "collect_all", "dry_run": True})
            self.assertEqual(job.steps[0].argv[1:], ["collect.py", "all", "--list-only"])
            data = Path(job.steps[0].env["HANDOFF1_DIR"])
            self.assertTrue((data / "CN" / "CN_layer2_links.md").is_file())
            job2 = cn_run.plan_cn(app, {"cn_mode": "collect_cac"})
            self.assertEqual(job2.steps[0].argv[1:], ["collect.py", "cac"])
            job3 = cn_run.plan_cn(app, {"cn_mode": "collect", "cn_sources": ["samr", "cac"], "dry_run": True})
            self.assertEqual([st.argv[1:] for st in job3.steps], [["collect.py", "cac", "--list-only"], ["collect.py", "samr", "--list-only"]])
            self.assertIn("Collect CAC, SAMR", job3.title)

    def test_parser_turns_the_tools_lines_into_sentences(self):
        job = jobs.Job(stage="p1", title="t", steps=[])
        out = cn_run.parse_cn("   111 listed now; 3 new, 0 gone, 1 retitled", job)
        self.assertEqual(out[0], "CAC lists 111 documents now: 3 new, 0 gone, 1 retitled.")
        out = cn_run.parse_cn("     7/111  OK        4574c  数字乡村高质量发展行动计划", job)
        self.assertTrue(out[0].startswith("Fetched 7 of 111"))
        self.assertEqual(out[1]["total"], 111)
        self.assertEqual(cn_run.parse_cn("[CAC] 政策法规 index", job)[0], "CAC: 政策法规 index.")
        self.assertIsNone(cn_run.parse_cn("=====", job))


class ExtractionInput(unittest.TestCase):
    def test_a_run_folder_feeds_extraction_with_the_economy_fixed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            s = settings_mod.load({"RDTII_RUNS_ROOT": str(root / "outputs"), "RDTII_INBOX_DIR": str(root / "inbox")})
            src = root / "outputs" / "scrape" / "CN_20260930-120000" / "data" / "CN" / cn_run.BASELINE / "auto" / "cac"
            (src / "raw").mkdir(parents=True)
            (src / "raw" / "abc-1a2b3c4d.html").write_text("<p>第一条 网络安全</p>", encoding="utf-8")
            (src / "provenance.tsv").write_text("n\ttitle\turl\tfile\n1\t网络安全法\thttps://www.cac.gov.cn/x.htm\tabc-1a2b3c4d\n", encoding="utf-8")
            folders = {f["kind"]: f for f in scrape.list_crawl_folders(s)}
            run = folders["China tools run"]
            self.assertEqual((run["rows"], run["cn_sources"]), (1, {"cac": 1}))
            inputs = [i for i in extract.list_inputs(s) if i["origin"] == "China tools"]
            self.assertEqual(len(inputs), 1)
            self.assertEqual((inputs[0]["economy"], inputs[0]["out_name"]), ("CN", "CN_20260930-120000_cac"))
            rows = extract.build_manifest_rows(src, "CN")
            self.assertEqual(rows[0]["source_url"], "https://www.cac.gov.cn/x.htm")
            self.assertEqual(rows[0]["retrieval_method"], "requests")
            self.assertTrue(rows[0]["doc_id"].startswith("cn-"))
            checks = extract.precheck(App(s), {"input": str(src)})
            self.assertFalse([c for c in checks if c["level"] == "fail"], checks)
            self.assertIn("the China tools run", next(c["text"] for c in checks if c["check"] == "economy"))


if __name__ == "__main__":
    unittest.main()
