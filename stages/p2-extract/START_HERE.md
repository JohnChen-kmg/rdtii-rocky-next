# rdtii-p2-extract — START HERE (Project 2: OCR & Tag Extraction)

**What this is.** The kickoff kit for **Project 2** of RDTII Rocky — turns Project 1's raw files into clean, article-level text (OCR/parse) and extracts structured, grounded **provision records** = **Hand-off #2**. Owns the **OCR &lt;5% CER** rubric item (10 pts) and **verbatim grounding** ("no quote = no record"). **No crawling, no indicator mapping.**

## Read in this order
1. **`PLAN.md`** — the full Project 2 plan (parse/OCR cascade, article segmentation, tag extraction, tasks T0–T9).
2. **`INTERFACE_CONTRACT.md`** — build to **§2 (Hand-off #1 you consume)** and **§3 (Hand-off #2 you emit: `provisions.jsonl` + `source_text/` + `laws.jsonl`)**.
3. **`reference/Target_Output_Summary.md`** — the downstream schema and the provision fields your records ultimately feed.

## What's in this folder
- `PLAN.md`, `INTERFACE_CONTRACT.md`, `reference/Target_Output_Summary.md`
- **`sample_docs/Sample legislations/`** — the real host test corpus:
  - `General/` — **native + HTML tests**: MY *Personal Data Protection Act 2010*, SG *Telecommunications Act 1999*, AU compilation (*C2026C00098VOL01*).
  - `PDF of scanned documents/` — **scanned / OCR-robustness tests**: Pakistan PECA, India Public Procurement (image PDFs). *These are Pakistan/India — use them to tune OCR; the Deliverable-#4 demo scan is a **live Malaysia gazette** retrieved by Project 1.*
  - `Multilanguage in one legal file/`, `Domestic language only/`, `Consolidated laws in one volumn/` — edge-case document types to harden against.

## The two things that matter most
1. **OCR &lt;5% CER is binary-ish (10 pts).** Run a standalone CER spike **early** (PLAN.md **T2b**) on a scanned page with Tesseract + preprocessing — discover reachability before committing the demo doc, not at demo time.
2. **Grounding is structural.** Every `verbatim_snippet` must be a character-exact substring of the frozen `source_text/<doc_id>.txt`; if no faithful snippet, emit **no record**. This is what makes the audit trail impossible to fake.

## First moves (from PLAN.md §2.11)
`T0` scaffold + vendor contract + shared `config/` → `T1` Lane B (native PDF) on SG PDPA → freeze `source_text` → `T2` segmentation → `s.26(1)` → **`T2b` OCR CER spike** → `T5` grounding gate.

**You can start before Project 1 finishes:** build against `sample_docs/` + a self-made manifest fixture; the real `handoff1/` slots in unchanged because the schema is frozen.
