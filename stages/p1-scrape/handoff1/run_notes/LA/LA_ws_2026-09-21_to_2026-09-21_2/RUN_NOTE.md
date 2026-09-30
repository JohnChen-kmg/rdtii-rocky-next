# Run note: LA_ws_2026-09-21_to_2026-09-21_2

Lao PDR, **the second update check and its delta crawl**, 21 September 2026. It re-ran the check of two hours
earlier against a corrected census, and crawled what it found.

## Read this first

- **The check is now right.** 1,760 `unchanged`, **13 `not_stored`, and zero `document_moved`** — against 46
  `document_moved` in the first check, 42 of which were an artefact of our own census
  (`../LA_ws_2026-09-21_to_2026-09-21/RUN_NOTE.md`). The delta is the 13 documents the first crawl really did
  not get.
- **Four of the 13 were recovered, and they were ours to lose.** All four are addresses the listing writes with
  an HTML entity — `&#039;` for an apostrophe — which the parser left in the path, so the first crawl asked for
  a file that does not exist. With the entity resolved they fetched first time: the **People's Court Law**, the
  **Lao Women's Union Law**, the Law on Officers of the Lao People's Army and the Lao People's Revolutionary
  Youth Union Law.
- **Eight of the other nine failed again, and that is the answer.** The same addresses, fetched a second time
  with corrected code, returned the portal's catch-all page again: links the gazette publishes and does not
  serve, confirmed twice rather than assumed once. **The ninth is a format, not a dead link.** LA-2120 returns a real Word
  document — `content_type: application/vnd.openxmlformats-officedocument…` on both attempts. `CONTRACT.md`
  3.2 allows `source_type` of only `html`, `pdf_native` or `pdf_scanned`, so there is nowhere to put a Word
  file and the engine correctly declines it. Its **Lao text is held**; only the English rendering is not.
- **The corpus is built from this run and the first one:** `LA_corpus_2026-09-21`, 1,762 documents. **Read its
  entry in `outputs/LA/README.md` before using it — it does not contain the 53 English translations**, for a
  reason that is a defect in a shared tool, not in this country's data.

## At a glance

| | |
| :---- | :---- |
| Country | Lao PDR (`LA`) |
| Run type | Update check against `LA_ws_2026-09-21` (pinned with `--baseline`), **with its delta crawl** |
| Date | 2026-09-21 |
| Time, UTC | Check 06:30:33 to 06:58; crawl 07:00 to 07:02 |
| Requests | **193** for the check, **13** for the crawl |
| Verdicts | 1,760 `unchanged`, 13 `not_stored`, 0 `document_moved`, 0 `new_law`, 0 `status_changed`, 0 `delisted` |
| Result | 13 attempted: **4 stored**, 9 failed (8 unserved by the portal, 1 refused by our classifier) |
| Validation | `manifest has 4 row(s); validate OK [contract 0.2.0]` |
| Audit | 4 read, 3 flagged `no_text_layer`, 9 `fetch_failed` |
| Status | **Usable.** Its four documents are in `LA_corpus_2026-09-21` |

## Why this check was re-run

The first check compared today's addresses against `links_used/laws.csv`, and 46 of those addresses had been
flattened by the shared CSV writer: `_cell` collapses runs of whitespace so a cell stays on one line, and **42
of this portal's filenames contain two consecutive spaces**. The documents had been fetched correctly all along
— only the census disagreed with them.

Three things were changed before this run, and this run is the proof they worked:

| Change | Evidence here |
| :---- | :---- |
| Lao PDR's own CSV writer leaves URL columns alone (`_URL_COLUMNS`, `_cells`) | 0 `document_moved`, against 46 |
| The link list was rebuilt with that fix and installed as the crawl run's `links_rebuilt/` | The census now agrees with `documents.jsonl` on every address |
| `updates/baseline.py` prefers a run's `links_rebuilt/` over its frozen `links_used/` | The check read the corrected census without anyone rewriting what the first crawl replayed |

## What it found

| Verdict | Laws | Fetched |
| :---- | ----: | :---- |
| `unchanged` | 1,760 | — |
| `not_stored` | 13 | Yes, all 13 |
| `new_law` | 0 | Nothing was published between the two checks |
| `status_changed` | 0 | No law changed its status word |
| `document_moved` | 0 | — |
| `delisted` | 0 | — |

## What the crawl got, and what it did not

**Recovered — ours, now fixed:**

| Law | Why it failed the first time |
| :---- | :---- |
| LA-1508 ກົດໝາຍວ່າດ້ວຍ ສານປະຊາຊົນ (People's Court Law) | `People&#039;s Court Law.doc to EOG.pdf` |
| LA-446 ກົດໝາຍວ່າດ້ວຍ ສະຫະພັນແມ່ຍິງລາວ (Lao Women's Union) | `Women&#039;s_Union Law.pdf` |
| LA-1385 ກົດໝາຍ ວ່າດ້ວຍນາຍທະຫານກອງທັບປະຊາຊົນລາວ | `The military commander of the Lao People&#039;s Army.pdf` |
| LA-516 ກົດໝາຍວ່າດ້ວຍ ຄະນະຊາວໜຸ່ມປະຊາຊົນປະຕິວັດລາວ | `The young people&#039;s revolution Law.pdf` |

**Served by the portal, but in a format the contract has no place for** — one document:

| Law | What happened |
| :---- | :---- |
| LA-2120 ດຳລັດວ່າດ້ວຍ ກອງທຶນເລືອດ | `Decree on Blood Fund No 258GOV - 23082023.docx`. The portal **serves it**, twice, as a real Word document. `CONTRACT.md` 3.2's `source_type` has only `html`, `pdf_native` and `pdf_scanned`, so there is nowhere to record it; declining is correct, not a defect. **This law's Lao text is held** — only the gazette's English rendering is not |

**Still not served by the portal, on a second attempt with corrected code** — these eight answered HTTP 200
with the site's own page:

| Law | The address the portal publishes |
| :---- | :---- |
| LA-1818 ດຳລັດ ວ່າດ້ວຍຂອບວຸດທິການສຶກສາແຫ່ງຊາດ | `Eng 566 ລບ 2021.pdf` — the English column only; **the Lao text of this law is held** |
| LA-912 ດຳລັດ ວ່າດ້ວຍສະມາຄົມ | `ດຳລັດ ວ່າດ້ວຍສະມາຄົມ.pdf` |
| LA-735, LA-698, LA-699 | `7. ດຳລັດ …`, `8. ຄຳສັ່ງ ຂອງລັດຖະມົນຕີ .pdf`, `9. ຄຳສັ່ງ ຂອງລັດຖະມົນຕີ .pdf` |
| LA-1055 | `scan0002.pdf` |
| LA-1518 | `0651ອຄກຄພນ2019.pdf` |
| LA-674 ຄຳແນະນຳ … ການປະກັນສັງຄົມ | The address carries **zero-width spaces** (U+200B) between syllables — a mistyped link in the portal's own CMS |

Each keeps its row in the census with its status and dates, and each is `not held` in `law_table.csv`. Nothing
was substituted and no address was repaired by hand (decision 17: flag, do not fix).

**LA-674 was tested, not guessed at.** Its address carries 20 zero-width spaces, which made it look like a
mistyped link to a file that exists. A probe of 2026-09-21 (5 requests) tried it with the zero-width spaces
removed, with the trailing space trimmed, and with both, and got the catch-all page every time — as did LA-698
and LA-699 with their trailing spaces trimmed. The files are not on the server under any name that can be
constructed (`countries/la-lao-pdr/NOTES.md` 6).

## Politeness

206 requests in all (193 + 13) at `REQUEST_DELAY_MS=6000` plus jitter, one at a time, one process against the
host. **No refusal of any kind.** Across the whole day — exploration, three probes, three link-list builds, the
crawl, two checks and this delta — the portal has taken roughly **4,300 requests** from us without once
returning a 403, a 429 or a challenge. The delay is ours: this host publishes no robots.txt.

## What is in this folder

| Path | What it is |
| :---- | :---- |
| `RUN_NOTE.md` | This note |
| `changes.md`, `changes.json` | The 13 verdicts and the 1,760 unchanged |
| `links_used/` | The delta list (13 rows) and the full census of 1,773 laws as read at 06:30 UTC |
| `manifest.csv`, `manifest.jsonl`, `raw/` | The four recovered documents |
| `audit.md`, `audit.json`, `cost_report.json`, `crawl_status.json`, `.idmap.json`, `logs/` | The usual |

## Issues encountered

1. **The 42 false `document_moved` of the first check** — diagnosed, fixed, and proved fixed here. The shared
   `_cell` still needs the same exemption for Singapore, Australia and Timor-Leste
   (`countries/la-lao-pdr/NOTES.md`, "Shared-file edits still to make", item 5).
2. **The corpus drops all 53 English translations.** `tools/merge_corpus.py` identifies a document by
   `(portal_id, document_kind)` and **not by language**, so each translation is filed as an older copy of its
   own Lao law and excluded. They are listed in `LA_corpus_2026-09-21/superseded.jsonl` and every file is still
   in the run folders, so nothing is lost on disk — but the folder downstream reads has none of them, and
   `law_table.csv` says so plainly: 55 laws list a translation, the corpus holds 0. The one-line fix is queued
   as shared-file edit 6.
