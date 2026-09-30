# Hand-off note — AU multi-volume truncation fix (corpus v2.4, 2026-07-17/18)

**To: P2 (extract/tag) and P3 (map). From: P1. Deadline context: Round 1 closes 20 Jul —
this unblocks the AU NEW/KNOWN diff.**

## What happened (one paragraph)

The AU HTML lane had silently captured only **volume 1** of every multi-volume
legislation.gov.au compilation (the `iframe#epubFrame` viewer renders one epub spine
document = one volume at a time). The independent judge caught it
(`SUBSTANTIVE_SPOTCHECK_MY_AU_2026-07-17.md`); the full audit found **33 affected acts**
(of 399 AU register HTML docs). All 33 have been re-fetched **complete** from the
register's dated epub (all volumes concatenated, verified against the OPF spine, official
host, full provenance). Details: P1 completion report **Addendum 5**;
audit: `AU_HTML_TRUNCATION_AUDIT_2026-07-17.md` (now 0 truncated remaining);
validate: 2,706 rows, 0 errors, contract 0.2.0 unchanged.

## What P2 must do (additive re-extract — 33 docs)

Re-extract the 33 `-002` doc_ids below and **retire the corresponding `-001`
extractions**. Do not re-run the whole AU lane: nothing else changed. Mechanics:

- Every `-002` row is `source_type=html`, same contract fields as before. The stored
  HTML is the register's own volume documents concatenated; volume boundaries are marked
  with `<!-- p1-epub-spine-doc i/n: … -->` comments (n = volume count) if you want
  per-volume splitting.
- The `-001` rows are still in the manifest (provenance) and are annotated
  `superseded by <new> …` in `crawl_notes` — **skip any manifest row whose crawl_notes
  contains "superseded by"** going forward; that rule is future-proof.
- Section markup is unchanged (`CharSectno`, `ActHead5`, etc. — same classes your HTML
  lane already parses); the files are just complete now (e.g. Corporations Act 2001:
  ss.1–1712 across 7 volumes, 22.7 MB).

| superseded (-001) | new (-002) | law | new size |
|---|---|---|---|
| au-asica2001-001 | au-asica2001-002 | Australian Securities and Investments Commission Act 2001 | 2.7 MB |
| au-ba2015-001 | au-ba2015-002 | Biosecurity Act 2015 | 3.2 MB |
| au-bsa1992c8a4-001 | au-bsa1992c8a4-002 | Broadcasting Services Act 1992 | 4.8 MB |
| au-ca1901-001 | au-ca1901-002 | Customs Act 1901 | 7.8 MB |
| au-ca1914-001 | au-ca1914-002 | Crimes Act 1914 | 5.5 MB |
| au-ca2001-001 | au-ca2001-002 | Corporations Act 2001 | 22.7 MB |
| au-cca1995-001 | au-cca1995-002 | Criminal Code Act 1995 | 7.2 MB |
| au-cca2010-001 | au-cca2010-002 | Competition and Consumer Act 2010 | 11.4 MB |
| au-cea1918-001 | au-cea1918-002 | Commonwealth Electoral Act 1918 | 4.4 MB |
| au-cta1995-001 | au-cta1995-002 | Customs Tariff Act 1995 | 16.1 MB |
| au-epbca1999-001 | au-epbca1999-002 | Environment Protection and Biodiversity Conservation Act 1999 | 5.9 MB |
| au-fbtaa1986-001 | au-fbtaa1986-002 | Fringe Benefits Tax Assessment Act 1986 | 2.2 MB |
| au-fla1975-001 | au-fla1975-002 | Family Law Act 1975 | 4.4 MB |
| au-fwa2009936e-001 | au-fwa2009936e-002 | Fair Work Act 2009 | 7.3 MB |
| au-hia1973-001 | au-hia1973-002 | Health Insurance Act 1973 | 3.6 MB |
| au-itaa1936-001 | au-itaa1936-002 | Income Tax Assessment Act 1936 | 11.7 MB |
| au-itaa1997-001 | au-itaa1997-002 | Income Tax Assessment Act 1997 | 33.1 MB |
| au-ma1958-001 | au-ma1958-002 | Migration Act 1958 | 6.3 MB |
| au-nccpa2009f78b-001 | au-nccpa2009f78b-002 | National Consumer Credit Protection Act 2009 | 3.7 MB |
| au-ntsa199954b8-001 | au-ntsa199954b8-002 | A New Tax System (Family Assistance) (Administration) Act 1999 | 3.0 MB |
| au-ntsa199978da-001 | au-ntsa199978da-002 | A New Tax System (Goods and Services Tax) Act 1999 | 4.5 MB |
| au-opggsa2006-001 | au-opggsa2006-002 | Offshore Petroleum and Greenhouse Gas Storage Act 2006 | 9.2 MB |
| au-sa1976-001 | au-sa1976-002 | Superannuation Act 1976 | 2.7 MB |
| au-sia1993-001 | au-sia1993-002 | Superannuation Industry (Supervision) Act 1993 | 4.0 MB |
| au-ssa1991-001 | au-ssa1991-002 | Social Security Act 1991 | 16.3 MB |
| au-ssa1999-001 | au-ssa1999-002 | Social Security (International Agreements) Act 1999 | 2.9 MB |
| au-ssa1999dcb5-001 | au-ssa1999dcb5-002 | Social Security (Administration) Act 1999 | 3.7 MB |
| au-ta1979-001 | au-ta1979-002 | Telecommunications (Interception and Access) Act 1979 | 3.9 MB |
| au-ta1997-001 | au-ta1997-002 | Telecommunications Act 1997 | 6.2 MB |
| au-taa1953-001 | au-taa1953-002 | Taxation Administration Act 1953 | 8.7 MB |
| au-tga1989-001 | au-tga1989-002 | Therapeutic Goods Act 1989 | 4.4 MB |
| au-vea1986-001 | au-vea1986-002 | Veterans' Entitlements Act 1986 | 8.3 MB |
| au-wa2007-001 | au-wa2007-002 | Water Act 2007 | 3.7 MB |

## What P3 must do (two indicator re-runs)

1. **Re-run AU P7-I3 (data retention)** against `au-ta1979-002`. The previous corpus
   physically lacked Part 5-1A of the TIA Act 1979; the new text contains
   ss.187A–187N — verified to include **s.187C** (the section the host baseline's only
   AU 7.3 row, r1-au-041, cites verbatim) and the phrase "data retention". Expect the
   KNOWN match to appear now; its absence before was a P1 corpus defect, not a mapping
   miss.
2. **Re-check AU P7-I5 (government access / interception)** against `au-ta1979-002`
   (interception warrants regime now complete through Chapter 5) and `au-ta1997-002`
   (Telecommunications Act 1997 now complete to s.594 — Part 14, incl. ss.313–315
   carrier assistance obligations, was in the missing volume 2).
3. Any other AU mapping that scored against the 33 acts above should be re-scored from
   the `-002` texts before the AU NEW/KNOWN diff is finalized — volumes 2+ were absent
   across the board (e.g. Corporations Act beyond s.260E, Fair Work beyond s.257).

## Provenance

Every re-fetch: official host (`www.legislation.gov.au` dated epub endpoints), plain
requests, rate-limited, logged in `crawl_log.jsonl` (34 entries incl. one disclosed
byte-identical duplicate), `.headers.json` sidecar per artifact, sha256 in the manifest.
