# Stage result — collection (p1-scrape), 2026-09-23

**What this stage was for.** Build, for each economy in the final round, a corpus of official legal texts that the
extraction stage can read: fetched from official sources, recorded so every document can be traced back to the page
it came from, and re-checkable later for what has changed.

**Status: closed for six economies.** Five are engine-driven corpora; China is a hand-and-tool collection with a
different shape, for reasons of law rather than convenience (below).

---

## 1. What exists

| Economy | Corpus | Documents | Size | Rows flagged | Portal |
| :---- | :---- | ----: | ----: | ----: | :---- |
| **Malaysia** | `MY_corpus_2026-09-15` | 1,391 | 0.95 GB | 178 (12.8%) | `lom.agc.gov.my` |
| **Singapore** | `SG_corpus_2026-09-16` | 738 | 0.19 GB | 6 (0.8%) | `sso.agc.gov.sg` |
| **Australia** | `AU_corpus_2026-09-19` | 1,278 | 0.80 GB | 91 (7.1%) | `legislation.gov.au` |
| **Timor-Leste** | `TL_corpus_2026-09-20` | 1,921 | 3.99 GB | 146 (7.6%) | `mj.gov.tl/jornal` |
| **Lao PDR** | `LA_corpus_2026-09-21` | 1,762 | 3.67 GB | **1,695 (96.2%)** | `laoofficialgazette.gov.la` |
| **China** | `CN_sources_2026-09-21` | 1,085 | — | — | not one portal; see §4 |

**7,090 documents in five corpora, plus 1,085 for China. 9.6 GB of stored law.** Every corpus validates against
contract 0.2.0 with **0 errors and 0 warnings**.

All of it is under `outputs/<CC>/`. **`outputs/<CC>/README.md` is the index for each economy** — one row per run and
corpus, saying what it was and what it stored. Start there, not in the folders.

### Where the documents came from

Scope is **every principal law the portal lists**, not only the pillar 6 and 7 ones. The registries' title rules
*mark* relevant laws — they steer where the expensive per-act work goes (reading timelines, taking subsidiary
legislation, crawl order) and never limit what is fetched.

| Economy | Listed | In scope | Marked relevant |
| :---- | ---: | ---: | ---: |
| Malaysia | 1,291 | 1,246 | 111 |
| Singapore | 877 | 846 | 9 |
| Australia | 4,776 | 1,275 | 20 |
| Timor-Leste | 4,788 | 4,739 | 863 |
| Lao PDR | 1,773 | 1,773 | 322 |

Australia's gap is not a shortfall: the 3,501 not crawled are amending and consequential acts that the Federal
Register compiles into the principal act, so they are listed and recorded rather than missed.

---

## 2. What the extraction stage receives

Each corpus folder holds:

| Path | What it is |
| :---- | :---- |
| `manifest.csv`, `manifest.jsonl` | **The corpus in the Hand-off #1 shape** — one row per document. This is what to read |
| `raw/` | the documents and their header sidecars, under their original paths |
| `links_used/documents.jsonl` | one link row per document, with `contract_meta.content_flags` and which run it came from |
| `law_table.csv` | one row per law: in force or not, effective date, last amendment, status source |
| `superseded.jsonl` | every older copy a newer run replaced, and what it matched on |
| `corpus_meta.json` | per-run counts, validation result |
| `CORPUS_NOTE.md` | what came from where, in words |

`raw/` is **not in git** (`outputs/**/raw/` is ignored; 19 GB). Everything that *describes* the documents is
tracked, so every claim in this document can be checked from the repository alone.

---

## 3. Quality — read this before using any corpus

Convention rule 6 is **flag, do not fix**: a stored file that is not the law's text stays exactly as the portal
served it, flagged, so extraction knows and the portal can be told. Flags are per row in
`links_used/documents.jsonl` and summarised in each `CORPUS_NOTE.md`.

**The one figure that changes how you plan extraction:**

> **96% of Lao PDR's corpus has no text layer.** 1,695 of 1,762 documents are scans. The Lao Official Gazette
> publishes images, not text. **Nothing can be extracted from Lao PDR without OCR**, and OCR of Lao script is a
> project in itself. This is a property of the source, not a defect in the collection.

The rest, by economy:

- **Malaysia, 178 flagged.** The ones that matter: **76 `repeal_notice`** (the stored file is a repeal notice, not
  the act), **56 `no_text_layer`**, **5 `other_act_text`** (a different act altogether), 7 `language_mismatch` (a
  Malay file behind an English link). Also 90 `short_principal` — suspiciously short, not necessarily wrong.
- **Timor-Leste, 146 flagged**: 65 `short_principal`, 35 `no_sumario`, 29 `no_text_layer`, 14 `duplicate_content`,
  4 `not_a_gazette_issue`, 4 `act_not_in_text`.
- **Australia, 91 flagged**: 88 `as_made_short_act`, 2 `renamed_since_enactment`, 1 `short_principal`. Low risk —
  as-made texts are short because they are short.
- **Singapore, 6 flagged**: 5 `short_principal`, 1 `duplicate_content`. Effectively clean.

**In plain terms: Singapore and Australia can be extracted as they stand; Malaysia needs roughly 137 documents
treated as suspect; Timor-Leste needs about 80; Lao PDR needs an OCR decision before anything else.**

---

## 4. China is a different shape, deliberately

China is **not an engine adapter and has no manifest**. The reason is legal, not technical: the 立法法 splits
publication into two channels. Laws and administrative regulations are published by the legislature (the national
database); **departmental rules are filed with the State Council, not the NPC, and appear only on each ministry's
own site**. One portal cannot hold China's operative tier.

On top of that, `flk.npc.gov.cn` — the national database — **forbids automated collection in robots.txt**, and MIIT
and Customs refuse an honest client (403 and 412). So:

| Layer | What | How | Count |
| :---- | :---- | :---- | ----: |
| 1 | the national database | downloaded by hand, indexed offline | **945** |
| 2 | CAC (`cac.gov.cn`) | crawled whole — its index is 88% relevant | **111** |
| 2 | `gov.cn` | verified links, crawled | 6 |
| 2 | MIIT | by hand, plus 6 fetched from hosts that permit us | 23 |
| — | twelve further sources | deferred, files kept, on the watch list | — |

`countries/cn-china/SOURCES.md` records **why every source is in, deferred, unusable or not collected**, including a
section on what this round did not do well.

**What China needs before extraction can read it like the others: a manifest in the contract's shape.** It does not
have one. The corpus is a folder per source, each with a `provenance.tsv`, and layer 1 is eleven `.zip` archives of
`.docx` files. Building that manifest is the first China task of the next stage.

---

## 5. Keeping it current

Every economy has an update check that asks the portal what changed instead of re-crawling:
`python -m <country>.updates` for the five engine economies, `countries/cn-china/tools/update.py` for China. Each
writes its own dated folder with `changes.md`.

**Every economy's check has been run live at least once** — Malaysia 3, Timor-Leste 2, Lao PDR 2, Singapore 1,
Australia 1, China 1.

**Two rules govern what an update can claim:**

- **Rule 11 — every update says what it cannot see.** No economy's evidence sits on one website. Each keeps
  `updates/watchlist.tsv`, every source the check does *not* collect, and **the check prints that list before it
  runs and again when it finishes**. A check is not a complete update until those have been looked at by hand.
- **Rule 13 — a source that refuses us is updated by a person, and the tool prepares that walk.** Where a host
  refuses an honest client, nothing automatic will ever report that a rule was amended. Those documents are marked
  `update_check` in their provenance sheet, and a worklist is generated with **the exact address of every document
  held**, so the check is a comparison and not a search.

**Rule 14 — the customs and tariff source stays manual in every economy, by decision.** Tariff schedules, de
minimis thresholds and cross-border e-commerce notices answer indicators 1.4, 12.2, 12.5 and 12.6, and are the
least automatable material in the instrument: mostly not legislation, published as PDF schedules, HS-code lookups
and announcements, in a different shape in every economy. Each watch list now carries **the exact page** for its
economy's tariff and de minimis, verified 2026-09-22. **At scoring time the researcher opens the link, reads the
figure, and records the figure, the page and the date read.** Details and eight traps found while verifying them
are in `notes/2026-09-22_layer2-updates-and-the-customs-source.md` — including that Singapore did **not** abolish
its S$400 relief in 2023, and that Timor-Leste's import duty is 5%, not the 2.5% most sources report.

---

## 6. Evidence

- **Tests.** China: 51 offline tests, verified 2026-09-23. The other suites were last verified in a clean sandbox
  on 2026-09-22 — Malaysia 175, Singapore 36, Australia 33 (plus 9 engine), Timor-Leste 36, Lao PDR 60 with 1
  expected failure, shared tools 22, the engine's own 25. **Total 438 tests and 1 expected failure**, of which only
  China's 51 have been re-run since the watch lists gained a column on 2026-09-22.
- **Audits.** `tools/audit_run.py` reads the first pages of every stored file and writes `audit.md` / `audit.json`
  into each run folder. That is where the flag counts above come from.
- **Politeness.** Every request goes through a paced client: robots.txt read first and recorded with the date, at
  least 3 s between requests to a host plus the host's own `Crawl-delay` when longer, one request at a time,
  rest-and-slow-down on 429 and 503, and **a refusal is never retried with a different client**. Per-request logs
  are in each run's `logs/` and `crawl_log.jsonl`.
- **The workshop audit of 2026-09-22** (`notes/WORKSHOP_AUDIT_2026-09-22.md`) checked every country folder against
  the conventions and every suite in a sandbox rebuilt from the documented install steps.

---

## 7. What is not done, and who should do it

**Needs a decision from the next stage:**

1. **Lao PDR and OCR** — 96% of its corpus is images. Extract with OCR, or treat Lao PDR as evidence-by-hand?
2. **China's manifest** — the corpus has no contract-shaped manifest. Someone must build one.
3. **The flagged files** — 137 Malaysian and ~80 Timor-Leste documents are suspect. Re-fetch, exclude, or carry
   the flags into extraction and let scoring see them?

**Known gaps, recorded where they occur:**

- Malaysia's `legal_status` is `unknown` for 1,135 of 1,291 laws — honest, not defaulted, but the law table cannot
  state in-force status for most acts.
- China: `电信网码号资源管理办法` is held only as a text-less print; the 2024 consolidated `进网管理办法` was not taken;
  four documents were declined, **including the only source for indicator 5.1**; Customs' 公告 section is untriaged.
- China's layer-1 export lacks at least one law (固体废物污染环境防治法), so a bulk download is not guaranteed complete.
- MIIT's own rule tier (部门规章, 规范性文件) was never enumerated — only its 法律法规 section was walked.

**Hand-backs to the engine repository** (read-only from this workshop, listed in `countries/README.md`):
`cryptography==44.0.0` in `requirements.txt`; delete `tests/test_my_selection.py`; Timor-Leste's and Lao PDR's
engine changes (economy code, adapter registry, manifest schema, slug). One Lao test is an expected failure until
the last of these lands.

**Two shared-code defects awaiting a decision**, because they change behaviour in code four countries import:
`catalogue._cell` collapses whitespace inside a URL, and `merge_corpus.identity()` ignores language — the second
cost Lao PDR 53 documents.

---

## 8. What this stage deliberately did not do

- **It did not read the gold set.** Rule D4: no source, seed or target was chosen from the previous database.
  Where the host's earlier coding was counted, it is disclosed as a cross-check only and nothing was selected from
  it (`countries/cn-china/SOURCES.md`).
- **It did not defeat any refusal.** Where robots.txt forbids, nothing was sent. Where a host refuses an honest
  client, documents were collected by hand in a browser — the user-agent was never changed to evade a block, no
  certificate check was disabled, and a browser was never driven to get past a 403.
- **It did not fix wrong files.** They are stored as served and flagged.
- **It did not automate the customs source** in any economy — see rule 14.

---

## Where to read further

`CONVENTIONS.md` — the rulebook, 14 rules · `POLICY.md` — what to fetch and how politely · `CONTRACT.md` — the
hand-off shape · `outputs/<CC>/README.md` — each economy's runs · `countries/<cc>-<name>/NOTES.md` — each
economy's ten-section record · `notes/` — the cross-economy problems, one file each.
