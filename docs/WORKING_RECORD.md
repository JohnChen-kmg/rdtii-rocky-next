# The working record

**Why this is in the submission rather than left behind.** The host marks honesty. Section 4 of the
submission document says its readiness table is "not a menu you will be tested from" and that "an honest
gap here costs you nothing". The live-test note says an honest account of what broke earns credit from
the committee. So the notes, the measurements and the problem registers are evidence, not clutter.

Everything here is text. No host material, no binaries.

| Path | What it holds |
| :---- | :---- |
| `stage_results/` | One file per stage, written by the workshop that did the work on the day it closed. Each says what exists, how good it is, what the next stage inherits and **what was deliberately not done**. Plus the mapping-to-interface data contract |
| `issues/` | Cross-stage problems that no single stage owned, with the decision each needed. Includes the one that found we had measured source dispersion the wrong way, and the correction |
| `stages/p0-instrument/` | How the 61-indicator codebook was built, and the disambiguations behind it |
| `stages/p1-scrape/` | The conventions, the politeness policy, the per-economy surveys, and why China is collected by hand |
| `stages/p2-extract/` | The OCR and translation tool comparisons, per script, with the losing options named. The character-error-rate work. What the grounding guarantee does and does not cover |
| `stages/p3-map/` | The experiment notes, the selection work, the problems register and its root causes |
| `stages/interface/` | The interface plan and its decisions |
| `planning/` | The requirements read line by line from the host documents, the authoritative measured numbers, the coverage register, and the questions put to the secretariat |

## Three things in here worth a reviewer's attention

**The OCR comparison is a real comparison.** `stages/p2-extract/` records that Tesseract is the only
engine tested that returns Lao characters at all, that one vision-language model writes Lao in Thai
script and another in Khmer, and that the `fast` model matched the `best` one to within half a point at
half the size. The chosen tool per economy is in `TOOLS_BY_ECONOMY.md`, with the number behind each
choice.

**The limits are stated, not implied.** Lao PDR cannot claim the under-5% character error rate, because
no Lao page has a hand-keyed reference. Roughly one Lao article number in seven was misread and repaired
from its position in the document, and every such record says so. The grounding guarantee is that a quote
is a character-exact substring of the text we stored, which is a narrower claim than fidelity to the page.

**A mistake and its correction are both kept.** `issues/2026-09-21_source-dispersion.md` measured how
many websites the tool needs by counting cited domains, concluded India needed 66, and was superseded the
same day by a analysis that resolved each row to its operative publisher and found the real figure is a
median of two for the mandatory pillars. The wrong file is kept with its error explained rather than
deleted.

## Absolute paths

Several notes cite paths on the machine where the work was done, of the form
`C:\Users\woshi\Desktop\...`. Those are the author's working paths and a reviewer cannot follow them.
They are left as written rather than rewritten, because editing a dated record to look tidier is worse
than leaving it accurate. Where a path matters to running the tool, the README and
`interface/DATA_PATHS.md` give the setting instead.
