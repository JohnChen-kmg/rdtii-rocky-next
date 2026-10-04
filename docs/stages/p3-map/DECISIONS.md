# Decisions: mapping and the two engines

Task-level choices only. Code changes belong in
`C:\Users\woshi\Desktop\rdtii-rocky-finale\docs\CHANGELOG_FINALE.md`.

Newest entries go at the top. Every entry carries a date, a decision, a reason, and what breaks if
it is reversed later. Entries marked **Proposed** are recommendations, not settled.

---

## 2026-10-04, M17 After the second hand-off: scales and economy-level questions come from the blocks; the measured requests are pinned

**Decision.** The stage reads from each block what it used to fix in code: the scores a verdict may
carry (`scoring.values`), and for an economy-level indicator the framework's name and the branches
it is asked with. The evaluator reads `label_flag` in place of a list of ids. Before any of it, a
test pins every request a model receives for the nine indicators of pillars 6 and 7, and those
requests are the same after the change.

**Reason.** The instrument of 4 October gives all 61 indicators the depth of pillars 6 and 7, with
five different scales and 13 economy-level indicators; one enum and a two-entry table no longer fit.
The nine measured indicators must not move while the other 52 are made to work, because every filed
row and every reported figure came from their requests.

**Two rules that follow from "must not move".** The scores offered to a model are the union over the
run's scope, not each indicator's own list: per indicator, 6.3, 7.3 and 7.5 would lose the 0.5 they
have always been offered. And 7.1 and 7.2 keep the scale sentence they were measured with, while the
other eleven economy-level indicators are asked with their block's scoring tree.

**The developer's decisions of 4 October.** Counting indicators: the instrument states the count rule
as data (R5), the stage does not hand-code twelve rules. What an absence scores: a field on the block
(R6), needed first for 11.2. Evaluator: suspect rows and the seven of Round 1's review are out;
advisory, host-marked and candidate rows count, with a second figure on unflagged rows. Verification
runs against a model: left for now. How the query is built from the instrument for the indicators
that lacked this depth, across the model choices now on the page: to be looked at in detail later.

**If reversed.** Restore the fixed enum and the table and every indicator outside pillars 6 and 7 with
another scale validates wrongly or ends "pending"; nothing changes for the nine.

---

## 2026-10-04, M16 A role may have its own engine, and three unmeasured engines are declared

**Decision.** `engines.json` version 1.1.0 lists each engine's models with a price card and declares
C (DeepSeek), D (Kimi) and E (ChatGPT), reached by one OpenAI-compatible client. A role takes its own
engine from `RDTII_ENGINE_MAPPER`, `RDTII_ENGINE_VERIFIER` or `RDTII_ENGINE_ESCALATION` and otherwise
follows `RDTII_ENGINE`. Every engine and model the pipeline was not scored on carries `measured: false`.
Added after the finale, on the branch; A and B and the requests they send are unchanged.

**Reason.** The developer asked on 4 October for a model choice per step from the interface: other
Claude models first, then DeepSeek, Kimi and ChatGPT. M1 already put engines and prices in JSON so that
this would be a declaration; what was missing was a client for the third kind of provider and a way to
give one role a different engine. Decision #3 stands: triage stays local, and a role whose engine lacks
its key is refused, never moved to a local model.

**What is not claimed.** No row has been produced on C, D or E, or on Claude Sonnet 5.5, Opus 5.5 or
Fable 5.1; no key for them was at hand on 4 October. The client was exercised against a local
OpenAI-compatible server only. The prompts and the traps were written for Claude. A figure from one of
these models is a new measurement, not a continuation of the reported ones.

**If reversed.** Remove the three engines and the role variables and the stage is the two-engine stage
of the submission; nothing else depends on them.

---

## 2026-09-27, M15 Selection recall is reported as 56/63; the 61/63 figure is in-sample and must be labelled so

**Decision.** The four per-(economy, indicator) overrides in `config/selection.json` stay at their
current values, and the number we report changes instead.

- **Selection recall: 56 of 63 = 88.9%.** This is the figure no gold row influenced.
- **61 of 63 = 96.8%** is disclosed separately and always labelled *after four per-cell ceiling
  adjustments informed by the gold set* — an in-sample result, not a measurement of the method.

**Reason.** The overrides were derived by backward induction. `selection.json`'s own `_measured`
field says so: *"Each entry names the gold row that needed it, its in-economy rank and its cosine."*
SG 7.1's ceiling went 400 to 600 because gold `r1-sg-039` sits at rank 538; CN 7.5's went to 3,800
because gold rows sit at ranks 2,302 and 3,416. Reporting 61/63 as recall would therefore be
circular: the ceilings were widened until the gold rows fit, and the figure then reports that they
fit.

Measured 27 September on `run_2026-09-27`, all 63 resolvable gold rows:

| configuration | candidate pairs | gold reached |
| :---- | ---: | ---: |
| as shipped, four gold-derived overrides | 45,141 | 61/63 |
| overrides removed, gold never consulted | 42,260 | **56/63** |
| gold-free rule: ceiling = rows above θ, cap 4,000 | 90,219 | 59/63 |

Five hits depend on the overrides: `r1-sg-039`, `r2-cn-043`, `r2-cn-065`, `r2-cn-067`, `r2-cn-070`.

**Why the parameters stay.** Each override also carries an independent θ-based justification that
never needed gold — for CN 7.5, *all* 3,747 of China's rows in that cell clear θ, because
government-access language is pervasive in Chinese law, so the cell is legitimately deep rather than
noisy. That reasoning stands on its own. Switching to the gold-free rule now would invalidate the
21,175 triaged pairs and the $41.42 already spent, for two fewer rows at double the candidate volume.
It is a better fit for the M14 experiment, where it can be tested against a different embedder.

**What must change in the write-up.** The `_measured` justifications lead with the θ-based reason and
demote the gold row to how the cell was *noticed*, explicitly flagged as such. Any place quoting
0.968 as recall is corrected to 0.889.

**Consequence if reversed:** a desk reviewer who reads `selection.json` finds the gold rows named in
the justification, concludes the recall figure is fitted, and discounts it — and is right to. Stating
the un-tuned figure first costs eight points of a number and buys the credibility of every other
number in the submission.

**Standing rule this restates.** The gold set scores a rule; it never chooses a parameter. No
backward induction.

---

## 2026-09-27, M14 The threshold and the cap freeze as they are; tuning them is a post-deadline experiment, conditional on the retrieval model

**Decision.** `θ`, the floors, the ceilings and the language offsets in `config/selection.json` ship
at their current values. Finding the best threshold and cap becomes a named experiment for 1–14
October, run jointly with the model comparison rather than before it.

**Reason.** Three measurements, all 27 September, recorded in
`notes/2026-09-27-cap-function-and-query-review.md` §9.

- A uniform ceiling multiplier gains **zero** gold laws: 61 of 63 at 1.0×, and still 61 of 63 at
  2.0×, for 61% more candidate pairs. The ceiling is not the binding constraint on recall.
- At its margin the ceiling is **not discriminating**. Doubling it moves the marginal cosine under
  0.004 per 100 ranks in **34 of 36 (economy, indicator) cells**, Australia included. It is a budget
  dial, not a relevance filter.
- The one miss that looked like a defect is a **within-law ordering failure** no cap can fix: in
  China's Cybersecurity Law the penalties article (Art. 73, cosine 0.568) outranked the article
  carrying the duty (Art. 21, 0.561), and triage then correctly refused the penalties article.

**Why conditional on the model.** The flat band is a property of BGE-M3 at this depth, not of the
task. Another embedder may have real gradient there, which would make the ceiling meaningful again.
Threshold, cap and embedder therefore have to be tuned together; values fitted hard to this embedder
would not transfer, which is the worst input to the comparison the experiment exists to run.

**Why not just fix the one cell.** Raising CN 7.4's ceiling until `r2-cn-065` returns is fitting to
the host's 2025 database, which the standing constraint forbids. The general finding is admissible
evidence; the gold-row-shaped fix is not.

**Consequence if reversed:** cap values tuned before the embedder is settled get re-tuned anyway, and
any gain measured now is unattributable — it could be the cap or the embedder. Reversing also spends
candidate volume for no measured recall: 1.61× the pairs at 2× the ceiling bought nothing.

**Accepted cost.** The two selection misses (`r2-cn-069`, `r2-la-039`) and any row whose best
provision loses to a topically-similar sibling. Measured position: **61 of 63** resolvable gold laws
reach selection, **56 of 63** survive triage.

**Safe to defer because it is settings, not code.** All of these values are reachable through
`SELECTION_CONFIG` without touching a tracked file, so 30 September does not close the question.

---

## 2026-09-27, M13 **Proposed** The pre-freeze list, and what is deferred behind a measurement

**Proposed, not settled.** Recommendations from the analysis in
`notes/2026-09-27-cap-function-and-query-review.md`, which holds the measurements behind each line.

**Settled by measurement, and closed:**

- **No corpus-size term in the cap.** Share of corpus selected runs 2.97% (Australia, 302,564
  provisions) to 20.58% (China, 50,026), anti-correlated with size; the two smallest corpora deviate
  in opposite directions. A size term would spend more where retrieval is already perfect and would
  hand Australia seven times Lao's budget for the same live hour.
- **No sparsity-aware floor.** `m_eff = max(m, 3 × n_above)` reaches one of the three rows it was
  designed for.
- **No different embedding package.** The query's language dominates any plausible model difference:
  a Chinese query moved a gold row from rank 798 to 66 on the same embedder.
- **No prompt experimentation for engine A.** Of the five gold rows the mapper declined, three were
  correct refusals of score-0 rows and two were operative rules sitting in delegated legislation the
  mapper never saw. Coverage costs 23 rows; judgment costs 2.

**Proposed before 30 September, in order of value:**

1. ~~**J6** — `main.py` writes an empty dense stub, so on the interface path a China or Lao run
   retrieves nothing and reports success.~~ **Done, `ff92190`. The framing above was wrong and the
   correction matters.** `main.py` did not silently return nothing: it refused, at argument
   parsing, before any retrieval. It kept Round 1's three-economy table, so `--economy China` exited
   2 and `--docs cn-…-001` exited 2 with "no recognizable economy prefix (sg-/my-/au-)". No run
   could reach the stub, so no wrong submission was ever reachable from that path — the defect was
   that the shipped entry point could not run six of the economies the stage was ready for.
   The silent-zero failure was *latent*: widening the economy table on its own would have created
   it. So one commit does both — `config/economies.py` as the single home for codes, Coverage Matrix
   strings and corpus language, and `_retrieval_legs()`, which takes the bm25-only shortcut only
   when every economy in the run has an English corpus, runs both legs otherwise, and refuses by
   name when the dense leg cannot run. `_stub_dense_leg()` now mirrors `bm25_top.npz`'s own keys
   instead of writing `P6-I1_idx` against a leg keyed `6.1_idx`. 40 new tests, the first to reach
   `main.py` at all.
2. **Run-time language offset** by quantile matching, configured values kept as an override. Six of
   the nine live-test languages have no measured offset and the default can land anywhere between
   the 76th and 99.99th percentile. It also fixes a mis-calibration in rows we will actually file:
   Timor-Leste is selected 2.1 percentile points too strictly, China 3.6 too loosely.
3. **Run-time query translation** for the drawn indicator and language — two documents in the hour,
   against 558 pre-translated. Measured 12× rank improvement on Chinese; unverified on Lao.
4. ~~**Promote `NEW_CONF`, `NEW_CAP`, `NEW_CAP_TAIL` and the two worker counts to settings**, defaults
   unchanged.~~ **Done, `1de0d5b`** — seven numbers, not five: `SECTORAL_MAX` was in the same block,
   and there were three worker counts (`triage/haiku.py` 12, `mapping/runner.py` 8,
   `verify/blind.py` 8), not two. Defaults are Round 1's values exactly and two tests pin them, so
   the promotion changes no behaviour. On 15 October the draw is one economy and two indicators, so
   `NEW_CAP = 8` caps the live export at roughly 16–20 NEW rows however much the tool finds — raise
   it before the hour, not during it.

**Deferred behind a measurement:** per-engine prompt profiles — the seam, not the content. Gated on
Block F's China run, which produces the same fire-rate diagnostic for a non-English corpus. If China
looks like Singapore the prompt is portable and the seam buys nothing before the freeze.

**Why proposed rather than settled:** items 2 and 3 are code, so they freeze with the tag, and they
compete for the same days as blocks C, F and H. The developer decides what fits.

---

## 2026-09-27, M12 The scored selection is adopted, with its measured performance

**Decision:** the developer accepted the result on 2026-09-27. S2 selects by score, not by a fixed
per-cell cap:

    N(economy, indicator) = clip( |{ p : cos(p, query) >= theta + delta(language) }|, floor, ceiling )

with the band split at cosine 0.65, a sparse top-up on 6.1, 6.4 and 7.3, and per-(economy,
indicator) overrides each earned by a named gold row. Parameters live in `config/selection.json`,
which is settings and may still move on 15 October; `SELECT_MODE=caps` reverts to Round 1's path.

**Measured, on the six-economy index of 767,105 provisions (`run_2026-09-27`):**

| | |
| :---- | ---: |
| candidate pairs | 46,494, or 7,749 per economy, against 13,000 under the fixed caps |
| gold gate at this stage | **61 of 63 resolvable rows, 96.8%**, against a 0.95 target |
| cells by binding term | ceiling 28, theta 15, floor 11, none exhausted |
| projected cost, CN+LA+TL | $86 live, $67 with the batch lane |

**Measured end to end on the frozen Round 1 arm**, where every stage left an artifact: 80.6% of
resolvable gold rows reach the CSV. Retrieval and mapping lose nothing; the loss is the mapper
declining to fire (13.9%), then verification (3.2%) and curation (3.3%). By class, subject-specific
100%, horizontal instrument 85.7%, recurring duty 76.5%, prohibition 71.4% — the losses sit where
the traps are. Combined prediction: about 78% of resolvable gold rows reach a filed row, and about
81% for the three English economies.

**Why:** at equal gold recall it selects 40% fewer candidates than the fixed caps, and where it
does bind, the report says which term bound it, so a missing row has one attributable cause.

**The larger number this does not address:** 23 of 86 in-scope gold rows, 27%, are lost before the
funnel starts because the law is not in the corpus. No parameter available to this stage touches
that; see `notes/2026-09-27-laws-the-corpus-does-not-hold.md`.

**Consequence if reversed:** `SELECT_MODE=caps` restores Round 1's behaviour exactly, verified cell
for cell, at 13,000 pairs per economy and the gray band restored by PREFILTER_FLOOR=0.0001.

---

## 2026-09-27, M11 The final-round documents are the standard; the orientation slide is not

**Decision:** the developer's call, 2026-09-27, in their words: "final doc is the standard, the content
from the first round regarding the final content isn't the best to see." Three host documents name
different economy lists, and this settles which one this stage builds against:

| Source | Economies named | Status |
| :---- | :---- | :---- |
| `README_template_FINAL_ROUND.md`, `submission_template_stage3_v2`, `OUTPUT_TEMPLATE_FINAL_ROUND.xlsx` | Thailand, Viet Nam, Indonesia, China, India, Kazakhstan, Lao PDR, Mongolia, the Russian Federation | **governs** |
| `Finalist Orientation_Slide.pdf` slide 5, 18 August 2026 | Australia, Malaysia and Singapore mandatory, then at least three of eight including Timor-Leste | superseded |
| `ESCAP-RDTII-2.1_ Round 2 Database.xlsx` | seven sheets: no Viet Nam, no Kazakhstan, no Timor-Leste | what we actually hold |

**What follows.** The live test draws from the nine, and this stage has a corpus for two of them,
China and Lao PDR. The other seven are not a corpus problem to solve before the freeze — the live
hour expects live discovery, which is what C5a's six marks are for — they are a *readiness* problem,
and readiness is code that must land before 30 September:

- the language offset must be computed at run time, because six of the nine languages have no
  measured offset and the configured default can land anywhere between the 76th and the 99.99th
  percentile of an economy's own distribution (measured 2026-09-27 across six economies);
- the indicator query document must be translated at run time for the drawn indicator and language,
  because pre-translating is 62 indicators times nine languages and translating the drawn pair is two
  documents;
- `main.py` must run the dense leg (J6) — **done, `ff92190`**. It now takes the bm25-only shortcut
  only when every economy in the run has an English corpus, and refuses by name rather than stubbing
  an empty dense leg for an economy the sparse leg cannot read.

**Timor-Leste keeps its place in the submission.** It appears on no final-round list, but the
Coverage Matrix has a Timor-Leste row and C1a asks for three or more *diverse* economies; a
Portuguese, 99.6%-OCR corpus is the strongest diversity evidence we hold. It is not a live-test
candidate, which is a different axis. Nothing built for it is wasted.

**Why:** the three lists cannot all be right, and the one the secretariat will mark against is the
one it published with the final-round templates. Open question 1 asks the secretariat to confirm it;
the answer has not arrived, and the email folding it in
(`3_Final_Stage/HOST_EMAIL_DRAFT_2026-09-20.md`) is still not recorded as sent.

**Consequence if reversed:** if the orientation slide governs after all, the run-time work is merely
useful rather than necessary, and nothing done for it is wasted — the same code makes the offsets
right for Timor-Leste and China, which are mis-calibrated today by +2.1 and -3.6 percentile points
against the English economies. The reverse is not true: building against the slide and being drawn
Thailand leaves no path at all.

---

## 2026-09-26, M10 Map in the source language; translate the result, for people

**Decision:** the developer's call, 2026-09-26, in their words: "we only translate for the mapped result
and when language doesn't fit." Four parts:

1. **Evidence is never translated.** The `Verbatim Snippet` stays in the source language at its recorded
   offsets, and column N names that language. This upholds extraction's D5 and the host's column I rule.
2. **The mapper judges the source text** in every language it handles. Measured as low risk today:
   Portuguese, Chinese and Malay. English needs nothing.
3. **Translation happens after mapping**, on results, for the audit view, the reviewer, the 15 October
   judges and the English-facing fields. The mapper already writes its rationale in English, so the
   workbook's prose costs nothing.
4. **Where a language is measured not to fit**, a gloss may enter the prompt as a reading aid, but the
   quote must still be cut from the source text by span selection, never copied from the gloss. Lao is
   the open case and the only one; it is decided by experiment E6, not by argument.

Where a publisher's own English exists it is preferred over any model output. The Lao gazette published
English for 53 laws, including the pillar 6 and 7 statutes; none reached hand-off #2, because the corpus
merge files a translation as a superseded copy of its Lao twin. A request to carry them as a gloss field
is open with collection and extraction. Every machine gloss is labelled as machine-made.

**Why:** if the model judges a translation it will quote the translation, and an English quote is not a
substring of the stored Lao or Chinese text. That either ships an ungrounded quote or forces an
alignment back to source offsets that nothing does reliably on OCR'd text. C2b's 10 marks rest on
byte-exact quoting, so this is a correctness rule, not a preference. The economics agree rather than
compete: glossing after verification is about 6.5 hours of local GPU work that hides underneath the
hosted API calls, measured at 5.2 s per provision on `gemma3:12b`, while glossing every candidate
before mapping is about 29 hours and blocks the mapper.

**Consequence if reversed:** translating before mapping puts a 29-hour local job on the critical path
and, worse, makes every quote a translation artifact. The failure is quiet: the rows still look right,
and the grounding check either fails wholesale or has to be relaxed, which is the one check this stage
cannot afford to relax.

## 2026-09-20, M9 The user notification covers every indicator the tool does not automate

**Decision:** the developer's call, 2026-09-20, widening M8 to match instrument D14. For every
indicator the instrument marks as not automated, for whatever reason, the mapping stage does not run
the mapper. It writes the notification row, with the reason category in the sentence: outside the
automated scope; practice or external evidence; the tier that answers it is not published by this
economy's portal. The register of marks is
`C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\COVERAGE_AND_MANUAL_CHECKS.md`.

For a run whose task falls outside pillars 6 and 7, the stage writes the notification rows for the
drawn indicators and stops. It does not map pillar 6 and 7 seeds against a pillar 4 question. That
needs the crawler and `main.py` to pass the drawn pillar through instead of rewriting it to 6 and 7,
item A4 in the scraping workshop's `notes\INSTRUMENT_IMPACT_2026-09-13.md`. Until A4 is fixed, this
entry cannot be honoured on the day.

**How, proposed.** The reason comes from the instrument's mark, never from a list here. The sentence
is one string in one place. The review screen shows the flag before the export does.

**Why:** the mark is only honest if it is complete. A notification on some uncovered indicators and
silence on others tells the reader that silence means covered. The host's own readiness table says an
honest gap costs nothing.

**Consequence if reversed:** partial marking, which is worse than none, or a live-test draw outside
the automated scope answered with the wrong documents and full confidence.

## 2026-09-20, M8 Rows for indicators outside the legal dataset carry a user notification

**Decision:** the developer's call, 2026-09-20, recorded as instrument D13. For any indicator the
instrument marks as answered outside the legal dataset, the mapping stage does not run the mapper. It
writes the row, or the null row, with one fixed sentence in Notes: the result for this indicator may
come from a source other than the legal dataset and should be checked outside the tool.

**How, proposed.** Read the marker from the instrument rather than keeping a list here, so the two
cannot disagree. Leave Confidence empty, because there is no verdict to be confident about. Never tag
such a row NEW. Where a per-economy override applies, the sentence names the tier the portal does not
publish. The interface shows the same flag on the review screen, so a policy officer sees it before
the export does.

**Why:** the finding at
`C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\ISSUES\2026-09-20_subordinate-tier-coverage.md`.
Some indicators are answered by catalogues, standards, filings or blocklists that no legal instrument
carries. Running the mapper over statute text for them produces a plausible verdict that reads as
evidence. The host's format rule asks for an informative statement where there is no relevant law,
and the live-test short note asks which indicator a ministry should check first. This sentence is that
answer, written into the row.

**Consequence if reversed:** the mapper cites a real act for a question the act does not answer. The
host scores a real act cited to the wrong section as zero. This is the same failure with a better
disguise, and it lands on the indicators where a reviewer can least easily check the tool.

## 2026-09-12, M7 Six economies and pillars 6 and 7 are required. Further is optional

**Decision:** Mapping covers the nine scoreable indicators of pillars 6 and 7 across six economies.
Mapping for further pillars is optional. The engine work, steps 2A to 2E, is unchanged, because the
engines and the ledger do not depend on how many indicators exist.

**Why:** The developer's scope call, taken against a freeze minimum that had outgrown 18 days. The
existing single cached instrument prefix already covers nine indicators, so the per-pillar prompt
that twelve pillars needed is no longer required.

**Consequence if reversed:** The per-pillar prompt and the instrument loader come back as
dependencies. What is lost by keeping it: the "further domains" share of C1b, and live-test discovery
on any other pillar. The workbook's 101-row limit still matters. Six economies at Round 1's density
is roughly twice the 142 rows Round 1 filed, so host question 7 stays live.

## 2026-09-12, M6 Engine B is a hosted open-weights endpoint, with the local lane kept as proof. Proposed

**Decision:** declare Engine B as a hosted endpoint serving an open-weights checkpoint. Keep the
existing Ollama lane as a second, local demonstration that the weights really can be run here.

**Why:** C5b is observed live in a UN building. Local inference on venue hardware is not a bet
worth taking, and five teams will be on the same network in the same hour. The host's Section 5
language says a hosted open-weights API is acceptable. Question 5 in
`C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\OPEN_QUESTIONS_FOR_HOST.md` asks the
secretariat to confirm that for C4b on 30 September and for C5b on 15 October. Keeping the local
lane means the answer changes which engine is default, not which code ships.

**Consequence if reversed:** if the secretariat requires locally run weights, Engine B becomes the
Ollama lane and throughput drops to roughly 1 provision per second on one consumer GPU, measured.
The live demonstration then has to be scoped to a document count that finishes inside the window.
Decide that scope before 30 September, because after the freeze only settings may change.

---

## 2026-09-12, M5 Model choice fails before spending, not after

**Decision:** refuse to build a paid client for a model with no entry in the price table. An
unknown model raises at construction time.

**Why:** `usd()` in `config/llm/base.py` returns `0.0` for any model absent from `PRICES`. An
unpriced provider therefore makes every cost report read as free, and the budget guard in
`mapping/runner.py` never fires because the running total never rises. The secretariat verifies
cost claims against the code, so a silent zero is worse than a crash. The precedent already exists
at `mapping/batch_runner.py:341`, which asserts the mapper model is in `PRICES` before submitting a
batch. This decision generalises that assert to every paid path.

**Consequence if reversed:** a typo in a model name produces a full run that reports zero dollars,
and the error is invisible until a bill arrives or a judge asks. Reversing this also removes the
only mechanism that forces a new provider's prices to be recorded with a source and a date.

---

## 2026-09-12, M4 The extract stage's vendored config package is not merged with this one

**Decision:** leave `stages/p2-extract/config/llm/` separate from `stages/p3-map/config/llm/`.
Mirror the ledger writer file into it instead of unifying the packages.

**Why:** the two packages share file names but their client interfaces have already diverged. The
stages share no Python by design and are wired only by files on disk. Merging them would create the
first cross-stage import in the repo, three weeks before a freeze, for no marks. Mirroring one
file is a copy with a note at the top saying where the canonical version lives, which is the
pattern the repo already uses for `indicator_ids.py`.

**Consequence if reversed:** a single shared package means the extract stage and the mapping stage
must upgrade their client contracts together. Any change to `complete()` then touches two stages
and their tests, and the 30-minute clean-machine deploy gains a shared dependency that both stages
must resolve identically.

---

## 2026-09-12, M3 The Anthropic Batches path stays Anthropic-only

**Decision:** `mapping/batch_runner.py` remains an Anthropic-only optimisation, declared as part of
Engine A. It is not generalised to other providers.

**Why:** it buys 50 per cent on every token class, which paid for the Round 1 bulk runs. No other
provider offers the same transport, so generalising it means writing a second batching protocol.
The live test on 15 October uses the live path, so this costs nothing on the day. Declaring it as
an Engine A optimisation is also honest: it is a real cost lever, and it is not available on
Engine B.

**Consequence if reversed:** generalising the batch lane adds a second asynchronous transport, with
its own polling, state file and failure modes. It saves money only on runs that are not on the
clock.
If Engine B later needs bulk throughput, raise its worker count first.

---

## 2026-09-12, M2 One run means one output directory, with a run manifest

**Decision:** every run writes into its own output directory and records a run manifest naming the
engine actually resolved, the model per role, the commit and the input document count.

**Why:** the mapper resumes from existing verdicts. `run_mapping()` in `mapping/runner.py` reads
`verdicts_<ECON>.jsonl`, collects the provision ids already judged, and skips them. A second engine
writing into the same tree would therefore judge nothing, inherit the first engine's verdicts, and
report a perfect match. That is a false result in the exact place the live test is watching. A
separate directory per run makes the comparison in step 2E possible at all, and the manifest is
what proves the second pass covered the same documents without fetching any.

**Consequence if reversed:** the engine swap cannot be demonstrated honestly. Any apparent
agreement between engines becomes unfalsifiable, and 4 of the 10 live-test marks rest on it.

---

## 2026-09-12, M1 Engines and prices are declared in JSON, not YAML

**Decision:** `config/llm/engines.json` and `config/llm/prices.json` are JSON. Configuration that
the interface must read is JSON throughout.

**Why:** the interface is deliberately dependency-free. `interface/dashboard.py` is stdlib-only,
and that is the shortest path through the 30-minute clean-machine test. JSON is in the standard
library and YAML is not. The mapping stage already reads YAML for the instrument signatures through
PyYAML, so the stage could read either. The interface cannot.

**Consequence if reversed:** the interface gains a dependency, or it gains a hand-rolled parser,
or the engine list has to be duplicated in a second format. All three are worse than losing
comments in a config file.

---

## Still open

| Question | Blocks | Where it is tracked |
| :---- | :---- | :---- |
| Does a hosted open-weights endpoint satisfy C4b and C5b? | which engine is default on the day | question 5 in `C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\OPEN_QUESTIONS_FOR_HOST.md` |
| Which two providers are declared? | 2D, and the Section 5 text | decided when the 2B experiments run, not before |
| Does the ledger cover p2-extract, or p3-map only? | the wording of the submission's cost claim | cut list item 1 in PLAN.md |
