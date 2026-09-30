# Hand-off: sending the instrument to the finale repo

The instrument is built, checked and edited in this folder. The pipeline runs in the finale repo. At
hand-off, the finished instrument is copied into the repo so the mapping stage can use it. Until then,
`instrument\` (the files) and `code\scripts\` (the code) in this folder are the only working copy.
Decisions D9 and D12 in `DECISIONS.md` record why.

| | Path |
| :---- | :---- |
| This folder | `C:\Users\woshi\Desktop\rdtii-finale-0-instrument` |
| Finale repo | `C:\Users\woshi\Desktop\rdtii-rocky-finale`, branch `finale` |
| The contract | `instrument\output\`. This is what the mapping stage reads, from its own copy at `stages\p3-map\contracts\instrument\` |

## When to hand off

Not yet. Three things come first.

1. **The mapping stage must accept decimal IDs.** It still runs on the Round 1 instrument: nine
   indicators with `P6-I1`-style IDs. Copying this instrument in before its code changes breaks
   mapping. The changes are code in the repo, under `stages\p3-map\`:
   - replace the `INDICATORS` literal in `config\settings.py` with a loader that reads the 61 IDs in
     host order. `src\p3map\mapping\prompt.py` already reads all 61 blocks from `indicators.yaml`, but
     it renders only the IDs in that literal
   - settle per-pillar or single prompt in `src\p3map\mapping\prompt.py`
   - remove the hard-coded legacy IDs in `src\p3map\output\submission.py`, `src\p3map\select.py`,
     `src\p3map\rollup.py`, `src\p3map\mapping\schema.py` and `src\p3map\output\excel_export.py`
   - make `src\p3map\eval\evaluator.py` and `src\p3map\discovery\malaysia.py` read `label_flag` from the
     gold set instead of their own ID lists
   - read the Round 1 baseline with decimal IDs in `src\p3map\discovery\baseline.py`
   - apply leave-one-economy-out in `src\p3map\prefilter\queries.py`, using `exemplar_for`
   - write `migrate_ids.py` for the Round 1 run artefacts and retrieval index (`PLAN.md` step 3A)
2. **Our open decisions**, listed in `REPORT_2026-09-13_overnight.md` section 3:
   - review of the 14 Tier B drafts
   - whether Round 1's 6.2 cells survive the host's stricter trap wording
   - what to ask the secretariat about rolling rows up to an economy score
3. **The host workbook question.** `instrument\reference\OUTPUT_TEMPLATE_FINAL_ROUND.xlsx` is a host
   document. Open host question 10 asks whether host workbooks may sit in the public repo.

## What goes where

| From this folder | To the finale repo | How |
| :---- | :---- | :---- |
| `instrument\output\` | `stages\p0-instrument\output\` | Mirror. This also deletes the nine old `P6-I1.yaml`-style signature files |
| `instrument\output\` | `stages\p3-map\contracts\instrument\` | Mirror. This is the contract the mapping stage reads |
| `code\scripts\` | `stages\p0-instrument\scripts\` | Mirror. The scripts find the stage folder in either layout |
| `code\scripts\indicator_ids.py` | `stages\p3-map\config\indicator_ids.py` | Copy the same file. The repo test compares the two byte for byte |
| `instrument\README.md`, `instrument\START_HERE.md` | `stages\p0-instrument\` | Copy |
| `instrument\reference\OUTPUT_TEMPLATE_FINAL_ROUND.xlsx` | `stages\p0-instrument\reference\` | Only if host question 10 allows it |
| Entries tagged **instrument** in `CHANGELOG.md` | `docs\CHANGELOG_FINALE.md`, under W3 | Paste |

The rest of `instrument\` is unchanged from the repo, so there is nothing to send:
- `examples\`, `framework\` and the other `reference\` files
- `INTERFACE_CONTRACT.md`, `PLAN.md`, `TOOL_WORKFLOW_PROPOSAL.md`
- `requirements.txt`, `.gitignore`

If you edit one of them here, add it to the table.

## What never leaves this folder

| Folder | Why |
| :---- | :---- |
| `sources\` | Host documents, ESCAP and KMITL material |
| `drafting\` | Host workbook rows and Guide text |
| `code\tools\`, `code\README.md` | The tools read `sources\`; the README describes this workspace's layout |
| `notes\`, `evidence\`, `REPORT_*.md` | Working notes and proof for the submission. Quote from them; don't copy them in |

The repo already tracks some Round 1 host files: two databases in `stages\p0-instrument\examples\`,
plus the Round 1 template and two CSVs in `reference\`. That predates this folder and falls under the
same host question.

## Steps

Run these in PowerShell. For `robocopy`, exit codes 0 to 7 mean success and 8 or higher means failure.

1. **Check here first.**

   ```
   python C:\Users\woshi\Desktop\rdtii-finale-0-instrument\code\tools\validate.py --save
   ```

   It must end with `PASS` and `exit code: 0`. Before hand-off, its INFO line says the vendored copy
   is not re-vendored. That is expected. If the codebook changed, also run
   `python code\tools\audit_citations.py` from this folder and read the lines it lists.

2. **Branch the repo.** Never commit on `finale` directly.

   ```
   git -C C:\Users\woshi\Desktop\rdtii-rocky-finale switch -c w3-instrument
   ```

   The name `w3-instrument-61` is still held by the old worktree (last section).

3. **Copy.**

   ```
   $WS   = "C:\Users\woshi\Desktop\rdtii-finale-0-instrument\instrument"
   $CODE = "C:\Users\woshi\Desktop\rdtii-finale-0-instrument\code\scripts"
   $RP   = "C:\Users\woshi\Desktop\rdtii-rocky-finale\stages"
   robocopy "$WS\output" "$RP\p0-instrument\output" /MIR
   robocopy "$WS\output" "$RP\p3-map\contracts\instrument" /MIR
   robocopy "$CODE"      "$RP\p0-instrument\scripts" /MIR /XD __pycache__
   Copy-Item "$CODE\indicator_ids.py" "$RP\p3-map\config\indicator_ids.py"
   Copy-Item "$WS\README.md", "$WS\START_HERE.md" "$RP\p0-instrument\"
   ```

4. **Check in the repo.** Both commands must pass.

   ```
   cd C:\Users\woshi\Desktop\rdtii-rocky-finale\stages\p0-instrument
   $env:RDTII_GUIDE_TEXT = "C:\Users\woshi\Desktop\rdtii-finale-0-instrument\sources\text\guide.txt"
   python -X utf8 scripts\validate_instrument.py --require-vendored
   cd ..\p3-map
   python -m pytest tests\test_indicator_ids.py -q
   ```

   Then run the mapping stage's own tests and a small mapping run before trusting the result.

5. **Review and record.**
   - Read `git status` and `git diff --stat`.
   - Paste the instrument entries into `docs\CHANGELOG_FINALE.md`.
   - Commit only when we agree.
   - Add a hand-off entry to `CHANGELOG.md` here, with the repo commit.

6. **Keep editing here.** Later changes go through the same steps. Don't edit the repo copy
   directly. If someone does, bring the change back here before the next hand-off, or it will be
   overwritten.

## Line endings

Files in this folder mix Windows (CRLF) and Unix (LF) line endings. Git on this machine
(`core.autocrlf=true`) writes CRLF when it checks files out, while the build scripts write LF. Git
treats both as the same content.
- The validator's comparison with the repo ignores the difference.
- The repo's `tests\test_indicator_ids.py` compares its two copies of `indicator_ids.py` byte for
  byte, so step 3 copies the same file to both places.

## The old worktree

`C:\Users\woshi\Desktop\rdtii-rocky-finale-w3`, on branch `w3-instrument-61`, holds the overnight build,
uncommitted. This folder replaced it on 13 September 2026.
- Everything in it is here, byte for byte. Later fixes were made here only.
- Its changelog entries are in `CHANGELOG.md`.
- Don't edit it.

To remove it, once we agree:

```
git -C C:\Users\woshi\Desktop\rdtii-rocky-finale worktree remove --force C:\Users\woshi\Desktop\rdtii-rocky-finale-w3
git -C C:\Users\woshi\Desktop\rdtii-rocky-finale branch -D w3-instrument-61
```

`--force` is needed because its changes were never committed. They are all in this folder.
