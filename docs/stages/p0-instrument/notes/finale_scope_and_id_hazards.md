# Finale scope and indicator-ID hazards

Question answered: which indicators must the finale instrument cover, and what can go wrong with their IDs?
Checked 2026-09-13 against the host files in `sources/`.

## Scope: 62 listed, 61 scoreable

| Class | IDs | Source | Treatment |
| :---- | :---- | :---- | :---- |
| Scoreable, legal evidence | 58 IDs | Methodology sheet has criteria and scores | In scope |
| Scoreable, practice evidence | 3.4, 5.3, 9.1 | Internal Guide p.8 ("sub-pillar focuses on enforcement and practices") | In scope; secondary sources allowed for the practice; `evidence: practice` in `indicator_order.yaml` |
| Non-regulatory, listed | 6.5 | Non-regulatory indicators note; no methodology row; template note "not present in the Round 1 database extract" | Out of scope, declared |
| Non-regulatory, not listed | 1.1, 1.2, 1.3, 2.4, 4.4, 4.7, 4.8, 5.6, 9.2, 12.10-12.13 | Non-regulatory indicators note; Internal Guide p.8 (WITS, V-Dem, treaty status) | Not in the finale list; the tool does not extract them |

So the answer to "some indicators may not be needed because mapping doesn't extract them" is: of the 62 the host lists, only 6.5. The rest of the non-regulatory set is already absent from the list.

Every scoreable ID has at least 9 coded rows across the two host databases (1,054 unstruck rows in all).

## The host renumbered three indicators — never map by the Guide's numbers

| Guide position | Guide name | Host ID | Why |
| :---- | :---- | :---- | :---- |
| Pillar 4, 1st | Patent application issues | **4.01** | would otherwise be 4.1 |
| Pillar 4, 10th | Lack of effective trade secrets legal framework | **4.1** | 4.10 stored as a number collapses to 4.1 |
| Pillar 12, 1st | Foreign equity limits in e-commerce sector | **12.01** | would otherwise be 12.1, colliding with 12.10 as a number |

Evidence: the Guide's pillar 4 list (printed p.29) names ten indicators in order; the host template places "4.1 Lack of effective trade secrets legal framework" last in pillar 4, after 4.9. Host "4.1" is therefore trade secrets, not patent applications. Anything that matches Guide sections to host IDs must match by name.

## Other facts worth knowing

- The methodology sheets in the Round 1 and Round 2 databases are identical for all 61 IDs (category, criteria, scores). The template names the Round 1 copy as its source.
- In the methodology sheet, 54 IDs are stored as numbers and the seven 12.4.x IDs as text. The Indicator Reference sheet stores all 62 as text. Read IDs through `indicator_ids.normalize()`.
- Host category text has typos ("User identify requirements", "Hoirzontal", "souce code"). `category_official` keeps them verbatim so the validator can machine-match; `name` in the signature files may correct them.
- 1.4 is the only criteria cell with an extra note line ("0.25 for each measure, up to 1"); it becomes a coding rule, not a scoring branch.
- The template gives pillar weights only for pillars 6-7.
- The Indicator Reference sheet's rows 79-85 are the host's "five mapping traps checked every round" (see `trap_sources_pillars_6_7.md`).
