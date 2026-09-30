# Starting prompt — mapping stage, written 2026-09-24

Paste the block below into a fresh session opened in `C:\Users\woshi\Desktop\rdtii-finale-3-mapping`.
Written for an agent that has not seen this project. Every figure in it is checkable in the files it
names.

---

You are starting stage 3 of the RDTII finale build: **mapping**. Extraction froze on 24 September and
handed over 766,526 grounded provisions across six economies. Your job is to decide which RDTII
indicator each provision evidences, roll that up to an economy score, and produce the evidence rows
the submission is marked on.

Your workshop is `C:\Users\woshi\Desktop\rdtii-finale-3-mapping`. The stage code is
`stages\p3-map\` in the repository at `C:\Users\woshi\Desktop\rdtii-rocky-finale`. The extraction and
collection workshops are **read-only to you**.

We will work in three phases, in this order, and I want to talk through each before you build:

1. **Understand the workflow and design.** Read the eleven-step Round 1 mechanism, confirm what the
   input actually is, and propose what changes for the finale.
2. **Experiment.** Compare mapping strategies and AI models on a fixed sample, with a pre-registered
   protocol and measured cost.
3. **Map for real.** Production runs, the workbook rows, and the two-engine comparison.

**Do not start phase 2 until we have agreed the design, and do not start phase 3 until the experiments
have answered which strategy and which models.**

## Read these first, in this order

| File | Why |
| :---- | :---- |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\finale_progress\STAGE_RESULT_p2-extract_2026-09-24.md` | **What you are actually being given.** Newer than every plan in this workshop. Where it disagrees, it wins |
| `C:\Users\woshi\Desktop\rdtii-finale-2-extraction\TOOLS_BY_ECONOMY.md` | How the text was read, per economy, and how good it is. This is the section below that matters most |
| `PRELIMINARY_PLAN_2026-09-22.md` | The task in one page, the critical path, work packages W1 to W14, seven open decisions, and the host's live-test sheets read cell by cell |
| `reference\round1\mechanism\MAPPING_MECHANISM.md` | The eleven steps S0 to S10 as Round 1 ran them |
| `notes\INSTRUMENT_IMPACT_2026-09-22.md` | Every place the new 61-indicator instrument breaks the current code, with file and line |
| `DECISIONS.md` | M1 to M9. M2, M5, M8 and M9 bind your design |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\AUTHORITATIVE_NUMBERS.md` | Round 1's measured cost and scale. Quote from here, never from memory |

Do not re-derive what those establish. Cite them and move on.

## The input, which is the thing to get right

Hand-off #2 is `C:\Users\woshi\Desktop\rdtii-finale-handoff2\`, 5.9 GB.

| Economy | Provisions | Law rows | Language | How the text was read |
| :---- | ----: | ----: | :---- | :---- |
| Australia | 302,243 | 1,277 | eng | HTML and native PDF |
| Timor-Leste | 189,557 | 2,879 | por | native PDF, 2,730 by OCR |
| Singapore | 110,661 | 738 | eng | native PDF |
| Malaysia | 72,505 | 1,389 | eng, 146 msa | native PDF, 211 by OCR |
| China | 50,026 | 1,085 | zho | docx and HTML, no scans |
| Lao PDR | 41,534 | 1,762 | lao | **41,362 of 41,534 by OCR** |

**Four traps will cost you a day each if you meet them by surprise.**

1. **`HANDOFF2_DIR` must be set to that folder.** It defaults to `..\handoff2`, which still holds
   **Round 1's July output**: 411,986 provisions over three economies. A run that forgets it reads the
   old data and looks like it worked. Make the run fail loudly instead, or assert the provision count
   at start-up.
2. **`laws.jsonl` is one row per ACT, not per document.** Timor-Leste has 2,879 law rows over 1,921
   documents, because a gazette issue carries several separate acts, each with its own Article 6.
   Anything that keys `laws.jsonl` on `doc_id` silently keeps only the last act of each issue.
3. **The contract bump to 0.3.0 is not optional.** The vendored schema in `stages\p3-map\` had
   `economy` as an enum of three, a `doc_id` pattern of `^(sg|au|my)-`, and `additionalProperties:
   false` against 27 new fields. Before the bump it rejects **every** record extraction emits,
   Singapore's included. The branch `p2-extract-contract-0.3.0` carries the corrected copy into this
   stage as well, byte-identical.
4. **Nothing is tagged.** `scope`, `data_type` and `obligation_type` are null on all 766,526 records,
   with `tags_source: not_tagged`. Extraction demoted them because mapping has no consumer for them.
   If your code reads them, that assumption is now wrong.

## What the OCR actually gives you, and what it does not

This is the critical point for this stage. **The grounding guarantee is narrower than it looks.**

Every `verbatim_snippet` is a character-exact substring of `source_text\<doc_id>.txt` at the recorded
offsets. That was re-checked by re-reading the frozen text from disk: 18,000 records sampled, zero
mismatches. So a quote is provably a piece of **the text we stored**.

It is not a guarantee that the stored text matches the page. For Lao PDR, where 99.6% of provisions
come from OCR, the measured figures are:

| | Lao PDR | Timor-Leste scans | Malaysia scan |
| :---- | :---- | :---- | :---- |
| Character agreement | about **94%** | — | CER **0.0047** against a hand-keyed page |
| Title recovery | 0.891 | 0.866 | — |
| Article-number sequence agreement | **0.856** | 0.906 | — |

**Read the third row carefully. Roughly one Lao article number in seven was misread and repaired from
its position in the document.** Extraction did not hide this: every repaired record carries
`article_number_as_read`, what the page actually printed, and `citation_confidence`.

| Economy | exact citations | text trusted | **repaired from position** |
| :---- | ----: | ----: | ----: |
| Timor-Leste | 180,297 | 4,591 | **4,669, or 2.5%** |
| Lao PDR | 39,836 | 213 | **1,485, or 3.6%** |
| China | 50,006 | 4 | 16, or 0.03% |
| SG, AU, MY | all | — | — |

**A real act cited to the wrong article scores zero under criterion C2b.** So three things follow, and
I want your design to say how it handles each.

- **Read `citation_confidence` and carry it forward.** A row built on a repaired citation should be
  visible to the reviewer, and probably should not be filed at all in the 101-row workbook when an
  exact-citation row would do instead.
- **The Lao rubric claim has a ceiling.** Extraction states it cannot claim the under-5% error rate
  for Lao, because no Lao page has a hand-keyed reference. Do not let a corpus-wide accuracy number
  from an English fixture get stamped on a Lao row.
- **About 6% of Lao characters are wrong.** That is the text your retrieval will search and your model
  will judge. Expect keyword retrieval to behave worse in Lao than the English economies, and design
  the experiment in phase 2 to measure that rather than assume it.

Two more fields exist because of this, and they are useful to you. `law_name_en` is **100% filled**
across all six economies, with `law_name_en_source` saying whether the English title is the source's
own or machine-rendered. That is what you match against the host's 2025 baseline, where Lao and
Chinese laws are listed in English. And `act_index` with `act_count` handle the Timorese multi-act
issues, with `act_index` deliberately null on about 36% of Timorese provisions rather than guessed.

## What this stage is marked on

Directly C2a 10, C2b 10, C4b 7 and C5 10, which is 37 points. Indirectly the rows you write are the
evidence for C1a, C1b and C1c, worth 40 more.

| Date | Deliverable |
| :---- | :---- |
| 30 Sep | The evidence workbook: 14 columns, **at most 101 rows**, decimal-text indicator IDs, a verbatim snippet, a rationale of at most 300 characters, a confidence, and the Language of Source column |
| 30 Sep | Word Section 5, the engine declaration. **Cannot be corrected after the deadline.** Per engine: the exact checkpoint, the cost of one run of two indicators, and known weaknesses on legal text. Only real runs produce these |
| 30 Sep | Code freeze. Settings may change afterwards; code may not |
| 15 Oct | Live test: one economy of nine, one pillar, two indicators. Engine A fetches, Engine B re-reads the same documents and fetches nothing. A comparison file whose found-by strings are exactly `Engine A only`, `Engine B only` or `Both` |

## Phase 1, the workflow and the design

Round 1 ran eleven steps: free retrieval by BM25 and dense embeddings where the indicator is the
query, a cheap lenient triage, a schema-forced verdict from the strong model against a cached
codebook prefix, blind re-judging by a second model with a third as tiebreak, then deterministic
rollup, NEW against KNOWN, emit and evaluate.

Three things changed, and the design has to absorb them.

- **Nine indicators became 61**, with decimal-text IDs such as `6.1`, `4.01` and `12.4.1`. Never
  float-parse them: `12.10` is not `12.1`. The instrument is built and waiting, and **it cannot be
  handed over until this stage accepts decimal IDs.** That migration is the gate, and the file list is
  in `notes\INSTRUMENT_IMPACT_2026-09-22.md`.
- **Three economies became six, three of them non-English.** Retrieval that leans on English keywords
  will not find a Lao or Chinese provision.
- **411,986 provisions became 766,526.** Round 1's mapping and verification cost US$281.59 for three
  economies and nine indicators. Naive scaling to six economies and 61 indicators is an order of
  magnitude more than anyone will spend, so **what the prefilter and triage cut is now the central
  design question, not an optimisation.**

Before building, tell me: what the candidate-pair count looks like per economy under the current
prefilter, where you think it should be cut, and what you would change in S1 to S5 for a non-English
corpus.

## Phase 2, the experiments

I want strategies and models compared properly, not chosen by argument.

**Pre-register before spending.** Write down the sample, the metric, the decision rule and the budget
cap in a dated file in `evidence\`, then run. Round 1 did this for its DeepSeek comparison and the
report is in `reference\round1\ab\`; copy that shape. A result that was not pre-registered is worth
much less to the submission than one that was.

**Compare on the same fixed sample**, drawn across all six economies so that Lao and Chinese behaviour
show up rather than being averaged away by Australia's volume.

Strategies worth testing, at least:

- Retrieval: BM25 alone, dense alone, both, and what each misses in Lao and Chinese.
- The triage step: keep it, or let the strong model see more candidates and skip it.
- The prompt: one codebook prefix of all automated blocks against one prefix per pillar. Measured, the
  pillar 6 and pillar 7 prefixes are 19,842 and 20,902 characters, so a single prefix of both stays
  near Round 1's 25,974 and keeps the cache economics.
- Verification: the blind two-of-three panel against a single stronger judge.
- Whether judging in the source language beats judging a translated gloss.

Models: at least one strong hosted model and at least one open-weights model that can run locally,
because **at least one declared engine must be open weights and the pipeline must run end to end with
no proprietary service.** Round 1 measured about one provision per second locally at zero dollars, and
citations and offsets byte-identical across three models, which tells you the deterministic parts do
not depend on the model and only the judgement does.

Report per engine: agreement against the gold set, cost per thousand candidate pairs measured from a
ledger rather than estimated, wall-clock, and the failure mode on legal text. Those numbers are what
Word Section 5 needs, and Section 5 cannot be fixed after the deadline.

## Phase 3, production

Only after the design and the experiments are settled. Full runs per economy into their own output
directory, the unified cost ledger, the NEW-against-KNOWN tagging, the 101-row selection, the
notification rows for indicators the tool does not automate, and the two-engine comparison export.

Two rules from the issue record bind the comparison. **Match the Discovery Tag on instrument name and
section, never on URL**: in four economies the host's own baseline barely cites the main law database
at all, not once in Malaysia, so a URL join scores it at zero and measures the wrong thing. And a null
for a source nobody looked at means "not looked for", which is a different statement from "no
provision found".

## Hard rules

- **Grounding survives this stage.** A quote that reaches the workbook is still a character-exact
  substring of the frozen text. If a model paraphrases, the row does not ship.
- **One run means one output directory with a run manifest** (M2). Round 1's runner resumes from
  existing verdicts, so two engines writing into one tree will silently skip work and the engine swap
  becomes unprovable. Four marks depend on that manifest.
- **Model choice fails before spending, not after** (M5). Refuse to build a paid client for a model
  with no price entry.
- **Every indicator the tool does not automate gets the fixed notification row** (M8, M9), driven by
  the instrument's coverage mark.
- **Cost comes from a ledger, per run and per engine, with no manual arithmetic.** The secretariat
  verifies cost claims against the code, and Round 1 had three unevidenced components that will read
  worse when cost is also recorded live on 15 October.

## Settle these before phase 3

`PRELIMINARY_PLAN_2026-09-22.md` section 8 holds seven decisions with a recommendation each. The four
that change the most work: whether Engine B is local or hosted; whether the Round 1 economies are
re-mapped on the new corpora or their verified rows are reused; whether the Round 1 pillar 6.2 rows
survive the stricter trap wording; and the rule for choosing 101 rows when Round 1 alone filed 142.

Put them to me with your recommendation and what it costs if the answer goes the other way. Do not
stall on the ones that do not block. State your assumption, write it down, and carry on.

## What not to do

- Do not change anything in the extraction or collection workshops. Findings go back as notes.
- Do not choose a source, a seed or a target by reading the host's 2025 database. Cross-checks are
  disclosed as cross-checks.
- Do not let a translated string become a `verbatim_snippet`. The original is the evidence.
- Do not report a pooled accuracy figure across scripts. An English error rate on a Lao row is a false
  claim, and the Lao numbers above do not support the rubric's under-5% bar.
- Do not spend on a full run before the experiments have set the strategy.

Work in the walkthrough style this project uses: before an edit, name the files, show the current
control flow in ten lines or fewer, state the change in plain words, and say what you will check
afterwards. After it, append three lines to the changelog saying what, why, and how it was verified.

Start with phase 1. Read the files listed above, then come back and tell me three things: what the
extraction hand-off gives you that the 22 September plan did not expect, what you think the candidate
pair count and cost look like at 61 indicators, and what you propose to change in the eleven steps
before we run anything.
