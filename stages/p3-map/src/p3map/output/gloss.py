"""S9b — English glosses of non-English quotes, for the human reviewer only.

Checklist item 11 asks that the audit interface "can be driven by a non-technical policy officer".
Today it cannot be, for 141 of our 263 scored rows: a reviewer who does not read Chinese, Lao or
Portuguese sees a quote they have no way to check. This produces an English gloss for those rows so
the review view can show it beside the original.

Three things make this safe, and they are the whole design:

1. **It writes its own file.** `out/audit/gloss_<ECON>.jsonl`, which `output/submission.py` never
   opens. There is no code path by which a gloss can reach column I of the submission. That is
   deliberate: the standing rule is that a translated string never becomes a verbatim snippet, and
   the safest way to keep a rule is to make breaking it impossible rather than merely forbidden.
2. **The original travels with it.** Every record carries the source text it glosses, so the gloss
   is always read against the bytes rather than instead of them.
3. **It is labelled.** Every record says `machine_translation: true` and names the model. A reviewer
   is told what they are reading.

The host requires no translation anywhere -- the Output Data instructions ask column N for "the
original language of the document, not the language you translated into", and neither the README
template nor the Stage 3 Word template mentions translation at all. So this exists for our reviewer
and for criterion C3, not for compliance.

English rows are skipped: there is nothing to gloss.

    python -m src.p3map.output.gloss CN
"""
from __future__ import annotations

import json

from concurrent.futures import ThreadPoolExecutor, as_completed

from config import economies
from config import manifest
from config.llm.base import usd
from config.llm.factory import get_llm
from config.settings import SETTINGS

# The mapper's verdict rows carry no language field -- `language_of_source_name` was read here
# from the start and is absent from all 7,049 rows, so every gloss before this said "the source
# language" and left the model to infer it from the bytes. The economy knows, so ask the economy.
_LANG_NAME = {"zho": "Chinese", "lao": "Lao", "por": "Portuguese", "eng": "English",
              "tha": "Thai", "vie": "Vietnamese", "ind": "Indonesian",
              "kaz": "Kazakh", "mon": "Mongolian", "rus": "Russian"}


def _language_for(economy: str) -> str:
    return _LANG_NAME.get(economies.language(economy) or "", "the source language")

SCHEMA = {
    "type": "object",
    "properties": {
        "english": {"type": "string", "maxLength": 1200},
        "is_literal": {"type": "boolean"},
    },
    "required": ["english", "is_literal"],
}

PROMPT = """Translate this quoted passage from a {lang} legal instrument into English.

{law}, {section}

QUOTED PASSAGE:
{quote}

Translate LITERALLY, clause by clause. This gloss sits beside the original in a review screen so a
policy officer who does not read {lang} can check whether the provision says what our tool claims.
Keep legal terms of art; do not summarise, do not interpret, do not add anything the passage does
not say. If the passage is truncated mid-sentence, translate what is there and stop.

is_literal: false if the passage is too garbled (OCR noise, a fragment starting mid-word) to render
faithfully -- say so rather than inventing a clean sentence."""


def run_gloss(economy: str, limit: int = 0) -> dict:
    out_dir = SETTINGS.out_dir / "audit"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"gloss_{economy}.jsonl"

    done: set[tuple[str, str]] = set()
    if path.exists():
        with path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                done.add((r["provision_id"], r["indicator"]))

    # the quote and its metadata live in the mapper's verdicts; whether it survived is in verify
    meta: dict[tuple[str, str], dict] = {}
    with (SETTINGS.out_dir / "map" / f"verdicts_{economy}.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if "error" in r:
                continue
            for v in r.get("verdicts") or []:
                if v.get("applies") and (v.get("verbatim_quote") or "").strip():
                    meta[(r["provision_id"], v["indicator"])] = {
                        "quote": v["verbatim_quote"],
                        "law_name": r.get("law_name") or "?",
                        "article_section": r.get("article_section") or "?",
                        "language": _language_for(economy),
                    }

    # EVERY fire, not only the upheld ones. The QA Overturned sheet is where a reviewer goes to
    # challenge a rejection, and for a Chinese or Lao row they could not: 162 and 68 fires
    # respectively sat there untranslated while the upheld ones were glossed.
    todo = []
    for key, m in meta.items():
        if key not in done:
            todo.append((key, m))
    if limit:
        todo = todo[:limit]

    if not todo:
        print(f"[gloss:{economy}] nothing to gloss ({len(done)} already done)", flush=True)
        return {"economy": economy, "glossed": 0, "already": len(done), "cost_usd": 0.0}

    client = get_llm(SETTINGS, role="verifier")
    print(f"[gloss:{economy}] {len(todo)} quotes to gloss on {client.model} "
          f"(resumed past {len(done)})", flush=True)

    def one(item):
        (pid, ind), m = item
        lang = m["language"] or "the source language"
        v = client.complete(
            PROMPT.format(lang=lang, law=m["law_name"][:120],
                          section=m["article_section"], quote=m["quote"][:2000]),
            SCHEMA, max_tokens=900)
        return {"provision_id": pid, "indicator": ind, "economy": economy,
                "language_of_source": m["language"],
                "law_name": m["law_name"], "article_section": m["article_section"],
                # the original always travels with the gloss
                "original": m["quote"],
                "english": v["english"],
                "is_literal": bool(v.get("is_literal", True)),
                "machine_translation": True,
                "model": client.model,
                "note": ("Machine translation for review only. The submitted evidence is the "
                         "original text in `original`; this gloss is never filed.")}

    n = errs = rough = 0
    with path.open("a", encoding="utf-8") as fout, ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(one, it) for it in todo]
        for fut in as_completed(futs):
            try:
                row = fut.result()
            except Exception as e:                                  # noqa: BLE001
                errs += 1
                continue
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
            rough += not row["is_literal"]

    cost = usd(client.model, client.usage)
    manifest.record("gloss", economy=economy, model=client.model, glossed=n,
                    not_literal=rough, errors=errs, cost_usd=round(cost, 4))
    print(f"[gloss:{economy}] {n} glossed, {rough} flagged not literal, {errs} errors, "
          f"${cost:.2f} -> {path}", flush=True)
    return {"economy": economy, "glossed": n, "not_literal": rough,
            "errors": errs, "cost_usd": round(cost, 4)}


SECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "english": {"type": "string", "maxLength": 14000},
        "is_literal": {"type": "boolean"},
    },
    "required": ["english", "is_literal"],
}

SECTION_PROMPT = """Translate this provision from a {lang} legal instrument into English.

{law}, {section}

PROVISION:
{text}

Translate LITERALLY and in full, clause by clause, keeping the numbering and structure of the
original. This sits beside the source text in a review screen so a policy officer who does not read
{lang} can see the whole provision our tool drew a quote from. Keep legal terms of art; do not
summarise, do not interpret, do not add anything the provision does not say.

is_literal: false if the text is too garbled (OCR noise, broken segmentation) to render faithfully."""


def run_section_gloss(economy: str, limit: int = 0) -> dict:
    """Gloss the FULL provision text behind every WORKBOOK ROW, once per provision.

    Keyed by provision_id rather than by (provision, indicator): the section is the same whichever
    indicator fired on it, so glossing it once serves them all.

    Three kinds of row reach the workbook, and all three are covered:

      fires          the All fires sheet and the per-indicator sheets, QA Overturned and
                     QA Ungrounded being subsets of it
      not-in-force   QA NotInForce -- a provision the trap check flagged, which usually never
                     fired at all, so the fire-only pass skipped every one of them
      errors         QA Errors -- the provisions whose verdict failed schema validation. These
                     carry a provision_id and nothing else, so their law name and section come
                     from the corpus rather than from the verdict that did not parse.

    What is deliberately NOT glossed: a provision the mapper read and declined. It is not a row
    on any sheet -- 5,777 of them across this run -- and translating text that appears in no
    surface would cost about $14 to produce nothing a reviewer can open.
    """
    out_dir = SETTINGS.out_dir / "audit"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"gloss_sections_{economy}.jsonl"

    done: set[str] = set()
    if path.exists():
        with path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    done.add(json.loads(line)["provision_id"])
                except (json.JSONDecodeError, KeyError):
                    continue

    lang = _language_for(economy)
    want: dict[str, dict] = {}
    with (SETTINGS.out_dir / "map" / f"verdicts_{economy}.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            pid = r.get("provision_id")
            if not pid or pid in done:
                continue
            keep = "error" in r or any(v.get("applies") for v in r.get("verdicts") or [])
            if not keep and not (r.get("trap_checks") or {}).get("provision_in_force", True):
                keep = True
            if keep:
                want[pid] = {"law_name": r.get("law_name") or "",
                             "article_section": r.get("article_section") or "",
                             "language": lang}

    texts: dict[str, str] = {}
    with (SETTINGS.index_dir / "prefilter_corpus.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            pid = r["provision_id"]
            if pid in want:
                texts[pid] = r.get("text") or ""
                # an error row has no parsed verdict to name its law -- the corpus does
                m = want[pid]
                m["law_name"] = m["law_name"] or (r.get("law_name") or "?")
                m["article_section"] = m["article_section"] or (r.get("article_section") or "?")

    todo = [(p, m) for p, m in want.items() if texts.get(p, "").strip()]
    if limit:
        todo = todo[:limit]
    if not todo:
        print(f"[gloss-sections:{economy}] nothing to do ({len(done)} already done)", flush=True)
        return {"economy": economy, "glossed": 0, "already": len(done), "cost_usd": 0.0}

    client = get_llm(SETTINGS, role="verifier")
    print(f"[gloss-sections:{economy}] {len(todo)} provisions on {client.model} "
          f"(resumed past {len(done)})", flush=True)

    def one(item):
        pid, m = item
        lang = m["language"] or "the source language"
        v = client.complete(
            SECTION_PROMPT.format(lang=lang, law=m["law_name"][:120],
                                  section=m["article_section"], text=texts[pid][:9000]),
            SECTION_SCHEMA, max_tokens=6000)
        return {"provision_id": pid, "economy": economy,
                "language_of_source": m["language"],
                "law_name": m["law_name"], "article_section": m["article_section"],
                "original": texts[pid],
                "english": v["english"],
                "is_literal": bool(v.get("is_literal", True)),
                "machine_translation": True, "model": client.model,
                "note": ("Machine translation for review only. The submitted evidence is the "
                         "original text in `original`; this gloss is never filed.")}

    n = errs = rough = 0
    with path.open("a", encoding="utf-8") as fout, ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(one, it) for it in todo]
        for fut in as_completed(futs):
            try:
                row = fut.result()
            except Exception:                                       # noqa: BLE001
                errs += 1
                continue
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
            rough += not row["is_literal"]

    cost = usd(client.model, client.usage)
    manifest.record("gloss_sections", economy=economy, model=client.model, glossed=n,
                    not_literal=rough, errors=errs, cost_usd=round(cost, 4))
    print(f"[gloss-sections:{economy}] {n} glossed, {rough} not literal, {errs} errors, "
          f"${cost:.2f} -> {path}", flush=True)
    return {"economy": economy, "glossed": n, "not_literal": rough,
            "errors": errs, "cost_usd": round(cost, 4)}


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="S9b — English glosses for the review screen")
    ap.add_argument("economy")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sections", action="store_true",
                    help="gloss the FULL provision text instead of the quote, once per provision")
    a = ap.parse_args()
    (run_section_gloss if a.sections else run_gloss)(a.economy, limit=a.limit)
