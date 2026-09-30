"""What changed on the Lao Official Gazette since the last run, and what that means for the crawl.

This portal answers more than Timor-Leste's, because **every row states a status**. A law that was ປັດຈຸບັນ
(current) and is now ສະບັບເກົ່າ (old version) has been superseded, and the portal says so in the listing — no
document has to be opened to find out. That gives this check a verdict the append-only gazettes cannot offer:

| Found | Verdict | Fetched? |
| :---- | :---- | :---- |
| A law the baseline never listed | `new_law` | Yes, unless we already hold that exact file |
| A law whose status word changed (ປັດຈຸບັນ -> ສະບັບເກົ່າ) | `status_changed` | Yes: the portal often posts the revised text at the same time |
| A law we listed, whose file we never stored | `not_stored` | Yes |
| A law we listed, now pointing at a different file | `document_moved` | Yes |
| A law that now has an English translation it did not have | `translation_added` | Yes: the new file only |
| A law the baseline listed that the portal no longer lists | `delisted` | No: reported |
| Anything else | `unchanged` | No |

With `--since` and no baseline, a law counts as `new_law` when the gazette published it on or after that date —
the `ເຜີຍແຜ່ລົງຈົດໝາຍເຫດ` column, which is the date the portal itself orders its listings by.

**There is still no `amended` verdict**, and that is right here too: the gazette publishes as made and never
edits a document. An amendment arrives either as its own ກົດໝາຍ ວ່າດ້ວຍການປັບປຸງ… instrument (a `new_law` whose
`document_kind` is `amending_act`) or as a whole revised text, ສະບັບປັບປຸງ, which is a `new_law` of its own and
pushes the text it replaces into the `old=1` listing — where this check sees it as `status_changed`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

FETCH = ("new_law", "status_changed", "not_stored", "document_moved", "translation_added")


@dataclass
class Change:
    change: str            # new_law | status_changed | not_stored | document_moved | translation_added |
                           # delisted | unchanged
    portal_id: str
    law_name: Optional[str] = None
    legal_type_label: Optional[str] = None
    document_kind: Optional[str] = None
    made_on: Optional[str] = None
    gazetted_on: Optional[str] = None
    legal_status: Optional[str] = None
    status_word: Optional[str] = None
    previous_status_word: Optional[str] = None
    document_url: Optional[str] = None
    previous_document_url: Optional[str] = None
    stored_doc_id: Optional[str] = None
    note: Optional[str] = None

    def as_dict(self) -> dict:
        return dict(self.__dict__)


@dataclass
class Changes:
    since: Optional[str] = None
    checked_at: Optional[str] = None
    requests: int = 0
    changes: list[Change] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def to_fetch(self) -> list[Change]:
        """One entry per document to crawl, deduplicated by address."""
        seen, out = set(), []
        for c in self.changes:
            if c.change not in FETCH or not c.document_url or c.document_url in seen:
                continue
            # a law new to the LIST whose file we already hold is not new to us, and WORKFLOW.md section 3 has
            # always said so; until 2026-09-21 it was queued anyway
            if c.change == "new_law" and c.stored_doc_id:
                continue
            seen.add(c.document_url)
            out.append(c)
        return out

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for c in self.changes:
            out[c.change] = out.get(c.change, 0) + 1
        return out


def compare(listed: dict, baseline, since: Optional[str], checked_at: Optional[str] = None,
            requests: int = 0, partial: bool = False) -> Changes:
    """Every law the portal lists today against what the baseline held.

    `partial` says only the first pages of each listing were read, and suppresses every `delisted` verdict: a
    law below the cut was not seen, which is not the same as the portal dropping it.
    """
    out = Changes(since=since, checked_at=checked_at, requests=requests)
    held = dict(baseline.acts) if baseline is not None else {}
    stored = baseline.stored if baseline is not None else {}
    seen: set[str] = set()

    for _legal_type, rows in listed.items():
        for row in rows:
            seen.add(row.code)
            was = held.get(row.code)
            lao, english = row.url("lao"), row.url("eng")
            common = dict(portal_id=row.code, law_name=row.title, document_kind=row.document_kind,
                          legal_type_label=row.kind_label,
                          made_on=row.made_on, gazetted_on=row.gazetted_on, legal_status=row.legal_status,
                          status_word=row.status_label, document_url=lao or english)
            if was is None:
                if baseline is None and since and (row.gazetted_on or "") < since:
                    continue                                   # date mode: older than the date, not a change
                # A new law is its FILES, plural: a law first listed with both a Lao text and a translation
                # needs both queued, and the census carries both.
                for url in [u for u in (lao, english) if u]:
                    note = ("the file it points at is already stored: the law is new to the list, not to us"
                            if url in stored else None)
                    if url == english:
                        note = "; ".join(x for x in [note, "the gazette's English translation"] if x)
                    out.changes.append(Change(change="new_law", note=note,
                                              stored_doc_id=(stored.get(url) or {}).get("doc_id"),
                                              **{**common, "document_url": url}))
                continue

            before_lao = (was.get("lao_url") or "").strip() or None
            before_english = (was.get("english_url") or "").strip() or None
            before_word = (was.get("status_word") or "").strip() or None

            # The status word is a property of the LAW; the two files are judged separately beneath it. Until
            # 2026-09-21 these were one elif chain, so a law that changed status and gained a translation on the
            # same day reported only the status change and the English file was never queued — and never could
            # be again, because the next run's census already recorded the address (`../NOTES.md` 2.6).
            before_count = len(out.changes)
            if before_word and row.status_label and before_word != row.status_label:
                out.changes.append(Change(change="status_changed", previous_status_word=before_word,
                                          previous_document_url=before_lao,
                                          note=f"the portal now marks this law {row.status_label!r}, where the "
                                               f"last run read {before_word!r}", **common))

            for url, before, language in ((lao, before_lao, "Lao"), (english, before_english, "English")):
                if not url:
                    continue
                per_file = {**common, "document_url": url}
                if before and url != before:
                    out.changes.append(Change(change="document_moved", previous_document_url=before,
                                              note=f"the portal now points this law at a different {language} "
                                                   f"file", **per_file))
                elif not before and language == "English":
                    out.changes.append(Change(
                        change="translation_added",
                        note="the gazette now offers an English translation it did not before", **per_file))
                elif url not in stored:
                    out.changes.append(Change(change="not_stored",
                                              note=f"the {language} file was listed before, but no run holds it",
                                              **per_file))
            if len(out.changes) == before_count:
                out.changes.append(Change(change="unchanged",
                                          stored_doc_id=(stored.get(lao or english or "") or {}).get("doc_id"),
                                          **common))

    for portal_id, was in held.items():
        if portal_id in seen or partial:
            continue
        out.changes.append(Change(change="delisted", portal_id=portal_id, law_name=was.get("title"),
                                  legal_type_label=was.get("legal_type_label"),
                                  document_kind=was.get("document_kind"), made_on=was.get("made_on"),
                                  gazetted_on=was.get("gazetted_on"), status_word=was.get("status_word"),
                                  legal_status=was.get("legal_status"),
                                  document_url=(was.get("lao_url") or was.get("english_url") or None),
                                  note="the portal no longer lists this law; the copy we hold is unaffected"))
    return out
