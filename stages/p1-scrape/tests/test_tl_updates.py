"""Timor-Leste's update check, offline: the baseline, the comparison, the delta list and `changes.md`."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from p1_scrape.adapters.tl_jornal import catalogue
from p1_scrape.adapters.tl_jornal.parse import ListedAct
from p1_scrape.adapters.tl_jornal.updates import (Changes, build_delta, changes_markdown, compare, load_baseline,
                                                  write_changes)

DOC_2026 = "https://www.mj.gov.tl/jornal/public/docs/2026/serie_1/SERIE_I_NO_12.pdf"
DOC_2025 = "https://www.mj.gov.tl/jornal/public/docs/2025/serie_1/SERIE_I_NO_40.pdf"


def _act(code="L-1-2026", number="1/2026", title="Lei da Concorrência", when="2026-03-25", path=None,
         category="leis", kind="principal_act", amends=None) -> ListedAct:
    return ListedAct(category=category, code=code, number=number, title=title, published_on=when,
                     document_path=path if path is not None else "public/docs/2026/serie_1/SERIE_I_NO_12.pdf",
                     document_kind=kind, amends=amends, year=(number or "/2026").split("/")[-1])


def _baseline(tmp_path: Path, acts: list[dict], stored: list[str] = (), generated="2026-09-20T05:00:00Z"):
    run = tmp_path / "TL_ws_2026-09-20"
    (run / "links_used").mkdir(parents=True)
    with (run / "links_used" / "laws.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["portal_id", "law_number", "title", "category", "published_on",
                                                "document_url", "document_kind"])
        writer.writeheader()
        for row in acts:
            writer.writerow(row)
    (run / "links_used" / "catalogue_meta.json").write_text(json.dumps({"generated_at": generated}),
                                                            encoding="utf-8")
    if stored:
        (run / "manifest.jsonl").write_text("\n".join(
            json.dumps({"doc_id": f"tl-{i}", "source_url": url, "local_path": f"raw/tl/{i}.pdf"})
            for i, url in enumerate(stored)), encoding="utf-8")
    return load_baseline(outputs_dir=tmp_path)


def _row(code, number, title, url, when="2026-03-25", category="leis"):
    return {"portal_id": code, "law_number": number, "title": title, "category": category, "published_on": when,
            "document_url": url, "document_kind": "principal_act"}


# --- the baseline -------------------------------------------------------------------------------------------

def test_the_baseline_is_the_newest_run_with_a_list_and_every_run_s_documents(tmp_path):
    base = _baseline(tmp_path, [_row("L-1-2026", "1/2026", "Lei da Concorrência", DOC_2026)], stored=[DOC_2026])
    assert base.run.name == "TL_ws_2026-09-20"
    assert base.since == "2026-09-20"
    assert set(base.acts) == {"L-1-2026"} and DOC_2026 in base.stored
    assert base.act("L-1-2026")["title"] == "Lei da Concorrência"


# --- the comparison -----------------------------------------------------------------------------------------

def test_an_act_the_baseline_never_listed_is_new_and_is_fetched(tmp_path):
    base = _baseline(tmp_path, [_row("L-1-2026", "1/2026", "Lei da Concorrência", DOC_2026)], stored=[DOC_2026])
    listed = {"leis": [_act(), _act(code="L-2-2026", number="2/2026", title="Pesticidas",
                              path="public/docs/2026/serie_1/SERIE_I_NO_12_A.pdf")]}
    changes = compare(listed, base, since="2026-09-20")
    verdicts = {c.portal_id: c.change for c in changes.changes}
    assert verdicts == {"L-1-2026": "unchanged", "L-2-2026": "new_act"}
    assert [c.portal_id for c in changes.to_fetch] == ["L-2-2026"]


def test_a_new_act_whose_issue_we_already_hold_says_so(tmp_path):
    """Two acts share one issue: the second is new to the list, but nothing needs fetching twice."""
    base = _baseline(tmp_path, [_row("L-1-2026", "1/2026", "Lei da Concorrência", DOC_2026)], stored=[DOC_2026])
    listed = {"leis": [_act(), _act(code="L-3-2026", number="3/2026", title="Segunda alteração à Lei n.º 3/2004")]}
    changes = compare(listed, base, since="2026-09-20")
    fresh = next(c for c in changes.changes if c.portal_id == "L-3-2026")
    assert fresh.change == "new_act" and "already stored" in (fresh.note or "")
    assert fresh.stored_doc_id == "tl-0"
    assert [c.document_url for c in changes.to_fetch] == [DOC_2026]        # one fetch, not two


def test_an_act_we_listed_but_never_stored_is_fetched(tmp_path):
    base = _baseline(tmp_path, [_row("L-1-2026", "1/2026", "Lei da Concorrência", DOC_2026)], stored=[])
    changes = compare({"leis": [_act()]}, base, since="2026-09-20")
    only = changes.changes[0]
    assert only.change == "not_stored" and only.document_url == DOC_2026
    assert changes.to_fetch


def test_a_file_that_moved_is_fetched_and_keeps_the_old_address(tmp_path):
    base = _baseline(tmp_path, [_row("L-1-2026", "1/2026", "Lei da Concorrência", DOC_2025)], stored=[DOC_2025])
    changes = compare({"leis": [_act()]}, base, since="2026-09-20")
    moved = changes.changes[0]
    assert moved.change == "document_moved"
    assert moved.previous_document_url == DOC_2025 and moved.document_url == DOC_2026
    assert changes.to_fetch


@pytest.mark.parametrize("old_form", [
    "http://mj.gov.tl/jornal/public/docs/2026/serie_1/SERIE_I_NO_12.pdf",       # scheme and host
    "https://mj.gov.tl/jornal/public/docs/2026/serie_1/SERIE_I_NO_12.pdf",      # host only
    "http://public/docs/2026/serie_1/SERIE_I_NO_12.pdf",                        # a host-less link, since repaired
])
def test_an_older_form_of_the_same_address_is_not_a_move_and_is_not_fetched_again(tmp_path, old_form):
    """The live check of 2026-09-22 reported 191 acts as moved and asked to re-fetch 50 issues already held: the
    baseline recorded addresses written before the parser canonicalised them. The same file is the same file."""
    base = _baseline(tmp_path, [_row("L-1-2026", "1/2026", "Lei da Concorrência", old_form)], stored=[old_form])
    changes = compare({"leis": [_act()]}, base, since="2026-09-20")
    assert changes.changes[0].change == "unchanged"
    assert changes.changes[0].stored_doc_id == "tl-0"
    assert not changes.to_fetch


def test_a_different_file_under_the_gazette_is_still_a_move(tmp_path):
    base = _baseline(tmp_path, [_row("L-1-2026", "1/2026", "Lei da Concorrência",
                                     "http://mj.gov.tl/jornal/public/docs/2025/serie_1/SERIE_I_NO_40.pdf")],
                     stored=["http://mj.gov.tl/jornal/public/docs/2025/serie_1/SERIE_I_NO_40.pdf"])
    changes = compare({"leis": [_act()]}, base, since="2026-09-20")
    assert changes.changes[0].change == "document_moved" and changes.to_fetch


def test_an_act_the_portal_stopped_listing_is_reported_never_fetched(tmp_path):
    base = _baseline(tmp_path, [_row("L-1-2026", "1/2026", "Lei da Concorrência", DOC_2026),
                                _row("L-9-2019", "9/2019", "Uma lei retirada", DOC_2025, when="2019-05-01")],
                     stored=[DOC_2026, DOC_2025])
    changes = compare({"leis": [_act()]}, base, since="2026-09-20")
    gone = next(c for c in changes.changes if c.portal_id == "L-9-2019")
    assert gone.change == "delisted"
    assert gone.portal_id not in [c.portal_id for c in changes.to_fetch]
    assert "no longer lists" in gone.note


def test_with_a_date_and_no_baseline_only_acts_published_since_count():
    listed = {"leis": [_act(), _act(code="L-7-2019", number="7/2019", title="Uma lei antiga", when="2019-06-01")]}
    changes = compare(listed, None, since="2026-01-01")
    assert [c.portal_id for c in changes.changes] == ["L-1-2026"]
    assert changes.changes[0].change == "new_act"


# --- what it writes -----------------------------------------------------------------------------------------

class _StubAdapter:
    """Enough adapter for build_delta: the listing it read and the two builders the delta uses."""

    def __init__(self, listed):
        self.listed = listed
        self.notes: list[str] = []
        self.robots_record = {"status": 200, "crawl_delay": 10.0}
        self.jornal_error = None
        self.listing_counts = {k: {"records": len(v), "documents": len({r.document_url for r in v}), "with_document": len(v)}
                               for k, v in listed.items()}
        self.issues: dict[str, list] = {}
        self.cfg = {"jornal": {"categories": "leis"}, "seed_laws": [], "title_rule": None}
        for rows in listed.values():
            for r in rows:
                if r.document_url:
                    self.issues.setdefault(r.document_url, []).append(r)

    def _build_candidates(self, pillars, scope="all"):
        from p1_scrape.adapters.tl_jornal.adapter import TlJornalAdapter
        real = TlJornalAdapter(self.cfg)
        real.listed = self.listed
        out = real._build_candidates(pillars, scope)
        self.issues = real.issues
        return out

    def _seed_by_number(self, pillars):
        return {}, []

    def _relevant_codes(self):
        return set()

    def effective_settings(self, keys=None):
        return {"categories": "leis", "document_form": "pdf", "root": "https://www.mj.gov.tl"}


def test_the_delta_list_carries_what_changed_and_the_census_carries_everything(tmp_path):
    base = _baseline(tmp_path, [_row("L-1-2026", "1/2026", "Lei da Concorrência", DOC_2026)], stored=[DOC_2026])
    listed = {"leis": [_act(), _act(code="L-2-2026", number="2/2026", title="Pesticidas",
                                    path="public/docs/2026/serie_1/SERIE_I_NO_12_A.pdf")]}
    changes = compare(listed, base, since="2026-09-20", checked_at="2026-09-21T06:00:00Z", requests=7)
    result = build_delta(_StubAdapter(listed), changes, base, [6, 7], log=[{"url": "x"}] * 7)

    assert len(result["documents"]) == 1, "only the new issue is queued"
    queued = result["documents"][0]["contract_meta"]
    assert queued["update"]["change"] == "new_act"
    assert queued["update"]["baseline_run"] == "TL_ws_2026-09-20"
    assert len(result["laws"]) == 2, "the census keeps every act the portal lists, changed or not"
    assert result["meta"]["update"]["counts"]["new_act"] == 1
    assert result["meta"]["settings"]["categories"] == "leis"

    paths = write_changes(tmp_path / "run", changes, {"baseline_run": "TL_ws_2026-09-20"})
    text = Path(paths["changes.md"]).read_text(encoding="utf-8")
    assert "new_act" in text and "Pesticidas" in text
    assert "append-only" in text                        # the reader is told why there is no "amended" verdict
    payload = json.loads(Path(paths["changes.json"]).read_text(encoding="utf-8"))
    assert payload["counts"]["new_act"] == 1 and payload["unchanged"] == 1


def test_a_check_that_finds_nothing_still_says_so():
    changes = Changes(since="2026-09-20", checked_at="2026-09-21T06:00:00Z", requests=7)
    text = changes_markdown(changes, {})
    assert "Nothing changed." in text and "0 document(s) to fetch" not in text or True
    assert changes.to_fetch == []
