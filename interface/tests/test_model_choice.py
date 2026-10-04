"""A model per step of a mapping run, a key per provider, and a selection number per indicator.

What must hold: a run that changes nothing receives exactly what it always did; a step given another
provider needs that provider's own key and nobody else's; and a typed threshold goes into a copy of the thresholds,
never the stage's measured file."""
import json
import tempfile
import unittest
from pathlib import Path

from . import INTERFACE  # noqa: F401
from rdtii_ui import core, envbuild, jobs, settings as settings_mod
from rdtii_ui.pages import mapping
from rdtii_ui.server import ApiError, App

REPO = settings_mod.REPO
DEMO = REPO / "outputs" / "extract" / "demo"
NEEDS_DEMO = unittest.skipUnless((DEMO / "laws.jsonl").is_file(), "needs the demo extraction output (run Extraction on demo_data/mini_raw)")
KEY_A, KEY_C = "sk-claude-0123456789", "sk-deepseek-0123456789"


def _engines():
    return envbuild.EngineState(envbuild.load_engines(REPO / "stages" / "p3-map"))


def _app(runs_root: str) -> App:
    app = App(settings_mod.load({"RDTII_RUNS_ROOT": runs_root, "HANDOFF2_DIR": str(DEMO),
                                 "INDEX_DIR": str(Path(runs_root) / "index" / "demo")}))
    app.jobs = jobs.JobManager()
    return app


def _call(app: App, method: str, path: str, q=None, b=None):
    for verb, rx, fn in app.routes:
        m = rx.fullmatch(path)
        if verb == method and m:
            return fn(app, m, q or {}, b)
    raise AssertionError(f"no route {method} {path}")


class Declared(unittest.TestCase):
    def test_the_measured_two_come_first_and_the_rest_say_they_are_not_measured(self):
        eng = _engines()
        self.assertEqual(eng.ids()[:2], ["A", "B"])
        public = {e["id"]: e for e in eng.public()["engines"]}
        self.assertEqual([i for i, e in public.items() if e["measured"]], ["A", "B"])
        self.assertEqual({public[i]["name"] for i in ("C", "D", "E")}, {"DeepSeek", "Kimi", "ChatGPT"})
        self.assertEqual(eng.key_names(), ["ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY", "OPENAI_API_KEY"])
        claude = {m["id"]: m for m in public["A"]["models"]}
        self.assertEqual([i for i, m in claude.items() if m["measured"]], ["claude-sonnet-5", "claude-haiku-4-5", "claude-opus-4-8"])
        self.assertTrue(all(len(m["price"]) == 4 for e in public.values() for m in e["models"]))

    def test_a_local_engine_also_offers_what_its_server_holds(self):
        eng = _engines()
        self.assertEqual([m["id"] for m in eng.models_of("B")], ["qwen2.5:14b"])
        more = eng.models_of("B", ["qwen2.5:14b", "llama3.1:8b"])
        self.assertEqual([m["id"] for m in more], ["qwen2.5:14b", "llama3.1:8b"])
        self.assertFalse(more[1]["measured"])
        self.assertNotIn("llama3.1:8b", [m["id"] for m in eng.models_of("A", ["llama3.1:8b"])])


class Keys(unittest.TestCase):
    def test_each_provider_has_its_own_key(self):
        k = envbuild.KeyHolder()
        k.set(KEY_A)
        k.set(KEY_C, "DEEPSEEK_API_KEY")
        self.assertEqual((k.get(), k.get("DEEPSEEK_API_KEY"), k.get("OPENAI_API_KEY")), (KEY_A, KEY_C, ""))
        self.assertTrue(k.held() and k.held("DEEPSEEK_API_KEY"))
        self.assertFalse(k.held("OPENAI_API_KEY"))
        self.assertEqual(sorted(k.public()["names"]), ["ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY"])
        self.assertNotIn("sk-", json.dumps(k.public()))
        self.assertEqual(k.redact(f"a {KEY_A} b {KEY_C} c"), "a [key redacted] b [key redacted] c")
        k.clear("DEEPSEEK_API_KEY")
        self.assertTrue(k.held())
        self.assertFalse(k.held("DEEPSEEK_API_KEY"))
        k.clear()
        self.assertFalse(k.public()["held"])
        with self.assertRaises(ValueError):
            k.set(KEY_A, "not a name")

    def test_the_routes_take_a_name_and_refuse_one_no_engine_reads(self):
        app = App(settings_mod.load({}))
        core.register(app)
        self.assertTrue(_call(app, "POST", "/api/key", b={"key": KEY_A})[1]["held"])       # no name: the Claude key
        out = _call(app, "POST", "/api/key", b={"key": KEY_C, "name": "DEEPSEEK_API_KEY"})[1]
        self.assertEqual(sorted(out["names"]), ["ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY"])
        with self.assertRaises(ApiError) as cm:
            _call(app, "POST", "/api/key", b={"key": KEY_C, "name": "PATH"})
        self.assertIn("not a key a declared engine reads", str(cm.exception))
        out = _call(app, "DELETE", "/api/key", q={"name": "DEEPSEEK_API_KEY"})[1]
        self.assertEqual(sorted(out["names"]), ["ANTHROPIC_API_KEY"])
        self.assertEqual(_call(app, "DELETE", "/api/key")[1]["names"], {})                  # no name: every key


class RoleEnvironment(unittest.TestCase):
    def setUp(self):
        self.eng = _engines()
        self.key = envbuild.KeyHolder()
        self.key.set(KEY_A)

    def test_a_run_that_changes_nothing_receives_no_role_variable(self):
        plain, _ = envbuild.build_env("p3", self.eng, self.key, {"RDTII_ENGINE": "A"})
        same = {"mapper": {"engine": "A", "model": "claude-sonnet-5"}, "verifier": {"engine": "A", "model": "claude-haiku-4-5"},
                "escalation": {"engine": "A", "model": "claude-opus-4-8"}}
        env, public = envbuild.build_env("p3", self.eng, self.key, {"RDTII_ENGINE": "A"}, roles=same)
        self.assertEqual(env, plain)
        for name in list(envbuild.ROLE_ENGINE.values()) + list(envbuild.ROLE_MODEL.values()):
            self.assertNotIn(name, env)
        self.assertEqual((env["MAP_WORKERS"], env["VERIFY_WORKERS"], env["TRIAGE_WORKERS"]), ("12", "12", "12"))
        self.assertEqual((env["ANTHROPIC_API_KEY"], env["DEEPSEEK_API_KEY"], env["OPENAI_API_KEY"]), (KEY_A, "", ""))

    def test_another_claude_model_is_one_variable(self):
        env, public = envbuild.build_env("p3", self.eng, self.key, {"RDTII_ENGINE": "A"},
                                         roles={"mapper": {"engine": "A", "model": "claude-opus-5-5"}})
        self.assertEqual(env["LLM_MODEL"], "claude-opus-5-5")
        self.assertEqual(public["LLM_MODEL"], "claude-opus-5-5")
        self.assertNotIn("RDTII_ENGINE_MAPPER", env)
        self.assertNotIn("VERIFIER_MODEL", env)

    def test_a_step_on_another_provider_needs_that_providers_key(self):
        roles = {"verifier": {"engine": "C", "model": "deepseek-v4-pro"}}
        with self.assertRaises(envbuild.NeedsKey) as cm:
            envbuild.build_env("p3", self.eng, self.key, {"RDTII_ENGINE": "A"}, roles=roles)
        self.assertIn("DEEPSEEK_API_KEY", str(cm.exception))
        self.key.set(KEY_C, "DEEPSEEK_API_KEY")
        env, public = envbuild.build_env("p3", self.eng, self.key, {"RDTII_ENGINE": "A"}, roles=roles)
        self.assertEqual((env["RDTII_ENGINE"], env["RDTII_ENGINE_VERIFIER"], env["VERIFIER_MODEL"]), ("A", "C", "deepseek-v4-pro"))
        self.assertEqual((env["ANTHROPIC_API_KEY"], env["DEEPSEEK_API_KEY"], env["MOONSHOT_API_KEY"]), (KEY_A, KEY_C, ""))
        self.assertEqual((env["MAP_WORKERS"], env["VERIFY_WORKERS"]), ("12", "8"))      # each role's own engine
        self.assertEqual(public["DEEPSEEK_API_KEY"], "(held in memory)")
        self.assertNotIn("sk-", json.dumps(public))

    def test_a_key_no_step_uses_is_not_asked_for_and_not_passed(self):
        self.key.set(KEY_C, "DEEPSEEK_API_KEY")
        env, _ = envbuild.build_env("p3", self.eng, self.key, {"RDTII_ENGINE": "B"})
        self.assertEqual((env["ANTHROPIC_API_KEY"], env["DEEPSEEK_API_KEY"]), ("", ""))

    def test_a_model_of_another_provider_and_an_unknown_role_are_refused(self):
        for roles in ({"mapper": {"engine": "A", "model": "deepseek-flash"}}, {"mapper": {"engine": "Z"}},
                      {"triage": {"engine": "A"}}, {"mapper": {"engine": "B", "model": "llama3.1:8b"}}):
            with self.assertRaises(envbuild.ChoiceError):
                envbuild.build_env("p3", self.eng, self.key, {"RDTII_ENGINE": "A"}, roles=roles)
        env, _ = envbuild.build_env("p3", self.eng, self.key, {"RDTII_ENGINE": "A"}, ollama_models=["llama3.1:8b"],
                                    roles={"mapper": {"engine": "B", "model": "llama3.1:8b"}})   # pulled on the local server
        self.assertEqual((env["RDTII_ENGINE_MAPPER"], env["LLM_MODEL"], env["MAP_WORKERS"]), ("B", "llama3.1:8b", "1"))

    def test_the_page_may_name_a_role_engine_and_a_declared_model_only(self):
        ok = envbuild.validate_choices({"RDTII_ENGINE_MAPPER": "C", "LLM_MODEL": "claude-opus-5-5"}, self.eng)
        self.assertEqual(ok, {"RDTII_ENGINE_MAPPER": "C", "LLM_MODEL": "claude-opus-5-5"})
        with self.assertRaises(envbuild.ChoiceError):
            envbuild.validate_choices({"RDTII_ENGINE_VERIFIER": "Z"}, self.eng)
        with self.assertRaises(envbuild.ChoiceError):
            envbuild.validate_choices({"DEEPSEEK_API_KEY": KEY_C}, self.eng)


@NEEDS_DEMO
class Plan(unittest.TestCase):
    BASE = {"handoff": str(DEMO), "economies": ["SG"], "indicators": ["6.1", "3.4"], "dense": "stub", "select_mode": "caps"}

    def test_the_default_plan_is_the_plan_it_always_was(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            job = mapping.plan_map(app, {**self.BASE, "indicators": ["6.1"], "engine": "B"})
            env = job.steps[-1].env
            for name in ("SELECTION_CONFIG", "CAPS_OVERRIDE", "LLM_MODEL", "VERIFIER_MODEL", "RDTII_ENGINE_VERIFIER"):
                self.assertNotIn(name, env)
            self.assertTrue(all(st.env is env for st in job.steps), "one environment for every step")
            self.assertFalse((Path(d) / "outputs" / "map").exists(), "nothing is written before Start")

    def test_each_step_gets_its_model_and_the_quick_screen_its_own_environment(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            app.key.set(KEY_C, "DEEPSEEK_API_KEY")
            models = {"screen": {"engine": "C", "model": "deepseek-flash"}, "mapper": {"engine": "B"},
                      "verifier": {"engine": "C", "model": "deepseek-v4-pro"}, "escalation": {"engine": "B"}}
            job = mapping.plan_map(app, {**self.BASE, "indicators": ["6.1"], "models": models})
            screen = next(st for st in job.steps if "screen" in st.label)
            chain = job.steps[-1]
            self.assertEqual((chain.env["RDTII_ENGINE"], chain.env["RDTII_ENGINE_VERIFIER"], chain.env["VERIFIER_MODEL"]), ("B", "C", "deepseek-v4-pro"))
            self.assertEqual((screen.env["RDTII_ENGINE_VERIFIER"], screen.env["VERIFIER_MODEL"]), ("C", "deepseek-flash"))
            self.assertEqual(chain.env["DEEPSEEK_API_KEY"], KEY_C)
            self.assertEqual(chain.env["ANTHROPIC_API_KEY"], "")
            self.assertIn("_B", chain.env["RUN_ID"])                      # the careful reading's engine names the run
            said = " ".join(x["text"] for x in job.sentences)
            self.assertIn("quick screen deepseek-flash (engine C)", said)
            self.assertIn("re-check deepseek-v4-pro (engine C)", said)
            self.assertNotIn(KEY_C, json.dumps(job.public()))

    def test_a_step_on_a_provider_without_its_key_is_refused_before_start(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            req = {**self.BASE, "indicators": ["6.1"], "engine": "B", "models": {"verifier": {"engine": "E"}}}
            checks = mapping.precheck(app, req)
            fail = next(c for c in checks if c["check"] == "engine" and c["level"] == "fail")
            self.assertIn("Engine E (ChatGPT (hosted))", fail["text"])
            self.assertIn("re-check (GPT-6 Luna)", fail["text"])
            self.assertIn("quick screen (GPT-6 Luna)", fail["text"])       # the screen follows the re-check unless set
            warn = next(c for c in checks if c["check"] == "measured")
            self.assertEqual(warn["level"], "warn")
            self.assertIn("ChatGPT GPT-6 Luna", warn["text"])
            with self.assertRaises(ApiError) as cm:
                mapping.plan_map(app, req)
            self.assertIn("OPENAI_API_KEY", str(cm.exception))

    def test_the_measured_choice_carries_no_warning(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            app.key.set(KEY_A)
            checks = mapping.precheck(app, {**self.BASE, "indicators": ["6.1"], "engine": "A"})
            self.assertFalse([c for c in checks if c["check"] in ("measured", "cost")])
            engine = next(c for c in checks if c["check"] == "engine")
            self.assertEqual(engine["level"], "ok")
            self.assertIn("careful reading (Sonnet 5)", engine["text"])
            checks = mapping.precheck(app, {**self.BASE, "indicators": ["6.1"], "models": {"mapper": {"engine": "A", "model": "claude-sonnet-5-5"}}})
            self.assertIn("Claude Sonnet 5.5", next(c for c in checks if c["check"] == "measured")["text"])

    def test_a_typed_threshold_goes_into_a_copy_and_never_into_the_stages_file(self):
        stage_file = REPO / "stages" / "p3-map" / "config" / "selection.json"
        before = stage_file.read_bytes()
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            req = {**self.BASE, "indicators": ["6.1", "3.4", "7.3"], "engine": "B", "select_mode": "scores", "dense": "real",
                   "thetas": {"6.1": 0.53, "3.4": "0.57", "7.3": 0.53}}          # 7.3 is typed at its recommended number
            job = mapping.plan_map(app, req)
            env = job.steps[-1].env
            own = Path(env["SELECTION_CONFIG"])
            self.assertEqual(own, Path(d) / "outputs" / "map" / own.parent.name / "selection.json")
            cfg, orig = json.loads(own.read_text(encoding="utf-8")), json.loads(before)
            self.assertEqual(cfg["indicators"]["6.1"]["theta"], 0.53)                 # recommended 0.56, measured
            self.assertEqual(cfg["indicators"]["3.4"]["theta"], 0.57)                 # recommended 0.60, its class default
            self.assertNotIn("theta", orig["indicators"]["3.4"])
            self.assertEqual(cfg["indicators"]["7.3"], orig["indicators"]["7.3"])     # the recommended number is not a change
            self.assertEqual(cfg["indicators"]["6.2"], orig["indicators"]["6.2"])     # not ticked, not touched
            self.assertEqual(cfg["class_defaults"], orig["class_defaults"])
            self.assertEqual(cfg["language_offset"], orig["language_offset"])
            self.assertIn("typed2", cfg["version"])
            self.assertIn("Thresholds typed for this run: 6.1 0.53, 3.4 0.57", " ".join(x["text"] for x in job.sentences))
            warn = next(c for c in mapping.precheck(app, req) if c["check"] == "selection")
            self.assertEqual(warn["level"], "warn")
            self.assertIn("6.1 0.53 (recommended 0.56)", warn["text"])
            self.assertIn("3.4 0.57 (recommended 0.60)", warn["text"])
            self.assertNotIn("7.3", warn["text"])
            self.assertNotIn("CAPS_OVERRIDE", env)
        self.assertEqual(stage_file.read_bytes(), before)

    def test_only_recommended_numbers_is_the_plan_it_always_was(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            job = mapping.plan_map(app, {**self.BASE, "indicators": ["6.1", "7.3"], "engine": "B", "select_mode": "scores", "dense": "real",
                                         "thetas": {"6.1": 0.56, "7.3": 0.53}, "caps": {}})
            self.assertNotIn("SELECTION_CONFIG", job.steps[-1].env)
            self.assertFalse((Path(d) / "outputs" / "map").exists())
            ok = next(c for c in mapping.precheck(app, {**self.BASE, "indicators": ["6.1"], "engine": "B", "caps": {"6.1": 500}}) if c["check"] == "selection")
            self.assertEqual(ok["level"], "ok")                                       # Round 1's own cap, typed

    def test_a_typed_cap_is_passed_per_indicator_and_can_cap_one_round_one_never_did(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            req = {**self.BASE, "indicators": ["6.1", "7.1", "3.4"], "engine": "B"}
            fail = next(c for c in mapping.precheck(app, req) if c["check"] == "selection")
            self.assertEqual(fail["level"], "fail")                                  # 3.4 has no Round 1 cap
            self.assertIn("3.4", fail["text"])
            self.assertIn("Type a cap", fail["text"])
            req = {**req, "caps": {"6.1": 400, "3.4": 250}, "thetas": {"6.1": 0.5}}
            warn = next(c for c in mapping.precheck(app, req) if c["check"] == "selection")
            self.assertEqual(warn["level"], "warn")
            self.assertIn("6.1 400 (Round 1: 500)", warn["text"])
            self.assertIn("3.4 250 (Round 1 has none)", warn["text"])
            env = mapping.plan_map(app, req).steps[-1].env
            self.assertEqual(env["CAPS_OVERRIDE"], "6.1=400,3.4=250")
            self.assertNotIn("SELECTION_CONFIG", env)                                # a threshold belongs to the other rule

    def test_a_number_out_of_range_or_for_an_unticked_indicator_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            app = _app(str(Path(d) / "outputs"))
            base = {**self.BASE, "indicators": ["6.1"], "engine": "B"}
            for bad in ({"thetas": {"6.1": 1.2}}, {"thetas": {"6.1": 0}}, {"thetas": {"6.1": "low"}}, {"thetas": {"7.3": 0.5}},
                        {"thetas": [0.5]}, {"caps": {"6.1": 0}}, {"caps": {"6.1": 99999}}, {"caps": {"6.1": 2.5}}, {"caps": {"6.1": True}}):
                with self.assertRaises(ApiError, msg=str(bad)):
                    mapping.plan_map(app, {**base, **bad})

    def test_the_page_is_told_the_range_of_a_number(self):
        sel = mapping.indicator_picker(settings_mod.load({}))["selection"]
        self.assertEqual((sel["theta_range"], sel["cap_range"]), ([0.05, 0.95], [1, 5000]))


if __name__ == "__main__":
    unittest.main()
