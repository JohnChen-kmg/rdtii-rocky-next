# notes/

Working notes for the mapping task, one file per thread of thought. What belongs here is the
reasoning that is too long for a DECISIONS.md entry and too rough for the repo. Write down why a
candidate provider looked promising. Write down what a disagreement between two engines turned on,
and how a gate threshold was arrived at. Write down what broke during a rehearsal and how long each
phase took. Name files by date and subject, such as `2026-09-15-engine-b-shortlist.md`. No source code, no
copies of the repo's engineering docs, and no git repository in this folder. When a note settles
something, promote the conclusion to DECISIONS.md and leave the note as the trail behind it.

## Index

| Note | What it is |
| :---- | :---- |
| `INSTRUMENT_IMPACT_2026-09-22.md` | What the instrument change of 13 September breaks in this stage, with file and line against repo commit `92a5e9d`. Two silent failures, the `P*.yaml` glob in triage and legacy IDs in the schema the model reads. Four requests to the instrument, one to scraping |
| `WORKFLOW_2026-09-24.md` | The eleven steps S0 to S10 in detail: input, output, which instrument file each step reads, and one real provision traced the whole way, plus the Chinese, Lao and Timorese cases. Read this before changing any step |
| `2026-09-27-sparse-leg-blind-to-cn-la.md` | Measured on the real six-economy index: the BM25 leg returns **zero rows for China and Lao PDR** across all nine indicators and all 450,000 top-K slots, and 4.4% for Timor-Leste against a 24.7% corpus share. Since `main.py` stubs the dense leg with an empty file, the interface's own run path would produce zero rows for two of the nine live-test economies. Code, so it must be fixed before the freeze. Also answers whether the fix needs another package: it does not, and a Chinese or Lao tokeniser would return no extra rows, because the query is English and those corpora are 99.3% non-Latin |
| `2026-09-27-laws-the-corpus-does-not-hold.md` | Measured on the six-economy index: 23 host gold rows cite 11 laws this corpus does not hold, seven of them Chinese departmental rules or GB/T standards — the exact tier the coverage register says the national database omits. Lao's cyber-crime law alone accounts for three rows, and Malaysia's two Codes of Practice are crawled but unparsed, so that pair is an extraction request. Includes the correction that took the figure from nineteen to eleven: an English name in a non-Latin jurisdiction is a translation, not identity |
| `2026-09-27-cap-function-and-query-review.md` | The selection function as it now stands, with every parameter and the gold row that earned each override; what it is measured to do (46,494 pairs, 61 of 63 gold, 40% fewer candidates than the fixed caps) broken down by economy and indicator class; the end-to-end funnel on the Round 1 arm; and the three refinements measurement rejected — a corpus-size term, a sparsity-aware floor, a different embedder — against the one it endorsed, asking the question in the corpus's own language |
| `2026-09-27-host-output-template.md` | What OUTPUT_TEMPLATE_FINAL_ROUND.xlsx actually requires, read from the file: three constraints checked by formula rather than by eye (the Pillar formula yields "?" for `P6-I1`, so legacy IDs would show zero coverage for every economy; the economy string must match the Coverage Matrix row label, which is "Lao PDR" and not the Instructions' "Lao People's Democratic Republic"; the sheet holds rows 9 to 109). Column N's exact requirement, the per-indicator weights, and the 29-item submission checklist mapped against where this stage stands |
| `2026-09-27-overnight-freeze-work.md` | Blocks B, D and E of the three-day plan, with the evidence: a Singapore re-emit that reproduces all 42 filed rows and all 811 NEW/KNOWN rows field for field, caps mode reproducing Round 1's 27 cells, and scores mode holding gold recall at 37/37 on a quarter fewer candidates. Four defects only a run could find, including a `PREFILTER_FLOOR` default that empties the gray band and a missing API key that used to hand mapping to a local model. Ends with the runbook for when the embedding run finishes |
| `2026-09-26-selection-cap-function.md` | Why the per-indicator caps are replaced by a score threshold with a floor and a ceiling, every variable defined, and the verification against Round 1: same gold gate 37/37, all 27 economy scores unchanged, 88% of filed rows retained, 45% of the candidate volume. Charts at <https://claude.ai/artifact/QQyDPSqmCfdXhwb1DMhB7b> |
| `2026-09-24-experiment-proposal.md` | Proposed phase-2 experiments: seven arms, the fixed sample, the metrics, candidate models for Engine B and the translation tools. Includes a measured blocker: the local client sends no `num_ctx`, so Ollama truncates to 2,048 tokens from the front of the prompt |

## Cross-stage issues that touch mapping

Recorded outside this workshop, in the planning folder, so every stage reads one copy.

| Issue | What it asks of mapping |
| :---- | :---- |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\ISSUES\2026-09-21_minimal-source-set.md` | **Match the Discovery Tag comparison on instrument name and section, never on URL.** Measured against the host's own 2025 citations, the main law database is cited 0 times out of 172 for Malaysia, 2 of 147 for the Russian Federation, 12 of 250 for Thailand and 14 of 254 for India. A comparison keyed on URLs scores the main database at zero in those four economies and measures the wrong thing. A second finding for scoring: an Indonesian row names a Constitutional Court decision as co-equal with the statute it displaces, so reading only the statute returns a confidently wrong answer rather than a missing one |
