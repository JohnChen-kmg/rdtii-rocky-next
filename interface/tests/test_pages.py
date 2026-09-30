"""The Scraping and Extraction set-up lists, read from the stages' own files."""
import unittest

from . import INTERFACE  # noqa: F401
from rdtii_ui import settings as settings_mod
from rdtii_ui.pages import extract, scrape


class Scraping(unittest.TestCase):
    def setUp(self):
        self.s = settings_mod.load({})

    def test_registry_and_codes_come_from_the_stage(self):
        reg = scrape.registry(self.s)
        self.assertEqual(set(reg), {"SG", "MY", "AU", "TL", "LA"})
        self.assertEqual(reg["SG"], "sg_sso")
        self.assertEqual(scrape.valid_codes(self.s), ["SG", "AU", "MY", "TL", "LA"])

    def test_china_is_listed_but_not_crawlable(self):
        econs = {e["code"]: e for e in scrape.list_economies(self.s)}
        self.assertTrue(econs["SG"]["crawlable"])
        self.assertFalse(econs["CN"]["crawlable"])
        self.assertIn("by hand", econs["CN"]["note"])
        self.assertEqual(econs["CN"]["watchlist_rows"], 33)
        self.assertEqual(econs["SG"]["delay_ms"], 6000)
        self.assertEqual(econs["AU"]["delay_ms"], 10000)

    def test_singapore_sources_portals_seeds_watchlist(self):
        d = scrape.describe_sources(self.s, "SG")
        self.assertGreaterEqual(len(d["portals"]), 4)
        self.assertTrue(any("sso.agc.gov.sg" in p["root"] for p in d["portals"]))
        self.assertEqual(d["counts"]["seed"], 203)
        self.assertEqual(d["seeds_total"], 203)
        self.assertEqual(len(d["watchlist"]), 7)
        self.assertIn("what_to_look_for", d["watchlist"][0])

    def test_singapore_holdings_come_from_the_shipped_corpus(self):
        d = scrape.describe_sources(self.s, "SG")
        h = d["holdings"]
        self.assertEqual(h["rows"], 738)
        self.assertEqual(h["sub"], "(9.30 Finale Submission)")
        self.assertTrue(h["facts"][0][1].startswith("738 documents in the shipped corpus SG_corpus_2026-09-16"))
        self.assertIn("not in the repository", h["facts"][0][1])
        self.assertNotIn("Bytes", dict(h["facts"]))
        nf = dict(h["facts"])["Not fetched"]
        self.assertTrue(nf.startswith("330 of 1068 listed laws: 297 repealed"), nf)
        self.assertIn("10 not yet in force", nf)
        au = dict(scrape.describe_sources(self.s, "AU")["holdings"]["facts"])["Not fetched"]
        self.assertIn("3501 amending acts folded", au)
        docs = scrape.holdings_documents(self.s, "SG")
        self.assertEqual(docs["total"], 738)
        self.assertTrue(docs["documents"][0]["law_name"])

    def test_singapore_document_list_by_scope(self):
        d = scrape.list_documents(self.s, "SG", "all")
        self.assertEqual(d["total"], 1041)
        self.assertEqual(d["counts"], {"all": 1041, "relevant": 204, "seed": 203})
        self.assertEqual(scrape.list_documents(self.s, "SG", "seed")["total"], 203)
        self.assertEqual(scrape.list_documents(self.s, "SG", "relevant")["total"], 204)
        first = d["documents"][0]
        self.assertTrue(first["law_name"] and first["url"].startswith("http"))

    def test_malaysia_portals_include_agency_list(self):
        d = scrape.describe_sources(self.s, "MY")
        kinds = {p["kind"] for p in d["portals"]}
        self.assertIn("agency_portals", kinds)
        self.assertIn("gazette", kinds)

    def test_malaysia_crawls_laws_of_malaysia_only(self):
        """The registry marks its gazette group 'not read by the scraper' and the Federal Gazette host is dead;
        the crawler reads lom.agc.gov.my from the adapter block. The card must say so, once."""
        d = scrape.describe_sources(self.s, "MY")
        crawled = [p for p in d["portals"] if p["crawled"]]
        self.assertEqual([p["root"] for p in crawled], ["https://lom.agc.gov.my"])
        self.assertEqual(crawled[0]["kind"], "primary_statutes")
        fed = next(p for p in d["portals"] if "federalgazette" in p["root"])
        self.assertFalse(fed["crawled"])
        self.assertEqual(fed["note"], "not read by the scraper")
        self.assertTrue(any("federalgazette" in w["url"] for w in d["watchlist"]))

    def test_singapore_still_crawls_sso_once(self):
        d = scrape.describe_sources(self.s, "SG")
        crawled = [p for p in d["portals"] if p["crawled"]]
        self.assertEqual(len(crawled), 1)
        self.assertIn("sso.agc.gov.sg", crawled[0]["root"])
        self.assertEqual(crawled[0]["kind"], "primary_statutes")

    def test_crawl_folders_include_the_demo_corpus(self):
        folders = {f["id"]: f for f in scrape.list_crawl_folders(self.s)}
        demo = folders["demo_data/mini_raw"]
        self.assertEqual(demo["rows"], 5)
        self.assertEqual(demo["raw_present"], 4)
        self.assertEqual(demo["by_source_type"], {"html": 2, "pdf_scanned": 1, "pdf_native": 2})


class Extraction(unittest.TestCase):
    def setUp(self):
        self.s = settings_mod.load({})

    def test_inputs_start_with_handoff1_and_mark_shipped_manifests(self):
        inputs = extract.list_inputs(self.s)
        self.assertEqual(inputs[0]["id"], "demo_data/mini_raw")
        self.assertEqual(inputs[0]["kind"], "crawled")
        shipped = [i for i in inputs if i["origin"] == "shipped manifest"]
        self.assertTrue(shipped)
        self.assertTrue(all(i["documents_present"] is False for i in shipped))

    def test_hand_collected_folder_is_described_without_a_manifest(self):
        d = extract.describe_input(settings_mod.REPO / "demo_data", "typed")
        self.assertEqual(d["kind"], "hand_collected")
        self.assertGreaterEqual(d["rows"], 1)
        self.assertIn("pdf", d["by_source_type"])

    def test_doc_id_rule(self):
        self.assertTrue(extract.valid_doc_id("sg-pdpa2012-001"))
        self.assertFalse(extract.valid_doc_id("SG-pdpa-1"))


if __name__ == "__main__":
    unittest.main()
