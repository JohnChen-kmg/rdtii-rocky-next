# Build plan and gaps

Derived from `REQUIREMENTS.md`. This is the working checklist, so edit it freely as
items land. Last revised 2026-09-12.

## Scope decision, 2026-09-12

**Required for 30 September: six economies, pillars 6 and 7. Anything further is optional.**

| | Required | Optional, only if time allows |
| :---- | :---- | :---- |
| Economies | Six. Singapore, Malaysia and Australia are done, so **three new ones**. Slide 7 asks for at least three non-English, and the Round 1 three are English, so **all three new economies must be non-English**. India is mostly English and would not count | A fourth economy or more |
| Pillars | **6 and 7.** Nine scoreable indicators, already hand-authored at full depth. 6.5 stays out of scope | Pillars 1 to 5 and 8 to 12 |

Why this is enough: six economies meets both host readings of C1a, three in the workbook and six on
slide 7, so open question 6 no longer blocks anything. Pillars 6 and 7 are the mandatory pair.

What it costs, stated once so it is not rediscovered later:

- **C1b is 15 points for "pillars 6 and 7 mandatory, plus further RDTII domains".** The "further"
  part is not earned without optional pillars.
- **The live test draws one of nine economies and "may be a pillar you were never asked to work".**
  If it lands outside the six economies or outside pillars 6 and 7, the six discovery points of C5
  are likely lost. The four engine-swap points stay earnable, because the switch and the comparison
  work on any run.

Cheapest optional insurance, if a day frees up: generate machine-extracted Tier C codebook entries
for the other ten pillars from the host methodology sheet, instrument step 3B, about 8 hours. It
gives the live test something to map against on any pillar and costs no hand authoring.

Choose the three new economies from the nine live-test economies, so each one also protects the live
test: Thailand, Viet Nam, Indonesia, China, Kazakhstan, Lao PDR, Mongolia, Russian Federation. India
is in the nine but would not count as non-English.

**How the uncovered part is handled, decided 2026-09-20.** The index's operative content often sits in
a legal tier below the statute, and whether a portal publishes that tier decides whether an economy is
scoreable. For China's national database, 43 of 61 indicators are not answerable from what it carries,
and the pattern is general. The developer's decision: do not build coverage for it. Mark every
indicator the tool does not automate, in every economy, for a researcher's manual check, with the
reason, and say so in the output. The register of marks is `COVERAGE_AND_MANUAL_CHECKS.md` in this
folder. The full record, with three decisions still open on subsidiary instruments, per-portal tiers
and China's route, is `ISSUES\2026-09-20_subordinate-tier-coverage.md`. One code fix survives the
decision: the silent rewrite of other pillars to 6 and 7 must become an explicit out-of-scope message
before the freeze.

---

Revised 2026-09-10 after reading the dashboard source. The interface is further along than a
file listing suggests, and it now lives in the repo at `interface/`.

| Gap | Criteria at stake | Current state |
| :---- | :---- | :---- |
| Six economies, three non-English. Required | C1a 15, C1c 10 | Three English economies done. Three new non-English economies remain. The largest remaining build. |
| Pillars beyond 6 and 7. **Optional since 2026-09-12** | C1b 15, partly | Nine indicators across two pillars, done. Extension to further pillars is stretch work only. |
| Two **declared** engines, chosen from a control | C4b 7, C5b 4 | The plumbing exists. `interface/dashboard.py` gates `LLM_PROVIDER`, `LLM_MODEL`, `VERIFIER_MODEL` and `OCR_ENGINE` through `MODEL_ENV_ALLOWLIST`, set from the UI and validated server-side, and `probe_ollama()` checks a real local open-weights lane. What is missing is narrowing many models to exactly two declared engines behind one control. |
| Native two-engine comparison export | C5 10 | Does not exist. Section 5 of the Word template asks specifically whether the tool produces it natively. |
| Unified cost ledger, per run and per engine | C5, and Section 2 | Two separate ledgers with different scopes and three disclosed unevidenced components. See `AUTHORITATIVE_NUMBERS.md`. |
| Interface deploys from a clean clone | C3a 10, C3b 5, C4a 8 | Migrated into the repo on 2026-09-10. `DEFAULT_REPO` still resolves to an absolute Desktop path, so a reviewer's clone would not find the pipeline. One default to change. |
| Indicator IDs as decimal text | C2a 10 | Filed as `P6-I1`. Needs restating as `6.1` form in the export writer. |
| Repo public, Apache 2.0, release tag | C4a 8 | Licence is in place. The repo has no remote yet, deliberately. |

### What is already strong and should be protected

- **Stdlib-only single-file interface.** No dependency to install is the shortest path
  through the 30-minute clean-machine test.
- **Byte-exact grounding.** Every quoted snippet is a character-exact substring of frozen
  source text at recorded offsets, machine-re-verified at validation. That is C2b.
- **Blind second-model verification.** Every "applies" verdict is re-judged by a model that
  never sees the first model's reasoning, and roughly a third were overturned. That is the
  kind of thing judges ask about.
- **A real open-weights lane that has actually run**, not a declared intention.
- **A disclosure habit.** The cost ledger refuses to quote what it cannot evidence, and the
  instrument notes separate machine-checked from human-attested claims. The host marks honesty
  up, not down.
