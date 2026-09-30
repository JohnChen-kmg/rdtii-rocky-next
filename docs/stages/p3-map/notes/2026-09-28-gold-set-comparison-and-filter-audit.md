# Gold-set comparison and filter audit: what we found, what we missed, and whether our filters were right

28 September 2026, after S4–S10 completed for China, Lao PDR and Timor-Leste against the shipping
codebook. Every number here is measured on `run_2026-09-27`. **The gold set scored this analysis; it
chose nothing** — no parameter, prompt or threshold was changed because of anything below.

## 0. The one fact that frames everything

**0 of 201 China and Lao baseline rows carry an article number.** The baseline cites *laws*. We cite
law + article + verbatim quote + source URL. So a like-for-like comparison is only possible at law
level, and wherever we match we are supplying precision the baseline does not have.

Only rows the baseline *scores* can be missed. Absence rows (score 0 with no article) assert that
nothing exists, so there is nothing to retrieve. That leaves **32 scoring rows: 27 China, 5 Lao**.
Timor-Leste has no baseline sheet at all.

---

## 1. Score agreement, by country and indicator

| ind | CN ours | CN gold | | LA ours | LA gold | | TL ours | TL gold |
| :-- | ---: | ---: | :-- | ---: | ---: | :-- | ---: | :---- |
| 6.1 | 1.0 | 0.5 | ✗ | 0.0 | 0.0 | ✓ | 0.0 | — |
| 6.2 | 1.0 | 1.0 | ✓ | 1.0 | 0.0 | ✗ | 1.0 | — |
| 6.3 | 1.0 | 1.0 | ✓ | 1.0 | 0.0 | ✗ | 0.0 | — |
| 6.4 | 1.0 | 1.0 | ✓ | 1.0 | 1.0 | ✓ | 0.0 | — |
| 7.1 | 0.0 | 0.0 | ✓ | **pending** | 0.5 | ✗ | **pending** | — |
| 7.2 | 0.0 | 0.0 | ✓ | 0.0 | 0.0 | ✓ | **pending** | — |
| 7.3 | 1.0 | 1.0 | ✓ | 1.0 | 1.0 | ✓ | 1.0 | — |
| 7.4 | 1.0 | 1.0 | ✓ | 0.0 | 1.0 | ✗ | 0.0 | — |
| 7.5 | 1.0 | 1.0 | ✓ | 1.0 | 0.0 | ✗ | 1.0 | — |

**China 8/9. Lao 4/9.** LA 7.2 was `pending` until the fix in §6 and now resolves to 0.0, matching.

**The disagreements are mostly in our favour.** LA 6.2/6.3/7.5 and CN 6.1 score *higher* than the
baseline on evidence that reads soundly — a local satellite-ground-station mandate, a Lao
data-centre mandate, ten sectoral retention floors. Our score differing from gold is therefore not
automatically our error. CN 6.1 (ours 1.0 against 0.5) rests on the codebook's own escalation clause:
ten distinct verified half-point measures, and the coding rule says escalate to 1 exactly that way.

## 2. Loss attribution

| | CN | LA | **combined** |
| :---- | ---: | ---: | ---: |
| scoring baseline rows | 27 | 5 | **32** |
| **reproduced** | 12 (44.4%) | 1 (20%) | **13 (40.6%)** |
| **missed — law not in our corpus** | 9 (33.3%) | 1 (20%) | **10 (31.3%)** |
| **missed — our pipeline** | 6 (22.2%) | 3 (60%) | **9 (28.1%)** |

Of the **19 misses: 53% are a crawl gap, 47% are ours.** Almost an even split, and just over half the
gap is a collection ceiling this stage cannot lift.

**Inside our 47%:**

| stage | rows | which |
| :---- | ---: | :---- |
| never selected (retrieval) | 3 | CN 7.4 Cybersecurity Law · CN 7.5 Internet Post Comments · LA 6.4 Financial Consumer Decree |
| dropped by triage | 1 | CN 7.5 Generative AI Interim Measures |
| mapper did not fire | 1 | CN 7.5 Internet E-mail Services |
| verifier overturned | 2 | LA 7.1 and LA 7.4, both the Electronic Data Protection Law |
| in corpus, no fire in that cell — untraced | 2 | CN 6.2 Industrial & Telecom Measure · CN 6.3 Map Management Regulations |

The last two are honestly untraced: the law-name matcher failed on those fragments and I did not
guess. Map Management does retrieve and fire — we filed it for 6.2 — it simply produced no 6.3 fire.

**Read the headline correctly.** 40.6% reproduction understates the stage, because a third of the
gold rows cite documents we never fetched. The achievable ceiling is **69%**, and against that
ceiling we reproduce **13 of 22 = 59%**.

And reproduction is not the product. We filed **108 rows against 32 scoring baseline rows**, the
majority outside the gold set entirely.

## 3. Where the missing laws actually live

**7 distinct instruments** account for all 10 missed rows.

| Economy | Law | Cells | Baseline's source host |
| :-- | :---- | :---- | :---- |
| CN | Interim Measures, Online Ride-Hailing | 6.1, 6.2, 6.3, 7.3 | `www.gov.cn` |
| CN | Interim Measures, Business Activities of… | 6.1 | `www.gov.cn` |
| CN | Accounting Records Measures | 7.3 | `www.gov.cn` |
| CN | Population Health Information Measures | 6.2 | `www.cac.gov.cn` |
| CN | Personal Financial Information Tech Spec | 6.4 | `www.pbc.gov.cn` |
| CN | Information Security Tech – PI Spec Amendment | 7.4 | `openstd.samr.gov.cn`, `tc260.org.cn` |
| LA | Prevention & Combating Cyber Crime Law | 7.3 | *(commentary site only)* |

What we hold:

| | hosts, by document count |
| :-- | :---- |
| CN | `flk.npc.gov.cn` **924** · `cac.gov.cn` 108 · `miit.gov.cn` 18 · **`gov.cn` 11** |
| LA | `laoofficialgazette.gov.la` **1,109** |

Three patterns, all actionable by the collection stage rather than this one:

1. **`www.gov.cn` is the largest single gap.** Three of the seven live there and we hold 11 documents
   from it against 924 from the NPC database. That is the State Council gazette, where ministry-level
   *Interim Measures* are published. The Ride-Hailing Measures alone cost 4 of the 10 missed rows.
2. **Two are not legislation.** The PBOC financial-information spec is an industry standard (JR/T);
   the Information Security Technology amendment is a **national standard** on `openstd.samr.gov.cn` /
   TC260 (the GB/T series). No law crawler will find these, and whether a standard belongs in a
   database of *laws* is a question for the host, not a defect in ours.
3. **Lao's gap is narrower.** We hold 1,109 gazette documents and nothing else. The missing Cyber
   Crime Law is a National Assembly law that ought to be in that gazette; the baseline's only link is
   a commentary site, so its record cannot tell us whether the gazette copy exists. That is one
   targeted check, not a crawl expansion.

Findings 1–3 go back to the scraping workshop as notes, never as edits.

## 4. Filter audit: did our filters make sense?

I read the full text and the reviewers' reasoning for all five filtered rows. **Three are clearly
correct, one is a structural flaw rather than a misjudgement, one goes against us.**

### 4.1 LA 7.4 — Electronic Data Protection Law Art. 23 — verifier — **CORRECT**

Mapper: "a unit/staff responsible specifically for data security management" is a DPO-equivalent,
Horizontal, score 1, **confidence 0.55**.

Verifier (Haiku, 0.95): *"adjacent roles (e.g. a 'security officer' or 'data security unit') do not
satisfy the DPO definition unless the role is responsibility for personal-data-protection compliance
under a data protection law."* Escalation (Opus, 0.82) independently: *"a security-officer/risk-
assessment duty, not a DPO… or a DPIA."*

A data-security officer is not a Data Protection Officer. Both reviewers agreed; the mapper was the
least confident party. The filter was right, and the open question is whether the real DPO duty sits
in another article of that law that never fired.

### 4.2 CN 7.5 — Generative AI Interim Measures Art. 21 — triage — **CORRECT**

The provision sits in 第四章 監督检查和法律责任. It requires providers to supply technical and data support
to supervisors, and requires officials to keep state/trade secrets and personal information
confidential. The shipping codebook's new 7.5 trap excludes precisely these two things: *"not generic
inspection of business records by a regulator, and not a secrecy duty with a court-order carve-out."*

### 4.3 CN 7.4 — Cybersecurity Law Art. 73 — triage — **CORRECT; the loss is retrieval**

Art. 73 is the legal-liability chapter, cross-referencing Arts. 37/39/46 rather than stating a duty.
Triage refused a penalties article, correctly. Of 162 CSL provisions we hold, exactly **one** was
selected for 7.4 and it was that one. The article carrying the duty (Art. 21) ranked **782**, outside
the 700 ceiling, in a band where cosine moves 0.012 across 400 ranks. No ceiling value fixes an
ordering that carries no signal — decision **M14**.

### 4.4 LA 7.1 — Electronic Data Protection Law Art. 1 — verifier — **defensible, but the conclusion is discarded**

Mapper: Art. 1 is the purpose/scope article of a horizontal data-protection law, so the economy-level
answer is 0 (a framework exists). Confidence 0.55.

Verifier: *"Per-provision citations of a data-protection act tagged 7.1 are not discoveries and score
zero… Article 1 is a single provision of the act, not the act's existence."* Escalation: *"'electronic
data' here is defined broadly (numbers, text, images, audio, video) rather than as personal data with
access/rectification/erasure rights."*

Two things matter here. We **filed CN 7.1 on PIPL Art. 1**, also a purpose clause, and it stood — so
this is not inconsistency; the escalation identified a real legal distinction, that Lao's law governs
electronic data generally rather than personal data with data-subject rights. And that conclusion
**points at the baseline's 0.5**.

**This is the defect.** The verifier reached an informative finding — "this is not a comprehensive
personal-data framework" — and the pipeline throws it away, leaving the cell `pending` and scoring
nothing. The fix is not to loosen the verifier. It is to let a *reasoned rejection* on an
economy-level indicator count as evidence instead of silence.

### 4.5 CN 7.5 — Internet E-mail Services Art. 5 — mapper — **ARGUABLE, and the baseline's reading is at least as good**

Text: *"Except where necessary for national security or criminal investigation, whereby public
security organs or procuratorates inspect communication content in accordance with legally prescribed
procedures, no organisation or individual may infringe citizens' communication secrecy."*

The mapper declined it at **confidence 0.6** as "a protective clause against interference with
correspondence". Formally that is what the article is. Substantively the carve-out authorises
**procuratorate** inspection — government access to communications with no judicial order, which is
7.5's core test. The new trap says exclude a secrecy duty with a carve-out; the baseline reads the
carve-out as the finding. Both are tenable and ours is the weaker one.

This is the only one of five filters that plausibly cost us a row on the merits.

## 5. Corrections to my own earlier statements

Recorded because both were wrong and both were stated confidently.

1. **"Lao matched 0 of 5 baseline laws."** Wrong. The matcher compared the baseline's English name
   against our Lao-script `Law Name` and could not bridge them. Redone on doc ids, LA reproduced 1 of
   5 — the Electronic Data Protection Law for 6.4, Arts. 17 and 18.
2. **"The verifier is too aggressive on economy-level cells, and LA 7.1/7.4 are directly caused by
   it."** Wrong twice. The verifier was *right* on 7.4 (§4.1), and 7.4 is not an economy-level
   indicator — only 7.1 and 7.2 are. The real defect is narrower and structural (§4.4).

## 6. Fixed during this audit

**The economy-level scorer discarded a cell on a transient shape failure.** LA 7.2 read
`economy-level call failed: KeyError` with 36 verified evidence rows unused; the identical call then
succeeded. Same envelope problem as the mapper. `_framework_score()` now unwraps a single-key
envelope and defaults the two descriptive fields, while still refusing to invent a score. **LA 7.2
now resolves to 0.0, matching the baseline.**

Three cells remain `pending`: LA 7.1, TL 7.1, TL 7.2 — all "economy-level indicator, zero verified
evidence", which is §4.4's defect.

## 7. What I would fix, in order

1. **Use a reasoned rejection on an economy-level cell as evidence** (§4.4). It is the only filter
   error of the five, it costs three `pending` cells today, and it is a prompt-and-plumbing change
   rather than a retrieval one.
2. **Ask the collection stage for `www.gov.cn`** (§3). Eleven documents against 924 from the NPC
   database, and one law there costs four missed rows.
3. **Decide whether GB/T and JR/T standards belong in a law database at all** (§3). Two of the seven
   missing instruments are standards, not legislation. This is a question for the host.
4. **Leave CN 7.4 alone** (§4.3). M14 already settled it: the cap is not the constraint, and tuning
   it to recover a known gold row would be fitting to the baseline.

## 8. Method, for reproducibility

- Score comparison: `out/rollup/economy_scores_<E>.json` against `out/baseline_rows.jsonl`.
- Law-level comparison: resolved on **doc ids**, via `doc_meta`'s three name forms, never on name
  strings across scripts — see correction 1.
- Stage attribution: a baseline row's resolved doc ids traced through `select/*_pairs.jsonl`,
  `triage/haiku_results.jsonl`, `map/verdicts_<E>.jsonl` and `verify/verified_<E>.jsonl`.
- Filter audit: the full `mapper`, `verifier` and `escalation` records in `verified_<E>.jsonl`, plus
  the provision text from `index/prefilter_corpus.jsonl`.
- Probes: `evidence/probes/gold_after_triage.py`, `verify_s4.py`.
