"""The Scraping Start plan: the crawler command, the link-list frontier, politeness, and the parser."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from . import INTERFACE  # noqa: F401
from rdtii_ui import jobs, probes, settings as settings_mod
from rdtii_ui.pages import scrape
from rdtii_ui.server import App, ApiError

STARTS = {"ok": True, "text": "The crawler's browser starts (Playwright 1.63.0, Chromium 153).", "hint": ""}
_browser = mock.patch.object(probes, "probe_browser_launch", return_value=STARTS)


def setUpModule():
    """Whether this machine's crawler can start a browser is not what these tests are about."""
    _browser.start()


def tearDownModule():
    _browser.stop()


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


def _fingerprints(s, wrong=()):
    """The registry fingerprints as the stage would report them: each economy's own list's, except `wrong`."""
    return {c: ("0" * 64 if c in wrong else scrape.link_list(s, c)["cfg_sha256"]) for c in ("SG", "AU", "MY", "TL", "LA")}


class LinkList(unittest.TestCase):
    """Whether the crawler will take the link list is said by Check, before Start, not by a skipped run after it."""

    def test_check_says_when_the_crawler_would_refuse_the_list(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            s = app.settings
            req = {"economies": ["SG", "AU"], "scope": "all", "frontier": "links"}
            with mock.patch.object(scrape, "registry_fingerprints", return_value=_fingerprints(s)):
                checks = scrape.precheck(app, req)
                self.assertFalse([c for c in checks if c["level"] == "fail"], checks)
                self.assertIn("built for the registry the crawler reads", next(c["text"] for c in checks if c["check"] == "frontier"))
            with mock.patch.object(scrape, "registry_fingerprints", return_value=_fingerprints(s, wrong=("AU",))):
                fails = [c for c in scrape.precheck(app, req) if c["level"] == "fail"]
                self.assertEqual([c["check"] for c in fails], ["frontier"])
                self.assertIn("AU: the shipped link list of 2026-09-19 was built for a different registry", fails[0]["text"])
                self.assertIn("Refresh from the portal", fails[0]["text"])
                # the same request with a refresh does not depend on the list: it builds its own
                self.assertFalse([c for c in scrape.precheck(app, {**req, "frontier": "discover"}) if c["level"] == "fail"])
            with mock.patch.object(scrape, "registry_fingerprints", return_value={}):      # the stage's Python could not say
                levels = [c["level"] for c in scrape.precheck(app, req) if c["check"] == "frontier"]
                self.assertEqual(levels, ["warn", "warn"])

    def test_the_cost_of_a_crawl_is_read_from_the_lists_own_record(self):
        s = settings_mod.load({})
        meta = scrape.catalogue_meta(s, "SG")
        e = scrape.estimate(s, "SG", "all", "discover")
        self.assertEqual((e["documents"], e["listing_requests"], e["delay_s"]), (meta["counts"]["all"], meta["requests"], 6.0))
        # how long the listings take is what the last build's own log measured, first request to last
        self.assertEqual(e["listing_seconds"], scrape.link_list(s, "SG")["build_seconds"])
        self.assertGreater(e["listing_seconds"], 60 * 60)             # Singapore: over an hour, not "up to 20 minutes"
        text = scrape.estimate_text("SG", e)
        self.assertIn(f"about {meta['requests']} requests", text)
        self.assertIn("the last time they were read", text)
        replay = scrape.estimate(s, "SG", "all", "links")
        self.assertEqual(replay["listing_requests"], 0)
        self.assertNotIn("listings", scrape.estimate_text("SG", replay))
        self.assertEqual(scrape.estimate(s, "AU", "all", "links", limit=5)["documents"], 5)
        self.assertIn("at most", scrape.estimate_text("AU", scrape.estimate(s, "AU", "all", "links"), second_pass=True))
        self.assertEqual([scrape._span(x) for x in (20, 60 * 54, 60 * 98, 3600 * 3.5, 60 * 119)],
                         ["about 1 min", "about 54 min", "about 1 h 45 min", "about 3 h 30 min", "about 2 h"])

    def test_check_states_how_long_the_listings_really_take(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            checks = scrape.precheck(app, {"economies": ["SG", "TL"], "scope": "relevant", "frontier": "discover"})
            self.assertFalse([c for c in checks if c["level"] == "fail"], checks)
            times = {c["text"][:2]: c["text"] for c in checks if c["check"] == "time"}
            self.assertIn("about 68 min the last time they were read", times["SG"])
            self.assertIn("about 7 requests", times["TL"])


class Refresh(unittest.TestCase):
    """'Refresh from the portal': the stage's catalogue tool reads the listings into a link list kept under the
    runs root, and the crawl replays that list."""

    def _built(self, s, code: str, stamp: str, fingerprint: str | None = None, documents: int = 4) -> Path:
        """A link list as the catalogue tool leaves it, cut from the shipped one."""
        shipped = scrape.shipped_links_dir(s, code)
        dest = s.runs_root / "scrape" / code / {"AU": "legislation-gov-au", "TL": "mj-gov-tl"}[code] / f"links_{stamp}"
        dest.mkdir(parents=True)
        rows = (shipped / "documents.jsonl").read_text(encoding="utf-8").splitlines()[:documents]
        (dest / "documents.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")
        meta = json.loads((shipped / "catalogue_meta.json").read_text(encoding="utf-8"))
        meta.update(generated_at="2026-10-04T04:21:54Z", counts={"all": documents, "seed": 1, "relevant": 2})
        if fingerprint:
            meta["cfg_sha256"] = fingerprint
        (dest / "catalogue_meta.json").write_text(json.dumps(meta), encoding="utf-8")
        return dest

    def test_the_listings_are_read_into_a_list_of_the_runs_own_then_replayed(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            job = scrape.plan_scrape(app, {"economies": ["AU"], "scope": "all", "frontier": "discover"})
            self.assertEqual(len(job.steps), 3)
            build, crawl = job.steps[1], job.steps[2]
            self.assertEqual(build.argv[1:3], ["-m", "p1_scrape.adapters.au_legislation.catalogue"])
            new_list = Path(build.argv[build.argv.index("--out") + 1])
            self.assertEqual(new_list.relative_to(Path(d) / "outputs" / "scrape").parts[:2], ("AU", "legislation-gov-au"))
            self.assertTrue(new_list.name.startswith("links_"))
            self.assertEqual(build.env["REQUEST_DELAY_MS"], "3000")           # the register's API asks for no delay
            self.assertEqual(crawl.env["REQUEST_DELAY_MS"], "10000")          # its document host asks for ten seconds
            self.assertEqual((crawl.env["REGISTER_FRONTIER"], Path(crawl.env["REGISTER_LINKS_FILE"])),
                             ("links_file", new_list / "documents.jsonl"))
            self.assertTrue(any("a link list refreshed from the portal" in x["text"] for x in job.sentences))
            self.assertEqual(scrape.plan_scrape(app, {"economies": ["SG"], "frontier": "discover"}).steps[1].env["REQUEST_DELAY_MS"], "6000")

    def test_a_listing_that_could_not_be_read_stops_the_run_before_any_fetch(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            job = scrape.plan_scrape(app, {"economies": ["TL"], "scope": "relevant", "frontier": "discover"})
            job.steps[1].on_done(job, 2)                 # the tool's exit when the portal could not be read
            self.assertIn("no new link list and nothing was fetched", job.progress["_fail"])
            job2 = scrape.plan_scrape(app, {"economies": ["TL"], "scope": "relevant", "frontier": "discover"})
            job2.steps[1].on_done(job2, 0)               # exit 0 with no file is a failure too
            self.assertIn("_fail", job2.progress)

    def test_a_quick_run_cuts_its_small_list_from_the_new_one(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            s = app.settings
            job = scrape.plan_scrape(app, {"economies": ["TL"], "scope": "all", "frontier": "discover", "limit": 2})
            build, crawl = job.steps[1], job.steps[2]
            self.assertEqual(Path(crawl.env["JORNAL_LINKS_FILE"]), job.out_dir / "links_used" / "documents.jsonl")
            self.assertEqual(crawl.env.get("MAX_CANDIDATES_PER_ECONOMY"), None)      # scope all: the small list is the cap
            new_list = Path(build.argv[build.argv.index("--out") + 1])
            self._built(s, "TL", new_list.name[len("links_"):], documents=5)         # the tool has run
            build.on_done(job, 0)
            self.assertNotIn("_fail", job.progress)
            rows = (job.out_dir / "links_used" / "documents.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(rows), 2)
            self.assertTrue(any("the new link list is in" in x["text"] for x in job.sentences))
            self.assertFalse([c for c in scrape.precheck(app, {"economies": ["TL"], "scope": "all", "frontier": "discover", "limit": 2})
                              if c["level"] == "fail"])
            for bad in ("abc", -1, 501):
                with self.assertRaises(ApiError, msg=str(bad)):
                    scrape.plan_scrape(app, {"economies": ["TL"], "limit": bad})
            self.assertIsNone(scrape._norm(app, {"economies": ["TL"], "limit": ""})["limit"])

    def test_the_newest_list_that_fits_the_registry_is_the_one_in_use(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            s = app.settings
            shipped = scrape.shipped_links_dir(s, "AU")
            own = json.loads((shipped / "catalogue_meta.json").read_text(encoding="utf-8"))["cfg_sha256"]
            with mock.patch.object(scrape, "registry_fingerprints", return_value={"AU": own}):
                self.assertEqual(scrape.links_dir(s, "AU"), shipped)                  # nothing refreshed yet
                older = self._built(s, "AU", "20261004-002154")
                newer = self._built(s, "AU", "20261005-090000")
                self.assertEqual(scrape.refreshed_links(s, "AU"), [newer, older])
                self.assertEqual(scrape.links_dir(s, "AU"), newer)
                self.assertEqual(scrape.link_list(s, "AU")["origin"], "refreshed")
                self.assertEqual(scrape.catalogue_meta(s, "AU")["counts"]["all"], 4)    # the page's counts follow the list in use
                self.assertIn("the link list refreshed here on 2026-10-04", scrape.link_state(s, "AU")["text"])
                job = scrape.plan_scrape(app, {"economies": ["AU"], "scope": "all", "frontier": "links"})
                self.assertEqual(Path(job.steps[1].env["REGISTER_LINKS_FILE"]), newer / "documents.jsonl")
                stale = self._built(s, "AU", "20261006-090000", fingerprint="0" * 64)   # built for another registry
                self.assertEqual(scrape.links_dir(s, "AU"), newer)                      # passed over, as the crawler would refuse it
                self.assertNotIn(stale, [scrape.links_dir(s, "AU")])
            self.assertEqual(scrape.links_dir(s, "TL"), scrape.shipped_links_dir(s, "TL"))

    def test_a_link_list_folder_is_shown_as_one_and_is_no_crawl_folder(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            s = app.settings
            built = self._built(s, "AU", "20261004-002154")
            row = next(f for f in scrape.list_crawl_folders(s) if f["name"] == built.name)
            self.assertEqual((row["kind"], row["rows"], row["economy"], row["source"]), ("link list", 4, "AU", "legislation-gov-au"))
            self.assertEqual(scrape.economy_runs(s, "AU"), [])                         # never offered for a second pass
            from rdtii_ui.pages import extract
            self.assertNotIn(built.name, [i["name"] for i in extract.list_inputs(s)])    # nor as an Extraction input

    def test_what_the_catalogue_tool_prints_is_said_in_plain_words(self):
        job = jobs.Job(stage="p1", title="t", steps=[])
        p = scrape.parse_p1
        self.assertEqual(p("[catalogue] AU: identified as 'Mozilla/5.0 x (+contact: a@b.c)', 3 s between requests", job)[0],
                         "AU: reading the portal's listings, one request every 3 s.")
        self.assertEqual(p("[catalogue] AU: {'all': 1275, 'seed': 21, 'relevant': 23} documents; kinds {'principal_act': 1262}; 121 API", job)[0],
                         "AU: the list is complete, 1275 documents on the portal, 23 of them in Sample.")
        self.assertEqual(p("[catalogue] TL: 4793 act(s) listed -> 1939 document(s); {'all': 1939, 'seed': 9, 'relevant': 198}; kinds {}", job)[0],
                         "TL: the list is complete, 1939 documents on the portal, 198 of them in Sample.")
        said = p("[catalogue] LA: nothing written (ConnectionError: ('Connection aborted.', ConnectionResetError(10054, 'x', None, 10054, None)))", job)[0]
        self.assertIn("LA: no link list was written: the portal closed or dropped the connection", said)
        poll = scrape._listing_poll(68 * 60, every=120, clock=iter([0, 60, 121, 130, 300]).__next__)
        self.assertEqual([bool(poll(job)) for _ in range(4)], [False, False, True, False])
        self.assertIn("5 min so far; the last time took about 68 min", poll(job))


class QuickRun(unittest.TestCase):
    def test_the_first_documents_are_replayed_from_a_small_list_of_their_own(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            s = app.settings
            job = scrape.plan_scrape(app, {"economies": ["AU"], "scope": "all", "frontier": "links", "limit": 3})
            small = Path(job.steps[1].env["REGISTER_LINKS_FILE"])
            self.assertEqual(small, job.out_dir / "links_used" / "documents.jsonl")
            rows = [json.loads(x) for x in small.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 3)
            self.assertTrue(all("all" in r["scopes"] for r in rows))
            self.assertEqual([r["order"] for r in rows], sorted(r["order"] for r in rows))
            # the list's record of the registry it was built for travels with it, or the crawler would refuse it
            kept = json.loads((small.parent / "catalogue_meta.json").read_text(encoding="utf-8"))
            self.assertEqual(kept["cfg_sha256"], scrape.link_list(s, "AU")["cfg_sha256"])
            self.assertTrue(job.title.startswith("Quick run: AU"))
            self.assertIn("first 3 documents", job.steps[1].label)
            self.assertTrue(any("3 documents at 10 s" in x["text"] for x in job.sentences))
            full = scrape.plan_scrape(app, {"economies": ["AU"], "scope": "all", "frontier": "links"})
            self.assertEqual(Path(full.steps[1].env["REGISTER_LINKS_FILE"]), scrape.links_file(s, "AU"))


class SecondPass(unittest.TestCase):
    def _runs(self, root: Path) -> dict:
        made = {}
        for code, key, stamp in (("SG", "sso-agc-gov-sg", "20261003-225540"), ("SG", "sso-agc-gov-sg", "20261004-000048"),
                                 ("AU", "legislation-gov-au", "20261004-000116")):
            p = root / "outputs" / "scrape" / code / key / stamp
            p.mkdir(parents=True)
            made[f"{code}/{stamp}"] = p
        (root / "outputs" / "scrape" / "SG" / "sso-agc-gov-sg" / "hand_all_20261004-010101").mkdir()
        return made

    def test_each_economy_goes_over_a_folder_of_its_own(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            made = self._runs(Path(d))
            s = app.settings
            self.assertEqual(scrape.economy_runs(s, "SG"), [made["SG/20261004-000048"], made["SG/20261003-225540"]])   # newest first, no hand_ manifest
            self.assertEqual(scrape.economy_runs(s, "AU"), [made["AU/20261004-000116"]])
            # the request that went wrong on 4 October: Australia sent over a Singapore folder
            with self.assertRaises(ApiError) as cm:
                scrape.plan_scrape(app, {"economies": ["AU"], "mode": "same", "folder": str(made["SG/20261003-225540"])})
            self.assertIn("is not a crawl folder of AU", str(cm.exception))
            checks = scrape.precheck(app, {"economies": ["AU"], "mode": "same", "folders": {"AU": str(made["SG/20261003-225540"])}})
            self.assertEqual([c["check"] for c in checks if c["level"] == "fail"], ["request"])
            jobs_ = scrape.plan_jobs(app, {"economies": ["SG", "AU"], "mode": "same", "scope": "all",
                                           "folders": {"SG": str(made["SG/20261003-225540"])}})
            self.assertEqual([j.out_dir for j in jobs_], [made["SG/20261003-225540"], made["AU/20261004-000116"]])   # AU: its newest
            for job, code in zip(jobs_, ("SG", "AU")):
                argv = job.steps[1].argv
                self.assertEqual(argv[argv.index("--economy") + 1], code)
            with self.assertRaises(ApiError) as cm:
                scrape.plan_jobs(app, {"economies": ["MY"], "mode": "same"})
            self.assertIn("No crawl folder for MY yet", str(cm.exception))

    def test_a_new_crawl_of_several_economies_is_one_run_each(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            jobs_ = scrape.plan_jobs(app, {"economies": ["SG", "AU"], "scope": "relevant", "dry_run": True})
            rel = [j.out_dir.relative_to(Path(d) / "outputs" / "scrape").parts[:2] for j in jobs_]
            self.assertEqual(rel, [("SG", "sso-agc-gov-sg"), ("AU", "legislation-gov-au")])
            self.assertEqual([j.steps[1].env["REQUEST_DELAY_MS"] for j in jobs_], ["6000", "10000"])   # each at its own portal's pace


class Narration(unittest.TestCase):
    def test_the_silent_listing_phase_is_told_by_the_clock(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            now = [1000.0]
            job = jobs.Job(stage="p1", title="t", steps=[])
            poll = scrape._poll_status(out, listing_seconds=54 * 60, every=120, clock=lambda: now[0])
            self.assertIsNone(poll(job))
            now[0] += 119
            self.assertIsNone(poll(job))
            now[0] += 2
            said = poll(job)
            self.assertIn("Reading the portal's listings: 2 min so far", said)
            self.assertIn("about 54 min", said)
            self.assertIsNone(poll(job))                        # not again until the next two minutes
            job.bump(total=40)                                  # the list is complete: the crawl speaks for itself now
            now[0] += 500
            self.assertIsNone(poll(job))

    def test_a_status_file_left_by_an_earlier_pass_is_not_reported(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            status = out / "crawl_status.json"
            status.write_text(json.dumps({"attempted": 9, "stored_total": 9, "state": "done", "todo": 9}), encoding="utf-8")
            old = status.stat().st_mtime
            job = jobs.Job(stage="p1", title="t", steps=[])
            poll = scrape._poll_status(out, clock=lambda: old + 600)
            self.assertIsNone(poll(job))
            self.assertIsNone(job.progress.get("total"))
            os.utime(status, (old + 700, old + 700))            # written again, in this run
            self.assertEqual(poll(job), "9 attempted, 9 stored (done).")

    def test_the_status_file_never_takes_the_count_back(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            job = jobs.Job(stage="p1", title="t", steps=[])
            job.bump(total=2, done=1)                       # "Fetched 1 of 2" has been printed
            poll = scrape._poll_status(out)
            (out / "crawl_status.json").write_text(json.dumps({"attempted": 0, "stored_total": 0, "state": "crawling", "todo": 2}), encoding="utf-8")
            self.assertIsNone(poll(job))                    # the file is behind the lines
            self.assertEqual(job.progress["done"], 1)

    def test_a_refused_list_and_the_start_are_said_plainly(self):
        job = jobs.Job(stage="p1", title="t", steps=[])
        line = ("[crawl] SKIP AU: ValueError: link file C:\\x\\documents.jsonl was built from a different registry: "
                "rebuild it with au_legislation.catalogue")
        text, updates = scrape.parse_p1(line, job)
        self.assertIn("AU skipped: its link list was built for a different registry", text)
        self.assertIn("Refresh from the portal", text)
        self.assertEqual(updates, {"+skipped_economies": 1})
        self.assertEqual(scrape.parse_p1("[health] built-in tracker on: heartbeat + x", job)[0], "The crawler has started.")
        text, _ = scrape.parse_p1("[crawl] SKIP LA: ConnectionError: ('Connection aborted.', ConnectionResetError(10054))", job)
        self.assertIn("LA skipped: the portal closed or dropped the connection", text)
        self.assertIn("start it again", text)

    def test_the_two_adapters_that_report_their_listing_progress_are_heard(self):
        job = jobs.Job(stage="p1", title="t", steps=[])
        self.assertEqual(scrape.parse_p1("[catalogue] MY: 50 timeline(s) read; 106 request(s) so far", job)[0],
                         "MY: reading the portal's listings, 106 requests so far.")
        self.assertEqual(scrape.parse_p1("[catalogue] LA: Decree (legaltype=3): 258 law(s) in 27 page(s)", job)[0],
                         "LA: listing read, Decree: 258 laws in 27 pages.")


class Browser(unittest.TestCase):
    """A Chromium folder on disk says nothing once the Playwright package has moved to another build; on
    4 October every page fetched through the browser failed as HTTP 0 while the check read "installed"."""

    def test_what_the_launch_test_prints_is_read(self):
        ok = probes.read_launch("\n".join(["noise", "BROWSER ok 1.63.0 153.0.8010.12", ""]), "py")
        self.assertEqual((ok["ok"], ok["text"]), (True, "The crawler's browser starts (Playwright 1.63.0, Chromium 153.0.8010.12)."))
        stale = probes.read_launch("BROWSER fail 1.63.0 BrowserType.launch: Executable doesn't exist at C:/x/chromium_headless_shell-1243/chrome.exe", "C:/py/python.exe")
        self.assertFalse(stale["ok"])
        self.assertIn("needs a Chromium build that is not installed", stale["text"])
        self.assertEqual(stale["hint"], '"C:/py/python.exe" -m playwright install chromium')
        none = probes.read_launch("BROWSER no-package ModuleNotFoundError", "py")
        self.assertIn("has no Playwright package", none["text"])
        self.assertFalse(probes.read_launch("", "py")["ok"])

    def test_the_answer_is_kept_until_the_builds_on_disk_change(self):
        calls = []

        class Done:
            stdout = "BROWSER ok 1.63.0 153.0"

        def run(argv, **kw):
            calls.append(argv[0])
            return Done()
        _browser.stop()
        try:
            builds = mock.patch.object(probes, "_browser_builds", return_value=("chromium-1243",))
            with builds, mock.patch.dict(probes._launch_cache, {}, clear=True):
                self.assertTrue(probes.probe_browser_launch("py-a", run=run)["ok"])
                self.assertTrue(probes.probe_browser_launch("py-a", run=run)["ok"])
                self.assertEqual(calls, ["py-a"])                               # asked once
                self.assertTrue(probes.probe_chromium("py-a")["tested"])        # the header's dot shows the tested answer
                self.assertFalse(probes.probe_chromium("py-b")["tested"])
                with mock.patch.object(probes, "_browser_builds", return_value=("chromium-1243", "chromium-1300")):
                    probes.probe_browser_launch("py-a", run=run)
                self.assertEqual(calls, ["py-a", "py-a"])                       # a new build on disk: asked again
            with mock.patch.object(probes, "_browser_builds", return_value=()):
                self.assertFalse(probes.probe_chromium("py-a")["ok"])           # no build at all
        finally:
            _browser.start()

    def test_a_crawl_without_its_browser_fails_check_and_a_dry_run_is_warned(self):
        broken = {"ok": False, "text": "The crawler's browser cannot start: Playwright 1.63.0 needs a Chromium build that is not installed.",
                  "hint": '"python" -m playwright install chromium'}
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            with mock.patch.object(probes, "probe_browser_launch", return_value=broken):
                checks = scrape.precheck(app, {"economies": ["AU"], "scope": "relevant"})
                fail = next(c for c in checks if c["check"] == "browser")
                self.assertEqual(fail["level"], "fail")
                self.assertIn("would fail as HTTP 0", fail["text"])
                self.assertIn("-m playwright install chromium", fail["text"])
                dry = next(c for c in scrape.precheck(app, {"economies": ["AU"], "scope": "relevant", "dry_run": True}) if c["check"] == "browser")
                self.assertEqual(dry["level"], "warn")
        job = jobs.Job(stage="p1", title="t", steps=[])
        said = scrape.parse_p1("[crawl] XX AU Cyber Security Rules 2025 -> https://www.legislation.gov.au/F2025L00278/latest/text (HTTP 0)", job)[0]
        self.assertIn("no answer: the portal did not reply or the browser could not open the page", said)
        self.assertEqual(scrape.parse_p1("[crawl] XX SG Some Act -> https://x/y (HTTP 404)", job)[0], "Could not fetch Some Act (HTTP 404).")


class Depth(unittest.TestCase):
    def test_a_run_folder_too_deep_for_windows_fails_the_check(self):
        s = settings_mod.load({})
        self.assertEqual(scrape.stored_below(s), len("raw/xx/") + 80 + 1 + len("20261004T0419Z_99__scanned.pdf.headers.json"))
        shallow, deep = Path("C:/runs/scrape/AU/legislation-gov-au/20261004-000000"), Path("C:/" + "x" * 180)
        self.assertGreater(scrape.path_room(s, shallow, os_name="nt", long_paths=False), 0)
        self.assertLess(scrape.path_room(s, deep, os_name="nt", long_paths=False), 0)
        self.assertIsNone(scrape.path_room(s, deep, os_name="nt", long_paths=True))
        self.assertIsNone(scrape.path_room(s, deep, os_name="posix"))
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            with mock.patch.object(scrape, "path_room", return_value=-12):
                fails = [c for c in scrape.precheck(app, {"economies": ["AU"], "scope": "all"}) if c["level"] == "fail"]
            self.assertEqual([c["check"] for c in fails], ["path"])
            self.assertIn("12 too many", fails[0]["text"])
            self.assertIn("RDTII_RUNS_ROOT", fails[0]["text"])


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
