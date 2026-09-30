# Requests to the collection stage, 2026-09-23

Written by extraction. The collection workshop is read-only to us, so these are requests for the
developer to take across, per the project convention. Each says what, why, and which code reads it.

**R5 asks for files to be dropped from two corpora.** It revises an earlier position of ours;
the measurement that changed it is in that section.

---

## R1. Malaysia's `legal_status` is `unknown` on 1,135 of 1,291 laws

**What:** can the portal supply in-force status for Malaysian acts, even partially?

**Why:** extraction must not publish provisions from a repealed act — the instrument scores a
repealed provision zero, and the host's own rule is explicit about it. Today we can only identify
133 Malaysian acts as `repealed`; for 1,135 the status is honestly unknown, so we cannot separate
"in force" from "repealed" for most of the corpus. Singapore's crawler already drops repealed acts
at the crawl (collection decision 19); Malaysia has no equivalent because the status is not known.

**What reads it:** `law_table.csv` `legal_status`, joined on `doc_id`; extraction carries it onto
every provision and `laws.jsonl` row so mapping can filter.

**If the answer is no**, that is fine and we will say so: those rows ship with
`legal_status: unknown`, and the submission states that Malaysian in-force status could not be
established for most acts.

---

## R2. Re-merge the Lao corpus with a language-aware `identity()`

**What:** `tools/merge_corpus.py:97-101` builds a document's identity from `portal_id` and
`document_kind` and **ignores language**, so each Lao law's English edition collided with its Lao
original and was superseded. All 53 are on disk in `LA_ws_2026-09-21` and none is in the corpus.
Collection has already logged this as one of two shared-code defects awaiting a decision.

**Why it matters more than it looks:**

1. **They are the only published English of any law in this project.** 1,513 native-text pages.
2. **50 of the 53 are the only text-layer copy** of a law whose Lao original is a scan.
3. They are the reference the translation comparison was measured against.
4. **They carry the official English titles**, which the workbook's Law Name column needs for Lao —
   without them every Lao title is machine-rendered.

**What reads it:** extraction reads the corpus, never a run folder, so today these files are
unreachable by the contract. Either the corpus is re-merged, or we record an explicit exception.

**One caution:** the English edition is a translation, so it must never become the
`verbatim_snippet`. It is the source of `law_name_en` and a reference, not evidence.

---

## R3. The seven Malaysian acts held only in Malay

**What:** can AGC's English text be re-fetched for the seven documents flagged `language_mismatch`?
They include **Act 680, the Electronic Government Activities Act 2007**, which is in scope.

**Why:** the English link served the Malay file, and no act in the corpus has a second copy in the
other language. Extraction will otherwise mark them `language_of_source: msa` from the flag, which
is honest but loses the English text AGC does publish.

**What reads it:** `contract_meta.language` and the `language_mismatch` flag.

---

## R4. China's manifest — who builds it

**What:** China has no manifest in the contract's shape. Extraction needs one before it can read
China like the others.

**Why:** it is the first China task either way, and the provenance sheets are collection's. Our
recommendation, if it falls to extraction, is that we build it and collection reviews it, because
the sheets carry the facts and we carry the schema.

**What reads it:** `ingest.load_manifest`. Details of every required column and its source are in
this workshop's plan, W8.

---

## R5. Drop the repealed documents from the Lao and Malaysian corpora, as Singapore already does

**What:** apply Singapore's rule to Lao PDR and Malaysia — a repealed act is listed in
`law_table.csv` with its status and **no file is stored**.

**Why, measured 2026-09-23 on the corpora:**

| | Rows marked `repealed` | With a stored file | Topic-relevant to pillars 6 and 7 |
| :---- | ----: | ----: | ----: |
| Malaysia | 133 | **90** | **0** |
| Lao PDR | 293 | **291** | **0** |
| Singapore | 297 | **0** | — |
| Timor-Leste | `unknown` on all 4,788 | 0 | — |

**Not one of the 381 stored repealed documents is topic-relevant by title.** They are dead weight:
they are excluded before OCR and before extraction, so they cost no processing, but they sit in the
corpus and in every count of it.

**Singapore already solves this, and it is collection's own decision 19** — "Singapore's repealed
acts are dropped from the crawl". Its 297 repealed acts keep a `law_table.csv` row stating the
status, with no `doc_id` and no file. That keeps the coverage answer — "the portal lists this act,
it is repealed, we did not store it" — while storing nothing. It is a better answer than the one
extraction proposed on 2026-09-22, which was to store them and exclude them downstream.

**The limit:** Malaysia's `legal_status` is `unknown` on 1,285 of 1,441 rows, so only the 90 known
repealed acts can be dropped. The rest cannot, because nobody knows their status — which is R1.

**What reads it:** nothing in extraction needs these documents. The `law_table.csv` row is what
extraction reads to report coverage.

**Also in this class, for the same treatment:** the **76 Malaysian `repeal_notice` files**, where
the stored file is a repeal cover sheet rather than the act. Verified: median 313 characters,
maximum 1,533, none over 3,000. There is nothing in them to quote, and 75 of the 76 already carry
`legal_status: repealed`.

**Not in this class, and they should stay:** the 5 Malaysian and 4 Timorese files that hold **a
different act than the one they are filed under**. Those are wrong files, not repealed ones, and
the acts they actually contain are real. Extraction excludes them from provisions and records which
act the file really holds; deleting them would lose the evidence that the portal serves the wrong
document at a stable address, which is the thing worth reporting to AGC.

---

## On reproducibility, since this reverses our earlier position

Dropping files at the crawl is not hand-editing a generated corpus, which rule 7 forbids. It is a
crawl rule, applied by the code, the way Singapore's already is — so the corpus stays reproducible
from the portal plus the settings. That distinction is what makes R5 safe and what made the
"delete them afterwards" idea unsafe.
