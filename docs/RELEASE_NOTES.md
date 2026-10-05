# Release notes — `final-submission`, prepared 5 October 2026

**RDTII Rocky**, final round of the UN Global Hackathon on AI for Digital Trade Regulatory Analysis.
Team: Rocky has a home run. This release follows the one of 1 October, whose notes are kept below.

## What did not change

- **The filed evidence.** `submission/` is byte for byte what was filed on 1 October: 101 workbook rows of
  318 produced, six economies, four languages, from the run of 27 September, with its cost ledger
  ($275.24 on Engine A, $0 on Engine B).
- **The two declared engines.** Engine A is the hosted Claude stack (Sonnet 5, Haiku 4.5, Opus 4.8);
  Engine B is Qwen2.5-14B-Instruct, local, digest-pinned. The request Claude receives is unchanged.
- **The honesty rules.** No quote, no record; a translation never becomes evidence; the gold set scores and
  never steers; robots.txt is obeyed.

## What changed since 1 October

| Area | Change |
| :-- | :-- |
| Starting the tool | Double-click launchers for Windows, macOS and Linux open the pages in a window of their own; closing it stops the tool, and a run with it, after a warning. One instance per repository. A `.venv` is found by itself; otherwise Appendix → This machine names the Python of each stage |
| Overview | A workflow map of the three stages; a cost report in three blocks (money by model and step, time by stage, a calculator); estimated performance by model, from one experiment of 4 October, said to be small |
| Scraping | One run per economy; results filed by economy and source; Check asks the stage whether the link list fits and states the time; Refresh from the portal; Quick run (the first N documents); a crawl the portal cut short ends as failed, nothing lost |
| Hand-collected files | Any of the six economies, no source to pick: each file is judged by what it is (ready, or why not and what to do) and filed under `inbox/<economy>/Hand_collected/<date_time>/` |
| Extraction | Documents that gave no provision are listed "to check"; article headings in capitals or with a non-breaking space are found; an English "Article N" pattern for English editions; the language an adapter read from the portal travels with each file; the OCR choice shows its measured pace and memory |
| Mapping | Run is laid out as the steps in order, A to E: candidate selection with a number per indicator (the recommended one prefilled), quick screen, careful reading, re-check, tie-break, each model step with its own provider and model. Keys for hosted providers in one place, held in memory only |
| Engines offered | DeepSeek, Kimi and ChatGPT can be chosen per step through one OpenAI-compatible client. They are **not** declared engines and are marked "not measured" |
| Instrument | The 52 indicators outside pillars 6 and 7 now carry blocks of the same depth (scoring trees, coding rules, traps, count rules, absence scores). No person has reviewed them yet |
| Output of every stage | A table of runs: when each began, when it last ran, complete or not, with Open folder and Clear. In Mapping a click on a run examines it, and its Record names the model of each step |
| Appendix | Opens with "Adding a new economy": what each stage needs, the file that holds it, what is built |
| Tests | Interface 94 → 291; crawler 429; extraction 134 (six need a development tool not shipped); mapping 505. A workflow runs the interface's tests on Windows, macOS and Ubuntu |

## A fault found and repaired on 5 October

From 4 October a change of ours made every real crawl end with an error after it had stored its documents:
the crawler wrote each adapter's facts about a file into the manifest, and the crawler's own contract check
allows no other field there. The facts now go to a side file, `manifest_meta.jsonl`. Found by a small test
run from the page, repaired, and run again: three Timor-Leste documents crawled, checked and extracted.

## Tested on 5 October, from the page, small runs

Scraping (a Quick run of three documents, a dry run, files dropped by hand), Extraction (the demo corpus and
three more inputs), Mapping on local Qwen (Singapore, indicators 6.1 and 6.4: two rows in the host's
columns in three minutes, $0), Accept, Reject, Correct and Clear decision with the export after each, Stop,
Clear run, the self-test. No hosted model was called in this test. The record is in
`docs/CHANGELOG_FINALE.md`, under 2026-10-05.

## Honest limits added to the README's list

No full run has been made and scored on a model outside the two declared engines. Local Qwen agrees with
Claude less often on Lao (78%) than on the other languages. A rerun today will not reproduce the filed rows
byte for byte: the portals move, a model does not always answer twice alike, and the rulebooks of 52
indicators are deeper than on 27 September. No window has been opened by us on a Mac.

## Verify this release

```
git checkout final-submission
python -m unittest discover -s interface/tests -t interface   # 291 tests
python interface/app.py                                        # http://127.0.0.1:8765/
```

---

# Release notes — the release of 1 October 2026 (kept as written)

The judged release of **RDTII Rocky** for the final round of the UN Global Hackathon on AI for
Digital Trade Regulatory Analysis. Team: Rocky has a home run.

## What this release contains

- **Four pipeline stages** joined by versioned file contracts (0.3.0): polite collection, per-script
  extraction with byte-anchored grounding, indicator mapping with blind verification, and packaging.
- **A machine codebook of the RDTII 2.1 methodology**: 61 in-scope indicators as decimal-text IDs,
  one block each — legal question, scoring tree, coding rules, the host's trap wording — plus a
  1,054-row gold set used to score the pipeline, never to tune it.
- **Six economies run end to end**: Australia, Malaysia, Singapore, China, Lao PDR, Timor-Leste;
  three non-English (Chinese, Lao, Portuguese); Timor-Leste mapped against all 61 indicators, so all
  twelve pillars appear in the output.
- **Two declared engines** (`stages/p3-map/config/llm/engines.json`): the hosted Claude stack with
  pinned model IDs, and Qwen2.5-14B-Instruct (Apache-2.0) local via Ollama, digest-pinned, covering
  all four roles at $0. Both run the identical conversation; the switch is one control in the
  interface and is recorded in each run's manifest.
- **A from-scratch interface** (standard-library Python, 94 tests): Overview with a worked example,
  three stage tabs with Check-then-Start runs and plain-words progress, a hand-collected inbox,
  review with original-beside-English, append-only decisions, 14-column CSV/xlsx export, clearable
  caches, and an Appendix self-test.
- **The filed evidence**: 101 workbook rows (of 318 produced) across six economies in four
  languages, with the per-run cost ledger — the finale run (six economies on pillars 6 and 7,
  $206.00, plus Timor-Leste across the other 52 indicators, $69.04) cost **$275.24** on Engine A
  and **$0** on Engine B; extending all six economies to all 61 indicators projects to about $850
  from the measured Timor-Leste ratio — and the packaging report that verified IDs-as-text and
  untouched template formulas.
- **The working record** under `docs/`: per-stage results written the day each stage closed, the OCR
  and translation tool comparisons with the losing options named, the problems register, and one
  superseded analysis kept with its error explained.

## Changes since Round 1 (tag `final-submission` in the Round 1 repository)

- Indicators: 9 → 61, decimal-text IDs throughout.
- Economies: 3 English → 6, three non-English; language always from the crawler, never guessed.
- Selection: nine hand-set caps → a per-indicator threshold function derived from our own Round 1
  artifacts; the finale run paid for 0.10% of the possible candidate pairs.
- Extraction: contract 0.3.0; laws recorded per act; OCR measured per script; repaired citations
  carried visibly instead of silently.
- China: collected lawfully by hand where robots.txt forbids crawling, with per-file provenance and
  recorded gaps.
- Interface: rebuilt from scratch; the old dashboard is not in this repository.

## Honest limits, unchanged from the README

Lao OCR is ~94% character agreement and the under-5% CER is not claimed for Lao; China's
below-statute tier is partly manual by law; indicators whose answers live outside legal databases
carry a manual-check notice; the 30-minute deploy was rehearsed on one machine so far.

## Verify this release

```
git checkout final-submission
python -m unittest discover -s interface/tests -t interface   # 94 tests
python interface/app.py                                        # http://127.0.0.1:8765/
```
