"""The run layer's rules: the allowlist, the environment a stage gets, the Clear guard, and a real job."""
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

from . import INTERFACE  # noqa: F401
from rdtii_ui import envbuild, fsguard, jobs, settings as settings_mod
from rdtii_ui.server import ApiError


def _engines():
    return envbuild.EngineState(envbuild.load_engines(settings_mod.REPO / "stages" / "p3-map"))


class Allowlist(unittest.TestCase):
    def setUp(self):
        self.eng = _engines()
        self.key = envbuild.KeyHolder()

    def test_engines_come_from_the_stage_file(self):
        self.assertEqual(self.eng.ids(), ["A", "B"])
        self.assertEqual(self.eng.selected, "A")

    def test_unknown_name_and_unlisted_value_are_refused(self):
        with self.assertRaises(envbuild.ChoiceError):
            envbuild.validate_choices({"PATH": "x"}, self.eng)
        with self.assertRaises(envbuild.ChoiceError):
            envbuild.validate_choices({"RDTII_ENGINE": "Z"}, self.eng)
        with self.assertRaises(envbuild.ChoiceError):
            envbuild.validate_choices({"LLM_MODEL": "gpt-9"}, self.eng)
        with self.assertRaises(envbuild.ChoiceError):
            envbuild.validate_choices({"ANTHROPIC_API_KEY": "sk-x"}, self.eng)
        self.assertEqual(envbuild.validate_choices({"RDTII_ENGINE": "B"}, self.eng), {"RDTII_ENGINE": "B"})

    def test_engine_b_gets_no_key_and_one_worker(self):
        env, public = envbuild.build_env("p3", self.eng, self.key, {"RDTII_ENGINE": "B"}, {"OUT_DIR": "x"})
        self.assertEqual(env["RDTII_ENGINE"], "B")
        self.assertEqual(env["ANTHROPIC_API_KEY"], "")
        self.assertEqual(env["MAP_WORKERS"], "1")
        self.assertTrue(env["OLLAMA_HOST"].startswith("http"))
        self.assertEqual(public["OUT_DIR"], "x")
        self.assertNotIn("ANTHROPIC_API_KEY", public)

    def test_engine_a_needs_a_held_key_and_never_shows_it(self):
        with self.assertRaises(envbuild.NeedsKey):
            envbuild.build_env("p3", self.eng, self.key, {"RDTII_ENGINE": "A"})
        self.key.set("sk-test-0123456789")
        env, public = envbuild.build_env("p3", self.eng, self.key, {"RDTII_ENGINE": "A"})
        self.assertEqual(env["ANTHROPIC_API_KEY"], "sk-test-0123456789")
        self.assertEqual(public["ANTHROPIC_API_KEY"], "(held in memory)")
        self.assertEqual(env["MAP_WORKERS"], "12")
        self.assertEqual(self.key.redact("token sk-test-0123456789 here"), "token [key redacted] here")

    def test_p2_gets_pythonpath_and_utf8(self):
        env, _ = envbuild.build_env("p2", self.eng, self.key, {"RDTII_ENGINE": "B"})
        self.assertEqual(env["PYTHONPATH"], "src" + os.pathsep + ".")
        self.assertEqual(env["PYTHONUTF8"], "1")


class ClearGuard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name) / "outputs"
        (root / "extract" / "demo" / "ocr").mkdir(parents=True)
        (root / "extract" / "demo" / "ocr" / "page.txt").write_text("x")
        (root / "extract" / "demo" / "provisions.jsonl").write_text("{}\n")
        (root / "scrape" / "run1" / "raw").mkdir(parents=True)
        self.s = settings_mod.load({"RDTII_RUNS_ROOT": str(root)})
        self.root = root

    def tearDown(self):
        self.tmp.cleanup()

    def test_allowed_shapes(self):
        t = fsguard.check_clearable(self.s, str(self.root / "extract" / "demo" / "ocr"), [])
        self.assertEqual(t, (self.root / "extract" / "demo" / "ocr").resolve())
        fsguard.check_clearable(self.s, str(self.root / "extract" / "demo"), [])
        fsguard.check_clearable(self.s, str(self.root / "scrape" / "run1" / "raw"), [])

    def test_refused_shapes(self):
        for bad in (self.root, self.root / "extract", self.root / "extract" / "demo" / "provisions.jsonl",
                    settings_mod.REPO / "interface" / "fixtures", settings_mod.REPO / "stages"):
            with self.assertRaises(ApiError, msg=str(bad)):
                fsguard.check_clearable(self.s, str(bad), [])

    def test_busy_folder_is_refused_then_cleared_with_a_token(self):
        target = self.root / "extract" / "demo" / "ocr"
        with self.assertRaises(ApiError):
            fsguard.check_clearable(self.s, str(target), [self.root / "extract" / "demo"])
        t = fsguard.check_clearable(self.s, str(target), [])
        tok = fsguard.issue_token(t)
        self.assertEqual(fsguard.redeem_token(tok), t)
        with self.assertRaises(ApiError):
            fsguard.redeem_token(tok)  # single use
        fsguard.clear(t)
        self.assertFalse(target.exists())
        self.assertTrue((self.root / "extract" / "demo" / "provisions.jsonl").exists())


class RealJob(unittest.TestCase):
    def test_selftest_job_streams_sentences_and_finishes(self):
        mgr = jobs.JobManager()
        job = mgr.submit(jobs.selftest_job(sys.executable, lambda s: s))
        deadline = time.time() + 30
        while job.status in ("queued", "running") and time.time() < deadline:
            time.sleep(0.2)
        self.assertEqual(job.status, "done", job.public())
        texts = [s["text"] for s in job.sentences]
        self.assertIn("Tick 5 of 5.", texts)
        self.assertEqual(job.progress["done"], 5)
        self.assertEqual(job.rc, 0)

    def test_cancel_stops_a_running_job(self):
        mgr = jobs.JobManager()
        job = mgr.submit(jobs.selftest_job(sys.executable, lambda s: s))
        deadline = time.time() + 10
        while job.status != "running" and time.time() < deadline:
            time.sleep(0.1)
        time.sleep(1.2)
        self.assertTrue(mgr.cancel(job.id))
        deadline = time.time() + 15
        while job.status == "running" and time.time() < deadline:
            time.sleep(0.2)
        self.assertEqual(job.status, "cancelled")
        self.assertLess(job.progress["done"], 5)


if __name__ == "__main__":
    unittest.main()
