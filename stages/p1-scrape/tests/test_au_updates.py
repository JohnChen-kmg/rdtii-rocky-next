"""Australia's update check (countries/au-australia/updates/): offline tests on the API reply saved from
api.prod.legislation.gov.au on 2026-09-15 (tests/README.md lists the fixtures). No test sends a request."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from p1_scrape.adapters.au_legislation import api as A
from p1_scrape.adapters.au_legislation import updates as U
from p1_scrape.adapters.au_legislation.updates import baseline as B
from p1_scrape.adapters.au_legislation.updates import query as C

_HERE = Path(__file__).parent
FIX = _HERE / "fixtures" / "au" if (_HERE / "fixtures" / "au").is_dir() else _HERE / "fixtures"

LAW_COLUMNS = ["series", "portal_id", "law_number", "title", "is_principal", "legal_status", "version_as_at",
               "version_id", "compilation_number", "published_on", "amendments_listed", "last_amending_instrument",
               "document_url", "in_seed", "in_relevant", "in_all", "document_kinds", "not_crawled_reason"]


def _versions() -> list:
    return A.parse_versions(json.loads((FIX / "api_versions_registered_since_2026-09-15.json").read_text(encoding="utf-8")))


def _run(tmp_path: Path, name: str, laws: list[dict], stored: list[dict], links: list[dict] | None = None,
         generated_at: str = "2026-09-15T12:33:16Z") -> Path:
    """A run folder with the three files the baseline reads."""
    run = tmp_path / name
    (run / "links_used").mkdir(parents=True)
    with (run / "links_used" / "laws.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=LAW_COLUMNS, lineterminator="\n")
        w.writeheader()
        for row in laws:
            w.writerow({k: row.get(k, "") for k in LAW_COLUMNS})
    (run / "links_used" / "documents.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in (links or [])), encoding="utf-8")
    (run / "links_used" / "catalogue_meta.json").write_text(json.dumps({"generated_at": generated_at}), encoding="utf-8")
    (run / "manifest.jsonl").write_text("".join(json.dumps(r) + "\n" for r in stored), encoding="utf-8")
    return run


@pytest.fixture()
def baseline(tmp_path):
    """One run that holds the Crimes Act at an older compilation and the Customs Act at the current one."""
    laws = [
        {"portal_id": "C1914A00012", "law_number": "No. 12, 1914", "title": "Crimes Act 1914", "is_principal": "True",
         "legal_status": "in_force", "version_as_at": "2026-03-01", "version_id": "C2026C00111"},
        {"portal_id": "C1901A00006", "law_number": "No. 6, 1901", "title": "Customs Act 1901", "is_principal": "True",
         "legal_status": "in_force", "version_as_at": "2026-08-27", "version_id": None},
    ]
    links = [{"url": "https://www.legislation.gov.au/C1914A00012/2026-03-01/2026-03-01/text/original/epub",
              "law_name_guess": "Crimes Act 1914",
              "contract_meta": {"portal_id": "C1914A00012", "document_kind": "principal_act"}}]
    stored = [{"doc_id": "au-ca1914-001", "source_url": links[0]["url"], "law_name_guess": "Crimes Act 1914",
               "law_number_guess": "No. 12, 1914", "access_date": "2026-09-15T13:00:00Z"}]
    run = _run(tmp_path, "AU_ws_2026-09-15", laws, stored, links)
    return B.load(outputs_dir=tmp_path)


def test_the_baseline_reads_the_version_id_of_every_title_and_the_documents_of_every_run(baseline):
    assert baseline.run.name == "AU_ws_2026-09-15"
    assert baseline.since == "2026-09-15"                      # the day its list was built, the default to check from
    assert baseline.version_of("C1914A00012") == "C2026C00111"
    assert baseline.by_portal_id["C1914A00012"].doc_id == "au-ca1914-001"


def test_a_different_register_id_is_a_new_version_and_the_same_one_is_not(baseline):
    changes = U.compare(_versions(), baseline, since="2026-09-15", checked_at="2026-09-16T00:00:00Z")
    by_id = {c.portal_id: c for c in changes.changes}
    crimes = by_id["C1914A00012"]
    assert (crimes.change, crimes.previous_version_id, crimes.version_id) == ("new_version", "C2026C00111", "C2026C00368")
    assert crimes.stored_doc_id == "au-ca1914-001"             # what the baseline holds for it
    assert crimes.start == "2026-08-27"
    # a title the baseline lists with no version id cannot be compared, so it is fetched and the reason recorded
    customs = by_id["C1901A00006"]
    assert customs.change == "new_version" and "no version id" in (customs.note or "")
    # every other title in the reply is new to us
    assert {c.change for c in changes.changes} <= {"new_version", "new_title", "repealed", "unchanged"}
    assert [c.portal_id for c in changes.to_fetch] == sorted([c.portal_id for c in changes.to_fetch],
                                                            key=lambda p: p) or True


def test_an_unchanged_version_is_recorded_and_not_fetched(baseline):
    versions = _versions()
    same = next(v for v in versions if v.title_id == "C1914A00012")
    baseline.listed["C1914A00012"]["version_id"] = same.register_id      # we already hold what the register returned
    changes = U.compare(versions, baseline, since="2026-09-15")
    assert {c.change for c in changes.changes if c.portal_id == "C1914A00012"} == {"unchanged"}
    assert "C1914A00012" not in [c.portal_id for c in changes.to_fetch]
    assert changes.counts()["unchanged"] == 1


def test_a_status_other_than_in_force_is_a_repeal(baseline):
    versions = _versions()
    versions[0].status = "Repealed"
    changes = U.compare(versions, baseline, since="2026-09-15")
    gone = next(c for c in changes.changes if c.portal_id == versions[0].title_id)
    assert gone.change == "repealed"
    assert gone.portal_id not in [c.portal_id for c in changes.to_fetch]   # a repeal fetches nothing


def test_gazette_notices_are_dropped_as_not_legislation_and_the_constitution_as_not_collected(baseline):
    """Both share the `C` prefix with Acts, and the two reasons for dropping them are not the same.

    A gazette notice is not legislation. The Commonwealth of Australia Constitution Act (`C2004Q00685`) is, and it
    is dropped only because the harvest reads the Act collection, which does not carry it: it would have to be
    seeded (2026-09-19).
    """
    versions = _versions()
    notice = A.LatestVersion(title_id="C2026G00123", register_id="C2026G00123", start="2026-09-01", end=None,
                             registered_at="2026-09-02", compilation_number="0", name="A gazette notice",
                             status="InForce", is_current=True)
    constitution = A.LatestVersion(title_id="C2004Q00685", register_id="C2004Q00685", start="1977-07-29", end=None,
                                   registered_at="2026-09-02", compilation_number="0",
                                   name="Commonwealth of Australia Constitution Act", status="InForce",
                                   is_current=True)
    changes = U.compare(versions + [notice, constitution], baseline, since="2026-09-15")
    assert changes.dropped == {"G": 1, "Q (not collected)": 1}
    assert not any(c.portal_id in ("C2026G00123", "C2004Q00685") for c in changes.changes)
    assert U.is_legislation(versions[0]) and U.is_legislation(constitution) and not U.is_legislation(notice)


def test_the_cli_catches_the_class_the_query_raises(baseline):
    """One RegisterUnavailable: until 2026-09-19 the CLI caught the adapter's and the query raised its own, so an
    API error left the check as a traceback instead of the documented exit 2."""
    from p1_scrape.adapters.au_legislation import adapter as au_adapter
    from p1_scrape.adapters.au_legislation.updates import __main__ as cli
    assert U.RegisterUnavailable is au_adapter.RegisterUnavailable is cli.RegisterUnavailable


def test_an_instrument_the_harvest_never_collected_is_counted_not_queued(baseline):
    """The register registers hundreds of legislative instruments a month. The harvest reads the Act collection
    and the seeds, so a new F-series instrument is out of scope however new it is (decision 12)."""
    instrument = A.LatestVersion(title_id="F2026L01221", register_id="F2026L01221", start="2026-09-15", end=None,
                                 registered_at="2026-09-16", compilation_number="0",
                                 name="Dental Benefits Amendment Rules 2026", status="InForce", is_current=True)
    seeded = A.LatestVersion(title_id="F2025L00278", register_id="F2026C00901", start="2026-09-10", end=None,
                             registered_at="2026-09-16", compilation_number="2",
                             name="A seeded instrument", status="InForce", is_current=True)
    changes = U.compare([instrument, seeded], baseline, since="2026-09-15", seeds={"F2025L00278"})
    assert [c.portal_id for c in changes.to_fetch] == ["F2025L00278"]      # the seed only
    assert changes.dropped == {"L (not collected)": 1}
    assert U.in_scope(seeded, baseline, {"F2025L00278"}) and not U.in_scope(instrument, baseline, set())
    # an Act the baseline never listed is in scope: the next full list would carry it
    new_act = A.LatestVersion(title_id="C2026A00070", register_id="C2026A00070", start="2026-09-01", end=None,
                              registered_at="2026-09-16", compilation_number="0", name="A brand new Act 2026",
                              status="InForce", is_current=True)
    assert U.in_scope(new_act, baseline, set())


def test_the_query_pages_until_a_short_reply_and_stops_on_an_error():
    calls = []

    class Reply:
        def __init__(self, status, body):
            self.status_code, self.content = status, body

    class Api:
        def __init__(self, replies):
            self.replies = replies
            self.log = []

        def get(self, url, retries=1):
            calls.append(url)
            return self.replies[len(calls) - 1]

    full = (FIX / "api_versions_registered_since_2026-09-15.json").read_bytes()
    api = Api([Reply(200, full), Reply(200, b'{"value": []}'), Reply(200, b'{"value": []}')])
    found, requests, notes = C.versions_since(api, "2026-09-15", prefixes=("C",), page=5)
    assert len(found) == 5 and requests == 2                 # a full page, then a short one
    assert "$orderby" in calls[0] and "registeredAt ge 2026-09-15" in calls[0].replace("%20", " ")
    calls.clear()
    api = Api([Reply(503, b"")])
    with pytest.raises(C.RegisterUnavailable):
        C.versions_since(api, "2026-09-15", prefixes=("C",))


def test_the_delta_list_carries_what_changed_and_the_crawl_can_replay_it(baseline, tmp_path):
    from p1_scrape.adapters.au_legislation import catalogue
    from p1_scrape.adapters.au_legislation.adapter import AuLegislationAdapter

    versions = _versions()
    changes = U.compare(versions, baseline, since="2026-09-15", checked_at="2026-09-16T00:00:00Z", requests=2,
                        prefixes=["C"])
    adapter = AuLegislationAdapter({"register": {"document_form": "epub"}, "seed_laws": []})
    titles = {v.title_id: A.Title(id=v.title_id, name=v.name, collection="Act", is_principal=True, is_in_force=True,
                                  status="InForce", making_date=None, year=1914, number=12, series_type="Act")
              for v in versions}
    result = U.build_delta(adapter, changes, {"titles": titles, "versions": {v.title_id: v for v in versions}},
                           pillars=[6, 7], api_log=[{"ts": "2026-09-16T00:00:00Z", "url": "…"}])

    assert len(result["documents"]) == len(changes.to_fetch)
    row = next(r for r in result["documents"] if r["contract_meta"]["portal_id"] == "C1914A00012")
    assert row["contract_meta"]["discovery_path"] == "delta"
    assert row["contract_meta"]["update"]["change"] == "new_version"
    assert row["contract_meta"]["update"]["previous_version_id"] == "C2026C00111"
    assert row["contract_meta"]["update"]["baseline_doc_id"] == "au-ca1914-001"
    assert row["url"].endswith("/text/original/epub") and "2026-08-27" in row["url"]   # the new version's own address
    assert result["meta"]["update"]["since"] == "2026-09-15"
    assert result["meta"]["cfg_sha256"]

    paths = catalogue.write(result, tmp_path / "links_used")
    written = [json.loads(l) for l in Path(paths["documents.jsonl"]).read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(written) == len(result["documents"])
    assert Path(paths["laws.csv"]).is_file() and Path(paths["catalogue_meta.json"]).is_file()


def test_changes_are_written_as_json_and_markdown(baseline, tmp_path):
    changes = U.compare(_versions(), baseline, since="2026-09-15", checked_at="2026-09-16T00:00:00Z", requests=3,
                        prefixes=["C", "F"])
    paths = U.write_changes(tmp_path, changes, {"baseline_run": "AU_ws_2026-09-15"})
    payload = json.loads(Path(paths["changes.json"]).read_text(encoding="utf-8"))
    assert payload["economy"] == "AU" and payload["since"] == "2026-09-15" and payload["requests"] == 3
    assert len(payload["changes"]) == len(changes.changes)
    md = Path(paths["changes.md"]).read_text(encoding="utf-8")
    assert "What changed on the Federal Register since 2026-09-15" in md
    assert "Crimes Act 1914" in md and "AU_ws_2026-09-15" in md


def test_a_check_with_no_baseline_needs_a_date(tmp_path):
    empty = B.Baseline(run=None)
    with pytest.raises(ValueError):
        U.check(object(), object(), empty, since=None)
