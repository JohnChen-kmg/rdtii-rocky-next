# The three open items: the instrument copy, the economy-level `pending` cells, and Block G

29 September 2026. One day to the code freeze. Each section gives the motivation, the detail, and
what I would do. Two need your hands; one needs your judgement.

Ordered by consequence: **Block G is the one that decides whether the submission is compliant.**

---

# 1. Block G — and it is not optional

## The motivation, which is stronger than I have been saying

The final-round slide reads: *"Select at least 3 from 8 countries above (in addition to 3 mandatory
countries: Australia Malaysia Singapore)."*

**This run has zero rows for Australia, Malaysia and Singapore.** Verified just now:
`out/submission/` contains `records_CN.csv`, `records_LA.csv`, `records_TL.csv` and nothing else.
Their 142 verified rows exist only in the frozen Round 1 arm at
`C:\Users\woshi\Desktop\RDTII\pipeline-data\rdtii-p3-map`.

So this is not "108 rows versus 250". It is **a submission missing all three mandatory economies.**
Everything else on this list is quality; this one is compliance.

## Why the rows cannot simply be copied

| | Round 1's rows | what the finale needs |
| :---- | :---- | :---- |
| indicator IDs | `P6-I1`, `P7-I5` | decimal — `6.1`, `7.5` |
| columns | **13** | **14** — column N, Language of Source, REQUIRED, drives C1c |
| codebook they were judged against | Round 1's | the shipping one, whose nine blocks all changed |
| verifier that cleared them | Round 1's | the current two-reviewer chain |

Counts: **SG 42, MY 57, AU 43 = 142.**

## Two routes, and I now prefer the second

### Route A — reuse (the 27 September decision)

1. Migrate 142 rows to decimal through `normalize()`.
2. Add column N.
3. Currency-check each cited law against the new crawl — has the text changed since July?
4. Re-run `urlcheck` (Round 1: 94 of 94 green).
5. **F2, the re-judge.** ~115 of the 142 sit in cells whose wording tightened:

   | new trap | rows exposed |
   | :---- | ---: |
   | 7.5 regulator inspection / secrecy carve-out | 39 |
   | 7.3 "prescribed period" with no number | 36 |
   | 6.2 books and records with no storage locus | 22 |
   | 7.1 / 7.2 per-provision rows score zero | 12 |
   | 6.3 licensee network-security rules | 3 |

   ~**$2** batch.
6. **Disclose in the Word document** that these rows come from the Round 1 run, not the frozen
   release. Not optional.

**Cost: ~$2 and perhaps two hours of attended migration, checking and disclosure.**

### Route B — re-run Australia, Malaysia and Singapore fresh

Everything needed is already in the index: 21,088 gray pairs and 3,863 direct pairs for the three.
Costed from measured rates, with each economy's own Round 1 keep rate (AU 30.8%, SG 17.7%, MY 13.8%):

| stage | volume | cost |
| :---- | ---: | ---: |
| triage | 21,088 gray pairs | $33 |
| map, batch | 8,236 pairs → 4,335 provisions | $37 |
| verify | 1,779 fires | $26 |
| **total** | | **~$96** |

Perhaps 90 minutes of machine time, almost all unattended.

### Why B is probably the better trade now

When the reuse decision was taken on 27 September it looked like a clean $200 saving. Three things
measured since have eaten most of that margin:

1. **All nine codebook blocks changed substantively**, not just 6.2. The re-judge is ~115 of 142
   rows, not the 22 the plan budgeted — so most of the reused set has to go back through a model
   anyway.
2. **The reused rows are 13-column, legacy-ID, and Round-1-verified.** Route A ends with rows that
   need a migration, a currency check, a re-judge and a disclosure paragraph. Route B ends with rows
   that need none of those, in the shipping format, judged by the pipeline we are submitting.
3. **Our own run out-performs the baseline where we can compare it.** China filed 55 rows against 27
   scoring baseline rows, and the additions were substantive — the entire 2022–24 cross-border
   transfer apparatus for 6.4, the National Intelligence and Criminal Procedure Laws for 7.5. There
   is no reason to expect the three English economies to behave worse, and Australia's 30.8% keep
   rate is the highest we have measured.

Against that, Route B costs **$96 and a reproducibility argument**: Round 1's 142 rows are already
verified evidence, and re-running means the submission no longer contains them.

**My recommendation: Route B**, keeping Round 1's rows as supporting evidence rather than as the
filed rows. If the $96 is unwelcome, Route A is defensible — but then the disclosure paragraph has to
be honest that the mandatory economies' rows were produced by an earlier pipeline against an earlier
codebook.

---

# 2. The economy-level `pending` cells — your judgement

## What is happening

Three cells score nothing: **LA 7.1, TL 7.1, TL 7.2**.

7.1 and 7.2 are the only two **economy-level, inverted** indicators: 0 means the economy *has* a
framework, 1 means it lacks one. `rollup.py` answers them by sending the verified evidence to Opus
and asking whether a comprehensive framework exists. When every fire in the cell is overturned,
there is no verified evidence, and `_framework_score()` returns `pending` with *"no evidence rows
collected"*.

## Why it is not simply a bug

The verifier's rejections were reasoned, and the reasoning is itself a finding. On LA 7.1 it said of
Lao's Law on Electronic Data Protection:

> *"'electronic data' here is defined broadly (numbers, text, images, audio, video) rather than as
> personal data with access/rectification/erasure rights"*

That argues the framework is **not** a comprehensive personal-data regime — which supports the
baseline's 0.5, not our mapper's 0. The conclusion was reached and then discarded.

For comparison, **CN 7.1 was upheld on PIPL Art. 1**, also a purpose clause. So this is not
inconsistency; the reviewers found a real legal distinction between the two laws.

## The options

| | what it does | risk |
| :---- | :---- | :---- |
| **(a) leave `pending`** | scores nothing, Notes explains | three blank cells in the Coverage Matrix; on 15 October a drawn 7.1/7.2 could come back blank |
| **(b) score from the rejection** | pass the overturned candidates *and* the reviewers' reasons to the economy-level scorer; require it to name a controlling law or return `pending` | it must not conclude an absence from a retrieval gap — the constraint is what prevents that |
| **(c) default an empty cell to the inverted maximum** | `pending` → 1 ("lacks a framework") | **wrong.** Conflates "we found nothing" with "nothing exists". Would have scored Lao 1 when a law plainly exists |

## What I would do

**(b), with the constraint.** The scorer already returns `controlling_law`; requiring it to be
non-empty means the cell can conclude *"a law exists but is not comprehensive → 0.5"* from evidence,
and cannot conclude *"no law exists"* from silence. If it cannot name a law, it stays `pending`.

**Cost:** about an hour of code, a few cents to re-run rollup for the affected economies.

**Why it matters beyond three cells:** on 15 October the draw may name 7.1 or 7.2. If the verifier is
strict on that economy, the live run produces a blank cell inside the hour, with no time to notice.

**This is yours because it changes what a cell is permitted to conclude** — that is a methodology
choice, not a patch.

---

# 3. The instrument copy — your terminal

## The motivation

Everything last night ran against the shipping codebook through `INSTRUMENT_DIR`, so **the results
are sound**. What is wrong is the repository we tag.

| | the repo today | the workshop |
| :---- | :---- | :---- |
| vintage | legacy | decimal |
| codebook blocks | **9** | **61** |
| gold rows | **51** | **1,054** |
| signature files | `P6-I1.yaml` … | `6.1.yaml` … |

Four consequences:

1. **`contracts/instrument/` is tracked.** Whatever it holds on 30 September is what the submitted
   system codes against permanently. This is the only genuinely irreversible deadline on the list.
2. **A reviewer who clones the repo gets Round 1's nine-block codebook** and cannot reproduce what we
   filed.
3. **The shipped system cannot evaluate China or Lao at all** — 51 gold rows, none for either. That
   is how my first gold-survival run silently reported a clean funnel over the wrong population.
4. **Four `test_coverage.py` tests stay skipped** — the M8/M9 notification marks need
   `indicator_order.yaml`, which only the decimal vintage carries. The suite should go **283 → 287**.

## Why it is blocked

The sandbox refuses `robocopy` as irreversible local destruction, with `/MIR` and without. I checked
what it destroys: **exactly nine files**, the legacy `signatures/P6-I1.yaml` … `P7-I5.yaml`, in each
of two directories. All 30 files under those paths are tracked and committed, so the mirror reverses
with `git checkout`.

## The detail

Branch `w3-instrument` is already cut from `w2-mapping-finale`. `HANDOFF.md` step 3:

```
$WS   = "C:\Users\woshi\Desktop\rdtii-finale-0-instrument\instrument"
$CODE = "C:\Users\woshi\Desktop\rdtii-finale-0-instrument\code\scripts"
$RP   = "C:\Users\woshi\Desktop\rdtii-rocky-finale\stages"
robocopy "$WS\output" "$RP\p0-instrument\output" /MIR
robocopy "$WS\output" "$RP\p3-map\contracts\instrument" /MIR
robocopy "$CODE"      "$RP\p0-instrument\scripts" /MIR /XD __pycache__
Copy-Item "$CODE\indicator_ids.py" "$RP\p3-map\config\indicator_ids.py"
Copy-Item "$WS\README.md", "$WS\START_HERE.md" "$RP\p0-instrument\"
```

Then step 4, both of which must pass:

```
cd ...\stages\p0-instrument
$env:RDTII_GUIDE_TEXT = "...\rdtii-finale-0-instrument\sources\text\guide.txt"
python -X utf8 scripts\validate_instrument.py --require-vendored
cd ..\p3-map
python -m pytest tests\test_indicator_ids.py -q
```

Step 1 already passed: the workshop validator gives **PASS, exit 0**, 61/62 in scope, gold 1,054 rows
round-tripping.

## Verified in advance, so this should be uneventful

With `INSTRUMENT_DIR` pointed at the workshop the full suite gives **283 passed, 0 failed**, and the
nine query documents are **byte-identical** across the hand-off (sha256, 9/9) — so the index, the
dense top-K and the selected pairs all stay valid. `indicator_ids.py` differs from the workshop copy
**only in line endings**, which is what `HANDOFF.md`'s line-endings section anticipates.

## One thing I flagged and did not decide

`code\scripts\data\curated_exemplars.yaml` (68 KB) goes into the repo under the prescribed mirror and
holds host workbook rows. That falls under open **host question 10** — the same category as the gold
set the repo already tracks. The build scripts need it to regenerate the instrument, so excluding it
costs reproducibility. Flagged, not decided.

---

# What I would do, in order

| | | cost | who |
| :-- | :---- | ---: | :---- |
| 1 | **The instrument copy** — five commands, then step 4's two checks | $0 | you, five minutes |
| 2 | **Decide Block G: Route A or Route B** | $2 or $96 | you |
| 3 | Run whichever route you pick | — | me, unattended |
| 4 | **Decide the economy-level question** | ~1 h code | you, then me |
| 5 | C1 from the problems register — cross-checks as gates | ~1½ h | me |
| 6 | The gazette-title refusal, and TL's Civil Code citation | ~1 h | me |

Items 1 and 2 are the only ones with a hard deadline: the copy because the tag freezes the codebook,
and Block G because without it the submission has no mandatory economies.

Total spend so far: **$159.21**.
