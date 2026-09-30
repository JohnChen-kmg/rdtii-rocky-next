"""Provision-Record assembly: deterministic fields + grounded metadata + LLM soft tags.

Split by reliability (PLAN.md section 2.6):
- everything mechanically derivable is deterministic (offsets, snippet bytes,
  contexts, locators, carried provenance);
- law_name / law_number / last_amended are GROUNDED like the snippet (2.6b):
  regex-first over the frozen text, value bytes copied from the text, offsets
  persisted, null-if-ungrounded - never a free-text LLM guess;
- only scope / data_type / obligation_type / extraction_confidence come from
  the LLM, as non-exclusive soft hints (2.6a), via get_llm().complete().
  The LLM never emits quoted bytes or offsets.
"""

from __future__ import annotations

import bisect
import logging
import re
import time
from dataclasses import dataclass
from typing import Any

from config.llm.base import LLMClient
from rdtii_p2 import ground
from rdtii_p2.segment import SegmentResult, Span

log = logging.getLogger("rdtii_p2.extract")

OBLIGATION_TYPES = [
    "ban", "storage", "infrastructure", "conditional", "retention_minimum",
    "dp_framework", "cybersecurity", "dpia_dpo", "gov_access", "other",
]

TAG_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "scope": {"type": "string", "enum": ["horizontal", "sectoral"]},
        "data_type": {"type": "string", "enum": ["personal", "non-personal"]},
        "obligation_type": {"type": "string", "enum": OBLIGATION_TYPES},
        "extraction_confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": ["scope", "data_type", "obligation_type", "extraction_confidence"],
}

# Snippets longer than this are cut back to the last sentence boundary - the
# bytes remain an exact substring; the cut is logged by the caller.
SNIPPET_MAX_CHARS = 1500
# Contract 3.2 permits dropping a record ONLY when no faithful snippet can be
# produced - a short provision ("The Former Commission is dissolved.") is
# still a provision, so only empty/whitespace-only spans are skipped.
SNIPPET_MIN_CHARS = 1

# no ^ anchor: Pattern.match(text, pos) anchors at pos, and ^ would only ever
# match at pos 0 (MULTILINE is not set)
_MARKER = re.compile(r"\s*(?:\d{1,3}[A-Z]{0,2}\.\s*[—–-]?\s*)?(?:\(\d+[A-Z]?\)\s*)?")
_SHORT_TITLE = re.compile(
    r"This Act (?:is|may be cited as) the ([A-Z][^.\n]{3,90}?Act(?:[ ,]?\d{4})?)"
)
_AMENDED_UP_TO = re.compile(
    r"amendments up to (?:and including )?(\d{1,2} \w+ \d{4})"
)
# AU compilations: "Includes amendments: Act No. 53, 2026" - ground the year
_AMENDED_INCLUDES = re.compile(r"Includes amendments:[^\n]*?(\d{4})")
# the numeral must not be a year: 'Legislation Act 2003' is a TITLE, not
# 'Act No. 2003' - reject 18xx/19xx/20xx unless followed by 'of <year>'
_ACT_NUMBER = re.compile(
    r"\b(?:Act|Ordinance)\s+(?:No\.\s*)?(?!(?:1[89]|20)\d{2}\b)\d+(?:\s+of\s+\d{4})?\b")
# a law-number match on one of these lines refers to an AMENDING act, not the
# principal act - grounded-but-wrong is worse than null
_AMENDMENT_CONTEXT = re.compile(
    r"(?i)includes amendments|amendments up to|as amended|amended by|wef ")


@dataclass
class GroundedField:
    value: str | None
    char_start: int | None = None
    char_end: int | None = None


@dataclass
class DocMetadata:
    law_name: GroundedField
    law_number: GroundedField
    last_amended: GroundedField


# ------------------------------------------------------- grounded metadata ----

def _field_from_match(text: str, start: int, end: int) -> GroundedField:
    return GroundedField(value=text[start:end], char_start=start, char_end=end)


def ground_law_name(text: str, guess: str | None) -> GroundedField:
    match = _SHORT_TITLE.search(text)
    if match:
        return _field_from_match(text, match.start(1), match.end(1))
    if guess:
        position = text.find(guess)
        if position != -1:
            return _field_from_match(text, position, position + len(guess))
        # masthead prints titles in ALL CAPS, often line-wrapped
        collapsed = re.sub(r"\s+", " ", text[:3000]).upper()
        if guess.upper() in collapsed:
            # groundable in folded form only - fall through to honest null
            log.info("law_name only matches case/whitespace-folded masthead; leaving null")
    return GroundedField(value=None)


def ground_law_number(text: str, guess: str | None) -> GroundedField:
    def excluded(position: int) -> bool:
        line_start = text.rfind("\n", 0, position) + 1
        line_end = text.find("\n", position)
        line = text[line_start:line_end if line_end != -1 else len(text)]
        return text.find("[", line_start, position) != -1 or bool(
            _AMENDMENT_CONTEXT.search(line))

    if guess:
        for match in re.finditer(re.escape(guess), text):
            if not excluded(match.start()):
                return _field_from_match(text, match.start(), match.end())
    for match in _ACT_NUMBER.finditer(text[:5000]):
        if not excluded(match.start()):
            return _field_from_match(text, match.start(), match.end())
    return GroundedField(value=None)


def ground_last_amended(text: str) -> GroundedField:
    match = _AMENDED_UP_TO.search(text) or _AMENDED_INCLUDES.search(text)
    if match:
        return _field_from_match(text, match.start(1), match.end(1))
    return GroundedField(value=None)


def ground_doc_metadata(text: str, law_name_guess: str | None,
                        law_number_guess: str | None) -> DocMetadata:
    return DocMetadata(
        law_name=ground_law_name(text, law_name_guess),
        law_number=ground_law_number(text, law_number_guess),
        last_amended=ground_last_amended(text),
    )


# ------------------------------------------------------------ URL compose ----

def compose_url(base: str, anchor_hint: str | None, anchor_kind: str | None) -> str:
    """Contract section 3.6: deterministic deep-link composition."""
    if not anchor_hint or not anchor_kind or anchor_kind == "none":
        return base
    if anchor_kind == "query":
        suffix = anchor_hint.lstrip("?&")
        joiner = "&" if "?" in base else "?"
        return f"{base}{joiner}{suffix}"
    if anchor_kind == "fragment":
        return base + (anchor_hint if anchor_hint.startswith("#") else f"#{anchor_hint}")
    raise ValueError(f"unknown anchor_kind {anchor_kind!r}")


# ----------------------------------------------------------------- LLM tags ----

# Shared verbatim by the single and batched prompts so batching never shifts
# the tag definitions the models were validated against (s.26(1) golden case).
_TAG_DEFINITIONS = (
    "Definitions:\n"
    "- scope: 'horizontal' if the INSTRUMENT applies economy-wide across "
    "sectors; 'sectoral' if it governs one sector (banking, telecom, ...).\n"
    "- data_type: what data the provision governs ('personal' vs 'non-personal').\n"
    "- obligation_type: ban (transfer prohibited OUTRIGHT, no exceptions or "
    "conditions / local processing mandated) | storage (domestic copy required) "
    "| infrastructure (local servers/data centres required) | conditional "
    "(transfer restricted by default BUT allowed under conditions such as "
    "consent/adequacy/contract/approval/prescribed requirements) | "
    "retention_minimum (data must be kept AT LEAST some period) | dp_framework "
    "(general data-protection framework provision) | cybersecurity "
    "(cybersecurity framework provision) | dpia_dpo (DPIA duty or DPO "
    "appointment) | gov_access (government access to data) | other.\n\n"
    "DECISION RULE for ban vs conditional: if the prohibition contains ANY "
    "escape clause ('except', 'unless', 'subject to', 'in accordance with "
    "requirements/regulations', 'with consent/approval'), it is 'conditional', "
    "never 'ban'. 'ban' is reserved for absolute prohibitions with no lawful "
    "route to transfer.\n\n"
    "SCOPE RULE for ban/storage/infrastructure/conditional: these four classes "
    "describe CROSS-BORDER data-transfer or data-localisation rules only. An "
    "absolute prohibition that is not about moving/keeping data across borders "
    "(an offence, a conduct rule, a consent rule) is dp_framework or other - "
    "never 'ban'.\n\n"
)


def _provision_block(span: Span, snippet: str, context_before: str) -> str:
    return (
        f"Provision: {span.article_section}"
        + (f" ({span.heading})" if span.heading else "") + "\n"
        f"Hierarchy: {' > '.join(span.hierarchy)}\n"
        f"Preceding context: ...{context_before[-150:]}\n"
        f"Provision text:\n{snippet[:800]}\n"
    )


def _tag_prompt(law_name: str | None, span: Span, snippet: str,
                context_before: str) -> str:
    return (
        "You are tagging one provision of a statute for a legal-data pipeline. "
        "These tags are coarse routing hints only; a downstream system makes all "
        "real decisions. If you are not confident about obligation_type, use "
        '"other" and lower extraction_confidence.\n\n'
        + _TAG_DEFINITIONS
        + f"Law: {law_name or 'unknown'}\n"
        + _provision_block(span, snippet, context_before)
    )


def _normalize_tags(result: dict[str, Any]) -> dict[str, Any]:
    """Every enum is guarded: forced tool use does NOT hard-guarantee enum
    values (real batch results contained '<UNKNOWN>' and 'sectral'). An
    invalid value falls back to the safe default and caps confidence at 0.3
    so downstream widens rather than trusts."""
    scope = result.get("scope")
    data_type = result.get("data_type")
    obligation = result.get("obligation_type")
    confidence = result.get("extraction_confidence")
    valid = (scope in ("horizontal", "sectoral")
             and data_type in ("personal", "non-personal")
             and obligation in OBLIGATION_TYPES)
    normalized = round(min(max(float(confidence), 0.0), 1.0), 2) if confidence is not None else None
    if not valid and normalized is not None:
        normalized = min(normalized, 0.3)
    return {
        "scope": scope if scope in ("horizontal", "sectoral") else "horizontal",
        "data_type": data_type if data_type in ("personal", "non-personal") else "personal",
        "obligation_type": obligation if obligation in OBLIGATION_TYPES else "other",
        "extraction_confidence": normalized,
    }


def llm_tags(llm: LLMClient, law_name: str | None, span: Span, snippet: str,
             context_before: str) -> dict[str, Any]:
    try:
        result = llm.complete(_tag_prompt(law_name, span, snippet, context_before), TAG_SCHEMA)
        return _normalize_tags(result)
    except Exception as exc:
        log.warning("%s: LLM tagging failed (%s) - emitting other/low-confidence", span.article_section, exc)
        return {"scope": "horizontal", "data_type": "personal",
                "obligation_type": "other", "extraction_confidence": 0.0}


# TagItem: (span, snippet, context_before) - everything one provision's prompt needs.
TagItem = tuple[Span, str, str]


def _batch_tag_prompt(law_name: str | None, items: list[TagItem]) -> str:
    blocks = [
        f"--- id: {span.article_section}\n" + _provision_block(span, snippet, before)
        for span, snippet, before in items
    ]
    return (
        f"You are tagging {len(items)} provisions of one statute for a legal-data "
        "pipeline. These tags are coarse routing hints only; a downstream system "
        "makes all real decisions. If you are not confident about a provision's "
        'obligation_type, use "other" and lower its extraction_confidence.\n\n'
        + _TAG_DEFINITIONS
        + 'Return JSON with key "provisions": an array containing EXACTLY one '
        "entry per provision below, in the same order, each carrying its \"id\" "
        "copied verbatim. Judge every provision independently.\n\n"
        f"Law: {law_name or 'unknown'}\n\n"
        + "\n".join(blocks)
    )


def _batch_schema(ids: list[str]) -> dict[str, Any]:
    item = {
        "type": "object",
        "properties": {"id": {"type": "string", "enum": sorted(set(ids))},
                       **TAG_SCHEMA["properties"]},
        "required": ["id", *TAG_SCHEMA["required"]],
    }
    return {
        "type": "object",
        "properties": {"provisions": {"type": "array", "items": item}},
        "required": ["provisions"],
    }


def match_batch_entries(ids: list[str], entries: list[dict[str, Any]]
                        ) -> list[dict[str, Any]] | None:
    """Map a batch response onto `ids` order: by id when ids round-trip cleanly,
    by order when only the count matches, None when unrecoverable."""
    by_id = {entry.get("id"): entry for entry in entries}
    if len(entries) == len(ids) == len(by_id) and set(by_id) == set(ids):
        return [_normalize_tags(by_id[i]) for i in ids]
    if len(entries) == len(ids):
        log.warning("batch tag ids inconsistent - mapping %d entries by order", len(ids))
        return [_normalize_tags(entry) for entry in entries]
    return None


def _tag_chunk(llm: LLMClient, law_name: str | None, chunk: list[TagItem]) -> list[dict[str, Any]]:
    ids = [span.article_section for span, _, _ in chunk]
    try:
        result = llm.complete(_batch_tag_prompt(law_name, chunk), _batch_schema(ids))
        entries = result["provisions"]
        matched = match_batch_entries(ids, entries)
        if matched is None:
            raise ValueError(f"batch returned {len(entries)} entries for {len(ids)} provisions")
        return matched
    except Exception as exc:
        log.warning("batch tagging failed (%s) - falling back to one-provision calls "
                    "for %d provisions", exc, len(chunk))
        return [llm_tags(llm, law_name, span, snippet, before)
                for span, snippet, before in chunk]


def llm_tags_batch(llm: LLMClient, law_name: str | None, items: list[TagItem],
                   batch_size: int) -> list[dict[str, Any]]:
    """Tag provisions `batch_size` per LLM call - prompt processing dominates
    per-call latency, so packing provisions shares it. Worst case (malformed
    batch response) degrades chunk-by-chunk to the proven single-call path.
    batch_size<=1 IS the single-call path (byte-identical prompts)."""
    size = max(1, batch_size)
    tags: list[dict[str, Any]] = []
    for chunk_start in range(0, len(items), size):
        chunk = items[chunk_start:chunk_start + size]
        if size == 1 or len(chunk) == 1:
            tags.extend(llm_tags(llm, law_name, span, snippet, before)
                        for span, snippet, before in chunk)
        else:
            tags.extend(_tag_chunk(llm, law_name, chunk))
        if chunk_start and (chunk_start // size) % 10 == 0:
            log.info("tagging: %d/%d provisions done", len(tags), len(items))
    return tags


# ------------------------------------------------------------ record build ----

def candidate_spans(segmented: SegmentResult) -> list[Span]:
    """One candidate per provision: subsections, plus sections with no subsections.

    "Has subsections" is decided by POSITION, not by citation. It used to be a set of
    `hierarchy[-2]` - the parent article's citation string - which is only safe while every
    article in a document has a distinct number. A Timorese gazette issue holds many acts and
    each restarts at Artigo 1, so once article numbers stopped being silently renumbered into
    one ascending run (2026-09-23), act 2's "Art. 1" began matching act 1's "Art. 1" and was
    dropped as though it had subsections of its own: **11,999 provisions disappeared from
    Timor-Leste without a single drop being logged**, because a filtered candidate is never
    a record and so is never reported as dropped. A character range belongs to one act.
    """
    starts = sorted(span.char_start for span in segmented.spans
                    if span.unit == "subsection")

    def has_subsection(section: Span) -> bool:
        index = bisect.bisect_left(starts, section.char_start)
        return index < len(starts) and starts[index] < section.char_end

    candidates = []
    for span in segmented.spans:
        if span.unit == "subsection":
            candidates.append(span)
        elif span.unit == "section" and not has_subsection(span):
            candidates.append(span)
    return candidates


def snippet_offsets(text: str, span: Span) -> tuple[int, int]:
    """Trim the leading '26.—(1) ' marker and trailing whitespace; long spans
    are cut back to the last sentence boundary before SNIPPET_MAX_CHARS."""
    marker = _MARKER.match(text, span.char_start, span.char_end)
    start = marker.end() if marker else span.char_start
    end = span.char_end
    while end > start and text[end - 1] in " \n\t":
        end -= 1
    if end - start > SNIPPET_MAX_CHARS:
        window = text[start:start + SNIPPET_MAX_CHARS]
        cut = max(window.rfind(". "), window.rfind(".\n"), window.rfind(";\n"))
        end = start + (cut + 1 if cut > 40 else SNIPPET_MAX_CHARS)
    return start, end


# ISO 639-3 to the name the workbook's Language of Source column asks for:
# "Thai, Vietnamese, Bahasa Indonesia, Russian, English".
_LANGUAGE_NAMES = {
    "eng": "English", "lao": "Lao", "por": "Portuguese", "zho": "Chinese",
    "msa": "Malay", "tet": "Tetum", "ind": "Bahasa Indonesia", "tha": "Thai",
    "vie": "Vietnamese", "rus": "Russian", "hin": "Hindi", "mon": "Mongolian",
}


def _language_name(code: str | None) -> str | None:
    if not code:
        return None
    return _LANGUAGE_NAMES.get(code, code)


def _fact(facts, attribute: str, default=None):
    """Read one collection fact, or the default when no sidecar row exists."""
    if facts is None:
        return default
    value = getattr(facts, attribute, None)
    return default if value is None else value


def _provision_id(doc_id: str, act, article_section: str) -> str:
    """<doc_id>#<section>, or <doc_id>#a<n>#<section> when a document holds several acts.

    Without the act index two acts in one gazette issue collide: tl-ldcn-001 carries both
    Lei 1/2026 and Decreto-Lei 13/2026, and both have an Article 6.
    """
    index = (act or {}).get("act_index")
    if index:
        return f"{doc_id}#a{index}#{article_section}"
    return f"{doc_id}#{article_section}"


def stamp_tagging_model(record: dict[str, Any], model: str, confidence) -> None:
    """Record which model tagged a provision, and keep the OCR engine beside it.

    `model_version` is rebuilt from the record's own `ocr_engine` rather than parsed out of
    the old value. An untagged record's `model_version` is just "tesseract-lao" with no "+",
    so splitting on "+" and keeping the tail would silently drop the OCR engine the moment a
    tagger was stamped over it - the provenance would go backwards as tagging improved.
    """
    record["extraction_model"] = model
    record["tags_source"] = "llm_failed" if confidence == 0.0 else "llm"
    # `ocr_engine` is the field of record; the old "<model>+<engine>" string is the fallback
    # so a provisions.jsonl written before that field existed still keeps its engine.
    engine = record.get("ocr_engine") or (record.get("model_version") or "").partition("+")[2]
    parts = [part for part in (model, engine) if part]
    record["model_version"] = "+".join(parts)


def build_record(
    *,
    text: str,
    span: Span,
    row: dict[str, Any],
    metadata: DocMetadata,
    source_type_final: str,
    pdf_is_scanned_final: bool | None,
    snippet_source: str,
    page_for_offset,
    llm: LLMClient | None,
    settings,
    ocr_quality_cer: float | None = None,
    facts=None,
    act=None,
    ocr_cer_method: str | None = None,
    ocr_script: str | None = None,
    ocr_engine: str | None = None,
    source_url: str | None = None,
    tagging_model: str | None = None,
    language: str | None = None,
) -> dict[str, Any] | None:
    """Assemble one Provision-Record; returns None (and logs) if grounding fails."""
    started = time.monotonic()
    start, end = snippet_offsets(text, span)
    if end - start < SNIPPET_MIN_CHARS:
        log.info("%s: span too short after trim (%d chars) - skipped",
                 span.article_section, end - start)
        return None
    grounded = ground.copy_grounded(text, start, end)
    try:
        ground.verify(text, grounded.char_start, grounded.char_end, grounded.snippet)
    except ground.GroundingError as exc:
        log.error("%s: DROPPED - %s", span.article_section, exc)
        return None

    # No model ran means no judgement exists, and the record has to say so. Until
    # 2026-09-23 this branch filled horizontal/personal/other and still stamped
    # `settings.llm_model`, so 492,178 provisions across four economies asserted that
    # qwen2.5:14b had judged them when nothing had run at all. A placeholder that is
    # indistinguishable from a finding is worse than an empty field: it does not look
    # like a gap, it looks like an answer.
    if llm is not None:
        tags = llm_tags(llm, metadata.law_name.value or row.get("law_name_guess"),
                        span, grounded.snippet, grounded.context_before)
        tags_source = "llm_failed" if tags.get("extraction_confidence") == 0.0 else "llm"
        tagging_model = tagging_model or settings.llm_model
    else:
        tags = {"scope": None, "data_type": None,
                "obligation_type": None, "extraction_confidence": None}
        tags_source = "not_tagged"
        tagging_model = None

    # the crawler's per-document language wins; `language` is the economy's declared
    # default, used where a corpus has no sidecar at all (China has neither law_table.csv
    # nor links_used/, so every fact is absent and the field would otherwise be null while
    # the segmenter was already using the declared language)
    _resolved_language = _fact(facts, "language") or language

    page = page_for_offset(span.char_start)
    location_parts = [level for level in span.hierarchy[:-1] if not level.startswith("(")]
    location = ", ".join(location_parts + ([f"p.{page}"] if page else []))

    # model_version names only what actually touched this record: the tagger if one ran,
    # the OCR engine if the text came from pixels, and nothing when neither did.
    parts = [part for part in (tagging_model,
                               ocr_engine if ocr_quality_cer is not None else None) if part]
    model_version = "+".join(parts) if parts else None

    record = {
        # the version THIS build produced the record against (contract 3.9),
        # not the manifest row's version (which may be an older MINOR)
        "contract_version": settings.contract_version,
        "instrument_version": row.get("instrument_version"),
        "provision_id": _provision_id(row["doc_id"], act, span.article_section),
        "doc_id": row["doc_id"],
        "economy": row["economy"],
        "law_name": metadata.law_name.value or row["law_name_guess"],
        "law_name_grounded": metadata.law_name.value is not None,
        "law_name_char_start": metadata.law_name.char_start,
        "law_name_char_end": metadata.law_name.char_end,
        "law_number": (act or {}).get("law_number") or metadata.law_number.value,
        "law_number_char_start": metadata.law_number.char_start,
        "law_number_char_end": metadata.law_number.char_end,
        "last_amended": metadata.last_amended.value,
        "last_amended_char_start": metadata.last_amended.char_start,
        "last_amended_char_end": metadata.last_amended.char_end,
        "article_section": span.article_section,
        "verbatim_snippet": grounded.snippet,
        "snippet_char_start": grounded.char_start,
        "snippet_char_end": grounded.char_end,
        "snippet_source": snippet_source,
        "location_reference": location or None,
        "source_url": source_url or compose_url(row["source_url"], row.get("anchor_hint"),
                                                row.get("anchor_kind")),
        "raw_context_before": grounded.context_before,
        "raw_context_after": grounded.context_after,
        "scope": tags["scope"],
        "data_type": tags["data_type"],
        "obligation_type": tags["obligation_type"],
        "extraction_confidence": tags["extraction_confidence"],
        # "llm" | "llm_failed" | "not_tagged" - which of the three the four fields above
        # are, without having to infer it from a null confidence
        "tags_source": tags_source,
        # --- the act, when one document holds several (a Timorese gazette issue holds
        # up to 39, and two acts in one issue can both have an Article 6)
        "act_index": (act or {}).get("act_index"),
        # authoritative from the sidecar even when the offsets could not be located, so a
        # reader can tell "one act" from "several acts we could not separate"
        "act_count": (act or {}).get("act_count", 1),
        "law_name_en": (act or {}).get("law_name_en"),
        "law_name_original": (act or {}).get("law_name_original")
                             or metadata.law_name.value or row["law_name_guess"],
        "law_name_en_source": (act or {}).get("law_name_en_source"),
        # --- how the article number was arrived at
        "article_number_as_read": getattr(span, "number_as_read", None),
        "citation_confidence": getattr(span, "citation_confidence", "exact"),
        "citation_repair_method": getattr(span, "citation_repair_method", None),
        "page": page,
        # --- what collection knew: read, never detected (D3)
        "language_of_source": _resolved_language,
        "language_of_source_name": _language_name(_resolved_language),
        # never "detected": either the crawler declared it per document (D3), or the
        # economy declared it for the corpus, and the record says which
        "language_source": (_fact(facts, "language_source")
                            or ("economy_default" if _resolved_language else None)),
        "collection_channel": _fact(facts, "collection_channel", "portal_crawl"),
        "in_official_database": _fact(facts, "in_official_database", True),
        "source_authority": _fact(facts, "source_authority"),
        "collection_note": _fact(facts, "collection_note"),
        "provenance_ref": _fact(facts, "provenance_ref"),
        "content_flags": sorted(getattr(facts, "content_flags", []) or []),
        "document_kind": sorted(getattr(facts, "document_kinds", []) or []) or None,
        "legal_status": sorted(getattr(facts, "legal_statuses", []) or []) or None,
        "use": sorted(getattr(facts, "uses", []) or []) or None,
        "ocr_cer_method": ocr_cer_method,
        "ocr_script": ocr_script,
        "source_file_path": row["local_path"],
        "source_type": source_type_final,
        "pdf_is_scanned": pdf_is_scanned_final,
        "ocr_quality_cer": ocr_quality_cer,
        "ocr_engine": ocr_engine,
        "retrieval_method": row["retrieval_method"],
        "extraction_model": tagging_model,
        "model_version": model_version,
        "access_date": row["access_date"],
        "processing_time_seconds": None,  # set below, after all work for this record
    }
    record["processing_time_seconds"] = round(time.monotonic() - started, 3)
    return record
