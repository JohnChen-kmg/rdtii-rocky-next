# Open questions for the secretariat

Raised 2026-09-10, extended 2026-09-12 after reading every host template line by line.
Send to escap-digitaltrade-hackathon@un.org, cc thapanee.su@kmitl.ac.th.
Question 1 still blocks the choice of the three new economies, so ask it first. Question 6 was
settled on our side on 2026-09-12 by choosing six economies.

## Status

| | |
| :---- | :---- |
| Sent | **Not recorded as sent.** Fill in the date when it goes. |
| Draft of 2026-09-20 | `HOST_EMAIL_DRAFT_2026-09-20.md`: three questions, folding in 1 and 6, plus the freeze boundary and manual checks. Questions 2 to 5 and 7 to 10 stay unsent |
| Chase if no reply by | 16 September 2026 |
| Proceed on the working assumptions below if no reply by | 18 September 2026 |

Nothing in this workspace records these questions as sent. Documents that call them "filed"
mean written down, not delivered.

---

## 1. Which economy list governs? Three host documents disagree.

| Source | Economies named |
| :---- | :---- |
| `Finalist Orientation_Slide.pdf`, slide 5, dated 18 Aug 2026 | **Mandatory:** Australia, Malaysia, Singapore. **Pick at least 3 of 8:** China, India, Indonesia, Lao PDR, Mongolia, Russian Federation, Thailand, **Timor-Leste** |
| `README_template_FINAL_ROUND.md` | "the nine economies whose 2025 RDTII database you hold: Thailand, **Viet Nam**, Indonesia, China, India, **Kazakhstan**, Lao PDR, Mongolia, Russian Federation" |
| `submission_template_stage3_v2_CLEAN.docx`, Section 4 table | The same nine as the README template. No Australia, Malaysia or Singapore row. No Timor-Leste row. |
| `OUTPUT_TEMPLATE_FINAL_ROUND.xlsx`, Instructions sheet | The live test uses one of the same nine, "with one pillar and two indicators" |

Three specific contradictions:

- **Australia, Malaysia and Singapore.** The slides make them mandatory. Neither Word
  template has a row for them. Are the Round 1 economies still required, and do they
  count toward the C1a economy bar?
- **Timor-Leste** appears only in the slides. It has no sheet in the Round 2 database,
  so there is no baseline to diff a Discovery Tag against. Every find would be NEW by
  default. Is that intended?
- **Viet Nam and Kazakhstan** appear in the Word template, the README template and the
  workbook, but neither has a sheet in `ESCAP-RDTII-2.1_ Round 2 Database.xlsx`. All three
  say "the nine economies whose 2025 RDTII database you hold". Is there an updated database
  we have not received?

**Database sheets actually held:** China, India, Indonesia, Lao PDR, Mongolia,
Russian Federation, Thailand. Seven, not nine.

### Our working assumption until they answer

Target the economies that appear on every list and have a baseline sheet, plus the three
Round 1 economies already complete. Prioritise by the live test, since it draws only from the
nine. Treat Timor-Leste as a stretch target. Treat Viet Nam and Kazakhstan as live-test risks
to prepare adapters for, even without a baseline.

---

## 2. How long is the walkthrough recording, and what must it show?

The host documents split three against two:

| Source | Length |
| :---- | :---- |
| `README_template_FINAL_ROUND.md` | "Three to four minutes" |
| Workbook Instructions sheet | "a 3-4 minute screen recording of your audit view" |
| Workbook Submission Checklist, item 19 | "3-4 min" |
| Word template, Section 6 | "Five minutes of screen capture with narration" |
| `Finalist Orientation_Slide.pdf`, slide 4 | "a 5-minute walkthrough recording" |

The content also differs. Section 6 of the Word template lists five beats, including
following a row to its official source at the cited article. Checklist item 19 lists four
and omits that one. The workbook adds that the recording "is the fallback if we cannot deploy
your system from your guide", which makes it more important than a demonstration.

**Working assumption:** record to about four minutes, which satisfies "three to four" and
stays under five, and include all five Section 6 beats.

---

## 3. Is Docker expected, or only permitted?

Section 1 of the Word template says to assume the reviewer has "Docker and Python 3.10+
installed." The README template's Quick Start shows only a Python venv. Does a
Docker-based deployment path count toward the 30-minute C4a test, and is a plain venv
still acceptable on its own?

---

## 4. Is the indicator ID format change retroactive?

Round 1 was filed with IDs in `P6-I1` form. The finale requires decimal text such as
`6.1` and `7.3`. Confirm that previously filed rows should be restated in the new format
in the finale workbook, rather than carried over as filed.

Related: the workbook contradicts itself. The Instructions sheet says write `6.1`, "Not
'P6-I1'". The column hint in row 5 of the Output Data sheet still gives the example as
`"P6-I1" , "P6_I2"`. Separately, three host documents warn that `12.10` collapses to `12.1`,
but no indicator `12.10` exists in the Indicator Reference sheet. The real trailing-zero pair
is `4.01` against `4.1`.

---

## 5. What counts as "open weights" for Engine B, and may it be hosted?

The Word template says different things in two sections:

- **Section 5:** "at least one open-weights model you could run yourself ... A hosted
  open-weights API is acceptable."
- **Section 3 checkbox:** "The core pipeline can be run end to end with no proprietary API
  or **hosted service** — that is, on the open-weights engine declared in Section 5."
- **Checklist item 12:** "runs end to end on the open-weights engine alone, with no
  proprietary API". This one does not mention hosted services.

If Engine B is a hosted open-weights endpoint, Section 5 is satisfied but the Section 3
checkbox, read literally, is not. Confirm whether a hosted endpoint serving an open-weights
checkpoint satisfies Section 3, C4b on 30 September and C5b on 15 October, given that local
inference on venue hardware with five teams sharing a network may not be feasible.

**Working assumption:** declare an open-weights checkpoint that can demonstrably run locally,
so Section 3 can be ticked honestly, even if the live hour uses a hosted endpoint serving the
same checkpoint. State both in Section 5.

---

## 6. Is the C1a bar three economies or six?

| Source | Economies | Non-English |
| :---- | :---- | :---- |
| Slide 7, "Five major differences" | "Minimum six economies processed autonomously" | "At least three" |
| Rubric on slide 6, and the workbook | "Three or more diverse economies" | not stated |
| Workbook Instructions sheet | "Depth across three beats a thin pass over ten" | not stated |
| Submission Checklist item 15 and 17 | "three or more economies" | "At least one non-English source" |

This is the single largest planning lever we have. Each new adapter is roughly 4 to 8 hours
plus 6 to 8 hours of politeness-limited crawling. The difference between three new economies
and zero is 30 to 50 hours of an 18-day window.

**Settled on our side, 2026-09-12:** six economies, three of them non-English, pillars 6 and 7.
That satisfies both readings, so this question no longer blocks work. Still worth asking,
because the answer decides whether a fourth new economy is worth any optional time. See the
scope decision at the top of `GAPS_AND_PLAN.md`.

---

## 7. The Coverage Matrix cannot count two of the live-test economies correctly

Verified by reading the workbook cell by cell:

- **The Russian Federation has no row.** It is one of the nine live-test economies and one of
  the seven baseline sheets supplied. Its provisions would not be counted anywhere.
- **Lao is labelled "Lao PDR".** The field rule for column A says to use the official UN name,
  giving "Lao People's Democratic Republic" as its own example. The matrix counts by exact
  text match, so following the field rule makes Lao count as zero.
- **The data area ends at row 109.** Every formula stops there, so the template holds 101
  provisions. Round 1 alone filed 142. Confirm whether more rows, or several workbooks, are
  expected.

**Working assumption:** write the economy label the matrix counts, record the full UN name in
Notes, add a Russian Federation row by copying an existing row's formulas, and extend the
formula range if the submission exceeds 101 rows. Declare every change in the Word document.

---

## 8. The Word template has no self-assessment section

Slide 4 says the Word document contains "your self-assessment against C1a–C4b". The
`submission_template_stage3_v2_CLEAN.docx` we hold has six sections and none of them is a
self-assessment. Confirm whether a self-assessment is required, and if so where it goes.

---

## 9. What does "left available for the marking period" require?

Checklist item 29: "After submission the interface can be left available for the marking
period." The secretariat deploys from the repository on its own clean machine. Confirm whether
item 29 means only that the repository stays deployable, or that a hosted instance must also
stay reachable between 30 September and 14 October.

---

## 10. May ESCAP's own workbooks sit in a public repository?

The repository must be public at the release tag. It currently tracks
`Round1_Baseline_Database.xlsx`, `Round2_Methodology_and_Examples.xlsx` and the host's sample
legislation folder. The statutes are public law. The baseline workbooks are ESCAP's work
product. Confirm whether they may be redistributed, or whether the repository should instead
tell a reviewer where to place their own copy.

If the answer is no, removing them after the repository is public means rewriting git history,
so this should be settled before the release tag.
