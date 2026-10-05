"""The Overview's cost report: one data block in the page feeds its tables and the calculator.

What must hold: the finale's figures are the ledger's, to the cent; every model the Mapping page offers has a
price and a pace here, under the same provider, with the same default per step; and a figure that was not
measured says so."""
import json
import re
import unittest

from . import INTERFACE
from rdtii_ui import settings as settings_mod

REPO = settings_mod.REPO
STEPS = ("screen", "read", "recheck", "tiebreak")


def _data() -> dict:
    page = (INTERFACE / "static" / "index.html").read_text(encoding="utf-8")
    block = re.search(r'<script type="application/json" id="cost-data">(.*?)</script>', page, re.S)
    assert block, "the page has no cost data block"
    return json.loads(block.group(1))


class Finale(unittest.TestCase):
    def setUp(self):
        self.data = _data()
        self.finale = self.data["finale"]
        self.ledger = json.loads((REPO / "submission" / "reports" / "cost_ledger.json").read_text(encoding="utf-8"))

    def test_the_whole_run_is_the_ledgers_total(self):
        total = self.finale["total"]
        self.assertEqual(total["total"], self.ledger["total_usd"])
        by_stage = self.ledger["by_stage_usd"]
        self.assertEqual(total["read"], by_stage["S4 mapping (Sonnet)"])
        self.assertEqual(total["screen"], by_stage["S3b triage (Haiku)"])
        self.assertEqual(total["verify"], by_stage["S5 blind verification (Haiku + Opus)"])
        self.assertAlmostEqual(total["translate"], by_stage["S9b gloss, provision text"] + by_stage["S9b gloss, quotes"], places=2)
        self.assertEqual(total["scores"], by_stage["S6 economy-level rollup"])
        self.assertEqual(self.finale["run"], self.ledger["run_id"])

    def test_each_economys_careful_reading_is_the_ledgers(self):
        by_economy = self.ledger["S4_detail"]["by_economy"]
        for e in self.finale["economies"]:
            self.assertEqual(e["usd"]["read"], by_economy[e["id"]], e["id"])
        self.assertEqual(self.finale["other"][0]["usd"]["read"], by_economy["TL (52-indicator arm)"])

    def test_the_rows_add_up(self):
        rows = self.finale["economies"] + self.finale["other"]
        for r in rows:                                   # a row is its steps, to a cent of rounding
            u = r["usd"]
            self.assertAlmostEqual(u["screen"] + u["read"] + u["verify"] + u["translate"] + u["scores"], u["total"], delta=0.011, msg=r["name"])
        for k in ("screen", "read", "verify"):           # a column is the whole run's
            self.assertAlmostEqual(sum(r["usd"][k] for r in rows), self.finale["total"][k], delta=0.011, msg=k)
        self.assertAlmostEqual(sum(r["usd"]["translate"] for r in rows), self.finale["total"]["translate"], delta=0.02)

    def test_the_six_economies_each_carry_what_the_calculator_reads(self):
        self.assertEqual([e["id"] for e in self.finale["economies"]], ["AU", "CN", "SG", "MY", "LA", "TL"])
        for e in self.finale["economies"]:
            for k in STEPS + ("translate",):
                self.assertGreaterEqual(e["calls"][k], 0, (e["id"], k))
            self.assertGreaterEqual(e["calls"]["recheck"], e["calls"]["tiebreak"])   # a tie-break follows a re-check
            for k in ("documents", "provisions", "scrape_sec", "extract_min"):
                self.assertGreater(e[k], 0, (e["id"], k))


class Models(unittest.TestCase):
    def setUp(self):
        self.data = _data()
        self.engines = json.loads((REPO / "stages" / "p3-map" / "config" / "llm" / "engines.json").read_text(encoding="utf-8"))["engines"]
        self.models = {m["id"]: m for m in self.data["models"]}

    def test_every_model_the_mapping_page_offers_is_priced_under_its_provider(self):
        declared = {m["id"]: eid for eid, e in self.engines.items() for m in e["models"]}
        self.assertEqual({mid: m["provider"] for mid, m in self.models.items()}, declared)

    def test_a_providers_defaults_and_pace_are_the_stages(self):
        role = {"screen": "verifier", "read": "mapper", "recheck": "verifier", "tiebreak": "escalation"}
        self.assertEqual([p["id"] for p in self.data["providers"]], list(self.engines))
        for p in self.data["providers"]:
            e = self.engines[p["id"]]
            self.assertEqual(p["name"], e["name"])
            self.assertEqual(p["workers"], e["workers"])
            self.assertEqual(p["roles"], {step: e["roles"][role[step]] for step in STEPS})

    def test_every_model_has_a_price_and_a_pace_for_each_step(self):
        for mid, m in self.models.items():
            self.assertEqual(set(m["usd"]), {"screen", "read", "recheck", "translate"}, mid)
            self.assertEqual(set(m["sec"]), {"screen", "read", "recheck"}, mid)
            self.assertTrue(all(v > 0 for v in m["sec"].values()), mid)
            free = all(p == 0 for p in next(x for e in self.engines.values() for x in e["models"] if x["id"] == mid)["price"])
            self.assertEqual(all(v == 0 for v in m["usd"].values()), free, mid)   # $0 only where the price card is $0
            for key in m["est"]:
                kind, _, step = key.partition(".")
                self.assertIn(step, m[kind], (mid, key))

    def test_a_figure_that_was_not_measured_says_so(self):
        # measured on 4 October (costs_by_model_and_task.csv) or billed in the finale; every other price is an estimate
        measured = {"screen": {"qwen2.5:14b", "gpt-6-luna", "deepseek-flash", "kimi-k2.6", "claude-haiku-4-5", "claude-sonnet-5-5", "claude-opus-5-5", "claude-opus-5", "claude-fable-5-1"},
                    "read": {"qwen2.5:14b", "deepseek-v4-pro", "gpt-6.1-sol", "kimi-k3", "claude-sonnet-5"},
                    "recheck": {"qwen2.5:14b", "gpt-6-luna", "deepseek-flash", "deepseek-v4-pro", "gpt-6.1-sol", "kimi-k2.6", "kimi-k3"},
                    "translate": {"qwen2.5:14b", "claude-haiku-4-5"}}
        for mid, m in self.models.items():
            for step, ids in measured.items():
                self.assertEqual(f"usd.{step}" not in m["est"], mid in ids, (mid, step))

    def test_the_finales_models_are_the_stages_measured_engine(self):
        picked = self.data["finale"]["models"]
        self.assertEqual({k: picked[k] for k in STEPS}, self.data["providers"][0]["roles"])
        self.assertEqual(self.data["finale"]["read_live"], 2)   # the batch lane is half price, so live is twice the bill


if __name__ == "__main__":
    unittest.main()
