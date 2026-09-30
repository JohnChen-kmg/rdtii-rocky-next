# Extraction decisions

Task-level choices and the reason for each. Newest at the bottom, so the file reads as a
history. Code changes are not logged here. They go in
`C:\Users\woshi\Desktop\rdtii-rocky-finale\docs\CHANGELOG_FINALE.md`.

Each entry carries the date the decision took effect. Entries D1 and D2 predate this file and
were recorded here on 2026-09-12 from the code and from
`rdtii-rocky-finale\stages\p2-extract\docs\KICKOFF_DECISIONS_2026-07-12.md`.

---

## 2026-07-12 D1. No quote, no record

**Decision:** A provision record is emitted only when the quoted snippet is a character-exact
substring of the frozen source text at the recorded offsets. `ground.verify()` re-checks
`source_text[start:end] == snippet` immediately before the record is built. A record that fails
is dropped and the drop is logged. It is never emitted with a warning.

**Why:** It makes hallucinated citations structurally impossible rather than merely unlikely.
The snippet bytes are copied from the frozen text by `ground.copy_grounded`, never taken from a
model. This is the whole of C2b, ten points, and the mapping stage re-verifies the same
assertion at its own ingest.

**The limit, and keep saying it:** Grounding guarantees consistency with the persisted source
text. It does not guarantee fidelity to the true printed statute. For a scanned document the
frozen text is OCR output, so a perfectly grounded snippet can still be a faithful quotation of
a misread page. That distinction is why the character error rate work exists and why it must be
stated in the submission rather than glossed.

**Consequence if reversed:** C2b collapses. Every citation in the tool becomes a claim rather
than a check, and the one thing a policy officer can verify unaided goes away with it.

---

## 2026-07-12 D2. The under-5% error rate claim is scoped in code

**Decision:** `cer.CerReport.meets_rubric()` returns true only when `doc_cer` is under 0.05 and
`cer_method` is `native_twin` or `gold_page`. An estimate can never satisfy the rubric bar. The
conservative corpus-wide value in `cer.ENGINE_FIXTURE_ESTIMATE_CER` exists so that
`ocr_quality_cer` is honestly non-null with its provenance disclosed, and it is deliberately
excluded from the rubric claim.

**Why:** The claim is only as good as the reference it was measured against. Putting the rule in
code rather than in a document means nobody can quietly make the claim on an estimate later,
including the author under deadline pressure. The secretariat verifies claims against the code,
so the code is the right place for the rule.

**Extension for the finale:** Any OCR engine swap must re-pass the same gold-page gate. A new
engine inherits no figure from Tesseract. This matters directly on 15 October, where an engine
swap is worth four marks and a judge may ask what the new engine's accuracy is.

**Consequence if reversed:** The tool would be able to quote an accuracy figure it never
measured. One question from a judge about which document that figure came from and the answer is
"an estimate", in front of the panel.

---

## 2026-09-12 D3. Language arrives from the crawler, it is never guessed here

**Decision:** The per-document language comes from a new manifest column written by the crawler
stage. Extraction reads it and maps it to a Tesseract pack. Extraction does not run language
detection of its own.

**Why:** The crawler already knows the portal, the economy and the seed configuration, which is
better evidence than a detector run over OCR output that may itself be garbage. Detecting the
language from text that was misread because the language was unknown is circular. A provenance
column should record a known fact, not an inference.

**Consequence if reversed:** Extraction would carry a detector whose failure mode is exactly the
case it is needed for, a scanned non-Latin page. The `language_of_source` column in the finale
workbook would then hold an inference presented as provenance, which is the kind of quiet
overclaim this build avoids everywhere else.

---

## 2026-09-12 D4. Re-vendor the Hand-off #1 schema in the same commit as the crawler bump

**Decision:** When the crawler changes `stages\p1-scrape\contracts\schemas\manifest.schema.json`,
the copy at `stages\p2-extract\00_contracts\schemas\manifest.schema.json` is updated in the same
commit. The same rule applies to the provision schema and the mapping stage's copy.

**Why:** Both vendored copies set `additionalProperties: false`. A new column added upstream
rejects every row downstream until the copy catches up. Verified 2026-09-12: the manifest schema
also pins `economy` to `SG`, `AU`, `MY` and `doc_id` to `^(sg|au|my)-...`, so the six-economy
change is a schema change before it is anything else.

**Consequence if reversed:** A split-commit workflow leaves the repository in a state where the
pipeline cannot run. On a public repo at a release tag that is a clean-machine deployment
failure. That is C4a, eight marks. The secretariat would find it rather than us.

---

## 2026-09-12 D5. Extraction does not translate. PROPOSED

**Decision:** Extraction stays wholly in the source language. The frozen source text, the
segmentation, the offsets and the verbatim snippet are all in the language of the original
document. The mapping stage reads the original. No translated text enters a provision record.

**Why:** The host's rule is that the verbatim snippet is the evidence. A translated snippet is
not a substring of the frozen source text, so admitting one would mean relaxing
`ground.verify()`, and D1 goes with it. A reviewer opening audit mode must see the words that
are actually in the statute, at the offsets recorded, or the audit trail is theatre.

**What this costs:** A judge who reads only English sees a Lao snippet and cannot assess it
unaided. That is a real C3a risk and it should be answered, not hidden.

**How to answer it without breaking D1:** Translation for the reader belongs in the interface or
in the mapping stage. It goes in a clearly separate, clearly labelled field beside the verbatim
snippet, never in place of it. The provision record keeps one quotation and it is the original.
Extraction builds none of this.

**Consequence if reversed:** Either C2b's verbatim guarantee weakens, or the record carries two
quotations and a reviewer has to work out which one is the evidence. Both are worse than an
untranslated snippet with a translation shown next to it.

---

## 2026-09-12 D6. One hand-keyed gold page per script, not per document. PROPOSED

**Decision:** The character error rate claim extends to a script only when a hand-keyed gold
page exists for that script. Documents in a script with no gold page carry an estimate,
disclosed as an estimate, exactly as the Round 1 corpus does today.

**Why:** Hand-keying is the expensive part and there is no way around it. Per script is the
smallest unit that carries real information, because the error modes are script level. Latin
errors come from margins and small caps. Thai and Lao errors come from stacked vowel and tone
marks. A second Malaysian gazette page would add almost nothing. A first Lao page changes what
can be claimed.

**The measurement caveat that goes with it:** `cer.py` normalises both sides with NFC plus
whitespace collapse before a character-level Levenshtein distance. Thai and Lao do not space
between words and use combining marks that count as separate characters, so a Lao percentage
and an English percentage are not directly comparable. Record the script in the report and say
so where the figure is quoted.

**Consequence if reversed:** Measuring per document is unaffordable at 2,673 documents and
measuring once for everything is dishonest. Reversing to "one figure for the corpus" is the
thing `meets_rubric` was written to prevent.

---

## 2026-09-12 D7. Language packs ship in the repo, not fetched at run time. PROPOSED

**Decision:** The Tesseract language data needed for the declared economies is committed under
`stages\p2-extract\fixtures\tessdata_local\`, alongside the Malay pack already there. The code
sets `TESSDATA_PREFIX`, not the reviewer. This is subject to the licence check in step 4 of
`PLAN.md` and to a size measurement.

**Why:** Thirty minutes on a clean machine, C4a, eight marks. A run-time download is a network
dependency inside the timed window and a failure mode on a locked-down machine. The precedent
already exists because `C:\Program Files\Tesseract-OCR\tessdata` was not writable, which is why
the Malay pack lives in the repo today. Asking the reviewer to set an environment variable by
hand, as the current stage README does, will not survive the test.

**Open and unresolved:** Total size. Five packs at `tessdata_best` size is plausibly around
60 MB, which is a real cost in a repo that must clone fast. Measure it, prefer `tessdata_fast`
if it passes the gold-page gate, and record the measurement in `evidence\`.

**Consequence if reversed:** A documented download step in the deployment guide is the fallback
and it is survivable. It moves risk from repo size to reviewer network, and it must then be
timed inside the thirty minutes rather than assumed.

---

## 2026-09-12 D8. Six economies and pillars 6 and 7 are required. Further is optional

**Decision:** Extraction must handle the three new economies chosen for the six, all non-English.
Language packs, gold pages and OCR timing are required for their scripts only. Other scripts are
optional.

**Why:** The developer's scope call. Six economies meets both host readings of C1a, and three new
non-English economies meets slide 7's non-English bar. Pillar scope does not change extraction,
because extraction works per document, not per indicator.

**Consequence if reversed:** Covering all nine live-test economies means up to nine packs, more gold
pages, and scripts nobody has measured. What is lost by not doing it: honest language claims in Word
Section 4 for the economies left out, and the live test if the sealed draw lands on one of them.

**Addendum, 2026-09-22. A record of fact, not a new decision.** The three new economies built by
the crawl task are Timor-Leste, Lao PDR and China (scraping `CONVENTIONS.md` section 6). No
`DECISIONS.md` in any workshop records that choice, which is question Q1 in `PLAN.md`. Timor-Leste is
not one of the nine live-test economies, so of the three only Lao PDR and China protect the live test.
The scripts this decision now covers are Lao, Portuguese and Chinese, not Lao and Thai.

---

## 2026-09-22 D9. The stage code is worked on here, as a working copy, and handed back

**Decision:** The developer's call, 2026-09-22. The Round 1 stage `stages\p2-extract` is copied into
`code\` at repo commit `92a5e9d`, with the same layout, so a hand-back is a straight copy.
`PROVENANCE.tsv` records each file's repo path, commit and sha256 at copy time. The drift check in
`README.md` runs before anything goes back. The copy leaves out the Round 1 build plan, `docs\`,
`sample_docs\` (the host's set is in the planning folder) and the Malay pack binary.

This replaces the README's former rule "No source code is copied here". `notes\` keeps its own rule
of no source code.

**Why:** The same model the crawl task adopted in its decision 8 and the instrument in its D9. Nearly
every file in the stage changes for the finale (`notes\2026-09-22_code_audit.md`), so the copy is the
whole stage rather than a few modules. Working here keeps the finale edits apart from the repo's
`finale` branch until they are tested together, and the hashes stop a hand-back overwriting a repo
change nobody saw.

**Consequence if reversed:** The work happens on a branch of the repo instead. That is workable, and
it is simpler for a stage whose every file changes. What is lost is the workshop layout the other
stages share, and the evidence and notes sitting beside the code they describe.

---

## 2026-09-23 D10. Two declared OCR engines, both local: Tesseract, and a vision model that must not read Lao

**Decision:** Engine A is Tesseract 5.4.0 with `tessdata_fast`, for every script. Engine B, the
declared second engine, is `qwen2.5vl:7b` through Ollama, for Latin scripts only. A cloud
document-AI service is documented as an optional third path and is not built.

**Why:** Measured on the same pages, `evidence\2026-09-23_ocr_engine_comparison.md`. The vision model
**transliterates Lao into Thai script**: 36% of returned letters in the expected script, char F1
0.076, 178% character error rate. It is not garbled output that a checker would catch, it is fluent
text in the wrong script, and under D1 it cannot produce a citable Lao provision at all. On Latin
scripts it is competitive and beats Tesseract on Portuguese raw CER, which is why it earns the second
slot rather than being discarded. `tessdata_fast` is the default because on real Lao scans it matches
`tessdata_best` to within half a point at half the time and half the repository size.

Both engines are local and open weights, so the pipeline runs end to end with no proprietary service,
which the host requires of OCR as well as of the language model.

**Consequence if reversed:** A cloud OCR as the only Lao path would put every document on someone
else's machine, cost money, and fail the no-proprietary rule. Declaring the vision model for Lao
would publish confident Thai-script text as Lao law.

---

## 2026-09-23 D11. Extraction does not translate, and where the publisher's English exists it is preferred to any model

**Decision:** D5 stands unchanged: the verbatim snippet is always the source language. No gloss field
ships this round. The comparison was run and handed to the developer as a recommendation.

**Why:** Measured against the Lao Official Gazette's own English translations,
`evidence\2026-09-23_translation_comparison.md`. Three local models were compared and the ceiling was
calibrated: re-wording the publisher's own English, with no Lao involved at all, scores chrF 0.807,
so that is what "correct but differently worded" looks like. **`gemma3:12b` reaches 0.658, 82% of
that ceiling; `qwen2.5:14b` 0.561, 70%; `llama3.1:8b` 0.338.** Gemma 3 lists Lao among its supported
languages and Qwen 2.5 does not, which is the likeliest explanation. **If a gloss is ever shown it is
gemma3, not qwen** — which matters to mapping, whose Engine B is `qwen2.5:14b`.

A second measurement weighs as much: glossing the same article from a clean text layer and from OCR
of the same page produces English outputs that agree only **0.559** with each other, so **OCR noise
contributes about as much as the choice of model**. They improve together.

Read rather than scored, even the better model is not safe as evidence. qwen turned "duty-free zones"
into "free zones" and hardened "promotes" into "shall promote"; gemma3 fixed both but renamed a cited
statute, rendering "the Law on Customs" as "the Tax Code". Pillars 6 and 7 turn on exactly these
distinctions: "must not transfer **unless**" is 6.4 where "must not transfer" is 6.1. A gloss that
moves a provision between indicators, fluently, is worse than no gloss.

**The better artefact already exists.** The gazette publishes its own English for 53 Lao laws, 1,513
pages, already retrieved. It is attributable to the publisher, costs nothing, and beats any model
output. It is currently dropped from the corpus by a known defect in `merge_corpus.identity()`, which
is question Q9.

**Consequence if reversed:** Building a gloss costs 6 to 8 hours plus machine time over every
provision, makes extraction own a job no stage has claimed, and puts a model's wording next to the
evidence in a submission marked on citation fidelity.

---

## 2026-09-23 D12. Flagged documents are carried and marked; 87 that are provably not the law are excluded with a reason

**Decision:** Of 2,116 flagged documents, 2,029 are extracted with their flags carried into every
record. 87 are excluded from provision extraction and instead get a `laws.jsonl` row with
`coverage_status: excluded` and the reason: 76 Malaysian repeal notices, 5 Malaysian wrong-act files,
4 Timorese wrong-act files, and 2 Ministry of Justice Tetum translations recorded as Portuguese.
Nothing is re-fetched: the portal serves the wrong file at the recorded address.

**Why:** A repeal notice holds no act text — median 313 characters, maximum 1,533 across all 76 — so
D1 blocks a record anyway, and excluding makes the zero explicit instead of an unexplained gap. The
wrong-act files are the real danger: `my-wpa2009-001` is filed as the Witness Protection Act 2009 and
contains 26,828 characters of the Judicial Appointments Commission Act 2009, with `legal_status`
`unknown` and `use` `evidence`, so no other filter catches it, and the genuine act is already in the
corpus under its own id. The two Tetum files would publish a translation as source text, breaching
D5 and D3 in one row.

**Consequence if reversed:** Carrying everything publishes provisions cited to the wrong instrument,
which is the citation-fidelity failure this stage exists to prevent. Excluding everything flagged
would discard 1,780 documents whose only fault is that the source publishes images.

---

## 2026-09-23 D13. One output format for all six economies, carrying how each document was obtained

**Decision:** The format is specified in `OUTPUT_FORMAT.md` and is the same for every economy. Every
provision carries `collection_channel`, `in_official_database`, `source_authority`,
`collection_note`, `content_flags` and `provenance_ref` alongside the evidence, plus
`language_of_source` with its display name, act identity for documents holding several acts, and
`citation_confidence` with the article number as OCR read it. `laws.jsonl` becomes one row per act
and gains `coverage_status` and `exclusion_reason`.

**Why:** The developer's requirement of 2026-09-23: a document that the economy's official law
database does not carry must say so, and a hand-collected document must carry the collector's own
note. China makes this unavoidable — its Legislation Law files departmental rules with the State
Council rather than the NPC, so the national database cannot hold its operative tier, and those rules
were collected by hand because the database forbids automated collection. That is a fact about
Chinese law, not a defect in the collection, and the submission is marked on the honesty of the
account. `citation_confidence` exists because one Lao article number in seven is misread by OCR and
is repaired from sequence position; an invisible repair is a wrong citation nobody can see.

**Consequence if reversed:** Per-economy shapes would grow branches in mapping and the dashboard, as
they did in Round 1, and the workbook could not tell a judge which evidence came from a national
database and which from a ministry page collected by hand.


**Addendum, 2026-09-23, revising the repealed half of this decision.** The developer asked why
repealed documents are kept at all. Measured: of 381 stored documents marked `repealed` across
Malaysia and Lao PDR, **none is topic-relevant to pillars 6 and 7**, and Singapore's crawler already
drops repealed acts entirely (collection decision 19), keeping only a `law_table.csv` row that
states the status. That is a better answer than storing them and excluding them here: the coverage
question is still answerable from the law tracker, and nothing dead is carried.

So the request to collection is R5 in `notes6-09-23_requests_to_collection.md`: apply
Singapore's rule to Lao PDR and Malaysia, including the 76 Malaysian repeal-notice files. Only the
90 Malaysian acts whose status is actually known can be dropped, because `legal_status` is
`unknown` on 1,285 of 1,441 rows.

**The wrong-file classes are not affected.** The 5 Malaysian `other_act_text` and 4 Timorese
`act(s)_not_in_text` documents hold a different act than the one they are filed under. They stay,
excluded from provisions with the observed act recorded, because they are evidence that the portal
serves the wrong document at a stable address.

**Second addendum, 2026-09-23, after collection answered.** The recommendation to drop repealed
documents is **split by economy**, and one of our own findings was withdrawn.

**Withdrawn:** the claim that no stored repealed document is topic-relevant. It was produced by
matching English and Chinese keywords against **Lao-script titles**, a test that could not return a
positive. Collection's own Lao title rule finds 56 of 291, 16 at core tier, including
`la-la447-001`, the **Law on Electronic Transactions** — the most pillar-relevant title in the Lao
corpus. Acting on our recommendation would have deleted it.

| Economy | Decision | Why |
| :---- | :---- | :---- |
| Malaysia | **Drop the 87** at the merge, with the wrong-file carve-out | None is topic-relevant, and their `use: evidence` marking makes them a live hazard |
| Lao PDR | **Drop nothing** | All 291 are already `linkage`, so they cost extraction nothing; 16 are core-tier relevant and 2 have no in-force successor held |

Collection also found that four of the five Malaysian `other_act_text` files we asked to **keep** are
themselves `repealed`, so a blanket drop would have destroyed the evidence that request existed to
preserve. The carve-out has to be applied inside the drop rule, not beside it.

**The hazard that mattered more than the deletion question:** `_mark_use` decides `use` from
`document_kind` alone and never reads `legal_status`, so Malaysia's 90 repealed acts are marked
`use: evidence` — the law table is instructing extraction to read repealed acts as evidence.
Extraction now defends on its own side too: **a document whose `legal_status` is `repealed` yields
no provisions, whatever `use` says.**
