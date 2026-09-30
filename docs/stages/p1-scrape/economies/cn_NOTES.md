# China (CN) — notes

The general note in the layout every country keeps (`CONVENTIONS.md` section 4). China is not an engine adapter, so
several sections point to the files that already say more: **`SOURCES.md`** (why each source is in or out),
**`WORKFLOW.md`** (how to run everything), `README.md` (the tools), and `outputs/CN/CN_sources_2026-09-21/README.md`
(the corpus). Written 2026-09-22.

## 1. The website

### 1.1 The sites and hosts used

| Layer | Host | robots.txt, read 2026-09-21 | Delay |
| :---- | :---- | :---- | :---- |
| 1 | `flk.npc.gov.cn` — the national database | **forbids automated collection** | by hand |
| 2 | `www.cac.gov.cn` | permits; `/zfz/`, `/wxb_zfz/`, `/wxzf/` and one video path disallowed | 8–12 s |
| 2 | `www.gov.cn` | permits; legacy paths only | 8–12 s |
| 2 | `www.miit.gov.cn` | refused, 403 — robots.txt included | by hand |
| 2 | `www.customs.gov.cn` | 412, and a certificate Chrome rejects | by hand |

Every host considered, with its verdict, is in `SOURCES.md` and `countries/_finale-survey/robots_2026-09-21.json`.

### 1.2 What the portals look like

China publishes its law through two channels fixed by the 立法法: the legislature's (laws and administrative
regulations, in the national database) and the executive's (departmental rules and normative documents, on each
ministry's own site). `SOURCES.md`, "Why China needs more than one source". How each automatic source is read —
CAC's JSON index, SAMR's and MOFCOM's JPAAS API, the gazette's `gbgl.json` — is in `README.md`.

### 1.3 What to watch for

`WORKFLOW.md` section 7. The ones that cost the most time: CAC writes `href` unquoted; JPAAS returns 99 rows for
`pageSize=100`; a ministry page is often only a wrapper and the law is in its attachment; MIIT's 法律法规 list stops at
2022-01-29 and shows no in-force status.

**And how a hand-saved file is saved decides whether it can be read at all.** Windows' "Microsoft Print to PDF"
printer converts Chinese glyphs to vector outlines: the file looks perfect and holds no text. Check the first file
of any batch with `tools/checkdocs.py` (`CONVENTIONS.md` rule 12).

## 2. How our scraper works

### 2.1 The big picture

```
layer 1   flk.npc.gov.cn --(by hand, bulk)--> manual/npc-database/raw/*.zip --layer1.py--> index.csv   945 documents
layer 2   CAC index --collect.py--> auto/cac/            111 documents
          gov.cn    --collect.py--> auto/govcn/           6 documents
          MIIT, Customs --(by hand, triage.py)--> manual/miit/, manual/customs/
update    update.py: layer 1 offline against a fresh export; CAC and gov.cn live; the watch list before and after
```

### 2.2 The code

`countries/cn-china/tools/`: `polite.py`, `collect.py`, `update.py`, `layer1.py`, `triage.py`, `checkdocs.py`, `manual_check.py`; the
watch list is printed by `../my-malaysia/scraper/watchlist.py`. Described in `README.md`.

### 2.3 What goes into the link list

There is no engine link list. For CAC the listing is `auto/cac/list.csv`; for layer 1 the export's `index.csv`; for
the manual hosts, each folder's `provenance.tsv`, pre-filled with what to download.

### 2.4 Politeness

One request at a time per host, 8–12 s apart, an honest fixed User-Agent, robots.txt read first, a refusal never
retried with another client, rest and slow down on 429 and 503 — all in `tools/polite.py`, and tested
(`tests/test_cn.py`).

### 2.5 What the engine must change

Nothing: China does not use the engine. If a Chinese source is ever read through the engine, the economy code, the
adapter registry and the manifest schema would need the same changes Timor-Leste and Lao PDR needed.

### 2.6 The update check

`tools/update.py`, **and a worklist for the half it cannot reach** (`tools/manual_check.py`, rule 13): MIIT and
Customs refuse us, so 23 of the collection's documents can only be re-checked by a person, each with its address
in `MANUAL_UPDATE_CHECK.md`. First live run 2026-09-22: 12 requests, all HTTP 200, nothing changed
(`outputs/CN/CN_sources_2026-09-21_to_2026-09-22`). **Layer 1 is only compared when a fresh export is passed**, and it
is the most important part of an update.

## 3. Runs

| Run | What | Result |
| :---- | :---- | :---- |
| `outputs/CN/CN_manual_2026-09-20` | five administrative regulations, by hand | the database carries articles, not attachments |
| `outputs/CN/CN_ws_2026-09-21` | CAC's index, crawled | 111 of 111; 42 tier-2 documents a hand-built list had missed |
| `outputs/CN/CN_layer2_2026-09-21` | a six-document browser probe, set aside | a method tested and ruled out |
| **`outputs/CN/CN_sources_2026-09-21`** | **the corpus, one folder per source** | layer 1 945; CAC 111; gov.cn 6; MIIT and Customs by hand; 12 sources deferred |
| `outputs/CN/CN_sources_2026-09-21_to_2026-09-22` | the first update check | nothing changed |
| MIIT by hand, 2026-09-22 | the 法律法规 section walked, all 7 pages | 18 of 165 taken; **all 18 need re-saving**, no text layer |

## 4. Output format against `CONTRACT.md`

**Not on the contract.** Every other country hands extraction an engine manifest (`manifest.csv`, `manifest.jsonl`) in
the Hand-off #1 shape. China's corpus is a folder per source, each with a `provenance.tsv`, and layer 1 is eleven
`.zip` archives of `.docx` files. **A manifest in the contract's shape still has to be built** before stage 2 can read
China the way it reads the others — one row per document, with the version date the file names carry. Recorded as a
question to the extraction workshop in `RDTII Finale Plan/3_Final_Stage/ISSUES/2026-09-21_update-watchlist.md`.

## 5. Open choices for the developer

- Whether to crawl `www.npc.gov.cn`, which permits us, as the signal that layer 1 needs a fresh export (`SOURCES.md`).
- Whether judicial interpretations count as evidence for 4.01, 4.2, 4.3 and 4.1 — a question for the instrument.
- Which deferred source to bring back if a live test draws one of the 18 indicators deferring left on layer 1 alone
  (`outputs/CN/CN_sources_2026-09-21/_deferred/README.md`).
- Whether the watch-list reminder should become a gate (decision (l) of the finale plan's issue record).
- **How layer 2 should be collected in a later round** (the developer, 2026-09-22, closing this one): systematically
  rather than selectively — an automatic collector per ministry section where the host permits it, as CAC was taken
  whole, so relevance is decided in the corpus and not at the point of collection. MIIT's 部门规章 and 规范性文件
  sections were never enumerated at all. Argued in `SOURCES.md`, "What this round did not do well".

## 6. Known gaps

- **No contract-shaped manifest** (section 4).
- **The layer-1 export is not guaranteed complete**: it lacks at least one law (固体废物污染环境防治法).
- **MIIT's 法律法规 section is walked in full** — all seven pages, 165 items, 18 taken (11%), downloaded 2026-09-22.
  **Two things remain there**: the 18 files carry no text layer and must be saved again (rule 12), and the
  **部门规章 and 规范性文件 categories are not yet walked** — the rule tier lives there, not in 法律法规, which holds
  the laws MIIT did not write. Only 2 of this folder's 13 verified MIIT documents appear on the list that was walked.
- The 11 MIIT documents already verified by link are not yet downloaded, including 工业和信息化领域数据安全管理办法
  （试行）and the 2024 增值电信 opening pilot.
- **Two held MIIT rules are superseded, found 2026-09-22 by the cached gazette**: 无线电频率划分规定 (now 令62,
  in force 2023-07-01) and 通信短信息服务管理规定 (now 令74, in force 2026-05-01). The new texts are in
  `manual/miit/mirror_permitted/`, fetched from gov.cn; the old ones are kept as history.
- **6 of the 23 MIIT documents now have a machine-readable copy** from a permitted host
  (`manual/miit/mirror_permitted/`). The other 17 still need saving again in a browser (rule 12).
- **MIIT is closed with three known holes**, all recorded on its sheet: 电信网码号资源管理办法 is held only as a
  text-less print, so extraction cannot read it; the 2024 令68 进网管理办法 was not taken, leaving the superseded
  2014 text; and four documents were declined, **including the only source for indicator 5.1** (telecom
  infrastructure sharing).
- Customs' 公告 section is not yet triaged.
- The 26 links recovered by the multi-link fix are unfetched; they sit in deferred folders.

## 7. Round 1 corpus, against the portal

China was not in Round 1. It appears first in the Round 2 host database.

## 8. Dead ends

- **Driving a browser to get past MIIT's and NDRC's 403** — tested on six documents on 2026-09-21 and ruled out by the
  developer the same day (`outputs/CN/CN_layer2_2026-09-21/RUN_NOTE.md`).
- **The State Council Gazette as the rule tier's source** — it gives a rule's text as issued, not the text in force;
  its index was stopped at 180 of 936 issues and deferred (`SOURCES.md`).
- **`moj.gov.cn`'s 国家规章库** — its robots.txt answers with a bot trap.
- **Taking SAMR's and MOFCOM's sections whole** — 18% and 22% relevant; deferred.

## 9. Evaluation only

Counts over the host's coding, **never a seed** (rule D4): the finale plan's research reports the host's 111 China rows
citing `gov.cn` 62 times, `flk.npc.gov.cn` 19 and `cac.gov.cn` 17, and MIIT zero times. Disclosed in `SOURCES.md`;
nothing was selected from it.

## 10. Files, hand-back and evidence

Nothing is handed back: China has no engine package. The evidence behind this note is the run notes under
`outputs/CN/`, the watch list (`watchlist.tsv`), the robots readings (`countries/_finale-survey/robots_2026-09-21.json`),
the checklist and links files (`outputs/CN/CN_layer2_checklist.md`, `CN_layer2_links.md`) and the tests
(`tests/test_cn.py`, fixtures saved 2026-09-21).
