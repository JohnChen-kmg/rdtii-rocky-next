# Mapping-Tool Framework — Deep Research & Proposal

**Produced overnight 2026-07-14 → 15** from: three extraction passes over every official RDTII document in `reference/`, an audit of the vendored P0 instrument and the delivered `handoff2/` corpus, two web-research passes (tooling + regulatory workflows), one architecture-design pass, a full-corpus keyword scan, and the budget/scaling discussion with John on 15 Jul.
**Purpose** (the two asks): ① extract the mapping *instrument* from the official documents — scenarios, assignments, situations; ② map the *extraction results* (305,980 provisions) to a concrete workflow.
**Precedence:** where this document differs from `PLAN.md` or `KICKOFF_DECISIONS_2026-07-12.md`, this document reflects the newer research and the 15-Jul discussion; interfaces (Hand-off #2 in, frozen 13-column CSV/JSON out) are unchanged.
**Citation key:** GUIDE = `ESCAP-RDTII-2.1-guide.pdf` (130 pp; page numbers are *PDF* pages; printed folio = PDF − 12) · INT = internal guide · NONREG = non-regulatory indicators note · QA = hackathon Q&A summary · KB = knowledge base · ANSKEY = answer key & feedback · FMT = format requirements · SLIDES = extraction hands-on slides (59) · R1DB = Round-1 baseline xlsx · R2DB = Round-2 database xlsx · TEMPLATE = OUTPUT_TEMPLATE.xlsx · INSTR = `contracts/instrument/`.

---

## 0 · Executive summary

- **The instrument is in hand and validated.** Independent re-extraction of the official documents confirms the vendored `contracts/instrument/` is faithful and near-complete; this research adds a handful of scoring nuances (P6-I1/I2 escalation clause, P6-I4 personal-data asymmetry, P7-I4's theoretical 0.25, pillar-internal weights) and a large body of host doctrine from the assignments and slides (§1.5) that should shape the prompts.
- **The single most design-critical finding:** the nine indicators are *not* one kind of question. Seven are provision-level; **P7-I1 and P7-I2 are economy-level framework-existence questions with inverted polarity** — they require an evidence roll-up stage that no per-provision call can perform (§1.4, §2.4).
- **The workflow** is an 11-stage funnel (§2.9): 305,980 provisions → free prefilter over 2.75M (provision × indicator) pairs → local-model triage ($0) → ~10–11k Sonnet-judged pairs → blind verification → economy roll-up → NEW/KNOWN diff → Malaysia error-check → a curated ~110–180-row CSV with a full audit trail.
- **Budget (settled 15 Jul): batch-first + local triage ≈ $150–260, hard ceiling $400** — with a day-2, ~$10 A/B that may cut it to ~$80–130 by letting Haiku map first and Sonnet re-judge only what fires or wavers (§2.10). Nothing API-billed runs until the key is topped up; every preparation step below is local and free.
- **Scaling story (also the sustainability pitch):** per-economy caps bound bootstrap at ~$50–90; Round-1's graded verdicts become fine-tuning data that drops later economies to ~$10–20; content-addressed deltas make staying current ~$5–20/economy/year. Local-language economies cost ~1.5–2× (§2.11).
- **The 20-pt NEW lever has a concrete target list** (§3.4): 2025 Malaysian PDPA-amendment commencements (new DPO duty, breach notification, transfer-regime overhaul), Singapore's Cybersecurity Amendment commencement (31 Oct 2025), Australia's ransomware-reporting rules (30 May 2025) — all verified against official portals, all likely postdating the baseline.

---

# Part 1 — The mapping instrument, extracted from the official documents

## 1.1 The nine indicators — authoritative definitions and scoring

Scope: Pillars 6 & 7 only; **6.5 is out** (non-regulatory treaty-participation — NONREG p.1: "an automated data retrieval method is not required"); **7.5 is in**. Definitions below are from the methodology (GUIDE pp.60–74) — *never* from TEMPLATE's "Indicator Reference" tab, which is wrong (§1.6.4).

| ID | Name | Core question | Allowed scores & conditions | Weight in pillar |
|---|---|---|---|---|
| P6-I1 | Ban & local processing | Transfer banned per se / must data be processed locally? | **1** = covers personal data OR horizontal, **or ≥2** sector/data-limited measures (escalation clause); **0.5** = one measure on non-personal/specific data or to one economy; **0** = free transfer (GUIDE p.62) | **38%** |
| P6-I2 | Local storage | Must a *copy* stay in-country (transfer may continue)? | **1** = personal/horizontal **or ≥2** limited measures; **0.5** = one limited measure; **0** = none (GUIDE p.63) | 12% |
| P6-I3 | Infrastructure | Local data centre / server required as a service precondition? | **1** = at least one requirement; **0** = none. Binary. (GUIDE p.64) | **31%** |
| P6-I4 | Conditional flow | Transfer only if conditions met (consent / adequacy / contract / approval)? | **1** = covers personal data (*even sector-specific* — the asymmetry, GUIDE p.66) OR horizontal; **0.5** = non-personal/specific data only; **0** = no condition. **No escalation clause.** | 12% |
| P7-I1 | *Lack of* comprehensive DP framework | Horizontal data-protection law exist? | **1** = none; **0.5** = sectoral only; **0** = comprehensive horizontal. **INVERTED.** (GUIDE p.70) | 31% |
| P7-I2 | *Lack of* dedicated cybersecurity framework | Dedicated cybersecurity law exist? | **1** = none; **0.5** = non-dedicated and/or sectoral-dedicated; **0** = dedicated horizontal. **INVERTED.** (GUIDE p.71) | 31% |
| P7-I3 | Minimum retention | Any rule requiring data kept **at least** N period? | **1** = minimum-period (or permanent, fn.36) requirement; **0** = none, or period unspecified ("as long as necessary"). Binary. (GUIDE p.72) | 16% |
| P7-I4 | DPIA / DPO | Duty to appoint a DPO / run a DPIA? | **1** = DPO (± DPIA) all sectors; **0.5** = specific sector; **0.25** = DPIA-only (theoretical, never observed — *flag, don't emit*); **0** = none (GUIDE p.73) | 6% |
| P7-I5 | Government access | Gov access to personal data **without** independent judicial authorization? | **1** = yes (incl. undefined/ambiguous authority — Cambodia example); **0** = access is court-gated. Binary. (GUIDE p.74) | 16% |

Notes that matter for design:
- **P6-I3 at 31% weight** is the second-heaviest Pillar-6 indicator despite being binary and rare — a missed infrastructure requirement is expensive.
- Scores are *hints only* in our output (JSON `score_hint`; the 13-column CSV has no score column). Zone 3 scoring is officially "human, optional/bonus" — Zone-2 record quality is what is graded (`Target_Output_Summary.md` §4).
- Score-0/absence is still an *evidenced* record: "note the lack of measures and cite the relevant general rule … state the reason" (GUIDE p.24; INT p.10).

## 1.2 Cross-cutting doctrines (each is a validator or prompt rule)

1. **Enforced only** — pending drafts and repealed measures are excluded (INT p.8). To check in-force: repealed/replaced? effective date? formally adopted? (SLIDES 16–17). *Trap instances found:* SG Data-Portability Part 6B and AU ADM-transparency duty are enacted-but-not-in-force (§3.4) — must not be scored.
2. **Official sources only** — secondary sources (trackers, law-firm reviews, news) "serve only to guide researchers to the primary sources" (GUIDE p.24). The cited URL must be the law on an official portal.
3. **Government-data exception** — measures applied to government data are not scored, for **6.1–6.4 and 7.3 only** (INT p.9; GUIDE pp.62–66, 72). Not stated for 7.1/7.2/7.4/7.5.
4. **Commercial focus** — the database captures commercial activities (GUIDE p.66).
5. **Recording ≠ controlling** — "any legal text published by a government body is recorded"; whether it *controls* the score is case-by-case; regulator Notices are legal instruments; sectoral rules are recorded even when a horizontal law exists (ANSKEY p.2). Hierarchy is a conflict-resolver, never a filter.
6. **Hierarchy ≠ coverage** — "Horizontal does not mean higher rank; sectoral does not mean lower rank" (SLIDES 13). A law covering two sectors is still sectoral.
7. **Multi-indicator texts** — "one measure can be listed under several RDTII sub-pillars" (INT p.11; GUIDE p.23 states the same rule in different words); one article → two indicators = two rows (TEMPLATE instructions). The host names wrong-indicator mapping the **highest risk** (ANSKEY p.3).
8. **One instrument per row when coverage differs** — from the R1DB reviewer dialogue (§1.6.3).
9. **Operative clause, not title** — "never record only the law title; record the operative provision and your reasoning" (SLIDES 4); watch trigger words: *unless, except that, provided that, subject to, notwithstanding, only if, no later than, to the extent, may/shall/must/will, not liable unless* (SLIDES 27), plus the 7.3 floor-wording *not less than / at least / minimum period* (GUIDE p.72; `indicators.yaml`).
10. **Score >0 requires** differential domestic/foreign treatment, a non-economic-objective barrier, or failure to adopt a significant framework (INT p.10, as encoded in `policies.yaml`; GUIDE p.22 words its three conditions differently — administrative burden · differential treatment · not following recognized international norms).
11. **Timeframe convention** — "Since [Month Year], last amended in [Month Year]" (FMT p.3).
12. **Never blank** — where nothing is found: an informative "No provision found" statement citing the governing law (GUIDE p.24; FMT p.2; SLIDES 54 item 5).

## 1.3 The trap catalog (scenario rules the mapper must encode)

| # | Trap | Rule | Source | Canonical example |
|---|---|---|---|---|
| 1 | **Ban vs conditional (6.1 vs 6.4)** — the #1 mis-mapping | A prohibition liftable by conditions (consent/adequacy/contract/approval) is 6.4, never 6.1. Classify by whether a *compliant transfer path exists*. | INT p.13; Assignment-2 brief is *dedicated* to this boundary | SG PDPA s.26(1) → 6.4. MY PDPA s.129 reads as prohibition but has exceptions → baseline codes 6.1=0, 6.4=1 |
| 2 | **Max ≠ min retention (7.3)** | "Not longer than necessary" is a maximum-period rule → **not** 7.3, score 0 (may still be recorded). Only "at least N" floors score 1; permanent retention = 1. | GUIDE p.72 + fn.35/36; INT p.13 | SG PDPA s.25 = the canonical negative (scored 0 in baseline); Bangladesh 6-yr e-commerce rule = positive (SLIDES 45) |
| 3 | **Government data not scored** (6.1–6.4, 7.3) | Localization/retention of government data → no scored row. | INT p.9 | AU TikTok-on-gov-devices ban → Pillar 2/10, not 6.1 (INT p.11) |
| 4 | **Inverted polarity (7.1, 7.2)** | An economy *with* a comprehensive/dedicated framework scores **0**. Never emit 1 because a strong law was found. | GUIDE pp.70–71; ANSKEY p.2 | SG PDPA → 7.1 = 0; SG Cybersecurity Act 2018 → 7.2 = 0 |
| 5 | **6.4 personal-data asymmetry** | Personal-data conditions score 1 *even when sectoral* (unlike 6.1/6.2 where sectoral = 0.5). | GUIDE p.66 | Korea geographic-survey-data approval = 0.5 (non-personal, specific) |
| 6 | **Escalation clause is 6.1/6.2 only** | ≥2 category-2 measures → 1; never applies to 6.4. | GUIDE pp.62–63 | MY's five sectoral 6.2 storage rows |
| 7 | **Confidentiality ≠ transfer ban** | Bank-secrecy/professional-secrecy disclosure rules are not cross-border measures unless they regulate *movement across borders*. | INSTR (answer-key doctrine); Scoring_Criteria anti-checklist ("SG Banking Act trap") | SG Banking Act s.47 recorded under 7.1 at 0, not 6.1 |
| 8 | **Adjacent roles ≠ DPO; advisory ≠ mandate (7.4)** | Registry contacts, local representatives, compliance officers don't satisfy the DPO duty; recommended DPIAs create no mandate. DPIA-only = 0.25 → flag for human review, don't emit. | GUIDE p.73 | Türkiye VERBIS contact ≠ DPO; AU PIA "contemplated but not mandated" = 0 |
| 9 | **6.3 excludes licensing & operations** | Data-centre licensing/registration → indicator 9.4 (out of scope); operational/technical rules on existing centres → not scored; non-transfer-related data-centre rules → record at 0. | GUIDE p.64; INT p.13 | China ride-hailing local-server rule = the positive (SLIDES 40–41) |
| 10 | **Storage (where) vs retention (how long)** | Location rules → 6.2; duration rules → 7.3; the same instrument can carry both (two rows). | GUIDE p.71 fn.34 | SG Companies Act s.199: "kept in Singapore" → 6.2 *and* "5 years" → 7.3 (INSTR exemplar) |
| 11 | **7.5 reaches beyond privacy law** | Search criminal procedure, surveillance, telecom, intelligence law; warrantless-in-urgency exceptions and undefined "legitimate authority" *do* score 1. | GUIDE p.74; R1DB MY row-59 dialogue | SG CPC 2010 ss.20/39 → 1; Thailand CSA court-gated powers → 0 |
| 12 | **Keyword myopia** | "Do not rely solely on a literal piecemeal analysis of statutory keywords; instead, consider both the semantic context and the underlying legal functions." | SLIDES 37 | Bhutan CoP network segmentation: *not* 6.2/6.3 despite storage-adjacent words (SLIDES 36–37) |

## 1.4 Provision-level vs economy-level indicators (design-critical)

- **Provision-level** (6.1–6.4, 7.3, 7.5, mostly 7.4): the evidence is a clause; one clause = one row; an economy can have many rows (baseline: MY 7.5 has 6 rows, SG 7.3 has 5).
- **Economy-level** (7.1, 7.2): the question is "does a framework *exist*?" The controlling evidence is the horizontal act's scope provision; sectoral instruments are recorded alongside but don't move the score (ANSKEY worked example). No SG/AU/MY scores 1 on either — the pipeline will mostly evidence 0/0.5, which are still cited rows.
- Consequence: per-provision LLM calls must never emit economy scores for 7.1/7.2 — they classify each provision's *role* (horizontal scope provision / sectoral framework / not relevant), and a separate roll-up judgment composes the cell (§2.4). This also structurally contains the polarity trap.

## 1.5 Host doctrine from the assignments and slides (what the graders actually reward)

**The worked error-check (ANSKEY pp.1–2, the Assignment-1 case):** a tool output recorded the *MAS Notice on Cyber Hygiene (2019)* for SG 7.2. Wrong twice: the URL 404'd, and the notice was cancelled 1 Jul 2022 and replaced by Notice FSM-N16 — "a researcher would record the latest Notice FSM-N16." What teams missed: the dead URL, the supersession, and that sectoral regulations are still *recorded* (not controlling) beside the Cybersecurity Act 2018. → Our error-check classes: URL validity, currency/supersession, controlling-vs-recorded (§2.6).

**The host's own quality checklist (SLIDES 54):** correct indicator + scope? source official, current, in force? exact provision, not title? rule separated from exceptions/thresholds? absence still cites the governing law?

**The host's error taxonomy (Assignment-1 brief):** incorrect citation · missing act · misinterpretation · wrong answer to the indicator's core legal question · broken URLs · outdated laws · portal barriers · unstructured formats · **hallucinated indicators**. (Our closed 9-ID vocabulary + schema kills the last.)

**13 worked mapping examples with answers (SLIDES 30–53)** — few-shot material: Korea financial local-processing → 6.1 · Türkiye social-network storage → 6.2 · Viet Nam ≥1 local server → 6.3 · Palau notify+consent → 6.4 · Armenia PDP Art.27 → 6.4 · Bhutan CoP access-control → *not* 6.2/6.3 · Kazakhstan Art.12(2) → 6.2 · China ride-hailing → 6.3 · Bangladesh 6-yr retention → 7.3 · SG DPO → 7.4 · SG CPC s.39(1) → 7.5 · Bhutan encryption CoP → 7.2 · India DPDP s.10 → 7.4.

**Recall-first, endorsed verbatim (ANSKEY p.3):** "The list doesn't have to be ranked; all relevant laws identified by this method can move on to next stage. In the early stages of the tool development, it is advisable to review a broader set of results to reduce the risk of overlooking relevant legal instruments." And: "RDTII database is as latest as 2025-early 2026 (SGP)" — you might discover new updates: the official framing of NEW.

## 1.6 Baseline & template anatomy

### 1.6.1 Round-1 baseline (the KNOWN set)
5 sheets (Methodology · Consolidated · Australia · Malaysia · Singapore); data rows SG 81 / MY 99 / AU 70 across all pillars. P6/P7 rows per indicator (SG|MY|AU): 6.1 (1|1|1) · 6.2 (1|**5**|1) · 6.3 (1|1|1) · 6.4 (1|3|1) · 7.1 (2|3|1) · 7.2 (1|1|1) · 7.3 (**5**|**5**|1) · 7.4 (1|1|1) · 7.5 (1|**6**|3). **7.3 and 7.5 are the multi-row indicators** — retention floors and access powers live in tax, telecom, AML and procedure law, exactly where NEW provisions hide. Conventions: several laws per cell separated by ";"+blank line; `Impact` prose cites exact sections ("According to Section 26…"); official-portal URLs in Reference columns, commentary URLs relegated to Note.

### 1.6.2 Gold set (`INSTR/gold/gold_set.jsonl`, P6/P7 normalization of R1DB)
51 rows (AU 11 / MY 26 / SG 14) with provenance and `articles_mentioned`. **7 label flags: 2 suspect** — MY 7.3 "PDPA Retention Principle"=1 and MY 7.3 Communications-CoP=1, both *maximum*-period rules that the Guide's own rule scores 0 (SG's identical s.25 pattern **is** scored 0 in the same baseline) → the concrete Malaysia error-check targets; 5 advisory (AU My-Health-Records 6.1/6.2 gov-data tension — Guide's own worked example, 0.5 stands; MY sectoral-CoP 7.1 rows; SG telecom-licence 7.3 coverage mislabel). Absence-row precedent: `r1-au-036` — AU 6.3, Privacy Act 1988, "No infrastructure requirements were found" (settles §2.7).

### 1.6.3 The reviewer dialogue (R1DB Malaysia 7.5 row 59, Note column)
A preserved researcher⇄reviewer exchange: warrantless-access-in-urgency exceptions **do** drive 7.5 to 1 ("absence of internationally agreed frameworks" distinguishes this from TRIPS-sanctioned exceptions in Pillar 4); instruments with different coverage are **separated into their own rows**. This is the closest thing to the host's scoring case law.

### 1.6.4 The template trap (TEMPLATE "Indicator Reference" tab — WRONG)
GDPR-style labels contradict the methodology: P6-I2 "Adequacy standard", P6-I3 "Contractual safeguards", P6-I4 "Consent exception", P7-I1 "Legal basis for processing", P7-I2 "Purpose limitation", P7-I3 "Data subject rights", P7-I4 "Data breach notification", P7-I5 "Enforcement & penalties". Even its example rows carry GDPR rationales (row 8 maps PDPA s.24 → P7-I1 — questionable). `indicators.yaml` carries `WARNING_DO_NOT_USE`; no code reads this tab; the audit page footer surfaces the guard. The tab's *usable* rules stand: exact 13-column order, one row per provision, two indicators = two rows, no merged cells, delete example rows, NEW = 20/40 verbatim, "Mapping Rationale is not directly scored — blank is neutral, wrong misleads."

### 1.6.5 Round-2 database & practice dataset
R2DB: 7 economies (CN/IN/ID/LA/MN/RU/TH), same internal schema, 809 data rows — the few-shot exemplar pool (India 7.3 = 19 rows is the richest cluster). Round-2-only exemplars = the leakage-safe eval profile (Kickoff Decision 12). The practice dataset contains blank templates only (no answer key embedded).

## 1.7 Gap analysis — official documents vs the vendored instrument

**Verdict: the P0 instrument survives independent re-extraction.** All 9 scoring trees, the 8 encoded traps, the policies (enforced-only, official-sources, gov-data, hierarchy-not-a-filter, edge cases) and the 57 exemplars check out against the Guide/INT/ANSKEY wording — including the subtle ones (escalation clause on 6.1/6.2 only; 6.4 asymmetry; DPIA-only flag-don't-emit). Trap-count reconciliation: §1.3 rows 1–8 are the INSTR-encoded traps; rows 9–12 are methodology/slide-level rules (9 and 10 partially present as INSTR exceptions/negative-signals; 11's urgency rule is delta 4 below; 12 is a prompt-level principle). Deltas worth carrying into prompts/tests rather than instrument edits:

1. The **weights** (6.1 38%, 6.3 31%, 7.1/7.2 31%) — prioritization signal only (already in INSTR as informational).
2. **SLIDES trigger-word list and QC checklist** (§1.2 #9, §1.5) — add to the mapping prompt's decision procedure.
3. **13 worked examples** (§1.5) — candidate few-shots alongside the 57 curated exemplars (subject to the exemplar A/B, Kickoff Decision 7).
4. The **row-59 reviewer dialogue** (§1.6.3) — encode as a P7-I5 coding rule: "urgent-case warrantless access ⇒ 1".
5. **"Malaysia error-check" is our framing**, not the host's: the documented error-check is the SG 7.2 case; the transferable doctrine (URL + currency + controlling-evidence) applied to MY's 26 gold rows, anchored by the 2 suspect 7.3 rows, is the defensible implementation (§2.6).

---

# Part 2 — The workflow: mapping the corpus to the submission

## 2.1 Corpus facts that constrain the design (all measured)

- **305,980 grounded provisions / 2,613 laws** (SG 525 · MY 831 · AU 1,257); provision_count median 37, max 3,168; 158 zero-provision laws (`provision_count: 0, searched: true` — the "No provision found" input); **3 parse_failed docs** with *no corpus provisions*: the 2 MY PDP Codes of Practice (cited by 13 of the 51 gold rows — 3 of the 7 *flagged* ones, incl. suspect r1-my-054) + 1 OAIC guidance page.
- `provisions.jsonl` is 639 MB — stream only. 38 fields/record; `provision_id` carries `~n` disambiguators (opaque join key); ~44.7k records reportedly carry literal newlines inside `law_number` (FOUNDATION_SYNC figure — re-count at S0 ingest, since its sibling laws.jsonl count measured 312 vs the quoted 359; the collapse-whitespace rule for every CSV string column stands regardless); bilingual MY gazettes have Malay+English twins (map English, cross-note Malay).
- P2's tags are **soft boosts only** (measured agreement 46.6–80.6%); 6,297 provisions pre-flagged with cross-border classes (SG 2,128 / AU 3,087 / MY 1,082) — a strong P6 prior, never a gate. `extraction_confidence` skews low by design (0.1 on valid records) — low means "widen", never "exclude".
- The canonical slice target exists and is clean: `sg-pdpa2012-001#s.26(1)`, tagged `conditional`, confidence 0.95, byte-grounded.
- **Corpus v2.1 (re-delivered 2026-07-14 ~18:00–19:00 after P1/P2 updates — supersedes the counts above):** **317,388 provisions / 2,638 laws** (SG 525 · MY **856** · AU 1,257); provisions.jsonl now 659 MB; `contract_version` still 0.2.0; canonical target `sg-pdpa2012-001#s.26(1)` intact (tagged personal/conditional, conf 0.95). What changed: (a) **+25 MY docs** — 2024–25 acts the old crawl missed, incl. **PDP (Amendment) Act 2024 / A1727 (`my-pdpa2024-001`, 15 provisions: DPO duty at s.6, breach notification, s.129 transfer-regime change at s.10 — three §3.4 premium-NEW targets now in-corpus at act level)**, Data Sharing Act 2025, Online Safety Act 2025, Gig Workers Act 2025, Consumer Credit Act 2025; note A1727's own s.1(2) says "comes into operation on a date to be appointed" — commencement evidence stays external (phased 1 Jan/1 Apr/1 Jun 2025). (b) **SG CA2018 fixed**: re-crawled consolidated (338 provisions; post-2024-amendment content verified — s.17E "systems of temporary cybersecurity concern"). (c) **Schema change**: `doc_status` moved out of laws.jsonl into new **`doc_status.jsonl`** (fields: status · lane · reason · source_type_final · doc_cer) — S0 ingest must join on it; status counts ok 2,454 · zero_provisions 184 · parse_failed 3 (same three docs). Still outstanding from §3.4a: **all subsidiary/regulator instruments** (SG SL-Supp S677/S217/PDP Regs, MY PDPD guidelines + Act 854 P.U.(A) regs, AU F2025L00278) and the **AU SOCI re-crawl (still 1 provision)**; MY PDPA 2010 base text is still pre-amendment (amendments live only in `my-pdpa2024-001`); 2 MY CoPs + au-piag-001 still parse_failed.
- **Crawl-sufficiency audit (measured 2026-07-14 on corpus v2.0, 3-agent pass over manifest + laws.jsonl + gold set — partially remediated by v2.1 above):** the corpus is **acts-only from the three primary statute portals** (legislation.gov.au 1,257 · lom.agc.gov.my 831 · sso.agc.gov.sg 524 · +1 pdpc.gov.sg doc; **zero non-official hosts** — citation policy clean). Consequences: (a) **zero subsidiary/delegated instruments in any economy** (no SG SL/S-numbered docs, no MY P.U.(A)/guidelines, no AU F-register instruments) and 8 of 11 expected regulator sites unrepresented (mas/csa/imda/acma/cisc/mcmc/bnm/nacsa); (b) gold coverage: **28 of 38 baseline-cited instruments matched** — all statutes covered; 3 crawled-but-parse-failed (2 MY CoPs + OAIC PIA guidance = au-piag-001, which is gold r1-au-042); **7 never crawled** (AU Cyber Strategy, AU Assistance & Access Act 2018, AU Telecom Regs 2021, MY PDP Standard 2015, SG telecom licence + IP-telephony terms, SG PDPC children's guidelines); (c) **only 4 of the 14 §3.4 NEW leads are present** (MY A1727, MY Act 854, AU Cyber Security Act 2024, AU POLA-via-consolidated-Privacy-Act); SG Cybersecurity Act was crawled **as-enacted 2018** (2024 amendment NOT merged — consolidation does not rescue it) and AU SOCI Act parsed to **1 provision from a 267-page PDF** (unusable). Remediation: the ~20-document targeted delta crawl in §3.4a.

## 2.2 The funnel, measured

Full-corpus signature-keyword scan (script + results: session scratchpad `funnel_scan.py` / `funnel_scan_results.json`; single stream; per-indicator case-insensitive keyword nets from `INSTR/signatures/*.yaml`, matched over snippet + surrounding context). **Final re-measurement 2026-07-15 on the complete corpus (319,026 records = all delta + discovery layers extracted; only AU SOCI + 3 parse_failed remain broken)** — v2.3-partial values in ⟨brackets⟩ where they moved:

| Indicator (keyword net) | SG | AU | MY | Total |
|---|---|---|---|---|
| P6-I1 ban/local-processing | 2 | 12 | 40 | **54** (v2.0: 81) |
| P6-I2 local storage | 1,045 | 807 | 1,276 | 3,128 |
| P6-I3 infrastructure | 3 | 6 | **0** | **9 (unchanged since v2.0)** |
| P6-I4 conditional flow | 11,083 | 12,569 | 7,570 | 31,222 |
| P7-I1 DP framework | 314 | 887 | 220 | 1,421 |
| P7-I2 cybersecurity | 273 ⟨201⟩ | 70 | 80 | **423 ⟨345⟩** (v2.0: 216) |
| P7-I3 min. retention | 4,518 | 5,217 | 4,036 | 13,771 |
| P7-I4 DPO/DPIA | 465 | 198 | 134 ⟨117⟩ | 797 |
| P7-I5 gov access | 3,100 | 2,978 ⟨2,830⟩ | 3,340 | 9,418 |
| **≥1 indicator** | 19,197 | 21,524 | 15,440 | **56,161 provisions (60,243 pairs)** |
| ≥2 indicators | 1,552 | 1,191 | 1,214 | 3,957 |
| Corpus | 95,320 | 158,372 | 65,334 | 319,026 |

Shift notes across generations: v2.1 (delta re-extraction + 25 MY acts) moved MY P7-I5 +975, MY P6-I4 +1,195, MY P6-I1 −27 (map-all unchanged). v2.3 (15 regulator instruments) moved P7-I2 256→345 — the missing regulator layer landing exactly on the indicator that needed it. Final layer (17 §3.4a delta items) moved **SG P7-I2 +72 (CAA 2024's 187 provisions + FSM-N16 + S677), AU P7-I5 +148 (Assistance & Access Act, 613 provisions), MY P7-I4 +17 (DPO guideline)**. Total P7-I2 across the campaign: **216 → 423 (~2×)**. All design conclusions below survive every re-measurement; the P6-I4/P7-I3/P7-I5 big nets grew <5% total, so the banded caps stand as sized.

**What the measurements change (design refinements):**
- **P6-I1: map the entire net.** 54 keyword hits corpus-wide is *below* the planned 500/economy cap — every ban-candidate can go straight to Sonnet (+ dense-leg additions). The trap pair is fully covered cheaply; the volume lives on the P6-I4 side, as the methodology predicts.
- **P6-I3 is dense-leg-dependent — watch item.** 9 keyword hits total and **zero in Malaysia**, yet the indicator carries 31% of Pillar 6 and the baseline has an MY 6.3 row. The semantic leg (and the P6-I3 exemplar impacts as queries) must carry this indicator; if the dense candidates for MY 6.3 come back empty too, that's evidence *for* a legitimate "no provision found"/score-0 row — but it must be a verified absence, not a retrieval failure. Added to the risk register.
- **The big nets (P6-I4 31.0k, P7-I3 13.7k, P7-I5 9.3k) confirm banded selection.** Generic trigger words ("unless", "at least", "for a period of") inflate raw hits exactly as expected; BM25's IDF naturally down-weights them, and the caps + ranking cut to budget. The raw net is the recall ceiling, not the mapping volume.
- **Gray band re-sized: ~25–35k pairs** — the keyword pairs above `PREFILTER_FLOOR` not already selected into the direct band, plus dense-only candidates below the caps. ≈7–10 h of local triage **if** P2's measured 1.02 provisions/s tagging throughput holds per triage pair (an assumption — re-measure on a 200-pair sample on day 1); still one overnight run, with the floor as the tuning knob.

**The funnel at a glance:** 319,026 provisions → 2.87M scored pairs (free) → direct band (caps ≤9.7k; expected fill ~7–8k after measured keyword under-fill) + gray band (local triage, $0) → ~10–11k Sonnet-judged pairs → ~2.5–3k fires → verified → ~350–500 curated candidates → **~110–180 CSV rows**.

## 2.3 Tension 1 — funnel & triage · **Decision: 4-stage banded funnel with local-model triage**

- **S1 index:** BM25 (`bm25s`) over signature keywords + dense embeddings against indicator `definition_text` (+2–3 exemplar impacts), fused by RRF. Embedding text is **metadata-prefixed** (act title · jurisdiction · Part/section heading) — halves wrong-document retrieval on Australian legal corpora (arXiv:2510.06999, 2603.19251). Dense model: **Qwen3-Embedding-0.6B** recommended default (MLEB legal benchmark 77.13 vs BGE-M3's 69.44; Apache-2.0; CPU-capable), BGE-M3 stays the `.env` fallback — the swap is one config value (open question #5).
- **S2 selection:** per (indicator × economy) caps → direct band (cap ceiling 9,750; measured keyword under-fill on P6-I1/I3, P7-I1/I2/I4 puts expected fill at ~7–8k — Appendix A); next tranche above `PREFILTER_FLOOR` → gray band. Tag boosts never remove; gold-law allowlist is production-only and OFF for every reported recall number; Malay twins deduped.
- **S3 triage:** local **qwen2.5:14b** (measured 1.02 prov/s on the dev GPU → gray band overnight, $0), lenient binary relevance prompt; ~10–15% survive. **Gate:** 200-pair A/B vs Haiku on the SG slice; local false-negative rate <5% or fall back to Haiku (+$60–100).
- *Why triage at all:* the NEW points live in the lexical tail — "a third of the relevant laws are named 'Income Tax Act', 'Employment Act', 'Criminal Procedure Code'" (INSTR notes). Cutting the tail to save triage cost forfeits the 20-pt lever.
- *Named losers:* tight top-K straight to Sonnet (loses the tail); Haiku-maps-everything two-pass (doubles cost, and see §2.10 for the disciplined version of this idea).

## 2.4 Tension 2 — two-level mapping · **Decision: role-classify per provision; roll up per economy**

Per-provision schema (§2.9 S4) never emits economy scores. For P7-I1/I2 candidates it adds `role ∈ {horizontal_scope_provision, sectoral_framework_provision, not_relevant}` + scope facts. Then **6 roll-up calls** (3 economies × 2 indicators) see each cell's full deduped evidence, select controlling evidence (per "hierarchy resolves conflicts, never filters recording"), and emit the economy `score_hint` with polarity asserted by a schema-forced check ("comprehensive framework found ⇒ hint 0"). The other seven indicators roll up in code: max over verified rows + the official clauses (≥2-measure escalation for 6.1/6.2 only; 6.4 asymmetry; 7.4's 0.25 → flag). Sectoral rows get deterministic Notes: `"Recorded (sectoral) — controlling evidence for P7-I2 is Cybersecurity Act 2018; see row <id>"`. *Loser:* single-pass per-provision economy scoring — a snippet-sized window cannot decide a framework question, and it is exactly how the polarity trap fires.

## 2.5 Tension 3 — NEW/KNOWN diff · **Decision: 3-tier matcher, KNOWN-biased, human-eyeballed**

Match each surviving row against gold rows in the same (economy, indicator):
1. **Law match:** normalized names (whitespace collapse — the `Act\n14` fix; act-number canonicalization; amendment-suffix stripping), token-set fuzzy ≥ 0.85.
2. **Section match:** canonical roots (`s.26(1)` → `26`; never split `provision_id` on `#`) vs gold `articles_mentioned`.
3. **Verdicts:** law+section → **KNOWN** ("matches baseline <gold_id>" — kept; reproducing the baseline is explicitly rewarded). Law matched, section unrecorded, gold sections non-empty → **provision-level NEW**. Gold row prose-only → semantic fallback (embedding cosine ≥ 0.80 → KNOWN; ties → KNOWN). No law match in-cell → **instrument-level NEW**. `last_amended` postdating baseline currency + amendment-introduced text → **premium NEW** ("post-baseline amendment").

Conservatism: false-NEW before a judge who *knows the baseline* is a credibility error; JSON carries the match evidence (`discovery_match`: gold_id, tier, similarity); **every CSV NEW row is human-reviewed on 19 Jul** (est. 60–120 rows, one evening — protected time, open question #3). Expected NEW sources in order: unrecorded provisions inside baseline laws → sectoral instruments the baseline missed (7.3/7.5 tails) → post-baseline amendments (§3.4) → binding regulator notices/CoPs. *Losers:* embedding-only diff (baseline has no snippets — both over- and under-claims); law-level diff (forfeits the largest NEW class).

## 2.6 Tension 4 — Malaysia error-check · **Decision: 3 checks × 26 rows; methodological refutation for the parse_failed CoP**

Over all 26 MY gold rows: **(a) URL** — resolve with redirects recorded (pdp.gov.my rots; propose the corpus `source_url` or a Wayback snapshot as the Action); **(b) currency** — gold `timeframe` vs corpus `last_amended` / manifest `in_force_status` (the FSM-N16 supersession doctrine; A1727 commencements are prime targets); **(c) substance** — one Sonnet call comparing the gold impact text with the current corpus provision. The 2 suspect 7.3 rows: *PDPA Retention Principle = 1* refuted with the corpus's actual s.10 text (a maximum-period rule; Guide scores 0; SG's identical s.25 = 0 in the same baseline); *Communications CoP = 1* refuted **methodologically** — the doc is parse_failed (no corpus provisions), but the baseline row's own quoted text ("kept only as long as necessary", s.5.5) is a maximum-period rule, and the same baseline scored the identical banking-CoP pattern 0. A non-blocking re-parse request goes to P2 for the 2 CoPs; if it lands by 18 Jul the CoP provisions enter the normal funnel — otherwise the coverage grid marks them `parse_failed — checked at document level`. Output: `out/malaysia_errorcheck.csv` — `Baseline Entry | Retrieved Provision | Check Class (url/currency/score/indicator/citation) | Correct/Not-correct | Discrepancy | Action | Baseline Source | Main-CSV crossref`. *Loser:* fetch-and-parse inside P3 (violates the no-OCR/no-parsing boundary for 2 documents in the final 72 h).

## 2.7 Tension 5 — "No provision found" rows · **Decision: economy×indicator granularity**

CSV `no_provision` rows only for (economy × indicator) cells with zero verified evidence — expected **0–4 rows** — citing the governing law (name + number + official law-level URL from `laws.jsonl`), exactly the baseline's own practice (`r1-au-036`). The full 2,613×9 grid stays internal (`out/coverage_grid.csv`) as the "did you look?" proof for deck and audit. *Loser:* the literal policies.yaml reading — (governing law × searched indicator) ⇒ ~23k placeholder rows that bury ~150 substantive rows and invert judge-verifiability.

## 2.8 Tension 6 — CSV sizing & curation · **Decision: ~110–180 curated rows + overflow JSON**

Gates (deterministic, each decision logged to JSON `curation_reason`): keep all baseline-reproducing KNOWN rows (≤51); NEW rows need verifier-agreed confidence ≥ 0.75 + per-cell caps (≤8; ≤10 for 7.3/7.5, the sanctioned multi-row indicators) ranked by (verifier consensus, NEW tier, RRF); dedupe on (law, section root, indicator); English twin preferred; dual-indicator provisions = two cross-noted rows; P7-I1/I2 = 1 controlling + ≤3 recorded-sectoral rows per economy. Below-gate → `out/candidates_overflow.json` (full audit fields; cited in README/deck as discovery depth). Final validators: byte-exact quote re-assert, URL check as Notes-flag (never a rejection), whitespace collapse on all string columns, 13-column order, rationale ≤ 300, per-indicator allowed-score sets in JSON. *Rationale:* judges click every URL; ~150 verifiable rows with 60–120 defensible NEW beat 2,000 rows with broken links and one wrong-indicator row (the host's #1 risk). Composition: ≤51 KNOWN + 60–120 NEW + 0–4 absence rows ⇒ ~110–180. *Losers:* max-volume dump; 51-row baseline mimicry (caps the NEW lever at reproduction).

## 2.9 The 11 stages (with gates)

| # | Stage | Input → output | Engine | Gate |
|---|---|---|---|---|
| S0 | Ingest & grounding | handoff2 (streamed) → validated store + coverage grid | code | byte-exact quote assert per record (drop-loud); schema + MAJOR version check; 3 parse_failed enumerated |
| S1 | Prefilter index | store + signatures → RRF score per 2.75M pairs, cached | bm25s + Qwen3-Emb-0.6B (CPU/GPU, $0) | scores for 100% of provisions |
| S2 | Candidate selection | scores + boosts → direct band (caps ≤9.7k, ~7–8k fill) + gray band | code | **recall ≥ 0.95** on resolvable gold subset, allowlist OFF |
| S3 | Gray-zone triage | gray band → +~3k survivors | qwen2.5:14b local ($0) | 200-pair A/B vs Haiku, FN < 5%, else Haiku fallback |
| S4 | Mapping | ~10–11k pairs → schema-forced verdicts w/ trap booleans | Sonnet (Batch for AU/MY; live SG) | trap fixtures pass; s.26(1) → P6-I4 |
| S5 | Blind verify | fires (~2.5–3k) → verified + confidence | Haiku (blind) → Opus tiebreak | every fire carries a verifier verdict |
| S6 | Economy roll-up | verified rows → score_hints + roles + Notes | 6× Sonnet (7.1/7.2) + code | polarity assert; escalation/asymmetry asserts |
| S7 | NEW/KNOWN diff | rows + gold (first touch) → 3-tier tags + evidence | code + embeddings | no NEW without tier evidence |
| S8 | MY error-check | 26 MY gold rows → errorcheck CSV | URL checker + targeted Sonnet | 2 suspect rows adjudicated; 26/26 classed |
| S9 | Curate & emit | rows → 13-col CSV, records.json, audit HTML, overflow, cost report | code + **human NEW review** | 13-col validate; audit trio; whitespace fix |
| S10 | Eval | artifacts + gold → eval_report.json | code (allowlist OFF, R2-only exemplars) | honest recall/F1/verified-NEW for the deck |

**Traces.** *s.26(1):* S2 ranks it top-5 for both P6-I4 and P6-I1 (correct recall) → S4 trap check "compliant path exists" → fires P6-I4 only → S5 verifier agrees (0.9) → S7 law+section match → **KNOWN**, "matches baseline r1-sg". *MY Income Tax Act s.82:* gray band (act name suggests nothing) → S3 local model: plausibly 7.3 → S4 "not less than seven years" = floor → fires P7-I3 → S7 law present in baseline? (MY 7.3 gold cites it) → KNOWN or provision-NEW depending on section match — exactly the class where the tail pays.

## 2.10 Cost model & the lower-cost-model question

**Settled profile (15 Jul): batch-first + local triage — expected $150–260, hard ceiling $400.**

| Line | Volume | Engine | Cost |
|---|---|---|---|
| Triage | ~25–35k pairs (measured net; `PREFILTER_FLOOR` keeps survivors ≈3k) | qwen2.5:14b local, overnight | **$0** |
| Mapping | ~10–11k pairs | Sonnet — Batch (−50%) AU/MY, live SG slice | ~$125–210 |
| Blind verify | ~2.5–3k | Haiku, batched | ~$8–15 |
| Escalation | ~250–300 | Opus, batched | ~$15–30 |
| Roll-ups + error-check | ~30 | Sonnet | ~$3 |

**Can a lower-cost model do more?** Two honest answers:
1. **Local models (free): triage yes, mapping/verification no.** The verified evidence (Kickoff Decision 3): 16 GB-class open models cluster at 68–71% LegalBench vs Sonnet 83.9 — and the gap concentrates on the graded traps. P2's measured local tag agreement (46.6–80.6%) tells the same story. Mapping is the 40% substantive block; don't economize there with a local model.
2. **Haiku-first mapping (~$80–130 total) is a live option** — Haiku 4.5 scores 81.2 LegalBench at ⅓ Sonnet's price. Design: Haiku maps all ~10–11k pairs; Sonnet re-judges (a) everything that fires and (b) low-confidence non-fires; Opus stays the tiebreak. Risk: Haiku confidently missing a subtle conditional-transfer clause (never escalated → lost NEW row). **Resolution: a day-2 A/B for ~$10** — Sonnet vs Haiku on ~500 SG-slice pairs including all gold-law provisions; if Haiku's miss rate on gold-relevant pairs is ≈0 and trap fixtures hold, adopt Haiku-first; else stay Sonnet-first. The `.env` model spine makes this a config choice, not a rewrite.

**No API spend before the key is topped up.** Everything through S3 (scaffold, ingest, index, selection, local triage) plus this document, the scan, and all fixtures run at $0. First paid calls: the two day-2 A/Bs (~$10–15 total), then mapping.

## 2.11 Cost-scaling architecture (the sustainability story)

Three curve-benders, then the numbers:
1. **Caps bound marginal cost:** ~$50–90 per added economy (batched, local triage) regardless of statute-book size — corpus growth is absorbed by the free prefilter.
2. **Distillation cascade:** Round-1 produces ~10k graded verdicts → fine-tune a local model (permitted; weights published; Qwen base is Apache-2.0) → local handles the easy 70–80%, Claude only low-confidence/trap cases → **~$10–20/economy** at the Finale; unit economics improve with every economy mapped. First economy per *language* pays near-full price, then that language gets cheap too.
3. **Content-addressed deltas:** SHA-256 per document, frozen texts, cached embeddings/verdicts → re-runs pay only for changed/new provisions. **Bootstrap is one-time; staying current ≈ $5–20/economy/year** (a year of relevant legal change ≈ one amendment act + a few guidelines — Malaysia 2025 measured exactly that). The rubric's freshness requirement is this same delta loop, so it's a scored feature, not just savings.

| Scenario | Naive linear | Caps+batch+local triage | + cascade | Steady-state / yr |
|---|---|---|---|---|
| Round 1: 3 economies × 9 ind. | $360–585 | **$150–260** | — | ~$15–60 |
| Finale: 10 economies × 9 ind. | ~$1.2–2k | ~$500–900 | **~$150–350** | ~$50–200 |
| 20 economies × 9 ind. (≈½ non-English, ×1.5–2 those) | ~$3.0–5.9k | ~$1.3–2.7k | **~$0.6–1.3k** | ~$100–400 |
| Full: 24 economies × ~50 regulatory ind. | ~$16–26k | ~$4–7k | **~$1.5–3.5k** | ~$120–500 |

*Table = P3 mapping spend only; corpus acquisition (crawl/OCR/tagging) adds ≈$35–40/economy at measured Round-1 rates. "Naive linear" = live API, no caps/batch/local-triage, scaled linearly by economies × indicators.*

Local-language additions (Asia-Pacific): token inflation ×1.5–2.5 on non-Latin scripts (reading cost only); translated keyword packs ~$1–5/language (one-time); OCR stays local except hardest scripts (+$0–20/economy); "Verbatim (English)" column ~$1–3/economy (translations of emitted rows only); multilingual embeddings already handle cross-lingual retrieval at $0. The real non-English cost is QA effort: a hand-checked OCR reference page per script, longer human spot-checks. Note: "12 pillars" overstates the mapping surface — 15 indicators are officially non-regulatory (NONREG) and several pillars are formula/data-driven; ~50 regulatory indicators is the realistic ceiling. All figures above are replaced by the cost-meter's measured numbers as stages run.

## 2.12 Timeline & build-order deltas

**Prerequisite:** all documentation/files prepared before any API spend (done: this doc, scan, plan); **API key top-up gates day-2's A/Bs.**

| Date | Milestone |
|---|---|
| 15 Jul | Scaffold + config spine (T0) · S0 ingest + S1 index build overnight |
| 16 Jul | S2 recall gate (≥0.95, allowlist OFF) · triage A/B + mapper A/B (~$15) · SG slice S4–S5 |
| 17 Jul | SG verified end-to-end incl. audit HTML (START_HERE milestone held) |
| 18 Jul | AU + MY mapping/verification via Batch API · P2 re-parse deadline for the 2 CoPs |
| 19 Jul | S7 diff + S8 error-check + S9 curation · **human review of all NEW rows** · freeze candidate |
| 20 Jul | Final validate, package, submit (23:59 GMT+7) |

Deltas vs PLAN.md §11: T2 prefilter is built from `signatures/*.yaml` (not indicators-as-query) + banded selection; **new T2.5** = triage; T3 already superseded by Kickoff Decision 5 (messages.parse + trap_checks); T4's verifier is Haiku and the PLAN §4 **exclusive adversarial agent is cut permanently** (blind-verify + escalation supersedes it); **new T4.5** = economy roll-up; T6 diffs the real gold set from day one (`--baseline NONE`/proxy demoted to smoke tests); T8 no-provision granularity moves to economy×indicator; **new module** `output/curate.py` on the critical path.

## 2.13 Risk register

| Risk | Mitigation |
|---|---|
| False-NEW over-claiming (credibility with a baseline-fluent judge) | KNOWN-biased matcher + tier evidence in JSON + human review of every CSV NEW row |
| Wrong-indicator mapping (host's #1 error class) | schema-forced trap booleans + blind verify + trap fixtures in CI + roll-up polarity asserts |
| Local-triage false negatives | 200-pair A/B gate; Haiku fallback budgeted within the $400 ceiling |
| URL rot / offline judging | URL check is a Notes flag never a rejection; canonical permalinks; Wayback replacements; `url_cache.json` |
| The 2 parse_failed MY CoPs | methodological refutation path independent of parsing; non-blocking P2 re-parse request (deadline 18 Jul) |
| **P6-I3 invisible to keywords** (9 hits corpus-wide, MY = 0) despite 31% pillar weight | dense leg seeded with P6-I3 exemplar impacts; MY 6.3 dense candidates manually reviewed; an empty cell is emitted only as a *verified* absence row, never assumed from retrieval silence |
| **Acts-only crawl scope** (no subsidiary legislation/regulator instruments; 10 of 14 NEW leads + 7 gold instruments absent; SG CA2018 stale; AU SOCI unusable) | **⤷ RESOLVED 2026-07-15 (corpus v2.2/v2.3):** all 18 delta-request items fetched + a P1 discovery sweep added 15 regulator instruments (2,673 docs, validate clean). **Residual disclosed gaps (3, all with documented reasons):** BNM RMiT (bnm.gov.my serves HTTP 202 to non-browser clients — fetch attempt logged as evidence; manual browser grab possible), IMDA Telecom Cybersecurity CoP (text not published as a document), MCMC INSG Dec 2024 (no stable official URL). These three are disclosed in the Notes column if cited, never claimed as mapped. Only remaining upstream work: P2 re-parse of the 3 parse_failed docs |
| Batch API latency on 18 Jul | batches typically <1 h; submit early on the 18th; live path is the fallback |
| Budget overrun | run-level cost meter with `$400` hard stop + per-doc guardrail |
| Solo-builder time crunch | slice-first order (SG end-to-end by 17th) protected over breadth, per PLAN staging |

---

# Part 3 — External tools & prior art (web research, 2026-07-14)

## 3.1 Adopt / consider / reject

| Item | Verdict | Evidence / cost |
|---|---|---|
| **Qwen3-Embedding-0.6B** as dense leg (BGE-M3 → `.env` fallback) | **Adopt** (open question #5) | MLEB legal benchmark (arXiv:2510.19365, incl. SG+AU datasets): 77.13 vs BGE-M3 69.44 NDCG@10; Apache-2.0; sentence-transformers drop-in; ~2–4 h |
| Metadata-prefixed embedding text (act · jurisdiction · heading) | **Adopt** | Halves document-level retrieval mismatch on AU legal (arXiv:2510.06999, 2603.19251); free |
| In-house Commonwealth citation regex (s.26(1)(a) · Art. 12(2) · Cap. 50) | **Adopt** | No maintained parser exists: eyecite is US-only; Blackstone dead (spaCy-2, 2019); seed from Free Law Project `citation-regexes`; ~6–12 h |
| Rule-based repealed/superseded flags from in-force markers | **Adopt** | Portals encode status typographically; no ML needed; ~3–5 h |
| Wayback Availability API + canonical permalinks (legislation.gov.au `/latest/text`; SSO `/Act/<Name>` + `?ProvIds=`) + HEAD→GET liveness | **Adopt** | Trivial integration; directly serves the click-every-URL judging loop |
| Dynamic MMR few-shot exemplar selection + exemplar cap | Consider | Guards many-shot degradation (arXiv:2404.11018); reuses the embedding index; ~3–6 h |
| LLM-generated per-document summaries for embedding | Consider | SAC evidence is contracts-not-statutes; pilot on a held-out slice if time |
| voyage-law-2 / Kanon 2 embedders | Reject | Top legal scores but closed/API — fail the open-weight rubric |
| Blackstone / eyecite as dependencies; HyDE default; GraphCompliance; semantic hallucination classifiers | Reject | Dead/US-only; CPU-hostile; build cost beyond 20 Jul; weaker than our byte-exact grounding |
| Agent frameworks (LangGraph/DSPy/Haystack) | Reject | A linear, deterministic, auditable 5-day pipeline is *more* auditable in plain Python + the Anthropic SDK |

## 3.2 Design validation worth citing in the submission

- **MIT AI Risk Repository governance-mapping study (Oct 2025):** LLMs classifying 950+ legal/governance documents against indicator taxonomies reached κ 0.61–0.80 — Opus-class models *exceeded* the human–human agreement baseline; they shipped on a Sonnet-class model after an Opus pilot; documented failure mode "overstates coverage at medium confidence" → our blind verifier + confidence gate. Validates the exact map→verify→escalate economics.
- **Anthropic Citations + RAGTruth:** first-party and benchmark validation that span-level grounding is the standard — ours (byte-exact offsets, deterministic) is the *hard* version of that guarantee.
- **Hybrid sparse+dense retrieval on legal corpora** (arXiv:2603.19251): the pattern our RRF fusion implements, with measured DRM reductions on Australian legal text.

## 3.3 Prior art & novelty

Methodology precedents to cite: **EUI Digital Trade Integration DB** ("Turning Regulation into Data", CEPR DP21599) — the closest analog for coding legal text into trade indicators; **OECD Digital STRI** (binary indicator + source citation + comment = our 13-column shape); **Digital Policy Alert Handbook** (documented digital-policy taxonomy, human-reviewed events); UNCTAD cyberlaw tracker (coarse cross-check). **No published LLM automation of DTRI/RDTII-style legal indicator coding was found — the pipeline is genuinely novel**; frame it that way to judges. Public RDTII assets: guide PDF (dtri.uneca.org), ESCAP databases/dashboard page (bot-blocked — verify export format manually on day 1), the 2025 AP/ASEAN regulatory-review PDFs (parseable cross-check baselines).

## 3.4 Post-baseline NEW-evidence lead list (verify each against corpus + baseline before tagging)

| Economy | Development | In force | Feeds | Status vs baseline |
|---|---|---|---|---|
| MY | PDP (Amendment) Act 2024 (A1727) — phased 1 Jan / 1 Apr / 1 Jun 2025 | 2025 | multiple | act likely KNOWN; commencement dates = error-check targets |
| MY | → **new DPO duty** (controller *and* processor) | 1 Jun 2025 | **P7-I4** | **premium NEW** (would flip MY 7.4) |
| MY | → mandatory breach notification (s.12B, ≤72 h) | 1 Jun 2025 | DP | NEW |
| MY | → s.129 whitelist repealed → "substantially similar / adequate protection" regime | ~1 Apr 2025 | **P6-I4** | **NEW** (regime change on a KNOWN row) |
| MY | PDPD **Cross-Border Transfer Guidelines GP 3/2025** (TIA prescribed as the s.129 adequacy-assessment method; guideline wording is permissive — "may conduct" — with findings valid ≤3 yrs) + DPO Appointment + Breach Notification guidelines | 29 Apr / 1 Jun 2025 | P6-I4, P7-I4 | **highest-value NEW** |
| MY | Cyber Security Act 854 + licensing regs | 26 Aug 2024 | P7-I2 | likely KNOWN; subsidiary regs possible NEW |
| SG | Cybersecurity (Amendment) Act 2024 — most provisions commenced **31 Oct 2025** (S677/2025); Parts 3C/3D **not in force** | Oct 2025 | P7-I2 | NEW commencement; 3C/3D = enforced-only trap |
| SG | PDP (Statutory Bodies)(Amendment) Notification S217/2025; 2025 PDPC advisories (AI systems, children); Data-Portability Part 6B **enacted, not in force** | 2025 | DP | NEW leads; Part 6B must NOT be scored |
| AU | Cyber Security Act 2024 — ransomware-payment reporting commenced **30 May 2025** (F2025L00278); enforcement Phase 2 from 1 Jan 2026 | 2025–26 | P7-I2-adjacent | **NEW** |
| AU | Privacy and Other Leg. Amendment Act 2024 — statutory privacy tort 10 Jun 2025; ADM transparency deferred to 10 Dec 2026 (**not in force**) | 2025 | P7-I1-adjacent | NEW / trap |
| AU | SOCI amendments — data-storage systems holding business-critical data in scope; rules Apr 2025 | 2024–25 | P6-adjacent | NEW-ish |

**⚠️ Audit correction (2026-07-14): most of these are NOT in the corpus.** The crawl-sufficiency audit (§2.1) found only 4 of 14 present — the corpus contains no subsidiary legislation at all. Without a delta crawl, the premium-NEW claims above reduce to what the consolidated/parent acts carry (A1727's merged provisions, AU Cyber Security Act 2024's 290 provisions).

**⤷ v2.1 update (2026-07-14 evening):** the refreshed P1/P2 delivery closes part of this. Now in-corpus: **MY A1727 as `my-pdpa2024-001`** (DPO duty s.6 → P7-I4 premium NEW; breach notification; s.129 regime change s.10 → P6-I4 NEW), **SG CA2018 consolidated** (338 provisions incl. post-2024 content → the SG P7-I2 NEW-commencement claim is now evidenceable from the corpus), plus bonus 2025 MY acts (Data Sharing Act 2025, Online Safety Act 2025) worth screening as NEW leads. **Still missing (acts-only crawl persists):** all regulator/subsidiary instruments — MY GP 3/2025 + DPO/breach guidelines + Act 854 P.U.(A) regs, SG S677/S217/PDP Regs 2021, AU F2025L00278 — and AU SOCI still parses to 1 provision. The §3.4a delta request below remains live for exactly those items.

**⤷ P3 verification note (2026-07-15, measured):** at the v2.3-partial handoff2 (317,903 provisions / 2,653 laws), **all 15 discovery instruments are extracted with provisions** (au-pac2017-001 n=14 · TSRMP n=30 · credit code n=173 · CPS 234 n=35 · CPS 230 n=60 · CIRMP n=68 · smart devices n=29 · S678/2025 n=15 · CII Regs 2018 n=22 · CCoP n=11 · MAS TRM n=15 · SG breach regs S64/2021 n=26 · MY PDP Regs 2013 n=11 · SC GTRM n=4 · exemption order n=2). Thin extractions to sanity-check at S0: SC GTRM (4 provisions from a long guideline) and CCoP (11 from 65 pp).

**⤷ CORPUS COMPLETE (2026-07-15, P2 delta run verified by P3):** handoff2 now holds **319,026 provisions / 2,670 laws** (+3 parse_failed rows in doc_status.jsonl = 2,673 = P1's manifest, arithmetic exact). All 17 remaining delta doc_ids extracted and measured: `au-tolaa2018-001` A&A Act **n=613** · `au-tr2021-001` Telecom Regs n=131 · `sg-ca2024-001` Cybersecurity (Amdt) Act n=187 · `sg-pdpr2021-001` PDP Regs 2021 n=46 · `sg-mnfnch-001` FSM-N16 n=10 · `sg-can2025-001` S677 n=2 · `sg-pdpn2025-001` S217 n=2 · `sg-agpcspd2024-001` children's guidelines n=15 · `my-pdpgcbpdt2025-001` GP 3/2025 n=16 · `my-pdpgadpo2025-001` DPO guideline n=16 · `my-pdpgdbn2025-001` breach guideline n=22 · `my-pdps2015-001` PDP Standard 2015 n=14 · 4× Act 854 regs (15/5/11/3) · `au-csr2025-001` ransomware rules n=15. **Sole remaining broken doc: `au-scia2018-001` (SOCI) — P2's re-run took the PDF lane again (`source_type_final: pdf_native`, n=1) despite P1's HTML re-issue; needs a P2 lane override (route C2018A00029 to the HTML parser).** The 3 parse_failed docs are unchanged.

**⤷ v2.2/v2.3 update (2026-07-15):** the paragraph above is now history — **all 18 delta-request items were fetched by P1 (v2.2)**, and a P1 discovery sweep of the regulator layer (16 searches: pdpc/imda/mas/csa · pdp/mcmc/bnm/sc/nacsa · oaic/acma/apra/cisc + both SL registers) **added 15 more verified official instruments (v2.3: 2,673 docs, SG 536 / MY 869 / AU 1,268, validate clean)**. Additional post-baseline NEW candidates from the sweep (doc_ids in P1 report Addendum 3; verify text in-corpus before tagging, per this section's standing rule): SG Cybersecurity (CII)(Amendment) Regulations 2025 (S 678/2025); AU SOCI Telecom-Security-and-RMP Rules 2025 (telecom sector moved under SOCI, commenced 4 Apr 2025 → P7-I2); AU Smart-Devices Security Rules 2025; AU Privacy (Credit Reporting) Code 2024 (in force 1 Oct 2024); AU CPS 230 (commenced 1 Jul 2025); MY Cyber Security (Exemption) Order 2025; MY SC Guidelines on Technology Risk Management (revised ed. effective 19 Aug 2024). **Topic-8 direct hit:** AU Privacy (Australian Government Agencies — Governance) APP Code 2017 (`au-pac2017-001`) imposes a *mandatory PIA duty* on all federal agencies → P7-I4 candidate the baseline may have missed. KNOWN-grounding additions: SG CII Regs 2018 + CSA CCoP 2.0 + MAS TRM Guidelines, MY PDP Regulations 2013 (P.U.(A) 335, scanned→OCR lane), AU CIRMP Rules 2023 + CPS 234. Disclosed residual gaps: BNM RMiT / IMDA telecom CoP / MCMC INSG (see risk register §2.13).

### §3.4b Adversarial verification of the 15 v2.3 instruments (15-agent pass over extracted provisions, 2026-07-15; full verdicts: session scratchpad `v23_verification_verdicts.json`)

| Instrument | Verdict | What it means for mapping |
|---|---|---|
| SG S 678/2025 CII (Amdt) Regs | ✅ confirmed, **in force 31 Oct 2025 on the face of the text** | Premium NEW with in-corpus commencement evidence; frame as *material update to the 2018 sectoral framework*, not a new framework |
| SG CII Regs 2018 | ✅ binding; crawled copy is the **post-S678 consolidation** (deleted provisions marked) | KNOWN grounding; the audit duty lives in the parent Act s.15, not here |
| SG CCoP for CII | ✅ binding effect clause in text | 0.5-class sectoral P7-I2; "offence" enforcement sits in the parent Act, don't overclaim |
| **SG MAS TRM Guidelines** | ⚠️ **GUIDANCE-ONLY confirmed** — every operative clause is "should" + express self-disclaimer | **Never cite as controlling P7-I2 evidence** — record-only; the binding MAS instrument is Notice FSM-N16 (fetched, pending P2) |
| SG Breach Regs S 64/2021 | ✅ binding; thresholds present, timelines not in extract | P7-I1 grounding; deadline citations must come from PDPA s.26D itself |
| **MY Cyber Security (Exemption) Order 2025** | ✅ binding, in force **1 Feb 2025**: exempts **nine named companies (the major hyperscale cloud operators) from ALL of Act 854** | Double-edged: a strong post-baseline NEW row *and* a scope caveat on MY P7-I2 — Act 854 coverage of CSPs is refuted for those entities |
| MY A1727 (re-verified) | ✅ DPO duty (controllers *and* processors) + harm-qualified breach notification confirmed | Commencement is by-gazette-per-provision — in-force evidence stays external; cite the amendment act's section, not "s.129", from our extract |
| MY PDP Regs 2013 | ✅ binding, in force 15 Nov 2013; **text is English, not Malay** (fix metadata) | P7-I1/P6-I4 grounding; reg 7 is a *disposal* regime — **NOT P7-I3** (trap confirmed) |
| MY SC GTRM | ⚠️ CANNOT-TELL-grade: extraction thin (4 blocks, only the AI/ML principles section), hortatory language | S0 sanity-check target; don't use until re-extracted |
| AU TSRMP Rules 2025 | ✅ telecom-under-SOCI confirmed (s.61 rules switching on Part 2A) | P7-I2 sectoral NEW; commencement formula is conditional in text (4 Apr 2025 needs external confirmation) + 6-month obligation deferral — enforced-only check at scoring |
| AU CIRMP Rules 2023 | ✅ (verified within TSRMP pass) | KNOWN grounding for SOCI risk-management |
| AU Smart-Devices Rules 2025 | ✅ binding; substantive standards commenced **4 Mar 2026** (in force now) | Consumer-products-only scope; NEW row with careful reference-date note |
| **AU Privacy (AGA—Governance) APP Code** | ⚠️ PARTIAL — binding character confirmed, but the PIA-duty text is **headings-only in our extract** (ss.13–15 missing entirely) | S0 sanity-check/re-extraction target **before** any P7-I4 claim; duty is likely threshold-conditioned (high-privacy-risk projects) |
| AU CPS 234 | ✅ binding, commenced 1 Jul 2019 | 0.5-class sectoral P7-I2 KNOWN grounding; APRA incident-reporting ≠ P7-I5 |
| AU CPS 230 | ✅ binding, commenced 1 Jul 2025 in text | Sectoral NEW-ish; "CPS 230" designation inferred (not in extract); transitional to Jul 2026 for pre-existing contracts |
| AU Credit Reporting Code 2024 | ✅ binding sectoral P7-I1; **P7-I3 trap confirmed live** — s.1A is a destruction (max) regime; only s.22(3) holds a narrow genuine 5-yr *minimum* for compliance records | Exactly the max≠min discrimination the trap_checks schema exists for |

Cross-cutting: 4 instruments have deferred/phased application (TSRMP, smart devices, CPS 230, S678-consolidation deletions) → the **enforced-only check must run per-provision at mapping time, not per-instrument**. Three thin extractions (GTRM 4, CCoP 11, AGA Code 14 TOC-heavy) go on the S0 sanity-check list.

### §3.4c Round-2 verification: the 17 delta instruments (17-agent pass, 2026-07-15; full verdicts: scratchpad `v24_verification_verdicts.json`)

| Instrument | Verdict | What it means for mapping |
|---|---|---|
| SG PDP Regs 2021 (`sg-pdpr2021-001`) | ✅ binding, in force 1 Feb 2021; **regs 9–12 are the operative s.26 transfer conditions** | P6-I4 grounding solid. Nuance: SG has *no adequacy/whitelist mechanism* — the standard is "legally enforceable obligations" |
| AU A&A Act (`au-tolaa2018-001`, n=613) | ✅ binding, assent 8 Dec 2018; TAN/TCN compulsory, **TAR is voluntary**; s.317ZH warrant carve-out | P7-I5 gold grounding (r1-au-044). Cite as *Telecom Act 1997 Part 15 as inserted*, not the amending act's own sections |
| **AU Telecom Regs 2021** (`au-tr2021-001`) | ⚠️ PARTIAL — only *weak* P7-I5 content (ACMA research-scheme disclosure); Part 4 items are disclosure *exceptions* | **Gold row r1-au-044's citation of this instrument is weak** — core gov-access powers live in the TIA Act / Telecom Act Pt 13. Error-check-adjacent finding |
| SG S 677/2025 (`sg-can2025-001`) | ✅ binding, **in force 31 Oct 2025 in-text**; commences the CAA 2024 *except* a listed set of omitted sections | Partial commencement confirmed — never cite as bringing the whole Act into force; the omitted-sections list is the enforced-only evidence |
| SG CAA 2024 (`sg-ca2024-001`, n=187) | ⚠️ PARTIAL — expansion confirmed (STCC, ESCI, foundational digital infrastructure, new s.18F breach-reporting) but no in-text commencement, "cloud"/Third Schedule absent, **extraction labels defective from Part 3B onward** | Premium NEW stands (pair with S677 for dates); S0 sanity-check the labels before citing exact sections |
| SG S 217/2025 (`sg-pdpn2025-001`) | ✅ binding, in force 1 Apr 2025 | Minor scope housekeeping — record-grade, not framework-event NEW |
| SG FSM-N16 (`sg-mnfnch-001`) | ✅ binding ("shall"), takes effect 10 May 2024 | The controlling sectoral P7-I2 instrument for the host's SG 7.2 worked example. Scope caveat: designated financial holding companies, not all FIs; title "FSM-N16" not in text |
| SG children's guidelines (`sg-agpcspd2024-001`) | ⚠️ GUIDANCE-ONLY + extraction is Annex-A-only | Gold r1-sg-046 cites it for P7-I4 → treat as guidance-grade; re-extraction needed before quoting operative text |
| **MY PDP Standard 2015** (`my-pdps2015-001`) | ⚠️ **CANNOT_TELL — the extraction holds only the Security Standard; the Retention Standard section is entirely absent** | The r1-my-053 error-check cannot quote this doc either way yet → refutation stays anchored on PDPA s.10 + Guide FAQ; request P2 re-extraction if we want the direct quote |
| MY GP 3/2025 (`my-pdpgcbpdt2025-001`) | ✅/PARTIAL — TIA is **"may conduct"** (permissive trigger), steps "shall", record-keeping "must" (quasi-mandatory backstop); issued under s.48(g) | P6-I4 premium NEW stands (the binding conditions sit in s.129 itself); never call the TIA "mandatory"; effective date + 3-yr validity not in extract (truncated) |
| MY DPO guideline (`my-pdpgadpo2025-001`) | ⚠️ GUIDANCE-ONLY, extraction TOC-heavy | Binding anchor for P7-I4 is **s.12A Act 709** (via A1727); guideline is operational color; 1 Jun 2025 date needs external evidence |
| MY breach guideline (`my-pdpgdbn2025-001`) | ⚠️ extraction is the notification *form* only | Same pattern: score off A1727's s.12B, not this file |
| MY Act 854 regs ×4 | ✅ binding, all in force 26 Aug 2024; incident regs: notify **immediately** + 6 h initial particulars + 14 d supplementary | P7-I2 subsidiary NEW; compounding reg = enforcement machinery only (don't double-count); licensing scope = MSOC monitoring + pen-testing only |
| AU Ransomware Rules (`au-csr2025-001`) | ✅ binding; **the duty lives in Part 3 of the Cyber Security Act — the Rules prescribe the A$3m turnover threshold** and report content | Cite Act+Rules together; 30 May 2025 commencement is a conditional formula in-text — confirm externally |
| AU SOCI (`au-scia2018-001`) | ❌ re-confirmed broken: 1 provision of editorial boilerplate | The only unusable major act; P2 lane-override fix pending |

Round-2 cross-cutting: **the guideline-class PDFs extract badly** (TOC/form/annex-only: both MY PDPD guidelines, SG children's guidelines, MY PDP Standard 2015; label defects in SG CAA 2024) — a P2 extraction-quality pattern, not a crawl gap. None of it blocks scoring (every binding anchor sits in an act/regulation that extracted cleanly).

### §3.4d Caution triage → build rules (measured 2026-07-15; supersedes the warnings above)

**Finding 1 — every "missing" section exists in `source_text/` (verified by direct grep of the raw texts):** PDP Standard 2015 → *Retention Standard* present (+ disposal terms — the r1-my-053 refutation quote is recoverable); GP 3/2025 → **"three (3) years"** TIA validity *and* **"29 April"** effective date present; DPO guideline → **"shall appoint"** + the **20,000**-subject threshold present; breach guideline → "72 hours" / "shall notify" / "significant harm" / "seven (7) days" present; children's guidelines → DPIA content present; SG CAA 2024 → Part 3C/3D ×9, "foundational digital infrastructure" ×102, Third Schedule present; **AU SOCI → the full act text is in `au-scia2018-001.txt` (388,847 chars: Part 2A ×36, "risk management program" ×78, s.30A ×44) — the HTML fetch succeeded; only P2's segmentation failed.**

**Build rules this creates:**
1. **S0 special-doc index:** the 7 flagged docs (`my-pdps2015-001`, `my-pdpgcbpdt2025-001`, `my-pdpgadpo2025-001`, `my-pdpgdbn2025-001`, `sg-agpcspd2024-001`, `sg-ca2024-001`, `au-scia2018-001`) get a direct keyword+dense pass over their **source_text** in addition to their (thin) provisions, so S1/S2 candidate discovery cannot miss content that exists only in raw text.
2. **Curation-time quote protocol:** any CSV quote from these docs is located and byte-grounded against `source_text/<doc_id>.txt` (the contract's `snippet_source`/`source_file_path`/char-offset fields exist for exactly this), never against a thin provision record.
3. **SOCI fallback:** the P2 lane-override remains the right fix, but it is no longer a blocker — worst case SOCI is mapped from its source text as a special doc with byte-grounded quotes.

**Finding 2 — third-party-source audit (all 2,670 laws.jsonl rows, by URL host): 100% official government hosts.** legislation.gov.au 1,265 · lom.agc.gov.my 856 · sso.agc.gov.sg 531 · nacsa.gov.my 5 · pdp.gov.my 5 · pdpc.gov.sg 2 · mas.gov.sg 2 · sc.com.my 1 · apra.gov.au 1 · oaic.gov.au 1 · isomer-user-content.by.gov.sg 1. Zero non-government hosts.

**Source-policy rules (submission-facing):**
1. **Evidence = official hosts only** (satisfied corpus-wide, above). Secondary sources (law-firm alerts, IAPP, news) were used **only as discovery leads** during the P1 sweep and are never cited as evidence; if a lead's official text could not be fetched (BNM RMiT, IMDA CoP, MCMC INSG), the instrument is **disclosed, not claimed**.
2. **Canonical-URL rule at curation:** cite the canonical regulator/register page, not CDN or file-dump links — the one case in-corpus is `sg-ccpcii-001` (Isomer CDN link, official GovTech infrastructure): CSV cites the csa.gov.sg code-of-practice page; the CDN URL stays in the JSON as the access record.
3. **External-date rule:** commencement dates not present in any official text we hold (e.g. GP 3/2025's 29 Apr 2025 — now actually in-text; MY A1727's phased gazette dates — still external) are cited to the official gazette/register entry, with the Notes column disclosing the source; a date with no official citation does not go in the CSV.

### §3.4a Targeted delta-crawl request (to P1, ~20 single-document fetches, all URLs known)

Priority order: **(1) NEW-lever instruments** — SG: `sso.agc.gov.sg/SL-Supp/S677-2025/Published/`, `SL-Supp/S217-2025/Published/`, `SL/PDPA2012-S63-2021`, `Acts-Supp/19-2024/Published/` (Cybersecurity Amendment) + **re-crawl consolidated `Act/CA2018`** (current copy is as-enacted 2018); MY: the three 2025 pdp.gov.my guideline PDFs (cross-border GP 3/2025, DPO, breach) + the four Act 854 P.U.(A) regulations; AU: `legislation.gov.au/F2025L00278/latest/text` (ransomware rules) + **re-crawl SOCI Act as `/C2018A00029/latest/text` HTML** (PDF parse failed, 1 provision). **(2) Error-check/gold completeness** — MY PDP Standard 2015; re-parse the 2 crawled MY CoPs + au-piag-001; AU Assistance & Access Act 2018 + Telecom Regulations 2021; SG PDPC children's-data guidelines. Most are native PDFs or legislation.gov.au HTML — lanes P2 already parses; the earlier CoP failures were pdp.gov.my *HTML pages* without a portal parser, while the 2025 guidelines are *PDF files* (native lane).

---

# Part 4 — Open questions for discussion

1. **CSV volume:** approve the curated ~110–180-row CSV with `candidates_overflow.json` as a non-contract extra — or must every mapped row ship in the judged CSV?
2. **Parse_failed MY CoPs:** accept the methodological refutation for the Communications-CoP suspect row, or push P2 for a re-parse by 18 Jul (both are prepared)?
3. **NEW review time:** the human eyeball of all CSV NEW rows (est. 60–120, evening of 19 Jul) — is that time protected?
4. **P7-I1/I2 CSV shape:** 1 controlling + ≤3 recorded-sectoral rows per economy; `score_hint` JSON-only — confirm.
5. **Embedding swap:** adopt Qwen3-Embedding-0.6B as default dense leg (BGE-M3 remains the `.env` fallback) — revises Kickoff Decision 4 on MLEB evidence.
6. **Mapper A/B:** if Haiku-first passes the day-2 gold-slice A/B (miss-rate ≈0 on gold-relevant pairs, traps hold), adopt it (→ ~$80–130 total)?
7. **NEW-lead priority:** treat §3.4 as the priority verification list for 18–19 Jul?
8. **Delta crawl (from the 2026-07-14 crawl audit):** approve sending P1 the §3.4a ~20-document fetch list (deadline 17–18 Jul)? It unlocks 10 currently-impossible premium-NEW claims, fixes the stale SG Cybersecurity Act and the broken AU SOCI Act, and closes 7 gold-instrument gaps. Without it the pipeline still runs and scores — but the NEW headline rests on within-act discoveries only.

*(Resolved on 15 Jul: budget profile = batch-first + local triage, expected $150–260, hard ceiling $400; all docs/files prepared before API top-up; nothing billed runs until the key is funded.)*

---

## Appendix A — Per-cell direct-band candidate budgets (per economy)

| Indicator | Cap | Rationale |
|---|---|---|
| P6-I1, P6-I4 | 500 each | trap pair; 6,297 cross-border pre-flags; highest mis-mapping risk |
| P6-I2 | 300 | storage-copy language rarer |
| P6-I3 | 200 | narrow after licensing/operations exclusions; but 31% weight — don't starve |
| P7-I1 | 150 | economy-level; scope provisions only |
| P7-I2 | 200 | dedicated acts + sectoral frameworks |
| P7-I3, P7-I5 | 600 each | the multi-row, NEW-rich tails (tax/employment/telecom; CPC/surveillance) |
| P7-I4 | 200 | DPO/DPIA language lexically distinctive |
| **Total** | **caps ≈3,250/economy (9,750 ceiling)** | Caps are **upper bounds**: the measured keyword nets under-fill several cells (P6-I1 81 hits corpus-wide, P6-I3 9, P7-I2 216, P7-I4 754, P7-I1 1,326), so expected direct fill ≈ **7–8k**; + ~3k triage survivors ≈ **10–11k mapped pairs** |

## Appendix B — `malaysia_errorcheck.csv` columns

`Baseline Entry (gold_id · law · indicator · baseline score)` | `Retrieved Provision (provision_id · article_section)` | `Check Class (url / currency / score / indicator / citation)` | `Correct / Not-correct` | `Discrepancy` | `Action (corrected score / replacement URL / successor instrument / add-missing)` | `Baseline Source` | `Main-CSV crossref`. Expected: ≥2 Not-correct (the suspect 7.3 pair), 1–4 URL/currency actions, remainder Correct; contradictions mirrored into main-CSV col 13.

## Appendix C — Sources consulted

**Official:** GUIDE (130 pp) · INT (15 pp) · NONREG (5 pp) · QA (3 pp) · KB · ANSKEY (3 pp) · FMT (4 pp) · SLIDES (59) · R1DB · R2DB · Legal Inventory CSV (384 rows) · TEMPLATE. **Project:** INSTR (indicators/policies/9 signatures/57 exemplars/51-row gold set) · `Desktop\handoff2` (measured directly) · PLAN.md · KICKOFF_DECISIONS · FOUNDATION_SYNC · HANDOFF2_NOTES · Target_Output_Summary · Scoring_Criteria. **Web (primary sources cited inline):** MLEB (arXiv:2510.19365) · SAC (2510.06999) · metadata-RAG (2603.19251) · Many-Shot ICL (2404.11018) · MIT AI-Risk mapping study · Anthropic Citations · RAGTruth · EUI DTI / CEPR DP21599 · OECD Digital STRI · Digital Policy Alert Handbook · Wayback Availability API · legislation.gov.au + SSO permalink conventions · MY PDPD (A1727 + GP 3/2025) · SG SSO (19/2024, S677/2025, S217/2025) · AU Home Affairs / F2025L00278.
