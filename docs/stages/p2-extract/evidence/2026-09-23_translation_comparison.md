# Translation candidates compared, 2026-09-23

Measured because the live test says the tool "reads and **translates**", and no workshop owns
translation. This is the comparison and the recommendation the developer asked for. **Nothing here
is built into the pipeline**, and D5 stands: the verbatim snippet is always the source language.

Script: `experiments\translation_bench.py`. Raw output: `experiments\results\translation_bench.json`.

## The reference, and why this project has one at all

The Lao Official Gazette publishes its **own English translation** of some laws beside the Lao
original. Collection retrieved **53 of them, 1,513 pages**. They are in the run folder
`LA_ws_2026-09-21`, not in the corpus, because `merge_corpus.identity()` ignores language and
superseded each English file with its Lao twin.

That makes them the only reference translation this project has, and it was made by the publisher
rather than by us. Two laws were used, both digital-trade adjacent, both Lao-side scans:

| Law | Lao | English | Articles aligned |
| :---- | :---- | :---- | ----: |
| Law on Commercial Banks (amended) | `la-la2130-001`, 41pp scan | `la-la2130en-001`, 38pp | **113** |
| Decree on duty-free zones and duty-free shops | `la-la2076-001`, 35pp scan | `la-la2076en-001`, 36pp | **80** |

Alignment is by article number on both sides: 113 Lao articles found against 114 in the English.
That is a second, independent confirmation that OCR plus article segmentation works on Lao.

**The "translation only" condition could not be run.** Every Lao law with an official English twin
is a scan on the Lao side. All three exceptions have a native text layer that is legacy-font
mojibake with zero Lao characters. So every figure below measures the **production path**, OCR
included — which is the path that would actually ship.

## Result

Twelve articles per model, cross-judged (each model judged the other's output, never its own).

| Model | Licence | chrF vs the publisher's English | Share of the ceiling | Modality preserved | s/article |
| :---- | :---- | ----: | ----: | :---- | ----: |
| **gemma3:12b** | Gemma terms | **0.658** | **82%** | 9/12 | 5.5 |
| qwen2.5:14b | Apache-2.0 | 0.561 | 70% | 11/12 | 5.7 |
| llama3.1:8b | Llama 3.1 Community | 0.338 | 42% | 10/12 | 8.3 |

All three run locally on the existing Ollama service at zero cost. The model-as-judge column was
dropped from this table as unreliable: in one case it claimed a gloss "changes the focus to natural
resources" when it plainly did not. The readings below are mine, from the text.

### What the raw score means: the ceiling is 0.807, not 1.0

chrF against a *published* translation cannot reach 1.0, because a correct translation phrased
differently still scores below it. Measured: asking a model to re-word the **publisher's own
English**, with no Lao involved at all, scores **chrF 0.807** against the publisher's text
(`experiments\translation_diagnose.py`, section A, 5 articles: 0.758 to 0.872).

So 0.807 is what "correct, differently worded" looks like, and the share-of-ceiling column above is
the honest reading of each model. gemma3 reaches 82% of it; qwen2.5 reaches 70%.

### How much of the weakness is OCR rather than the model

Substantial, and it is measurable without any English reference. Take a Lao document whose text
layer is real Unicode, gloss the same article twice — once from the text layer, once from OCR of the
same page rendered to an image — and compare the two English outputs with each other:

| Document | Lao source agreement, text layer vs OCR | Resulting English glosses agree |
| :---- | ----: | ----: |
| `la-la1595-001` | 0.788 | **0.559** |
| `la-la1749-001` | 0.750 | **0.559** |

**The OCR-induced variance in the English output is as large as the entire measured gap to the
publisher's text.** Changing the model and improving the OCR are worth about the same, and they
compound: a better gloss of a misread page is still a gloss of a misread page.

## What the gloss actually does, read rather than scored

Decree on duty-free zones, article 4 — chrF 0.66, the best score in the set:

| | Text |
| :---- | :---- |
| **Publisher** | "State Policies for DFZs and Duty-Free Shops. The State encourages and promotes domestic and foreign investment in DFZs and Duty-Free Shops by providing Policies or Privileges in accordance with…" |
| **qwen2.5:14b** | "POLICY ON FREE ZONE AND FREE MARKET WORK. The State encourages both domestic and foreign investors to invest in free zones and free markets by providing incentives or profit benefits according to the…" |

Article 7:

| | Text |
| :---- | :---- |
| **Publisher** | "International Cooperation. The State promotes foreign, regional, and international cooperation through the exchange of lessons learned, data and information, science, techniques, technologies…" |
| **qwen2.5:14b** | "INTERNATIONAL COOPERATION. The State **shall** promote international cooperation with foreign countries, regions, and international organizations through the exchange of **educational programs**, information…" |

The same two articles, with **gemma3:12b**:

| | Text |
| :---- | :---- |
| **Publisher, art. 4** | "…by providing Policies or Privileges in accordance with **the Law on Customs**, the Law on Tax Management, the Law on Investment Promotion…" |
| **gemma3:12b** | "…by providing policies or benefits according to **the Tax Code**, the Law on Tax Administration, the Law on Investment Promotion…" |
| **Publisher, art. 7** | "The State promotes foreign, regional, and international cooperation through the exchange of **lessons learned**, data and information…" |
| **gemma3:12b** | "The State promotes cooperation with foreign countries, regionally and internationally through the exchange of **lessons learned**, information, science, technology…" |

gemma3 fixes both failures that qwen made: "lessons learned" is correct where qwen wrote "educational
programs", "duty-free zones" is recognisable where qwen wrote "free markets", and "promotes" stays
soft instead of hardening into "shall promote".

**It still makes a legally significant error.** In article 4 it renders the cited **Law on Customs**
as "the Tax Code" — it names the wrong instrument. A mapper following that citation would look up a
law the provision does not mention.

**The substance survives. The terminology does not.** In every sample the subject, the actor and the
broad obligation come through — an analyst would know what the article is about. But:

- **Domain terms drift**, badly in qwen ("ປອດພາສີ", duty-free, becomes "free", so a reader would not
  know the article is about customs at all) and mildly in gemma3 ("tax-free" for "duty-free").
- **A cited statute can be renamed.** gemma3 turned "the Law on Customs" into "the Tax Code".
- **Modality hardens.** qwen turned "promotes" into "shall promote": a policy statement reads as a
  binding obligation. gemma3 kept it, but lost the modality test on 3 of 12 articles.

The last one is the disqualifying failure. Pillars 6 and 7 turn on exactly this distinction — "must
not transfer **unless**" is indicator 6.4 while "must not transfer" is 6.1, and a prescribed period
with no number does not count for 7.3. A gloss that strengthens or softens modality will move a
provision between indicators, and it will do it fluently enough that nobody notices.

## Chinese, Portuguese and Malay — a different problem entirely

No corpus outside Lao PDR carries a published English translation, so there is nothing to score
against. Two things were measured instead, and a third was available that Lao did not allow:
**Chinese, Portuguese and Malay can be read and checked directly.**

Inter-model agreement — the same article glossed by `gemma3:12b` and `qwen2.5:14b`, the two outputs
compared with each other. It does not prove correctness, but Lao anchors the scale:

| Script | Economy | Agreement | Numbers preserved | s/article |
| :---- | :---- | ----: | :---- | ----: |
| Portuguese | Timor-Leste | **0.846** | 2/3 | 10.5 |
| Chinese | China | **0.836** | 3/3 | 9.5 |
| Malay | Malaysia | 0.733 | 3/3 | 11.5 |
| **Lao** | Lao PDR | **0.591** | 3/3 | 9.7 |

Chinese and Portuguese sit a full quarter above Lao. Both are high-resource pairs, both models
support them officially, and neither goes through OCR: China's corpus has no scans at all and
Timor-Leste's is 98% native text. Read by hand, the Chinese gloss of the Cybersecurity Law is
legally precise — 应当 and 不得 come through correctly as "must" and "must not", and "expressly
inform users and obtain consent" is right.

**So translation is a Lao problem, not a general one.** For China and Timor-Leste a gloss would be
a convenience; for Malaysia it is not needed at all.

### Malaysia: skip it

The corpus is English — `eng` on 1,244 of the law tracker's rows against `msa` on 2. Malaysia's
AGC publishes an English version of these acts, so there is no translation task.

**One correction to "all of them have an English version": we do not hold English for seven of
them.** Those seven carry the `language_mismatch` flag — the English link served the Malay file —
and no act in the corpus has a second copy in the other language. They include **Act 680, the
Electronic Government Activities Act 2007**, which is in scope for a digital-trade index.

The fix is not a translation tool. It is, in order of preference: mark those seven
`language_of_source: msa` from the crawler's own flag, and ask collection whether the English text
can be re-fetched from AGC. Either way nothing is translated and nothing is guessed.

### What the Portuguese test found instead, and it is worse than a translation problem

The Timorese article chosen for the test was `tl-ldcn-001`, "Artigo 6.º" of a document the law
tracker names **Lei da Concorrência**. The gloss came back about fuel smuggling, so the document
was opened. It is one gazette issue holding **two acts**:

| Act | Its Article 6 |
| :---- | :---- |
| **Lei N.º 1/2026, Lei da Concorrência** | "Práticas restritivas horizontais" |
| **Decreto-Lei N.º 13/2026**, temporary fuel-price stabilisation | "Fiscalização e prevenção de desvio de combustíveis" |

Both acts have an Article 6, in one PDF, under one `doc_id`. The naive path took the second and
would have published it as **Lei da Concorrência, Article 6** — a real provision cited to the wrong
statute, which is the failure the host scores zero.

This was found by accident while testing translation, on the first multi-act Timorese document
picked at random. It is the direct evidence for `act_index` in `OUTPUT_FORMAT.md` and for W7 in the
plan, and it is the reason W7's honest fallback — extract single-act issues only — matters even if
the splitting itself is cut.

## The question that actually matters: can a model JUDGE in Lao?

Stage 3 does not translate. It reads a provision and decides whether it satisfies an indicator. So
the deciding question is not translation quality but **whether the model reaches the same verdict
reading the Lao as it reaches reading the English**.

That is testable with no human annotation, because the gazette published its own English of these
laws. For eight aligned articles of the duty-free decree, each model answered the same five factual
legal questions twice — once over the OCR'd Lao, once over the publisher's English — and the answers
were compared (`experiments\judge_in_language.py`).

| Model | Verdict agreement, Lao against the official English |
| :---- | ----: |
| **gemma3:12b** | **90%** (36 of 40) |
| qwen2.5:14b | 85% (34 of 40) |

Per question, gemma3: obligation 8/8, penalty 8/8, state approval 7/8, time period 7/8, cross-border
6/8.

**Judging is easier than translating, and by a wide margin.** gemma3 scores 0.658 on translation and
0.90 on reaching the same legal conclusion. A model can tell that a provision imposes a duty, or
sets a deadline, without being able to render it into fluent legal English. That is the capability
stage 3 needs.

**Two limits, stated so the number is not over-read:**

1. **It is self-consistency, not accuracy.** Each model is compared against *itself* reading
   English, so 90% means gemma3's Lao reading agrees with gemma3's English reading. Both could be
   wrong the same way.
2. **The models disagreed with each other on the English side**, which means the reference verdicts
   are model-dependent. qwen2.5 read the English of article 2 as imposing no obligation where
   gemma3 read one. That is a difference in legal reading, not in Lao.

**What it changes:** a full English gloss of the candidate set is **not** required for stage 3 to
work on Lao. It is an accuracy aid worth 5 to 13 hours, not a precondition. That materially lowers
the cost of running the open-weights lane on Lao PDR.

## Recommendation

1. **Extraction translates nothing.** D5 stands. The verbatim snippet stays in the source language,
   at the recorded offsets, and remains the evidence.
2. **Where the publisher's own English exists, use that, not a model.** 53 Lao laws have an official
   English translation already on disk. It is a better artefact than any gloss in this table, it is
   attributable to the publisher, and it costs nothing. **Ask collection to re-merge the Lao corpus
   with a language-aware `identity()`** so those 53 files are addressable; they are currently
   dropped by a known defect that collection has already logged.
3. **Where it does not exist, a gloss is a reading aid and is labelled one.** If mapping or the
   dashboard wants one, the candidate is **`gemma3:12b`**, not `qwen2.5:14b`: 0.658 against 0.561,
   at the same speed, and it fixes the terminology and modality failures qwen made on the articles
   read by hand. Gemma 3 lists Lao among its supported languages; Qwen 2.5 does not list it at all,
   which is the likeliest explanation for the gap. The gloss must sit **beside** the original, never
   in place of it, and must never be the text an indicator decision rests on — even gemma3 named the
   wrong statute in one of the two articles read.
   **Note for mapping:** their Engine B is `qwen2.5:14b`. For Lao specifically, that is the weaker
   model of the two, and this is worth knowing before the live test draws Lao PDR.
4. **Better OCR buys as much as a better model.** The two are coupled and roughly equal in weight,
   so the Lao OCR work in W3 to W5 improves any future gloss for free.
5. **Do not use NLLB-200.** CC-BY-NC forbids commercial use, which contaminates the "fully open and
   reusable" claim, and its Lao quality is unmeasured here either way.
6. **Do not buy a cloud translation service for this.** The costed routes were $1,300 to $2,600 for
   the Lao corpus, the host's no-proprietary rule applies to translation as well as OCR, and the
   provision that actually gets scored is a handful per economy, not 24,000 pages.

## What was not measured

- **Chinese and Portuguese glossing.** No reference translation exists for either corpus, so there
  is nothing to score against. qwen2.5's Chinese is its home ground and would very likely be better
  than its Lao; that is an expectation, not a measurement.
- **Any cloud translator.** No key, and they are excluded by the no-proprietary rule from being the
  only path.
- **Whether a gloss changes a mapping verdict.** The honest test is to run mapping twice, once with
  and once without the gloss, and compare the indicator decisions. That belongs to stage 3 and is
  the experiment to run if anyone proposes shipping a gloss.
