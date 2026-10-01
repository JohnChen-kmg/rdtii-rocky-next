# Release notes — `final-submission`, 1 October 2026

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
- **A from-scratch interface** (standard-library Python, 93 tests): Overview with a worked example,
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
python -m unittest discover -s interface/tests -t interface   # 93 tests
python interface/app.py                                        # http://127.0.0.1:8765/
```
