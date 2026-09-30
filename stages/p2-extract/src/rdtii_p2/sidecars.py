"""Facts about a document that the manifest does not carry, and the decision to read it.

The manifest is one row per document and holds none of: the language, whether the document is
evidence or mere linkage, what kind of instrument it is, whether it is still in force, or
whether collection flagged the stored file as not being the law it is filed under. Those live
in two sidecars that collection writes beside every corpus:

    law_table.csv                one row per LAW - use, language, document_kind, legal_status
    links_used/documents.jsonl   contract_meta.content_flags, joined on
                                 contract_meta.corpus.doc_id, which is the contract's join key

Reading them is not language detection and not guessing (D3): every value here was written by
the crawler, and this module records which sidecar each value came from.

A law table row is per LAW, so a Timorese gazette issue holding 39 acts has 39 rows against one
doc_id. Anything aggregated across those rows says so.
"""

from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("rdtii_p2.sidecars")

# Uses that mean "do not read this document for indicator evidence" (collection decision 20).
LINKAGE_USES = {"linkage", "not held"}
# ...and the exception: our held text predates the amending instrument, so it is read normally.
READ_ANYWAY = {"linkage, text needed"}

# A stored file that is not the law it is filed under. Both spellings of the Timorese flag
# exist in the corpus, so this matches on prefix.
WRONG_INSTRUMENT_FLAGS = ("other_act_text", "act_not_in_text", "acts_not_in_text")
REPEAL_NOTICE_FLAG = "repeal_notice"

# Two Timorese documents are Ministry of Justice translations filed as the original, headed
# "TRADUCAO" with a "Titulo Original" line, and recorded as language por. Extracting them would
# publish a translation as source text, which breaches D5 and D3 at once. Named rather than
# pattern-matched because it is a finding about two specific files, audited by collection.
TRANSLATION_NOT_SOURCE = {
    "tl-lbn-001": "Ministry of Justice Tetum translation of the Nationality Act, filed as por",
    "tl-kenegpn-001": "Ministry of Justice Tetum translation, filed as por",
}


@dataclass
class DocFacts:
    """Everything known about one document beyond its manifest row."""

    doc_id: str
    language: str | None = None
    language_source: str | None = None
    content_flags: list[str] = field(default_factory=list)
    uses: set[str] = field(default_factory=set)
    document_kinds: set[str] = field(default_factory=set)
    legal_statuses: set[str] = field(default_factory=set)
    acts: list[dict] = field(default_factory=list)      # one law_table row per act
    contains: list = field(default_factory=list)        # contract_meta.contains, TL
    decision: str = "read"                              # read | skip | exclude
    reason: str | None = None

    @property
    def act_count(self) -> int:
        return len(self.acts)

    @property
    def is_repealed(self) -> bool:
        """True only when every act in the document is repealed. A mixed issue is read."""
        return bool(self.legal_statuses) and self.legal_statuses == {"repealed"}

    def decide(self) -> None:
        """Set decision and reason. Order matters: the worst problem wins."""
        flags = set(self.content_flags)

        if self.doc_id in TRANSLATION_NOT_SOURCE:
            self.decision, self.reason = "exclude", "translation_not_source"
            return
        if any(f.startswith(WRONG_INSTRUMENT_FLAGS) for f in flags):
            self.decision, self.reason = "exclude", "wrong_instrument"
            return
        if REPEAL_NOTICE_FLAG in flags:
            self.decision, self.reason = "exclude", "repeal_notice_only"
            return
        # Whatever `use` says. Malaysia's law table marks 90 repealed acts `use: evidence`
        # because _mark_use reads document_kind and never legal_status.
        if self.is_repealed:
            self.decision, self.reason = "exclude", "repealed"
            return

        if self.uses:
            readable = {u for u in self.uses
                        if u in READ_ANYWAY or not any(u.startswith(l) for l in LINKAGE_USES)}
            if not readable:
                self.decision = "skip"
                self.reason = "not_held" if self.uses == {"not held"} else "linkage"
                return
        self.decision, self.reason = "read", None

    def as_row(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "decision": self.decision,
            "reason": self.reason,
            "language_of_source": self.language,
            "language_source": self.language_source,
            "content_flags": sorted(self.content_flags),
            "use": sorted(self.uses),
            "document_kind": sorted(self.document_kinds),
            "legal_status": sorted(self.legal_statuses),
            "act_count": self.act_count,
        }


def _read_law_table(path: Path) -> dict[str, DocFacts]:
    facts: dict[str, DocFacts] = {}
    if not path.is_file():
        log.warning("no law_table.csv beside the corpus: %s", path)
        return facts
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            doc_id = (row.get("doc_id") or "").strip()
            if not doc_id:
                continue                       # a law the portal lists that the corpus lacks
            f = facts.setdefault(doc_id, DocFacts(doc_id=doc_id))
            for key, target in (("use", f.uses), ("document_kind", f.document_kinds),
                                ("legal_status", f.legal_statuses)):
                value = (row.get(key) or "").strip()
                if value:
                    target.add(value)
            if not f.language and (row.get("language") or "").strip():
                f.language = row["language"].strip()
                f.language_source = "law_table"
            f.acts.append(row)
    return facts


def _read_link_rows(path: Path, facts: dict[str, DocFacts]) -> None:
    """contract_meta.corpus.doc_id is the contract's join key (merge_corpus.py)."""
    if not path.is_file():
        log.warning("no links_used/documents.jsonl beside the corpus: %s", path)
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            meta = row.get("contract_meta") or {}
            doc_id = ((meta.get("corpus") or {}).get("doc_id") or "").strip()
            if not doc_id:
                continue
            f = facts.setdefault(doc_id, DocFacts(doc_id=doc_id))
            f.content_flags = list(meta.get("content_flags") or [])
            if meta.get("contains"):
                f.contains = meta["contains"]
            if meta.get("language") and not f.language:
                f.language = meta["language"]
                f.language_source = meta.get("language_source") or "link_row"
            elif meta.get("language") and f.language_source == "law_table":
                f.language_source = meta.get("language_source") or "portal_field"


def load_facts(corpus_dir: Path, registry_default_language: str | None = None,
               mismatch_language: str | None = None) -> dict[str, DocFacts]:
    """Join both sidecars and decide, per document, whether it is read.

    `registry_default_language` fills documents the crawler left blank; the contract calls
    that `registry_default` and it is a declared fallback, not a guess about the text.

    `mismatch_language` is the language of a file the crawler flagged `language_mismatch` -
    it read the label as one language and found the file was another. Reading that flag is
    reading a crawler field, so D3 holds; leaving the wrong label on would put a false
    Language of Source in the workbook.
    """
    facts = _read_law_table(corpus_dir / "law_table.csv")
    _read_link_rows(corpus_dir / "links_used" / "documents.jsonl", facts)
    for f in facts.values():
        if mismatch_language and "language_mismatch" in f.content_flags:
            f.language = mismatch_language
            f.language_source = "content_flag"
        elif not f.language and registry_default_language:
            f.language = registry_default_language
            f.language_source = "registry_default"
        f.decide()
    return facts


def summarise(facts: dict[str, DocFacts]) -> dict:
    counts: dict[str, int] = {}
    reasons: dict[str, int] = {}
    for f in facts.values():
        counts[f.decision] = counts.get(f.decision, 0) + 1
        if f.reason:
            reasons[f.reason] = reasons.get(f.reason, 0) + 1
    return {"decisions": counts, "reasons": reasons, "documents": len(facts)}
