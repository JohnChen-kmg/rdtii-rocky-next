# S8 — Malaysia error-check · $0 · no LLM (harness)

**What we're doing:** the host's double-weighted task — auditing the 26 Malaysia
baseline rows for three failure modes.

**In → Out**
- In: the MY gold rows + the corpus + the live MY submission.
- Out: `out/errorcheck/malaysia_errorcheck.csv` (68 check rows).

**Three checks**
- **URL** — does each baseline reference URL still resolve (HTTP HEAD, cached)?
- **Currency** — baseline timeframe vs the corpus `last_amended` (missed amendments?).
- **Substance** — does the cited section exist, and for the two SUSPECT 7.3 rows
  (`r1-my-053/054`, scored 1) is it really a **minimum** retention period?

**Instrument:** the min-vs-max retention trap is encoded as regexes (`MIN_RE`
"not less than / at least"; `MAX_RE` "no longer than / cease / destroy").

**Result:** 4 dead baseline URLs found; each check row carries a `Main-CSV crossref`
to the actual submitted MY rows. The mapper independently supplied the refutation
for the suspect rows (it ruled PDPA s.10(2) a *maximum*-retention rule).
