# 1 · Target Output Summary

**Team:** Rocky has a home run · **Member:** John (Jiaxiang) Chen
**Round 1 deadline:** 20 July 2026, 23:59 GMT+7 (Bangkok) · **Live demo:** 3 August 2026
**Sources of truth:** RDTII 2.1 Guide + `Round 2 Database.xlsx` methodology sheet (indicator definitions) · `OUTPUT_TEMPLATE_31MAY.xlsx` (output schema) · organizer email 19 June + final Q&A (authoritative).

> This document defines *what we must produce* and *what "excellent" looks like*. Read alongside [2_Scoring_Criteria.md](2_Scoring_Criteria.md) (how it's judged) and [3_Division_of_Tasks.md](3_Division_of_Tasks.md) (how we build it).

---

## 1. What we deliver

**Four artifacts uploaded to the JotForm portal by 20 July** (the live demo is a separate 3 Aug event, *not* a 20 July upload):

| # | Deliverable | Format | The bar |
|---|---|---|---|
| 1 | **Functional Prototype** | GitHub repo + Quick Start README | A reviewer with basic Python sets up and runs it in <10 min on a **standard CPU box**, no help from us. Runs Task 1 (discover) + Task 2 (map) end-to-end, no manual steps. |
| 2 | **Structured Output File** | one consolidated CSV **+** JSON | The extracted records for SG/AU/MY, Pillars 6 & 7. Exact 13-column schema (§3). Read by non-technical judges too. |
| 3 | **Technical Pitch Deck** | slides | Problem–solution fit + our extraction/mapping logic for Task 1 & Task 2. Non-technical judges included. |
| 4 | **Screen-recording Walkthrough** | video, **≤10 min** | The engine processing a **scanned/image PDF** and generating correct citations. |

**5th (3 Aug, if shortlisted):** Live Demo + Interview — the engine runs and produces output *in real time*. Not a slideshow.

---

## 2. The engine contract ("what 'runs' means")

```
Input:  a country + a topic/pillar   (e.g. python main.py --economy Singapore --pillar 6)
Output: outputs/Singapore_P6_<timestamp>.csv  +  .json   (+ logs/)
Between: NO manual steps.
```

- Crawls **live official government portals** → retrieves the law (text PDF, **scanned/image PDF**, or **HTML**) → extracts provisions at article level → maps each to an RDTII indicator → emits a fully-cited row.
- Works on **both** text PDFs and scanned PDFs, **and** HTML (HTML is the harder, higher-value target).
- Handles unanticipated input (mis-spelled country, edge cases) without crashing.
- If a commercial API is used, a **switchable open-source fallback** exists (config value, not a rewrite).
- **Freshness:** not a static snapshot — the tool must be able to detect newly released/amended documents (the DB is current to 2025–early 2026; new finds are possible and highly rewarded).

**Economies (Round 1, all English):** Singapore, Australia, Malaysia. (Malaysia additionally = error-check existing entries + new collection.)
**Pillars (mandatory):** 6 (Cross-border Data Flows) and 7 (Domestic Data Protection).

---

## 3. Output schema — build to this exactly

Primary = **CSV** (opens in Excel, filterable row-by-row for the policy judge). Supplementary = **JSON** (richer metadata for the technical judge). **Do not rename or reorder columns — judges validate programmatically.** One consolidated file for final submission (P6 + P7 merged), not one file per pillar.

### CSV — 13 columns, this order

| # | Column | Req. | Content |
|---|---|---|---|
| 1 | `Economy` | ✅ | Official UN name (e.g. "Malaysia", "Lao People's Democratic Republic" — not "Laos") |
| 2 | `Law Name` | ✅ | Full official statute name + year (no abbreviations — "Personal Data Protection Act 2012", not "PDPA") |
| 3 | `Law Number / Ref` | ✅* | Official act/law number (e.g. `Act 709`, `B.E. 2562`, `No. 26 of 2000`) |
| 4 | `Last Amended` | ✅ | Year of most recent amendment; month+year if known; **blank if never amended** |
| 5 | `Indicator ID` | ✅ | RDTII code — `P6-I1`…`P6-I4`, `P7-I1`…`P7-I5` (see §4). Either `P6-I1` or `6.1` accepted **if the description is correct**. |
| 6 | `Article / Section` | ✅ | Exact article **and** paragraph — `Art. 26(2)`, `s. 16(1)(a)`. Never just "Art. 26". |
| 7 | `Discovery Tag` | ✅ | `NEW` = tool found it independently; `KNOWN` = in the provided baseline. (§5) |
| 8 | `Location Reference` | ⬜ | PDF: page no. \| HTML: URL anchor / section path (e.g. `#s26`, `Part IV > s.26`) |
| 9 | `Verbatim Snippet` | ✅ | Exact quoted text — **no paraphrasing, no editing** |
| 10 | `Mapping Rationale` | ⬜ | ≤300 chars, format: *"This [article] [prohibits/requires/permits/establishes] [what]. Maps to [indicator] because [1-sentence legal logic]."* |
| 11 | `Source URL` | ✅ | Direct, working URL to the law on the **official** portal (not Google, not a third-party DB) |
| 12 | `Confidence` | ⬜ | Model certainty 0.00–1.00 |
| 13 | `Notes` | ⬜ | OCR issues, partial doc, bilingual source, cross-references, **repealed/outdated flag**, broken-URL flag |

\* `Law Number/Ref` is listed Optional in the recommended-fields slide but Required in the template instructions — treat as **required where available**.

**Additional columns are allowed** appended after column 13 (e.g. `Verbatim (English)`, `Coverage`, `HSN codes`) — required columns must all be present and in order.

### JSON — same fields **plus** metadata

`source_pdf_path`, `ocr_quality_cer` (character error rate), `processing_time_seconds`, `model_version` (LLM + OCR versions, pinned), `provisions[]` (array of all rows for one law), `raw_context_before` / `raw_context_after` (surrounding text for human-in-the-loop review), `pdf_is_scanned`, `retrieval_method`.

---

## 4. In-scope indicators (9) — the RDTII 2.1 definitions (authoritative)

⚠️ **Use these definitions, from the methodology sheet — NOT the output template's "Indicator Reference" tab, which uses a wrong GDPR-style taxonomy.** Pillar 6 has **only 4** scored indicators; **6.5 is out of scope** (non-regulatory, excluded from the template). 7.5 **is** in scope and mandatory.

### Pillar 6 — Cross-border Data Flows (decision tree: 6.1 → 6.2 → 6.3 → 6.4)
| ID | Indicator | Core question | Scoring tree (1 / 0.5 / 0) |
|---|---|---|---|
| `P6-I1` | **Ban & local processing** | Is transfer banned / must data be processed locally? | 1 = all sectors/personal data (or >1 cat-2 measure) · 0.5 = specific sector/data/non-personal, or ban to one country · 0 = none |
| `P6-I2` | **Local storage** | Must a *copy* be stored domestically? (transfer may still be allowed) | 1 = all sectors/personal · 0.5 = specific · 0 = none |
| `P6-I3` | **Infrastructure** | Local servers / data centres required to supply the service? | 1 = requirement · 0 = none |
| `P6-I4` | **Conditional flow** | Transfer allowed *only if* conditions met (consent/adequacy/contract/approval)? | 1 = conditions for all sectors/personal · 0.5 = specific/non-personal · 0 = none |

*Exception (all of 6.1–6.4): do **not** score data-localization applied to **government** data.*
*Key trap: consent/adequacy = **6.4 conditional flow**, NOT a 6.1 ban.*

### Pillar 7 — Domestic Data Protection
| ID | Indicator | Core question | Scoring tree |
|---|---|---|---|
| `P7-I1` | **Comprehensive DP framework** | Horizontal data-protection law? | 1 = none · 0.5 = sectoral only · 0 = comprehensive/horizontal |
| `P7-I2` | **Dedicated cybersecurity framework** | Dedicated cybersecurity law? | 1 = none · 0.5 = non-dedicated/sectoral · 0 = dedicated horizontal |
| `P7-I3` | **Minimum data-retention** | Rule requiring data kept *at least* N period? | 1 = minimum-retention requirement · 0 = none. *("don't keep longer than necessary" ≠ 7.3)* |
| `P7-I4` | **DPIA / DPO** | Duty to appoint a DPO or run a DPIA? | 1 = all sectors · 0.5 = specific sector · 0 = none |
| `P7-I5` | **Government access to personal data** | Law enabling gov access to personal data? | 1 = access without court order · 0 = none. *Look beyond privacy law → criminal procedure, surveillance, telecom.* |

> Zone 3 (assigning the 0/0.5/1 score) stays with a human and is **optional/bonus** — our tool may emit the value, but do not over-invest; a clean Zone 2 record is what's scored.

---

## 5. NEW vs KNOWN (the biggest scoring lever)

- **NEW = worth 20 of the 40 Substantive-Accuracy points** — "the single largest differentiator."
- Judged at the **provision level, not the statute level.** A **new clause inside a law already in the baseline still counts as NEW.** → mine known laws for un-recorded provisions.
- `KNOWN` = the provision was provided as a baseline example (still include it — it proves we match known cases).
- We tag by diffing our finds against the **Round 1 SG/AU/MY baseline database** (the "Database" folder / provided Google Sheet — *not yet in our local folder; obtaining it is high-priority*).

---

## 6. Edge-case handling (encode as rules)

| Situation | Rule |
|---|---|
| **No provision found** for an indicator | Do **not** leave blank. Record "No provision found" (cite the general governing law + reason). Recording a justified absence is valuable. |
| **Repealed / superseded law** | Don't record it. If recorded, you **must** flag "repealed" in Notes — else it reads as active = wrong evidence = penalty. Record active laws only. |
| **Broken / dead URL** | Flag in Notes; prefer the official replacement. |
| **Same provision → 2 indicators** | Two rows (one per indicator). Not mutually exclusive — the same text can map to several indicators. |
| **One indicator ← multiple laws** | Separate rows next to each other; cross-reference in Notes. |
| **Non-English source** (Final Round) | Verbatim snippet = original text **+** an appended `Verbatim (English)` column. Round 1 is all English → low priority. |
| **Sectoral vs horizontal** | Record **both**; authority = legal hierarchy (who enacted it), not breadth. A law covering 2 sectors is still *sectoral*. |

---

## 7. A gold-standard row (the target)

```
Economy:            Singapore
Law Name:           Personal Data Protection Act 2012
Law Number/Ref:     Act 709
Last Amended:       2025
Indicator ID:       P6-I4
Article / Section:  s. 26(1)
Discovery Tag:      NEW
Location Reference: p. 32
Verbatim Snippet:   "An organisation shall not transfer personal data to a country or
                     territory outside Singapore unless..."
Mapping Rationale:  "This s. 26(1) restricts cross-border transfer as the default and
                     permits it only on prescribed conditions. Maps to P6-I4 because
                     transfer is conditional, not banned."
Source URL:         https://sso.agc.gov.sg/Act/PDPA2012
Confidence:         0.95
Notes:
```

A **weak** row (point deduction) paraphrases the snippet, cites "s. 26" without the paragraph, omits the Discovery Tag, has a vague rationale ("this is about data transfers"), or a broken URL.

---

## 8. Ideal result — one paragraph

An open-source, Apache-2.0, **CPU-runnable** engine that a reviewer clones, configures with their own key, and runs on `--economy X --pillar 6/7`; it autonomously crawls SG/AU/MY official portals (HTML **and** PDF, including scanned), extracts every relevant provision at article level, maps each to the correct RDTII 2.1 indicator with a **verbatim, auditable citation and working URL in every row**, tags `NEW` vs the baseline at the provision level, handles absences/repeals/edge-cases cleanly, and emits one consolidated CSV+JSON that a policy judge verifies in Excel and a technical judge re-runs from the README — while **discovering valid new provisions the baseline doesn't have** (the headline differentiator) and reporting a **real, measured** per-document cost.
