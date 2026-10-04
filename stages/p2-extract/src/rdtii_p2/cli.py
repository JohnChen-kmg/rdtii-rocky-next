"""p2-extract CLI - run | validate | demo | pilot (contract section 5.3).

`run` is fully non-interactive: entry gates (schema, contract-MAJOR, env
preflight) fail loudly before any work; every stage streams one narration line
per meaningful decision to stdout and mirrors a structured copy to
logs/run_<ts>.jsonl (contract section 9.1).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from config.settings import Settings, load_settings
from rdtii_p2 import (acts, emit, extract_fields, ground, parse_pdf_native, router,
                      segment, segment_civil)
from config.ocr import langmap
from rdtii_p2 import ocr_cache, ocr_prepass
from rdtii_p2.ingest import (IngestError, Manifest, ManifestRow, is_superseded,
                             load_manifest, preflight)
from rdtii_p2.normalize import NormalizedDoc, normalize_pages
from rdtii_p2.sidecars import DocFacts, load_facts
from rdtii_p2.status import DocStatus

log = logging.getLogger("rdtii_p2")


# ---------------------------------------------------------------- logging ----

class _JsonlHandler(logging.Handler):
    def __init__(self, path: Path):
        super().__init__()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(path, "a", encoding="utf-8", newline="\n")

    def emit(self, record: logging.LogRecord) -> None:
        entry = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        self._fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._fh.flush()


def _setup_logging() -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    # ollama's httpx logs one line per REST call - noise, not narration (9.1)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter("[P2] %(message)s"))
    root.addHandler(console)
    root.addHandler(_JsonlHandler(Path("logs") / f"run_{stamp}.jsonl"))


# -------------------------------------------------------------------- run ----

def _select_rows(manifest: Manifest, only_doc: str | None, economy: str | None,
                 only_docs_file: str | None = None) -> list[ManifestRow]:
    rows = manifest.rows
    if only_doc:
        rows = [r for r in rows if r.data["doc_id"] == only_doc]
        if not rows:
            raise IngestError(f"--only-doc {only_doc}: not in manifest")
    if only_docs_file:
        wanted = {line.strip() for line in
                  Path(only_docs_file).read_text(encoding="utf-8").splitlines()
                  if line.strip()}
        rows = [r for r in rows if r.data["doc_id"] in wanted]
        if not rows:
            raise IngestError(f"--only-docs {only_docs_file}: no doc_ids matched")
    if economy:
        rows = [r for r in rows if r.data["economy"] == economy.upper()]
        if not rows:
            raise IngestError(f"--economy {economy}: no manifest rows")
    return rows


# kickoff decision #3: OCR the scanned lane in priority order - keyword-hot
# titles first, the rest afterwards; non-scanned docs are cheap and go first.
_PRIORITY_KEYWORDS = (
    "personal data", "data protection", "communication", "multimedia",
    "electronic", "computer", "cyber", "telecommunication", "digital",
    "information", "privacy", "security",
)


def _fact_columns(fact: DocFacts) -> dict:
    """The collection facts a doc_status row carries, in the shape DocStatus expects."""
    return {
        "language_of_source": fact.language,
        "language_source": fact.language_source,
        "content_flags": sorted(fact.content_flags),
        "use": sorted(fact.uses),
        "document_kind": sorted(fact.document_kinds),
        "legal_status": sorted(fact.legal_statuses),
        "act_count": fact.act_count,
    }


def _scanned_rank(row: ManifestRow) -> tuple[int, int]:
    if row.data["source_type"] != "pdf_scanned":
        return (0, 0)
    title = (row.data.get("law_name_guess") or "").lower()
    return (1, 0 if any(k in title for k in _PRIORITY_KEYWORDS) else 1)


def _segment_for(text: str, language: str | None, economy_language: str | None = None) -> segment.SegmentResult:
    """Pick the segmenter by the document's declared language, never by sniffing the text.

    English keeps `segment.py` untouched, so the Round 1 corpus stays the regression
    baseline. Everything else goes to the profile for its legal tradition; an unknown
    language falls back to the common-law segmenter and says so, because emitting nothing
    is worse than emitting what the old path would have emitted.
    """
    if language in segment_civil.PROFILES and language != segment_civil.ENGLISH_ARTICLES:
        return segment_civil.segment_civil(text, language)
    if (language == "eng" and economy_language in segment_civil.PROFILES
            and economy_language != segment_civil.ENGLISH_ARTICLES):
        # Declared English, in an economy whose own language is written in articles: the publisher's
        # English edition of such a law ("Article 12"). Both facts are declared (the crawler's language
        # for the file, the economy's language for the run); the text is not sniffed. When that profile
        # finds nothing, the common-law segmenter below still gets its turn, as before.
        result = segment_civil.segment_civil(text, segment_civil.ENGLISH_ARTICLES)
        if result.n_sections:
            return result
    if language not in (None, "eng", "msa"):
        log.warning("no segmenter profile for language %r - using the common-law segmenter",
                    language)
    return segment.segment(text)


def _parse_doc(doc_id: str, decision: router.Route, local_path: Path, source_url: str,
               settings: Settings, out_dir: Path, force: bool = False,
               language: str | None = None, economy_language: str | None = None
               ) -> tuple[NormalizedDoc, segment.SegmentResult, dict[str, str] | None,
                          dict | None]:
    """Lane A/B/C parsing + segmentation. NOTHING is written to disk here -
    source_text is frozen only after extraction succeeds (rerun safety).
    Fourth element is lane C OCR metadata (engine, preprocessing) or None."""
    if decision.lane == "D":
        from rdtii_p2 import parse_docx

        doc = parse_docx.extract(local_path)
        log.info("%s: lane D read %d paragraph(s), %d table(s) -> %d chars",
                 doc_id, doc.paragraphs, doc.tables, len(doc.text))
        normalized = normalize_pages([doc.text])
        segmented = _segment_for(normalized.text, language, economy_language)
        return normalized, segmented, None, None
    if decision.lane == "B":
        raw_pages = parse_pdf_native.extract_pages(local_path)
        log.info("%s: lane B extracted %d pages (pypdfium2)", doc_id, len(raw_pages))
        normalized = normalize_pages(raw_pages)
        segmented = _segment_for(normalized.text, language, economy_language)
        return normalized, segmented, None, None
    if decision.lane == "A":
        from rdtii_p2 import parse_html

        html_doc = parse_html.parse(local_path, source_url)
        log.info("%s: lane A parsed -> %d chars, %d spans, %d anchors",
                 doc_id, len(html_doc.text), len(html_doc.spans), len(html_doc.anchors))
        if not html_doc.spans and html_doc.text.strip():
            # Word-export instruments that number paragraphs as literal text
            # ("15. An APRA-regulated entity must...") carry no DOM section
            # markup at all - the generic segmenter already handles that
            # numbering (it segments the same instruments' PDF twins)
            segmented = _segment_for(html_doc.text, language, economy_language)
            log.info("%s: lane A found no DOM sections - generic segmenter "
                     "fallback: %d sections, %d spans",
                     doc_id, segmented.n_sections, len(segmented.spans))
        else:
            segmented = segment.SegmentResult(
                spans=html_doc.spans,
                n_sections=sum(1 for s in html_doc.spans if s.unit == "section"),
            )
        return NormalizedDoc(text=html_doc.text), segmented, html_doc.anchors, None
    if decision.lane == "C":
        from config.ocr.factory import get_ocr

        cached = None if force else emit.read_normalized(out_dir, doc_id)
        if cached is not None:
            # kickoff decision #3: OCR once, cache forever in source_text/
            log.info("%s: lane C using cached OCR text (%d chars) - re-OCR with --force",
                     doc_id, len(cached.text))
            ocr_meta = {"engine": settings.ocr_engine, "preprocessing": ["cached"],
                        "cached": True}
            return cached, _segment_for(cached.text, language, economy_language), None, ocr_meta
        # the pre-pass has almost always been here first: `p2-extract ocr` fills a
        # per-page cache in parallel, keyed on the file's sha256, the engine, the language
        # and the DPI, so nothing is re-read because the normaliser changed
        pack = langmap.pack_for(language)
        pages = None
        if not force and local_path.is_file():
            # the key includes the file's own hash, so a re-crawled document re-OCRs by
            # itself; a file that is not there cannot be hashed, and the engine below
            # will report its absence
            meta = ocr_cache.DocCache(
                doc_id=doc_id, content_sha256=ocr_cache.file_sha256(local_path),
                engine=f"tesseract-{pack}", language=language or "eng",
                dpi=ocr_prepass.RENDER_DPI)
            pages = ocr_cache.read(out_dir, doc_id, meta)
        if pages is not None:
            log.info("%s: lane C using %d cached OCR page(s) (%s)", doc_id, len(pages), pack)
            normalized = normalize_pages(pages)
            segmented = _segment_for(normalized.text, language, economy_language)
            return normalized, segmented, None, {"engine": f"tesseract-{pack}",
                                                 "preprocessing": ["cached"], "cached": True}
        engine = get_ocr(settings, language=language)
        result = engine.to_text(local_path)
        log.info("%s: lane C OCR'd %d pages (%s)", doc_id, len(result.pages), result.engine)
        normalized = normalize_pages([page.text for page in result.pages])
        segmented = _segment_for(normalized.text, language, economy_language)
        ocr_meta = {"engine": result.engine, "preprocessing": result.preprocessing,
                    "cached": False}
        return normalized, segmented, None, ocr_meta
    raise ValueError(f"unknown lane {decision.lane!r}")


def _extract_doc(doc_id: str, row: ManifestRow, decision: router.Route,
                 normalized: NormalizedDoc, segmented: segment.SegmentResult,
                 llm, settings: Settings, out_dir: Path,
                 anchors: dict[str, str] | None = None,
                 ocr_quality_cer: float | None = None,
                 ocr_engine: str | None = None,
                 facts=None,
                 ocr_cer_method: str | None = None,
                 ocr_script: str | None = None,
                 language: str | None = None
                 ) -> tuple[list[dict], extract_fields.DocMetadata, list[dict]]:
    """T3-T5: grounded metadata + per-provision records + grounding gate.
    Also returns tag_inputs rows (the Batches-lane sidecar; llm=None defers tags)."""
    metadata = extract_fields.ground_doc_metadata(
        normalized.text, row.data.get("law_name_guess"), row.data.get("law_number_guess"))
    log.info("%s: metadata law_name=%r law_number=%r last_amended=%r",
             doc_id, metadata.law_name.value, metadata.law_number.value,
             metadata.last_amended.value)
    candidates = extract_fields.candidate_spans(segmented)

    # Where each act the sidecar names begins. Only used when EVERY act was located at a
    # distinct offset: a partial split folds a missed act's articles into the act before it
    # and attributes them to the wrong law, which is worse than leaving act_index null.
    act_spans: list = []
    act_total = getattr(facts, "act_count", 1) or 1
    # where each candidate's own ARTICLE heading starts. A subsection belongs to its article,
    # and if the two fall in different acts the provision straddles a boundary: a Timorese
    # resolution numbers its items "1. 2. 3." with no Artigo at all, so the segmenter attaches
    # them to the last article it saw, which can be in the act before. Neither act is a safe
    # answer, so that provision's act_index is withheld rather than guessed.
    article_start: dict[int, int] = {}
    _last_section = None
    for _span in segmented.spans:
        if _span.unit == "section":
            _last_section = _span.char_start
        article_start[id(_span)] = (_last_section if _last_section is not None
                                    else _span.char_start)
    if act_total > 1:
        act_spans, located = acts.locate(normalized.text, getattr(facts, "acts", []))
        if act_spans:
            log.info("%s: %d acts located, provisions split per act", doc_id, len(act_spans))
        else:
            log.info("%s: %d of %d acts located - act_index withheld (completeness gate)",
                     doc_id, located, act_total)

    records: list[dict] = []
    straddling = 0
    tag_items: list[extract_fields.TagItem] = []
    dropped = 0
    # consolidated statutes restart numbering per schedule/bundled instrument:
    # the citation stays honest, the record id gets a ~n disambiguator
    seen_citations: dict[str, int] = {}
    for span in candidates:
        deep_url = None
        if anchors and span.article_section in anchors:
            deep_url = extract_fields.compose_url(
                row.data["source_url"], f"#{anchors[span.article_section]}", "fragment")
        act = None
        if act_spans:
            located_act = acts.act_at(act_spans, span.char_start)
            heading_act = acts.act_at(act_spans, article_start.get(id(span), span.char_start))
            if located_act is not None and heading_act is not None                     and located_act.index != heading_act.index:
                straddling += 1
                located_act = None      # ambiguous: withheld, not guessed
            if located_act is not None:
                act = {"act_index": located_act.index, "act_count": len(act_spans),
                       "law_name_original": located_act.law_name,
                       "law_number": located_act.law_number,
                       "document_kind": located_act.document_kind}
        elif act_total > 1:
            # the count is authoritative even when the offsets are not: mapping can see
            # that this document holds several acts and discount a single attribution
            act = {"act_count": act_total}
        record = extract_fields.build_record(
            text=normalized.text, span=span, row=row.data, metadata=metadata, act=act,
            source_type_final=decision.source_type_final,
            pdf_is_scanned_final=decision.pdf_is_scanned_final,
            snippet_source={"A": "html", "B": "native", "C": "ocr",
                            "D": "native"}[decision.lane],
            page_for_offset=normalized.page_for_offset,
            llm=None, settings=settings, source_url=deep_url,  # tags batched below
            language=language,
            ocr_quality_cer=ocr_quality_cer, ocr_engine=ocr_engine,
            facts=facts, ocr_cer_method=ocr_cer_method, ocr_script=ocr_script,
        )
        if record is None:
            dropped += 1
            emit.append_extract_log(out_dir, {
                "doc_id": doc_id, "stage": "extract", "action": "dropped",
                "article_section": span.article_section,
            })
            continue
        count = seen_citations.get(span.article_section, 0) + 1
        seen_citations[span.article_section] = count
        if count > 1:
            record["provision_id"] = f"{record['provision_id']}~{count}"
        records.append(record)
        tag_items.append((span, record["verbatim_snippet"], record["raw_context_before"]))
    log.info("%s: %d records grounded, %d dropped/skipped%s",
             doc_id, len(records), dropped,
             f", {straddling} act_index withheld (straddles a boundary)" if straddling else "")

    law_for_prompt = metadata.law_name.value or row.data.get("law_name_guess")
    tag_rows = [
        {
            "provision_id": record["provision_id"], "doc_id": doc_id,
            "law_name": law_for_prompt, "article_section": span.article_section,
            "heading": span.heading, "hierarchy": list(span.hierarchy),
            "snippet": snippet, "context_before": before,
        }
        for record, (span, snippet, before) in zip(records, tag_items)
    ]

    if llm and records:
        tag_started = time.monotonic()
        tags = extract_fields.llm_tags_batch(
            llm, metadata.law_name.value or row.data.get("law_name_guess"),
            tag_items, settings.tag_batch_size)
        elapsed = time.monotonic() - tag_started
        share = elapsed / len(records)
        model = getattr(llm, "model", None) or settings.llm_model
        for record, tag in zip(records, tags):
            for key in ("scope", "data_type", "obligation_type", "extraction_confidence"):
                record[key] = tag[key]
            # the record was built untagged, so the model that just judged it has to be
            # written in now - otherwise a tagged provision still reads `not_tagged`
            extract_fields.stamp_tagging_model(record, model, tag["extraction_confidence"])
            record["processing_time_seconds"] = round(
                record["processing_time_seconds"] + share, 3)
        log.info("%s: tagged %d provisions in %.1fs (%.2f prov/s, batch=%d)",
                 doc_id, len(records), elapsed,
                 len(records) / elapsed if elapsed > 0 else 0.0, settings.tag_batch_size)
    return records, metadata, tag_rows


def cmd_run(args: argparse.Namespace) -> int:
    settings = load_settings()
    manifest_csv = Path(args.manifest) if args.manifest else settings.handoff1_dir / "manifest.csv"
    raw_root = Path(args.raw) if args.raw else settings.handoff1_dir
    out_dir = Path(args.out) if args.out else settings.out_dir

    manifest = load_manifest(manifest_csv, raw_root, settings)
    rows = _select_rows(manifest, args.only_doc, args.economy,
                        getattr(args, "only_docs", None))
    rows = sorted(rows, key=_scanned_rank)  # stable: manifest order within buckets

    # What collection knew that the manifest does not carry, and the decision that follows
    # from it. Decided here, before anything is processed, so a document that is not read
    # leaves a row saying why instead of being silently absent.
    facts = load_facts(raw_root,
                       registry_default_language=getattr(args, "default_language", None),
                       mismatch_language=getattr(args, "mismatch_language", None))
    not_read: list[DocStatus] = []
    keep: list = []
    for row in rows:
        fact = facts.get(row.data["doc_id"])
        if fact is None or fact.decision == "read":
            keep.append(row)
            continue
        not_read.append(DocStatus(
            doc_id=fact.doc_id,
            status="excluded" if fact.decision == "exclude" else "skipped",
            n_provisions=0, lane=None, reason=fact.reason,
            source_type_final=row.data.get("source_type"),
            **_fact_columns(fact)))
    not_read_law_rows = [
        _law_row(row, settings, provision_count=0, notes=None,
                 coverage_status="excluded" if facts[row.data["doc_id"]].decision == "exclude"
                 else "skipped",
                 exclusion_reason=facts[row.data["doc_id"]].reason,
                 facts=facts[row.data["doc_id"]])
        for row in rows
        if row.data["doc_id"] in facts and facts[row.data["doc_id"]].decision != "read"
    ]
    if not_read:
        counts: dict[str, int] = {}
        for s in not_read:
            counts[str(s.reason)] = counts.get(str(s.reason), 0) + 1
        log.info("not read: %d of %d documents %s",
                 len(not_read), len(rows), counts)
    rows = keep
    needs_ocr = any(r.data["source_type"] == "pdf_scanned" for r in rows)
    # Only demand a model when one will actually be called. `run --skip-tags` is the
    # finale's normal mode: the tags are soft hints that mapping mostly ignores, and
    # requiring a pulled Ollama model to extract text made the stage un-runnable on a
    # clean machine with no model and no key.
    preflight(settings, needs_ocr=needs_ocr, needs_llm=not args.skip_tags)

    # one client per MODEL, not one per corpus: a corpus can hold more than one language,
    # and the tagger is chosen by the document's own language (config/llm/tagmap.py)
    llm_clients: dict = {}          # model name -> its client

    def llm_for(language: str | None):
        if args.skip_tags:
            return None
        from config.llm import tagmap
        from config.llm.factory import get_llm

        model = tagmap.tagger_for(language)
        if model not in llm_clients:
            llm_clients[model] = get_llm(settings, language=language)
        return llm_clients[model]

    llm = None
    # the not-read rows are part of the ledger: coverage must show them
    statuses: list[DocStatus] = list(not_read)
    law_rows: list[dict] = list(not_read_law_rows)
    all_records: list[dict] = []
    all_tag_rows: list[dict] = []
    started = time.monotonic()

    for row in rows:
        doc_id = row.data["doc_id"]
        local_path = manifest.resolve_local_path(row)
        if not local_path.is_file():
            log.error("%s: raw file missing: %s", doc_id, local_path)
            statuses.append(DocStatus(doc_id, "parse_failed", 0, None,
                                      f"raw file missing: {row.data['local_path']}", None))
            emit.remove_stale_doc_artifacts(out_dir, doc_id)
            continue

        decision = None
        try:
            # route() opens the PDF (chars/page recheck) - a corrupt file must
            # fail THIS doc, never the whole run
            decision = router.route(row.data["source_type"], row.data["pdf_is_scanned"],
                                    local_path, settings)
            if decision.reroute_reason:
                emit.append_extract_log(out_dir, {"doc_id": doc_id, "stage": "route",
                                                  "reroute": decision.reroute_reason})
            log.info("%s: lane %s (%s)", doc_id, decision.lane, decision.source_type_final)
            # The document's own declared language (D3), read once: it picks the OCR pack,
            # the segmenter profile and the tagging model.
            #
            # The fallback is not cosmetic. `load_facts` returns {} for a corpus with no
            # law_table.csv and no links_used/ - which is exactly China - so every Chinese
            # document would come through here as None, and None selects the common-law
            # segmenter and the English OCR pack. `cmd_ocr` has always had this fallback
            # (--default-language, from economies.json); the run loop did not, and the two
            # disagreeing is what would have read a Chinese corpus as English.
            language = (getattr(facts.get(doc_id), "language", None)
                        or getattr(args, "default_language", None))
            normalized, segmented, anchors, ocr_meta = _parse_doc(
                doc_id, decision, local_path, row.data["source_url"],
                settings, out_dir, force=args.force, language=language,
                economy_language=getattr(args, "default_language", None))
            ocr_cer = None
            ocr_engine_str = None
            if ocr_meta is not None:
                from rdtii_p2 import cer as cer_mod

                report_dir = out_dir / "ocr" / doc_id
                existing = (cer_mod.load_report(report_dir / "cer_report.json")
                            if (report_dir / "cer_report.json").is_file() else None)
                if existing and existing.get("cer_method") in ("native_twin", "gold_page"):
                    # demo doc: a genuinely measured report wins over the estimate
                    ocr_cer = existing["doc_cer"]
                    ocr_engine_str = existing["ocr_engine"]
                elif ocr_meta["cached"] and existing:
                    ocr_cer = existing["doc_cer"]
                    ocr_engine_str = existing["ocr_engine"]
                else:
                    report = cer_mod.make_estimate_report(
                        doc_id, ocr_meta["engine"], ocr_meta["preprocessing"])
                    cer_mod.write_report(report, report_dir)
                    ocr_cer = report.doc_cer
                    ocr_engine_str = ocr_meta["engine"]
            records, metadata, tag_rows = _extract_doc(doc_id, row, decision,
                                                       normalized, segmented,
                                                       llm_for(language),
                                                       settings, out_dir,
                                                       anchors=anchors,
                                                       ocr_quality_cer=ocr_cer,
                                                       ocr_engine=ocr_engine_str,
                                                       facts=facts.get(doc_id),
                                                       language=language)
            if args.skip_tags:
                all_tag_rows.extend(tag_rows)
        except NotImplementedError as exc:
            log.warning("%s: %s", doc_id, exc)
            statuses.append(DocStatus(doc_id, "parse_failed", 0,
                                      decision.lane if decision else None, str(exc),
                                      decision.source_type_final if decision else None))
            emit.remove_stale_doc_artifacts(out_dir, doc_id)
            continue
        except Exception as exc:
            log.error("%s: lane %s failed: %s", doc_id,
                      decision.lane if decision else "?", exc)
            statuses.append(DocStatus(doc_id, "parse_failed", 0,
                                      decision.lane if decision else None,
                                      f"error: {exc}",
                                      decision.source_type_final if decision else None))
            emit.remove_stale_doc_artifacts(out_dir, doc_id)
            continue

        # extraction succeeded - only NOW freeze source_text (rerun safety:
        # a mid-doc failure must never replace text that old records index)
        frozen_path = emit.write_source_text(out_dir, doc_id, normalized)
        log.info("%s: source_text frozen -> %s (%d chars, %d furniture lines stripped)",
                 doc_id, frozen_path, len(normalized.text), len(normalized.furniture_removed))
        emit.append_extract_log(out_dir, {
            "doc_id": doc_id, "stage": "segment",
            "n_sections": segmented.n_sections, "n_spans": len(segmented.spans),
            "dropped_toc_candidates": segmented.dropped_toc_candidates,
            "furniture_removed": normalized.furniture_removed,
        })
        if records:
            all_records.extend(records)
            statuses.append(DocStatus(doc_id, "ok", len(records), decision.lane, None,
                                      decision.source_type_final))
            per_act = _act_law_rows(row, settings, records, metadata, facts.get(doc_id))
            if per_act:
                law_rows.extend(per_act)
            else:
                law_rows.append(_law_row(
                    row, settings, provision_count=len(records), notes=None,
                    metadata=metadata, coverage_status="searched", facts=facts.get(doc_id)))
        else:
            reason = "parsed cleanly; no citable provision grounded"
            statuses.append(DocStatus(doc_id, "zero_provisions", 0, decision.lane,
                                      reason, decision.source_type_final))
            emit.write_by_law_empty(out_dir, doc_id)
            law_rows.append(_law_row(row, settings, provision_count=0,
                                     notes=reason, metadata=metadata,
                                     coverage_status="zero_provisions",
                                     facts=facts.get(doc_id)))

    processed = {status.doc_id for status in statuses}
    emit.write_provisions(out_dir, all_records, processed)
    emit.write_doc_status(out_dir, statuses)
    emit.write_laws(out_dir, law_rows, processed)
    if args.skip_tags:
        emit.write_tag_inputs(out_dir, all_tag_rows, processed)
        log.info("tags deferred: %d rows -> tag_inputs.jsonl (next: p2-extract tag-corpus)",
                 len(all_tag_rows))
    usage = {"input_tokens": 0, "output_tokens": 0}
    for client in llm_clients.values():
        for key, value in client.usage_totals().items():
            usage[key] = usage.get(key, 0) + value
    report = {
        "docs_processed": len(rows),
        "records_emitted": len(all_records),
        "wallclock_seconds": round(time.monotonic() - started, 2),
        "llm_model": ", ".join(sorted(llm_clients)) or None,
        "llm_tokens": usage,
        "estimated_usd": _estimated_usd(settings, usage) if llm else None,
    }
    # judge-facing cost evidence must survive incremental runs: carry the
    # cumulative tagging history (and any prior-run entries) forward instead
    # of clobbering the consolidated report
    report_path = out_dir / "cost_report.json"
    if report_path.is_file():
        previous = json.loads(report_path.read_text(encoding="utf-8"))
        for key, value in previous.items():
            if key not in report and key != "generated_at":
                report[key] = value
    emit.write_cost_report(out_dir, report)
    log.info("run complete: %d docs, doc_status + laws + cost_report written to %s",
             len(rows), out_dir)
    return 0


# Sync-API list prices, USD per million tokens (input, output). The Batches
# API halves these; the Batches lane writes its own report with actual spend.
_API_PRICES_PER_MTOK = {
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-sonnet-5": (3.0, 15.0),
    "claude-opus-4-8": (5.0, 25.0),
}


def _estimated_usd(settings: Settings, usage: dict[str, int]) -> float | None:
    """Measured-token cost at list price; None when the price is unknown."""
    if settings.llm_provider == "ollama":
        return 0.0
    prices = _API_PRICES_PER_MTOK.get(settings.llm_model)
    if not prices:
        return None
    in_price, out_price = prices
    return round(usage["input_tokens"] / 1e6 * in_price
                 + usage["output_tokens"] / 1e6 * out_price, 4)


def _pillars_in_scope(pillar_hint: str | None) -> list[int]:
    """Legacy hints or pillar numbers as text. Round 1 mapped everything to 6 and 7 and
    dropped the rest silently; the instrument now covers twelve pillars, so an unknown
    hint yields an empty list rather than a wrong one."""
    if not pillar_hint:
        return []
    legacy = {"P6": [6], "P7": [7], "both": [6, 7]}
    if pillar_hint in legacy:
        return legacy[pillar_hint]
    out = []
    for part in str(pillar_hint).split(","):
        part = part.strip()
        if part.isdigit() and 1 <= int(part) <= 12:
            out.append(int(part))
    return out


def _act_law_rows(row: ManifestRow, settings: Settings, records: list[dict],
                  metadata, facts) -> list[dict]:
    """One laws.jsonl row per ACT, when this document's provisions were split into acts.

    A Timorese gazette issue is one document holding many separate laws, and mapping reads
    laws.jsonl as the list of laws searched. One row per document there says a 26-act issue is
    one law, whatever the provisions say.

    Returns [] when the acts were not split - single-act documents, and multi-act documents
    the completeness gate withheld - so the caller keeps the one-row-per-document behaviour
    and nothing changes for five of the six economies.
    """
    indexed = [r for r in records if r.get("act_index")]
    if not indexed:
        return []
    total = getattr(facts, "act_count", 1) or 1
    by_act: dict[int, list[dict]] = {}
    for record in records:
        by_act.setdefault(record.get("act_index") or 0, []).append(record)
    located = len([k for k in by_act if k])
    rows: list[dict] = []
    for index in sorted(k for k in by_act if k):
        group = by_act[index]
        rows.append(_law_row(
            row, settings, provision_count=len(group), notes=None, metadata=metadata,
            coverage_status="searched", facts=facts,
            act={"act_index": index, "act_count": total,
                 "law_name_original": group[0].get("law_name_original"),
                 "law_number": group[0].get("law_number")},
            acts_located=located))
    # provisions the straddle gate withheld still belong to this document and must be
    # counted somewhere, or validate's per-document total will not reconcile
    orphans = by_act.get(0)
    if orphans:
        rows.append(_law_row(
            row, settings, provision_count=len(orphans),
            notes="provisions whose act could not be determined (heading in another act)",
            metadata=metadata, coverage_status="searched", facts=facts,
            act={"act_count": total}, acts_located=located))
    return rows


def _law_row(row: ManifestRow, settings: Settings, provision_count: int,
             notes: str | None, metadata=None, coverage_status: str = "searched",
             exclusion_reason: str | None = None, facts=None, act=None,
             acts_located: int | None = None) -> dict:
    pillars = _pillars_in_scope(row.data.get("pillar_hint"))
    hints = row.data.get("indicator_hints")
    # An act's own name and number beat the document-level guess: a gazette issue's
    # law_name_guess is the ISSUE, not any one of the acts printed in it.
    law_name = ((act or {}).get("law_name_original")
                or (metadata.law_name.value if metadata and metadata.law_name.value
                    else row.data["law_name_guess"]))
    law_number = ((act or {}).get("law_number")
                  or (metadata.law_number.value if metadata and metadata.law_number.value
                      else row.data.get("law_number_guess")))
    return {
        "contract_version": settings.contract_version,
        "doc_id": row.data["doc_id"],
        "economy": row.data["economy"],
        "law_name": law_name,
        "law_number": law_number,
        "source_url": row.data["source_url"],
        "pillars_in_scope": pillars,
        "indicators_searched": [h.strip() for h in hints.split(",")] if hints else [],
        "provision_count": provision_count,
        "searched": coverage_status in {"searched", "zero_provisions"},
        # what happened to this law, so an absence is explained rather than silent, and so a
        # document that must not be cited cannot become the authority for a "no provision" row
        "coverage_status": coverage_status,
        "exclusion_reason": exclusion_reason,
        "language_of_source": getattr(facts, "language", None),
        "document_kind": sorted(getattr(facts, "document_kinds", []) or []) or None,
        "legal_status": sorted(getattr(facts, "legal_statuses", []) or []) or None,
        "use": sorted(getattr(facts, "uses", []) or []) or None,
        "content_flags": sorted(getattr(facts, "content_flags", []) or []),
        # one row per ACT, not per document, once the acts are located (contract 3.9)
        "act_index": (act or {}).get("act_index"),
        "act_count": (act or {}).get("act_count") or getattr(facts, "act_count", 1) or 1,
        "acts_located": acts_located,
        "law_name_original": (act or {}).get("law_name_original"),
        "law_name_en": None,
        "law_name_en_source": None,
        "notes": notes,
    }


# ------------------------------------------------------------- tag-corpus ----

def cmd_tag_corpus(args: argparse.Namespace) -> int:
    """Batches-API tagging over tag_inputs.jsonl (run --skip-tags first)."""
    import anthropic

    from config.llm.anthropic_client import AnthropicClient
    from rdtii_p2 import tag_batches

    settings = load_settings()
    if not settings.anthropic_api_key:
        log.error("ANTHROPIC_API_KEY is empty - the Batches lane needs a real key")
        return 1
    out_dir = Path(args.out) if args.out else settings.out_dir
    rows = tag_batches.load_tag_inputs(out_dir)
    if args.only_untagged:
        untagged: set[str] = set()
        with open(out_dir / "provisions.jsonl", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    record = json.loads(line)
                    if record.get("extraction_confidence") is None:
                        untagged.add(record["provision_id"])
        rows = [row for row in rows if row["provision_id"] in untagged]
        log.info("--only-untagged: %d of %d tag_inputs rows still need tags",
                 len(rows), len(untagged) or 1)
        if not rows:
            log.info("nothing to tag - all records already carry tags")
            return 0
    started = time.monotonic()

    if args.resume:
        state = tag_batches.load_state(out_dir)
        model, batch_size = state["model"], state["batch_size"]
        batch_ids = state["batch_ids"]
        if state["n_rows"] != len(rows):
            log.error("tag_inputs.jsonl changed since submit (%d rows vs %d at "
                      "submit) - re-submit instead of resuming", len(rows), state["n_rows"])
            return 1
        chunks = tag_batches.make_chunks(rows, batch_size)
        log.info("resuming %d batch(es), model %s, %d requests",
                 len(batch_ids), model, len(chunks))
    else:
        model, batch_size = args.model, args.batch_size
        chunks = tag_batches.make_chunks(rows, batch_size)
        log.info("packed %d provisions into %d requests (batch_size=%d, model=%s)",
                 len(rows), len(chunks), batch_size, model)
        if args.dry_run:
            return 0
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        batch_ids = tag_batches.submit(client, chunks, model)
        tag_batches.save_state(out_dir, {
            "batch_ids": batch_ids, "model": model,
            "batch_size": batch_size, "n_rows": len(rows),
        })

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    tag_batches.poll_until_ended(client, batch_ids, args.poll_interval)
    tags, leftovers, usage = tag_batches.collect_tags(client, batch_ids, chunks)
    if leftovers:
        log.warning("%d provisions failed in the batch - retrying synchronously",
                    len(leftovers))
        sync_client = AnthropicClient(api_key=settings.anthropic_api_key, model=model)
        tags.update(tag_batches.retry_sync(sync_client, leftovers))
        sync_usage = sync_client.usage_totals()
        usage["input_tokens"] += sync_usage["input_tokens"]
        usage["output_tokens"] += sync_usage["output_tokens"]
    updated, unmatched = tag_batches.apply_tags(out_dir, tags, model)
    summary = tag_batches.update_cost_report(
        out_dir, settings, model, usage, time.monotonic() - started, updated)
    log.info("tag-corpus complete: %d records tagged (%d tags without a record), "
             "tokens in=%d out=%d, est USD (batch discount) %s",
             updated, unmatched, usage["input_tokens"], usage["output_tokens"],
             summary["estimated_usd_with_batch_discount"])
    return 0


# --------------------------------------------------------------- validate ----

def cmd_ocr(args: argparse.Namespace) -> int:
    """Fill the OCR page cache for a corpus, in parallel. The only parallel step."""
    settings = load_settings()
    manifest_csv = Path(args.manifest or settings.handoff1_dir / "manifest.csv")
    raw_root = Path(args.raw or settings.handoff1_dir)
    out_dir = Path(args.out or settings.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(manifest_csv, raw_root, settings)
    rows = _select_rows(manifest, args.only_doc, args.economy,
                        getattr(args, "only_docs", None))
    facts = load_facts(raw_root,
                       registry_default_language=getattr(args, "default_language", None),
                       mismatch_language=getattr(args, "mismatch_language", None))

    tessdata = langmap.use_vendored_packs(args.pack)
    log.info("OCR packs: %s (%s)", tessdata, ", ".join(sorted(langmap.installed_packs(args.pack))))

    jobs = {}
    for row in rows:
        doc_id = row.data["doc_id"]
        fact = facts.get(doc_id)
        if fact is not None and fact.decision != "read":
            continue                       # excluded or linkage: never worth OCRing
        flags = set(getattr(fact, "content_flags", []) or [])
        scanned = row.data["source_type"] == "pdf_scanned" or "no_text_layer" in flags
        if not scanned:
            continue
        path = manifest.resolve_local_path(row)
        if not path.is_file():
            log.error("%s: raw file missing: %s", doc_id, path)
            continue
        language = getattr(fact, "language", None) or args.default_language or "eng"
        pages = int(row.data.get("page_count") or 0)
        if pages < 1:
            log.warning("%s: manifest records no page count, skipping", doc_id)
            continue
        jobs[doc_id] = (path, pages, language, langmap.pack_for(language), tessdata,
                        ocr_cache.file_sha256(path))

    if not jobs:
        log.info("no scanned documents to OCR in this corpus")
        return 0
    langmap.check_packs({spec[2] for spec in jobs.values()}, args.pack)
    report = ocr_prepass.run_prepass(jobs, out_dir, workers=args.workers)
    log.info("OCR pre-pass report: %s", json.dumps(report, ensure_ascii=False))
    return 1 if report.get("failed") else 0


def cmd_validate(args: argparse.Namespace) -> int:
    import jsonschema

    from rdtii_p2.ingest import SCHEMA_PATH

    provisions_path = Path(args.provisions)
    out_dir = provisions_path.parent
    source_text_dir = Path(args.source_text) if args.source_text else out_dir / "source_text"
    failures: list[str] = []
    schema_failures: list[str] = []

    records: list[dict] = []
    if provisions_path.is_file():
        with open(provisions_path, encoding="utf-8") as fh:
            records = [json.loads(line) for line in fh if line.strip()]

    schemas_dir = SCHEMA_PATH.parent
    provision_validator = jsonschema.Draft202012Validator(
        json.loads((schemas_dir / "provision.schema.json").read_text(encoding="utf-8")))
    laws_validator = jsonschema.Draft202012Validator(
        json.loads((schemas_dir / "laws.schema.json").read_text(encoding="utf-8")))

    for record in records:
        for err in provision_validator.iter_errors(record):
            schema_failures.append(
                f"{record.get('provision_id', '?')}: {err.json_path}: {err.message[:120]}")

    laws_path = Path(args.laws) if args.laws else out_dir / "laws.jsonl"
    if laws_path.is_file():
        with open(laws_path, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                law = json.loads(line)
                for err in laws_validator.iter_errors(law):
                    schema_failures.append(
                        f"laws.jsonl {law.get('doc_id', '?')}: {err.json_path}: {err.message[:120]}")
    else:
        failures.append("laws.jsonl missing")

    seen_provision_ids: set[str] = set()
    for record in records:
        pid = record.get("provision_id", "?")
        if pid in seen_provision_ids:
            failures.append(f"{pid}: duplicate provision_id")
        seen_provision_ids.add(pid)

    # Hard offline gates: grounding + scanned-CER + doc_status consistency (2.3a)
    grounded = 0
    for record in records:
        doc_id = record["doc_id"]
        text_path = source_text_dir / f"{doc_id}.txt"
        if not text_path.is_file():
            failures.append(f"{record['provision_id']}: source_text/{doc_id}.txt missing")
            continue
        text = text_path.read_text(encoding="utf-8")
        try:
            ground.verify(text, record["snippet_char_start"], record["snippet_char_end"],
                          record["verbatim_snippet"])
            grounded += 1
        except ground.GroundingError as exc:
            failures.append(f"{record['provision_id']}: {exc}")
        if record.get("source_type") == "pdf_scanned" and record.get("ocr_quality_cer") is None:
            failures.append(f"{record['provision_id']}: scanned source but ocr_quality_cer is null")

    status_path = out_dir / "doc_status.jsonl"
    statuses: list[dict] = []
    by_doc: dict[str, int] = {}
    for record in records:
        by_doc[record["doc_id"]] = by_doc.get(record["doc_id"], 0) + 1
    if status_path.is_file():
        with open(status_path, encoding="utf-8") as fh:
            statuses = [json.loads(line) for line in fh if line.strip()]
        seen = [s["doc_id"] for s in statuses]
        if len(seen) != len(set(seen)):
            failures.append("doc_status.jsonl: duplicate doc_id rows")
        status_docs = set(seen)
        # every record's doc must carry a status row - orphan records are a
        # silently-dropped-doc signal (PLAN 2.3.1)
        for doc_id in by_doc:
            if doc_id not in status_docs:
                failures.append(f"{doc_id}: {by_doc[doc_id]} records but no doc_status row")
        # provision_count SUMMED per document: laws.jsonl holds one row per ACT once a
        # gazette issue is split, so a dict keyed on doc_id keeps only the last act's row.
        laws_counts: dict[str, int] = {}
        if laws_path.is_file():
            with open(laws_path, encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    law = json.loads(line)
                    laws_counts[law["doc_id"]] = (laws_counts.get(law["doc_id"], 0)
                                                  + (law.get("provision_count") or 0))
        for status in statuses:
            doc_id = status["doc_id"]
            actual = by_doc.get(doc_id, 0)
            if status["status"] == "ok" and actual < 1:
                failures.append(f"{doc_id}: status ok but no records")
            if status["status"] != "ok" and actual > 0:
                failures.append(f"{doc_id}: status {status['status']} but has records")
            if status["status"] == "ok" and status.get("n_provisions") != actual:
                failures.append(f"{doc_id}: n_provisions={status.get('n_provisions')} "
                                f"but {actual} records present")
            if status["status"] in ("ok", "zero_provisions"):
                # contract 3.9: every processed doc has laws row + by_law + source_text
                if doc_id not in laws_counts:
                    failures.append(f"{doc_id}: processed but no laws.jsonl row")
                elif laws_counts[doc_id] != actual:
                    # SUMMED across the document's rows: laws.jsonl carries one row per ACT
                    # once a gazette issue is split, so a dict keyed on doc_id would keep
                    # only the last act's count and fail on every multi-act document.
                    failures.append(
                        f"{doc_id}: laws.provision_count total={laws_counts[doc_id]} "
                        f"but {actual} records")
                if not (out_dir / "by_law" / f"{doc_id}.json").is_file():
                    failures.append(f"{doc_id}: processed but by_law/{doc_id}.json missing")
                if not (source_text_dir / f"{doc_id}.txt").is_file():
                    failures.append(f"{doc_id}: processed but source_text/{doc_id}.txt missing")
    else:
        failures.append("doc_status.jsonl missing")

    if args.manifest:
        import csv as _csv

        with open(Path(args.manifest), encoding="utf-8-sig", newline="") as fh:
            manifest_rows = list(_csv.DictReader(fh))
        # P1 standing rule: "superseded by" rows are provenance-only - their
        # extractions are retired, so completeness must not require them
        manifest_ids = [r["doc_id"] for r in manifest_rows
                        if not is_superseded(r.get("crawl_notes"))]
        status_ids = [s["doc_id"] for s in statuses]
        missing = set(manifest_ids) - set(status_ids)
        if missing:
            failures.append(
                f"doc_status incomplete vs manifest: {len(missing)} doc(s) never "
                f"processed, e.g. {sorted(missing)[:3]}")
        retired = {r["doc_id"] for r in manifest_rows
                   if is_superseded(r.get("crawl_notes"))}
        stale = retired & set(status_ids)
        if stale:
            failures.append(
                f"{len(stale)} superseded doc(s) still present in doc_status "
                f"(retire them), e.g. {sorted(stale)[:3]}")

    from config.settings import load_settings as _load

    pinned_major = _load().contract_version.split(".")[0]
    for record in records:
        if record["contract_version"].split(".")[0] != pinned_major:
            failures.append(f"{record['provision_id']}: contract_version "
                            f"{record['contract_version']} vs pinned major {pinned_major}.x")
            break

    # PLAN 2.3a: URL liveness is advisory - attempted when a quick network
    # probe succeeds (or --check-urls forces it), never a drop condition
    url_summary = "skipped_offline"
    if args.check_urls or _network_available():
        url_summary = _check_urls_advisory(records)

    print(f"[P2] validate: records={len(records)} "
          f"schema={'PASS' if not schema_failures else 'FAIL'} "
          f"grounding={'PASS' if grounded == len(records) else 'FAIL'} "
          f"doc_status={'PASS' if status_path.is_file() and not failures else ('FAIL' if failures else 'PASS')} "
          f"url_check={url_summary}")
    if failures or schema_failures:
        for failure in (schema_failures + failures)[:20]:
            print(f"[P2]   FAIL: {failure}")
        return 1
    return 0


def _network_available() -> bool:
    """2-second probe so the offline/air-gapped run never blocks on URLs."""
    import socket

    try:
        socket.create_connection(("1.1.1.1", 443), timeout=2).close()
        return True
    except OSError:
        return False


def _check_urls_advisory(records: list[dict]) -> str:
    """Advisory only - a record is NEVER dropped for an unreachable URL (2.3a).
    Deduplicated by URL WITHOUT its fragment: thousands of per-section anchor
    URLs (#_Toc...) hit the same page, and fragments never reach the server."""
    import urllib.parse
    import urllib.request

    urls = sorted({
        urllib.parse.urldefrag(r["source_url"])[0]
        for r in records if r.get("source_url")
    })
    live = 0
    for url in urls:
        try:
            request = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(request, timeout=5) as response:
                if response.status < 400:
                    live += 1
                else:
                    log.warning("url_check=http_%d %s", response.status, url)
        except Exception as exc:
            log.info("url_check unreachable (advisory): %s (%s)", url, exc)
    return f"{live}_live/{len(urls)}_checked"


# ------------------------------------------------------------ demo, pilot ----

def cmd_demo(args: argparse.Namespace) -> int:
    """Deliverable #4: a manifest-retrieved scanned doc, gold-page CER measured
    live, then the full pipeline over it (records inherit the measured CER)."""
    import re as _re

    from config.ocr.factory import get_ocr
    from rdtii_p2 import cer as cer_mod

    settings = load_settings()
    doc_id = args.doc or "my-cma1998-001"
    out_dir = Path(args.out) if args.out else settings.out_dir
    manifest_csv = Path(args.manifest) if args.manifest else settings.handoff1_dir / "manifest.csv"
    raw_root = Path(args.raw) if args.raw else settings.handoff1_dir
    manifest = load_manifest(manifest_csv, raw_root, settings)
    row = _select_rows(manifest, doc_id, None)[0]
    if row.data["source_type"] != "pdf_scanned":
        log.error("%s is not pdf_scanned - Deliverable #4 requires a scanned doc", doc_id)
        return 1
    local_path = manifest.resolve_local_path(row)
    log.info("demo: %s retrieved via manifest (%s), pdf_is_scanned=%s",
             doc_id, row.data["local_path"], row.data["pdf_is_scanned"])

    gold_dir = Path("fixtures/ocr_reference") / doc_id
    gold_path = (Path(args.gold) if args.gold
                 else next(iter(sorted(gold_dir.glob("gold_page_*.txt"))), None))
    if gold_path is None or not gold_path.is_file():
        log.error("no gold transcription under %s - transcribe one page first", gold_dir)
        return 1
    page_match = _re.search(r"(\d+)", gold_path.stem)
    page = args.page or (int(page_match.group(1)) if page_match else None)
    if page is None:
        log.error("cannot infer page number from %s - pass --page", gold_path.name)
        return 1

    engine = get_ocr(settings)
    started = time.monotonic()
    result = engine.to_text(local_path, pages=[page])
    report = cer_mod.measure_doc(
        doc_id=doc_id,
        page_pairs=[(page, gold_path.read_text(encoding="utf-8"), result.pages[0].text)],
        cer_method="gold_page", reference_source=str(gold_path),
        ocr_engine=result.engine, preprocessing=result.preprocessing)
    report_path = cer_mod.write_report(report, out_dir / "ocr" / doc_id)
    verdict = ("MEETS the <5% rubric bar" if report.meets_rubric()
               else "DOES NOT MEET the <5% bar")
    log.info("demo: gold-page CER %.4f (%.2f%%) on p.%d in %.1fs -> %s [%s]",
             report.doc_cer, report.doc_cer * 100, page,
             time.monotonic() - started, report_path, verdict)

    status = cmd_run(argparse.Namespace(
        manifest=args.manifest, raw=args.raw, out=args.out, only_doc=doc_id,
        only_docs=None, economy=None, force=False, skip_tags=False))
    return status if status != 0 else (0 if report.meets_rubric() else 1)


def cmd_pilot(args: argparse.Namespace) -> int:
    """T2b CER pilot: OCR one scanned page, measure CER against a gold page."""
    from rdtii_p2 import cer as cer_mod
    from config.ocr.factory import get_ocr

    settings = load_settings()
    if args.engine:
        settings.ocr_engine = args.engine
    engine = get_ocr(settings)

    scan = Path(args.scan)
    gold_text = Path(args.gold).read_text(encoding="utf-8")
    log.info("pilot: OCR %s p.%d with %s", scan.name, args.page, engine.engine_id)
    started = time.monotonic()
    result = engine.to_text(scan, pages=[args.page])
    elapsed = time.monotonic() - started
    page = result.pages[0]
    log.info("pilot: %d chars OCR'd in %.1fs (mean word conf %s)",
             len(page.text), elapsed,
             f"{page.mean_word_confidence:.1f}" if page.mean_word_confidence else "n/a")

    doc_id = args.doc_id or scan.stem
    report = cer_mod.measure_doc(
        doc_id=doc_id,
        page_pairs=[(args.page, gold_text, page.text)],
        cer_method="gold_page",
        reference_source=str(args.gold),
        ocr_engine=result.engine,
        preprocessing=result.preprocessing,
    )
    out_dir = Path(args.out) / doc_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"page_{args.page:04d}.txt").write_text(page.text, encoding="utf-8")
    (out_dir / f"page_{args.page:04d}.confidences.json").write_text(
        json.dumps({"mean_word_confidence": page.mean_word_confidence,
                    "elapsed_seconds": round(elapsed, 2)}),
        encoding="utf-8",
    )
    path = cer_mod.write_report(report, out_dir)
    verdict = "MEETS <5% rubric bar" if report.meets_rubric() else "DOES NOT MEET <5% bar"
    log.info("pilot: CER %.4f (%.2f%%) via %s -> %s [%s]",
             report.doc_cer, report.doc_cer * 100, report.cer_method, path, verdict)
    return 0 if report.doc_cer < 0.05 else 1


# ------------------------------------------------------------------- main ----

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="p2-extract",
        description="RDTII Project 2 - OCR & tag extraction (Hand-off #1 -> Hand-off #2)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="process manifest docs into Hand-off #2")
    run.add_argument("--manifest", help="path to handoff1/manifest.csv")
    run.add_argument("--raw", help="handoff1/ root that local_path is relative to")
    run.add_argument("--out", help="handoff2/ output dir")
    run.add_argument("--only-doc", help="process a single doc_id")
    run.add_argument("--only-docs", dest="only_docs",
                     help="file listing one doc_id per line to process")
    run.add_argument("--economy", help="filter to one economy code, e.g. LA")
    run.add_argument("--default-language", dest="default_language",
                     help="ISO 639-3 language for documents the crawler left blank; "
                          "recorded as language_source=registry_default, never as a "
                          "portal field")
    run.add_argument("--mismatch-language", dest="mismatch_language",
                     help="ISO 639-3 language of files the crawler flagged "
                          "language_mismatch, e.g. msa for Malaysia")
    run.add_argument("--force", action="store_true", help="re-process even if unchanged")
    run.add_argument("--skip-tags", action="store_true",
                     help="defer LLM tags: emit untagged records + tag_inputs.jsonl "
                          "for the tag-corpus Batches lane")
    run.set_defaults(func=cmd_run)

    ocr = sub.add_parser("ocr", help="fill the OCR page cache for a corpus, in parallel")
    ocr.add_argument("--manifest", help="path to the corpus manifest.csv")
    ocr.add_argument("--raw", help="corpus root that local_path is relative to")
    ocr.add_argument("--out", help="output dir holding ocr/")
    ocr.add_argument("--only-doc", help="one doc_id")
    ocr.add_argument("--only-docs", dest="only_docs", help="file of doc_ids, one per line")
    ocr.add_argument("--economy", help="filter to one economy code")
    ocr.add_argument("--workers", type=int, default=ocr_prepass.DEFAULT_WORKERS,
                     help="parallel workers (default 16; Tesseract crashes intermittently "
                          "above about 16, and scaling flattens after 12)")
    ocr.add_argument("--pack", default=langmap.DEFAULT_QUALITY, choices=["fast", "best"],
                     help="which vendored pack set to use (default fast: measured within "
                          "half a point of best on real Lao scans, at half the time)")
    ocr.add_argument("--default-language", dest="default_language")
    ocr.add_argument("--mismatch-language", dest="mismatch_language")
    ocr.set_defaults(func=cmd_ocr)

    tag = sub.add_parser("tag-corpus",
                         help="tag tag_inputs.jsonl via the Anthropic Batches API "
                              "(50%% discount), then rewrite provisions.jsonl")
    tag.add_argument("--out", help="handoff2/ dir holding tag_inputs.jsonl")
    tag.add_argument("--model", default="claude-haiku-4-5")
    tag.add_argument("--batch-size", type=int, default=10,
                     help="provisions per batch request")
    tag.add_argument("--poll-interval", type=int, default=60)
    tag.add_argument("--dry-run", action="store_true",
                     help="pack and count requests, submit nothing")
    tag.add_argument("--resume", action="store_true",
                     help="poll/apply the batch recorded in tag_batch_state.json")
    tag.add_argument("--only-untagged", dest="only_untagged", action="store_true",
                     help="submit only provisions whose record has no tags yet "
                          "(extraction_confidence null)")
    tag.set_defaults(func=cmd_tag_corpus)

    validate = sub.add_parser("validate", help="offline hard gates: schema + grounding + doc_status")
    validate.add_argument("--provisions", required=True)
    validate.add_argument("--source-text", dest="source_text")
    validate.add_argument("--laws")
    validate.add_argument("--manifest",
                          help="also enforce doc_status completeness vs this manifest")
    validate.add_argument("--check-urls", action="store_true",
                          help="force advisory URL liveness even without a network probe")
    validate.set_defaults(func=cmd_validate)

    demo = sub.add_parser("demo", help="Deliverable-#4 scanned-PDF demo: gold-page "
                                       "CER + full pipeline on a manifest doc")
    demo.add_argument("--doc", help="scanned doc_id (default my-cma1998-001)")
    demo.add_argument("--gold", help="gold transcription .txt (default: fixtures/ocr_reference/<doc>/gold_page_*.txt)")
    demo.add_argument("--page", type=int, help="1-based page of the gold transcription")
    demo.add_argument("--manifest", help="path to handoff1/manifest.csv")
    demo.add_argument("--raw", help="handoff1/ root")
    demo.add_argument("--out", help="handoff2/ output dir")
    demo.set_defaults(func=cmd_demo)

    pilot = sub.add_parser("pilot", help="T2b OCR CER pilot: one page vs a gold transcription")
    pilot.add_argument("--scan", required=True, help="scanned PDF path")
    pilot.add_argument("--gold", required=True, help="gold transcription .txt")
    pilot.add_argument("--page", type=int, required=True, help="1-based page to OCR")
    pilot.add_argument("--engine", choices=["tesseract", "paddleocr", "azure_docint"])
    pilot.add_argument("--doc-id", dest="doc_id")
    pilot.add_argument("--out", default="fixtures/ocr_reference")
    pilot.set_defaults(func=cmd_pilot)

    args = parser.parse_args(argv)
    _setup_logging()
    try:
        return args.func(args)
    except IngestError as exc:
        log.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
