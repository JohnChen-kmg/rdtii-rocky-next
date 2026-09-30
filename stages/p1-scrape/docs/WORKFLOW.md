# Stage 1 workflow — how each portal is crawled, and every problem we hit

This is the engineering log for Project 1: the overall pipeline, then the per-country
recipe (discovery → retrieval → metadata), the problems encountered on each portal, and
how the code handles them. Companion to the map in the [README](../README.md#workflow-map).

## Overall pipeline

Thin shared core + one adapter per portal. Every adapter answers three questions:
`discover()` (what laws exist?), `build_plans()` (how do I fetch each one?),
`extract_anchor()` (optional deep-link into the law).

Per law: **discover → fetch → classify → store → manifest row**, with:

- **Scope**: `seed` (curated seed_laws) / `relevant` (seed ∪ vocabulary-matched titles) /
  `all` (**the complete portal corpus** — the deliverable; pillar mapping is Project 3's
  job, so nothing is excluded by topic at crawl time).
- **Classification** (contract §2.3): pypdfium2 mean chars/page ≥ 100 → `pdf_native`, below
  → `pdf_scanned`, non-PDF → `html`. Never raises — mislabeled junk is skipped, corrupt
  PDFs kept as scanned for Project 2 to inspect.
- **Resilience**: resumable via `.idmap.json` (re-runs skip retrieved laws), manifest
  checkpoint every 10 docs, adaptive throttle cooldown + retry rounds, per-economy and
  per-document fault isolation (one bad document can never kill a run).
- **Tracking**: built-in `CrawlHealth` — a `[health]` heartbeat, a continuously refreshed
  `crawl_status.json`, and an auto-abort when a portal starts serving junk (10 consecutive
  non-PDF answers to PDF requests). External watchdog: `tools/crawl_tracker.py`
  (exit 2 = stall, exit 3 = throttle suspected).
- **Provenance** (the live-crawl proof): every fetch — including failures — appends to
  `crawl_log.jsonl`; every stored document gets a `.headers.json` sidecar with final URL,
  status, redirect chain, and response headers.

Final corpus (v2.4, 2026-07-18): **2,706 manifest rows = 2,673 current documents + 33
superseded** (SG 536 / MY 869 / AU 1,268 current), validate OK, contract 0.2.0 — every
document in its **most current and complete** form (see the version-currency fixes in
the per-country tables below); OCR workload 43 docs / ~1,050 pages. v2.2 added the
**subsidiary/regulator layer** (P3's 18-item delta request): SG SL + PDPC/MAS notices,
MY PDP guidelines + Act 854 P.U.(A) regulations (via NACSA), AU F-series legislative
instruments — plus the SOCI Act re-issued as full-text HTML (`form: html` seed pin) so
P2's proven HTML lane parses it. v2.3 added a **proactive discovery sweep** (15 more
instruments): SG CII regulations (2018 + the 2025 amendment) + CSA CCoP 2.0 + MAS TRM
Guidelines + PDP breach-notification regs; MY PDP Regulations 2013 + SC GTRM + Act 854
Exemption Order 2025; AU SOCI CIRMP/TSRMP Rules + Smart-Devices Rules 2025 +
CPS 230/234 + AGA Governance APP Code + Credit Reporting Code 2024. One known miss:
BNM RMiT (bnm.gov.my answers HTTP 202 to non-browser clients — attempt logged in
crawl_log.jsonl). v2.4 is the **AU multi-volume truncation fix** (independent judge's
find): 33 AU HTML acts re-fetched complete via the register's dated epub — see the AU
table below, report Addendum 5, and `AU_HTML_TRUNCATION_AUDIT_2026-07-17.md`.

---

## 1. Malaysia — lom.agc.gov.my (Laws of Malaysia, AGC)

**Why this portal:** Malaysia has no single consolidated statutes site; lom is the
official AGC database and addresses every act by NUMBER. (`federalgazette.agc.gov.my`
fails DNS — intentionally omitted.)

**Discovery:** enumerate `act-detail.php?language=BI&act=<n>` for n = 1…900 (`LOM_MAX_ACT`).
Each detail page (static HTML, one `requests` fetch) yields, in one pass:
- the PDF.js viewers' `file=` params → the act's **whole document history in
  chronological order** (original gazette → amendment gazettes → reprints → the
  **current consolidated English version** under an `/EN/` path, native text);
- the real law **title** — in a `<span>` under the `<h1>Act N</h1>` of `#page-title`;
- **Publication Date / Royal Assent Date / Commencement Remark**.

**Retrieval:** direct PDF download via `requests`, **preferring the most current file**:
`/EN/` consolidation → newest REPRINT/REVISED → original as-enacted (last resort).

**Problems hit → fixes:**
| Problem | Fix |
|---|---|
| 759/768 titles came out as generic "Act N" in v1 | The real title is in a `<span>` *after* the `<h1>`, not in any heading tag — parser fixed; 741/833 now have real titles. The remaining 92 have a **blank title on the portal itself** (verified); their PDFs carry the title on the cover page for Project 2. |
| Some act numbers return a 5-byte `false` body mislabeled `application/pdf` | This crashed PyMuPDF and killed a whole run once. Now: `classify()` never raises, and a PDF-plan response without `%PDF-` magic is **skipped and logged**, not stored. |
| 474 of 833 MY acts are image scans (0 chars/page) | Correctly classified `pdf_scanned` → they are the OCR workload (and evidence) for Project 2. |
| **Version currency (caught 2026-07-14, corpus v2.1):** the picker preferred the *first/original* file, so many acts were stored as the **as-enacted original** (often a decades-old gazette scan) even though the page also offers the **current consolidated English version** (`/EN/Act N.pdf`, native text — e.g. PDPA: we held the 2010 "ori"; a 2016 consolidation existed) | `_extract_pdf_url` now prefers `/EN/` → newest reprint → original (unit-tested); **MY fully re-crawled** with the new selection. Side benefit: most former scans became native text, collapsing the OCR workload. |
| Stale seed URLs (hasil deep-link 404, pdp.gov.my redirects, one non-whitelisted fallback) | Seeds resolve via lom-by-number first; sources_my.yaml cleaned (whitelist: cyrilla.org, commonlii.org, um.edu.my — MY last-resort only). |

## 2. Singapore — sso.agc.gov.sg (Singapore Statutes Online)

**Discovery:** the full "Current Acts" browse listing. SSO caps `PageSize` at 500 and its
page cursor is unreliable, so we take the **union of ASC + DESC sorted listings** (2
fetches) → all ~523 current acts with real titles.

**Retrieval:** native PDF per act via the `?ViewType=Pdf` endpoint (fast `requests` path).
The HTML form (`?WholeDoc=1`, Playwright, `div#legisContent`) exists for `--forms html|both`.

**Problems hit → fixes:**
| Problem | Fix |
|---|---|
| **HTTP 467 anti-bot** after ~20 heavy HTML fetches | Escalation ladder + shared browser session + exponential backoff; and the PDF `requests` path avoids the heavy HTML entirely — the full 523-act PDF crawl ran with zero throttle events on day 1. |
| **HTTP 202 / RSS-instead-of-PDF** under sustained re-crawling (day 2) | SSO builds PDFs on demand and degrades under load: 202 = "still generating", or it serves an RSS/HTML placeholder with status 200. Fix 1: bounded quick-retry in the fetcher (4s/8s/12s). Fix 2: `CrawlHealth` counts consecutive junk responses and **aborts SG early** instead of burning through the queue. Fix 3: since the v1 PDFs were already on disk and sha-verified, the v2 run **migrated all 525 SG rows without touching SSO again**. |
| `PageSize=5000` silently returns ~21 acts | Out-of-range values reset to a tiny default — hence the ASC∪DESC union at PageSize=500. |
| Listing carries no dates | SG rows have title + `in_force_status="Current"`; dates would need per-act page parsing (deferred — Project 2 sees the full text anyway). |
| **Stale Cybersecurity Act (caught by the 2026-07-14 baseline audit):** the seed URL pointed at `Acts-Supp/9-2018` (the as-enacted supplement), and name-dedup then skipped the listing's current-consolidation candidate — so the corpus held the 2018 original (75 pp), missing the 2024 amendments | Seed fixed to `/Act/CA2018` (both yaml copies); row purged + re-fetched → current consolidation (119 pp, 2024 amendments verified present). Rule of thumb encoded in the config comment: **Acts-Supp is only for amendment acts**, never principal acts. |

## 3. Australia — legislation.gov.au (Federal Register of Legislation)

**Discovery:** the register's OData API:
`api.prod.legislation.gov.au/v1/titles?$filter=isInForce eq true and collection eq 'Act'`
→ 4,747 in-force Acts → client-side `isPrincipal` filter → **1,258 principal in-force
Acts**, each with real name, `makingDate` (assent) and status.

**Retrieval (native PDF, HTML fallback):** each act's `/latest/downloads` page (static
HTML, `requests`) contains the dated PDF href. Single-file acts →
`/<rid>/<date>/<date>/text/original/pdf` (867 acts). Large acts (Criminal Code, Customs…)
exist **only as multi-volume PDFs** — those fall back to the complete single-file
full-text HTML at `/latest/text` (391 acts).

**Volume policy (v2.4):** a multi-volume compilation is stored as **one document
containing every volume** — the register's dated epub, all spine documents concatenated
in order, with `p1-epub-spine-doc i/n` boundary markers so completeness is
machine-checkable. Not per-volume rows: one act = one row = one file. The corpus does
not claim to be "the complete AU statute book" beyond this: it holds every in-force
principal act (plus the seeded instrument layer), each in its latest compilation, all
volumes included — verified by `tools/audit_au_truncation.py` (0 truncated).

**Problems hit → fixes:**
| Problem | Fix |
|---|---|
| The Act text on `/latest/text` lives inside a **blob: iframe** (`iframe#epubFrame`) — a naive fetch captures a 1.6 KB nav shell | `FetchPlan.iframe_selector`: the fetcher waits for the frame and captures the **framed document** (e.g. Privacy Act = 2.35 MB, all 353 section headers). |
| API quirks: `$top` max 100; `$filter` responses have **no `@odata.nextLink`**; adding `isPrincipal` as a third filter conjunct → HTTP 400 | Paginate with `$skip`; filter `isPrincipal` client-side. |
| The dated PDF URL 404s for some acts if given an arbitrary date | Parse the **exact compilation date** from each act's downloads page (1 cheap requests fetch per act during discovery). |
| Multi-volume acts have no single PDF | Detected on the downloads page (only `/pdf/1..N` hrefs, no base `/pdf`) → complete HTML fallback. |
| One dead seed id (`C2021C00496`, withdrawn compilation) | The register itself 404s it ("title could not be loaded"); logged and skipped — the live-fetch attempt is still auditable evidence. |
| **CRITICAL — multi-volume truncation (caught by the independent judge, 2026-07-17; corpus v2.4):** the epubFrame renders ONE epub spine document at a time, and one spine document = one volume — so all **33** multi-volume compilations were silently stored as **volume 1 only** (TIA 1979 stopped at s.186J, losing Part 5-1A's s.187C metadata retention; Corporations 2001 stopped at s.260E of 1712; ITAA 1997 held 1 of 12 volumes) | Multi-volume acts are now fetched as the register's dated **epub** (plain `requests`), and `p1_scrape/epub.py` concatenates **every** spine document, verified against the OPF spine — any shortfall fails loudly. Stored artifacts carry `p1-epub-spine-doc i/n` markers (machine-checkable completeness). The framed fallback now **rejects** captures self-declaring "This compilation is in N volumes". All 33 re-fetched under §5.4 supersession (`-002`, `supersedes` notes; `-001` rows kept + annotated). Audit tool + report: `tools/audit_au_truncation.py`, `docs/AU_HTML_TRUNCATION_AUDIT_2026-07-17.md` — 0 truncated remaining. |
| A downstream audit reported the SOCI Act 2018 PDF as "broken" (1 provision extracted from 267 pp) | **File verified healthy** (2026-07-14): 438k chars of text (1,641/page), current 2026-06-04 compilation, all Parts present. The 1-provision result is a Project-2 splitter issue (AU compilations put section numbers on their own line) — **not** a retrieval defect; re-crawling is a no-op. |

---

## Re-running (the corpus is reproducible)

```powershell
# complete corpus, resumable — safe to interrupt and re-run any number of times
.\.venv\Scripts\python scrape.py --economy SG,MY,AU --scope all --out handoff1
.\.venv\Scripts\python scrape.py --validate handoff1\manifest.csv
```

Practical notes learned the hard way:
- **Where SG live-fetch provenance lives** (don't misread SG coverage as thin): the
  current `handoff1_v2/crawl_log.jsonl` holds only ~16 sso.agc.gov.sg entries because
  the 525-act SG corpus was **migrated from the validated v1 run rather than re-fetched**
  (deliberately — see the SSO anti-bot row above). The bulk of SG live-fetch evidence is
  (a) the per-document `.headers.json` sidecars beside every SG raw file (525+ of them,
  each with final URL/status/headers from the original live fetch) and (b) the v1 run's
  full crawl log in `handoff1_old_v01/crawl_log.jsonl` (524 OK sso.agc.gov.sg entries).
- **SG**: don't hammer SSO twice in one day — resume skips retrieved laws, and the health
  monitor stops the economy if the anti-bot wakes up. PDFs regenerate server-side, so
  content hashes can legitimately differ between runs (doc_id stays stable; `supersedes`
  is noted).
- **MY / AU**: the first ~20 minutes per economy are the (quiet) inventory harvest;
  watch `crawl_status.json` or the `[health]` heartbeat, not just manifest row count.
- Timing at polite rates: SG ~45 min, MY ~2.5 h, AU ~4 h (resolution + fetch).
