# Overnight, 27 September: the migration, the S0 gate, and the scored selection

Blocks B, D and E of the three-day plan, plus J1 to J4, H1 to H3, H5 and the evaluator decision.
Ten commits on `w2-mapping-finale`; the test suite went from 49 to 181. Nothing was spent: every run below was
local, and everything that read the frozen Round 1 arm read it read-only, writing into a scratch
copy.

| Commit | What |
| :---- | :---- |
| `275c39a` | One normalising instrument loader; decimal IDs and any economy through eleven files |
| `2710b6b` | A missing API key refuses instead of handing mapping to a local model |
| `3581ea1` | S0's contract checks become a gate; every setting documented |
| `62dcc92` | The scored selection wired into S2; the floor that emptied the gray band |
| `2e14f70` | The run manifest (J4), and a batch lane that cannot bill the wrong engine (J1) |
| `4b93bb1` | Column N, Language of Source, and economy names the Coverage Matrix can count |
| `c7648d7` | The snippet gates every row (H5); two trap checks finally do something (H3) |
| `9b0f54b` | Two named engines selected by one variable, engine B pinned by digest (J2, J3) |
| `787b234` | The evaluator measures its own caveat instead of asserting it |
| `3abbb2e` | The two paid stages that recorded no cost now do |
| `ea9b921` | The coverage mark, read from the instrument; China's pillar 6 says so (M8, M9) |
| `fbe7e34` | The quote is cut from the source, so a Chinese row is not lost to one comma |
| `64790d7` | Tests for which economies the URL check actually checks |

## The part that matters: it was verified, not just changed

Block B's exit condition was a Singapore re-emit. Run against the frozen arm, with the **finale**
instrument vendored and decimal IDs live throughout:

| Check | Round 1 | Re-emit | |
| :---- | ---: | ---: | :---- |
| NEW/KNOWN rows | 811 | 811 | every field identical, `baseline_match`, `law_fuzzy` and `match_evidence` included |
| `records_SG.csv` rows | 42 | 42 | all 13 columns, every field identical |
| Fields that differ | — | 1 | the Notes cross-reference that names an indicator: "see the 6.4 rows" |
| Rollup, provision-level | 7 scores | 7 scores | identical, escalation clause included, now read from the codebook |
| S2 in caps mode | 9,750 direct / 29,250 gray, 27 cells | same | gold recall 37/37 |
| S2 in scores mode | — | 9,698 pairs/economy | gold recall 37/37, against 13,000 pairs in caps mode |

The 7.1 and 7.2 rollup scores are the only ones not compared: they need one paid economy-level
call each, so the test stubbed the call and they came back `pending`, which is the documented
behaviour when that call fails.

## Four defects that only a run could find

### 1. `PREFILTER_FLOOR` defaulted to a value that empties the gray band

An RRF score is `1/(60 + rank)`. The code default, 0.008, therefore cuts in at about rank 65 —
inside every direct cap, which run from 150 to 600. Measured against the reference arm: on the
code default the gray band is **0 rows** where Round 1 filed 29,250, and gold recall falls from
37/37 to 35/37. Round 1 itself ran 0.0001, from its `.env`.

This matters because `SELECT_MODE=caps` is the revert path if the scored selection surprises us on
15 October, and a revert that silently drops three quarters of the candidates is not a revert.

It also corrects a call I made earlier tonight: Block D resolved the `.env.example`-versus-code
disagreement in favour of the code, on the reasoning that an example file goes stale. The
measurement says the opposite — the example was right and the code default had never been
exercised.

### 2. A missing API key silently downgraded mapping to a local model

`get_llm` fell back to `OLLAMA_MODEL` whenever `ANTHROPIC_API_KEY` was empty, for every role,
printing one line. In Round 1 that was a convenience for working without credits. For the finale
it is a correctness hole: kickoff decision #3 reserves mapping, verification and tie-breaks for a
hosted model, and C4b/C5b declare two engines by name. An unset key during a run would file rows
judged by `llama3.1:8b`, bill nothing, and report success — and nothing in the output would say
so.

Found by accident: the rollup test blanked the key to keep the run free, and the economy-level
call resolved to `OllamaClient(llama3.1:8b)` and hung on a GPU already busy embedding.

Judging roles now refuse, naming the variable and the explicit local route. Triage is untouched —
it is local-first by design.

### 3. `language_of_source` is null on all 1,085 Chinese laws

Every other economy has it: AU 1,277/1,277 eng, LA 1,762/1,762 lao, MY 1,380 eng + 9 msa, SG
738/738 eng, TL 2,879/2,879 por. China has none, while every Chinese **provision** carries
`language_of_source_name: Chinese`.

Two things read it: the CSV's language column, and the selection threshold's per-language offset.
S0 now fills the name from the provisions where the law row is silent, so China resolves to `zho`
(offset −0.02) rather than to the conservative default (−0.03). Request R5 below asks for the
field itself.

### 4. Round 1's artifacts are unreadable to a decimal stage, silently

Anticipated as plan item B11, but the shape is worth recording: every join between a stage and a
run artifact is on `(provision_id, indicator)`, and none of them raises on a miss. Reading Round
1's `verdicts_SG.jsonl` with decimal IDs in memory produces an empty `mapv`, an empty `tags` list,
and a CSV of nothing but no-provision rows — reported as success. `from_artifact()` now normalises
the ID at every artifact read.

## The baseline had a second book, and a column read at the wrong place

Two findings while migrating `discovery/baseline.py`:

- The **Round 2 host database** is in the repo's reference tree and has an identical layout. It
  carries the baseline rows for China (31 in pillars 6 and 7) and Lao PDR (13); Timor-Leste is in
  neither book, so every TL fire is NEW by construction and the Notes have to say why. Both books
  are now read, and Round 1 keeps its `baseline_id`s so the reuse path still joins.
- The **"Note" column is L on Singapore and China but M on Australia and Lao PDR.** Round 1 read L
  unconditionally, so every Australian note was dropped — and a note is where the baseline often
  cites the section that decides KNOWN versus NEW. It is now located from each sheet's header.
  Measured consequence for Round 1: 13 rows gain a note, 4 of them in pillars 6 or 7, and **0 of
  51 cited-section sets change**, so Round 1's tagging is provably unaffected. For Lao PDR, whose
  note sits in M, it would have mattered.

## What this does to the cost of Block F

Nothing, and that is the point: F1's estimate of ~23,600 candidate pairs and $162 live / $112
batch already assumed the scored selection (7,864 × 3 economies). Until tonight nothing called it,
so the estimate described code that was not running. It now describes the code that runs.

## Requests to other workstreams

**R5 — extraction.** `language_of_source` is null on all 1,085 CN law rows while the provisions
carry `language_of_source_name: Chinese`. Mapping fills the gap locally, but the field is part of
the 0.3.0 contract and the CSV's language column is marked. Related, and not blocking: `law_name_en`
is null on every provision record while being populated on every law row (CN 1,085/1,085, LA
1,762/1,762, TL 2,877/2,879). Mapping reads the law row, so nothing is lost — but a consumer who
trusts the provision field would find nothing there.

**No new instrument request.** The loader reads both vintages and they agree on every answer the
stage uses for the nine automated indicators.

## Not touched, deliberately

- **Block C, the instrument hand-off.** `HANDOFF.md` step 5 says to commit only when we agree.
- **`main.py` (J6).** The empty dense stub is still there, and it is still the highest-value code
  fix left: on that path a China or Lao run retrieves nothing and reports success. It is the
  interface's own file, so the patch is proposed rather than applied. See
  `2026-09-27-sparse-leg-blind-to-cn-la.md`, which now also answers whether China and Lao need
  another package. They do not — a tokeniser would not return a single extra row, because the
  query is English and the corpus is 99.3% non-Latin.

## The runbook for when the embedding run finishes

It was at 200k of 767k rows at 02:00, 53 rows/s, so about 05:00. The index it leaves behind keys
its arrays `P6-I1_idx`, because the run started before the decimal switch; `select.py` reads either
vintage, so nothing is lost either way. S0 does need re-running, for the four document fields it
now carries into `doc_meta.json`.

The embeddings are cached by row **count** and model, not by row order, so the one real risk is a
corpus whose order changed under them. `corpus_ids.json`, written by tonight's BM25 leg, is the
snapshot that settles it — compare before rebuilding the sparse leg, which overwrites it.

```
RUN=.../run_2026-09-27
# 1. the corpus row order must be unchanged, or the cached embeddings are misaligned
python -m src.p3map.cli ingest                     # ~45 s; rewrites the corpus and doc_meta
python - <<'EOF'
import json
ids = json.load(open(f"{RUN}/index/corpus_ids.json", encoding="utf-8"))
new = [json.loads(l)["provision_id"] for l in open(f"{RUN}/index/prefilter_corpus.jsonl", encoding="utf-8")]
print("order identical:", ids == new, len(ids), len(new))
EOF
# 2. only if that says True
python -m src.p3map.cli prefilter --leg bm25       # minutes; decimal keys, rewrites corpus_ids
python -m src.p3map.cli prefilter --leg dense      # resumes at n; recomputes top-K, minutes
python -m src.p3map.cli select                     # scores mode
```

Then the check still outstanding from the sparse-leg note: count the **dense** top-K by economy.
If China and Lao are thin there too, retrieval as a whole is the problem rather than one leg.
`select_report.json` answers it directly now — a cell that ran out of ranking is reported as
`bound_by: exhausted` and warns on stdout.

---

## Added after the first half of the night

### The host's own template turned out to be the authority on three things

Read in full and written up separately in `2026-09-27-host-output-template.md`. The short version,
because it changes work that was already planned:

- **the decimal ID migration is worth marks, not tidiness.** Column O of the Output Data sheet is
  the host's formula `IFERROR(INT($E9), IFERROR(VALUE(LEFT($E9,FIND(".",$E9)-1)),"?"))`, and the
  Coverage Matrix counts only rows whose pillar came out a number. `P6-I1` yields `"?"`, so filing
  Round 1's ID form would have shown **zero provisions for every economy** on the sheet C1a is read
  from;
- **the economy string must match the Coverage Matrix row label**, which is `Lao PDR` — not the
  Instructions sheet's "official UN country name, e.g. Lao People's Democratic Republic". The
  matrix counts with COUNTIFS against column A, so the prose loses to the formula;
- **column N is a language name**, not a code, and it "drives criterion C1c".

Both are implemented. Column N will carry English for AU/MY/SG, Lao for LA, Portuguese for TL,
Bahasa Malaysia for nine Malaysian laws, and Chinese for CN through the provision-level fallback —
three non-English languages where checklist item 17 asks for one.

### The zero-score filters cost one row in 142

`trap_checks` were written by the mapper and read nowhere, and only NEW rows were gated on
groundedness. Both now apply to every row, and the measured effect across all three Round 1
economies is:

| | Round 1 | Re-emit | |
| :---- | ---: | ---: | :---- |
| Singapore | 42 | 42 | no row lost or gained |
| Malaysia | 57 | 57 | no row lost or gained |
| Australia | 43 | 42 | one row dropped, one replaced |

Australia's two changes are the whole cost of both filters: a `6.1` row on the Competition and
Consumer Act dropped because the mapper itself flagged it government-data-only, which the codebook
does not score for 6.1-6.4 or 7.3; and a `7.3` KNOWN row whose verbatim quote could not be found in
the source, replaced by a grounded verified fire for the same baseline row.

**That second one has a price, and it is recorded.** The replacement cites a different act, so gold
row `r1-au-041` — which cites the Telecommunications (Interception and Access) Act 1979 for 7.3 —
is no longer matched, and Australia's measured row recall falls from 0.889 to 0.75. The honest
choice was between filing an unverifiable quote and losing the hit, and the host verifies column I
against the source. What it points at is a curation task: find a grounded quote for s.187C(1) of
that Act, and the hit comes back.

### The evaluator was going to ship a false claim

`eval/evaluator.py` emitted a hard-coded paragraph for Malaysia naming four gold ids and a recall of
16/18 — true of the run that produced it and of nothing else. On the finale's 1,054-row gold set it
would have described nothing while sitting in an evidence file.

Underneath it were two real faults, both now fixed and measured:

- the law matcher divided shared tokens by the **shorter** name, so "Personal Data Protection Code
  of Practice For Banking Sector And Financial Institutions 2017" scored 1.0 against "Personal Data
  Protection Act 2010". Four Malaysian gold rows were resolved, and some counted as hits, against a
  law they do not cite. Dividing by the cited name's own tokens computes the correction the
  paragraph made by hand: Malaysia goes from 22 resolvable rows at 0.727 to 16 at 0.875;
- a gold row whose cited document is in the corpus with zero provisions could not have been mapped
  by anything, so the report now carries `cited_but_unparsed_sources` and a recall over the rows
  whose sources parsed — generated, and absent when there is nothing to say.

### Engines are named now

`RDTII_ENGINE=A|B` selects from `config/llm/engines.json`: A is the hosted Claude stack, B is
`qwen2.5:14b` pinned by digest `sha256:7cdf5a01…85b22f6`, read from the local Ollama 0.34.4 server.
With the variable unset nothing changes, so a run configured before tonight resolves as it did then.
The batch lane refuses an engine that does not declare it, the no-key refusal names the engine
route, and the manifest records engine id, label, open-weights flag and digest per entry.

Checklist item 9 wants the swap to happen "from inside the interface, with no code or config change"
— the interface now has one variable to set. Item 12, the pipeline running end to end on the
open-weights engine alone, is J5 and needs the GPU, which is busy until about 05:00.

### Two paid stages were invisible in the cost ledger

The economy-level rollup call and the Haiku triage pass recorded no cost. Both do now, and the
rollup builds one client per run instead of one per indicator — which is also what stops it hanging
when there is no key: it leaves 7.1 and 7.2 `pending` with the reason and still computes the seven
provision-level scores, which need no model at all.

## What is still open, in the order I would take it

1. **J5, the end-to-end run on engine B** — checklist item 12, needs the GPU free.
2. **H4, the no-provision Discovery Tag** — a judgement about how the host scores an absence, set
   out at the end of the template note. Not a patch to make unattended.
3. **H6, the notification rows** (M8/M9) — fixed sentences a marker reads, so the wording wants a
   second pair of eyes.
4. **J6, the empty dense stub in `main.py`** — still the highest-value code fix outstanding, and
   still the interface's own file.
5. **Block C, the instrument hand-off** — `HANDOFF.md` step 5 says to commit only when we agree.

### The one that would have cost every Chinese row

Found by measuring the grounding check against real corpus text rather than reasoning about it.
Round 1 decided whether a quote was real with a single comparison — whitespace collapsed,
lowercased, substring — and filed whatever the model returned. Against Chinese:

| What the model returns | Round 1's check |
| :---- | :---- |
| the exact substring | grounded |
| one space inserted mid-quote | **not grounded** — Chinese has no whitespace run to collapse |
| full-width `，` written as `,` | **not grounded** |
| ideographic `。` written as `.` | **not grounded** |
| the quote wrapped in curly quotation marks | **not grounded** |

On its own that was a lost row here and there. Combined with this afternoon's H5 gate — an
ungrounded row is no longer filed at all — it becomes a China run that files **nothing**, reports
`dropped: ungrounded_quote`, and exits zero.

Decision M10 already said what to do, so `mapping/anchor.py` does it: locate the model's quote
under progressively more forgiving comparisons, then file **the source's own substring for that
span**. The locator is forgiving; the evidence is not. Verified over the September corpus — 1,200
provisions in six languages, 14,400 anchorings across six perturbations:

- **0** cases where the filed text was not the source's own bytes;
- 6 (0.04%) where the span differed from the intended quote at all, every one of them by a single
  edge quotation mark in the ambiguous case where the source's own quote mark sits at the boundary;
- a paraphrase, a translation, and a quote from a different provision are all refused.

Both mapper lanes use it, so the live and batch paths file identical bytes, and the run report now
carries `quotes_recut_from_source` — a quoting-fidelity number per engine that Section 5 has no
other source for, and one I expect to differ between engine A and engine B.

### Block G's reuse path is already demonstrated

Its first step was "migrate the 142 filed rows to decimal through `normalize()`". Re-running the
emitter over the frozen arm does that and proves it in one pass, recorded at
`evidence/reuse/reemit_2026-09-27.md`: Singapore 42 of 42 and Malaysia 57 of 57 identical, Australia
42 of 43 with the one government-data-only row dropped and the one ungrounded row replaced, and the
thirteen Round 1 columns unchanged in order and content.

What remains of Block G is the part that needs the network or a paid call: the URL liveness re-run,
the currency check against the new crawl (already on the plan's cut line), and F2's 6.2 re-judge.

---

## The morning run, 04:30

The embedding leg finished: 767,105 rows in 212 minutes, and `reindex_after_dense.py` took the
index the rest of the way — S0 re-ingest (the row order unchanged, so the 1.5 GB of embeddings
stayed valid), the sparse leg rebuilt with decimal keys, the dense top-K recomputed in 16 seconds
from the cache, and S2.

**The dense leg sees China and Lao.** This was the check left open by the sparse-leg note. Top-50,000
rows per indicator, counted by economy, against each economy's share of the corpus:

| Economy | corpus share | dense top-K share | slots |
| :---- | ---: | ---: | ---: |
| CN | 6.5% | **10.9%** | 49,157 |
| SG | 14.4% | 21.0% | 94,476 |
| MY | 9.5% | 13.3% | 59,855 |
| AU | 39.4% | 47.3% | 212,760 |
| LA | 5.4% | 4.3% | 19,335 |
| TL | 24.7% | **3.2%** | 14,417 |

China is over-represented, which is what you would expect of a jurisdiction whose data law is dense
with exactly this subject matter, and Lao sits close to its share. Against **zero** slots in the
sparse leg for both, that settles it: the dense leg is the multilingual leg, and J6 — making the
live path run it — is the whole fix.

Timor-Leste is the thin one, 7.7 times under-represented. That is not blindness: the Jornal da
República publishes the entire statute book as gazette issues, so TL's 189,000 provisions are mostly
appointments, budgets and resolutions. A low share of a data-law top-K is the correct answer for
that corpus. Its cells still fill — 5,022 candidate pairs, none of them depth-limited.

### The gold gate, and three causes that looked like one number

S2's first run read **0.871 against a 0.95 target, 8 misses**. Diagnosing each separately mattered,
because only three were retrieval:

- **five were the gate resolving a gold row against the wrong documents** — a global name index that
  matched a Malaysian row against two Lao documents, token coverage divided by the shorter name, and
  documents counted even with zero provisions;
- **three were a law number read as part of the name.** The host writes "Law on Electronic Data
  Protection No.25/NA 2017"; the corpus carries "Law on Electronic Data Protection". Lao's central
  data-protection statute (55 provisions) and Malaysia's Criminal Procedure Code (986) looked absent
  for that reason alone;
- **three were real, and every one was above theta and outside the ceiling** — which is what the
  per-(economy, indicator) overrides exist for. SG 7.1 from 400 to 600 (the Banking Act row sits at
  in-economy rank 538, cosine 0.594 against theta 0.550); CN 7.5 from 1,800 to 3,800 (two rows at
  ranks 2,302 and 3,416, and all 3,747 of China's rows in that top-K are above theta, because
  government-access language is pervasive in Chinese law). Both are settings, so both can still move
  on 15 October.

**The gate now reads 53 of 53, no misses.** Candidates: 44,377 pairs, 7,396 per economy — CN 10,244,
AU 8,995, SG 8,104, MY 7,852, TL 5,022, LA 4,160. For block F's three economies that is 19,426
candidate pairs against the plan's estimate of 23,600, so F1's $162 is conservative.

And the gate stopped hiding what it cannot reach: 33 gold rows cite **19 laws the corpus does not
hold**, thirteen of them Chinese departmental rules and technical specifications. Written up in
`2026-09-27-nineteen-laws-the-corpus-does-not-hold.md`, because it is a scraping request and the
cheapest three documents on that list are worth five gold rows between them.

### And then the gate's own measurement turned out to be the thing measured

53/53 lasted an hour. For China and Lao the gate could only compare **English** names, because the
normaliser drops every non-Latin character — so a Chinese `law_name` reduces to the empty string and
only `law_name_en` can match. Every Chinese and Lao document has one, and it is a *translation*: two
independent translations of one Chinese title rarely share 80% of their words.

So the gate had been reporting laws absent that were sitting in the corpus under their own name. The
host writes the original inside 《》 beside its English, which makes the character sequence itself the
reliable key. With original-script matching:

| | before | after |
| :---- | ---: | ---: |
| resolvable gold rows | 53 | **63** |
| laws the corpus genuinely lacks | 19 | **11** |
| recall | 1.0 | **0.9365 (59/63)** |

Recall went *down* because the denominator became honest. Six Chinese laws came back, including the
March 2024 cross-border flow rules, and Malaysia's Criminal Procedure Code with its 986 provisions.

`config/lawnames.py` now owns this question for the gate, the evaluator and NEW/KNOWN, with every
rule each of them had separately plus the two that were missing — digit-bearing tokens dropped
(a law number is an identifier), and a one-word name matched exactly rather than by containment, so
"Banking Act 1970" cannot be answered by "Islamic Banking Act".

The four remaining misses are all **below theta**, not outside a ceiling, so they are a threshold
question. The sweep, run on the real index:

| Chinese offset | CN pairs | all pairs | gold | recovered |
| ---: | ---: | ---: | ---: | :---- |
| −0.02 (measured) | 10,244 | 43,022 | 59/63 | — |
| **−0.03** | 10,919 | 43,697 | **60/63 = 0.952** | r2-cn-043 |
| −0.04 | 11,499 | 44,277 | 60/63 | same |
| −0.05, −0.06 | 11,647 | 44,425 | 60/63 | same |

One row for 675 candidate pairs, and the gate passes. Nothing recovers the other three at a
defensible threshold: CN 7.4's Cybersecurity Law row needs an offset near −0.055 **and** a higher
ceiling, and two rows sit below the index cut entirely. The measured offsets were explicitly lower
bounds ("the gloss is machine-made, which biases these toward zero"), so −0.03 is inside the
measurement rather than fitted to a row — but it is a setting, and the call is yours.

### One dead setting was load-bearing after all

`PREFILTER_TOPK` was 3 in settings, documented as dead, while both retrieval legs hard-coded 50,000.
Measured on this index, **the 50,000th cosine sits above theta for 7.3 and 7.5** — so for those two
indicators the index depth, not the threshold, decided the candidate set, and no tuning could reach
past it. Timor-Leste's 7.5 cell was one of the truncated ones.

It is now the index depth, default 150,000, where the cut falls below every theta (7.3 0.538 →
0.503, 7.5 0.572 → 0.527). Theta decides, which is the design. It costs 3.2% more candidate pairs
and 6 MB of arrays, the recompute takes 16 seconds from the cached embeddings, and being a setting
it can go deeper on 15 October without touching code.

Final state of the run: 45,813 candidate pairs (direct 4,231, gray 41,582), gold 59/63, both legs at
depth 150,000, ready for S3.
