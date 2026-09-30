# Where each pillar 6-7 trap comes from

Question answered: for Stage A, what host source stands behind each trap line in the codebook?
Traced 2026-09-12/13 from the host PDFs (text extracts in `sources/text/`) and the host workbooks.
Page numbers: `Guide p.N` is the **printed** page (PDF page = printed + 12). Everything else is the PDF page.

Since the finale migration, every trap line in `indicators.yaml` ends with these citations in parentheses.

## The traps

| Indicator | Trap | Host source | Checked against host rows |
| :---- | :---- | :---- | :---- |
| 6.1 | A ban is not a condition: "must not transfer unless [condition]" is 6.4 | Internal Guide p.13 (FAQ 6.1 vs 6.4); Indicator Reference row 84; Extraction slides pp.33, 56; Assignment 2 brief pp.1-2 | Malaysia PDPA s.129: 6.1 = 0 (r1-my-038), 6.4 = 1 (r1-my-045) |
| 6.1 | Confidentiality is not a ban | Canvas deck pp.10-11: ESCAP marked Singapore Banking Act s.47 tagged 6.1 as "misinterpretation of law" | Banking Act s.47 recorded under 7.1 (r1-sg-039); Singapore 6.1 = 0 (r1-sg-033) |
| 6.2 | Location, not duration | Guide p.59 fn.34; Extraction slides p.31 | Singapore and Malaysia record-location rows whose duration maps to 7.3 (r1-sg-034, r1-my-042) |
| 6.2 | Storage locus, not general record-keeping | Indicator Reference row 83 (finale template) | See concern below |
| 6.3 | Licensing is not an infrastructure mandate (it is 9.4) | Internal Guide pp.13-14; Guide p.52; Extraction slides pp.36-37 | No 6.3 = 1 row in SG/AU/MY; positives come from Round 2 (CN, RU, ID, MN) |
| 6.4 | Mirror of the ban trap: a compliant path means 6.4 | Guide p.54 (Singapore example); Canvas deck p.7 (PDPA s.26(1) tagged 6.4); Indicator Reference row 84 | Singapore PDPA s.26: 6.4 = 1 (r1-sg-036) |
| 7.1, 7.2 | Inverted polarity | Methodology sheet 7.1/7.2 ("Lack of ..."); Guide pp.58-59; Assignment 1 answer key p.2 ("Extra note: Inversion of polarity"); Extraction slides pp.43-44 | Singapore PDPA 7.1 = 0 (r1-sg-038); Cybersecurity Act 7.2 = 0 (r1-sg-040) |
| 7.1, 7.2 | Economy-level: answered once per economy; per-provision citations are not discoveries | Indicator Reference row 80 (finale template) | Round 1 recorded several 7.1 rows per economy (r1-my-049/050/051) |
| 7.3 | A maximum period is not a minimum | Guide p.60 (scoring text, fn.35, fn.36); Internal Guide p.13; Extraction slides p.45; Assignment 2 brief p.2; Indicator Reference row 81 | Singapore PDPA s.25 = 0 (r1-sg-041) follows it; Malaysia r1-my-053/054 = 1 break it (flagged suspect) |
| 7.3 | "Prescribed period" with no number, notification deadlines, appeal windows are not retention rules | Indicator Reference row 81 (finale template) | — |
| 7.4 | Adjacent roles are not DPOs | Guide p.61 (Türkiye: VERBIS contact person and local representative, no DPO mandate; Singapore DPIA only advised) | Australia PIA not mandated = 0 (r1-au-042); India compliance officer = 0 (r2-in-095) |
| 7.5 | Look beyond privacy law | Extraction slides p.47 (criminal procedure, surveillance, lawful access, national security, telecom law); slides pp.48-49 quiz (Singapore CPC s.39 → 7.5); Guide p.62; Methodology sheet 7.5 ("without court orders") | SG CPC = 1 (r1-sg-047); MY CPC s.116B = 1 (r1-my-064); MY SOSMA s.6(3) = 1 (r1-my-063); AU TIA Act = 1 (r1-au-044); MY PDPA = 0 (r1-my-059) |
| 7.5 | Not generic inspection of business records; not a secrecy duty with a court-order carve-out | Indicator Reference row 82 (finale template) | — |
| 6.1-6.4, 7.3 | Government data is not scored (exception) | Methodology sheet rows 30-33, 37 (category text); Guide pp.50-52, 54, 60; Internal Guide p.9 | Australia My Health Records rows flagged advisory (r1-au-034/035) |

## Other rules, same method

| Rule | Host source |
| :---- | :---- |
| 6.4 scores personal-data conditions 1 even when sector-specific; 6.1/6.2 sectoral personal data is 0.5 | Guide p.54 ("regardless of whether it is horizontal or sector-specific") against Guide pp.50-51; Australia precedent r1-au-034 = 0.5 |
| "More than one measure → 1" exists for 6.1 and 6.2 only | Guide pp.50-51 and Methodology sheet 6.1/6.2 have it; Guide p.54 and Methodology sheet 6.4 do not |
| Dual recording under 6.1 and 6.2 | Guide p.51 (Australia example) |
| Record at 0.00 rather than drop (6.3 without mandate, 7.3 without period) | Internal Guide p.13 |
| 7.4 never emits the theoretical 0.25 | Guide p.61 (DPIA-only 0.25 "has not been found"); Methodology sheet 7.4 allows only 1/0.5/0 |
| Guide typo: the 6.3 section calls local storage "indicator 6.1" | Guide p.51 |
| Amending act cited in place of the principal act scores zero | Indicator Reference row 85 |

## Concern to discuss: the finale template tightens three Round 1 readings

1. **6.2 storage locus (row 83).** Round 1 argued 6.2 up to 1 in Singapore, Malaysia and Australia from bookkeeping/tax record-location rules (DISCLOSURES item d). The host now says 6.2 is "a storage locus, not general record-keeping". A rule that records must be kept *at a place in the economy* is arguably still a locus; a duty just to keep records is not. The Round 1 exemplars r1-sg-034 and r1-my-042 sit on that line.
2. **7.1/7.2 economy-level (row 80).** Round 1 emitted several 7.1 rows per economy (horizontal law plus sectoral codes). The host says per-provision citations are not discoveries and score zero. The codebook now says: answer once per economy; sectoral instruments feed the answer but are not discoveries.
3. **7.5 business-records inspection (row 82).** Regulator inspection powers over business records do not count; the codebook now says so.

The workspace README's line "The host does not state them on the finale template" is out of date: rows 79-85 of the Indicator Reference sheet state them.
