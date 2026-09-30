"""Singapore's update check (countries/sg-singapore/updates/): offline tests on pages saved from sso.agc.gov.sg on
2026-09-15 and 2026-09-16 (tests/README.md lists them). No test sends a request."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from p1_scrape.adapters.sg_sso import updates as U
from p1_scrape.adapters.sg_sso.parse import parse_detail, parse_listing, parse_sl_tab
from p1_scrape.adapters.sg_sso.updates import baseline as B
from p1_scrape.adapters.sg_sso.updates import query as Q

_HERE = Path(__file__).parent
FIX = _HERE / "fixtures" / "sg" if (_HERE / "fixtures" / "sg").is_dir() else _HERE / "fixtures"

LAW_COLUMNS = ["listing", "portal_id", "law_number", "title", "legal_status", "version_as_at", "published_on",
               "repeal_date", "detail_read", "versions_listed", "amendments_listed", "last_amending_instrument",
               "revised_edition", "subsidiary_listed", "document_url", "in_seed", "in_relevant", "in_all",
               "document_kinds", "not_crawled_reason"]


def _page(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def pages():
    return {
        "current": parse_listing(_page("sso_browse_act_current_asc_2026-09-15.html"), "current"),
        "repealed": parse_listing(_page("sso_browse_act_repealed_2026-09-15.html"), "repealed"),
        "acts_supp": parse_listing(_page("sso_browse_acts_supp_2026_2026-09-15.html"), "acts_supp"),
        "PDPA2012": parse_detail(_page("sso_act_PDPA2012_2026-09-15.html"), "PDPA2012"),
        "OCHA2023": parse_detail(_page("sso_act_OCHA2023_2026-09-16.html"), "OCHA2023"),
        "PDPA2012_sl": parse_sl_tab(_page("sso_act_PDPA2012_sl_2026-09-15.html")),
    }


def _baseline(tmp_path: Path, laws: list[dict], links: list[dict] | None = None,
              generated_at: str = "2026-09-15T12:58:17Z") -> B.Baseline:
    run = tmp_path / "SG_ws_2026-09-15"
    (run / "links_used").mkdir(parents=True)
    with (run / "links_used" / "laws.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=LAW_COLUMNS, lineterminator="\n")
        w.writeheader()
        for r in laws:
            w.writerow({k: r.get(k, "") for k in LAW_COLUMNS})
    (run / "links_used" / "documents.jsonl").write_text("".join(json.dumps(r) + "\n" for r in (links or [])),
                                                        encoding="utf-8")
    (run / "links_used" / "catalogue_meta.json").write_text(json.dumps({"generated_at": generated_at}), encoding="utf-8")
    (run / "manifest.jsonl").write_text("", encoding="utf-8")
    return B.load(outputs_dir=tmp_path)


def _current(code: str, version: str) -> dict:
    return {"listing": "current", "portal_id": code, "title": code, "legal_status": "in_force", "version_as_at": version}


def _every_current_act(pages, **overrides) -> list[dict]:
    """A baseline that holds every act on the saved Current page, so only the rule under test decides."""
    return [_current(r.code, overrides.get(r.code, "2000-01-01")) for r in pages["current"]]


# --- the baseline -----------------------------------------------------------------------------------------------

def test_the_baseline_reads_every_acts_version_date_and_the_day_its_list_was_built(tmp_path, pages):
    b = _baseline(tmp_path, [_current("PDPA2012", "2022-10-01"), {"listing": "repealed", "portal_id": "AA1963"}])
    assert b.run.name == "SG_ws_2026-09-15"
    assert b.since == "2026-09-15"
    assert b.version_of("PDPA2012") == "2022-10-01"
    assert b.current == {"PDPA2012"} and b.listing_of("AA1963") == "repealed"


# --- which timelines are read ---------------------------------------------------------------------------------

def test_an_act_whose_file_is_older_than_the_date_is_not_read_and_the_cap_puts_seeds_first(tmp_path, pages):
    b = _baseline(tmp_path, _every_current_act(pages))
    rows = pages["current"]
    since = "2026-09-01"
    fresh = sorted(r.code for r in rows if r.file_stamp and r.file_stamp >= since)
    to_read, over = U.timeline_candidates(rows, b, since, seeds=set(), relevant=set(), cap=0)
    assert sorted(to_read) == fresh and over == []
    assert "PDPA2012" not in to_read                   # its file dates from 2025-12-29: it cannot have a new version
    # a seed goes to the front of the queue, and the cap reports the rest rather than dropping them
    seed = fresh[-1]
    to_read, over = U.timeline_candidates(rows, b, since, seeds={seed}, relevant=set(), cap=3)
    assert to_read[0] == seed and len(to_read) == 3 and len(over) == len(fresh) - 3


# --- amendments come from the timeline ------------------------------------------------------------------------

def test_an_amendment_is_decided_by_the_timelines_in_force_date(tmp_path, pages):
    listed = {"current": pages["current"]}
    b = _baseline(tmp_path, _every_current_act(pages, PDPA2012="2022-10-01"))
    changes = U.compare(listed, {"PDPA2012": pages["PDPA2012"]}, {}, b, since="2025-12-01")
    pdpa = next(c for c in changes.changes if c.portal_id == "PDPA2012")
    assert (pdpa.change, pdpa.in_force_from, pdpa.previous_version, pdpa.amended_by) == \
        ("amended", "2025-12-05", "2022-10-01", "Act 19 of 2025")
    assert pdpa.portal_id in [c.portal_id for c in changes.to_fetch]

    # the same act, already recorded at its newest version: its file was only regenerated
    b = _baseline(tmp_path / "again", _every_current_act(pages, PDPA2012="2025-12-05"))
    changes = U.compare(listed, {"PDPA2012": pages["PDPA2012"]}, {}, b, since="2025-12-01")
    assert next(c for c in changes.changes if c.portal_id == "PDPA2012").change == "regenerated"


def test_a_publication_date_long_before_the_date_does_not_hide_an_amendment(tmp_path, pages):
    """The Online Criminal Harms Act's version of 15 September 2026 comes from Act 10 of 2025, published in March
    2025. A check that compared publication dates with its date would call it unchanged."""
    b = _baseline(tmp_path, _every_current_act(pages, OCHA2023="2026-08-17"))
    changes = U.compare({"current": pages["current"]}, {"OCHA2023": pages["OCHA2023"]}, {}, b, since="2026-09-10")
    ocha = next(c for c in changes.changes if c.portal_id == "OCHA2023")
    assert ocha.published_on == "2025-03-05" and ocha.in_force_from == "2026-09-15"
    assert ocha.change.startswith("amended")


def test_a_new_version_the_portal_has_no_file_for_yet_is_reported_and_not_fetched(tmp_path, pages):
    b = _baseline(tmp_path, _every_current_act(pages, OCHA2023="2026-08-17"))
    changes = U.compare({"current": pages["current"]}, {"OCHA2023": pages["OCHA2023"]}, {}, b, since="2026-09-10")
    ocha = next(c for c in changes.changes if c.portal_id == "OCHA2023")
    assert ocha.change == "amended_file_pending" and ocha.has_file is False
    assert "OCHA2023" not in [c.portal_id for c in changes.to_fetch]
    assert "next check" in ocha.note


def test_with_no_baseline_an_act_is_amended_when_its_in_force_date_falls_on_or_after_the_date(pages):
    changes = U.compare({"current": pages["current"]}, {"PDPA2012": pages["PDPA2012"]}, {}, None, since="2025-12-01")
    assert next(c for c in changes.changes if c.portal_id == "PDPA2012").change == "amended"
    changes = U.compare({"current": pages["current"]}, {"PDPA2012": pages["PDPA2012"]}, {}, None, since="2026-01-01")
    assert next(c for c in changes.changes if c.portal_id == "PDPA2012").change == "regenerated"


# --- new acts, publications, repeals, regulations -------------------------------------------------------------

def test_an_act_the_baseline_did_not_hold_is_new_and_one_it_held_as_uncommenced_has_commenced(tmp_path, pages):
    laws = [r for r in _every_current_act(pages) if r["portal_id"] not in ("PDPA2012", "OCHA2023")]
    laws.append({"listing": "uncommenced", "portal_id": "OCHA2023", "title": "Online Criminal Harms Act 2023"})
    b = _baseline(tmp_path, laws)
    changes = U.compare({"current": pages["current"]}, {}, {}, b, since="2026-09-15")
    new = {c.portal_id: c for c in changes.changes if c.change == "new_act"}
    assert set(new) == {"PDPA2012", "OCHA2023"}
    assert new["PDPA2012"].note is None and "commenced" in new["OCHA2023"].note
    assert {c.portal_id for c in changes.to_fetch} >= {"PDPA2012", "OCHA2023"}


def test_a_repeal_on_or_after_the_date_is_reported_and_never_fetched(tmp_path, pages):
    b = _baseline(tmp_path, _every_current_act(pages))
    changes = U.compare({"current": pages["current"], "repealed": pages["repealed"]}, {}, {}, b, since="2026-07-01")
    repealed = {c.portal_id: c for c in changes.changes if c.change == "repealed"}
    assert {"HAA1988", "SSAA2016", "WSAA2003"} <= set(repealed)
    assert all(r.repeal_date >= "2026-07-01" for r in repealed.values())
    assert not set(repealed) & {c.portal_id for c in changes.to_fetch}
    changes = U.compare({"current": pages["current"], "repealed": pages["repealed"]}, {}, {}, b, since="2026-07-02")
    assert not [c for c in changes.changes if c.change == "repealed"]


def test_an_act_the_baseline_held_as_current_that_is_now_repealed_is_reported_whatever_the_date(tmp_path, pages):
    old = next(r for r in pages["repealed"] if r.repeal_date and r.repeal_date < "2000-01-01")
    b = _baseline(tmp_path, _every_current_act(pages) + [_current(old.code, "1990-01-01")])
    changes = U.compare({"current": pages["current"], "repealed": pages["repealed"]}, {}, {}, b, since="2026-09-15")
    gone = next(c for c in changes.changes if c.portal_id == old.code)
    assert gone.change == "repealed" and "held it as current" in gone.note


def test_an_acts_supplement_entry_on_or_after_the_date_is_fetched_and_an_earlier_one_is_not(tmp_path, pages):
    b = _baseline(tmp_path, _every_current_act(pages))
    listed = {"current": pages["current"], "acts_supp": pages["acts_supp"]}
    changes = U.compare(listed, {}, {}, b, since="2026-06-13")
    pubs = {c.portal_id for c in changes.changes if c.change == "new_publication"}
    assert pubs == {"14-2026", "18-2026"}
    # an entry a run's list already carried is not new again
    b.laws["18-2026"] = {"listing": "acts_supp", "portal_id": "18-2026"}
    changes = U.compare(listed, {}, {}, b, since="2026-06-13")
    assert {c.portal_id for c in changes.changes if c.change == "new_publication"} == {"14-2026"}


def test_a_regulation_new_to_a_seed_acts_tab_is_fetched_and_one_whose_date_moved_is_amended(tmp_path, pages):
    sl = pages["PDPA2012_sl"]
    known = [{"url": f"https://sso.agc.gov.sg/SL/{s.code}", "contract_meta": {
        "document_kind": "subsidiary_legislation", "portal_id": s.code, "version_as_at": s.doc_date}}
        for s in sl if s.code != "PDPA2012-S65-2021"]
    known[0]["contract_meta"]["version_as_at"] = "2000-01-01"          # recorded at an older date
    b = _baseline(tmp_path, _every_current_act(pages), links=known)
    changes = U.compare({"current": pages["current"]}, {}, {"PDPA2012": sl}, b, since="2024-01-01")
    by_code = {c.portal_id: c for c in changes.changes if c.listing == "regulation"}
    assert by_code["PDPA2012-S65-2021"].change == "new_regulation" and by_code["PDPA2012-S65-2021"].parent == "PDPA2012"
    assert by_code[known[0]["contract_meta"]["portal_id"]].change == "amended"


# --- what a check writes --------------------------------------------------------------------------------------

def test_the_checks_law_list_keeps_every_act_it_did_not_re_read_at_the_baselines_version(tmp_path, pages):
    """So a check's own run folder is a complete baseline for the next one."""
    class Adapter:
        listed = {"current": pages["current"][:3]}
        details = {pages["current"][0].code: pages["PDPA2012"]}
        subsidiary, subsidiary_totals = {}, {}

    first, second, third = (r.code for r in pages["current"][:3])
    b = _baseline(tmp_path, [_current(first, "1999-01-01"), _current(second, "2021-05-05"),
                             {"listing": "current", "portal_id": "GONE2001", "title": "An act no listing carries"}])
    rows = {r["portal_id"]: r for r in U.carried_forward(Adapter(), b, documents=[])}
    assert rows[first]["version_as_at"] == "2025-12-05"         # re-read: the fresh date
    assert rows[second]["version_as_at"] == "2021-05-05"        # not re-read: the baseline's date
    assert rows[third]["version_as_at"] in (None, "")          # never known, not invented
    assert "not on any listing" in rows["GONE2001"]["not_crawled_reason"]


def test_changes_are_written_as_json_and_markdown(tmp_path, pages):
    b = _baseline(tmp_path, _every_current_act(pages, PDPA2012="2022-10-01"))
    changes = U.compare({"current": pages["current"], "repealed": pages["repealed"]},
                        {"PDPA2012": pages["PDPA2012"]}, {}, b, since="2026-07-01", checked_at="2026-09-16T00:00:00Z",
                        not_checked=["AA2004"], requests=9)
    paths = U.write_changes(tmp_path / "out", changes, {"baseline_run": "SG_ws_2026-09-15"})
    payload = json.loads(Path(paths["changes.json"]).read_text(encoding="utf-8"))
    assert payload["economy"] == "SG" and payload["requests"] == 9
    assert payload["counts"]["not_checked"] == 1 and payload["counts"]["repealed"] >= 3
    md = Path(paths["changes.md"]).read_text(encoding="utf-8")
    assert "Not checked: the cap on timeline reads was reached" in md and "## Repealed" in md
    assert "in-force date on the act's own timeline" in md


# --- the requests ---------------------------------------------------------------------------------------------

def test_a_challenge_midway_stops_the_reads_and_keeps_what_was_found(tmp_path, pages):
    from p1_scrape.adapters.my_gazette.records import LomThrottled

    fresh = [r for r in pages["current"] if r.file_stamp and r.file_stamp >= "2026-09-01"][:4]

    class Client:
        log = [{"ts": "x"}] * 7

    class Adapter:
        root = "https://sso.agc.gov.sg"
        listed = {"current": pages["current"]}
        details, subsidiary, notes = {}, {}, []
        reads = 0

        def _check_robots(self, client): pass
        def _open_sso(self, client): pass
        def _seed_by_code(self, pillars): return {}, []
        def _mark_relevance(self, items): pass

        def _load_detail(self, code, client):
            Adapter.reads += 1
            if Adapter.reads == 3:
                raise LomThrottled("HTTP 202, x-amzn-waf-action: challenge")
            self.details[code] = pages["PDPA2012"]

        def _load_sl(self, code, client):
            raise AssertionError("no regulations tab is read after a challenge")

    b = _baseline(tmp_path, _every_current_act(pages))
    changes = Q.check(Adapter(), Client(), b, since="2026-09-01", pillars=[6, 7], max_timelines=4)
    assert changes.timelines_read == 2
    not_checked = [c.portal_id for c in changes.changes if c.change == "not_checked"]
    assert len(not_checked) >= 2
    assert any("challenged the check" in n for n in changes.notes)
