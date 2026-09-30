# Run note: TL_ws_2026-09-20

Timor-Leste, **the first crawl**, 20 September 2026: every gazette issue the Jornal da República lists, from the
link list built the same morning.

## Read this first

- **1,935 of 1,953 documents stored**, 3.9 GB, covering **4,707 of the 4,788 acts** the portal lists. The portal
  never refused us: 1,953 requests at its own `Crawl-delay: 10`, no 403, no throttling, over 8½ hours.
- **A document here is a gazette issue, not an act.** 923 issues carry more than one act; one carries 39. So the
  manifest is shorter than the law table by design, and a manifest row joins to its acts through
  `contract_meta.contains`.
- **Three engine defects were found and worked around in the sandbox.** None of them is in this country's code,
  and all three must be fixed in the repo before the freeze if a fourth economy is to be real (below).
- **The corpus is built:** `TL_corpus_2026-09-20`, 1,921 documents, 14 superseded, **validation OK**. That is what
  downstream reads.
- **30 documents are scans with no text layer** (1.6%). The exploration had sampled two years and found native
  text; the full crawl shows a minority of older issues are images. Timor-Leste is still the cheapest country for
  extraction, but it is not OCR-free.

## At a glance

| | |
| :---- | :---- |
| Country | Timor-Leste (`TL`) |
| Run type | First crawl, scope `all`, from `links_used/documents.jsonl` (built 2026-09-20 05:56 UTC) |
| Time, UTC | 06:27:43 to 13:53:32, then a resume 13:55:08 to 14:52:57 |
| Time, machine clock | US Eastern Daylight Time, UTC−4: 02:27 to 10:52 |
| Pace | `REQUEST_DELAY_MS=10000`, the portal's stated `Crawl-delay` |
| Listed | 1,953 documents, carrying 4,788 acts |
| Stored | **1,935** (1,684 in the first pass, 251 in the resume) |
| Size | 3.9 GB |
| Audit | 1,935 read, **160 flagged**, 17 missing. Rules: `TL` |
| Law table | `law_table.csv`, 4,707 acts covered by the stored issues |
| Corpus | `TL_corpus_2026-09-20`: 1,921 documents, 14 superseded, validation OK |

## The three engine defects this crawl found

Each was patched **in the sandbox copy only** so the crawl could finish. The repo is untouched, and each is a
hand-back request (`countries/README.md`).

| What happened | Where | The fix used here |
| :---- | :---- | :---- |
| `WARN unrecognized economy 'TL' — skipping; nothing to crawl.` The engine hard-codes the three economies | `economies.py`, `adapters/registry.py` | `TL` added to both. The repo fix is `PLAN.md` 1A-2/1A-3: read the codes from the YAML headers |
| **254 documents downloaded and then lost**: the storage folder is the whole law title slugified, and Portuguese titles push the path past Windows' 260-character limit | `utils.slugify`, used by `storage.py` | Capped at 80 characters with a hash suffix, so it stays deterministic. Recovered all 254 on the resume |
| `economy: 'TL' is not one of ['SG','AU','MY']` and `doc_id … does not match '^(sg\|au\|my)-…'` — the manifest schema enumerates the three | `contracts/schemas/manifest.schema.json` | Widened to `^[A-Z]{2}$` and `^[a-z]{2}-…`, which is exactly what `CONTRACT.md` already proposes for 0.3.0 |

A fourth appeared in our own shared tool: `merge_corpus.py` placed files under the run's folder names, and a
corpus path is four characters longer than a run path, so folders that just fitted overflowed. It now caps folder
names the same way. That one **is** ours and is fixed in the workshop, not only in the sandbox.

## What is missing, and why

**18 of 1,953 documents were not stored.** Every one is the portal's own defect, not ours:

| Cause | Count | Detail |
| :---- | ----: | :---- |
| HTTP 404 | 12 | The listing links to a file the portal does not serve. Dead links, spread over 2013 to 2015 |
| A link that lost its host | 5 | The row says `http://public/docs/…`: the host is missing and `public` was read as one. **The parser now repairs these**, so the next list build recovers them |
| The gazette's former domain | 1 | A row points at `www.jornal.gov.tl`, which no longer answers. Left as the portal states it, flagged `document_on_another_host`: rewriting a stated address would be fixing, not flagging |

They are listed in `audit.md` as `fetch_failed`, and each keeps its row in `links_used/laws.csv`.

## What the audit found

| Flag | Count | What it means |
| :---- | ----: | :---- |
| `short_principal` | 65 | A principal act of one or two pages. Normal here: many decrees are short |
| `no_sumario` | 35 | An issue whose contents page could not be read — often a scan |
| `no_text_layer` | 30 | A scanned issue. These need OCR; the rest do not |
| `duplicate_content` | 28 | 14 pairs: the same issue listed twice, once relative and once as `http://mj.gov.tl/…`. **The parser now canonicalises the host**, and the corpus already collapsed them to 14 superseded rows |
| `orphan_file` | 28 | Files under `raw/` with no manifest row: the 254 failed stores left bytes behind before the resume rewrote them |
| `not_a_gazette_issue` | 4 | Neither an issue nor a per-law extract. Worth a person's eye |
| `act_not_in_text`, `acts_not_in_text` | 4 | A file that does not contain the act the listing promised |

**The rules were corrected during this run.** The first audit flagged 718 documents, 277 of them
`not_a_gazette_issue`; 105 of those were **per-law extracts** (`…/leis_parlamento_nacional/6_2005.pdf`), which
carry one act and no masthead, and 418 more were one-page issues, which are normal. `RULES["TL"]` now knows both
shapes, and the count fell to 160 real findings.

## Issues

1. **Not every Timorese PDF is native text** (30 scans). `NOTES.md` 1.2 said no OCR was needed anywhere, on a
   sample of two; corrected there.
2. **The 17 `fetch_failed` rows will be retried by the update check**, not by a retry of this run: a retry with a
   rebuilt list is a new run (`outputs/README.md` rule 1). Five of them are now recoverable thanks to the parser
   fix.
3. **1,138 of the 1,953 documents are presidential decrees and resolutions** — honours, appointments, ratifications
   — collected because the scope is `all`. The title rule's exclusions keep them out of the relevant scope, and the
   law table marks them `agency_or_other`. Dropping the category would halve the crawl; it is an open choice in
   `NOTES.md` 5.
