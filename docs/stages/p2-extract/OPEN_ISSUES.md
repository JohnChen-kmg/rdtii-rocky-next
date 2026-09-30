# Open issues — FROZEN 2026-09-24

**Stage 2 is frozen.** 766,526 provisions across six economies, contract 0.3.0, handed off to
`Desktop/rdtii-finale-handoff2/` and handed back to the repository on branch
`p2-extract-contract-0.3.0`.

Nothing below blocks the submission. Each item is a known limitation that is recorded in the
output itself, so a reader meets it as a marked gap rather than as a wrong answer.

| Left open | Where it is visible | Why it was left |
| :---- | :---- | :---- |
| Timor-Leste `act_index` null on ~36% of provisions | the field itself; `act_count` stays authoritative | the completeness and straddle gates withhold rather than guess; a partial split folds one act's articles into another |
| Citation contradicts its own text: TL 2.5%, LA 3.6% | `citation_confidence`, `article_number_as_read` | OCR and gazette structure; every repair is recorded, never silent |
| No provision tagged | `tags_source: not_tagged`, `extraction_model: null` | `OUTPUT_FORMAT.md` §7: these fields have no consumer in mapping and are "not to be improved" |
| 5 legacy OLE2 `.doc` unread | `doc_status` `parse_failed` with the reason | needs a new dependency a week before freeze |
| China: 24 documents with no numbering | `zero_provisions` | they genuinely carry no articles |
| Round 1 English regression never run | — | see below |

**The one worth knowing about.** Every check run on this stage is internal: self-consistency
across economies, determinism per lane, grounding against our own frozen text, conformance to
our own schemas. All of it says the output agrees with itself. Nothing compared it to an
independent baseline. The Round 1 regression — 1,117 byte-identical documents — is the only
check that could surface a systematic error that every internal check would reproduce
faithfully. That is not hypothetical: the double-count bug fixed on 2026-09-23 survived Round 1
and three of my own audits for exactly that reason. It was judged not worth the remaining time
against the 30 September freeze. Recorded here so the decision is visible rather than implicit.

---

## A. Closed since this list was written

| Was | Outcome |
| :---- | :---- |
| **A1** China had no reader for any of its 1,090 documents | **Done.** Lane D (OOXML, stdlib zipfile + lxml) and three portal parsers. 1,058 documents extract, 49,977 provisions |
| **B1 (the part that mattered)** Timor-Leste citations | **Done.** `_repair_sequence` renumbered every act after the first in a multi-act issue: 120,968 of 189,355 provisions (63.9%) cited a number their own text contradicts. Now 2.5%. Lao improved from 11.6% to 3.8% |
| **Double-counted provisions** (not previously known) | **Done.** `candidate_spans` keyed "has subsections" on the article's citation string, so the same text was emitted twice wherever a citation repeated: 6,321 records in Malaysia, 298 in Australia, 69 in Singapore. Now keyed on character range; measured 0 overlaps |
| **Chinese law titles** | **Done.** 1,064 rendered, labelled `rendered`. SG/AU/MY carry the original English as `source_is_english` |
| **Chinese ordinal numbering** | **Done.** 决定 / 通知 / 规定 number `一、二、三`, not `第X条`. 64 documents recovered |
| **`--fresh` destroyed the OCR cache** | **Done.** Keeps the cache, clears the outputs |
| **"superseded by" was case-sensitive** | **Done.** Now case-insensitive and centralised |

---

## B. What is actually left

### B1. ~~Timor-Leste multi-act splitting~~ — DONE 2026-09-23

`act_index` on 120,690 provisions (63.7%), 552 documents, 850 distinct law numbers; 97.5% of act
slices begin at Artigo 1-3. Acts located from `law_table.csv`, never detected. Two gates keep it
honest: a **completeness gate** (no act_index unless every act the sidecar names was found at a
distinct offset) and a **straddle gate** (no act_index for a provision whose article heading is in
a different act than its text). 7,454 provisions withheld by the second, which cut wrong seams
from 9.2% to 1.1%.

**Left over:** one `laws.jsonl` row per act is still not emitted (+3-4 h), and `cmd_validate`
must be fixed first - it collapses `laws.jsonl` into a doc_id-keyed dict and will fail on every
multi-act document the moment per-act rows exist.

### B1-old (kept for the record)

The citation damage is fixed; the attribution gap is not. 911 of 1,921 documents hold more than
one act and 141,770 provisions sit in them, all attributed to a single law name.

**Scoped, not guessed:** `corpus/TL/law_table.csv` already carries one row per act (4,788 rows
over 1,921 documents), already parsed into `sidecars.DocFacts.acts` and already passed to
`build_record`, so `act_count` is free and authoritative. Acts are **located**, not detected:
84.1% of acts and 80.5% of multi-act documents locate cleanly. A **completeness gate** — emit
`act_index` only when the located count equals the sidecar's — turns the 16% miss into withheld
output rather than wrong output, because a partial split silently folds act 3 into act 2.

| Option | Cost |
| :---- | :---- |
| **Reduced: act_index/act_count, gated** (recommended) | **6–8 h** |
| Full: plus one `laws.jsonl` row per act | 10–12 h |
| Flag only: set `act_count` from the sidecar, leave `act_index` null | ~1 h |

**Trap:** `cmd_validate` collapses `laws.jsonl` into a doc_id-keyed dict and will fail on every
multi-act document the moment per-act rows are emitted.

### B2. The contract bump — required, or Hand-off #2 is rejected

0.2.0 → 0.3.0, MINOR: all additive or loosening, no removals, nothing newly required. The two
stages' vendored copies differ only by formatting today, so syncing is mechanical. **~20 min.**

### B3. The English regression against Round 1 has never been run

1,117 byte-identical documents, 143,835 provisions. Today's counts moved for good reasons on
every economy, which is exactly why a byte-level baseline is worth having. **~2 h.**

### B4. Tagging — 766,477 provisions carry `tags_source: not_tagged`

Honest and correct as it stands. The per-language tagger map exists and both models are pulled.
Recommended: tag the shortlist only, 2–4 h. `cmd_tag_corpus` needs an Anthropic key, which sits
badly with "no proprietary service on the path" — the local Ollama lane avoids that.

### B5. Smaller items

- 5 legacy OLE2 `.doc` — a reader, or a recorded exclusion (1 h, or free)
- 3 China documents still yielding nothing, 24 with no numbering at all
- 53 Lao laws have publisher English on their PDF cover pages — reading those would upgrade
  them from `rendered` to `publisher_translation` (~1 h)
- ~25 China detail URLs by hand, for the instruments most likely to be cited (~1 h)

---

## C. Superseded detail (kept for the record)

### A1. China — 1,090 documents produce nothing today

### A1. No reader for 943 `.docx`, 2 `.doc`, 140 HTML, 4 PDF

The manifest passes the ingest gate and every `local_path` resolves, but there is no `docx`
lane, no OLE2 reader, and no parser registered for `cac.gov.cn`, `miit.gov.cn` or `www.gov.cn`.
Lane A raises `NotImplementedError` for an unregistered host; the docx rows have no lane at all.

| Option | Cost | Gets |
| :---- | :---- | :---- |
| **A1a. docx lane + three HTML parsers** (recommended) | ~1 day | all 1,086 |
| A1b. docx lane only | ~3 hours | 943 (86%) — the national database, which is the core |
| A1c. HTML parsers only | ~4 hours | 140 — the ministry rules, which are where the digital-trade specifics live |
| A1d. Drop China | free | nothing; one of six economies missing from the submission |

**Note:** `python-docx` is **not installed** and is not in `pyproject.toml`. Use stdlib
`zipfile` + `lxml` — verified today to open all 943 OOXML packages with zero failures. Do not
add the dependency a week before freeze without re-running the clean-machine test.

**The 2 legacy `.doc` are OLE2 binary.** Nothing in the venv reads them. Options: exclude with a
recorded reason (2 documents, cheap, honest), or add `olefile`/`antiword` (new dependency).

---

## B. Produces wrong or misleading output right now

### B1. Timor-Leste multi-act: `act_index` is null on all 189,355 provisions

Measured today: `act_index: None` and `act_count: 1` on **every** Timorese record. Collection
measured that **911 of 1,921 Timorese documents hold more than one act** — one gazette issue
holds up to 39. `tl-ldcn-001` holds both Lei 1/2026 and Decreto-Lei 13/2026, *both with an
Article 6*.

**What this does to the output:** every act in a multi-act issue is attributed to one law name,
so stage 3 groups them as a single law and the wrong `law_name_en` is matched against the host
baseline. Provision ids do not collide — the code appends a `~n` disambiguator — so this is
silent. This is the largest correctness defect in the stage.

| Option | Cost | Trade-off |
| :---- | :---- | :---- |
| **B1a. Implement splitting for TL** (recommended) | ~half a day | fixes 911 documents; the plan already nominated this as the first cut if the week ran short, and the week did not run short |
| B1b. Flag only — set `act_count` from the sidecar, leave `act_index` null | ~1 hour | mapping can at least *see* which laws are unreliable and discount them |
| B1c. Leave it | free | 47% of the Timorese corpus mis-attributed, invisibly |

### B2. Nothing has been tagged — 722,986 provisions have no `scope`/`data_type`/`obligation_type`

All records are honestly `tags_source: not_tagged` with `extraction_model: null` (fixed today).
But the fields are empty, and the per-language tagger map is built and unused. Both models are
pulled and present locally (`gemma3:12b`, `qwen2.5:14b`).

| Option | Cost | Trade-off |
| :---- | :---- | :---- |
| **B2a. Tag the shortlist only** (recommended) | ~2–4 h | tags exist where they are read; `OUTPUT_FORMAT.md` records these as soft hints mapping mostly ignores |
| B2b. Tag everything locally | measured ~5.7 h for Lao alone; days across 722,986 | complete, probably not worth it for a demoted field |
| B2c. Ship untagged | free | honest and already true; the field is a documented gap |

### B3. The Batches tagging lane calls a proprietary API

`cmd_tag_corpus` requires `ANTHROPIC_API_KEY`. The submission's stated position is that both
declared engines are local and open with no proprietary service on the path.

| Option | Trade-off |
| :---- | :---- |
| **B3a. Use the local Ollama lane** (recommended) | keeps the claim true; slower |
| B3b. Keep Batches and disclose it | faster; the "no proprietary service" claim needs rewording |
| B3c. Delete the Batches lane | removes the contradiction and the option |

---

## C. Integrity and hand-off

### C1. Schema changes must reach `stages/p3-map` in the same commit

Today's contract changes are all additive, but **mapping vendors its own copies** (D4). If they
do not land together, Hand-off #2 is rejected downstream.

Added: `tags_source`, `source_url_basis`, `access_date_basis`, `access_date_observed`.
Made nullable: `scope`, `data_type`, `obligation_type`, `extraction_model`, `source_url`,
`access_date`, `law_name_guess`, `http_status`, `http_headers_path`.

Additive + optional = **MINOR bump, 0.2.0 → 0.3.0**. Not yet done.

### C2. The English regression against Round 1 has never been run

1,117 documents are byte-identical between rounds — same input bytes, so the new code should
reproduce Round 1's records apart from the added fields, across 143,835 provisions. **This is
the only check that would catch a silent segmentation change**, and today's count-stability
(SG, AU, MY identical) is only against my own earlier runs.

Recommended: run it before freeze. Roughly 2 hours including triage.

### C3. Timor-Leste's count moved by 105 and the cause is inferred, not proven

189,460 → 189,355. The first run was not `--fresh` and inherited 888 stale `by_law` files from
pilots; the re-run was. The old file is overwritten so this cannot be demonstrated. What can be
said firmly: none of the three code changes between the runs can alter a provision count for a
pure-PDF corpus with complete sidecar facts. Option: re-run TL twice from clean and confirm the
number is stable at 189,355 (~30 min, cheap certainty).

---

## D. Robustness — will not bite today, could bite on 15 October

### D1. `cmd_run` writes `provisions.jsonl` once, after the whole corpus

A killed run loses everything. Survivable at 30 minutes a corpus; it is the same shape of bug
as the OCR pre-pass one fixed today. Option: checkpoint every N documents (~1 hour).

### D2. Two provenance rows can name the same file

Now recorded in `crawl_notes` rather than silently resolved, but the ambiguity itself is
unresolved. Affects 1 China file. Option: ask collection which row governs.

### D3. `ocr/<doc_id>/` holds both the page cache and `cer_report.json`

Mixing a cache with a run artefact in one directory is what made `--fresh` destructive. Fixed
defensively; separating them would be cleaner.

---

## E. Accepted gaps — documented, no action proposed

| Gap | Recorded in |
| :---- | :---- |
| China `access_date`: a UTC instant for 6 of 1,090 | `corpus/CN/PROVENANCE_GAPS.md` §1 |
| China `source_url`: 945 carry the database root, 5 are null | §2 |
| China `http_status`/`http_headers_path`: null on all | §3 |
| **Customs: nothing collected**, 1 indicator unserved, its README routes to a folder not imported | §6 |
| Lao: no rubric-legal CER; every reference is a twin or proxy | `evidence/2026-09-23_ocr_engine_comparison.md` |
| Lao: 4,419 of 41,534 citations repaired from sequence | each record carries `article_number_as_read` |

**One worth a decision:** §2 notes that hand-looking-up real detail URLs for the ~25 database
instruments actually cited would buy precision exactly where a judge traces a citation. Perhaps
an hour of manual work. Everything else in E is genuinely accepted.

---

## Suggested order for the seven days

1. **B1** Timor-Leste multi-act splitting — the largest silent correctness defect
2. **A1a** China readers — the only thing standing between a manifest and a sixth economy
3. **C2** English regression against Round 1 — the only check that catches a silent break
4. **C1** contract bump and the mapping hand-off — cheap, and blocks Hand-off #2 if forgotten
5. **B2a** tag the shortlist
6. **E** the ~25 China URL lookups, if time allows
