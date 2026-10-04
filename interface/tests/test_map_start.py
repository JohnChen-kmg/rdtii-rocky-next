"""The Mapping run plan: handoff description, the step list per option, the environment, and the parser."""
import tempfile
import unittest
from pathlib import Path

from . import INTERFACE  # noqa: F401
from rdtii_ui import jobs, settings as settings_mod
from rdtii_ui.pages import mapping
from rdtii_ui.server import App

REPO = settings_mod.REPO
DEMO = REPO / "outputs" / "extract" / "demo"


def _app(runs_root: str) -> App:
    app = App(settings_mod.load({"RDTII_RUNS_ROOT": runs_root, "HANDOFF2_DIR": str(DEMO),
                                 "INDEX_DIR": str(Path(runs_root) / "index" / "demo")}))
    app.jobs = jobs.JobManager()
    return app


@unittest.skipUnless((DEMO / "laws.jsonl").is_file(), "needs the demo extraction output (run Extraction on demo_data/mini_raw)")
class PickerTiers(unittest.TestCase):
    def test_every_in_scope_indicator_has_a_tier_and_the_three_practice_based_are_marked(self):
        from rdtii_ui.pages import mapping as mp
        pk = mp.indicator_picker(settings_mod.load({}))
        flat = [i for p in pk["pillars"] for i in p["indicators"]]
        self.assertEqual(len(flat), 61)
        self.assertEqual(pk["tier_counts"], {"A": 9, "B": 52, "C": 0})
        self.assertTrue(all(i["tier"] in ("A", "B", "C") for i in flat))
        self.assertEqual({i["id"] for i in flat if i["automated"]}, {i["id"] for i in flat if i["tier"] == "A"})
        self.assertEqual(sorted(i["id"] for i in flat if i["practice_based"]), ["3.4", "5.3", "9.1"])
        self.assertNotIn("manual_note", pk)
        self.assertEqual(len(pk["tier_ids"]["A"]), 9)
        self.assertEqual(sorted(pk["tier_text"]), ["A", "B", "C"])
        self.assertIn("Pillars 6-7", pk["tier_text"]["A"])
        self.assertEqual(sorted(pk["practice_based"]), ["3.4", "5.3", "9.1"])
        self.assertEqual(pk["selection"]["thetas"]["6.1"], 0.56)
        self.assertEqual(len(pk["selection"]["measured"]), 9)
        self.assertEqual(len(pk["selection"]["thetas"]), 61)          # the other 52 take their class default
        self.assertEqual(pk["selection"]["thetas"]["3.4"], 0.6)       # subject_specific
        self.assertEqual(pk["selection"]["caps"]["per_indicator"]["6.1"], 500)
        self.assertEqual(pk["selection"]["caps"]["per_indicator"]["7.1"], 150)
        self.assertEqual(len(pk["selection"]["caps"]["per_indicator"]), 9)
        self.assertEqual(pk["selection"]["caps"]["gray_mult"], 3)
        self.assertEqual(pk["selection"]["direct_band"], 0.65)
        self.assertEqual(pk["selection"]["language_offset"]["por"], -0.03)


@unittest.skipUnless((DEMO / "laws.jsonl").is_file(), "needs the demo extraction output (run Extraction on demo_data/mini_raw)")
class DemoHandoff(unittest.TestCase):
    def test_handoff_is_described_from_laws_and_status(self):
        s = settings_mod.load({"HANDOFF2_DIR": str(DEMO)})
        h = mapping.describe_handoff(s, DEMO, "test")
        self.assertTrue(h["complete"])
        self.assertEqual(set(h["economies"]), {"AU", "MY", "SG"})
        self.assertEqual(h["documents"], 5)
        self.assertGreater(h["provisions"], 3000)
        self.assertEqual(h["languages"]["SG"], "eng")

    def test_plan_with_stub_dense_and_cap(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            job = mapping.plan_map(app, {"handoff": str(DEMO), "economies": ["SG"], "indicators": ["6.1", "6.4"],
                                         "engine": "B", "select_mode": "caps", "dense": "stub", "limit": 5})
            labels = [st.label for st in job.steps]
            self.assertEqual(len(labels), 8, labels)  # no baseline workbook configured, so no baseline step
            self.assertIn("imports", labels[0])
            self.assertIn("corpus index", labels[1])
            self.assertIn("keyword index", labels[2])
            self.assertIn("stub", labels[3])
            self.assertIn("select", labels[4])
            self.assertIn("screen", labels[5])
            self.assertTrue(labels[6].startswith("SG:"))
            self.assertTrue(labels[7].startswith("SG:"))
            self.assertTrue(any("baseline" in x["text"] and "skipped" in x["text"] for x in job.sentences))
            env = job.steps[4].env
            self.assertEqual(env["ECONOMIES"], "SG")
            self.assertEqual(env["INDICATORS_SCOPE"], "6.1,6.4")
            self.assertEqual(env["RDTII_ENGINE"], "B")
            self.assertEqual(env["ANTHROPIC_API_KEY"], "")
            self.assertEqual(env["MAP_WORKERS"], "1")
            self.assertEqual(env["SELECT_MODE"], "caps")
            self.assertTrue(env["OUT_DIR"].endswith("out"))
            self.assertIn("_B", env["RUN_ID"])
            self.assertIn("--limit", job.steps[5].argv)
            self.assertEqual(job.steps[6].argv[-1], "5")
            self.assertIn("--gloss", job.steps[7].argv)
            self.assertNotIn("sk-", str(job.env_public))

    def test_engine_a_without_key_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            with self.assertRaises(Exception) as cm:
                mapping.plan_map(app, {"handoff": str(DEMO), "economies": ["SG"], "engine": "A", "dense": "stub"})
            self.assertIn("key", str(cm.exception).lower())

    def test_precheck_flags_non_english_with_stub(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            checks = mapping.precheck(app, {"handoff": str(DEMO), "economies": ["SG"], "indicators": ["6.1"],
                                            "engine": "B", "select_mode": "scores", "dense": "stub"})
            dense = next(c for c in checks if c["check"] == "dense")
            self.assertEqual(dense["level"], "fail")
            self.assertTrue(any(c["check"] == "baseline" and c["level"] == "warn" for c in checks))


@unittest.skipUnless((DEMO / "laws.jsonl").is_file(), "needs the demo extraction output (run Extraction on demo_data/mini_raw)")
class IndexFollowsTheOutput(unittest.TestCase):
    """The index is reused while it is as new as the extraction output, and rebuilt once the output is newer."""

    def _index_with_age(self, app, seconds_before_output: int) -> Path:
        h = mapping.describe_handoff(app.settings, DEMO, "test")
        idx = Path(h["index"]["dir"]); idx.mkdir(parents=True, exist_ok=True)
        for name in ("prefilter_corpus.jsonl", "bm25_top.npz", "dense_top.npz"):
            (idx / name).write_bytes(b"x")                      # dense under 4096 bytes reads as the stub
        import os
        t = (DEMO / "provisions.jsonl").stat().st_mtime - seconds_before_output
        for f in idx.iterdir():
            os.utime(f, (t, t))
        return idx

    def test_current_index_is_reused(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            self._index_with_age(app, -3600)                    # an hour newer than the output
            h = mapping.describe_handoff(app.settings, DEMO, "test")
            self.assertFalse(h["index"]["stale"])
            job = mapping.plan_map(app, {"handoff": str(DEMO), "economies": ["SG"], "indicators": ["6.1"],
                                         "engine": "B", "select_mode": "caps", "dense": "stub"})
            labels = [st.label for st in job.steps]
            self.assertFalse(any("corpus index" in x or "keyword index" in x for x in labels), labels)
            checks = mapping.precheck(app, {"handoff": str(DEMO), "economies": ["SG"], "indicators": ["6.1"],
                                            "engine": "B", "select_mode": "caps", "dense": "stub"})
            self.assertIn("as new as the extraction output", next(c for c in checks if c["check"] == "index")["text"])

    def test_older_index_is_rebuilt_without_a_tick(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            self._index_with_age(app, 3600)                     # an hour older than the output
            h = mapping.describe_handoff(app.settings, DEMO, "test")
            self.assertTrue(h["index"]["stale"])
            job = mapping.plan_map(app, {"handoff": str(DEMO), "economies": ["SG"], "indicators": ["6.1"],
                                         "engine": "B", "select_mode": "caps", "dense": "stub"})
            labels = [st.label for st in job.steps]
            self.assertIn("corpus index", labels[1]); self.assertIn("keyword index", labels[2])
            checks = mapping.precheck(app, {"handoff": str(DEMO), "economies": ["SG"], "indicators": ["6.1"],
                                            "engine": "B", "select_mode": "caps", "dense": "stub"})
            self.assertIn("newer than its index", next(c for c in checks if c["check"] == "index")["text"])

    def _ranked_for(self, app, ids) -> None:
        """A current index whose two legs hold rankings for these indicators (an .npz is a zip of arrays)."""
        import os
        import zipfile
        idx = self._index_with_age(app, -3600)
        for name in ("bm25_top.npz", "dense_top.npz"):
            with zipfile.ZipFile(idx / name, "w") as z:
                for i in ids:
                    z.writestr(f"{i}_idx.npy", b"0" * 3000)
                    z.writestr(f"{i}_score.npy", b"0" * 3000)
        t = (DEMO / "provisions.jsonl").stat().st_mtime + 3600
        for f in idx.iterdir():
            os.utime(f, (t, t))

    def test_an_index_ranked_for_other_indicators_is_ranked_again(self):
        """The demo index held 6.1 and 6.4 only; a run on nine indicators passed Check and stopped at selection."""
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            self._ranked_for(app, ["6.1", "P6-I4"])               # one key in the form used before the decimal IDs
            h = mapping.describe_handoff(app.settings, DEMO, "test")
            self.assertEqual(h["index"]["indicators"], {"bm25": ["6.1", "6.4"], "dense": ["6.1", "6.4"]})
            req = {"handoff": str(DEMO), "economies": ["SG"], "indicators": ["6.1", "6.2"],
                   "engine": "B", "select_mode": "caps", "dense": "stub"}
            self.assertEqual(mapping._norm_request(app, req)["index_lacks"], ["6.2"])
            labels = [st.label for st in mapping.plan_map(app, req).steps]
            self.assertFalse(any("corpus index" in x for x in labels), labels)        # the provisions read are reused
            self.assertTrue(any("rank the keyword index" in x for x in labels), labels)
            self.assertTrue(any("stub" in x for x in labels), labels)                 # the stub mirrors the new keys
            text = next(c for c in mapping.precheck(app, req) if c["check"] == "index")["text"]
            self.assertIn("was ranked for 6.1, 6.4", text)
            self.assertIn("ranked again", text)

            same = {**req, "indicators": ["6.4", "6.1"]}                             # what the index already holds
            self.assertEqual(mapping._norm_request(app, same)["index_lacks"], [])
            labels = [st.label for st in mapping.plan_map(app, same).steps]
            self.assertFalse(any("keyword index" in x or "meaning index" in x for x in labels), labels)
            self.assertIn("as new as the extraction output",
                          next(c for c in mapping.precheck(app, same) if c["check"] == "index")["text"])

    def test_an_index_that_cannot_be_read_is_left_to_the_dates(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            self._index_with_age(app, -3600)                      # the legs are one byte each: not archives
            h = mapping.describe_handoff(app.settings, DEMO, "test")
            self.assertEqual(h["index"]["indicators"], {"bm25": None, "dense": None})
            n = mapping._norm_request(app, {"handoff": str(DEMO), "economies": ["SG"], "indicators": ["6.1"],
                                             "engine": "B", "select_mode": "caps", "dense": "stub"})
            self.assertEqual(n["index_lacks"], [])

    def test_build_rebuilds_a_current_index_from_scratch(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            self._index_with_age(app, -3600)
            n = mapping._norm_request(app, {"handoff": str(DEMO), "economies": ["SG"], "engine": "B",
                                                "select_mode": "caps", "dense": "real"})
            self.assertTrue(n["rebuild"]); self.assertEqual(n["dense"], "real")


class Parser(unittest.TestCase):
    def setUp(self):
        self.job = jobs.Job(stage="p3", title="t", steps=[])

    def test_progress_lines(self):
        p = mapping.parse_p3
        j = self.job
        self.assertEqual(p("[select] mode caps · 3,643 corpus rows · economies SG · 2 indicators", j)[0],
                         "Selecting candidates for SG across 2 indicator(s), caps rule.")
        out = p("[haiku-triage] 40/120 (0.4/s, keep 33%, err 0, ETA 3 min, $0.0000)", j)
        self.assertIn("Screened 40 of 120", out[0])
        self.assertEqual(out[1]["done"], 40)
        out = p("[map:SG] 12/30 (0.1/s, fires 4, ungrounded 0, err 0, ETA 4 min, $0.12)", j)
        self.assertIn("SG: 12 of 30 provisions judged, 4 matches", out[0])
        self.assertEqual(j.progress["cost_usd"], 0.12)
        out = p('[verify:SG] done (cumulative): {"agree": 3, "overturned": 1, "cost_usd": 0.05}', j)
        self.assertEqual(out[0], "SG: blind re-check done, 3 agreed, 1 overturned.")
        self.assertEqual(j.progress["cost_usd"], 0.17)
        self.assertEqual(p("[submission:SG] 7 rows -> C:/x/records_SG.csv", j)[0], "SG: 7 evidence rows written in the host's 14 columns.")
        self.assertIn("nothing to translate", p("[gloss:SG] nothing to gloss (0 already done)", j)[0])
        self.assertIsNone(p("[bm25] 6.1: top-150000, nonzero=12, max=3.20", j))
        self.assertIn("API key", p("config.llm.factory.LLMConfigError: role 'mapper' ... ANTHROPIC_API_KEY is empty", j)[0])


if __name__ == "__main__":
    unittest.main()
