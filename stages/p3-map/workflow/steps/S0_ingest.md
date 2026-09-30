# S0 — Ingest · $0 · no LLM

**What we're doing:** loading the extracted corpus and proving every quote we will
ever emit is real — byte-for-byte present in the source text.

**In → Out**
- In: `handoff2/provisions.jsonl` (411,986 provisions, streamed line-by-line).
- Out: `data/index/prefilter_corpus.jsonl` — one compact record per provision with a
  metadata-prefixed text field, plus `out/ingest_report.json`.

**What it does**
- For each provision, checks `verbatim_snippet == source_text[start:end]` (exact bytes).
- Prefixes each provision's text with its own metadata so search sees it for free:
  `"Personal Data Protection Act 2012 | s.26(1) | Part 6 … :: <body>"`.
- For 7 thin-extraction docs, adds `#st.<n>` source-text chunks so nothing that
  exists only in raw text is invisible to retrieval.

**Gate:** 100% byte-exact grounding (411,986 / 411,986). This is what makes the
"verbatim quote" guarantee in every later stage enforceable.
