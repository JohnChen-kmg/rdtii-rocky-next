# Requests from scraping to the instrument workstream, 13 September 2026

From the scraping stage (`stages\p1-scrape`, workshop `rdtii-finale-1-scraping`), in answer to
`NOTICE_FOR_OTHER_STAGES.md` section 6. The developer takes these to the instrument workstream. The
full impact list is in `INSTRUMENT_IMPACT_2026-09-13.md` in this workshop. Item numbers such as A2
refer to it.

Scraping edits no instrument file and no copy of one. Paths use the instrument workspace layout after
decision D12 (`code\scripts\`).

## R1. A scraping copy of `indicator_ids.py`. Needed

**What.**
- A new row in `HANDOFF.md` "What goes where", copying `code\scripts\indicator_ids.py` to
  `stages\p1-scrape\config\indicator_ids.py`.
- The same `Copy-Item` in step 3, from the same source file as the mapping copy, so every repo copy is
  byte-identical.
- Extend `validate_instrument.py` to check the new copy: `VENDORED_IDS` at line 59, the check at line 323.
- List both copies in the docstring at `indicator_ids.py:13`.

**Why.**
- The notice tells scraping to use `pillar_of()`.
- Round 1 rows must be read through `normalize()` and `legacy_of()`.
- The stages share no Python and each vendors what it consumes (`docs\CODE_MAP.md:49-50`,
  `INTERFACE_CONTRACT.md:565`), so scraping cannot import the `p0-instrument` or `p3-map` copy.
- Without a copy, scraping would write a second parser, which its own decision 5 rules out.

**Why `config\`.** Scraping already imports `config.settings` (`src\p1_scrape\cli.py:12`), and
`scrape.py` and `tests\conftest.py` put the stage root on the import path. `contracts\` holds data only
and is not importable.

**Which scraping code reads it.**
- The replacement for `src\p1_scrape\sources.py:31` `indicator_pillar` and `:40` `pillar_hint_for`.
- The shared seed filter replacing `adapters\sg_sso.py:57` and `:74`, `my_gazette.py:77`,
  `au_legislation.py:137`.
- Hint normalisation at `sg_sso.py:66`, `my_gazette.py:85`, `au_legislation.py:147`.
- The new `--indicators` check in step 1C.

**Note.** The file is already in the repo at `stages\p0-instrument\scripts\` and
`stages\p3-map\config\`, identical to yours apart from line endings. This request adds a destination
and a check. It does not change the instrument. Scraping adds its own byte-compare test once the copy
arrives from your file.

**Blocks.** Scraping's move to decimal IDs (A1, A2, C5) and 1C's ID validation.

## R2. A scraping copy of `indicator_order.yaml`. Needed

**What.** A single-file `Copy-Item` of `instrument\output\indicator_order.yaml` to
`stages\p1-scrape\contracts\instrument\indicator_order.yaml`. It is checked by the validator like the
mapping copy.

**Never `/MIR` into that folder.** It holds `sources_sg.yaml`, `sources_my.yaml` and `sources_au.yaml`,
which are not in your output. A mirror would delete them. `sources.py:16` would then silently fall
back to the working copies in `instrument\`.

**Why.** Scraping needs one machine-readable list, not a literal of its own (your D6):
- the pillar of each ID;
- which IDs are in scope;
- the 14 non-regulatory IDs;
- which are practice-based.

**Fields read.**

| Field | Used for |
| :---- | :---- |
| `indicators[].id`, `status` | Rejecting a registry tag or a drawn ID that is not in scope |
| `indicators[].pillar` | Accepting pillars 1 to 12 in `economies.parse_pillars` instead of the hard-coded 6 and 7 |
| `non_regulatory_indicators` | Refusing the 14 by name in the registry lint and in 1C |
| `practice_based`, `indicators[].evidence` | Allowing announcements, reports and ownership records only for 3.4, 5.3 and 9.1 |
| `name`, `pillar_label` | Error messages and the Run Record export |

No new field is needed for these.

**Optional, same file.** A `polarity` value on each entry (inverted, absence-based or plain), copied
from `policies.yaml` `scoring_policy.polarity`. Scraping's registry lint must make sure the 14
"Lack of" and absence-based indicators each have a framework law tagged (C3). One field here saves
vendoring `policies.yaml` as well. If added, declare it in `INTERFACE_CONTRACT.md` section 4.

**Which scraping code reads it.**
- `src\p1_scrape\economies.py:44-59`.
- A registry lint in `sources.load_sources` (`sources.py:20-26`).
- 1C's indicator validation.
- A coverage test replacing the check `INTERFACE_CONTRACT.md:360` describes and nothing implements.

**Blocks.** The registry lint (A3), 1C's ID validation, and the non-regulatory skip (C4).

## R3. `INTERFACE_CONTRACT.md`: ownership, readers and the registry mandate. Needed, no deadline

The file is identical in `instrument\`, `stages\p0-instrument` and `stages\p1-scrape`. The p2 and p3
copies have already drifted: 621 lines against 612.

**What.**
1. **Settle who owns `sources_<cc>.yaml`.** Section 4 (line 256, and line 19) calls it part of the
   shared P0 instrument. Your `CHANGELOG.md:71` calls the registries crawler-owned. Scraping proposes
   moving section 4.3 into the scraping section, or marking it scraping-owned.
2. **Declare scraping as a reader** of `indicator_order.yaml` and `indicator_ids.py` under "Who reads
   what" (lines 277-280), plus any field from R2.
3. **Restate the section 4.3 mandate** (lines 354 and 360). It asks for "all nine in-scope indicators"
   in legacy IDs. Replace it with quoted decimal IDs for whatever pillar scope the developer sets,
   excluding the non-regulatory indicators. The "CI check" at line 360 does not exist. Scraping will
   own and implement it.
4. **After scraping and extraction agree the manifest shape,** update section 2.2 (`pillar_hint` line
   71, `indicator_hints` line 72) and section 3 (`pillars_in_scope`, line 204).
5. **Add `INTERFACE_CONTRACT.md` to the `HANDOFF.md` table.** Today line 53 lists it as unchanged.
   Name destinations for p0, p1, p2 and p3, so the drifted copies are brought back in line.
6. **A hand-off question, not a block on scraping.** Line 569 makes any change to "the 9 indicator
   definitions" MAJOR, and line 560 puts `policies.yaml` under the shared contract version. The finale
   instrument replaces those definitions. Say how the version moves at hand-off.

**Why.** Notice section 6 routes every new field through section 4. Scraping's plan (steps 1A-1 and
1A-7) and `docs\ADDING_AN_ECONOMY.md` build on this spec, and judges read it.

**Which code reads it.** None at run time. `manifest.schema.json`, `sources.load_sources` and the
adapters implement it.

## R4. A class for WTO documents and a list of finding aids. Only if pillar 1 is crawled

**What.**
1. **An `intergovernmental_notification` class** in `policies.yaml` `citation_url_preference`
   (lines 75-79). It covers documents an economy submits and the WTO publishes, such as trade-remedy
   notifications. Today the only class a WTO document fits is `whitelisted_reputable_secondary`,
   "last resort only". That contradicts the notice, which makes WTO notifications 1.4's primary
   source.
2. **A machine-readable `finding_aids` list with hostnames:** I-TIP, Global Trade Alert, WTO Trade
   Policy Reviews, the Global Express Association database, DSTRI, UNCTAD Cyber Tracker, ITU DataHub.
   Say whether `trade-remedies.wto.org` counts as evidence or as a finding aid. The host's own 1.4 rows
   cite it (`gold_set.jsonl`, `r2-id-003`).
3. Declare both in section 4.

**Why.** Notice section 2, "Databases only point to the law", and section 4, "For 1.4, the primary
sources are WTO trade-remedy notifications". No instrument file names the hosts, and only one database
is mentioned in the codebook (`indicators.yaml:3214`).

**Which scraping code would read it.**
- A registry key for intergovernmental sources in each adapter's `discover()`.
- `_build_row` (`orchestrator.py:357`), recording the document kind.
- A registry lint that refuses a finding-aid host as a seed URL.

**Not requested.** A per-indicator evidence-source field. `signatures\<ID>.yaml` `exemplar_law_types`
already lists the document types scraping needs, including practice evidence for 3.4, 5.3 and 9.1.
Until R4 lands, scraping keeps its own finding-aid host list in registry config.

## R5. Declare a scraping read of three signature fields. Only if ranked discovery is built

**What.** Declare in section 4 that scraping may read `keywords`, `exemplar_law_types` and
`scope_patterns` from `signatures\<ID>.yaml`, and never `exemplars`.

**Why.** For pillars with no scraping registry, these are the only per-indicator vocabulary. The
exemplars carry the host baseline laws and URLs of the economies in the draw. Scraping must not seed
from them (notice section 3, and the gold set's "evaluation only").

**Which scraping code would read it.** `sources.all_query_terms` (`sources.py:53`) and a new
ranked-discovery module in step 1C, which is optional today.

**Not requested.** Native-language search terms. They are portal-specific and belong in scraping's
own registries. Adding them to signature keywords would change mapping's retrieval.
