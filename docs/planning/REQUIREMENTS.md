# Finale requirements — distilled

Sources: `../1_Rules/Final_Round/Finalist Orientation_Slide.pdf` (18 Aug 2026),
`README_template_FINAL_ROUND.md`, `submission_template_stage3_v2_CLEAN.docx`,
`Live_Test_Short_Note_TEMPLATE.docx`. Where they conflict, see `OPEN_QUESTIONS_FOR_HOST.md`.
The build plan that follows from this lives in `GAPS_AND_PLAN.md`.

## Dates

| Date | What |
| :---- | :---- |
| by 20 Sep 2026 | Submission portal link arrives from the secretariat |
| **30 Sep 2026** | Final submission and **code freeze**. Settings may change after this. Code may not. |
| 30 Sep – 14 Oct | Secretariat deploys from your guide on a clean machine. Advisory board review. |
| 14 Oct 2026 | Arrive Bangkok |
| **15 Oct 2026** | Grand Finale. Live stress test 10:00–11:30. Judges try the tool 13:00–13:30. Pitch and defence 14:00–16:00. |
| 16 Oct 2026 | Depart |

Venue: United Nations Building, Rajadamnern Nok Avenue, Bangkok 10200.

## Where the marks come from

| Weight | Component | When |
| ----: | :---- | :---- |
| 40 | The submission, deployed and tested by the secretariat | 30 Sep – 14 Oct |
| 50 | The judges, private trial then pitch and defence | 15 Oct afternoon |
| 10 | The live stress test | 15 Oct morning |
| 10 | Advisory board, extra: "which tool would you most want to use?" | 30 Sep – 14 Oct |

The judges carry half the total. The tool has to be persuasive in a private hands-on
trial, not only correct.

## The rubric

| ID | Criterion | Pts |
| :---- | :---- | ----: |
| C1a | Jurisdiction coverage. Three or more diverse economies, minimal reconfiguration | 15 |
| C1b | Regulatory domain coverage. Pillars 6 and 7 mandatory, plus further RDTII domains | 15 |
| C1c | Linguistic versatility. Same provision, same indicator, whatever the language | 10 |
| C2a | Framework alignment at scale. Mapping stays consistent across every economy | 10 |
| C2b | Citation fidelity at scale. Article-level, verbatim, no hallucinations | 10 |
| C3a | Audit mode, human in the loop. A policy officer can check the source unaided | 10 |
| C3b | UI/UX and export. Operable without training, export to the RDTII schema | 5 |
| C4a | Technical handover. Deployed from your docs in under 30 minutes. Apache 2.0 | 8 |
| C4b | No vendor lock-in. One config change swaps in an open-weight model | 7 |
| C5 | Live stress test. Discovery run 6, engine swap 4. Marked on 15 October | 10 |

## Four things to submit on 30 September

1. **Word document** — `submission_template_stage3_v2_CLEAN.docx`. Deployment guide,
   architecture, open-source compliance, live-test readiness table, AI engine declaration.
2. **Excel workbook** — `OUTPUT_TEMPLATE_FINAL_ROUND.xlsx`. Fourteen columns: the thirteen
   from Round 1 plus `language_of_source`.
3. **Working interface**, reached by deploying your repo. Evidenced by a walkthrough recording.
4. **Public repository at a release tag**, with full README, Apache 2.0 LICENSE and deployment docs.

## What changed from Round 1

The five differences the host flags on slide 7, plus two found by reading the templates.

- **At least six economies processed autonomously**, at least three of them non-English.
  Round 1 was three English-language economies.
- **All twelve pillars in scope.** Pillars 6 and 7 stay mandatory. The sealed live test may
  draw from any pillar. Round 1 covered only P6-I1 to I4 and P7-I1 to I5.
- **A user-facing interface is required**, marked on C3a and C3b for fifteen points by
  someone who did not build it.
- **Two declared engines, at least one open weights**, switched from inside the interface
  with no file edited and no command typed. Declared 30 September, frozen thereafter.
  Worth 7 points on C4b and 4 more on C5b.
- **Thirty minutes to deploy on a clean machine** from your documentation alone.
- **The repository must be public.** Round 1 was private with collaborator access. Nothing
  with credentials or licensed source text can ship.
- **Indicator IDs change format.** Round 1 filed `P6-I1`. The finale requires decimal text:
  `6.1`, `7.3`, `12.9`. Entered as a number, `12.10` collapses to `12.1` and `4.01` to `4.1`,
  which are different indicators. Write them as text.

## Hard constraints, stated twice or more by the host

- **The second pass must fetch nothing.** Its document list must be empty. The live-test
  short note has a field for documents fetched during the second pass, pre-filled
  "must be 0".
- **Polite crawling on by default.** One request per second per host, one parallel request
  per host, robots.txt respected. Five tools will read the same government sites in the
  same hour on 15 October.
- **Cost recorded per run and per engine**, produced by logging without manual arithmetic.
- **Measured costs from real runs, not estimates.** The secretariat verifies cost claims
  against the code.
- **A run starts from a button**, not a command line.

## What the live test demands, in order

1. Read the task. Set economy and indicators in the interface. Press start.
2. Engine A runs: finds sources, downloads, reads and translates, extracts, maps.
3. Review in your own interface. Accept, reject, correct. Export the evidence file.
4. Switch to Engine B. Re-run over documents already downloaded. Export the comparison.
5. Write the short note. Submit four files: evidence, comparison, run record, short note.

The comparison must say which engine found each provision, how the indicator, article
citation or quoted words differed for shared provisions, and elapsed time and cost per
engine. Section 5 of the Word template asks whether your tool produces that comparison
**natively**, so building it as a feature rather than assembling it by hand is worth points.

## Read line by line from the primary host documents, 2026-09-12

The sections above were distilled from summaries. This section comes from reading every
sheet, table and checkbox in the four final-round templates. Where it adds to or sharpens
the sections above, this section is the more precise one.

### The live test is narrow in scope and wide in reach

- **One economy, one pillar, two indicators.** Announced at the start of the hour. Source:
  the output workbook's Instructions sheet.
- **Any of nine economies:** Thailand, Viet Nam, Indonesia, China, India, Kazakhstan,
  Lao PDR, Mongolia, Russian Federation. "It may be a pillar you were never asked to work."
- **Engine A must actually download during the hour.** The Run Record sheet says that if no
  documents were fetched during the hour, C5a scores zero regardless of the evidence file.
  A pre-built corpus does not count.
- **Caches must be clearable on screen** before the clock starts. Submission checklist item 26.
- **The Run Record lists every document downloaded:** source URL, which pass, time, size in
  KB and file type. Engine B's count must be zero, and a steward checks it.
- **The comparison file uses exact strings.** Its formulas count `Engine A only`,
  `Engine B only` and `Both`. Any other wording counts as zero.
- **The comparison file also carries a paragraph on which engine's output you would
  submit.** The short note says that paragraph belongs in the comparison, not the note.
- **The short note asks** for provisions exported per engine, how many you believe are absent
  from the 2025 baseline, what you would fully trust, what broke, which rows or indicator a
  ministry should check first, and anything typed by hand. Stewards initial it.

### The Word document, field by field

| Section | What it actually asks for |
| :---- | :---- |
| Team information | Team ID assigned by ESCAP, and a GitHub **release** URL in the form `/releases/tag/v1.0.0` |
| 1 Deployment guide | Reviewer has Docker and Python 3.10 or later. Clone, environment, configuration including how each engine is selected, run, expected output, a verification step |
| 2 Architecture | Changes since Stage 2, component boundaries, the in-interface engine swap, data flow from Zone 1 crawl through Zone 2 extraction to the review interface, how the second pass avoids re-fetching, cost-efficiency measures |
| 3 Open-source compliance | Every dependency with its licence. Checkbox: the core pipeline runs end to end with **no proprietary API or hosted service**, on the open-weights engine |
| 4 Live-test readiness | The nine economies, each with pillars, languages handled, run end to end yes or no. "An honest gap here costs you nothing" |
| 5 Engine declaration | Per engine: provider and model, exact version or checkpoint, local or hosted and which host, **the screen and control name of the switch**, **approximate cost of one run of two indicators in US dollars**, **known weaknesses on legal text**. "An incomplete Section 5 cannot be corrected after the deadline" |
| 6 Walkthrough | Five minutes. Five beats: start a run with plain-words progress; one row beside its source text; follow that row to the official source at the cited article; **reject a row, export, and show the correction took effect**; switch the engine |

### The workbook, beyond the fourteen columns

- **Economy uses the official UN name**, for example "Lao People's Democratic Republic".
- **A real act cited to the wrong section scores zero.**
- **Flagging low confidence is treated as a strength.**
- **NEW means not in the 2025 baseline you hold.** KNOWN means it was in the sample kit.
- **The Output Data sheet holds rows 9 to 109 only.** The Pillar formula and every Coverage
  Matrix count stop at row 109, so the template has room for 101 provisions.
- **Column E is pre-formatted as text.** Writing a number into it still breaks the ID.
- **Remove example rows 7 and 8 before submitting.**
- **The submission checklist has 29 items, not 26.** New to our planning: no hard-coded
  paths (8), Zone 1 and Zone 2 as separate documented modules (10), the core pipeline runs on
  the open-weights engine alone (12), Engine A expected to be commercial hosted (20), caches
  clearable on screen (26), and the interface left available for the marking period (29).

### The README template, section by section

Every section is mandatory, not only Quick Start. Beyond what we already planned, it asks for:

- Quick Start from a root `requirements.txt` and a root `.env.example`, then **one command
  that starts the interface**, after which a reviewer never needs the command line again.
- A table naming the screen and control for six actions: start a run, audit view, follow to
  source, accept or reject or correct, switch engine, export.
- **File and line references** for the three politeness settings.
- **Swapping the OCR engine**, noting which options are proprietary. The no-proprietary rule
  covers OCR and translation, not only the language model.
- **Measured cost per document per engine**, broken into OCR, embedding, mapping A, mapping B
  and crawling, with a named benchmark document and wall-clock seconds per document.
- **Confidence calibration:** below what score a human should check.
- **Reproducing your submitted evidence:** one command that regenerates the workbook rows.
- Team roles: Technical Lead and Substantive Lead.
- The template file is saved as UTF-16. Convert it to UTF-8 before editing, or GitHub renders
  it as spaced-out characters.

### Scoring detail

- The Instructions sheet states the desk review as **90 points across C1a to C4b**, and says
  the judges mark separately and **do not see the desk-review scores**. The slides weight the
  same component at 40. Read the 90 as raw rubric points scaled to the 40 weight.
- On C1a the Instructions sheet says **"Depth across three beats a thin pass over ten"**, and
  the checklist asks only for three or more economies and at least one non-English source.
  Slide 7 says six economies and three non-English. See `OPEN_QUESTIONS_FOR_HOST.md` question 6.

### Defects inside the host templates that change engineering

- **The Coverage Matrix has no row for the Russian Federation.** Russia is one of the nine
  live-test economies and one of the seven baseline sheets we hold. Its provisions would be
  counted nowhere.
- **The Coverage Matrix labels Lao as "Lao PDR"** while the field rule demands the official
  UN name "Lao People's Democratic Republic". The counting formula matches exact text, so
  following the field rule makes Lao count as zero.

Both are raised as question 7. Until answered, write the label the matrix counts and record
the official name in Notes.

### Precedent for the 15 October pitch

The only written pitch rules we hold are for the online pitch on 3 August, filed at
`../1_Rules/Round_1/Pitching Rules.pdf`. Eight minutes of presentation, then seven minutes of
judge-led questions in which judges may ask you to run the tool live on a case they choose.
No time to rerun. "Errors in your own engine are part of the assessment." Nothing yet says the
finale pitch follows the same format, but it is the best evidence available.

---

This file is the static statement of what the host requires. It should change only if
the host changes the rules. What we intend to do about it lives in `GAPS_AND_PLAN.md`.
