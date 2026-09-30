# Delta-crawl request → P1 (rdtii-p1-scrape) + P2 (rdtii-p2-extract)

> **STATUS after corpus v2.1 delivery (2026-07-14 evening, verified by P3):**
> - ✅ **#5 DONE** — sg-ca2018-001 now consolidated (338 provisions, post-2024 content verified via s.17E).
> - ✅ **Bonus (not on this list)** — MY PDP (Amendment) Act 2024 / A1727 landed as `my-pdpa2024-001` (15 provisions: DPO duty, breach notification, s.129 change), + 24 more 2024–25 MY acts (Data Sharing Act 2025, Online Safety Act 2025, …).
> - ❌ ~~Still outstanding: #1–4, #6–13 (all subsidiary/regulator instruments), #14 (AU SOCI still 1 provision), all of Tier 2, and the 3 re-parse docs.~~
> - ✅ **P1 DELIVERY (2026-07-14 late, corpus v2.2): #1–4, #6–14 and ALL of Tier 2 (#15–19 incl. the optional MAS notice) fetched — 18/18, 0 failures, manifest validate OK (2,658 rows).** SOCI (#14) re-issued as full-text HTML (222 section headers) for the HTML lane. Doc_id ↔ document table in `rdtii-p1-scrape/docs/P1_COMPLETION_REPORT_2026-07-12.md` (Addendum 2). **Only the 3 re-parse docs remain — P2 work, no fetch needed.**
> - ⚠️ Schema note for the next delivery: `doc_status` now lives in `doc_status.jsonl` (not laws.jsonl) — acceptance criteria below read accordingly.
> - ✅ **P1 DISCOVERY SWEEP (2026-07-15, corpus v2.3, beyond this request):** +15 verified regulator instruments (2,673 docs, SG 536 / MY 869 / AU 1,268, validate clean) — doc_id table in `rdtii-p1-scrape/docs/P1_COMPLETION_REPORT_2026-07-12.md` Addendum 3. Disclosed unfetchable: BNM RMiT (HTTP 202 bot-gate, attempt logged), IMDA Telecom CoP (no document URL), MCMC INSG (no stable URL).
> - ✅ **P3 FINAL MEASUREMENT (2026-07-15): 17 of the 18 items are extracted and verified in handoff2** (319,026 provisions / 2,670 laws; doc counts reconcile exactly with P1's 2,673 manifest). Highlights: A&A Act n=613, SG CAA 2024 n=187, Telecom Regs n=131, PDP Regs 2021 n=46, GP 3/2025 n=16, FSM-N16 n=10.
> - ❌ **Item #14 (AU SOCI) remains the sole failure: P2's re-run selected the PDF lane again (`source_type_final: pdf_native`, n=1), ignoring P1's HTML re-issue.** Fix needed in P2: force doc `au-scia2018-001` through the HTML parser (source exists; 222 section headers). Plus the 3 re-parse docs. Everything else in this request is CLOSED.

**From:** P3 crawl-sufficiency audit, 2026-07-14 (see `MAPPING_FRAMEWORK_RESEARCH_2026-07-14.md` §2.1 + §3.4a)
**Deadline to be useful:** in `handoff2/` by **18 Jul morning** (joins the AU/MY bulk mapping run). P3's build proceeds regardless — these documents append incrementally.
**Scope discipline: fetch ONLY the items below.** The existing 2,616-doc crawl is validated and must not be re-run.

## Why (one line each)
- The corpus is acts-only: zero subsidiary legislation / regulator instruments in all three economies.
- 10 of our 14 premium NEW-discovery targets are in that missing layer.
- 2 parent acts are unusable as crawled (SG Cybersecurity Act = stale as-enacted 2018 copy; AU SOCI Act = 1 provision parsed from a 267-page PDF).
- 7 instruments cited by the Round-1 baseline were never crawled (blocks parts of KNOWN-matching + the MY error-check).

## Tier 1 — NEW-evidence lever (do these first)

| # | Economy | Document | URL / how to find | Lane | Feeds |
|---|---|---|---|---|---|
| 1 | SG | Commencement Notification S 677/2025 (Cybersecurity Amendment) | `https://sso.agc.gov.sg/SL-Supp/S677-2025/Published/20251015` | SSO | P7-I2 premium NEW |
| 2 | SG | PDP (Statutory Bodies)(Amendment) Notification S 217/2025 | `https://sso.agc.gov.sg/SL-Supp/S217-2025/Published/20250328` | SSO | DP NEW |
| 3 | SG | Personal Data Protection Regulations 2021 | SSO → PDPA 2012 → Subsidiary Legislation (S 63/2021) | SSO | P6-I4 evidence |
| 4 | SG | Cybersecurity (Amendment) Act 2024 (No. 19 of 2024), as enacted | `https://sso.agc.gov.sg/Acts-Supp/19-2024/Published/20240704` | SSO | P7-I2 NEW |
| 5 | SG | **RE-CRAWL** Cybersecurity Act 2018 — consolidated current text | `https://sso.agc.gov.sg/Act/CA2018` (replaces stale `Acts-Supp/9-2018` copy, doc sg-ca2018-001) | SSO | fixes stale parent |
| 6 | MY | Cross-Border Personal Data Transfer Guideline (GP 3/2025) | `https://www.pdp.gov.my/ppdpv1/wp-content/uploads/2025/08/GP_CBPDT_EN-1.pdf` | **native PDF** | P6-I4 premium NEW |
| 7 | MY | DPO Appointment Guideline (2025) | pdp.gov.my → Guidelines section, PDF link | native PDF | P7-I4 premium NEW |
| 8 | MY | Data Breach Notification Guideline (2025) | pdp.gov.my → Guidelines section, PDF link | native PDF | NEW |
| 9–12 | MY | Cyber Security Act 854 subsidiary regs ×4 (CSSP Licensing; Incident Notification; Risk Assessment & Audit; Compounding — all P.U.(A) 2024) | linked from `https://www.nacsa.gov.my/act854.php`; or lom.agc.gov.my P.U.(A) search | native PDF | P7-I2 NEW |
| 13 | AU | Cyber Security (Ransomware Payment Reporting) Rules 2025 | `https://www.legislation.gov.au/F2025L00278/latest/text` | HTML | premium NEW |
| 14 | AU | **RE-CRAWL** Security of Critical Infrastructure Act 2018 — as HTML | `https://www.legislation.gov.au/C2018A00029/latest/text` (PDF copy au-scia2018-001 parsed to 1 provision) | HTML | fixes broken parent |

## Tier 2 — baseline/gold completeness (if time permits)

| # | Economy | Document | URL / how to find | Feeds |
|---|---|---|---|---|
| 15 | MY | Personal Data Protection Standard 2015 | pdp.gov.my → Standards | error-check target r1-my-053 |
| 16 | AU | Telecommunications and Other Legislation Amendment (Assistance and Access) Act 2018 | legislation.gov.au search (C2018A00148) `/latest/text` | gold r1-au-044 (P7-I5) |
| 17 | AU | Telecommunications Regulations 2021 | `https://www.legislation.gov.au/F2021L00289/latest/text` | gold r1-au-044 |
| 18 | SG | PDPC Advisory Guidelines — Children's Personal Data | pdpc.gov.sg → Guidelines (PDF) | gold r1-sg-046 (P7-I4) |
| 19 | SG | *(optional)* MAS Notice FSM-N16 Cyber Hygiene | mas.gov.sg → Regulation → Notices | error-check narrative + SG 7.2 sectoral record |

## Re-parse (already crawled, no fetch needed — P2 only)
- `my-pdpcpbfs2017-001`, `my-pdpcpcs2017-001` (pdp.gov.my CoP HTML pages) and `au-piag-001` (OAIC guidance page): need a per-portal parser, **or** fetch PDF versions of the same instruments if the portals offer them (then the native lane handles it).

## P2 steps after fetch
```powershell
p2-extract run --only-doc <new_doc_id>      # per document; OCR/extract cached
p2-extract tag-corpus --only-untagged       # one small batch, ~$1
p2-extract validate --provisions ..\handoff2\provisions.jsonl --manifest <manifest.csv>
```

## Acceptance criteria
- Each item appears in `handoff2/laws.jsonl` with `provision_count > 0` (guidelines may be small; SOCI re-crawl should yield hundreds).
- Byte-exact grounding passes (P2's standard gate).
- sg-ca2018-001 replacement carries the consolidated text (post-2024-amendment sections present, e.g. Parts 3C/3D headings).
