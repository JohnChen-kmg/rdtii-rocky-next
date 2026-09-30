"""Lao PDR's update check, offline: the baseline, the comparison, the delta list and `changes.md`."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from p1_scrape.adapters.la_gazette import catalogue
from p1_scrape.adapters.la_gazette.parse import ListedLaw
from p1_scrape.adapters.la_gazette.updates import (Changes, build_delta, changes_markdown, compare,
                                                   runs_under,
                                                   load_baseline, write_changes)

LAO_A = "https://laoofficialgazette.gov.la/kcfinder/upload/files/88-25-6-2025_0001.pdf"
LAO_B = "https://laoofficialgazette.gov.la/kcfinder/upload/files/ 69. 11.12.2024.pdf"
ENG_A = "https://laoofficialgazette.gov.la/kcfinder/upload/files/Income Tax Law Eng.pdf"


def _law(law_id="2597", title="ກົດໝາຍວ່າດ້ວຍ ອາກອນລາຍໄດ້ (ສະບັບປັບປຸງ)", made="2025-06-25",
         gazetted="2026-06-19", status="ປັດຈຸບັນ", legal_status="in_force", lao="88-25-6-2025_0001.pdf",
         eng=None, legal_type=6, kind="principal_act", old=0) -> ListedLaw:
    return ListedLaw(legal_type=legal_type, law_id=law_id, title=title, agency="ກະຊວງ ການເງິນ", made_on=made,
                     gazetted_on=gazetted, kind_label="ກົດໝາຍ", status_label=status,
                     legal_status=legal_status, pdf_lao=f"/kcfinder/upload/files/{lao}" if lao else None,
                     pdf_english=f"/kcfinder/upload/files/{eng}" if eng else None, document_kind=kind, old=old)


def _row(portal_id, title, lao_url, status_word="ປັດຈຸບັນ", english_url="", gazetted="2026-06-19",
         kind="principal_act"):
    return {"portal_id": portal_id, "title": title, "lao_url": lao_url, "english_url": english_url,
            "status_word": status_word, "legal_status": "in_force", "gazetted_on": gazetted,
            "made_on": "2025-06-25", "document_kind": kind, "legal_type_label": "Law"}


def _baseline(tmp_path: Path, laws: list[dict], stored: list[str] = (), generated="2026-09-20T05:00:00Z"):
    run = tmp_path / "LA_ws_2026-09-20"
    (run / "links_used").mkdir(parents=True)
    with (run / "links_used" / "laws.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(laws[0]) if laws else ["portal_id"])
        writer.writeheader()
        writer.writerows(laws)
    (run / "links_used" / "catalogue_meta.json").write_text(json.dumps({"generated_at": generated}),
                                                            encoding="utf-8")
    if stored:
        (run / "manifest.jsonl").write_text("\n".join(
            json.dumps({"doc_id": f"la-{i}", "source_url": url, "local_path": f"raw/la/{i}.pdf"})
            for i, url in enumerate(stored)), encoding="utf-8")
    return load_baseline(outputs_dir=tmp_path)


# --- the baseline -------------------------------------------------------------------------------------------

def test_the_baseline_is_the_newest_run_with_a_list_and_every_run_s_documents(tmp_path):
    base = _baseline(tmp_path, [_row("LA-2597", "ກົດໝາຍວ່າດ້ວຍ ອາກອນລາຍໄດ້", LAO_A)], stored=[LAO_A])
    assert base.run.name == "LA_ws_2026-09-20"
    assert base.since == "2026-09-20"
    assert set(base.acts) == {"LA-2597"} and LAO_A in base.stored
    assert base.act("LA-2597")["status_word"] == "ປັດຈຸບັນ"


# --- the comparison -----------------------------------------------------------------------------------------

def test_a_law_the_baseline_never_listed_is_new_and_is_fetched(tmp_path):
    base = _baseline(tmp_path, [_row("LA-2597", "ອາກອນລາຍໄດ້", LAO_A)], stored=[LAO_A])
    listed = {6: [_law(), _law(law_id="2598", title="ກົດໝາຍວ່າດ້ວຍ ຄວາມປອດໄພໄຊເບີ", lao=" 69. 11.12.2024.pdf")]}
    changes = compare(listed, base, since="2026-09-20")
    assert {c.portal_id: c.change for c in changes.changes} == {"LA-2597": "unchanged", "LA-2598": "new_law"}
    assert [c.portal_id for c in changes.to_fetch] == ["LA-2598"]


def test_a_status_word_that_changed_is_the_verdict_no_other_portal_here_can_give(tmp_path):
    """The gazette marks each row ປັດຈຸບັນ or ສະບັບເກົ່າ. A law that moved between them has been superseded, and
    the listing says so without a document being opened."""
    base = _baseline(tmp_path, [_row("LA-2597", "ອາກອນລາຍໄດ້", LAO_A)], stored=[LAO_A])
    listed = {6: [_law(status="ສະບັບເກົ່າ", legal_status="repealed", old=1)]}
    changes = compare(listed, base, since="2026-09-20")
    only = changes.changes[0]
    assert only.change == "status_changed"
    assert (only.previous_status_word, only.status_word) == ("ປັດຈຸບັນ", "ສະບັບເກົ່າ")
    assert only.legal_status == "repealed"
    assert changes.to_fetch, "the revised text usually arrives with the supersession, so it is re-read"


def test_a_law_we_listed_but_never_stored_is_fetched(tmp_path):
    base = _baseline(tmp_path, [_row("LA-2597", "ອາກອນລາຍໄດ້", LAO_A)], stored=[])
    changes = compare({6: [_law()]}, base, since="2026-09-20")
    assert changes.changes[0].change == "not_stored"
    assert [c.document_url for c in changes.to_fetch] == [LAO_A]


def test_a_file_that_moved_is_fetched_and_keeps_the_old_address(tmp_path):
    base = _baseline(tmp_path, [_row("LA-2597", "ອາກອນລາຍໄດ້", LAO_B)], stored=[LAO_B])
    changes = compare({6: [_law()]}, base, since="2026-09-20")
    moved = changes.changes[0]
    assert moved.change == "document_moved"
    assert (moved.previous_document_url, moved.document_url) == (LAO_B, LAO_A)
    assert changes.to_fetch


def test_a_translation_the_gazette_did_not_have_before_is_fetched_on_its_own(tmp_path):
    """21 of 182 laws had an English text on 2026-09-20. The gazette adds them over time, and when it does, the
    Lao text we already hold does not need fetching again."""
    base = _baseline(tmp_path, [_row("LA-2597", "ອາກອນລາຍໄດ້", LAO_A)], stored=[LAO_A])
    changes = compare({6: [_law(eng="Income Tax Law Eng.pdf")]}, base, since="2026-09-20")
    added = changes.changes[0]
    assert added.change == "translation_added"
    assert [c.document_url for c in changes.to_fetch] == [ENG_A], "only the new English file is queued"


def test_a_status_change_and_a_new_translation_on_the_same_law_are_both_reported(tmp_path):
    """They were one elif chain until 2026-09-21, so the status change masked the translation and the English
    file was never queued — and never could be, because the next run's census already held the address. The
    gazette posts a revised text and its supersession together, which is exactly when the two coincide."""
    base = _baseline(tmp_path, [_row("LA-2597", "ອາກອນລາຍໄດ້", LAO_A)], stored=[LAO_A])
    listed = {6: [_law(status="ສະບັບເກົ່າ", legal_status="repealed", old=1, eng="Income Tax Law Eng.pdf")]}
    changes = compare(listed, base, since="2026-09-20")
    verdicts = {c.change for c in changes.changes}
    assert verdicts == {"status_changed", "translation_added"}
    assert sorted(c.document_url for c in changes.to_fetch) == sorted([LAO_A, ENG_A])


def test_a_moved_lao_file_and_a_moved_english_file_are_reported_separately(tmp_path):
    base = _baseline(tmp_path, [_row("LA-2597", "ອາກອນລາຍໄດ້", LAO_B, english_url=ENG_A)], stored=[LAO_B, ENG_A])
    listed = {6: [_law(eng="Income Tax Law Eng v2.pdf")]}
    changes = compare(listed, base, since="2026-09-20")
    moved = [c for c in changes.changes if c.change == "document_moved"]
    assert len(moved) == 2, "the Lao file and the translation each moved"
    assert {c.previous_document_url for c in moved} == {LAO_B, ENG_A}


def test_a_missing_translation_is_seen_even_when_the_lao_text_is_held(tmp_path):
    """`url = lao or english` put every English file outside the comparison: 55 of the 1,824 files could never
    be reported `not_stored`, so a translation dropped by a crawl was never re-queued by any later check."""
    base = _baseline(tmp_path, [_row("LA-2597", "ອາກອນລາຍໄດ້", LAO_A, english_url=ENG_A)], stored=[LAO_A])
    changes = compare({6: [_law(eng="Income Tax Law Eng.pdf")]}, base, since="2026-09-20")
    assert [c.change for c in changes.changes] == ["not_stored"]
    assert [c.document_url for c in changes.to_fetch] == [ENG_A]


def test_a_brand_new_law_queues_both_of_its_files(tmp_path):
    base = _baseline(tmp_path, [_row("LA-1", "ກົດໝາຍເກົ່າ", LAO_B)], stored=[LAO_B])
    listed = {6: [_law(law_id="1", title="ກົດໝາຍເກົ່າ", lao=" 69. 11.12.2024.pdf"),
                  _law(law_id="2597", eng="Income Tax Law Eng.pdf")]}
    changes = compare(listed, base, since="2026-09-20")
    fresh = [c for c in changes.changes if c.change == "new_law"]
    assert sorted(c.document_url for c in fresh) == sorted([LAO_A, ENG_A])


def test_a_law_the_portal_stopped_listing_is_reported_never_fetched(tmp_path):
    base = _baseline(tmp_path, [_row("LA-2597", "ອາກອນລາຍໄດ້", LAO_A),
                                _row("LA-1000", "ກົດໝາຍເກົ່າ", LAO_B, gazetted="2010-01-01")],
                     stored=[LAO_A, LAO_B])
    changes = compare({6: [_law()]}, base, since="2026-09-20")
    gone = next(c for c in changes.changes if c.portal_id == "LA-1000")
    assert gone.change == "delisted"
    assert gone.portal_id not in [c.portal_id for c in changes.to_fetch]
    assert "no longer lists" in gone.note


def test_a_partial_check_never_reports_a_law_as_delisted(tmp_path):
    """`--pages N` reads only the top of each listing. A law below the cut was not seen, which is not the same
    as the portal dropping it, and saying otherwise would raise a false alarm on every cheap check."""
    base = _baseline(tmp_path, [_row("LA-2597", "ອາກອນລາຍໄດ້", LAO_A),
                                _row("LA-1000", "ກົດໝາຍເກົ່າ", LAO_B, gazetted="2010-01-01")],
                     stored=[LAO_A, LAO_B])
    changes = compare({6: [_law()]}, base, since="2026-09-20", partial=True)
    assert "delisted" not in changes.counts()


def test_a_new_law_whose_exact_file_we_already_hold_is_not_fetched_again(tmp_path):
    """Two laws share a file on this portal, so a law new to the LIST can point at bytes we already have.
    `WORKFLOW.md` section 3 and diff.py's own table have always said it is not fetched; it was."""
    base = _baseline(tmp_path, [_row("LA-1069", "ຄຳສັ່ງ", LAO_A)], stored=[LAO_A])
    listed = {6: [_law(law_id="1069", title="ຄຳສັ່ງ"), _law(law_id="2178", title="ລັດຖະບັນຍັດ")]}
    changes = compare(listed, base, since="2026-09-20")
    fresh = next(c for c in changes.changes if c.portal_id == "LA-2178")
    assert fresh.change == "new_law" and fresh.stored_doc_id == "la-0"
    assert changes.to_fetch == [], "the bytes are already held; only the listing is new"


def test_a_partial_check_never_becomes_the_next_baseline(tmp_path):
    """A `--pages` run's census is a fraction of the portal's. Taken as a baseline, every law below the cut
    reads as new and the cheap check turns into a full re-crawl."""
    full = tmp_path / "LA_ws_2026-09-21"
    (full / "links_used").mkdir(parents=True)
    with (full / "links_used" / "laws.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(_row("LA-1", "a", LAO_A)))
        w.writeheader(); w.writerow(_row("LA-1", "a", LAO_A)); w.writerow(_row("LA-2", "b", LAO_B))
    (full / "links_used" / "catalogue_meta.json").write_text(
        json.dumps({"generated_at": "2026-09-21T00:00:00Z"}), encoding="utf-8")

    shallow = tmp_path / "LA_ws_2026-09-21_to_2026-10-05"
    (shallow / "links_used").mkdir(parents=True)
    with (shallow / "links_used" / "laws.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(_row("LA-1", "a", LAO_A)))
        w.writeheader(); w.writerow(_row("LA-1", "a", LAO_A))
    (shallow / "links_used" / "catalogue_meta.json").write_text(
        json.dumps({"generated_at": "2026-10-05T00:00:00Z"}), encoding="utf-8")
    (shallow / "changes.json").write_text(json.dumps({"partial": True}), encoding="utf-8")

    base = load_baseline(outputs_dir=tmp_path)
    assert base.run.name == "LA_ws_2026-09-21", "the full run is the baseline, not the shallow one"
    assert set(base.acts) == {"LA-1", "LA-2"}


def test_runs_are_ordered_by_the_day_they_ended(tmp_path):
    """A crawl is `LA_ws_<date>`; a check is `LA_ws_<since>_to_<date>`. Sorting the whole name ranks a check by
    the date it counted from, so a check that ran on 10-05 sorted below a crawl from 10-01."""
    for name in ("LA_ws_2026-10-01", "LA_ws_2026-09-21_to_2026-10-05", "LA_ws_2026-09-21"):
        (tmp_path / name).mkdir()
    assert [p.name for p in runs_under(tmp_path)] == [
        "LA_ws_2026-09-21_to_2026-10-05", "LA_ws_2026-10-01", "LA_ws_2026-09-21"]


def test_with_a_date_and_no_baseline_only_laws_gazetted_since_count():
    listed = {6: [_law(), _law(law_id="800", title="ກົດໝາຍເກົ່າ", gazetted="2015-11-24")]}
    changes = compare(listed, None, since="2026-01-01")
    assert [c.portal_id for c in changes.changes] == ["LA-2597"]
    assert changes.changes[0].change == "new_law"


# --- what it writes -----------------------------------------------------------------------------------------

class _StubAdapter:
    """Enough adapter for build_delta: the listing it read and the builders the delta uses."""

    def __init__(self, listed):
        self.listed = listed
        self.notes: list[str] = []
        self.robots_record = {"status": 200, "delay_used_s": 6.0}
        self.gazette_error = None
        self.listing_counts = {str(k): {"kind": "Law", "records": len(v), "pages_read": 1}
                               for k, v in listed.items()}
        self.cfg = {"gazette": {"legal_types": "6", "superseded": True}, "seed_laws": [], "title_rule": None}

    def rows(self):
        return [r for rows in self.listed.values() for r in rows]

    def _build_candidates(self, pillars, scope="all"):
        from p1_scrape.adapters.la_gazette.adapter import LaGazetteAdapter
        real = LaGazetteAdapter(self.cfg)
        real.listed = self.listed
        return real._build_candidates(pillars, scope)

    def _seed_by_id(self, pillars):
        return {}, []

    def _relevant_ids(self):
        return set()

    def effective_settings(self, keys=None):
        return {"legal_types": "6", "superseded": True, "english_pdfs": True,
                "root": "https://laoofficialgazette.gov.la"}


def test_the_delta_list_carries_what_changed_and_the_census_carries_everything(tmp_path):
    base = _baseline(tmp_path, [_row("LA-2597", "ອາກອນລາຍໄດ້", LAO_A)], stored=[LAO_A])
    listed = {6: [_law(), _law(law_id="2598", title="ກົດໝາຍວ່າດ້ວຍ ຄວາມປອດໄພໄຊເບີ", lao=" 69. 11.12.2024.pdf")]}
    changes = compare(listed, base, since="2026-09-20", checked_at="2026-09-21T06:00:00Z", requests=192)
    result = build_delta(_StubAdapter(listed), changes, base, [6, 7], log=[{"url": "x"}] * 192)

    assert len(result["documents"]) == 1, "only the new law is queued"
    queued = result["documents"][0]["contract_meta"]
    assert queued["update"]["change"] == "new_law"
    assert queued["update"]["baseline_run"] == "LA_ws_2026-09-20"
    assert len(result["laws"]) == 2, "the census keeps every law the portal lists, changed or not"
    assert result["meta"]["update"]["counts"]["new_law"] == 1
    assert result["meta"]["settings"]["superseded"] is True

    paths = write_changes(tmp_path / "run", changes, {"baseline_run": "LA_ws_2026-09-20"})
    text = Path(paths["changes.md"]).read_text(encoding="utf-8")
    assert "new_law" in text and "ຄວາມປອດໄພໄຊເບີ" in text
    assert "status_changed" in text          # the reader is told the verdict exists and why
    payload = json.loads(Path(paths["changes.json"]).read_text(encoding="utf-8"))
    assert payload["counts"]["new_law"] == 1 and payload["unchanged"] == 1


def test_changes_md_shows_the_status_word_moving(tmp_path):
    base = _baseline(tmp_path, [_row("LA-2597", "ອາກອນລາຍໄດ້", LAO_A)], stored=[LAO_A])
    changes = compare({6: [_law(status="ສະບັບເກົ່າ", legal_status="repealed", old=1)]}, base,
                      since="2026-09-20", checked_at="2026-09-21T06:00:00Z")
    text = changes_markdown(changes, {})
    assert "ປັດຈຸບັນ -> ສະບັບເກົ່າ" in text


def test_a_check_that_finds_nothing_still_says_so():
    changes = Changes(since="2026-09-20", checked_at="2026-09-21T06:00:00Z", requests=192)
    text = changes_markdown(changes, {})
    assert "Nothing changed." in text
    assert changes.to_fetch == []


def test_the_delta_list_is_a_link_list_the_crawl_can_replay(tmp_path):
    base = _baseline(tmp_path, [], stored=[]) if False else None
    listed = {6: [_law()]}
    changes = compare(listed, None, since="2020-01-01")
    result = build_delta(_StubAdapter(listed), changes, base, [6, 7], log=[])
    paths = catalogue.write(result, tmp_path / "links_used", registry_files=None)
    rows, meta = catalogue.read_documents(paths["documents.jsonl"])
    assert rows and meta["economy"] == "LA" and meta["cfg_sha256"]
    assert rows[0]["url"].endswith(".pdf") and rows[0]["scopes"] == ["all"]
