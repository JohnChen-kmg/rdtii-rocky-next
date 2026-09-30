# Proposed experiments: which strategy, which models, which translation tool

Written 2026-09-24, overnight, for review in the morning. **This is a proposal, not a pre-registration.**
Once we agree the arms and the thresholds, it is copied into `evidence\` with a real timestamp and the
budget cap, and only then does anything spend money. That order is the thing Round 1 got right and the
thing the host marks.

## What these experiments have to answer

Four questions, in the order they bind us:

1. **What does Word Section 5 say?** Per engine: exact checkpoint, the cost of one run of two
   indicators, and known weaknesses on legal text. It cannot be corrected after 30 September, and only a
   real run produces the numbers.
2. **Which engine is Engine B?** At least one declared engine must be open weights and the pipeline must
   run end to end with no proprietary service.
3. **Where is the money cut?** At 61 indicators the naive bill is thousands of dollars. At pillars 6 and
   7 it is a few hundred. What the prefilter and triage keep is the whole cost story.
4. **Does any of it work in Lao, Chinese and Portuguese?** Three of the six economies, and 91,560
   provisions where the English keyword leg returns noise.

## Before anything runs: five blockers

None of these is optional, and one of them invalidates any model comparison run today.

| # | Blocker | Why it blocks | Hours |
| :---- | :---- | :---- | ----: |
| B1 | **Local context window is unset.** `config\llm\ollama_client.py:21` passes only `temperature` and `num_predict`. **Measured on this machine, not assumed** — see the probe below: the default context is **2,048 tokens**. Our codebook prefix alone is 31,915 characters, about 8,000 tokens, before the provision text | **Any open-weights mapping result measured today is measuring truncation, not the model.** Round 1 only ran the local lane on short triage prompts, so this never showed | 0.5 |
| B2 | Decimal-ID migration, W1 | The new instrument cannot be read at all until it lands, and the experiments should test the finale codebook, not Round 1's | 10 |
| B3 | Contract 0.3.0 vendored schema | The current schema rejects every record in the hand-off, Singapore's included | 0.5 |
| B4 | Price table and ledger, W2 and W6 | The prompt requires cost measured from a ledger rather than estimated. Without it, Section 5's cost line is an estimate and reads as one | 6 |
| B5 | The dense index over the new corpus | S1 must have run once before any retrieval arm can be compared. 766,526 rows, about 1.6 GB of embeddings. Round 1 managed 412,565 rows in about 1 h 53 m, so **budget 3 h 30 m**, resume-safe | 3.5 (unattended) |

### The B1 probe, run 2026-09-24

`qwen2.5:14b` on the local Ollama, one prompt of about 16,850 characters' worth of filler with a marker
planted at the very start (`SECRET_A`) and another at the very end (`SECRET_B`), then asked to state both.

| Options sent | Tokens the model actually read | Answer |
| :---- | ----: | :---- |
| As the client sends them today | **2,050** | "UNKNOWN, BRAVO9." |
| Plus `num_ctx: 16384` | **11,284** | "SECRET_A is ALPHA7, SECRET_B is BRAVO9." |

Two things are now measured rather than believed. The default context is **2,048 tokens**, half of what I
assumed. And **truncation drops the front of the prompt**, which is where the cached codebook sits: the
model kept the marker at the end and lost the one at the start. An open-weights mapper run through this
client today would be judging provisions with no codebook in front of it, and would look far worse than
the model is.

To repeat it: POST to `http://localhost:11434/api/generate` with a prompt longer than 2,048 tokens and
read `prompt_eval_count` in the reply, once with the options the client sends today and once with
`"num_ctx": 16384` added. It takes about 25 seconds.

## The fixed sample

One sample, drawn once with a recorded seed, used by every arm. Drawn across all six economies, so Lao
and Chinese behaviour show up instead of being averaged away by Australia's 302,243 provisions.

| Stratum | Size | Why |
| :---- | ----: | :---- |
| Gold rows, pillars 6 and 7, whose cited law is in our corpus | ~95 | The only rows where we know the host's answer. Available: CN 31, MY 26, SG 14, LA 13, AU 11, TL 0 |
| Declared trap cases | 40 | The 6.1-against-6.4 conditional pattern and the 7.3 minimum-against-maximum retention pattern. Round 1's canonical case, SG PDPA s.26(1), is one of them |
| Random draw from the direct band | 200 | Measures precision where we have no key: how much of what retrieval likes is actually evidence |
| Random draw from the gray band | 100 | The band triage screens. Needed to answer whether triage earns its place |
| **Lao repaired-citation rows** | 40 | 3.6% of Lao provisions had their article number reconstructed. We need their behaviour measured, not assumed |
| **Timor-Leste rows with `act_index` null** | 40 | 36% of Timorese provisions. Can the model still identify the act? |
| **Lao rows with a published English translation** | 30 | The 53 gazette-translated laws are the only place we can compare source-language judging against a human translation |

About 545 provisions, which at Round 1's rate is roughly $9 per hosted arm.

**Leave-one-economy-out is mandatory.** The instrument's 400 signature exemplars now include China's and
Lao's own host rows. An economy's own baseline rows inside its retrieval query is the leakage channel
Round 1 disclosed; on a sealed live test it would be worse. Every arm drops the exemplars whose
`exemplar_for` names the economy being judged.

## What gets measured

Reported **per language, never pooled**. An English error rate stamped on a Lao row is a false claim, and
the host's under-5% bar is not supported for Lao by anything extraction measured.

| Metric | How | Why it decides something |
| :---- | :---- | :---- |
| Agreement with gold | Indicator and score against the host's coded row | The closest thing to accuracy we have |
| **Grounding rate, before any fallback** | Is `verbatim_quote` an exact substring? | The gate every non-Sonnet model failed in Round 1: Haiku 43.4%, DeepSeek 48.4% and 71.7%, against 98% |
| **Schema validity** | Did the model return a parseable verdict with all fields? | Small models degrade here first, and a schema failure is a wasted call |
| Trap accuracy | The five trap booleans, on the 40 trap cases | The host's declared first error class |
| Retrieval recall | Gold row surfaced in direct or gray | Round 1's gate was 1.0; below 0.95 the arm is out |
| **Cost per 1,000 candidate pairs** | From the ledger, never arithmetic | Section 5, and the secretariat verifies against code |
| Wall clock | Per provision, and per run | Live-test feasibility inside the hour |
| Failure mode, in words | Read 20 disagreements per arm by hand | Section 5 asks for known weaknesses on legal text |

## The arms

### E1 — Retrieval, and whether it works outside English. Run first

It sets which provisions every later arm sees, so nothing else can start before it.

| Arm | What |
| :---- | :---- |
| A | BM25 alone, as today: English stemmer, English stopwords |
| B | Dense alone, BGE-M3 |
| C | Both, RRF as today |
| D | Both, with **per-economy tokenization**: Portuguese stemmer for Timor-Leste, character n-grams for Chinese and Lao |
| E | Both, with the indicator query **glossed into the source language** by a local model |

Measured per economy. My expectation, to be falsified: A collapses for China and Lao, B carries them, D
beats B in Chinese, and E helps Lao most because OCR noise hurts embeddings less than it hurts terms.

**Decision rule.** Adopt the cheapest arm that keeps gold recall at or above 0.95 in every economy
separately. If no arm reaches it for Lao, say so in Section 4 rather than quietly reporting the average.

### E2 — Does triage earn its place?

| Arm | What |
| :---- | :---- |
| A | Today: gray band screened by Haiku, about 20% kept |
| B | No triage: the whole gray band goes to the mapper |
| C | No gray band at all: direct band only, caps raised |
| D | Triage by a local model at $0 |

The mapper's prefix is cached, so the marginal cost of one more provision is smaller than it looks, which
is what makes B plausible. **Decision rule.** Drop triage if B or C changes the verified-fire set by under
2% and costs less than A.

### E3 — The prompt

| Arm | What | Measured size |
| :---- | :---- | ----: |
| A | One prefix, all nine automated blocks | 31,915 chars, ~8.0k tokens |
| B | One prefix per pillar, two calls where a provision's candidates span both | 19,828 and 20,888 chars |
| C | One prefix, all 61 blocks, only relevant if scope widens | 122,667 chars, ~30.7k tokens |

A correction worth noting: the two pillar prefixes each contain 8,801 characters of shared header and
policy, so they cannot be added. A is 1.23× Round 1's 25,974, not level with it.

### E4 — The mapper model. The one Section 5 is written from

Same sample, same prompt, same schema, temperature 0. Candidates in the next section.

### E5 — Verification

| Arm | What |
| :---- | :---- |
| A | Today: blind second model, third as tiebreak, two of three decides |
| B | One stronger judge, no panel |
| C | Same model twice at temperature 0, as a determinism control |
| D | A local model as the blind verifier, for the Engine B lane |

Round 1's panel overturned about a third of all fires. **Decision rule.** Keep the panel unless B matches
its overturn precision on the gold sample at lower cost. Whatever wins, Engine B needs a verifier that is
also open weights, or the Section 3 checkbox cannot be ticked.

### E6 — Judge in the source language, or on a gloss?

For Lao, Chinese and Portuguese only.

| Arm | What the model sees |
| :---- | :---- |
| A | Source language only |
| B | Source plus an English gloss of the same provision |
| C | Gloss only |

**The snippet that reaches the workbook is always the source text**, whatever wins. A gloss is a reading
aid, never evidence. The 30 Lao laws with publisher English are the only place we can check a gloss
against a human translation rather than against another machine.

### E7 — Grounding mode, cheap and decisive

| Arm | What |
| :---- | :---- |
| A | Today: the model writes the quote, code checks it afterwards |
| B | Fallback: an ungrounded quote is replaced by the provision's own snippet, flagged, confidence lowered |
| C | The model returns sentence indices and code cuts the quote |

B and C make C2b independent of the engine, which is what makes an open-weights Engine B possible at all.
C is the better design and the larger change. This is code, so it is now or never.

## Candidate models

### Local, open weights — the Engine B pool

The machine is an RTX 4070 Ti SUPER, **16 GB**. With a 16k context the practical ceiling is a 14B model at
4-bit: roughly 9 GB of weights plus 2 to 3 GB of KV cache. A 24B at 4-bit leaves no room for the context
we need, which matters because our prefix is 8k tokens before the provision.

| Model | Size | Already local | Why it is a candidate | Risk |
| :---- | ----: | :---- | :---- | :---- |
| **qwen2.5:14b** | 9.0 GB | yes | Strong Chinese, the Round 1 local lane, already evidenced at about 1 provision/s | Round 1 measured it missing 16% of what Haiku kept, on triage |
| **gemma3:12b** | 8.1 GB | yes | Best measured Lao gloss of the three tested, chrF 0.658. Already trusted by extraction | Weaker at long structured output |
| **qwen3:14b** | ~9 GB | pull | Newer generation of the strongest multilingual open family | Thinking-mode output can fight a strict schema; test both modes |
| **sailor2:8b** | ~5 GB | 1b variant local | **Purpose-built for South-East Asian languages, Lao included.** The only candidate specifically trained where our worst corpus sits | Small, and untested for structured legal judgement |
| **llama3.1:8b** | 4.9 GB | yes | Baseline. Round 1 reproducibility control | Weakest multilingual of the set |
| **phi4:14b** | ~9 GB | pull | Strong reasoning per parameter | Mostly English-trained |
| **mistral-small:24b** | ~14 GB | pull | Best instruction following of the group | Will not fit beside a 16k context; include only if the others fail |

Pin whatever wins **by digest, not by tag**, because Section 5 asks for an exact checkpoint and a floating
alias is not an answer.

### Hosted — Engine A, and the reference arm

| Model | Role | Why |
| :---- | :---- | :---- |
| **claude-sonnet-5** | Engine A mapper | Round 1's mapper. It is the reference every other arm is compared against, so it must be in the sample even though it is not on trial |
| **claude-haiku-4-5** | Cheap mapper, verifier | Round 1's verifier. As a mapper it grounded 43.4%, which E7's fallback may change. Worth re-measuring |
| **claude-opus-5** | Tiebreak | Round 1 used Opus for the third vote |
| A hosted open-weights endpoint | Only if Engine B goes hosted | Needs the OpenAI-compatible client, W10, about 2 hours. Round 1's DeepSeek attempt failed four gates of four and the report was kept, which is the precedent for how to report a failure |

## Translation and gloss tools

Only for query glosses in E1 and reading aids in E6. **Nothing here ever produces a `verbatim_snippet`.**

| Tool | Licence | Evidence we have | Note |
| :---- | :---- | :---- | :---- |
| **gemma3:12b** | Gemma terms | **chrF 0.658** against publisher English on Lao, the best measured | Extraction's own choice. Already installed |
| **qwen2.5:14b** | Apache 2.0 | chrF 0.561 on Lao; agrees with gemma3 at 0.836 on Chinese | Clean licence, useful for the repo's compliance table |
| **llama3.1:8b** | Llama licence | chrF 0.338 on Lao | Included as the floor |
| **sailor2:8b** | Apache 2.0 | none yet | The candidate most likely to beat gemma3 on Lao |
| **NLLB-200 distilled** | **CC-BY-NC** | none | **Non-commercial. It would break the licence table in Word Section 3.** Recommend excluding it outright rather than testing something we cannot ship |
| Helsinki opus-mt | CC-BY / MIT | none | Thin Lao coverage; cheap to test for Portuguese |
| **The gazette's own English** | public document | 53 Lao laws, 1,513 pages, on disk | Not a tool: the reference everything else is scored against, and the gloss to prefer where it exists |

## Budget, and the order of spending

| Stage | Hosted spend | Wall clock |
| :---- | ----: | :---- |
| E1 retrieval | $0 | 2 h, mostly the index build |
| E2 triage | ~$4 | 1 h |
| E3 prompt | ~$6 | 1 h |
| E4 mapper models, 3 hosted arms | ~$27 | 2 h hosted, 4 to 6 h local |
| E5 verification | ~$8 | 1 h |
| E6 language | ~$5 | 2 h |
| E7 grounding | $0, re-scores E4 output | 0.5 h |
| **Total** | **about $50** | **12 to 15 h** |

**Proposed hard cap: $60**, enforced by the budget guard, with the run refusing to start if the dry-run
projection exceeds it. Round 1 spent $281.59 on production mapping, so $50 to choose the strategy is
proportionate.

## What I propose we agree in the morning

1. **The two decisions that change the arms**: whether Engine B is local or hosted (D-1), and whether the
   Round 1 economies are re-mapped or reused (D-2). If reuse wins, the sample's AU, SG and MY strata
   shrink and the experiments concentrate on China, Lao and Timor-Leste.
2. **B1 first, today.** The context-window fix is half an hour and every local number depends on it.
3. **Cut E3 and E5 if the week tightens.** E1, E4 and E7 are the ones Section 5 and C2b need. E2 is the
   cost lever. E3's answer is already implied by M7, and E5 can stay as Round 1 ran it.

## What would make me wrong

- If dense retrieval turns out to carry Lao well, E1's per-economy tokenization is wasted work, and the
  honest thing is to drop it rather than ship it because it was planned.
- If every local candidate fails schema validity even with the context fixed, Engine B becomes a hosted
  open-weights endpoint and W10 moves from optional to required. That decision belongs to the morning
  after E4, not before it.
- If gold agreement is low for every arm in Lao, the finding is about the OCR text, not the models, and
  it belongs in Section 4's readiness table as an honest gap rather than in Section 5 as a model
  weakness.
