# 1 · Web Scraping (Retrieval) — PROJECT 1 PLAN

> **Repo:** `rdtii-p1-scrape/` · **Pipeline stage:** P1 · **Owner:** John (solo) · **Contract:** obeys `00_contracts/` §2 (Hand-off #1), §4 (`sources_<cc>.yaml`), §5 crawler keys, §8 versioning.
> **One-line mandate:** crawl the live SG/AU/MY government legal portals and retrieve the *raw bytes* (HTML, native PDF, scanned/image PDF) with full locators + HTTP provenance, then emit **Hand-off #1** (`handoff1/` = `manifest.csv` + `manifest.jsonl` + `raw/**` + `crawl_log.jsonl`). Nothing is OCR'd, cleaned, tagged, or mapped here.

---

## 1. Purpose & non-goals

### 1.1 Purpose (what earns points)

Project 1 is the **only** stage that touches the live internet. It exists to make two rubric claims true and auditable:

1. **Live portal crawling — 10 pts, scored 0-or-10.** A tool that only reads pre-downloaded files scores **zero** on this item. Project 1 must *demonstrably* fetch from `sso.agc.gov.sg`, `legislation.gov.au`, and `federalgazette.agc.gov.my` at run time, over anti-bot / JS-rendered pages, and leave an auditable trail (`crawl_log.jsonl`, `.headers.json` sidecars, `retrieval_method`, `http_status`, redirect chains) proving the bytes came off the wire, not a cache.
2. **The PDF-and-HTML differentiator.** Named differentiator #2 in the rubric. Project 1 must retrieve *both* form factors and classify them correctly (`source_type ∈ {html, pdf_native, pdf_scanned}`), because HTML (the harder, higher-value one) round-trips a working deep-anchor URL and scanned PDFs seed the OCR item (Project 2) and Deliverable #4.

It also indirectly protects three downstream levers by getting locators right at retrieval time: citation fidelity (working `source_url` + `anchor_hint`), the OCR item (correct `pdf_is_scanned` routing), and NEW-evidence (over-inclusive discovery surfaces provisions the baseline never saw).

### 1.2 Non-goals (hard boundaries — do not cross the seam)

| NOT Project 1's job | Whose job | Why the boundary matters |
|---|---|---|
| OCR / text-layer extraction | Project 2 | P1 only *classifies* scanned vs native (2.3 decision rule); P2 *measures* `ocr_quality_cer`. |
| Text cleaning / DOM-to-article normalization | Project 2 | P1 stores the **rendered HTML as-is** (post-JS DOM) + anchor hints; no boilerplate stripping. |
| Article-boundary splitting, provision extraction | Project 2 | P1 emits **one row per document**, never per provision. |
| Feature tags (`scope`/`data_type`/`obligation_type`) | Project 2 | P1 may record a coarse `pillar_hint` from the seed query only. |
| Indicator mapping, NEW/KNOWN, scoring, final CSV | Project 3 | P1 never reads `indicators.yaml` scoring trees. |
| "No provision found" rows | Project 3 | P1's failure mode is a `crawl_log.jsonl` entry + optional `crawl_notes`, not a provision decision. |

**Litmus test for scope creep:** if a task requires reading the *text content* of a document to decide anything beyond "is this the right law / is it scanned / what's the anchor," it belongs to P2 or P3.

---

## 2. Position in the pipeline & the exact output contract

```
        LIVE PORTALS                    ┌──────────────── Hand-off #1 ────────────────┐
  sso.agc.gov.sg   ──┐                  │ handoff1/                                   │
  legislation.gov.au ├──►  PROJECT 1 ──►│   manifest.csv     (1 row / document)       │──► PROJECT 2
  federalgazette.…my ┘   (this repo)    │   manifest.jsonl   (+ nested http object)   │   (OCR+tags)
                                        │   raw/<cc>/<law>/  <ts>__<kind>.<ext> (+ .headers.json)
                                        │   crawl_log.jsonl  (every URL, incl fails)  │
                                        └─────────────────────────────────────────────┘
```

**The contract is frozen in §2 of `00_contracts/`. Project 1 does not get to redesign it.** Key obligations, restated so this plan is self-checking:

- **Folder convention (§2.1):** one leaf dir per `(economy, law)` guess; file name `<access-ts>__<kind>.<ext>` where `kind ∈ {native, scanned, page}`; every file has a `.headers.json` sidecar (http status/headers/redirect chain).
- **`local_path` and `http_headers_path` are RELATIVE to `handoff1/`** — no absolute paths in the manifest (portability is a contract rule; a leaked `C:\Users\...` path is a validate-time failure).
- **Manifest schema (§2.2):** the table defines **20 fields; the 14 required ones** (`doc_id`, `economy`, `source_url`, `access_date`, `source_type`, `pdf_is_scanned`, `local_path`, `law_name_guess`, `retrieval_method`, `http_status`, `http_headers_path`, `content_type`, `content_sha256`, `byte_size`) must all be present and non-null (`pdf_is_scanned` may be `null` **only** when `source_type=html`). The remaining 6 (`law_number_guess`, `page_count`, `anchor_hint`, `seed_query`, `pillar_hint`, `crawl_notes`) are optional. **`validate` (against `manifest.schema.json`) is the single source of truth for this set — this prose is a convenience restatement, not the authority.**
- **`doc_id` format:** `<cc>-<lawslug>-<seq>`, e.g. `sg-pdpa2012-001`. This id is carried end-to-end by P2/P3 — it is the join key of the whole system. **Must be stable across re-runs** (see §5.4 dedup) so a re-crawl doesn't renumber and orphan downstream records.
- **Scanned-vs-native decision rule (§2.3):** open every PDF with pypdfium2; `mean extractable chars/page ≥ 100` ⇒ `pdf_native` / `pdf_is_scanned=false`; below ⇒ `pdf_scanned` / `pdf_is_scanned=true`. A mis-flag is recoverable (P2 re-checks) but the field must always be present.
- **`CONTRACT_VERSION` / `instrument_version`** stamped into every manifest row (§8). `p1-scrape validate` refuses to proceed on a **major** version mismatch.

### 2.1 Exit gate for the hand-off (contract §2.4, reproduced as our Definition-of-Done)

- [ ] `manifest.csv` + `manifest.jsonl` validate against `00_contracts/schemas/manifest.schema.json` (our `validate` CLI is the gate).
- [ ] ≥ 1 `pdf_scanned` row exists **for at least one in-scope economy (SG, AU, or MY)** — needed for the OCR demo. This is *not* SG-specific: an MY gazette or an AU scanned instrument satisfies it equally (see §11 R4 for the self-sourced fallback and the in-scope-provision requirement).
- [ ] Every `local_path` and `http_headers_path` resolves on disk; every `source_url` returned `http_status < 400` at retrieval time, else `crawl_notes` explains (e.g. `orig 404; used AGC replacement`).
- [ ] `content_sha256` unique per distinct file (dedup enforced, §5.4).
- [ ] No absolute paths anywhere in the manifest.

---

## 3. Crawler architecture

### 3.1 Layered design (thin core + per-country adapters)

```
rdtii-p1-scrape/
  src/p1_scrape/
    cli.py                 # arg parse -> orchestrator
    orchestrator.py        # frontier loop: discover -> fetch -> classify -> store -> manifest row
    fetcher.py             # Playwright + requests fetch, ret/backoff, headers capture, sha256
    classifier.py          # §2.3 rule: html | pdf_native | pdf_scanned (pypdfium2 char/page)
    manifest.py            # row builder + CSV/JSONL writers + schema validate
    dedup.py               # sha256 + normalized-URL registry, stable doc_id assignment
    storage.py             # handoff1/ layout, <ts>__<kind>.<ext>, .headers.json sidecars
    crawl_logger.py        # append-only crawl_log.jsonl (every URL touched)
    politeness.py          # robots (advisory), rate limit, backoff, user-agent
    smoke.py               # 3-portal live-fetch smoke test (banks one fetch per portal, §10 T2b)
    adapters/
      base.py              # class PortalAdapter(ABC): discover()->[Candidate]; resolve(Candidate)->FetchPlan
      sg_sso.py            # sso.agc.gov.sg
      au_legislation.py    # legislation.gov.au (HTML-heavy, deep anchors)
      my_gazette.py        # federalgazette.agc.gov.my + lom.agc.gov.my (expect_scanned)
      registry.py          # economy -> adapter
    seed_import/
      legacy_sg_au.py      # wraps user's prior SG/AU scraper (see §6), COI-gated
  config/                  # vendored crawler-relevant keys from 00_contracts/config_template
  contracts/               # vendored pinned copy of 00_contracts (schemas + sources_*.yaml)
  tests/
  scrape.py                # thin entry -> src/p1_scrape/cli.py  (so `python scrape.py ...` works)
  requirements.txt         # PINNED versions, no "latest"
  README.md
```

**Why adapters, not one mega-crawler:** the three portals differ structurally (SSO = JS statute browser with in-page provision anchors; legislation.gov.au = HTML-heavy series pages with deep section anchors; federalgazette = a search/listing over image-PDF gazettes). A shared `fetcher`/`classifier`/`manifest`/`dedup` core plus a small `PortalAdapter` per site keeps the differences isolated and lets the SG adapter ship (vertical slice) before AU/MY exist. Each adapter implements two methods only: `discover()` → candidate URLs, and `resolve(candidate)` → a `FetchPlan` (URL, method, whether JS render is needed, anchor extraction hints).

### 3.2 The frontier loop (orchestrator)

```
for economy in requested:
  adapter = registry[economy]
  candidates = adapter.discover(sources_<cc>.yaml, pillars, seed_laws_only?)   # §4 over-inclusive
  candidates = dedup.normalize_and_filter(candidates)                          # URL-level pre-dedup
  for cand in candidates (politeness-rate-limited):
      plan  = adapter.resolve(cand)
      bytes, http = fetcher.fetch(plan)          # Playwright or requests; capture headers/redirects
      crawl_logger.log(cand.url, http)           # ALWAYS logged, success or fail
      if http.status >= 400: record failure + continue
      sha = sha256(bytes)
      if dedup.seen(sha): continue               # content-level dedup
      stype, is_scanned, pages = classifier.classify(bytes, http.content_type)
      path = storage.store(economy, law_slug, kind, ext, bytes, http)
      manifest.add_row(doc_id=dedup.stable_id(economy, law_slug, sha), ...)
manifest.write_csv_jsonl(); validate()
```

### 3.3 Anti-bot / JS handling (why Playwright is the default, not `requests`)

- **Default engine = Playwright (Chromium, headed-in-headless).** Government portals increasingly gate on JS challenge cookies and render statute bodies client-side. SSO's provision anchors (`?ProvIds=pr26-`) and legislation.gov.au's section HTML materialize only after JS. Playwright: (a) executes JS so the post-render DOM (what we store for HTML) is complete; (b) carries a realistic browser fingerprint / UA to clear soft anti-bot; (c) exposes `response.status`, `response.headers`, and the redirect chain for the `.headers.json` sidecar and the live-crawl audit.
- **`requests` fast-path.** For a URL that is already a direct PDF link with no JS gate (many gazette PDFs, some SSO PDF endpoints), the adapter's `FetchPlan.method=requests` skips the browser for speed and lower cost. `retrieval_method` records which was used (feeds provenance + resilience story).
- **Escalation ladder (per fetch, on failure):** `requests` → Playwright default context → Playwright with stealth UA + human-like delay + `wait_until=networkidle`. Each rung logged. If all fail, the URL is a `crawl_log.jsonl` failure row with reason (`403 anti-bot`, `timeout`, `challenge_unresolved`) — this **still earns the live-crawl point** because attempted+logged live fetches are the evidence, and it gives Project 3 a documented broken-URL to handle.
- **Timeouts / retries:** per-URL wall budget (default 45 s), 3 retries with exponential backoff + jitter, respected `Retry-After`. Config keys in §7.

### 3.4 Storage & provenance capture

For every retrieved doc: write the bytes to `raw/<cc>/<law_slug>/<ts>__<kind>.<ext>`, and a sibling `<same>.headers.json` = `{final_url, status, redirect_chain[], request_headers, response_headers, content_type, fetched_at, retrieval_method}`. This sidecar is what makes the "working URL" citation-fidelity claim and the live-crawl claim auditable by a non-technical judge in seconds.

---

## 4. Over-inclusive candidate discovery (seeded by P0)

**Principle: over-collect at retrieval, let Project 3 filter.** NEW-evidence is 20 pts and is judged at provision level; missing a document at P1 is unrecoverable downstream, whereas an extra retrieved document costs only disk + a few seconds of P2. So P1 biases toward recall.

### 4.1 Source strategy — official portals only (Malaysia is a federation)

**The host handed us a near-complete law→URL map.** `Knowledge Portal/Resource Library/Sample governemnt portals_Pillar 6_7.csv` + the Round 1 baseline DB list the actual SG/AU/MY laws + reference URLs for Pillars 6 & 7 — so `sources_<cc>.yaml` is **seeded directly from these** (not hand-curated), and discovery starts from a known target list, not cold. The evidence in those files fixes the per-country strategy:

- **Singapore & Australia — one official portal each is sufficient.** SG: **`sso.agc.gov.sg`** (Statutes Online) + regulators `pdpc.gov.sg`, `imda.gov.sg`. AU: **`legislation.gov.au`** (Federal Register) + `oaic.gov.au`, `cyber.gov.au`, `homeaffairs.gov.au`. Every in-scope law sits on the official portal; the baseline cites them as primary throughout. **Crawl official only — no third-party sites.** This is the confident, clear case (and the first two verticals we build).
- **Malaysia — a *federation* of official sites + a narrow reputable fallback.** MY has **no** consolidated free official statutes portal; laws are scattered across official agency sites (`pdp.gov.my`, `mcmc.gov.my`, `bnm.gov.my`, `ssm.com.my`, `customs.gov.my`, `miti.gov.my`, `hasil.gov.my`) + the federal gazette (`lom.agc.gov.my` / `federalgazette.agc.gov.my`, often scanned). ESCAP's own baseline even cites key MY acts (PDPA 709, Cyber Security Act 854, Criminal Procedure Code, Security Offences Act) from **non-government** copies (`um.edu.my`, `cyrilla.org`, `commonlii.org`, law-firm sites) because no official online copy is reachable.
- **Citation source hierarchy (contract §4.2 `citation_url_preference`):** official statutes portal → official regulator/agency site → official gazette scan → **(MY last-resort only)** a *whitelisted* reputable secondary, flagged in `Notes`. Third-party sites are **never a discovery crawl target** — only a last-resort *fetch* fallback for the handful of MY docs with no reachable official copy, mirroring what ESCAP itself did.

Discovery inputs come **only** from `contracts/instrument/sources_<cc>.yaml` (§4.3 of the contract) — P1 owns no hardcoded URLs:

- **`seed_laws`** — the known target laws (e.g. SG PDPA 2012). With `--seed-laws-only` (vertical-slice mode) discovery is *just* these; this is the fast, deterministic path the `run_slice` runner uses.
- **`portals`** — `primary_statutes.root`, `gazette`, `regulators[]`. The adapter walks these as crawl roots in breadth mode.
- **`seed_queries`** — vocabulary-seeded per pillar (`P6: ['"transfer" personal data outside Singapore', '"data localization"', ...]`, `P7: ['data breach notification', 'retention limitation', 'DPO appointment', ...]`). Each adapter turns these into that portal's native search (SSO search box, legislation.gov.au search, federalgazette search) and harvests result links, plus follows in-statute cross-references (e.g. a PDPA section referencing subsidiary regulations) to catch sectoral instruments — because 6/7 are omnibus statutes **plus** sectoral regulations, not the standalone acts Pillars 4/5 used (see §6.2).

**Candidate object:** `{url, economy, law_name_guess, law_number_guess?, anchor_hint?, seed_query?, pillar_hint?, expect_scanned?}` — a superset feeding the manifest's traceability fields (`seed_query`, `pillar_hint`, `anchor_hint`).

**Recall guardrails (avoid unbounded crawl):** per-economy candidate cap (config `MAX_CANDIDATES_PER_ECONOMY`, default 60), max crawl depth from a portal root (default 2), and a domain allow-list = only the hosts named in `sources_<cc>.yaml` (for SG/AU essentially `*.agc.gov.sg`/`legislation.gov.au` + the named regulators; for MY the federation of official agency hosts + gazette **plus a small explicitly whitelisted reputable-fallback list**, per §4.1 — never an open web crawl). This keeps discovery over-inclusive on *target laws* but not an open web crawl.

---

## 5. Cross-cutting crawl behaviors

### 5.1 Politeness & robots — **advisory, not a hard block on the 10-pt item**

The live-crawl item is a **binary 0-or-10** that depends on actually reaching public-record statute pages. Government portals commonly `Disallow` their *search/query* paths in `robots.txt` (e.g. legislation.gov.au and SSO gate search endpoints), so a naive "honor robots before every fetch" rule would silently zero the exact fetches P1 exists to earn. The stance is therefore:

- **Seed-law canonical URLs are always fetched.** These are public-record legislation pages the seed law already points to (the human-facing canonical statute URL) — public documents a citizen may read in a browser. Robots directives are treated as **advisory rate/scope guidance** for these specific URLs, not a hard gate. We crawl one document at a time, at a low polite rate, with an identifiable UA — the ethics stance is "polite citizen reading public law," documented in the README.
- **Discovery/search paths respect robots as scope guidance.** If `robots.txt` disallows a *search* path, the adapter does **not** hammer that endpoint; instead it falls back to the canonical seed-law URL (still a live fetch, still logged) or an alternate public listing. **The fallback URL is confirmed reachable (`http_status < 400`) before being relied on — never assumed allowed.** A `Disallow` on a search path must not remove a document we can reach by its canonical URL.
- **Config:** `RESPECT_ROBOTS_FOR_DISCOVERY=true` (advisory scoping of search/discovery), `ROBOTS_HARD_BLOCK=false` (seed-law canonical fetches are never hard-blocked). Both are documented so the ethics decision is transparent and reproducible.
- **Rate limit:** default 1 request / 2 s per host, jittered; concurrency 1 per host. Config `REQUEST_DELAY_MS`, `MAX_CONCURRENCY_PER_HOST`.
- **Identifiable UA** with contact string (config `USER_AGENT`), so an administrator can trace/contact rather than block.

### 5.2 Freshness / amendment detection

`last_amended` is authored by Project 2 (from document text), **but** P1 captures the retrieval-time signals P2/P3 need and records amendment *hints*:

- Capture `Last-Modified` / `ETag` response headers into the sidecar.
- SSO and legislation.gov.au print a "current version / in force as of" date on the statute page — the adapter extracts it into `crawl_notes` (e.g. `SSO shows 'Current version as at 09 Jul 2026'`) as a non-authoritative hint. This is a *locator* capture, not text parsing, so it stays in scope.
- **Repealed/superseded:** if a portal explicitly labels a result "Repealed"/"Revoked" in its listing metadata, tag it in `crawl_notes` and still retrieve it (Project 3's edge-case rule decides whether to drop or flag it — §4 `policies.yaml`). P1 does not silently discard.
- **Re-crawl freshness:** `content_sha256` lets a later re-run detect unchanged docs (skip, reuse seq) vs changed (new content hash → next `seq` under the same `(cc, lawslug)`, `crawl_notes: supersedes <doc_id>`). See §5.4 for how the idmap holds both.

### 5.3 Deduplication

Two-level, both required by contract §2.4 (`content_sha256` unique per file):

1. **URL-level (pre-fetch):** normalize URLs (lowercase host, strip tracking params, canonicalize SSO/legislation query params, keep meaningful `ProvIds`/section anchors) → skip already-queued URLs.
2. **Content-level (post-fetch):** `sha256(bytes)`; if seen, drop the duplicate and do not write a manifest row. Handles the common case where a statute is reachable via multiple URLs.

### 5.4 Stable `doc_id` assignment (idmap holds every version)

`doc_id = <cc>-<lawslug>-<seq>`. `lawslug` is a deterministic slugify of `law_name_guess`. The mapping is persisted in `handoff1/.idmap.json` **keyed by `(cc, lawslug)` → an ordered registry of `{content_sha256 → seq}` entries** (not a single scalar seq). This resolves the tension between join stability and supersession:

```jsonc
// handoff1/.idmap.json
{
  "sg::pdpa2012": {
    "current_seq": 1,
    "versions": [
      { "seq": 1, "content_sha256": "9f2c…", "first_seen": "2026-07-09T10:32Z", "current": true }
    ]
  }
}
```

- **Unchanged re-crawl** (same `content_sha256` already in `versions`) → reuse its `seq` → same `doc_id` → downstream join stability preserved (no orphaning, no renumbering).
- **Genuinely changed version** (new `content_sha256` under an existing `(cc, lawslug)`) → allocate the **next** `seq`, append to `versions`, set it `current: true`, flip the prior entry `current: false`, and write `crawl_notes: "supersedes sg-pdpa2012-001"` on the new manifest row. The old `doc_id` is never renumbered or destroyed.
- **Which doc_id is current** is signalled to downstream two ways: `current_seq` in the idmap, and — because P2/P3 read the manifest, not the idmap — the superseded row carries `crawl_notes: "superseded by sg-pdpa2012-002"` while the live row carries the forward `supersedes` note. Project 3's `repealed`/supersession edge rule (§4 `policies.yaml`) then decides drop-vs-flag.

### 5.5 Transparent run logging

Beyond the machine-readable `crawl_log.jsonl`, `p1-scrape crawl` streams a human-readable, per-document narration to **stdout** and mirrors it to `logs/` (contract §9.1): `SSO → PDPA 2012 → pdf_native (200) → anchor ?ProvIds=pr26- → stored → manifest sg-pdpa2012-001`. A judge watching the terminal sees the live crawl actually happen — reinforcing the 0-or-10 live-crawl claim and the no-manual-steps story, and giving the live demo its "engine visible" moment.

---

## 6. Consuming the user's prior SG/AU scraper

The user will supply his own prior web-scraping code for Singapore and Australia to **seed** Project 1. It is a *starting accelerant for the portal-access layer*, not a drop-in — treat it as a vendored, gated input under `src/p1_scrape/seed_import/legacy_sg_au.py`.

### 6.1 COI / IP gate (blocking, do before writing any code from it)

- **Provenance check (must pass before merge):** confirm the code is the user's **own** work or already public, **not** ESCAP-intern / employer IP. The whole repo ships **Apache-2.0**; vendoring restricted code poisons the license and could be a conflict-of-interest given the user's UN ESCAP link.
- **Action:** if provenance is anything other than clearly "mine or public," **do not vendor it** — reimplement the portal navigation from public docs. Record the decision in `README.md` → *Provenance* section. This is cheap insurance against disqualification.
- If clean: add its origin + license note to `NOTICE`, keep it in `seed_import/` (quarantined), and expose it behind the `PortalAdapter` interface so the rest of the crawler doesn't couple to its internals.

### 6.2 Pillars-4/5 → 6/7 retargeting caveat (what carries, what doesn't)

| Carries over (reuse) | Must change (rewrite) |
|---|---|
| Portal roots, session/cookie handling, JS-render approach, anti-bot workarounds, PDF-download plumbing for `sso.agc.gov.sg` and `legislation.gov.au` | The **query/target logic**. Pillars 4/5 targeted *standalone acts*; Pillars 6/7 are **omnibus statutes (PDPA, Privacy Act) + sectoral regulations + subsidiary instruments**. |
| Rate-limiting / politeness patterns already tuned to these hosts | Seed queries + candidate discovery (§4) — driven by `sources_<cc>.yaml` `seed_queries` for 6/7 vocabulary (transfer, localization, breach notification, retention, DPO), not the 4/5 act list. |
| Deep-anchor extraction for legislation.gov.au (high value for HTML differentiator) | Cross-reference following into subsidiary/sectoral regs (new for 6/7). |

**Bottom line:** salvage the *transport layer*, replace the *discovery layer*. The adapter boundary is exactly where this split lives — legacy code sits under `resolve()`/fetch; new P0-seeded discovery sits in `discover()`.

---

## 7. Tool choices & swappable fallbacks

All model-/engine-bearing choices are **config values, not rewrites** (the 15-pt modular-backend deliverable, shared config layer §5 of the contract). P1 uses only the crawler-relevant keys.

| Concern | Default | Fallback(s) | Config key | Rubric tie |
|---|---|---|---|---|
| Crawl engine | **Playwright** (Chromium) | `requests` (direct-PDF fast path); `httpx` | `CRAWL_ENGINE=playwright` | live-crawl 10; anti-bot |
| HTML capture | Playwright post-JS DOM (stored raw) | requests + raw HTML (non-JS pages) | — (per `FetchPlan`) | PDF+HTML differentiator |
| PDF scanned-classify | **pypdfium2** (chars/page, §2.3) | pdfminer.six char count | `SCAN_CHAR_THRESHOLD=100` | routes OCR item to P2 |
| robots/politeness | stdlib `urllib.robotparser` (advisory, §5.1) + rate limiter | — | `RESPECT_ROBOTS_FOR_DISCOVERY`, `ROBOTS_HARD_BLOCK`, `REQUEST_DELAY_MS` | no-manual, ethics |
| Crawl metering | wall-clock + byte + request counters → `cost_report.json` (**raw counters only**) | — | `MAX_CANDIDATES_PER_ECONOMY`, `CRAWL_DEPTH_MAX` | cost-efficiency (measured) |

**No LLM/OCR keys are used in P1** (those are P2/P3). **P1 does not emit a USD figure.** A crawl stage's real marginal cost is compute/wall-clock (~$0); converting bytes/wall-clock to dollars would require a rate assumption — an *estimate*, which violates the hard "REAL MEASURED (not an estimate)" constraint. So P1 emits **only raw measured counters** in `handoff1/cost_report.json` — `{wall_clock_seconds, total_bytes, request_count, retrieval_method_mix, docs_retrieved}` — and **explicitly defers the USD roll-up to Project 3's consolidated cost instrumentation** (P8), which owns the single measured per-document cost across all stages. There is **no `MAX_COST_USD_PER_DOC` guardrail in P1** (that key lives in the shared config for the LLM/OCR stages, not the crawler). Dependencies are **pinned** in `requirements.txt` (Playwright, pypdfium2, tenacity/backoff, jsonschema, pyyaml — all exact `==` versions; no `latest`). Playwright browser install is scripted in setup (`playwright install chromium`).

---

## 8. Rubric points Project 1 earns or protects

| Item | Pts | P1's role | Evidence artifact |
|---|---|---|---|
| **Live portal crawling** | **10 (0-or-10)** | **Owner.** Real live fetches over anti-bot/JS from **all 3** gov portals. | `crawl_log.jsonl` (every URL + status), `.headers.json` sidecars (redirect chains), `retrieval_method`, `http_status` in manifest; **3-portal smoke bundle (§10 T2b)**. |
| **PDF + HTML differentiator** | folds into crawl + citation | **Co-owner (retrieve both).** Correct `source_type` classification; HTML deep-anchor preserved. | `source_type` distribution in manifest; `anchor_hint`; stored post-JS HTML. |
| Citation fidelity (working URL) | ~10 (shared) | **Enables.** Captures resolvable `source_url` + anchor so P3's col 11 works. | `source_url` returns `<400` at retrieval; sidecar proves it. |
| OCR <5% CER | 10 | **Enables.** Correct `pdf_is_scanned` routing + ≥1 scanned doc (any in-scope economy) for the demo. | `pdf_scanned` rows exist; classifier decision logged. |
| End-to-end, no manual steps | part of Tech Resilience 30 | **Contributes.** `p1-scrape crawl` is fully non-interactive; first stage of `run_slice`. | runner chains CLI; no prompts. |
| Modular backend | 15 (shared) | **Contributes.** `CRAWL_ENGINE` swap; vendored `config/` factory pattern. | `.env` swap works. |
| Cost-efficiency (measured) | part of Architecture 30 | **Emits per-stage raw counters** (no fabricated USD). | `handoff1/cost_report.json` (wall-clock/bytes/requests). |
| NEW evidence | 20 (P3-owned) | **Protects.** Over-inclusive discovery surfaces off-baseline provisions. | candidate count > seed-law count; `seed_query` traceability. |

**The single most important sentence in this plan:** *the 10-pt live-crawl item is binary and P1 solely owns it — protect a working, logged live fetch of **all three** portals above every breadth ambition (see the §10 T2b smoke test, which banks that evidence before any adapter is finished).*

---

## 9. Repo scaffold, CLI, README

### 9.1 CLI signatures

Contract §5.3 fixes the canonical CLI as `p1-scrape crawl … / p1-scrape validate …`. The task also asks for `python scrape.py --economy Singapore --pillar 6`; we support **both** — `scrape.py` is a thin wrapper that maps friendly flags to the canonical verbs so the README Quick Start reads naturally on Windows.

```
# Canonical (used by run_slice.ps1/.sh)
p1-scrape crawl    --economy SG --pillars 6,7 --out handoff1/ [--seed-laws-only] [--dry-run]
p1-scrape crawl    --economy SG,AU,MY --pillars 6,7 --out handoff1/     # full evidence run
p1-scrape smoke    --out handoff1/                 # 3-portal live-fetch smoke bundle (§10 T2b)
p1-scrape validate --manifest handoff1/manifest.csv

# Friendly wrapper (README Quick Start)
python scrape.py --economy Singapore --pillar 6 [--out handoff1/] [--seed-laws-only]
python scrape.py --all --pillars 6,7 [--out handoff1/]      # maps to SG,AU,MY full evidence run
python scrape.py --smoke                                    # maps to `p1-scrape smoke`
python scrape.py --validate handoff1/manifest.csv
```

Flag semantics: `--economy` accepts `SG|AU|MY` (comma-separated ok) or full name (`Singapore|Australia|Malaysia`), case-insensitive, **must not crash on a misspelled/bad country** (log warning, exit non-zero cleanly — mirrors the contract's `bad_country_input` rule). `--pillars` filters seed queries. `--seed-laws-only` = deterministic vertical-slice path (seed_laws only, no query discovery). `--dry-run` = discover + log candidates, no fetch (for reviewing the frontier cheaply). `--all`/`--smoke` map to the multi-economy full-evidence run and the smoke bundle respectively.

### 9.2 README sections (Quick Start ≤ 10 min, Windows-aware)

1. **What this is / non-goals** (§1) — one paragraph, plus "produces `handoff1/`, does not OCR."
2. **Quick Start (clone → run in <10 min).** Windows-first because Python is **not reliably on PATH** (only MS Store stub): `py -3 -m venv .venv`; `.\.venv\Scripts\python -m pip install -r requirements.txt`; `.\.venv\Scripts\python -m playwright install chromium`; then the **fast path**: `.\.venv\Scripts\python scrape.py --economy Singapore --pillar 6 --seed-laws-only`. Record the absolute venv interpreter path (the top-level `run_slice` needs it).
3. **Full evidence run (reproduces the two things P1 exists to prove).** Immediately after Quick Start, document a single command a judge can run to reproduce the rubric evidence, because the fast path alone crawls *only* SG PDPA and shows neither the 3-portal live-crawl trail nor a scanned classification:
   - `.\.venv\Scripts\python scrape.py --all --pillars 6,7` (multi-economy crawl over SG/AU/MY) — produces `crawl_log.jsonl` entries for **all three portals** and at least one `pdf_scanned` row.
   - Or the cheap proof-only variant: `.\.venv\Scripts\python scrape.py --smoke` (banks one logged live fetch + `.headers.json` per portal without full discovery).
   - **Point the judge to the exact artifacts:** `handoff1/crawl_log.jsonl` (every live URL + HTTP status + redirect chain) and the `.headers.json` sidecars = reproducible proof of the **live-crawl (10 pts)** claim; `manifest.csv` `source_type` column (showing `html`, `pdf_native`, **and** `pdf_scanned`) = proof of the **PDF+HTML differentiator**.
4. **Output contract** — link to `00_contracts/` §2; show a sample manifest row + folder tree.
5. **Config keys** (§7 table) + `.env.example`.
6. **Architecture** (adapters diagram §3.1).
7. **Ethics / robots stance** (§5.1) — public-record statute pages, advisory robots, polite rate, identifiable UA. Explicit so the live-crawl approach is transparent.
8. **Provenance & license** — Apache-2.0; the §6.1 COI decision recorded here; `NOTICE` for any vendored legacy code.
9. **Contract version** targeted (§8) + how to re-sync `00_contracts/`.
10. **Troubleshooting** — anti-bot 403 (escalation ladder), Playwright browser missing, portal down (broken-URL handling).

---

## 10. Singapore-first vertical-slice task list (ordered by scoring-weight × risk)

Build order is **locked** to the thin slice: **Singapore · Pillar 6 · PDPA 2012 · one document → Hand-off #1 → (P2 → P3) → one cited row.** Ship the seam before breadth. **Exception (deliberate, not a slice violation):** the 3-portal live-fetch smoke test (T2b) runs *before* the AU/MY adapters exist. The vertical-slice lock governs the *end-to-end cited row* (which stays SG-only until T7 is green), **not** P1-internal fetch coverage — and the binary 10-pt live-crawl item requires evidence from all three portals, so banking that evidence cheaply and early is a schedule hedge, not scope creep.

| # | Task | Exit criterion | Owner-note |
|---|---|---|---|
| **T0** | Vendor pinned `00_contracts/` (schemas + `sources_sg.yaml`); wire `validate` to `manifest.schema.json`; stamp `CONTRACT_VERSION`. | `p1-scrape validate` runs on an empty/sample manifest and enforces schema + version-major gate. | Do first — nothing else validates without it. |
| **T1** | COI/IP gate on legacy SG/AU scraper (§6.1). | Written provenance decision in README; code either quarantined in `seed_import/` or explicitly not used. | **Blocking, cheap, do early.** |
| **T2** | Core: `fetcher` (Playwright + requests, headers/redirect capture, sha256), `storage` (folder layout + `.headers.json`), `crawl_logger`. | Fetch one hardcoded SSO URL live; bytes + sidecar on disk; entry in `crawl_log.jsonl`. | Proves live-crawl plumbing = the 10-pt item's spine. |
| **T2b** | **3-portal live-fetch smoke test** (`smoke.py` / `p1-scrape smoke`): bank ONE logged live fetch + `.headers.json` from `sso.agc.gov.sg`, `legislation.gov.au`, **AND** `federalgazette.agc.gov.my`, using each portal's canonical public statute/gazette URL — **independent of the full discovery/anchor logic of any adapter.** | `crawl_log.jsonl` contains ≥1 `http_status<400` fetch from each of the 3 hosts; 3 sidecars on disk. | **Protects the binary 10 pts early**, before AU/MY adapters are built, so a late MY/AU slip can't zero the item. Runs on the core fetcher alone. |
| **T3** | `classifier` (§2.3 pypdfium2 chars/page → html\|pdf_native\|pdf_scanned) + `SCAN_CHAR_THRESHOLD`. | Correctly classifies a known native PDF and a known scanned PDF in a unit test. | Routes OCR item; must always emit the flag. |
| **T4** | `sg_sso` adapter: `discover()` from `seed_laws` (PDPA 2012), `resolve()` to the statute page + PDF, extract provision `anchor_hint` (`?ProvIds=pr26-`). | `--seed-laws-only` retrieves PDPA 2012 as `pdf_native` and/or `html` with a working `source_url` + `anchor_hint`. | Deep anchor = citation-fidelity + HTML differentiator. |
| **T5** | `manifest` writer (CSV + JSONL with nested `http`) + `dedup` (sha256 + stable `doc_id` via `.idmap.json` version registry, §5.4). | `handoff1/manifest.csv` has 1 valid PDPA row; `doc_id=sg-pdpa2012-001`; re-run reuses id; a content change allocates seq 002 without renumbering; validate passes. | The join key of the whole system. |
| **T6** | `scrape.py` friendly wrapper + non-interactive `crawl`; bad-country + portal-down handled without crash; `cost_report.json` (raw counters only, §7). | `python scrape.py --economy Singapore --pillar 6 --seed-laws-only` completes non-interactively; `p1-scrape validate` green. | The "no manual steps" contribution. |
| **T7** | **Slice gate:** hand `handoff1/` to P2 (mock or real) and confirm it parses the manifest without a contract violation. | P2's `validate` accepts P1's output; the SG PDPA row flows to a P3 record (`s.26(1)`, P6-I4). | **Seam proven — this is slice success.** |
| **T8** | Ensure ≥1 `pdf_scanned` row exists for the demo, chosen to carry an **in-scope P6/P7 provision** (self-source a scanned gazette if no portal serves one, §11 R4). | A scanned PDF sits in `raw/**` classified `pdf_scanned`, and its content contains a provision that maps to an in-scope P6/P7 indicator (so Deliverable #4 yields a *correct cited row*, not just clean OCR). | Protects the OCR item + video. |

**Then, only after T7 is green:** promote the T2b smoke fetches into full adapters — Australia (`au_legislation`, HTML-heavy, deep anchors — the high-value HTML differentiator), then Malaysia (`my_gazette`, `expect_scanned:true` — biases to image-PDF capture for the OCR item and MY double-weight), then breadth (Pillar 7 seed queries, sectoral regs) and polish.

---

## 11. Dependencies, risks, mitigations

**Live crawl is the top schedule risk** — it is a binary 10 pts, it depends on third-party sites we don't control, and it is the one thing a "process pre-downloaded files" fallback cannot fake.

| ID | Risk | Likelihood/Impact | Mitigation |
|---|---|---|---|
| **R1** | **Anti-bot / IP block** on SSO or legislation.gov.au during judging (403/JS challenge). | Med / **High** (kills the 10-pt item) | Playwright stealth escalation ladder (§3.3); low polite rate; identifiable UA; **cache the raw bytes in `handoff1/raw/` at build time** so downstream never re-crawls — the live-crawl claim rests on the *logged* build-time fetch + sidecars, and judges re-run against the same portals. Document the escalation in README troubleshooting. |
| **R1b** | **robots.txt Disallow on search paths** silently blocks the fetches that earn the 10-pt item. | Med / **High** | §5.1 stance: robots is **advisory** scope guidance, not a hard block on seed-law canonical URLs (public-record statute pages). `ROBOTS_HARD_BLOCK=false` for those; search/discovery falls back to the confirmed-reachable canonical URL. Ethics stance documented in README §7. |
| **R2** | **Portal down / URL moved** at judge time (broken `source_url`). | Med / Med | `.headers.json` proves it resolved at retrieval; `sources_sg.yaml` carries the seed URL; `crawl_notes` records replacements; Project 3's `broken_url` edge rule flags it. Prefer official AGC replacement URLs. |
| **R3** | Legacy SG/AU scraper is **restricted IP** (COI). | Low / **High** (disqualification) | §6.1 hard gate before any reuse; reimplement from public docs if unclear; Apache-2.0 kept clean. |
| **R4** | **No scanned PDF available** on the SG portal (SSO is text) → nothing to seed the OCR demo from the slice economy. | Med / High (OCR item + Deliverable #4) | The contract requires a scanned row for **any in-scope economy**, not SG specifically (§2.1) — an MY federalgazette image-PDF or an AU scanned instrument satisfies it. If none is reachable in time, **self-source one scanned gazette/statute PDF that is confirmed to contain an in-scope P6/P7 provision** (data-transfer, breach-notification, retention, or DPO clause) so the Deliverable-#4 video shows a *correct in-scope cited row*, not merely successful OCR of an off-topic page. Classify it `pdf_scanned` normally. |
| **R5** | **Playwright/browser install fails on Windows** (MS Store Python stub, no PATH). | Med / Med | Setup script uses `py -3` + venv + absolute interpreter path; `playwright install chromium` scripted; README documents the exact commands; pinned versions avoid a bad `latest`. |
| **R6** | Over-inclusive discovery **balloons** into an open crawl (time sink). | Med / Med | Domain allow-list from `sources_<cc>.yaml`; candidate cap; crawl depth cap; `--seed-laws-only` deterministic path for the slice and the demo run. |
| **R7** | **Contract drift** across the 3 repos (manifest field renamed / miscounted). | Low / High (stated #1 integration risk) | Vendored pinned `00_contracts/`; `validate` against `manifest.schema.json` is the **single source of truth** for the required-field set (this plan's §2 restatement is convenience only); `CONTRACT_VERSION` major gate (§8); never edit the frozen manifest schema unilaterally — amendments go through the §8 PR/bump process. |

**Upstream dependency:** `00_contracts/instrument/sources_sg.yaml` must exist with the PDPA seed law + SG portal roots before T4 — but this is now cheap: seed it directly from `Knowledge Portal/Resource Library/Sample governemnt portals_Pillar 6_7.csv` (§4.1), which already contains SG's laws + `sso.agc.gov.sg` URLs. If P0 isn't formalized yet, a one-row `sources_sg.yaml` (PDPA 2012 + SSO root) unblocks the slice and is reconciled when P0 lands. **Downstream dependency:** Project 2 consumes `handoff1/` — coordinate the T7 seam test early with a mock P2 `validate` so a schema mismatch surfaces on day one, not on 19 July.
