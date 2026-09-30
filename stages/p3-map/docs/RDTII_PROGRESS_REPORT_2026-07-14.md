# RDTII Rocky — Progress Report & Next-Stage Plan

**Project:** Open-source engine for evidence-based RDTII 2.1 indicator mapping
**Team:** Rocky has a home run (John Chen, solo)
**Date:** 14 July 2026 · **Stage:** 2 of 3 complete · Round-1 deadline 20 July 2026

---

## 1. Executive summary

RDTII Rocky is an open-source (Apache-2.0), CPU-runnable pipeline that crawls
official government legal portals, extracts legislation at the individual-
provision level with verbatim, offset-verified citations, and maps the
evidence to the nine RDTII 2.1 indicators across Pillars 6 and 7.

As of this report, **two of the three pipeline stages are complete and
verified at full corpus scale**:

> **2,616 laws** from Singapore, Australia and Malaysia → **305,980
> grounded Provision-Records**, every quoted snippet byte-verified against
> its frozen source text, tagged and audit-ready — produced in one overnight
> run for **US$107.29 total** (≈ 4.1¢ per law), with a measured **$0 local
> fallback** that reproduces identical citations without any API key.

The remaining stage (indicator mapping and scoring — Project 3) consumes
this corpus and produces the final 13-column submission CSV.

## 2. System architecture (what exists today)

Three independent repositories wired only by validated file hand-offs — no
shared code, each stage re-runnable and auditable in isolation:

| Stage | Repository | Status | Output |
|---|---|---|---|
| 1 · Retrieve | `rdtii-p1-scrape` | ✅ complete | 2,616 laws (~6.7 GB raw HTML/PDF) + 28-field manifest, 0 validation errors |
| 2 · Extract & tag | `rdtii-p2-extract` | ✅ complete | 305,980 Provision-Records + frozen source texts + per-doc OCR quality reports |
| 3 · Map & score | `rdtii-p3-map` | ▶ next stage | Final 13-column CSV/JSON vs the 9 indicators, NEW/KNOWN evidence diff |

Two design rules govern everything:

- **Grounding — "no quote = no record."** The LLM never writes quoted bytes;
  it only points. Quote bytes are copied from the frozen source text and
  re-verified by character offsets at emit time *and* again by an offline
  `validate` command any reviewer can run.
- **Model-swap spine.** Every model-bearing engine (LLM, OCR) is selected by
  one `.env` line behind a common interface. An empty API key automatically
  falls back to fully local models, loudly — the judge's no-key run is a
  first-class path, not an afterthought.

## 3. Measured results (nothing below is an estimate)

| Metric | Result |
|---|---|
| Laws processed | 2,616 / 2,616 (SG · AU · MY) |
| Provision-Records | 305,980 (SG 94,892 · AU 157,204 · MY 53,884) |
| Extraction lanes | native PDF 224,080 · portal HTML 57,975 · **OCR 23,925** |
| Scanned pages OCR'd | 12,292 (Tesseract 5.4, cached & re-runnable) |
| **OCR accuracy (rubric item)** | **CER 2.72%** on the committed reference page, re-measured *live* by the demo command — meets the <5% bar; pilot pages 0.93% / 2.72% |
| Verification gates | schema ✅ · byte-exact grounding on all 305,980 quotes ✅ · doc-status/manifest completeness ✅ · unique record ids ✅ |
| **Cost, API showcase lane** | **$107.29 total ≈ 4.1¢/law** (Claude Haiku 4.5 via Batches API, four batches itemized in `cost_report.json`) |
| **Cost, local fallback lane** | **$0** at a measured 1.02 provisions/second on one consumer GPU |
| Cross-model reproducibility | Citations/offsets/metadata **byte-identical 309/309** across qwen2.5:14b, llama3.1:8b, Claude Haiku 4.5 |
| Automated tests | 82, all green |
| Cross-border signal for Pillar 6 | 6,297 provisions pre-flagged (ban/conditional/storage/infrastructure) as mapping-stage priority input |

Honesty rules applied throughout: the <5% CER claim is made only on
committed, hand-checked reference pages (never on estimates, which are
disclosed per document as `engine_fixture_estimate`); no cross-provider
output parity is claimed — identical citations plus a disclosed tag delta is
the claim; every dollar figure comes from logged token counts.

## 4. How the project has grown

**Day 0 (12 July) — de-risk the hardest item first.** Before writing the
pipeline, a half-day pilot measured OCR accuracy on real Malaysian gazette
scans against hand-keyed gold pages. Result: 0.93%/2.72% CER — the 10-point
all-or-nothing rubric item was proven reachable before anything else was
built.

**Day 1 — vertical slice before breadth.** The full pipeline was built and
proven end-to-end on one law (Singapore PDPA 2012), including the
contract's worked example (s.26(1)) reproduced byte-for-byte, then hardened
by an adversarial multi-agent review that surfaced 15 real defects —
all fixed with regression tests before scaling.

**Day 2 (12–13 July, overnight) — corpus scale, and the gates earned their
keep.** Scaling from 1 law to 2,616 surfaced three bug classes that only
appear at scale, and the pipeline's own verification gates caught all three:

1. *Australian drafting style* (sections headed "5B Extra-territorial…"
   without a dot) had silently produced zero provisions for 592 AU acts —
   including the Privacy Act 1988. Fixed with a fallback that uses each
   act's own table of contents as a structural filter; the Privacy Act went
   from 0 to 901 provisions.
2. *Consolidated statutes* restart section numbering per schedule (and
   Malaysian gazettes reprint bilingually), colliding record ids. Fixed with
   deterministic id disambiguation; a new validate gate now proves
   uniqueness corpus-wide.
3. *Imperfect model output* (18 of 282k batch responses carried invalid
   enum values). Fixed with defensive normalization that caps confidence so
   the mapping stage widens rather than trusts.

Each fix cost only a cache-hit re-extraction plus a small delta batch —
the architecture (frozen texts, OCR cached once, tags graftable, batches
resumable) made repair cheap. That is the growth story: **from "can OCR
work at all?" to a self-auditing, restartable corpus engine in 48 hours.**

## 5. Rubric position after Stage 2

| Scored item | Pts | Status |
|---|---|---|
| Live portal crawling | 10 | ✅ banked (Stage 1) |
| OCR on scanned PDFs, <5% CER | 10 | ✅ banked, judge-recomputable |
| Modular backend (config-swap LLM/OCR) | 15 | ✅ banked, three models demonstrated |
| PDF **and** HTML parsing differentiator | — | ✅ both, at corpus scale |
| Cost-efficiency (measured) | part of 30 | ✅ our stages emit itemized reports |
| Citation fidelity + audit trail | ~25 | 🟡 all required fields produced & verified; Stage 3 writes the final rows |
| Correct indicator mapping | ~10 | ▶ Stage 3 |
| Discovery of NEW evidence | 20 | ▶ Stage 3 |

## 6. Next stage — Project 3 plan (to Round-1 deadline)

`rdtii-p3-map` consumes Hand-off #2 (contract-versioned, release notes in
`docs/HANDOFF2_NOTES_2026-07-13.md`) and owns the substantive scoring blocks:

1. **Prefilter** — keyword-signature search over all 305,980 provisions
   (tags act as non-exclusive boosts, never gates — a mis-tag cannot hide
   evidence).
2. **Indicator mapping** — per-indicator scoring trees from the validated
   instrument, decided by the pinned showcase LLM, with the local no-key
   fallback preserved.
3. **Blind verification** — a second, independent pass re-judges each
   mapped row without seeing the first answer.
4. **NEW/KNOWN diff** — candidate evidence compared against the published
   RDTII baseline; the 20-point discovery block.
5. **Final CSV/JSON** — 13 columns, every substantive row carrying the
   audit trio (verbatim snippet + article/paragraph locator + working URL),
   validated by schema before submission.

| Target date | Milestone |
|---|---|
| 15 Jul | P3 scaffold + prefilter over the full corpus |
| 17 Jul | Singapore vertical slice mapped, blind-verified, hand-checked |
| 18–19 Jul | Three-economy run + NEW/KNOWN diff + `run_slice` end-to-end (crawl→CSV, no manual steps) |
| 20 Jul | Round-1 submission: engine + CSV + pitch-deck diagram + walkthrough video (the scanned-PDF demo command is the script for it) |
| 3 Aug | Live demo — rehearsed on the $0 no-key path |

## 7. Reproducing our claims

```powershell
git clone <rdtii-p2-extract>           # private repo, access on request
# ...Quick Start in README.md (venv, Tesseract, local models; no API key needed)
p2-extract validate --provisions handoff2/provisions.jsonl   # all gates, offline
p2-extract demo                        # live OCR-CER measurement + full pipeline
p2-extract pilot --scan fixtures/ocr_reference/my-cca1997-001.pdf `
                 --gold fixtures/ocr_reference/my-cca1997-001/gold_page_0005.txt --page 5
```

Every number in this report traces to a committed artifact: measured CER
reports (`fixtures/ocr_reference/`, `handoff2/ocr/`), itemized cost evidence
(`handoff2/cost_report.json`), the validation gates (`p2-extract validate`),
and 82 automated tests.
