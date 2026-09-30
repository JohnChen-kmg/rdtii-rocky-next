"""The Scraping Start plan: the crawler command, the link-list frontier, politeness, and the parser."""
import tempfile
import unittest
from pathlib import Path

from . import INTERFACE  # noqa: F401
from rdtii_ui import jobs, settings as settings_mod
from rdtii_ui.pages import scrape
from rdtii_ui.server import App, ApiError


def _app(runs_root: str) -> App:
    app = App(settings_mod.load({"RDTII_RUNS_ROOT": runs_root}))
    app.jobs = jobs.JobManager()
    return app


class Plan(unittest.TestCase):
    def test_frontier_prefixes_come_from_the_adapters(self):
        s = settings_mod.load({})
        self.assertEqual(scrape.frontier_prefix(s, "SG"), "SSO")
        self.assertEqual(scrape.frontier_prefix(s, "MY"), "LOM")
        self.assertEqual(scrape.frontier_prefix(s, "AU"), "REGISTER")
        self.assertEqual(scrape.frontier_prefix(s, "TL"), "JORNAL")
        self.assertEqual(scrape.frontier_prefix(s, "LA"), "GAZETTE")
        self.assertIsNone(scrape.frontier_prefix(s, "CN"))
        self.assertTrue(scrape.links_file(s, "SG").is_file())

    def test_dry_run_plan_for_singapore(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            job = scrape.plan_scrape(app, {"economies": ["SG"], "scope": "seed", "dry_run": True, "frontier": "links"})
            self.assertEqual(len(job.steps), 2)
            crawl = job.steps[1]
            self.assertEqual(crawl.argv[1:3], ["scrape.py", "--economy"])
            self.assertIn("SG", crawl.argv)
            self.assertIn("--dry-run", crawl.argv)
            self.assertIn("--scope", crawl.argv)
            self.assertEqual(crawl.argv[crawl.argv.index("--scope") + 1], "seed")
            self.assertEqual(crawl.env["REQUEST_DELAY_MS"], "6000")
            self.assertEqual(crawl.env["SSO_FRONTIER"], "links_file")
            self.assertTrue(crawl.env["SSO_LINKS_FILE"].endswith("documents.jsonl"))
            self.assertNotIn("ANTHROPIC_API_KEY", crawl.env)  # a crawl needs no engine and no key
            self.assertEqual(crawl.env["PYTHONPATH"], "src")
            self.assertTrue(str(job.out_dir).startswith(str(Path(d) / "outputs")))
            self.assertTrue(job.sentences and "link list" in job.sentences[0]["text"])

    def test_australia_and_malaysia_take_the_slower_pace_and_crypto_check(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            job = scrape.plan_scrape(app, {"economies": ["AU", "MY"], "scope": "relevant"})
            self.assertEqual(job.steps[1].env["REQUEST_DELAY_MS"], "10000")
            self.assertIn("cryptography", job.steps[0].argv[-1])
            self.assertIn("REGISTER_FRONTIER", job.steps[1].env)
            self.assertIn("LOM_FRONTIER", job.steps[1].env)

    def test_second_pass_needs_a_folder_under_the_runs_root(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            with self.assertRaises(ApiError):
                scrape.plan_scrape(app, {"economies": ["SG"], "mode": "same", "folder": str(settings_mod.REPO / "demo_data" / "mini_raw")})
            run = Path(d) / "outputs" / "scrape" / "SG_x"
            run.mkdir(parents=True)
            job = scrape.plan_scrape(app, {"economies": ["SG"], "mode": "same", "folder": str(run)})
            self.assertEqual(Path(job.steps[1].argv[job.steps[1].argv.index("--out") + 1]), run)

    def test_precheck_accepts_china_through_its_tools_refuses_unknown_codes_and_flags_dry_run(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            checks = scrape.precheck(app, {"economies": ["CN"], "dry_run": True})
            self.assertFalse(any(c["level"] == "fail" for c in checks), checks)
            self.assertTrue(any(c["check"] == "cn_tools" for c in checks))
            checks = scrape.precheck(app, {"economies": ["XX"], "dry_run": True})
            self.assertTrue(any(c["check"] == "economies" and c["level"] == "fail" for c in checks))
            checks = scrape.precheck(app, {"economies": ["SG"], "dry_run": True, "frontier": "links"})
            self.assertFalse(any(c["level"] == "fail" for c in checks), checks)
            self.assertTrue(any(c["check"] == "dry-run" for c in checks))


class Parser(unittest.TestCase):
    def test_lines(self):
        job = jobs.Job(stage="p1", title="t", steps=[])
        p = scrape.parse_p1
        out = p("[crawl] SG: 7 to fetch, 736 already retrieved [scope=all, forms=pdf, pillars=[6, 7]]", job)
        self.assertEqual(out[0], "SG: 7 to fetch, 736 already retrieved.")
        job.bump(**out[1])
        out = p("[crawl] OK SG Personal Data Protection Act 2012 -> pdf_native (200) -> sg-pdpa2012-001", job)
        self.assertEqual(out[0], "Fetched 1 of 7: Personal Data Protection Act 2012 (native PDF).")
        job.bump(**out[1])
        self.assertEqual(job.progress["done"], 1)
        out = p("[crawl] SG: 0 to fetch, 743 already retrieved [scope=seed, forms=both, pillars=[6, 7]]", job)
        self.assertIn("second pass, nothing new to fetch", out[0])
        self.assertEqual(p("[crawl] throttled (HTTP 467) on Some Act; cooldown 30s", job)[0], "The portal asked us to slow down (HTTP 467); waiting 30 s.")
        self.assertEqual(p("[crawl] manifest has 739 row(s); validate OK [contract 0.2.0]", job)[0], "Manifest written: 739 documents; schema check OK.")
        self.assertIn("tenacity", p("ModuleNotFoundError: No module named 'tenacity'", job)[0])
        self.assertIsNone(p("random noise", job))


if __name__ == "__main__":
    unittest.main()
