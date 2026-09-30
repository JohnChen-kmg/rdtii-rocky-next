# Findings owed upstream, from the mapping run

**29 September 2026. Written for the extraction and collection workshops.**

Nothing in your workshops has been changed. These are findings from mapping 14,456 provisions and
filing 318 rows, in the form you can act on or dismiss. Every number is from the handoff2 corpus or
this run's output and says where it came from, so you can re-derive it rather than take my word.

Two of the five are new and neither was visible before mapping cited the documents.

---

## 1. NEW, extraction — `law_name` is not resolved per act in a multi-act file

**The measurement.** Of Timorese gazette documents holding more than one act, **364 of 364 carry a
single document-level `law_name` across every act inside them, and 0 vary by act.** 120,690
provisions sit in that condition, 71% of Timor-Leste's 189,557. `act_index` and `act_count` are
populated and look correct — the acts *are* identified — but the title is attached per file, so
every act except one per file is mislabelled.

`citation_confidence` reports `"exact"` regardless.

**Re-derive it:** group TL provisions in `provisions.jsonl` by `doc_id` where `act_count > 1`, and
count distinct `law_name` per `act_index`.

**The case that found it.** `tl-paodlndda2006-001#a3#Art. 16(2)`, act 3 of 3, from
`serie1_no27.pdf` (2009):

| field | value |
| :---- | :---- |
| provision text | *"deve ser conservada no Sistema de Informação de Registo de Crédito por um período de tempo não inferior a dez anos"* |
| `law_name` | Primeira alteração da Lei n.º 3/2006 (Estatuto dos Combatentes da Libertação Nacional) |
| `law_name_en` | To establish the monthly value of the food allowance for Agents and Officers of the National Police of Timor-Leste |
| `citation_confidence` | `exact` |

Three unrelated subjects for one provision. The provision itself is a credit-registry retention
rule, which mapping scored correctly as a 7.3 hit at confidence 0.9 — **the mapping is right and the
citation is wrong**, which is the worst combination because nothing downstream can detect it.

**What it cost us.** 33 of Timor-Leste's 65 filed provisions — **51%** — carry a citation that
cannot be defended as written. We did not drop those rows, because the provision, quote, article and
URL are all verifiable; we added a caveat naming which act the provision is in and stating that the
Law Name may belong to another act in the same issue.

**Two things that would help, in order of value:**

1. Resolve `law_name` per `act_index`. A Jornal da República issue lists its acts; the title of each
   is at the head of that act.
2. Failing that, **stop reporting `citation_confidence: "exact"` when `act_count > 1` and the title
   is the file's rather than the act's.** A confidence field that says `exact` on a title we know is
   probably wrong is worse than no field, because it invites exactly the trust it cannot support.
   This is the cheaper fix and it is the one that matters more.

A related smaller point: `act_index` is null on 68,867 TL provisions (36%). Those are not
attributable to an act at all, and for those a caveat is the only thing available.

---

## 2. NEW, extraction — how bad the Lao OCR is, measured per provision

You recorded Lao PDR as 99.6% OCR at ~94% character agreement. Mapping produced an independent
per-provision reading of that, because we had a model translate each provision and let it refuse.

**Of 205 Lao provisions glossed, 196 (96%) came back flagged as too damaged to render faithfully.**
For comparison: China 58 of 592 (10%), Timor-Leste 75 of 173 and 146 of 370 (~40%). On short quotes
rather than whole provisions the Lao rate is 24 of 188 (13%) — because the mapper picks a clean
sentence, while a whole provision includes the ragged edges.

At 96% the flag has stopped discriminating between provisions and is better read as a property of
the corpus. The damage is specific and reproducible:

| in the document | should be | what it is |
| :---- | :---- | :---- |
| title vs body of the same act | ຄວາມປອດໄພໄຊເບີ | ຄວາມປອດໄພໄຂເບື — "cybersecurity" spelled two different ways in one file |
| a common word | ກົດໝາຍ | ກົດຫນາຍ — "law" |
| provision start | a consonant | `ັດຕັ້ງ` — begins with a vowel mark with nothing under it, i.e. cut mid-syllable |

The third is not OCR but segmentation: provision boundaries land inside a syllable. That one may be
cheap to improve, and it would raise the readable fraction without any re-OCR.

**We are not asking for a re-run.** The quotes we filed are byte-grounded and correct — they are the
source's own bytes. But a host reviewer checking a Lao row against the PDF will see the damage, and
the 24 flagged quotes are the rows where that is most likely. Worth knowing before 15 October.

---

## 3. Collection — the four already on the register, restated with the numbers

These were found earlier in the mapping run and are unchanged; they are here so all five findings
are in one place.

| # | finding | measured |
| :-- | :---- | :---- |
| 1 | **The same statutes crawled from two portals.** `cac.gov.cn` and `flk.npc.gov.cn` both supply the same Chinese laws | 20 China law names hold two `doc_id`s each. This is the single cause of our duplicate rows |
| 2 | **`www.gov.cn` barely crawled** | 11 documents against 924 from the NPC database. One law there accounts for 4 gold rows we miss — the largest single gap in China's coverage |
| 3 | **Bare-domain Source URLs** | 29 of China's 56 filed rows land a reviewer on a portal search page rather than the law. This is visible to a marker following our citations |
| 4 | **Lao's Cyber Crime Law is absent** | though the corpus holds 1,109 Lao gazette documents. One targeted check, not a crawl expansion |

Of these, **3 is the one a marker will notice** and 2 is the one that costs the most coverage.

---

## 4. One for us, not for you

`run_manifest.json` records `economies` but not `INDICATORS_SCOPE`, so a run scoped to a subset of
indicators does not say which subset. I destroyed and restored a file today because of it: re-emitting
Timor-Leste's 52-indicator arm without setting the scope produced 9 rows for the wrong nine
indicators, and the manifest could not tell me what the original scope had been. I recovered it from
that arm's own rollup. Recorded here because it is the same class of defect as the two above — an
artefact that does not record what produced it.

---

## What we are not asking for

No changes to either workshop before the 30 September submission. Extraction froze on 24 September
and collection before it; re-running either now would invalidate a mapping run we cannot repeat in
time. Item 2 above — dropping the false `exact` — is the only one I would consider worth doing
before 15 October, and only if it can be done without re-extracting.
