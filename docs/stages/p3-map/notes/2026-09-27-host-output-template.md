# What the host's final-round template actually requires

Read 2026-09-27 from `rdtii-finale-0-instrument\instrument\reference\OUTPUT_TEMPLATE_FINAL_ROUND.xlsx`
— seven sheets: Output Data, Indicator Reference, Coverage Matrix, Engine Comparison, Run Record,
Submission Checklist, Instructions. Everything below is quoted or derived from that file, not from
our own plan. Where our plan and the template disagree, the template is the authority; where two
sheets of the template disagree with each other, the one that is **checked by formula** wins,
because that is the one that produces the evidence a marker reads.

## Three constraints that are checked by machine

### 1. The indicator ID form decides whether the Coverage Matrix counts anything

Column O, "Pillar (auto — do not edit)", is the host's own formula:

```
=IF($E9="","",IFERROR(INT($E9),IFERROR(VALUE(LEFT($E9,FIND(".",$E9)-1)),"?")))
```

It reads the Indicator ID in column E, tries `INT()`, and otherwise takes the text left of the
first ".". Given `P6-I1` both attempts fail and the cell is `"?"`. The Coverage Matrix then counts

```
=COUNTIFS('Output Data'!$O$9:$O$109, 1, 'Output Data'!$A$9:$A$109, $A4)
```

— rows whose pillar is the **number** 1, 2, … So filing Round 1's ID form would show **zero
provisions for every economy in every pillar**, on the sheet C1a is read from ("three or more
diverse economies processed autonomously") and on checklist item 15.

The Instructions sheet says it in words too: "Write the RDTII 2.1 code exactly: 6.1, 6.4, 7.3,
12.3, 12.9. Not 'P6-I1', not 'Pillar 6 Indicator 1'." And: "Column E is formatted as text. This
matters: entered as a number, 12.10 collapses to 12.1 and 4.01 to 4.1, and the two are different
indicators" — which is decision F1, in the host's own words.

One stale spot to ignore: column E's own help text still reads `e.g. "P6-I1" , "P6_I2"`. The
example rows in the same sheet use `6.4` and `7.4`, the Indicator Reference sheet lists `6.1`…`7.5`,
and the formula only works decimally. The help text is Round 1 residue.

### 2. The economy string must match the Coverage Matrix row label

The matrix counts with `COUNTIFS(… $A$9:$A$109, $A4)` — an exact string match against its own row
labels, which are the 34 ESCAP economies as the host writes them:

> Australia, Bangladesh, Bhutan, Brunei Darussalam, Cambodia, China, Fiji, India, Indonesia,
> Japan, Kazakhstan, Kyrgyzstan, **Lao PDR**, Malaysia, Maldives, Mongolia, Myanmar, Nepal,
> New Zealand, Pakistan, Papua New Guinea, Philippines, Republic of Korea, Samoa, Singapore,
> Sri Lanka, Tajikistan, Thailand, **Timor-Leste**, Tonga, Turkmenistan, Uzbekistan, Vanuatu,
> Viet Nam

The Instructions sheet says instead: "Official UN country name, e.g. Lao People's Democratic
Republic, Viet Nam." Those two disagree for Lao PDR, and only one of them is counted. **We file
the matrix strings**, so our six are Australia, China, Lao PDR, Malaysia, Singapore, Timor-Leste.
A marker who prefers the longer form loses nothing by reading "Lao PDR" — it is the host's own
label — whereas a zero in the matrix is a mechanical failure of item 15.

### 3. The sheet holds 101 rows, and rows 7–8 must go

Both formulas address `$9:$109`, which is the 101 rows the plan assumes. The Instructions add:
"Remove rows 7 and 8 before submitting. They are illustration only."

## Column N, the one new column

> **Language of Source** (REQUIRED) — "Original language of the legal document — e.g. Thai,
> Vietnamese, Bahasa Indonesia, Russian, English. Drives criterion C1c."
> Instructions: "The original language of the document, not the language you translated into."

It takes a **name**, not a code, which settles the shape of decision M10's translation note: the
column records the source language, and any translation we file lives in the Notes or the
rationale, never here. Implemented today; measured against the September hand-off, it will carry

| Economy | Column N |
| :---- | :---- |
| AU, SG | English |
| MY | English (1,380 laws) and Bahasa Malaysia (9) |
| LA | Lao |
| TL | Portuguese |
| CN | Chinese, from the provision records — the law rows are null (see R5) |

Checklist item 17 asks for at least one non-English source recorded in this column. We will have
three languages beyond English.

## What the other sheets ask for, which we do not yet produce

**Engine Comparison** (completed during the live hour, not before): provider and model name, start
and end time, elapsed minutes, **documents fetched during this pass**, cost in US dollars, per
engine — and a line that reads "Engine B's 'documents fetched' …", i.e. the second pass must show
zero. The run manifest added today records provider, model per role, start time, cost and
`provisions_mapped` against `resumed_past`. It does **not** record documents fetched, because the
mapping stage fetches nothing: that number belongs to the scraping stage, and the comparison sheet
spans the whole pipeline. Whoever fills this sheet needs both stages' manifests.

**Run Record**: per engine one row (provider/model, start, end, elapsed, cost), then *every
document downloaded during the hour* — number, source URL, which pass fetched it, time, size in
KB, file type. Again a scraping-stage table; mapping contributes nothing to it.

**Indicator weights**, from the Indicator Reference sheet, which we had not recorded anywhere:

| | | | |
| :---- | ---: | :---- | ---: |
| 6.1 Ban and local processing | 38% | 7.1 Lack of comprehensive data-protection framework | 31% |
| 6.2 Local storage | 12% | 7.2 Lack of dedicated cybersecurity framework | 31% |
| 6.3 Infrastructure requirements | 31% | 7.3 Minimum retention period | 16% |
| 6.4 Conditional flow regimes | 12% | 7.4 DPIA or DPO requirements | 6% |
| 6.5 No binding agreement on transfer | 8% | 7.5 Government access to personal data | 16% |

This is a better rule for block I than "strongest row per indicator": with 101 slots, a row for
6.1 (38% of pillar 6) is worth more than a row for 6.4 (12%). It also says something about the
gray band — 6.1 and 6.3 together are 69% of pillar 6, and 6.3 is the indicator whose wording is
rarest, so it is the one most dependent on the dense leg.

## The Submission Checklist, in full

Twenty-nine items on the sheet (the Instructions sheet calls it twenty-six). The ones that belong
to this stage, or that this stage can break:

| # | Item | Where we stand |
| ---: | :---- | :---- |
| 9 | The AI model backend is swappable **from inside the interface**, with no code or config change | The seam is built (provider + model per role, refusing the wrong combinations); exposing it as a UI control is the interface's work, and `RDTII_ENGINE` (J3) is what it should set |
| 12 | The core pipeline runs end to end **on the open-weights engine alone**, with no proprietary API | Proven on one provision through the real S4 path on 26 September; not yet proven end to end. This is J5 and it must be run before the freeze |
| 14 | Output Data complete — **indicator IDs as text**, verbatim snippets, live source URLs | IDs as decimal text since today; urlcheck covers the URLs; the snippet is byte-grounded |
| 15 | Coverage Matrix shows three or more economies | Depends on constraints 1 and 2 above, both now satisfied |
| 16 | Both mandatory pillars covered, 6 and 7 | Our scope exactly (M7) |
| 17 | At least one non-English source recorded in Language of Source | Three, once CN/LA/TL rows are filed |
| 22 | A second pass re-reads documents already downloaded, fetching nothing new | The manifest now records it for mapping; the fetch count itself is scraping's |
| 27 | Cost recorded per run and per engine, in US dollars | `map_report_*` and `verify_report_*` carry `cost_usd`; the manifest copies it per entry |
| 28 | Ready for **any** of the nine 2025 economies and their languages, in any pillar | The economy list is no longer hard-coded; the instrument's 61 blocks are readable; but only pillars 6 and 7 are automated, which is what the M8/M9 notification rows exist to state |

And the sealed-task sentence worth pinning above the desk: "It may be a pillar you were never
asked to work."

## One question this raises for the output work

The Discovery Tag column takes two values only, and the host defines them as: "NEW = your tool
found it and it is not in the 2025 baseline you hold. KNOWN = it was in the sample kit." A
**no-provision row** — our deterministic "no qualifying measure found" row — is neither. Round 1
tagged it KNOWN, which plan item H4 calls a miscoding.

There is a reading in which KNOWN is right: where the baseline itself records an absence for that
(economy, indicator) — score 0 with no articles cited — our absence row reproduces the baseline's
own row, and KNOWN says exactly that. Where the baseline has no such row, KNOWN is a claim about
the sample kit that is not true.

That is a judgement about how the host scores an absence, not a bug to patch unattended.

**Settled 27 September, commit `7246cf5`.** Counted from `baseline_rows.jsonl`, across the 54
(economy, indicator) cells of the six economies:

| the sample kit | cells | tagging a no-provision row KNOWN |
| :---- | ---: | :---- |
| carries its own absence row (score 0, no article) | **23** | truthful — we reproduce that row |
| records a measure this run did not find | **22** | false, and conceals a miss |
| has no row for the cell at all (every TL cell) | **9** | false — nothing to reproduce |

So 31 of 54 would have carried an untrue tag, and the middle 22 are the worse case: those are
disagreements with the baseline, not absences. `kit_absence_state()` now returns `reproduces`,
`contradicts` or `absent`; only the first earns KNOWN. The other two leave the column **blank** and
Notes say which situation it is.

Blank is a disclosed choice against an Instructions sheet that asks for one of two values, so
`submission_report_<ECON>.json` carries `blank_discovery_tag {count, indicators}` and the emitter
prints the count — if a template check rejects a blank, that number says how many rows to revisit.

Reading the baseline to set this column is not backward induction: KNOWN *means* "was in the sample
kit", so deciding it requires reading the kit. The standing rule forbids letting the baseline choose
what we map or how we score, and this does neither.
