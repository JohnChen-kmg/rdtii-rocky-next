# How this repository was assembled

**Status on 5 October 2026**, added above the record of 29 September, which is kept as written below.

- The tree was pushed as `JohnChen-kmg/rdtii-rocky-finale-9.30` and judged at its tag `final-submission`
  (the release of 1 October). Since 4 October the post-finale work, branch `feature/desktop-workspace-triage`,
  is pushed to a second repository, `JohnChen-kmg/rdtii-rocky-next`, branch `main`, which the resubmission
  documents of 5 October name. On 5 October both repositories are still private.
- `interface/`: built from scratch on 29 and 30 September and reworked from 3 to 5 October; 291 tests. There
  is one interface in the tree; the Round 1 dashboard never travelled.
- Tests on 5 October: crawler 429 pass and 3 skipped; extraction 128 pass, 2 skipped, 6 fail for want of a
  workshop tool this repository does not hold; mapping 505 pass and 8 skipped.
- `main.py`: still not reviewed. Tried on 5 October, its default mode writes the 14 column names and no
  rows, because it keeps rows whose Indicator ID begins `P6-` and the filed rows carry `6.1`. The interface
  does not use it (`docs/DATA.md`).
- Of the six items under "Before the release tag": the tree is clean of host material (1); one interface is
  named (2); the deployment has been rehearsed on the development machine only (3); `main.py` was not
  checked beyond p1, and see above (4); the three run notes keep their absolute paths, as decided (5); the
  question in (6) was answered on 4 October: a resubmission is possible, and one is prepared.
- The language packs (last section) are 78 MB of tracked files: 58 MB `best`, 14 MB `fast`, and no Malay
  pack; the README says so since 5 October.

---

Created 2026-09-29 as `rdtii-finale-submission`, renamed the same day to
**`rdtii_rocky_finale_9.30`**, after the team name and the submission date. The remote name is chosen at
the first push and does not have to match the folder. Nothing inside this tree depends on either.

Created 2026-09-29. **This is the submission repository.** The release tag cut here is what a marker
deploys and what runs on 15 October, so what is in this tree is the submission and what is outside it
is not.

It is a fresh repository rather than a branch of the development one, for one reason:
`rdtii-rocky-finale` carries 77 files of ESCAP's own material in its git history, including the Round 1
and Round 2 databases, the methodology workbook, the output templates and the host's take-home
assignments. The submission requires a public repository, and deleting those files after publishing
does not remove them from history. This tree starts clean.

**The development history stays in `rdtii-rocky-finale` and in the five workshop folders.** Do not
delete them. They are the record of how the work was done and can be shown on request.

## What is here, and where it came from

| Path | Source | State |
| :---- | :---- | :---- |
| `LICENSE` | `rdtii-rocky-finale` | Apache 2.0, as required |
| `main.py` | `rdtii-rocky-finale` | Copied. **Needs review**: it orchestrates four stages and its paths predate this layout |
| `requirements-demo.txt` | `rdtii-rocky-finale` | Copied. Must stay free of the documentation toolchain |
| `stages/p0-instrument/output/` | `rdtii-finale-0-instrument\instrument\output` | The 61-block decimal codebook, policies, signatures and the 1,054-row gold set. Complete |
| `stages/p0-instrument/scripts/` | `rdtii-finale-0-instrument\code\scripts` | Build and validate scripts. Complete |
| `stages/p2-extract/` | `rdtii-finale-2-extraction\code` | Source, tests, config, contracts, fixtures. Verified identical to branch `p2-extract-contract-0.3.0` apart from line endings |
| `interface/` | nothing yet | Built from scratch tonight. Plan and decisions in `rdtii-finale-4-dashboard\` |
| `stages/p1-scrape/` | a merge: engine from `rdtii-rocky-finale`, six adapters from `rdtii-finale-1-scraping\countries\`, four hand-backs applied here | **Complete, 29 September.** 1,063 files. Engine (65 files) without `handoff1_v2/` or `reference/`; six economy packages under `src/p1_scrape/adapters/`; the live registries, which replace the engine's stale Round 1 copies; 21 MB of link lists; 68 MB of corpus evidence under `handoff1/`. **427 tests pass, 3 skip.** All four hand-backs applied, so the Lao xfail now passes and became a real test |
| `stages/p3-map/` | `rdtii-rocky-finale` branch `w2-mapping-finale` at `b4d3cde` | **Complete.** 203 files: `src` (40), `config` (18, including `llm/engines.json`), `tests` (25), `contracts/instrument` (70), `00_contracts/schemas`, `docs`, `workflow/steps` (S0-S10 + data dictionary), both requirements files, `.env.example`. **422 tests pass from this repository.** Taken with `git archive`, so only tracked files travelled |
| `submission/` | `rdtii-finale-p3-runs\run_2026-09-27` via `stages/p3-map/src/p3map/output/package.py` | **Complete.** 319 rows across six economies, one records CSV + JSON each, six audit pages, 31 reports including the cost ledger and a URL liveness pass. The curated 101 and the review workbooks are **not** here — see below |

## What is still to come, and from exactly where

**1. `stages/p1-scrape/` — DONE, 29 September.** The merge of three things, as planned.

The engine came from `rdtii-rocky-finale` minus two folders: `handoff1_v2/`, which was Round 1's output,
and `reference/`, whose two CSVs `START_HERE.md` itself calls "the host's law→URL map" — ESCAP's material,
and no code reads it. The six economy adapters were installed from
`rdtii-finale-1-scraping\countries\<cc>-<name>\` by each one's own documented install step, so each is a
package under `src/p1_scrape/adapters/` with its update check, its watch list and its `WORKFLOW.md`.
China has no adapter by decision — its national database forbids automated collection — so its seven
tools travel as `adapters/cn_npc/`.

**All four hand-backs are applied here**, and each is verified rather than asserted:

| Hand-back | Where | Proof |
| :---- | :---- | :---- |
| `cryptography==44.0.0` | `requirements.txt` | Laws of Malaysia encrypts its listings; the MY catalogue cannot read them without it |
| delete `tests/test_my_selection.py` | gone | it imported the flat `my_gazette.py` the package replaced, and a collection error aborted the whole run — the workshop's install ran **zero** Malaysian tests |
| the economy code and the adapter registry | `economies.py`, `adapters/registry.py` | `parse_economies("all")` returns all five and every adapter resolves to its class |
| the manifest schema | `contracts/schemas/manifest.schema.json` | `economy` widened to `^[A-Z]{2}$`, `doc_id` to `^[a-z]{2}-…`. Timor-Leste's 3,842 and Lao PDR's 3,524 validation errors are **gone**; both now report only the absent documents, exactly as the three Round 1 economies do |
| the slug | `utils.py`, `dedup.py`, `orchestrator.py` | the storage folder and doc_id key now come from the adapter's `law_slug`. The Lao xfail **passes**, so its marker was removed and the test now guards the fix rather than excusing its absence |

Two smaller corrections found while verifying. `tests/test_classifier.py` defaulted
`RDTII_SAMPLE_LEGISLATION` to an absolute path into ESCAP's baselines on the author's machine; there is
now no default, so the two tests skip on a clean clone. And China's tools resolved their collection and
watch list by the workshop's folder layout; they now honour `HANDOFF1_DIR` first and fall back to either
layout, so the suite runs from the workshop and from here.

`rdtii-finale-1-scraping\outputs\` is 19 GB of retrieved documents and does **not** travel. What does is
**68 MB of `handoff1/`**: every economy's corpus manifest, law table, link records, audit and note, plus
each run's note — the record of every document without the documents. `handoff1/README.md` explains it,
including that `scrape.py --validate` reports `local_path does not resolve on disk` until a crawl
populates `raw/`, and that this is the documents being absent rather than a contract breach.

**2. `stages/p3-map/` — DONE, 29 September.** Taken from `w2-mapping-finale` with `git archive`, so
only tracked files travelled and no `__pycache__`, `.venv` or `.env` could come with them. 422 tests
pass in this repository, `main.py` still resolves the stage at `STAGES / "p3-map"`, and no absolute
path survives in `src`, `config` or `tests`.

Three cautions in the earlier version of this note were true when it was written and are no longer:

- `excel_export.py` was uncommitted. It has been committed since, in three separate commits.
- `finale` was 47 commits stale. It was fast-forwarded on 29 September and now points at the same
  commit as `w2-mapping-finale`. **Both are still the wrong place to take it from for a different
  reason**: that repository tracks 22 files of ESCAP's own material right now and 23 appear in its
  history, so nothing cut from it can be made public. This tree remains the only publishable one.
- 318 rows. The retry work on 29 September recovered 187 of 196 provisions that had produced no
  verdict, which added rows; the figure is 319.

**3. `submission/` — DONE, 29 September.** 319 rows, six economies. The curation to 101 is written as
code (`stages/p3-map/src/p3map/output/template.py`) rather than described: breadth first, one row per
(economy × indicator) cell, then depth, with a doubtful citation losing to a clean one. It evidences
51 cells, so breadth costs half the sheet. The rule still has to be restated in the Word document.

## What deliberately did not travel

| Not copied | Why |
| :---- | :---- |
| ESCAP's workbooks, output templates and assignments | The repository is public at the release tag. A reviewer places their own copy at the path the README documents |
| `rdtii-finale-0-instrument\sources\` | 18 MB of host framework PDFs and training decks |
| `rdtii-finale-0-instrument\drafting\` | 5 MB of working history, superseded by `output/` |
| `rdtii-finale-2-extraction\out\` | 6.1 GB of extraction output. Regenerated by running the stage |
| `rdtii-finale-2-extraction\corpus\`, `experiments\` | Working inputs and the tool comparisons. The comparisons are evidence and belong in the Word document, not the code tree |
| `rdtii-finale-1-scraping\outputs\` — the documents | 19 GB of retrieved law. Every `raw/` folder. The manifests, law tables, link records, audits and notes that describe them **do** ship, as `stages/p1-scrape/handoff1/` |
| `rdtii-finale-1-scraping\outputs\` — the intermediate runs' bulk data | 75 MB of manifests and link lists from the individual crawls and update checks, every document in them already described by the corpus that superseded it. Each run's `RUN_NOTE.md`, `audit.md` and `changes.md` **do** ship, in `handoff1/run_notes/` |
| `stages/p1-scrape/handoff1_v2/` | Round 1's hand-off: output, 8.5 MB, and the folder `CONVENTIONS.md` rule 3 says is never read as an input |
| `stages/p1-scrape/reference/` — 2 CSVs | **Host material.** `START_HERE.md` calls `Sample_government_portals_Pillar6_7.csv` "the host's law→URL map", and `Legal_Inventory_SG_MY_AU.csv` carries the baseline database's own columns. No code reads either; a reviewer with their own copy needs no path from us |
| `rdtii-finale-1-scraping\countries\_finale-survey\`, `_template\` | The survey of candidate economies and the new-country template: development history, not the product |
| Every `logs/`, `out/`, `__pycache__`, `.venv` | Excluded by `.gitignore` at every depth |
| `stages/p3-map/reference/` — 45 files | **37 are host material**: ESCAP's Round 1 and Round 2 databases, the output template, the internal guide, the answer key and every take-home assignment. It also held two personal documents, a CV and a technical memo. This is the single directory that would have made the repository unpublishable |
| `stages/p3-map/logs/`, `.claude/` | Round 1 run logs, and agent tooling that is not part of the product |
| The filled host template, `OUTPUT_DATA_FILLED.xlsx` | It is the deliverable, and it embeds ESCAP's own Indicator Reference, Instructions, Coverage Matrix and Submission Checklist sheets. It goes to the host directly rather than into a public tree. Held in `rdtii-rocky-finale\submission\`, regenerable by `output/template.py` |
| `RDTII_P3_results_<E>.xlsx`, six review workbooks | Our own data, not the host's — but they are `.xlsx` and would make the `git ls-files` check non-empty, and `output/excel_export.py` rebuilds them from the run. Same argument as the index and the run directory |

## Before the release tag

1. **Make the repository public** and confirm no host material is tracked. `git ls-files` is the check,
   and it must stay clean after the p1 and p3 copies, which are the two most likely to reintroduce it.
   **After the p1 copy it is clean, with a caveat about the check itself:**
   `git ls-files | grep -iE "…|Baseline|…"` matches five Python modules named `baseline.py` — the update
   checks' own baseline, meaning the previous run — plus p0's
   `build_indicators_from_methodology.py` and p3's `discovery/baseline.py`. All seven are false
   positives. The checks that hold without them: **zero** `.xlsx`, `.xls`, `.docx`, `.doc` or `.pptx`
   files tracked anywhere, and **no** file named after a host artefact (`Round1_Baseline`,
   `Round2_Methodology`, `OUTPUT_TEMPLATE`, `ESCAP-RDTII`, `practice_dataset`, an assignment).
2. **Name one interface.** If any older dashboard ends up in the tree, the README and the Word document
   must say which one a marker deploys, or the interface marks land on whichever a reviewer opens first.
3. **Rehearse the deployment** from this tree on a clean machine, against the clock. The 30-minute
   deploy is worth 8 points and it is measured, not asserted.
4. **Check `main.py` still orchestrates** the four stages at these paths. For p1 it does: `STAGES /
   "p1-scrape"` resolves, `scrape.py` answers `--help`, and `src/p1_scrape` imports.
5. **One decision left in p1, for the developer.** Three shipped run notes still carry the development
   machine's absolute path, and with it a Windows username, in prose:
   `handoff1/run_notes/{AU/AU_ws_2026-09-15,MY/MY_ws_2026-09-14,SG/SG_ws_2026-09-15}/RUN_NOTE.md`,
   six occurrences. They are the provenance record of a particular run on a particular machine, and
   `CONVENTIONS.md` rule 7 keeps generated files unedited, so they were left as written. The four
   `WORKFLOW.md` files and one `README.md` that carried the same path **were** corrected, because those
   are instructions a reviewer follows and the path was no longer true. Nothing in code carries an
   absolute path; the one remaining string is a deliberate contract-violation fixture in
   `tests/test_manifest.py`, now `C:\somewhere\…` rather than a real profile.
6. **One open question worth asking tonight**: may the interface be updated between 30 September and
   15 October? The checklist implies no, and nobody has asked. A yes changes what has to be finished
   tomorrow.

## A note on the OCR language packs

`stages/p2-extract/fixtures/` is 82 MB, almost all of it Tesseract language packs, which ship in the
repository by decision D7 so that a clean deploy needs no download. 58 MB of that is the `best` packs
and 15 MB the `fast` packs. The measured choice for Lao was **`fast`**, on the evidence that it matches
`best` to within half a point at half the time and half the size. If repository weight matters, the
`best` packs are the first thing to drop, and the decision should be recorded rather than silent.
