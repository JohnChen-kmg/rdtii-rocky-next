"""S9 — curate verified+tagged fires into the judged 13-column output.

Curation (framework §2.8, KNOWN-biased):
- KNOWN: one row per matched baseline row — best fire wins (verification
  agree > tiebreak_upheld > pending, then confidence). Reproducing the
  baseline is rewarded; duplicates dilute.
- NEW: confidence >= NEW_CONF, quote grounded, not overturned; dedupe by
  (doc, section root, indicator); rank by confidence; per-cell caps
  (NEW_CAP, NEW_CAP_TAIL for the multi-row indicators 7.3/7.5).
- 7.1/7.2 (economy-level): only the controlling horizontal-scope row +
  up to SECTORAL_MAX sectoral records reach the CSV (framework §2.4); the
  full evidence set stays in records.json.
- No-provision rows: any (economy x indicator) cell left empty emits the
  mandatory placeholder row citing the governing law (from the baseline's
  own citation for that cell).

Outputs: out/submission/records_<ECON>.csv (13 frozen columns),
records_<ECON>.json (audit extras), and the combined Output-Data workbook
is assembled by `combine` once all economies exist.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from urllib.parse import urlsplit

from config.coverage import notification
from config.economies import ECON_NAME, language as econ_language
from config.lawnames import same_law
from config.instrument import from_artifact, load as load_instrument
from config.languages import host_name
from config.settings import INDICATORS, SETTINGS

# Baseline-law -> corpus-law similarity for a no-provision row's citation. Deliberately
# looser than NEWKNOWN_SIM: a miss here only falls back to the baseline's own (possibly mirror)
# URL, while a false positive there would mis-tag a row KNOWN.
# Indicators the codebook does not score when the obligation reaches only government or
# public-sector data. The sentence is the mapper's own trap description, which the model is
# instructed with: "not scored for 6.1-6.4, 7.3".
GOVERNMENT_DATA_EXCLUDED = frozenset({"6.1", "6.2", "6.3", "6.4", "7.3"})
NP_LAW_SIM = 0.80
# What reaches the CSV now lives in config/settings.py: a constant here could not be changed
# after the code freeze, and the live test is the run most likely to need it moved.
NEW_CONF = SETTINGS.new_conf
NEW_CAP = SETTINGS.new_cap
NEW_CAP_TAIL = SETTINGS.new_cap_tail
SECTORAL_MAX = SETTINGS.sectoral_max
# ECON_NAME (column A, the Coverage Matrix's COUNTIFS strings) now lives in config/economies.py,
# because main.py resolves the same economies at the repo root and the two must not disagree.
# The finale template adds column N, "Language of Source" (REQUIRED, "drives criterion C1c").
# Column O, "Pillar", is the host's own formula over column E -- never written here.
COLUMNS = ["Economy", "Law Name", "Law Number / Ref", "Last Amended",
           "Indicator ID", "Article / Section", "Discovery Tag",
           "Location Reference", "Verbatim Snippet", "Mapping Rationale",
           "Source URL", "Confidence", "Notes", "Language of Source"]
_VERIF_RANK = {"agree": 0, "tiebreak_upheld": 1, "pending": 2}


def np_reason(ins, indicator: str) -> str:
    """What a no-provision row says. The nine of pillars 6 and 7 keep this file's own wording, which
    the instrument copied onto their blocks; every other indicator takes its block's
    `null_statement`."""
    return _NP_REASON.get(indicator) or ins.null_statement(indicator) or "no qualifying measure found"


def absence_hint(ins, indicator: str) -> str | None:
    """The score a no-provision row carries in records.json: the block's `absence_score`, or None
    when the instrument leaves an absence unscored (an inverted indicator, 11.2, and the few whose
    answer lies outside the legislation searched). "0" on a vintage without the field, as before."""
    declared, absent = ins.absence(indicator)
    if not declared:
        return "0"
    return None if absent is None else f"{absent:g}"


def unfilable_reason(verdict: dict, trap_checks: dict, indicator: str) -> str | None:
    """Why this fire cannot be filed, or None if it can.

    Round 1 persisted `trap_checks` and read them nowhere, and gated only NEW rows on
    groundedness. Both are the difference between a row the host scores and a row it scores zero:

    - the snippet IS the evidence (column I: "Copy the EXACT text ... Verified against the
      source"), so an ungrounded quote cannot be filed whatever its discovery tag;
    - an enacted-but-not-commenced, repealed or bill-stage provision is not in force, and the
      enforced-only rule scores it zero;
    - a government-data-only obligation is not scored for 6.1-6.4 or 7.3. That is the codebook's
      rule and the one the mapper is instructed with, in the trap description it is sent.

    The confidence floor stays NEW-only on purpose, and is applied by the caller: groundedness is
    about whether the evidence exists, confidence about how sure the model is, and a
    baseline-reproducing row should not be dropped for the second.
    """
    if not verdict.get("quote_grounded_ws"):
        return "ungrounded_quote"
    if trap_checks.get("provision_in_force") is False:
        return "not_in_force"
    if (trap_checks.get("government_data_only") is True
            and indicator in GOVERNMENT_DATA_EXCLUDED):
        return "government_data_only"
    return None


def _ws(s: str) -> str:
    """Whitespace collapse for every CSV string (the Act\\n14 fix)."""
    return re.sub(r"\s+", " ", str(s or "")).strip()


def _sec_root(s: str) -> str:
    m = re.search(r"(\d+[A-Z]{0,3})", s or "")
    return m.group(1) if m else ""


def _stem_tokens(s: str) -> set[str]:
    """Law-name tokens, plural-stemmed (mirrors newknown/eval matchers)."""
    stop = {"act", "the", "of", "and", "an", "a", "law", "no"}
    out = set()
    for t in re.sub(r"[^a-z0-9 ]", "", re.sub(r"\s+", " ", (s or "").lower())).split():
        if t in stop or t.isdigit():
            continue
        if len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]
        out.add(t)
    return out


def _model_version(m: dict) -> str:
    """Host item 1: 'LLM + OCR version used' — factual composite of the
    upstream extraction stamps and this repo's mapping/verification models.
    Absent components are omitted, never guessed (no-provision rows and
    source-text-anchored rows have no per-provision extraction record)."""
    parts = []
    if m.get("extraction_model"):
        parts.append(f"extraction: {m['extraction_model']}")
    if m.get("ocr_engine"):
        parts.append(f"OCR: {m['ocr_engine']}")
    parts.append(f"mapping: {SETTINGS.llm_model}")
    parts.append(f"verification: {SETTINGS.verifier_model} "
                 f"(+{SETTINGS.escalation_model} tiebreak)")
    return "; ".join(parts)


# reason text for the contract §6 no-provision variant (blank Notes/blank
# Article-Section are named point-loss triggers)
_NP_REASON = {
    "6.1": "no complete cross-border transfer-prohibition measure found",
    "6.2": "no data-storage/localization measure found in the corpus",
    "6.3": "no local data-processing or infrastructure-localization "
             "requirement found in the corpus",
    "6.4": "no conditional cross-border transfer measure found in the corpus",
    "7.1": "no personal-data-protection framework evidence collected",
    "7.2": "no cybersecurity framework evidence collected",
    "7.3": "no minimum data-retention measure found in the corpus",
    "7.4": "no statutory DPO-appointment or DPIA mandate found in the corpus "
             "(guidance-only instruments are non-binding and not scored)",
    "7.5": "no government-access measure found in the corpus",
}



def multi_act_caveat(act_index, act_count) -> tuple[str, str]:      # noqa: ANN001
    """Say so when the Law Name may belong to a different act in the same source file.

    Measured 29 September 2026: of 364 Timorese gazette documents holding more than one act, **364
    carry a single document-level `law_name` across every act inside them and 0 vary by act.** The
    extractor identifies the acts -- `act_index` and `act_count` are populated and look right -- but
    never resolves the title per act, and reports `citation_confidence: "exact"` regardless. A
    Jornal da Republica issue can hold 22 separate acts, so every act but one is mislabelled.

    Hand-verified case: a credit-registry provision requiring retention "not less than ten years"
    (a correct 7.3 hit at confidence 0.9) is titled "Primeira alteracao da Lei n.o 3/2006
    (Estatuto dos Combatentes da Libertacao Nacional)", with a `law_name_en` about the monthly food
    allowance for National Police officers -- three unrelated subjects for one provision.

    Of Timor-Leste's 65 filed provisions: 13 come from single-act files (safe), 19 are act 1 of a
    multi-act file (probably the title's own act, since a gazette's document-level title is normally
    its first), 23 are a later act (the title is almost certainly wrong) and 10 have no act_index at
    all. So 33 of 65 -- 51% -- carry a citation that cannot be defended as written.

    This is upstream, and the standing rule is that findings go back to the extraction workshop as
    notes rather than edits. Mapping's defence is to stop asserting what it cannot support: the
    provision, quote, article and URL are all correct and verifiable, so the row is kept and the ONE
    field in doubt is marked. Deleting the row would throw away good evidence over a bad label.

    Three cases, not one, because one identical warning on 52 of Timor-Leste's 110 rows is noise a
    reader learns to skip. "A gazette's document-level title names its first act" is an inference
    from ordering, NOT verified against the PDFs, so act 1 is stated as probable rather than either
    warned about as if it were wrong or silently exempted on the strength of an unverified guess.

    Returns (bucket, note); bucket is "" when there is nothing to say.
    """
    if not isinstance(act_count, int) or act_count <= 1:
        return "", ""
    lead = (f"CITATION CAVEAT: the source file is a gazette issue containing {act_count} separate "
            "acts, and the upstream extraction records one title for the whole file rather than one "
            "per act. The article, quoted text and URL are verified. ")
    if act_index == 1:
        return "first_act", lead + (
            "This provision is in the first act of the issue, which is normally the act the file's "
            "title names — so the Law Name is probably right, but that ordering is an inference we "
            "have not confirmed against the source")
    if isinstance(act_index, int):
        return "later_act", lead + (
            f"This provision is in act {act_index} of {act_count}, so the Law Name most likely "
            "belongs to a different act in the same issue and must be confirmed against the source "
            "before this row is relied on")
    return "act_unknown", lead + (
        "Which act this provision belongs to was not recorded, so the Law Name cannot be checked "
        "against it at all; confirm against the source before relying on this row")


def searched_but_found_nothing(econ_display: str,
                               corpus_laws: list[dict]) -> tuple[str, str, str, str, bool]:
    """The citation for a no-provision row in an economy with NO baseline row to follow.

    Round 1's rule here was "cite the largest law in the corpus", used as a proxy for "the governing
    law". It is a bad proxy: the largest statute in a civil-law jurisdiction is the civil code, so
    for Timor-Leste it produced 45 rows naming "Aprova o Codigo Civil" -- the decree that ENACTS the
    code, not the code itself -- as the governing law for data localisation, data-centre rules and
    cross-border transfer. A marker can open that PDF and disprove it in a minute.

    So name no law, and instead say what WAS searched, which is checkable and true. No URL either: a
    no-provision row is already outside the scored-row completeness gate (it has no snippet), and a
    portal root in a column the host reads as law-level would be padding rather than evidence. The
    host is named in the reason instead -- every economy's corpus comes from a single portal for
    97-100% of its documents, so naming it states a fact about the search rather than a guess.

    Returns the same 5-tuple as the baseline paths: (name, number, url, language, named_a_real_law).
    """
    if corpus_laws:
        hosts = Counter(urlsplit(d["source_url"]).netloc for d in corpus_laws
                        if (d.get("source_url") or "").startswith("http"))
        where = f" from {hosts.most_common(1)[0][0]}" if hosts else ""
        return (f"{econ_display} — no governing instrument identified", "",
                f"n/a — {len(corpus_laws):,} {econ_display} instruments{where} searched, "
                "none governing this indicator", "", False)
    return (f"{econ_display} legal framework (no corpus available)", "",
            "n/a — hold-out economy without corpus or baseline "
            "(documented placeholder)", "", False)


def kit_absence_state(rows_here: list[dict]) -> str:
    """Which of three states this cell is in, for a no-provision row's Discovery Tag.

        The host defines the column with two values only: "NEW = your tool found it and it is not
        in the 2025 baseline you hold. KNOWN = it was in the sample kit." A no-provision row is
        neither in general -- decision H4 -- so the tag is earned, not assumed:

        - "reproduces"  the kit carries its own absence row here (score 0, no article cited), so
                        KNOWN is literally true: we reproduce that row.
        - "contradicts" the kit records a measure this run did not find. That is a disagreement,
                        not a reproduction, and KNOWN would conceal a miss.
        - "absent"      the kit has no row for this cell at all (every Timor-Leste cell).

        Reading the baseline to set this column is not backward induction: KNOWN *means* "was in
        the sample kit", so deciding it requires reading the kit. What the standing rule forbids is
        letting the baseline choose what we map or how we score, which this does not.
        """
    if not rows_here:
        return "absent"
    for b in rows_here:
        arts = str(b.get("articles_mentioned") or "").strip()
        raw = b.get("raw_score")
        score = str(raw if raw is not None else (b.get("score") or "")).strip()
        if arts in ("", "[]", "None") and score in ("0", "0.0"):
            return "reproduces"
    return "contradicts"

def run_submission(economy: str) -> dict:
    # --- joins: tags, mapper verdicts (quote/rationale/conf), provision meta
    # Missing stage inputs are tolerated (hold-out robustness, follow-up item
    # 2): an economy with no pipeline artifacts still emits a valid
    # all-no-provision CSV instead of crashing the judges' re-run.
    tags = []
    nk_path = SETTINGS.out_dir / "discovery" / f"newknown_{economy}.jsonl"
    if nk_path.exists():
        with nk_path.open(encoding="utf-8") as f:
            for line in f:
                t = json.loads(line)
                t["indicator"] = from_artifact(t["indicator"])
                tags.append(t)

    mapv: dict[tuple[str, str], dict] = {}
    traps: dict[str, dict] = {}
    prov_row: dict[str, dict] = {}
    mv_path = SETTINGS.out_dir / "map" / f"verdicts_{economy}.jsonl"
    if mv_path.exists():
        with mv_path.open(encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                if "error" in row:
                    continue
                prov_row[row["provision_id"]] = row
                traps[row["provision_id"]] = row.get("trap_checks") or {}
                for v in row["verdicts"]:
                    mapv[(row["provision_id"], from_artifact(v["indicator"]))] = v

    # metadata join + offsets for re-anchoring synthetic source-text-chunk ids
    # (audit 2026-07-16 item 1: "st.*" fires shipped with empty URL/section)
    wanted = {t["provision_id"] for t in tags}
    st_docs = {t["doc_id"] for t in tags if re.search(r"#st\.\d+$", t["provision_id"])}
    meta: dict[str, dict] = {}
    doc_provisions: dict[str, list[dict]] = defaultdict(list)
    if wanted or st_docs:  # hold-out economies skip the 638MB stream
        with (SETTINGS.handoff2_dir / "provisions.jsonl").open(encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                keep_meta = r["provision_id"] in wanted
                keep_offsets = r["doc_id"] in st_docs
                if not (keep_meta or keep_offsets):
                    continue
                m = {"law_number": r.get("law_number") or "",
                     "last_amended": r.get("last_amended") or "",
                     # column N. The provision record names the language; laws.jsonl carries the
                     # ISO code, which doc_lang below supplies when this is empty.
                     "language_of_source": host_name(r.get("language_of_source_name")),
                     "source_url": r.get("source_url") or "",
                     "location_reference": r.get("location_reference") or "",
                     # host JSON extras (follow-up item 1): raw upstream values;
                     # None stays None — never fabricate an OCR score or timing
                     "source_pdf_path": r.get("source_file_path"),
                     "ocr_quality_cer": r.get("ocr_quality_cer"),
                     "processing_time": r.get("processing_time_seconds"),
                     "extraction_model": r.get("extraction_model"),
                     "ocr_engine": r.get("ocr_engine"),
                     # Which act inside the source file this provision belongs to. Needed because
                     # upstream does not resolve `law_name` per act -- see _multi_act_caveat.
                     "act_index": r.get("act_index"),
                     "act_count": r.get("act_count"),
                     "raw_context": {"before": r.get("raw_context_before") or "",
                                     "after": r.get("raw_context_after") or ""}}
                if keep_meta:
                    meta[r["provision_id"]] = m
                if keep_offsets and isinstance(r.get("snippet_char_start"), int):
                    doc_provisions[r["doc_id"]].append({
                        "provision_id": r["provision_id"],
                        "article_section": r.get("article_section") or "",
                        "s": r["snippet_char_start"], "e": r["snippet_char_end"],
                        **m})

    doc_urls: dict[str, str] = {}
    doc_lang: dict[str, str] = {}
    corpus_laws: list[dict] = []
    with (SETTINGS.handoff2_dir / "laws.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            doc_urls[r["doc_id"]] = r.get("source_url") or ""
            doc_lang[r["doc_id"]] = host_name(r.get("language_of_source"))
            corpus_laws.append({k: r.get(k) for k in (
                "doc_id", "economy", "law_name", "law_name_en", "law_name_en_source",
                "law_number",
                "source_url", "provision_count")})

    _sec_line = re.compile(
        r"^\s*(\d{1,4}[A-Z]{0,3})\.(?:—|–|-|\s*\()", re.MULTILINE)

    def _reanchor(t: dict, quote: str) -> tuple[dict, str] | None:
        """Map a synthetic st.* fire onto its real provision (or doc fallback).
        Returns (meta_dict_with_section, note) or None to drop."""
        doc_id = t["doc_id"]
        src = SETTINGS.handoff2_dir / "source_text" / f"{doc_id}.txt"
        if not src.exists():
            return None
        text = src.read_text(encoding="utf-8", errors="replace")
        flat, flat_q = _ws(text).lower(), _ws(quote).lower()
        pos = flat.find(flat_q)
        if pos < 0:
            return None
        # flat position ~ raw position (whitespace collapse shifts are small);
        # scale to raw offset for window matching
        raw_pos = int(pos * (len(text) / max(len(flat), 1)))
        for p in doc_provisions.get(doc_id, []):
            if p["s"] - 500 <= raw_pos <= p["e"] + 500:
                return ({**p}, f"re-anchored from source-text chunk to {p['provision_id']}")
        # segmentation gap: doc-level fallback with derived section heading
        sec = ""
        for m in _sec_line.finditer(text, 0, min(raw_pos + 1, len(text))):
            sec = f"s.{m.group(1)}"
        if not doc_urls.get(doc_id):
            return None
        return ({"provision_id": t["provision_id"], "article_section": sec,
                 "law_number": "", "last_amended": "",
                 "source_url": doc_urls[doc_id], "location_reference": "",
                 # synthetic chunk: no upstream extraction record — nulls are
                 # the honest values, not omissions
                 "source_pdf_path": None, "ocr_quality_cer": None,
                 "processing_time": None, "extraction_model": None,
                 "ocr_engine": None, "raw_context": None},
                "anchored to source text (segmentation gap in extraction)")

    baseline_cells: dict[str, list[dict]] = defaultdict(list)
    bl_path = SETTINGS.out_dir / "baseline_rows.jsonl"
    if bl_path.exists():
        with bl_path.open(encoding="utf-8") as f:
            for line in f:
                b = json.loads(line)
                if b["in_p3_scope"] and b["economy"] == economy:
                    baseline_cells[b["indicator"]].append(b)

    # Two doc_ids can be the same law. The crawl fetched several Chinese statutes from BOTH
    # cac.gov.cn and flk.npc.gov.cn -- 20 CN law names carry two doc_ids each in handoff2, the
    # Cybersecurity Law, PIPL, the E-commerce Law and the Data Security Law among them. Dedupe keyed
    # on doc_id cannot see across those copies, which filed 5 duplicate China rows: the same
    # indicator, law and article twice. The submission's own note says duplicates dilute.
    #
    # This groups doc_ids by law identity using config.lawnames' tested matcher, so the dedupe key
    # below is the LAW rather than the document. A doc with no usable name keeps its own doc_id, so
    # nothing collapses by accident.
    _name_of_doc = {t["doc_id"]: _ws(t.get("law_name") or "") for t in tags}
    _law_of_doc: dict[str, str] = {}
    _law_groups: list[tuple[str, str]] = []          # (canonical key, a name in that group)
    for _d in sorted(_name_of_doc):
        _nm = _name_of_doc[_d]
        if not _nm:
            _law_of_doc[_d] = _d
            continue
        for _key, _seen_nm in _law_groups:
            if same_law(_nm, _seen_nm) or same_law(_seen_nm, _nm):
                _law_of_doc[_d] = _key
                break
        else:
            _law_groups.append((_d, _nm))
            _law_of_doc[_d] = _d
    _collapsed = len({d for d, k in _law_of_doc.items() if d != k})
    if _collapsed:
        print(f"[submission:{economy}] {_collapsed} document(s) collapsed into another copy of the "
              f"same law for dedupe (duplicate crawl)", flush=True)

    def _law_key(t: dict) -> str:
        return _law_of_doc.get(t["doc_id"], t["doc_id"])

    # Where an English title may and may not go.
    #
    # The host requires no translation anywhere: column N asks for "the original language of the
    # document, not the language you translated into", the checklist asks only that a non-English
    # source be recorded there, and neither the README template nor the Stage 3 Word template
    # mentions translation. So an English title is our own aid to a reader.
    #
    # It cannot be a new column: data runs A to N and O9 holds the host's own Pillar formula, which
    # the Coverage Matrix reads through COUNTIFS($O$9:$O$109, 1, ...). A fifteenth data column would
    # overwrite it and count zero provisions for every economy, on the sheet C1a is read from.
    #
    # And it does not belong in column B either, because outside AU/MY/SG every English title we
    # hold is machine-made (law_name_en_source == "rendered"). It goes to Notes, labelled, which is
    # what decision M10 says. Column I is never touched: the quoted provision is the evidence and a
    # translated string never becomes a verbatim snippet.
    _en_of_doc = {d["doc_id"]: _ws(d.get("law_name_en") or "") for d in corpus_laws}
    _en_src_of_doc = {d["doc_id"]: str(d.get("law_name_en_source") or "") for d in corpus_laws}

    def _english_title_note(t: dict) -> str:
        """A Notes clause carrying the English title, labelled when it is machine-made.

        The host requires NO translation anywhere: column N asks for "the original language of the
        document, not the language you translated into", the checklist asks only that a non-English
        source be recorded there, and neither the README template nor the Stage 3 Word template
        mentions translation at all. So an English title is our own aid to a reader, not compliance.

        It therefore does not belong in column B. Extraction records law_name_en_source, and for
        every economy whose law is not already in English the value is `rendered` -- machine-made:
        1,085 Chinese laws, 1,762 Lao, 2,877 Timorese. Putting one of those in the Law Name column
        would present a machine translation AS the law's name, unlabelled, in a content column.
        Decision M10 settled the placement: a translation we file lives in the Notes or the
        rationale. This is the Notes form, and it says which kind of English it is.
        """
        orig = _ws(t.get("law_name") or "")
        eng = _en_of_doc.get(t.get("doc_id"), "")
        if not eng or eng == orig:
            return ""
        src = _en_src_of_doc.get(t.get("doc_id"), "")
        if src == "rendered":
            return f"English title (machine-rendered, not official): {eng}"
        return f"English title: {eng}"

    def _kit_absence(ind: str) -> str:
        return kit_absence_state(baseline_cells.get(ind) or [])

    econ_display = ECON_NAME.get(economy, economy)  # hold-out safe (item 2a)

    def _np_citation(ind: str) -> tuple[str, str, str, str, bool]:
        """Governing-law citation for a no-provision row: (name, number, ONE
        working law-level URL, language, named_a_real_law). Canonical-URL rule: prefer the official
        corpus source_url over the baseline's own link (which can be a mirror). The language is the
        cited document's own, and "" where the citation comes from the baseline rather than the
        corpus -- column N is required, so a blank has to be visible rather than assumed.

        The last element says whether a real instrument was named, because Notes must not claim a
        governing law was "cited for reference" on a row that cites none."""
        b = (baseline_cells.get(ind) or [{}])[0]
        law_first = _ws(re.split(r"[;\n]", b.get("law") or "")[0])
        if law_first:
            bt = _stem_tokens(law_first)
            for d in corpus_laws:
                if d["economy"] != economy or not d.get("source_url"):
                    continue
                dt = _stem_tokens(d.get("law_name") or "")
                if bt and dt and len(bt & dt) / min(len(bt), len(dt)) >= NP_LAW_SIM:
                    return (d["law_name"], d.get("law_number") or "",
                            d["source_url"], doc_lang.get(d["doc_id"], ""), True)
            url = next((u.strip().rstrip(";") for u in (b.get("urls") or [])
                        if u.strip().startswith("http")), "")
            return law_first, "", url, "", True
        # No baseline for this economy. Round 1's rule here was "cite the largest law in the
        # corpus" -- a proxy for "the governing law", and a bad one. The largest statute in a
        # civil-law jurisdiction is the civil code, so for Timor-Leste this produced 45 rows naming
        # "Aprova o Codigo Civil" -- the decree that ENACTS the code, not the code itself -- as the
        # governing law for data localisation, data-centre rules and cross-border transfer. A
        # marker can open that PDF and disprove it. Naming nothing is merely unhelpful, and this
        # row's whole job is to say we searched and found nothing: so say that, and say how widely.
        return searched_but_found_nothing(
            econ_display, [d for d in corpus_laws if d["economy"] == economy])

    # --- curation
    def fire_key(t):  # noqa: ANN001
        return (_VERIF_RANK.get(t["verification"], 2),
                -mapv[(t["provision_id"], t["indicator"])]["confidence"])

    rows: list[dict] = []
    dropped: dict[str, int] = defaultdict(int)
    # rows whose Law Name may name the wrong act in a multi-act gazette issue, per indicator.
    # Reported, because "51% of Timor-Leste's citations are uncertain" must be a number in the
    # stage report rather than something a reader has to grep the Notes column to discover.
    caveated: dict[str, int] = defaultdict(int)

    def _filed(t_: dict, ind_: str) -> bool:
        reason = unfilable_reason(mapv[(t_["provision_id"], ind_)],
                                 traps.get(t_["provision_id"], {}), ind_)
        if reason:
            dropped[reason] += 1
            return False
        return True

    ins = load_instrument()
    for ind in INDICATORS:
        cell = [t for t in tags if t["indicator"] == ind]
        keep: list[tuple[dict, str]] = []  # (tag, note)
        # Economy-level is the codebook's word, not a literal here; rollup.py reads the same
        # field. On the Round 1 vintage, which carries no `level`, the loader falls back to
        # exactly the 7.1/7.2 pair this line used to hard-code.
        if ins.level(ind) == "economy":
            cell = [t for t in cell if _filed(t, ind)]
            horiz = sorted([t for t in cell
                            if mapv[(t["provision_id"], ind)]["coverage"] == "Horizontal"],
                           key=fire_key)
            # sectoral picks: baseline-matched laws first (reproduce the
            # baseline's own sectoral records), then by verification/confidence
            sect = sorted([t for t in cell
                           if mapv[(t["provision_id"], ind)]["coverage"] == "Sectoral"],
                          key=lambda t: (t["baseline_match"] is None, *fire_key(t)))
            if horiz:
                keep.append((horiz[0], "controlling horizontal framework evidence"))
            seen_laws: set[str] = set()
            for t in sect:
                if len(seen_laws) >= SECTORAL_MAX:
                    break
                lk = _ws(t["law_name"]).lower()
                if lk in seen_laws:
                    continue
                seen_laws.add(lk)
                keep.append((t, "sectoral framework recorded, not controlling"))
        else:
            known = [t for t in cell if t["discovery_tag"] == "KNOWN"]
            by_baseline: dict[str, list[dict]] = defaultdict(list)
            for t in known:
                by_baseline[t["baseline_match"]].append(t)
            for bid, group in sorted(by_baseline.items()):
                # prefer a filable fire for this baseline row; lose the row only if none of its
                # fires can be filed, which keeps the reproduction guarantee intact
                filable = [t for t in group if _filed(t, ind)]
                if not filable:
                    print(f"[submission] DROP KNOWN {bid} ({ind}): no filable fire among "
                          f"{len(group)}", flush=True)
                    continue
                keep.append((sorted(filable, key=fire_key)[0],
                             f"matches baseline {bid}"))
            news = [t for t in cell if t["discovery_tag"] == "NEW"
                    and mapv[(t["provision_id"], ind)]["confidence"] >= NEW_CONF
                    and _filed(t, ind)]
            seen: set[tuple] = set()
            deduped = []
            for t in sorted(news, key=fire_key):
                k = (_law_key(t), _sec_root(t["article_section"]))
                if k in seen:
                    continue
                seen.add(k)
                deduped.append(t)
            # baseline-law reproduction guarantee: every baseline row whose law
            # fired gets its best fire, outside the NEW cap — the host rewards
            # reproducing the baseline; caps must never starve it
            reproduced = {t2["baseline_match"] for t2, _ in keep
                          if t2.get("baseline_match")}
            guaranteed = []
            for t in deduped:
                if (t.get("baseline_match")
                        and t["baseline_match"] not in reproduced):
                    reproduced.add(t["baseline_match"])
                    guaranteed.append(t)
            cap = NEW_CAP_TAIL if ind in ("7.3", "7.5") else NEW_CAP
            rest = [t for t in deduped if t not in guaranteed]
            for t in guaranteed + rest[:cap]:
                keep.append((t, t["match_evidence"]))

        for t, note in keep:
            v = mapv[(t["provision_id"], t["indicator"])]
            m = meta.get(t["provision_id"], {})
            notes = [note]
            art_sec = t["article_section"]
            if re.search(r"#st\.\d+$", t["provision_id"]):
                ra = _reanchor(t, v["verbatim_quote"])
                if ra is None:
                    print(f"[submission] DROP synthetic fire without anchor: "
                          f"{t['provision_id']} {t['indicator']}")
                    continue
                m, ra_note = ra
                art_sec = m.get("article_section") or art_sec
                notes.append(ra_note)
            if t["verification"] == "pending":
                notes.append("verification pending")
            # decisions M8/M9: where this economy's portal does not publish the tier that answers
            # an indicator we do automate, the verdict stands and the row says what it rests on.
            # China's pillar 6 is the case today (coverage register, per-economy section).
            caveat = notification(t["indicator"], economy)
            if caveat:
                notes.append(caveat)
            _en_note = _english_title_note(t)
            if _en_note:
                notes.append(_en_note)
            # The Law Name may belong to another act in the same gazette issue -- upstream records
            # one title per FILE, not per act. Everything else on the row is verified, so the row
            # stands and the single field in doubt is marked. See multi_act_caveat.
            _ma_bucket, _ma = multi_act_caveat(m.get("act_index"), m.get("act_count"))
            if _ma:
                notes.append(_ma)
                caveated[_ma_bucket] += 1
            rows.append({
                "Economy": econ_display,
                "Law Name": _ws(t["law_name"]),
                "Law Number / Ref": _ws(m.get("law_number")),
                "Last Amended": _ws(m.get("last_amended")),
                "Indicator ID": t["indicator"],
                "Article / Section": _ws(art_sec),
                "Discovery Tag": t["discovery_tag"],
                "Location Reference": _ws(m.get("location_reference")),
                "Verbatim Snippet": _ws(v["verbatim_quote"]),
                "Mapping Rationale": _ws(v["rationale"])[:300],
                # URLs are exempt from _ws: internal double spaces are
                # significant on the MY LOM portal (collapse 500'd 2 links —
                # urlcheck 2026-07-16); strip ends only
                "Source URL": str(m.get("source_url") or "").strip(),
                "Confidence": v["confidence"],
                "Notes": _ws("; ".join(notes)),
                "Language of Source": (m.get("language_of_source")
                                       or doc_lang.get(t["doc_id"], "")),
                # host JSON extras (follow-up item 1) — JSON only; the CSV
                # writer's fixed COLUMNS + extrasaction="ignore" drop them
                "source_pdf_path": m.get("source_pdf_path"),
                "ocr_quality_cer": m.get("ocr_quality_cer"),
                "processing_time": m.get("processing_time"),
                "model_version": _model_version(m),
                "raw_context": m.get("raw_context"),
                "_record_type": "scored",
                "_provision_id": t["provision_id"],
                "_score_hint": t["score_hint"],
            })

    # second pass: no-provision rows are emitted only after every indicator's
    # scored rows exist, so cross-references ("see the 6.4 rows") can see
    # the whole row set regardless of indicator order
    for ind in INDICATORS:
        if not any(r for r in rows if r["Indicator ID"] == ind):
            # contract §6 no-provision variant: Article/Section = "n/a",
            # governing law name+number+exactly ONE working law-level URL,
            # and the REASON in Notes (follow-up item 3)
            np_law, np_num, np_url, np_lang, np_named_law = _np_citation(ind)
            # Column N is REQUIRED and drives C1c. _np_citation returns "" when the citation comes
            # from the baseline rather than the corpus, which left 4 of Lao's 25 rows blank. The
            # language of a Lao statute is not a guess, so it is filled from the economy's language
            # of legislation and Notes says that is where it came from -- a visible provenance
            # claim rather than a silent blank in a required column.
            np_lang_note = ""
            if not np_lang:
                code = econ_language(economy)
                if code:
                    np_lang = host_name(code)
                    np_lang_note = ("Language of Source is the economy's language of legislation, "
                                    "not a per-document reading: this row cites "
                                    + ("a governing law from the baseline rather than a corpus "
                                       "document" if np_named_law else "no document"))
            np_caveat = notification(ind, economy)
            reason = np_reason(ins, ind)
            if ind == "6.1" and any(r["Indicator ID"] == "6.4"
                                      and r["_record_type"] == "scored"
                                      for r in rows):
                reason += (f"; the {econ_display} regime is conditional-flow"
                           " — see the 6.4 rows")
            # H4: the tag is earned from the sample kit, not assumed. Round 1 wrote KNOWN
            # unconditionally, which claimed "it was in the sample kit" for cells where it was not.
            kit = _kit_absence(ind)
            np_tag = "KNOWN" if kit == "reproduces" else ""
            np_note = {
                "reproduces": "reproduces the 2025 baseline's own absence row for this indicator",
                "contradicts": ("the 2025 baseline records a measure for this indicator that this "
                                "run did not find; Discovery Tag left blank because the row is "
                                "neither a discovery nor a baseline reproduction"),
                "absent": ("no 2025 baseline row exists for this economy and indicator; Discovery "
                           "Tag left blank because the row is neither a discovery nor a baseline "
                           "reproduction"),
            }[kit]
            rows.append({
                "Economy": econ_display,
                "Law Name": _ws(np_law),
                "Law Number / Ref": _ws(np_num), "Last Amended": "",
                "Indicator ID": ind, "Article / Section": "n/a",
                "Discovery Tag": np_tag,
                "Location Reference": "",
                "Verbatim Snippet": "No provision found",
                "Mapping Rationale": "No qualifying measure identified in the corpus for this indicator",
                "Source URL": str(np_url or "").strip(),  # URLs: no _ws
                "Confidence": "",
                "Notes": _ws("; ".join(
                    [f"no-provision row: {reason}", np_note,
                     "governing law cited for reference" if np_named_law else
                     "no governing instrument is named because none was identified: naming the "
                     "economy's largest statute would assert a legal relationship we did not find"]
                    + ([np_lang_note] if np_lang_note else [])
                    + ([np_caveat] if np_caveat else []))),
                "Language of Source": np_lang,
                "source_pdf_path": None, "ocr_quality_cer": None,
                "processing_time": None,
                "model_version": _model_version({}),
                "raw_context": None,
                "_record_type": "no_provision", "_provision_id": "",
                "_score_hint": absence_hint(ins, ind),
            })

    # hard audit-trio gate (rubric FAIL trigger): every SCORED row must carry
    # a non-empty Article/Section, Verbatim Snippet, and Source URL
    violations = [r for r in rows if r["_record_type"] == "scored"
                  and not (r["Article / Section"] and r["Verbatim Snippet"]
                           and r["Source URL"])]
    if violations:
        for r in violations:
            print(f"[submission] AUDIT-TRIO VIOLATION dropped: "
                  f"{r['Indicator ID']} {r['Law Name'][:40]} "
                  f"pid={r['_provision_id']}")
        rows = [r for r in rows if r not in violations]

    out_dir = SETTINGS.out_dir / "submission"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"records_{economy}.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    # host JSON shape (follow-up item 1): provisions grouped per law —
    # "array — all rows for one law"; contract_version + economy top-level
    by_law: dict[tuple, dict] = {}
    law_order: list[tuple] = []
    for r in rows:
        k = (r["Law Name"], r["Law Number / Ref"])
        if k not in by_law:
            by_law[k] = {"law_name": r["Law Name"],
                         "law_number": r["Law Number / Ref"],
                         "source_url": r["Source URL"],
                         "provisions": []}
            law_order.append(k)
        by_law[k]["provisions"].append(r)
    (out_dir / f"records_{economy}.json").write_text(
        json.dumps({"contract_version": SETTINGS.contract_version,
                    "economy": economy, "economy_name": econ_display,
                    "laws": [by_law[k] for k in law_order]}, indent=1,
                   ensure_ascii=False), encoding="utf-8")

    per = defaultdict(int)
    for r in rows:
        per[f"{r['Indicator ID']}|{r['Discovery Tag']}"] += 1
    # H4 leaves the Discovery Tag blank where a no-provision row is neither a discovery nor a
    # baseline reproduction. The host's Instructions say the column takes two values, so a blank is
    # a deliberate, disclosed choice and must be countable rather than silent: if a template check
    # rejects it, this number says how many rows to revisit.
    blank_tag = [r["Indicator ID"] for r in rows if not str(r["Discovery Tag"]).strip()]
    report = {"economy": economy, "csv_rows": len(rows), "cells": dict(sorted(per.items())),
              "blank_discovery_tag": {"count": len(blank_tag), "indicators": sorted(blank_tag)},
              "dropped_before_curation": dict(sorted(dropped.items())),
              "multi_act_citation_caveat": {
                  "count": sum(caveated.values()),
                  "by_confidence": dict(sorted(caveated.items())),
                  "why": ("the source file is a gazette issue holding several acts and upstream "
                          "records one title per file, not per act; the article, quote and URL are "
                          "verified, the Law Name may name a different act in the same issue. "
                          "first_act = probably correct (unverified ordering inference); "
                          "later_act = most likely wrong; act_unknown = uncheckable")}}
    (out_dir / f"submission_report_{economy}.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[submission:{economy}] {len(rows)} rows -> {csv_path}")
    if dropped:
        print(f"   dropped before curation: {json.dumps(dict(sorted(dropped.items())))}")
    for k, n in sorted(per.items()):
        print(f"   {k}: {n}")
    if blank_tag:
        print(f"   Discovery Tag left BLANK on {len(blank_tag)} no-provision row(s) "
              f"({', '.join(sorted(blank_tag))}): neither a discovery nor a baseline "
              f"reproduction (H4). Disclosed, not an error.")
    return report


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="S9 emit: the filed rows for one economy, 14 columns in the host's order. Drops a row the zero-score filters refuse and says why in the report.")
    ap.add_argument("economy", nargs="?", default="SG")
    a = ap.parse_args()
    run_submission(a.economy)
