# Diagnostic probes, 2026-09-27

Read-only scripts that produced the measurements in
`notes/2026-09-27-cap-function-and-query-review.md`. None writes to a run directory or to the
frozen Round 1 arm. Run from the stage root with the run's environment set:

    cd C:\Users\woshi\Desktop\rdtii-rocky-finale\stages\p3-map
    INSTRUMENT_DIR=...\rdtii-finale-0-instrument\instrument\output python -X utf8 <script>

| Script | What it answers | Rerun it when |
| :---- | :---- | :---- |
| `gold_funnel.py` | Where gold rows are lost, stage by stage, by economy and by indicator class | **After block F.** It currently reads the Round 1 arm; point it at the new run to get the same table for China, Lao PDR and Timor-Leste. That table is the gate on the prompt-seam decision |
| `zh_query_probe.py` | Does a same-language query beat an English one? Holds the three **Chinese query documents** written by hand — the starting point if run-time translation goes ahead | Before writing translated queries |
| `query_lang_probe2.py` | Would the original caps suffice with a same-language query, and how well does the English query separate each economy's corpus | After any query change |
| `quantile_probe.py` | Where theta lands inside each economy's own distribution | After any theta or offset change |
| `recalibrate_offsets.py` | The offset that equalises the percentile, per language, and what it costs in volume and gold | Before adopting run-time delta |
| `gold_after_triage.py` | Gold survival through the stages that have run: in-corpus, selected, kept by triage | After each stage. **Needs `INSTRUMENT_DIR` pointed at the workshop** or it silently finds no China or Lao gold |
| `verify_s4.py` | The gate before `chain.py`: fire rate against Round 1's band, ungrounded fires, legacy ids, duplicate verdicts, which codebook produced the verdicts, and whether every triage keep reached the mapper | Immediately after S4, every time. Exit 0 = safe to chain |
| `handoff_probe.py` | What the instrument hand-off changes for the stage: automated set, exemplar economies, query length | Before any later hand-off |
| `handoff_queries.py` | Are the nine query documents byte-identical across the hand-off (they are), and what is in the CN exemplar | Before any later hand-off |
| `handoff_substantive.py` | Of the codebook edits, which could flip a verdict — normalises away the ID form and added citations, prints what survives | Before any later hand-off, and to scope a re-judge |

The three `handoff_*.py` probes produced `notes/2026-09-27-instrument-handoff-measured.md`. They
compare the vendored instrument against the workshop copy without copying anything, so they answer
"what will the hand-off do" before it is done. `handoff_substantive.py` is the one to rerun if the
codebook changes again: it is what turned "all nine blocks differ" into "18 substantive changes,
none of them a reversal".

`zh_query_probe.py` is the one with content rather than only logic: its `ZH` dictionary is three
indicator query documents in Chinese, written from the indicator definitions using the terms
Chinese instruments actually use. They want a native read before they ship.

`verify_s4.py` exists because `chain.py` has no error handling: one bad S4 propagates through five
further stages in silence. Its thresholds are Round 1's measured numbers, printed with their basis,
so a flag can be judged rather than merely noticed. `gold_after_triage.py` has one trap worth
repeating: the vendored instrument carries 51 gold rows and none for China or Lao, so without
`INSTRUMENT_DIR` it reports a clean funnel over the wrong population.
