# Instrument change, 13 September 2026: impact on scraping

Checked on 2026-09-13 against `C:\Users\woshi\Desktop\rdtii-finale-0-instrument\NOTICE_FOR_OTHER_STAGES.md`,
sections 2 to 4. The repo was at commit `92a5e9d` on `finale` and still runs the Round 1 instrument.
Nothing has been handed off.

Method: read-only. Five readers covered code, registries, the manifest contract, this workshop's
documents, and what the stage needs from the instrument. An independent checker re-opened every
cited line, then a completeness pass went through the notice bullet by bullet. 59 of 60 items survived
the check, one was rejected, and the completeness pass added 3. The key lines were spot-checked again
before writing. No code was run against a portal, and nothing in the repo or the instrument
workspace was edited.

The requests that come out of this are in `REQUESTS_TO_INSTRUMENT_2026-09-13.md`.

Moved into `notes/` on 2026-09-13. Workshop files (`README.md`, `PLAN.md`, `DECISIONS.md`) are cited relative to the workshop root.

Path roots used below:

| Root | Path |
| :---- | :---- |
| `p1/` | `C:\Users\woshi\Desktop\rdtii-rocky-finale\stages\p1-scrape\` |
| `p2/`, `p3/` | `...\rdtii-rocky-finale\stages\p2-extract\`, `...\stages\p3-map\` |
| `repo/` | `C:\Users\woshi\Desktop\rdtii-rocky-finale\` |
| `iws/` | `C:\Users\woshi\Desktop\rdtii-finale-0-instrument\` |

The instrument workspace moved its scripts from `instrument\scripts\` to `code\scripts\` at about
14:02 on 13 September (its decision D12). Paths below use the new layout.

## The short version

**Nothing in this stage breaks at the instrument hand-off.** No P1 code reads a file under
`stages\p0-instrument` or `stages\p3-map\contracts\instrument`, and `iws/HANDOFF.md` copies nothing
into `stages\p1-scrape`.

The breaks come from two places.

1. **P1 adopting decimal IDs.** The notice forbids writing `P6-I1`, so the registries and the manifest
   must move. Done in the wrong order, a seed crawl finds 0 laws and still exits 0.
2. **The live test.** One economy, one pillar of any twelve, two indicators. P1 today can express
   none of that: no pillar outside 6 and 7, no indicator input, no live-test economy.

## A. Code: indicator IDs and pillars

**A1. The pillar helpers cannot read decimal IDs.** Bites when P1 adopts decimal IDs.
- Where: `p1/src/p1_scrape/sources.py:31-37` `indicator_pillar`, `:40-49` `pillar_hint_for`.
- What breaks: `indicator_pillar('6.1')`, `('4.01')`, `('12.4.1')` return `None`, because `int('6.1')`
  raises and the error is swallowed. `pillar_hint_for` can only return `P6`, `P7`, `both` or `None`.
- Change: use `indicator_ids.pillar_of()`, which also accepts legacy IDs, so it can land before the
  registries move. Reject non-string input before calling it: `normalize()` renders a float `12.10`
  as `'12.1'` without error (`iws/code/scripts/indicator_ids.py:43`). Needs request R1.

**A2. The seed filter drops every decimal-tagged seed, silently.** Bites when P1 adopts decimal IDs.
- Where: the same line copied four times, `p1/src/p1_scrape/adapters/sg_sso.py:57` and `:74`,
  `my_gazette.py:77`, `au_legislation.py:137`.
- What breaks: `None in pillars` is false, so every seed is skipped. `parse_pillars` never returns an
  empty list, so the filter always runs. A 0-row manifest only warns (`p1/src/p1_scrape/manifest.py:158`)
  and `run_crawl` returns 0 (`orchestrator.py:239`). `repo/main.py:491` fails later with "no wanted
  docs". In the live hour that is no documents fetched, which scores C5a zero.
- Change: one shared seed-selection helper. Match indicators by normalised string equality, never
  numerically. Raise on an unparseable registry ID. Exit non-zero when a seed-scope run selects 0 laws.
  **Rewrite the helpers in the same commit as the YAML, in both registry copies.**

**A3. Unquoted decimal IDs in YAML load as floats.** Bites when P1 adopts decimal IDs.
- Where: `p1/src/p1_scrape/sources.py:25` `yaml.safe_load`. Registry IDs are unquoted today, for
  example `p1/instrument/sources_sg.yaml:19`.
- What breaks: `6.1` loads as a float, `12.10` as `12.1`. A float reaches `.upper()`, raises, and
  `orchestrator.py:219` skips the whole economy while the run exits 0. No two in-scope host IDs
  collide as floats, so the real harm is type errors and a skipped economy, not lost buckets.
- Change: quote every ID. Validate at load: each ID is a string, is in scope in `indicator_order.yaml`,
  and is not one of the 14 non-regulatory IDs. Add this to 1A-1's done-when, which today only needs the
  files to parse (`PLAN.md:54`). Needs request R2.

**A4. `parse_pillars` turns any other pillar, or bad input, into 6 and 7.** Bites on the live test.
- Where: `p1/src/p1_scrape/economies.py:47`, `:57`, `:59`. Defaults of `"6,7"` at `p1/src/p1_scrape/cli.py:27`
  and `p1/scrape.py:32`.
- What breaks: `'4'`, `'12'`, `'6.1'`, `'abc'` and `''` all return `[6, 7]`, with no message. A
  pillar-4 draw today fetches the pillar 6 and 7 seeds, which are the wrong documents. The same
  command rejects a bad economy.
- Change: accept pillars 1 to 12, raise on anything else. `PLAN.md:66-67` defers this as "a
  twelve-pillar task, not this one". Code is frozen on 30 September, so deferring means no other
  pillar is crawlable on 15 October.

**A5. No way to pass the two drawn indicators.** Bites on the live test.
- Where: no indicator option in `p1/src/p1_scrape/cli.py:24-36` or `p1/scrape.py:30-39`.
  `p1/src/p1_scrape/adapters/base.py:23` `discover(pillars, ...)` takes pillars only.
  `sources.py:53-59` `all_query_terms` flattens every query bucket, so `--pillars` does not narrow the
  vocabulary either (`sg_sso.py:39`, `:198`, `my_gazette.py:237`, `au_legislation.py:263`). The repo
  plan's claim that `--pillars` filters queries (`p1/PLAN.md:286`) is false.
- Change: `--indicators` in 1C, normalised and checked against the in-scope list. Derive pillars from
  it when `--pillars` is absent.

**A6. The launch path carries no pillar or indicators, and rejects every live-test economy.**
Bites on the live test. `main.py` and the dashboard are not owned by this stage.
- Where: `repo/main.py:467-468` and `:481-482` pass no `--pillars`. `repo/main.py:67-72` and
  `:146` exit for any economy outside SG, MY and AU. `repo/interface/dashboard.py:63` hard-codes
  the three, `:938-940` rejects others with HTTP 400, `:898` rejects a pillar field.
- Change: extend 1B-7's four-file plumbing to carry `--pillars` and `--indicators`. Derive both
  economy lists from the YAML headers of 1A-1. Add both files to the README gap table, which counts
  three hard-coded lists (`README.md:93`).

**A7. Hints are copied verbatim, in registry order.** Bites when P1 adopts decimal IDs.
- Where: `sg_sso.py:66`, `my_gazette.py:85`, `au_legislation.py:147`. `p1/tools/refetch_au_multivolume.py:122`
  copies legacy hints from old rows into new ones.
- Change: normalise each token and order by `indicator_order.yaml`, never by sorting.

**A8. English-only title matching.** Bites when a non-English economy is crawled beyond seed scope.
- Where: `re.findall(r"[a-z]+", ...)` at `sg_sso.py:187`, `:199`, `my_gazette.py:238`,
  `au_legislation.py:264`. The README tells new adapters to model on these (`README.md:187-189`).
- What breaks: Thai, Lao, Chinese or Cyrillic queries give no phrases, so `relevant` scope quietly
  becomes seed-only.
- Change: Unicode-aware matching in the 1A-7 template. Native-language terms live in the registry,
  keyed by quoted decimal ID. This is P1's job, not an instrument request.

**A9. No test covers any of the above.** Bites at the contract change.
- Where: the only legacy IDs in tests are the fixture at `p1/tests/test_manifest.py:38-39`, used by
  three tests that assert it validates. Nothing tests `indicator_pillar`, `pillar_hint_for`,
  `parse_pillars`, `discover` or `load_sources`. That is how A2 and A4 went unnoticed.
- Change: move the fixture to decimal text. Add tests: `4.01` and `4.1` stay distinct, `12.4.1` is
  pillar 12, a decimal-tagged seed is selected, a bad pillar raises, an unquoted float ID is rejected.

## B. The manifest contract and the stages that read it

Every item here needs agreement with extraction, inside the 0.3.0 commit (step 1A-6).

**B1. `pillar_hint` cannot name pillars 1 to 5 or 8 to 12.**
- Where: `"enum": ["P6", "P7", "both", null]` at line 73 of all three `manifest.schema.json` copies
  (`p1/contracts/schemas/`, `p2/00_contracts/schemas/`, `p3/00_contracts/schemas/`).
  `p1/INTERFACE_CONTRACT.md:71`.
- What breaks: a new value fails P1's own validation (`orchestrator.py:233`, then return code 1),
  which halts `main.py` at the crawl step. If P1's copy is updated and P2's is not, P2 ingest rejects the
  row. `p2/src/rdtii_p2/cli.py:408` maps anything but `P6`, `P7`, `both` to `[]`.
- Options (not a pick): widen with a pattern for pillar numbers as text, keeping the legacy values
  (MINOR, frozen rows stay valid); or freeze the field as legacy and derive pillars from
  `indicator_hints` with `pillar_of()`. The second loses nothing: on all 2,706 frozen rows
  `pillar_hint` equals the value derived from the hints. Changing the type is MAJOR.

**B2. `indicator_hints` is documented with a banned example and never checked.**
- Where: line 77 of all three schema copies, "e.g. 'P7-I2'". `p1/INTERFACE_CONTRACT.md:72`.
- Decimal values already validate, because the field is a plain string. Change the description, and
  optionally add a token pattern accepting legacy or decimal IDs.

**B3. Decimal hints break Hand-off #2, which decision 5 missed.**
- Where: `p2/src/rdtii_p2/cli.py:422` copies hint tokens into `laws.jsonl` `indicators_searched`.
  `p2/00_contracts/schemas/laws.schema.json:23` requires `^P[67]-I[1-5]$`, `:20` limits
  `pillars_in_scope` to `[6, 7]`. The p3 copy carries the same pins. `p2-extract validate` fails every such
  row. `p2-extract run` does not validate, so nothing crashes, but the gate fails.
- Also: `laws.schema.json:15-16` pin `doc_id` and `economy` to SG, AU and MY. A new economy fails
  there even after the manifest schemas widen. Decision 2 widens only the manifest copies.

**B4. The frozen manifest holds 63 legacy hint rows.**
- 63 of 2,706 rows carry hints: `pillar_hint` P7 50, both 11, P6 2. The 9 tokens are all legacy.
  The DATA and in-repo `manifest.csv` copies are identical.
- A schema that drops the legacy values fails those rows, and with them 1A-6's done-when
  (`PLAN.md:142-144`). Host question 4 now only decides whether these 63 rows are rewritten. The notice
  says read them through `normalize()` and `legacy_of()`.

**B5. 1A-6's done-when cannot pass as written, regardless of hints.**
- Where: `p1/src/p1_scrape/manifest.py:99-104` fails any CSV whose header is not exactly
  `MANIFEST_FIELDS`. The frozen file has 28 columns. The break starts at 1A-5 (`PLAN.md:104`),
  which appends `language` first.
- Change: accept a header that is a prefix of `MANIFEST_FIELDS` for older rows, or restate the
  done-when.

**B6. The manifest cannot tell a principal act from an amending act, a guidance note, a draft or
repealed text. The status it does carry is asserted, not observed.**
- Where: `source_type` is file format only (schema line 54). `in_force_status` is free text
  (schema line 132).
  - SG writes the literal `"Current"` at `sg_sso.py:67` and `:141`: 536 of 536 rows, including the
    amending act `sg-pdpa2020-001` and a PDPC guide.
  - MY never sets it: 869 of 869 rows empty.
  - AU reads it from the register harvest: 1,287 `InForce`, 14 empty, and null for every seed in seed
    scope.
- Known at discovery and thrown away: AU `isPrincipal` (`au_legislation.py:183`) and MY
  `type=amendment` (`my_gazette.py:111-113`).
- Nine amending or commencement instruments are seeded with the principal act's indicator tags:
  `p1/instrument/sources_sg.yaml:20`, `:40`, `:42`, `:44`, `:59`; `sources_my.yaml:28`;
  `sources_au.yaml:30`, `:32`, `:35`.
- Why it matters: drafts, repealed provisions and an amending act cited instead of the principal act
  all score zero (notice section 2). Extraction and mapping need this metadata to avoid them.
- Change: agree optional fields in 0.3.0: a document kind, a link from an amending act to its
  principal, and a status that holds only what was read from the portal, with its source. Stop writing
  the literal at `sg_sso.py:67`. **This corrects decision 8**, see E3.

**B7. The versioning rule is misquoted, and one clause needs a hand-off answer.**
- `p1/INTERFACE_CONTRACT.md:567` makes an appended optional field PATCH, not MINOR as decision 2 says
  (`DECISIONS.md:34`). `:568` makes a new enum value MINOR, which covers widening `pillar_hint`.
- `:569` freezes "the 9 indicator definitions" as MAJOR, time-boxed to 20 July. The finale instrument
  replaces them, and `:560` puts `policies.yaml` under the shared contract version. That is a question
  for the instrument hand-off, not a block on P1's 0.3.0. See request R3.

## C. Scope, the live test, and what to crawl

**C1. Step 1C covers pillars 6 and 7 in at most three of the nine draw economies.**
- Where: `PLAN.md:19`, `:296`. Notice section 4 and `iws/instrument/output/indicator_order.yaml:7-8`:
  the sealed task may fall in any pillar. Singapore, Malaysia and Australia are not in the draw.
- What breaks: with 1C's planned indicator filter, a draw outside 6 and 7 selects no seed, so nothing is
  fetched and C5a scores zero. Every seed in all six registry files is tagged P6 or P7 (21, 21, 20 seed laws).
- Change: state what 1C covers and disclose the rest as a risk, or reopen the "optional" ranked
  discovery. Needs the developer's scope decision, C2.

**C2. Decision 7 and the notice disagree on scope, and so does the instrument with itself.**
- This workshop: pillars 6 and 7 only (`DECISIONS.md:126-128`, `README.md:107`, `PLAN.md:297`).
- Notice section 4, line 97: "all twelve pillars need registries with decimal IDs".
- Instrument D8 (`iws/DECISIONS.md:105`), `iws/README.md:85` and `iws/PLAN.md:18` still say pillars
  6 and 7 are required. D11 built 61 blocks but did not withdraw D8. D8 itself names the cost: the live
  test's discovery points if the task lands elsewhere.
- **Recorded, not resolved.** The developer decides.

**C3. "Lack of" and absence-based indicators can leave a draw with no seed.**
- 14 of the 61 in-scope indicators are evidenced by the framework law whether the measure exists or not:
  4.5, 4.1, 5.1, 5.4, 5.7, 7.1, 7.2, 8.1, 8.2, 11.1, 12.9 (inverted) and 4.2, 4.6, 12.5 (absence-based),
  per `iws/instrument/output/policies.yaml:91`. A registry curated around restrictions may tag no seed
  for them.
- Change: the 1A-7 checklist requires at least one framework or general-rules law tagged per in-scope
  indicator. A registry lint lists untagged indicators. 1C fails loudly or falls back when a filter
  yields zero.

**C4. No step skips the 14 non-regulatory indicators.** Low exposure today: 13 of the 14 are absent
from `indicator_order.yaml`'s indicator list, and no seed carries one. It matters when new registries
are tagged. Pillar 1 has one in-scope indicator, 1.4.

**C5. No step migrates the registries and helpers to decimal IDs.**
- The 25-hour total (`PLAN.md:3`) and the freeze table (`PLAN.md:293`) have no such step. Without it
  the crawler keeps writing `P6-I1` after 30 September.
- Change: add a step. Done when both registry copies carry quoted decimal IDs, a seed run selects the
  same 21, 21 and 20 seeds as today, and new rows carry decimal hints.

**C6. Estimates assume nine indicators.** `PLAN.md:321`, `README.md:132`, `DECISIONS.md:138`. In-scope
indicators per pillar, from `indicator_order.yaml`: 1:1, 2:3, 3:5, 4:7, 5:6, 6:4, 7:5, 8:4, 9:3,
10:4, 11:4, 12:15. Mark each estimate "pillars 6 and 7 only", or re-estimate if scope widens.

**C7. Sources beyond national portals.** Bites if pillar 1, 3, 5 or 9 is crawled.
- 1.4's primary source is WTO trade-remedy notifications, which are intergovernmental. 3.4, 5.3 and 9.1
  take practice evidence: announcements, reports, ownership records. `README.md:9` says "official
  government portals" only.
- The adapters' generic fallbacks: SG ignores a seed's `form:`, AU honours only `html`
  (`au_legislation.py:236`), MY honours `pdf`. A PDF behind a non-`.pdf` URL, the shape
  `docs.wto.org` uses, is planned as a Playwright HTML fetch and most likely fails.
- Change: decide whether these are in scope. If so, add a WTO source, have every adapter honour
  `form:`, and see request R4.

**C8. No guard keeps finding aids out of `source_url`.**
- `README.md:204-205` points new economies at the host inventories as precedent. Those carry a Global
  Express Association file (`p1/reference/Legal_Inventory_SG_MY_AU.csv:111`), a WTO Trade Policy
  Review (`:145`) and a law-firm statute copy (`:303`). MY's fallback resolves to `cyrilla.org` copies
  (`p1/instrument/sources_my.yaml:20`, `:38`; `my_gazette.py:102`) with no flag in the manifest.
- All 2,706 frozen rows are on government hosts, so nothing is wrong today.
- Change: a P1-side finding-aid host list, where a hit is a pointer to resolve, never a document.
  Flag secondary copies. Allow company or ownership records only for 3.4, 5.3 and 9.1. Use the host
  inventories for law names only, never URLs.

**C9. robots.txt is never checked, though three documents say it is.**
- Where: `p1/src/p1_scrape/politeness.py:37` `RobotsAdvisor` is defined and never instantiated.
  `p1/config/settings.py:105-106` are read by nothing.
- Claimed at `README.md:83`, `README.md:165`, decision 6 (`DECISIONS.md:107`) and
  `repo/interface/dashboard.py:320`, `:559`. Checklist item 25 asks for file-and-line proof.
- Change: wire it in before the rate wait, or correct the claim. Record the choice. New hosts added for
  the finale inherit nothing today.

## D. Leakage and seeding

**D1. Seeding a Round 2 economy from its sheet is backward induction.**
- The gold set holds Round 2 rows with law names and URLs across all twelve pillars: TH 115, CN 111,
  ID 171, LA 90, MN 75, RU 97. Signature exemplars with URLs: TH 29, CN 46, ID 49, LA 37, MN 26, RU 46.
- Round 1's audit cleared P1 only because discovery was over-inclusive (2,673 documents,
  `LEAKAGE_AUDIT_2026-07-16.md:20`). Step 1C fetches only tagged seeds, so a sheet-seeded registry
  would fetch exactly the KNOWN laws in the sealed hour.
- Hosts harvested from those URLs include non-government copies: `base.garant.ru` 86 URLs,
  `consultant.ru`, `docs.cntd.ru`.

**D2. Viet Nam and Kazakhstan are clean, but proxies exist.** No gold row or exemplar comes from VN or
KZ. RU rows cite Eurasian Economic Commission instruments that also bind Kazakhstan, `r2-ru-089` and
`r2-ru-091` cite Kazakhstan's WTO accession document, and ASEAN instruments appear in ID, LA and TH
rows. Seeding a shared regional instrument is legitimate (`policies.yaml:54`). Taking the list from
another economy's sheet is not.

**D3. Round 1's disclosure is incomplete.**
- Five Round 1 seeds were requested by P3 by gold ID or error-check target
  (`p3/docs/DELTA_CRAWL_REQUEST_2026-07-14.md:43-47`): `p1/instrument/sources_au.yaml:32`, `:44`;
  `sources_sg.yaml:48`, `:51`; `sources_my.yaml:71`.
- Measured overlap, depending on how URLs are normalised: 26 to 30 of 62 seeds match the host CSV,
  25 to 26 match a Round 1 gold URL.
- `README.md:217` says the audit "found no backward induction". The audit says "no *hard* backward
  induction". `README.md:204` names only the CSV, while every registry header says "+ Round 1 baseline
  DB" (`p1/instrument/sources_sg.yaml:2`).

**D4. The rules that follow.**
- P1 never reads signature exemplars or the gold set for discovery, targeting or seeding. It reads none
  today.
- Every seed records its provenance: portal browse, official search, or a named host row.
- Any use of host rows is disclosed in a dated note, and the audit reasoning is re-run per new
  registry before commit.
- A sixth evidence artefact: seed provenance plus the leakage re-check.
- Registry header codes equal the gold codes CN, IN, ID, LA, MN, RU, TH. Mapping joins on the code
  (`p3/src/p3map/discovery/newknown.py:84-85`). VN and KZ codes are agreed with mapping.

## E. Documents now wrong or stale

| # | Where | What is wrong | Change |
| :---- | :---- | :---- | :---- |
| E1 | `DECISIONS.md` decision 5, lines 80-100 | Its instrument blocker is lifted: D1 and D7 settle decimal IDs, and `iws/CHANGELOG.md:71` says the registries are crawler-owned. "Not a schema break" is wrong downstream (B3). It never mentions `pillar_hint` (B1). "Use the p0 copy" can only mean a vendored copy: stages share no Python (`repo/docs/CODE_MAP.md:49-50`). It does not record the ordering trap (A2) | Revise when the developer takes it. Host question 4 stays open for the 63 rows only |
| E2 | `DECISIONS.md` decision 2, line 34 | Cites appended optional fields as MINOR. The contract says PATCH (B7) | Correct the citation |
| E3 | `DECISIONS.md` decision 8 | Its example treats `in_force_status` as three spellings of one value. The values are asserted, not observed (B6). Unifying the format would hide that. Adding amendment seeds tagged with the principal's indicators adds rows that score zero if cited | Corrected in place on 2026-09-13 |
| E4 | `PLAN.md` 1A-6, lines 122-144 | The table omits `pillar_hint`, `indicator_hints` and the P2 and P3 `laws.schema.json`. The done-when cannot pass (B5) | Add the rows, restate the done-when, re-estimate |
| E5 | `PLAN.md` 1A-1 line 54; 1A-2 lines 66-67; 1C lines 19 and 296; freeze table line 293 | No registry lint; the pillar fix deferred past the freeze; 1C scoped to pillars 6 and 7; no migration step | See A3, A4, C1, C5 |
| E6 | `README.md` lines 93, 100-103, 204-205, 217, 228-232 | The gap table misses `main.py` and the dashboard; the drift note names only `indicator_hints`; the seed precedent is URL-level; the leakage paraphrase; "the first thing to do" sends the developer to edit the YAML first, which invites A2 | Warning added under "The first thing to do". The rest waits for the scope decision |
| E7 | Repo documents | `p1/INTERFACE_CONTRACT.md:71-72`, `:204`, section 4 (`:256` to `:392`, `:583`); `p1/PLAN.md:286`; `p1/README.md:104`; `p1/scrape.py:5`; `p1/src/p1_scrape/sources.py:32`; `p1/src/p1_scrape/__init__.py:3`; `p1/START_HERE.md:12`; `p2/INTERFACE_CONTRACT.md:74-75`, `:213`; `repo/docs/CODE_MAP.md:303` | Update when the code lands. Dated reports stay as written. The contract text goes through request R3 |

## Checked and not affected

- The instrument hand-off itself, for the reasons in the short version.
- Float parsing in current readers: P1, P2, `main.py` and the dashboard all read the manifest with
  `csv` or `json`, so IDs stay text.
- `instrument_version` is always written as `None` (`p1/src/p1_scrape/orchestrator.py:364`).
- `seed_queries` keys are never parsed. Only the values are read, so renaming the keys needs no code.
- The classifier, fetcher, storage, dedup, smoke test and settings hold no indicator or pillar logic.
- No P3 code reads `pillar_hint` or `indicator_hints`, and no P3 code loads the manifest schema.
- The frozen raw bytes, `doc_id` values and sidecars.
- Decisions 1, 3 and 4. Decision 6's limits, apart from the robots claim in C9.
- Plan steps 1A-3, 1A-4, 1A-5, 1A-7, 1B, 1D and 1E, apart from the plumbing and header notes above.
- The retired `rdtii-rocky-finale-w3` worktree is referenced nowhere in this workshop or the stage.

## What blocks this stage

| Blocker | Owner | Blocks |
| :---- | :---- | :---- |
| Pillar scope for registries and 1C: pillars 6 and 7, or every drawable pillar (C1, C2) | Developer, with the instrument on D8 | 1C, registry curation, estimates |
| Manifest 0.3.0 shape: `pillar_hint`, `indicator_hints`, document kind, amendment link, observed status, `laws.schema.json` (B1 to B6) | Extraction, with mapping as a contract party | 1A-6, 1A-5, the decimal-ID migration |
| Requests R1 and R2: a P1 copy of `indicator_ids.py` and `indicator_order.yaml` | Instrument workstream | The decimal-ID migration (C5), the registry lint (A3), 1C's ID validation |
| Host question 1, which economies | Host | New registries, VN and KZ codes |
| Seed sources for new registries, and the robots claim (C9, D4) | Developer | Registry curation, the README politeness table |

Host question 4 no longer blocks the ID format. It decides only whether the 63 frozen legacy rows get
rewritten.

## An order of work that avoids the traps

1. Take the scope, seed-source and robots decisions.
2. Agree the 0.3.0 manifest shape with extraction, including `laws.schema.json`.
3. Send requests R1 and R2. `indicator_ids.py` is already in the repo, so R1 only adds a destination.
4. Make one commit covering:
   - the vendored helper, and the helpers rewritten on `pillar_of()`;
   - the one shared seed filter;
   - the registry lint;
   - quoted decimal IDs in both registry copies;
   - the new tests.

   Check that a seed run still selects 21, 21 and 20 seeds.
5. Then build 1C: `--indicators`, pillars 1 to 12, and a loud failure on zero. Rehearse `main.py` end to end
   with a pillar outside 6 and 7 before 15 October.
