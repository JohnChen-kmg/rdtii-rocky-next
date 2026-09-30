# Extraction's response to collection's answers, 23 September 2026

Answering `rdtii-finale-1-scraping\notes\2026-09-23_answers-to-extraction.md`. Collection accepted
three of our requests, refused two on evidence, and found an error in ours. Taking the error first.

## The error was ours, and it is the kind that deletes the wrong thing

We claimed "not one of the 381 stored repealed documents is topic-relevant". For Lao PDR that is
false, and the check that produced it was invalid: it matched **English and Chinese keywords against
Lao-script titles**, so it could not have matched anything. A null result from a test that cannot
return a positive is not evidence.

Re-run on Lao terms, confirmed here: `la-la447-001` is **ກົດໝາຍວ່າດ້ວຍ ທຸລະກຳທາງເອເລັກໂຕຣນິກ, the Law
on Electronic Transactions** — the single most pillar-6-and-7 relevant title in the Lao corpus — and
it is in the repealed-with-file set, along with the Telecommunications Law, the Media Law and four
instruments on internet services and data centres. Collection's own title rule finds 56 of 291, 16
at core tier.

**Had R5 been applied as we wrote it, it would have deleted exactly those.**

## Our recommendations on the six decisions

### 1. R5 scope — split it. Malaysia yes, Lao PDR no

**Malaysia: drop the 87**, with collection's wrong-file carve-out, at the merge. Collection's
correction 2 is right and we had missed it: four of the five `other_act_text` files we asked to
preserve are themselves `repealed`, so a blanket rule would have destroyed the evidence the same
request wanted kept.

**Lao PDR: drop nothing, and the reason is not sentiment.** All 291 are already `linkage` or
`linkage, text needed`, so decision 20 already keeps them out of reading and mapping. They cost
extraction nothing: not OCR, not segmentation, not a record. Against that, 16 are core-tier relevant
and two have no in-force successor in the corpus. **The upside of deleting them is disk tidiness;
the downside is deleting the Electronic Transactions Law.** That is not a trade worth making.

### 2. R5 and R2 order — the collision disappears under recommendation 1

If Lao PDR drops nothing, no English edition is lost, and R2 recovers all 53 rather than 37. The
question collection raised — does a repealed law's English edition go with it — does not have to be
answered at all.

### 3. The `use` fix — yes, and it is the most important item in this exchange

`_mark_use` (`countries/my-malaysia/scraper/checker.py:169-178`) decides `use` from `document_kind`
alone and never reads `legal_status`, so **Malaysia's 90 repealed acts are marked `use: evidence`** —
the law table is actively instructing extraction to read repealed acts as evidence for indicators.

That is the live hazard. It is independent of whether a single file is dropped, it is a few lines,
and it should be done first. Extraction will also defend on its own side: a document whose
`legal_status` is `repealed` yields no provisions regardless of what `use` says.

### 4. R2, the language-aware `identity()` — yes

53 English editions, 1,513 native-text pages, 50 of them the only text-layer copy of a law whose Lao
original is a scan. They carry the official English titles the workbook needs and they are the only
published translation reference in the project.

### 5. R3's seven conditional requests to AGC — worth sending, developer's call

Collection has shown there is no English file to fetch: AGC uploaded the Malay reprint into the
English project folder under the same name. So this is confirmation, not recovery. Seven conditional
requests under a minute either confirm the defect — which is what makes the report to AGC concrete —
or find that a file has been replaced since 15 September. Only Act 680 is in scope for pillars 6 and 7.

### 6. R4's contract change — yes, and here is what extraction needs each field to hold

| Problem | Our recommendation |
| :---- | :---- |
| `retrieval_method` has no value for 985 hand-collected documents | Add **`hand_collected`**. Inventing a value that the schema rejects, or mislabelling a browser download as `requests`, are both worse than a contract bump |
| `source_url` is required, and 945 layer-1 documents have no per-document address | Use the **bulk-export page's URL** for all 945, and add **`source_url_scope`** with values `document` and `bulk_export`. A judge then sees exactly what the address refers to. Nulling a required field, or inventing a deep link into a database whose robots.txt forbids automated access, are both worse |
| `local_path` must point at stored bytes; 945 are inside ZIP archives | **Collection unpacks** into `raw/`, keeping the archives as the download record. Extraction should not teach its loader a new path grammar for one economy, and the contract does not describe addressing into archives |

That is a MINOR bump, the same shape as decision 2, and it should land before extraction writes the
China loader rather than after.

## What extraction changes on its own side, today

1. **`legal_status: repealed` yields no provisions**, whatever `use` says. Belt and braces for the
   `_mark_use` defect, and correct on its own terms.
2. **The exclusion rule in `ingest` matches on a flag prefix**, so `act_not_in_text` and
   `acts_not_in_text` are both caught — collection confirmed both spellings exist.
3. **Our disclosure sentence for Malaysia changes** to collection's sharper version: AGC publishes a
   status marker only for acts that are repealed, superseded or not yet in force; 1,285 rows carry no
   marker; and where the marker could be tested independently it had caught 75 of 76 repeals. The
   population where it bites is 783 `use: evidence` rows, not 1,285.
4. **Our R1 figure was wrong**: 1,285 of 1,441, not 1,135 of 1,291.
