"""S0 ingest — stream provisions.jsonl, verify grounding, emit the prefilter corpus.

Contract obligations honored here (FOUNDATION_SYNC §C):
- stream line-by-line, never json-load whole (639+ MB);
- provision_id is an opaque join key (never split on '#');
- validate against the vendored provision.schema.json on a sample, as a GATE;
- Tier-1 byte grounding: verbatim_snippet == source_text[start:end] byte-exact,
  falling back to a contains-check (grounding=context-checked);
- tags are soft boosts, never gates; low confidence never excludes;
- doc_status lives in doc_status.jsonl (corpus v2.1+ schema), not laws.jsonl.

Outputs (data/index/):
- prefilter_corpus.jsonl : one compact record per provision (+ source_text chunks
  for SPECIAL_SOURCE_TEXT_DOCS) with the metadata-prefixed text the prefilter uses
- doc_meta.json          : per-doc economy/law_name/law_name_en/language/status/counts
- out/ingest_report.json : measured gate results
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter, OrderedDict
from pathlib import Path

from config import manifest
from config.settings import SETTINGS, SPECIAL_SOURCE_TEXT_DOCS

CHUNK_CHARS = 1200
CHUNK_OVERLAP = 150
SCHEMA_SAMPLE_EVERY = 64  # jsonschema-validate ~1/64 of records (≈5k) inline


class IngestGateError(RuntimeError):
    """A contract gate failed at S0. Nothing downstream should run on this corpus."""

# crude Malay detector for bilingual-twin bookkeeping (recall denominators only)
_MALAY_HINTS = re.compile(
    r"\b(hendaklah|yang|atau|dengan|bagi|adalah|tidak|boleh|kepada|seksyen|peraturan|akta)\b",
    re.IGNORECASE,
)


class _SourceCache:
    """LRU over source_text/<doc_id>.txt (5.3k files, keep 64 hot)."""

    def __init__(self, root: Path, cap: int = 64) -> None:
        self.root = root
        self.cap = cap
        self._cache: OrderedDict[str, str] = OrderedDict()

    def get(self, doc_id: str) -> str | None:
        if doc_id in self._cache:
            self._cache.move_to_end(doc_id)
            return self._cache[doc_id]
        f = self.root / f"{doc_id}.txt"
        if not f.exists():
            return None
        text = f.read_text(encoding="utf-8", errors="replace")
        self._cache[doc_id] = text
        if len(self._cache) > self.cap:
            self._cache.popitem(last=False)
        return text


def _prefilter_text(rec: dict) -> str:
    """Metadata-prefixed embedding/BM25 text (framework §3.1: SAC-style prefix)."""
    law = (rec.get("law_name") or "").strip()
    sec = (rec.get("article_section") or "").strip()
    loc = (rec.get("location_reference") or "").strip()
    body = " ".join(
        filter(
            None,
            (
                rec.get("raw_context_before"),
                rec.get("verbatim_snippet"),
                rec.get("raw_context_after"),
            ),
        )
    )
    return f"{law} | {sec} | {loc} :: {body}".strip()


def _chunk_source_text(doc_id: str, text: str) -> list[dict]:
    chunks = []
    step = CHUNK_CHARS - CHUNK_OVERLAP
    for i, start in enumerate(range(0, max(len(text) - CHUNK_OVERLAP, 1), step)):
        seg = text[start : start + CHUNK_CHARS]
        if len(seg.strip()) < 80:
            continue
        chunks.append(
            {
                "provision_id": f"{doc_id}#st.{i}",
                "doc_id": doc_id,
                "snippet_source": "source_text_chunk",
                "char_start": start,
                "char_end": start + len(seg),
                "text": seg,
            }
        )
    return chunks


def run_ingest() -> dict:
    t0 = time.time()
    h2 = SETTINGS.handoff2_dir
    idx = SETTINGS.index_dir
    idx.mkdir(parents=True, exist_ok=True)
    SETTINGS.out_dir.mkdir(parents=True, exist_ok=True)

    schema = None
    try:
        import jsonschema

        schema_path = Path("00_contracts/schemas/provision.schema.json")
        schema = jsonschema.Draft202012Validator(
            json.loads(schema_path.read_text(encoding="utf-8"))
        )
    except Exception as e:
        # Not a warning any more: with no validator the run cannot say the corpus meets the
        # contract, and C1c/C2 are marked on exactly that claim.
        schema_unavailable = f"{type(e).__name__}: {e}"
        print(f"[ingest] schema validator unavailable: {schema_unavailable}")
    else:
        schema_unavailable = None

    # ---- laws + doc_status (v2.1+ schema: status lives in doc_status.jsonl)
    doc_meta: dict[str, dict] = {}
    with (h2 / "laws.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            doc_meta[r["doc_id"]] = {
                "economy": r.get("economy"),
                "law_name": r.get("law_name"),
                # 0.3.0 document fields, carried because three later stages have no other
                # source for them: law_name_en is null on every provision record but populated
                # on every law here (CN 1085/1085, LA 1762/1762, TL 2877/2879), and the host
                # baseline is written in English -- without it NEW/KNOWN scores a Chinese or Lao
                # law name at 0 against the baseline and tags every fire NEW, silently.
                # language_of_source feeds the CSV's language column; legal_status and
                # act_index feed the zero-score filters and the TL citability rule.
                "law_name_en": r.get("law_name_en"),
                "law_name_original": r.get("law_name_original"),
                "language_of_source": r.get("language_of_source"),
                # filled from the provisions below where the law row is silent
                "language_of_source_name": None,
                "legal_status": r.get("legal_status"),
                "act_index": r.get("act_index"),
                "law_number": r.get("law_number"),
                "provision_count": r.get("provision_count"),
                "searched": r.get("searched"),
                "source_url": r.get("source_url"),
                "status": None,
            }
    with (h2 / "doc_status.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            d = doc_meta.setdefault(
                r["doc_id"],
                {"economy": None, "law_name": None, "law_name_en": None,
                 "law_name_original": None, "language_of_source": None,
                 "language_of_source_name": None,
                 "legal_status": None, "act_index": None, "law_number": None,
                 "provision_count": None, "searched": None, "source_url": None,
                 "status": None},
            )
            d["status"] = r.get("status")
            d["lane"] = r.get("lane")
            d["source_type_final"] = r.get("source_type_final")

    # ---- stream provisions
    src_cache = _SourceCache(h2 / "source_text")
    n = 0
    stats = Counter()
    grounding_fail_samples: list[str] = []
    schema_errors: list[str] = []
    version_mismatch = 0

    corpus_path = idx / "prefilter_corpus.jsonl"
    with (h2 / "provisions.jsonl").open(encoding="utf-8") as fin, corpus_path.open(
        "w", encoding="utf-8"
    ) as fout:
        for line in fin:
            n += 1
            rec = json.loads(line)

            cv = rec.get("contract_version") or ""
            if not cv.startswith("0."):
                version_mismatch += 1

            # the first record always, then every SCHEMA_SAMPLE_EVERY-th: a corpus smaller than
            # the sampling interval would otherwise validate nothing and still pass the gate
            if schema is not None and (n == 1 or n % SCHEMA_SAMPLE_EVERY == 0):
                errs = list(schema.iter_errors(rec))
                if errs:
                    stats["schema_sample_fail"] += 1
                    if len(schema_errors) < 10:
                        schema_errors.append(
                            f"{rec.get('provision_id')}: {errs[0].message[:120]}"
                        )
                else:
                    stats["schema_sample_ok"] += 1

            # Tier-1 byte grounding
            grounding = "unchecked"
            snippet = rec.get("verbatim_snippet") or ""
            doc_id = rec.get("doc_id") or ""
            s, e = rec.get("snippet_char_start"), rec.get("snippet_char_end")
            text = src_cache.get(doc_id)
            if text is not None and isinstance(s, int) and isinstance(e, int):
                if text[s:e] == snippet:
                    grounding = "byte-exact"
                elif snippet and snippet in text:
                    grounding = "context-checked"
                else:
                    grounding = "FAILED"
                    if len(grounding_fail_samples) < 10:
                        grounding_fail_samples.append(rec.get("provision_id", "?"))
            elif text is None:
                grounding = "no-source-text"
            stats[f"grounding:{grounding}"] += 1

            econ = rec.get("economy")
            stats[f"econ:{econ}"] += 1

            # `language_of_source` is null on all 1,085 Chinese laws while their provisions say
            # `language_of_source_name: Chinese`. The CSV's language column and the selection
            # threshold's language offset both read doc_meta, so carry the name where the law
            # row is silent -- once per document, not once per provision.
            dm = doc_meta.get(doc_id)
            if dm is not None and not dm.get("language_of_source_name"):
                name = rec.get("language_of_source_name")
                if name:
                    dm["language_of_source_name"] = name

            body_text = _prefilter_text(rec)
            is_malay = bool(len(_MALAY_HINTS.findall(body_text[:600])) >= 4)

            fout.write(
                json.dumps(
                    {
                        "provision_id": rec["provision_id"],
                        "doc_id": doc_id,
                        "economy": econ,
                        "text": body_text,
                        "law_name": rec.get("law_name"),
                        "article_section": rec.get("article_section"),
                        "obligation_type": rec.get("obligation_type"),
                        "data_type": rec.get("data_type"),
                        "scope": rec.get("scope"),
                        "grounding": grounding,
                        "lang_malay_guess": is_malay,
                        "snippet_source": rec.get("snippet_source"),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            if n % 50000 == 0:
                print(f"[ingest] {n} records, {time.time()-t0:.0f}s", flush=True)

        # ---- special docs: append source_text chunks (framework §3.4d rule 1)
        special_chunks = 0
        for doc_id in SPECIAL_SOURCE_TEXT_DOCS:
            text = src_cache.get(doc_id)
            if text is None:
                print(f"[ingest] WARNING: special doc {doc_id} has no source_text")
                continue
            meta = doc_meta.get(doc_id, {})
            for ch in _chunk_source_text(doc_id, text):
                fout.write(
                    json.dumps(
                        {
                            "provision_id": ch["provision_id"],
                            "doc_id": doc_id,
                            "economy": meta.get("economy"),
                            "text": f"{meta.get('law_name','')} :: {ch['text']}",
                            "law_name": meta.get("law_name"),
                            "article_section": None,
                            "obligation_type": None,
                            "data_type": None,
                            "scope": None,
                            "grounding": "source-text-chunk",
                            "lang_malay_guess": False,
                            "snippet_source": "source_text_chunk",
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                special_chunks += 1

    (idx / "doc_meta.json").write_text(
        json.dumps(doc_meta, ensure_ascii=False), encoding="utf-8"
    )

    report = {
        "records_streamed": n,
        "special_source_text_chunks": special_chunks,
        "contract_version_mismatches": version_mismatch,
        "stats": dict(stats),
        "grounding_fail_samples": grounding_fail_samples,
        "schema_error_samples": schema_errors,
        "elapsed_seconds": round(time.time() - t0, 1),
        "gates": {
            "byte_exact_share": round(
                stats["grounding:byte-exact"] / max(n, 1), 4
            ),
            "grounding_failed": stats["grounding:FAILED"],
            "schema_sample_failures": stats["schema_sample_fail"],
        },
    }
    # ---- gates. The report is written first: a failed gate must leave its diagnosis behind.
    sampled = stats["schema_sample_ok"] + stats["schema_sample_fail"]
    failures: list[str] = []
    if schema_unavailable:
        failures.append(f"provision.schema.json could not be loaded ({schema_unavailable}); "
                        f"no record was validated against the contract")
    elif stats["schema_sample_fail"]:
        failures.append(f"{stats['schema_sample_fail']} of {sampled} sampled records fail "
                        f"provision.schema.json (first errors in schema_error_samples)")
    if stats["grounding:FAILED"]:
        failures.append(f"{stats['grounding:FAILED']} records carry a snippet that is not in "
                        f"their source text (first ids in grounding_fail_samples)")
    report["gates"]["schema_sampled"] = sampled
    report["gates"]["failures"] = failures
    report["gates"]["passed"] = not failures
    report["gates"]["enforced"] = SETTINGS.ingest_gate
    (SETTINGS.out_dir / "ingest_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report["gates"], indent=2))
    print(f"[ingest] done: {n} records + {special_chunks} chunks in {report['elapsed_seconds']}s")
    # the input document count Section 3 asks for, recorded with the engine and commit that read it
    manifest.record(
        "ingest", records=n, source_text_chunks=special_chunks,
        documents=len(doc_meta),
        by_economy={k.split(":", 1)[1]: v for k, v in sorted(stats.items())
                    if k.startswith("econ:")},
        gates=report["gates"])
    if failures:
        msg = "; ".join(failures)
        if SETTINGS.ingest_gate:
            raise IngestGateError(
                f"S0 contract gate failed: {msg}. The report is at "
                f"{SETTINGS.out_dir / 'ingest_report.json'}. INGEST_GATE=off runs anyway.")
        print(f"[ingest] GATE NOT ENFORCED (INGEST_GATE=off): {msg}")
    return report


if __name__ == "__main__":
    # The gate raises; this exit code is for the case where it is switched off.
    sys.exit(0 if run_ingest()["gates"]["passed"] else 1)
