# Notice from the instrument workstream: contract and workflow changes (13 September 2026)

You are working on one stage of the RDTII finale tool. On 13 September 2026 the instrument changed.
The instrument is the codebook every stage keys on. Nothing in the finale repo has changed yet.

Read this, check your stage against it, and record the impact in your own workshop. Do not edit
instrument files or their copies in the repo. If you need an instrument change, send a request
instead (section 6).

| | Path |
| :---- | :---- |
| Instrument workspace, the source of truth | `C:\Users\woshi\Desktop\rdtii-finale-0-instrument`. The instrument's files are in `instrument\` and its code in `code\scripts\`; together they mirror the repo's `stages\p0-instrument`. `code\README.md` explains the code workflow |
| Finale repo | `C:\Users\woshi\Desktop\rdtii-rocky-finale` |
| Retired, do not use | `C:\Users\woshi\Desktop\rdtii-rocky-finale-w3` (worktree, branch `w3-instrument-61`) |

## 1. Status

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
