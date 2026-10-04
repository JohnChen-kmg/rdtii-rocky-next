# Notice from the instrument workstream: contract and workflow changes (13 September 2026, updated 4 October 2026)

You are working on one stage of the RDTII finale tool. The instrument is the codebook every stage keys
on. It changed on 13 September 2026 and was handed off to the repo on 29 September. **It changed again
on 4 October; that change is described first, below, and is not in the repo yet.**

Read this, check your stage against it, and record the impact in your own workshop. Do not edit
instrument files or their copies in the repo. If you need an instrument change, send a request
instead (section 6).

| | Path |
| :---- | :---- |
| Instrument workspace, the source of truth | `C:\Users\woshi\Desktop\rdtii-finale-0-instrument`. The instrument's files are in `instrument\` and its code in `code\scripts\`; together they mirror the repo's `stages\p0-instrument`. `code\README.md` explains the code workflow |
| Repo, working copy | `C:\Users\woshi\Desktop\rdtii_rocky_next`. The instrument is handed off here |
| Repo, submission | `C:\Users\woshi\Desktop\rdtii_rocky_finale_9.30`, public; its release tag is what runs on 15 October. The instrument is not copied here unless the developer decides the submission changes |
| Repo, development history | `C:\Users\woshi\Desktop\rdtii-rocky-finale`, at the 30 September tag. Section 1 onward was written when this was the only repo |
| Retired, do not use | `C:\Users\woshi\Desktop\rdtii-rocky-finale-w3` (worktree, branch `w3-instrument-61`) |

## Update of 4 October 2026: every indicator at pillar 6–7 depth

### Status

- **In the instrument workspace only.** All three repos hold the instrument as handed off on
  29 September (commit `bf2bb3e`). The developer decides when the 4 October round is handed off.
- **It drops in cleanly.** Rehearsed on 4 October in an exported copy of `rdtii_rocky_next` at commit
  `2edcf44`: mapping tests 450 passed and interface tests 216 passed, the same before and after the
  copy. The mapping stage's own code builds its prompt for each of the 61 indicators alone and for all
  61 together. `HANDOFF.md` has the table, and the four things the repo's owner does with the copy.
- **Pillars 6 and 7 are not affected.** The prefix `build_system_prefix()` builds for the default
  automated set is byte-identical before and after (31,929 characters, same SHA-256), and the nine
  pillar 6–7 signature files are unchanged.
- **The new content is a draft.** It was written by drafting agents from the host documents and
  machine-checked (cited pages and host rows exist, score sets match). No person has reviewed it.
- **Which indicators are automated has not changed.** Decisions D13 and D14 stand: pillars 6 and 7 are
  automated, and the other 52 are "manual" but can be run on request, as they were for Timor-Leste.
- **The `coverage` marks are now in `indicator_order.yaml`** (mapping request R1, instrument D16). They
  give the same nine automated indicators as before.

### What changes in the contract

| File | What changed |
| :---- | :---- |
| `indicators.yaml` | **All 52 blocks outside pillars 6 and 7 are full depth (Tier B). There is no Tier C block.** Every block carries the same keys: the ones listed in section 2 plus `weight`, `scoring_features`, `guide_examples`, `null_statement` and `sources` (`guide_heading`, `guide_pages`, `faq_pages`, `methodology_row`, `template_row`). Optional keys: `polarity`, `level`, `framework_name`, `review_notes`. New top-level key `block_fields` says which keys the prompt renders. The nine pillar 6–7 blocks gained only non-rendered keys |
| `indicators.yaml`, `level` | **`level: economy` is now on 13 blocks:** 4.2, 4.5, 4.6, 4.1, 5.1, 5.4, 5.7, 7.1, 7.2, 8.1, 8.2, 11.1, 12.9. Each also carries `framework_name`, the phrase that completes "does the economy lack a ___?" |
| `indicators.yaml`, `polarity` | **`polarity: inverted` is now on 14 blocks:** the 13 above plus 12.5. These are the same 14 IDs that `scoring_policy.polarity` names in prose, so nothing changes for a reader of that sentence. 12.5 is inverted but not economy-level and not binary: a threshold found scores 0.5 or 0 by its USD value |
| `indicators.yaml`, `null_statement` | On every block: what an absence row says. The nine pillar 6–7 values are copied from `submission.py` `_NP_REASON` |
| `indicators.yaml`, `review_notes` | Now on 39 blocks. Never render it into a prompt and never show it as host text |
| `indicator_order.yaml` | Three new fields on every entry: `coverage` (`automated`, `manual` or `excluded`), `coverage_reason` (`scope` or `practice` on a manual entry, the keys of mapping's reason categories) and `answer_nature` (the coverage register's codes L, Dg, Dr, T, F, W, operative code first). New top-level `coverage_marks`: the classes, reasons and nature codes, the counts, and `economy_overrides` (China's pillar 6, reason `portal_tier`). 9 automated, 52 manual, 6.5 excluded. Reason `practice` on six: 1.4, 3.4, 5.3, 9.1, 11.4, 12.6. Every earlier field is unchanged |
| `policies.yaml` | New last section `indicator_sets`: lists `inverted`, `economy_level`, `practice_based` and `non_regulatory`. Every earlier key is unchanged, so the sections the prompt renders are byte-identical |
| `signatures\<ID>.yaml` | `tier: B` on the 38 files that said C. 3.1 has one more exemplar, appended last. The nine pillar 6–7 files are unchanged |
| `gold\gold_set.jsonl` | `label_flag` on a suspect or advisory row now has `basis` (`round1_review` or `drafting_review_2026-10-04`). 208 more rows are flagged: suspect 53 and advisory 162 in total. Row count and every other field unchanged |
| `INSTRUMENT_NOTES.md` | Covers every indicator: one line each, and where each pillar's evidence lives |

Each trap is now written on both blocks it concerns, because a run may load one indicator without the
other.

### What it means for your stage

**Mapping (`stages\p3-map`).**
- **Economy-level scoring.** `rollup.py` takes the framework's name from a two-entry table (7.1, 7.2).
  For the other eleven economy-level indicators the call ends "pending" (a caught `KeyError`). Read
  `framework_name` from the block instead. The prompt's scale, "1 = no framework; 0.5 = sectoral or
  partial only; 0 = comprehensive framework", and its answer set 1 / 0.5 / 0 do not fit 5.4
  (1 / 0.5 / 0.25 / 0) or the binary 5.7, 11.1 and 12.9: each block's `scoring_tree` has the right
  branches.
- **Inverted list.** `indicator_sets.inverted` is the machine-readable list you asked for. It holds the
  same 14 IDs your loader lifts from the polarity sentence.
- **Absence statements.** `null_statement` is on every block, so the `_NP_REASON` table and its "no
  qualifying measure found" fallback can read from the instrument.
- **Counting measures.** These blocks score by how many measures an economy has: 1.4, 2.1, 2.3, 3.1,
  4.3, 4.9, 5.2, 5.3, 9.4, 10.1, 10.2, 10.3. The roll-up escalates only 6.1 and 6.2. Each block states
  the rule in its `scoring_tree` and `coding_rules`.
- **11.2.** A score of 0 needs positive evidence that self-declaration is allowed; an absence should
  not default to 0.
- **Prompt size.** One prefix for all 52 other indicators is now 298,967 characters (99,567 before). A
  two-indicator scope is about 20,000. Figures: `evidence\prefix_sizes_2026-10-04.md`.
- **Prompt header.** It says "Pillars 6-7" whatever `INDICATORS_SCOPE` holds.
- **Label flags.** 53 suspect rows should not count as gold in an evaluation; nothing reads
  `label_flag` today.
- **R1 is delivered.** `_automated_ids()` already reads `coverage: automated`; with the new file it
  returns the same nine. `config\coverage.py` can now read `coverage_reason` and
  `coverage_marks.economy_overrides` in place of its own derivation and its `PORTAL_TIER_GAPS` table.
  One difference to expect: the instrument gives 1.4, 11.4 and 12.6 the reason `practice`, where
  `coverage.py` gives them `scope` today.
- **Promoting an indicator to automated** is a line in the instrument's `coverage.yaml`. Your default
  run maps the automated set, so its prompt and cost grow with each indicator added.
- **Still open from your requests:** R2 (may S7 read the gold set as the NEW/KNOWN baseline) and R3
  (source-language keywords) are not answered yet.

**Dashboard (`interface\`).**
- The Guide page reads `indicators.yaml`. After hand-off the 52 other blocks are several times longer,
  every block has `weight`, `null_statement` and `sources`, and 39 have `review_notes`, which must not
  be shown as host text.
- **The indicator picker's tags change.** Your readers parse the new files without change. The tier
  counts go from A 9, B 14, C 38 to A 9, B 52, C 0: 52 indicators carry "not reviewed" and none carries
  "host criteria only". The automated nine and the practice-based three (3.4, 5.3, 9.1) are the same.
- **One pinned test.** `interface\tests\test_map_start.py` line 29 expects
  `{"A": 9, "B": 14, "C": 38}`; after hand-off it is `{"A": 9, "B": 52, "C": 0}`.
- **One stale sentence.** The repo `README.md`, under Known Limitations, calls the blocks outside
  pillars 6 and 7 "host-criteria-only". They are full depth and not yet reviewed.
- **Manual-check reasons.** `indicator_order.yaml` now says which six indicators need practice or
  external evidence (1.4, 3.4, 5.3, 9.1, 11.4, 12.6), in `coverage_reason`. The picker flags three of
  them today from `practice_based`.

**Scraping (`stages\p1-scrape`).**
- `INSTRUMENT_NOTES.md` section 9 and the banner above each pillar in `indicators.yaml` say what kinds
  of law each pillar's measures are found in. Use them when building source registries.
- Block 1.4 says its primary sources are WTO trade-remedy notifications and official gazettes. Your
  request R4 (a source class for WTO documents) is still open.
- Block 5.3 says the answer comes from ownership facts, not legislation.

**Extraction (`stages\p2-extract`).** Nothing new.

The tier list in section 2 below is superseded: tiers are now A 9, B 52, C 0.

## 1. Status as of 13 September (superseded by the update above)

- **The new instrument is a draft.** Its validator passes, but it has not been handed off.
- **The repo still holds the Round 1 instrument:** nine indicators with `P6-I1`-style IDs, in
  `stages\p0-instrument\output\` and `stages\p3-map\contracts\instrument\`. Anything you run today
  still sees Round 1.
- **The hand-off waits for two things:** the mapping-stage changes in section 4, and the developer's
  open decisions (reviewing 14 drafted indicators, and the host's stricter trap wording). The steps are
  in `HANDOFF.md` in the instrument workspace.
- **The instrument works differently from the other stages.** By the developer's decision (D9), it
  is built and edited in its workshop and copied into the repo at hand-off. The other workshops keep
  their "no code here" rule unless the developer says otherwise.

## 2. What changes in the contract

### IDs and scope

- **IDs are decimal text:** `"6.1"`, `"4.01"`, `"12.4.1"`.
  - Never parse them as numbers. `4.01` and `4.1` are different indicators.
  - Never write `P6-I1`. Read Round 1 artefacts through `indicator_ids.normalize()` and
    `legacy_of()`.
  - Order comes from `indicator_order.yaml`, never from sorting.
- **The host renumbered three of the Guide's IDs:** Guide 4.1 is host `4.01`, Guide 4.10 is host
  `4.1`, and Guide 12.1 is host `12.01`. Always use host IDs.
- **61 indicators are scoreable,** of the 62 the host lists. 6.5 is out of scope.
- **14 non-regulatory indicators never get rows:** 1.1, 1.2, 1.3, 2.4, 4.4, 4.7, 4.8, 5.6, 6.5, 9.2
  and 12.10–12.13. The host fills them from WITS, V-Dem and treaty status lists, and says no
  extraction tool is needed.
- **3.4, 5.3 and 9.1 are practice-based.** They are in scope, and their evidence may come from
  official announcements, reports and ownership records, not only from legal text.

### Files

These live in `instrument\output\` now, and in `stages\p3-map\contracts\instrument\` after hand-off.

| File | What changed |
| :---- | :---- |
| `indicator_order.yaml` | **New.** The 62 IDs in host order. Each entry has `id`, `pillar`, `pillar_label`, `name`, `weight_in_pillar`, `host_note`, `template_row`, `methodology_row`, `status` (in_scope or out_of_scope) and `evidence` (legal or practice). Top-level keys: `out_of_scope`, `non_regulatory_indicators`, `practice_based`, and `host_mapping_traps` (template rows 79–85). Read the indicator list from here |
| `indicators.yaml` | **One file holding all 61 blocks,** in host order and grouped by pillar. There is no `indicators_generated.yaml`. A new top-level key, `tiers`, describes the tiers. Every block has `id`, `pillar`, `tier` (A, B or C), `review_status`, `name`, `category_official`, `question`, `definition`, `scoring`, `scoring_tree`, `coding_rules`, `exceptions` and `disambiguation`. Some blocks also have `sources`, `scoring_features`, `guide_examples`, `weight`, `level` (`economy` on 7.1 and 7.2), `polarity` and `review_notes`. `polarity: inverted` is set on 7.1, 7.2, 8.1, 8.2 and 12.9 only. Never render `review_notes` into a prompt |
| `policies.yaml` | Decimal IDs throughout. New keys: `measure_inclusion.practice_based` and `non_regulatory`, `id_policy`, and `scoring_policy.economy_level_indicators`. New edge cases: `amending_act_cited_instead_of_principal`, `datacentre_rules_without_mandate` and `government_data_measure`. `citation_contract.section_rule` adds "a real act cited to the wrong section scores zero". **`scoring_policy.polarity` holds the full list of inverted indicators** (4.5, 4.1, 5.1, 5.4, 5.7, 7.1, 7.2, 8.1, 8.2, 11.1, 12.9) and of absence-based ones (4.2, 4.6, 12.5). Use this list, not the block field |
| `signatures\<ID>.yaml` | 61 files named by decimal ID (`6.1.yaml`, `12.4.1.yaml`). The `P6-I1.yaml`-style files are gone. Keys: `indicator`, `name`, `tier`, `instrument_version`, `keywords` (English only), `definition_text`, `exemplar_law_types`, `scope_patterns`, `negative_signals` and `exemplars`. Each exemplar has `economy`, `law`, `coverage`, `score`, `impact`, `url`, `teaching_note`, `gold_id` and `provenance`. There are 400 exemplars, drawn from Round 1 and Round 2 economies |
| `gold\gold_set.jsonl` | **1,054 rows, up from 51,** covering all pillars. Economies: AU, MY, SG (Round 1) and CN, IN, ID, LA, MN, RU, TH (Round 2). Row keys: `gold_id` (like `r1-my-053`), `baseline_round`, `economy`, `pillar`, `indicator`, `raw_score`, `law`, `coverage`, `impact`, `timeframe`, `urls`, `note`, `update_type`, `host_verification`, `articles_mentioned`, `label_flag` (`status` is suspect, advisory, host_marked or candidate, plus a `reason`), `exemplar_for` and `provenance` (`workbook`, `sheet`, `row`). Evaluation only; never use it to decide anything |

**Tiers:**
- **A (9):** pillars 6 and 7, from the Round 1 codebook.
- **B (14):** drafted at the same depth, not yet reviewed.
- **C (38):** built from host text only, with no traps.

Decision D4: a row mapped under a Tier C indicator names its tier in Notes, and needs more confidence
before it is tagged NEW.

### Host rules the instrument now encodes

These affect mapping, roll-up, export and review.
- **7.1 and 7.2 are economy-level.** Answer once per economy; per-provision rows score zero.
- **7.3 needs a stated minimum duration.** A prescribed period with no number, a notification
  deadline or an appeal window does not count.
- **7.5 is personal data accessed without independent judicial authorisation.** It does not cover
  inspection of business records, or a secrecy duty with a court-order carve-out.
- **6.2 is where data is stored, not general record-keeping.**
- **6.1 against 6.4:** "must not transfer UNLESS [condition]" is 6.4.
- **These score zero:** drafts, repealed provisions, an amending act cited instead of the principal
  act, and a real act cited to the wrong section.
- **Measures applied to government data** are not scored under 6.1–6.4 or 7.3.
- **Databases only point to the law:** I-TIP, Global Trade Alert, WTO Trade Policy Reviews, the
  Global Express Association database, DSTRI, UNCTAD Cyber Tracker and ITU DataHub. The cited source
  must be the official text.

## 3. Known baseline for NEW and KNOWN

The gold set now holds the Round 2 country sheets. For those economies, a law already in their sheet
is KNOWN. Viet Nam and Kazakhstan have no sheet, so every finding there is NEW. Signature exemplars now
come from the economies you will run. Exclude an economy's own rows when evaluating it: the
`exemplar_for` field says which rows each signature used.

## 4. What this means for your stage

### Scraping: `stages\p1-scrape`, workshop `rdtii-finale-1-scraping`

- **The registries are narrow.** `sources_<cc>.yaml` (in `instrument\`, with a pinned copy in
  `contracts\instrument\`) cover only SG, MY and AU, pillars 6 and 7. `seed_laws[].indicators` uses
  legacy IDs. The finale economies and all twelve pillars need registries with decimal IDs.
- **Decimal IDs break the pillar helpers.** `src\p1_scrape\sources.py:31` `indicator_pillar()`
  parses only `P6-I4` and returns None for decimal IDs; use `indicator_ids.pillar_of()`.
  `pillar_hint_for()` knows only pillars 6 and 7.
- **The manifest contract must change.** In `contracts\schemas\manifest.schema.json`, `pillar_hint`
  allows only `P6 | P7 | both | null`, and `indicator_hints` is documented with legacy IDs. Agree the
  new shape with extraction, which reads both fields.
- **The live test** is one economy, one pillar (any of the twelve) and two indicators, retrieved
  during the hour.
- **What to crawl:**
  - Skip the 14 non-regulatory indicators.
  - For 1.4, the primary sources are WTO trade-remedy notifications and official gazettes.
  - Treat the databases above as finding aids only.
- **Round 1 seeded its registries from the host baseline database.** If you seed from host rows
  again, disclose it, as the Round 1 leakage audit did.

### Extraction: `stages\p2-extract`, workshop `rdtii-finale-2-extraction`

- **The hint fields are Round 1 only.** `src\rdtii_p2\ingest.py:31` and `src\rdtii_p2\cli.py:409`
  read `pillar_hint` and `indicator_hints` from the crawler manifest, and map `pillar_hint` only to
  pillars 6, 7 or both. Accept decimal IDs and all twelve pillars once the manifest changes.
- **Keep article and paragraph on every provision.** A real act cited to the wrong section scores
  zero.
- **Mapping must tell principal acts from amending acts, and in-force text from drafts,** because the
  wrong one scores zero. Keep whatever metadata you extract for that.
- **Signature keywords are English only.** They feed the mapping prefilter. For non-English economies,
  only the dense (embedding) search leg is multilingual.

### Mapping: `stages\p3-map`, workshop `rdtii-finale-3-mapping`

The hand-off cannot happen until these are done.
- **Indicator list:** replace the `INDICATORS` literal (`config\settings.py:74`) with a loader that
  reads the 61 IDs from `indicator_order.yaml`, in host order.
- **Prompt:** `src\p3map\mapping\prompt.py` renders only the IDs in that literal, and its header still
  says "Pillars 6-7".
  - Decide between one prefix and one per pillar. Measured: one prefix with all 61 blocks is 122,681
    characters; per pillar it is 10,065–29,070; the Round 1 prefix was 25,974.
  - Never render `review_notes`.
- **Legacy IDs in code:** remove the hard-coded IDs in `src\p3map\output\submission.py`,
  `src\p3map\select.py`, `src\p3map\rollup.py`, `src\p3map\mapping\schema.py` and
  `src\p3map\output\excel_export.py`. Prefer the YAML fields (`level`, `polarity` together with
  `policies.yaml`, and `tier`) to per-indicator code branches.
- **Flags:** `src\p3map\eval\evaluator.py` and `src\p3map\discovery\malaysia.py` should read
  `label_flag.status` instead of their own ID lists. Rows marked suspect or host_marked are never
  exemplars; decide what evaluation does with each status.
- **Baseline:** `src\p3map\discovery\baseline.py` must read the baseline with decimal IDs. It also has
  to cover the Round 2 sheets (section 3).
- **Queries:** apply leave-one-economy-out in `src\p3map\prefilter\queries.py`, using `exemplar_for`.
- **Round 1 artefacts:** write `migrate_ids.py` for them. The index keys in `bm25_top.npz` and
  `dense_top.npz` go from `P6-I1_idx` to `6.1_idx`, and the IDs in `out\**\*.jsonl` also need
  converting.
- **Open question:** how rows roll up into one economy score is undefined for several indicators.
  It is going to the secretariat.
- **After hand-off:**
  - `contracts\instrument\` must match the instrument output. Run its validator with
    `--require-vendored`.
  - `tests\test_indicator_ids.py` compares the two copies of `indicator_ids.py` byte for byte.

### Dashboard: `interface\`, workshop `rdtii-finale-4-dashboard`

- **Guide page parsing:** `interface\dashboard.py` reads `stages\p3-map\contracts\instrument\indicators.yaml`
  for its Guide page (around lines 1575–1647). After hand-off, that file has 61 blocks, decimal IDs, a
  top-level `tiers` key, and per-block `tier`, `review_status`, `sources` and `review_notes`.
  - Check that the parsing still works.
  - Never show `review_notes` as host text.
- **Pipeline text:** its pipeline descriptions (around lines 412, 477 and 479) still say "6.1 → P6-I1"
  and name P6-I1 and P7-I1/I2. Update them when the mapping code changes.
- **Indicator lists:** load names, pillar labels and order from `indicator_order.yaml`. Show IDs as
  text, never as numbers; in Excel, format the column as text.
- **Tiers:** show the tier wherever a reviewer judges a row. Tier C rows carry the depth disclosure.
- **Export:**
  - Write decimal IDs. The template's Coverage Matrix derives the pillar by formula and writes "?"
    for `P6-I1`.
  - The 14 non-regulatory indicators get no rows and must not appear as gaps.

## 5. Workflow

- **Instrument changes** happen only in the instrument workspace. They are logged in its
  `CHANGELOG.md`, checked with `python code\tools\validate.py`, and sent to the repo through `HANDOFF.md`.
- **Line endings:** git here has `core.autocrlf=true`, and files mix CRLF and LF. Compare file
  content ignoring line endings. Where a test compares bytes, copy the same file to both places.
- **Host documents** (`sources\` in the instrument workspace) never go to the public repo.

## 6. What to do now

1. **Read** in the instrument workspace: `HANDOFF.md`, `DECISIONS.md` (D1–D11) and
   `instrument\output\README.md`.
2. **Check** your stage's `PLAN.md`, `DECISIONS.md` and code against sections 2–4. List what breaks
   or must change, with file and line.
3. **Record** that list in your workshop, dated.
4. **Request, don't change.** If you need something from the instrument (a field, a list, a rename),
   write down what, why, and which code reads it, for the developer to take to the instrument
   workstream. A new field must also be declared in `INTERFACE_CONTRACT.md` §4.
5. **Reply** with a short summary: what changes for your stage, what blocks you, and your requests.
