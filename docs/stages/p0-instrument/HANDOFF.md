# Hand-off: sending the instrument to the repo

The instrument is built, checked and edited in this folder. The pipeline runs in the repo. At hand-off,
the finished instrument is copied into the repo so the mapping stage and the interface can use it.
Until then, `instrument\` (the files) and `code\scripts\` (the code) in this folder are the only
working copy. Decisions D9 and D12 in `DECISIONS.md` record why.

## Which repo

There are four copies of the tool on this machine. Only one is the hand-off target.

| Folder on the Desktop | What it is | Hand off here? |
| :---- | :---- | :---- |
| `rdtii_rocky_next` | **The working copy**, where the mapping stage and the interface are developed since 3 October. On 4 October it was on branch `feature/desktop-workspace-triage` at commit `2edcf44`, and another session was committing to it that day | **Yes** |
| `rdtii_rocky_finale_9.30` | The submission repository, public. Its `ASSEMBLY.md` says its release tag is what runs on 15 October | Only if the developer decides the submission itself should change |
| `rdtii-rocky-finale` | The development history, at tag `finale-submission-2026-09-30`. The first hand-off landed here | No |
| `rdtii-rocky-finale-w3` | The worktree of the 13 September build, retired | No |

The contract is `instrument\output\`. The mapping stage reads its own copy at
`stages\p3-map\contracts\instrument\`, and the interface reads that same copy.

## Where things stand

- **First hand-off: done on 29 September 2026** (commit `bf2bb3e` in `rdtii-rocky-finale`, carried into
  the submission repository and `rdtii_rocky_next`). All three repos hold that instrument today.
- **Second hand-off: pending.** It carries the rounds of 4 October: every indicator at pillar 6–7 depth
  (D15) and the coverage marks (D16). 45 files differ from the repo's copy.
- **Rehearsed on 4 October** in an exported copy of `rdtii_rocky_next` at commit `2edcf44`, with the new
  files copied in as the steps below describe. The repo itself was not touched.

  | Check | Before | After |
  | :---- | :---- | :---- |
  | Mapping stage tests (`stages\p3-map`) | 450 passed, 9 skipped | 450 passed, 9 skipped |
  | Interface tests (`interface\tests`) | 216 passed, 17 skipped | 216 passed, 17 skipped |
  | Interface indicator picker, read with its own parsers | 61 indicators; tiers A 9, B 14, C 38 | 61 indicators; tiers A 9, B 52, C 0 |
  | Automated set, as the mapping stage and the interface resolve it | the nine of pillars 6 and 7 | the same nine |
  | Pillar 6–7 mapping prompt, built by the mapping stage's code | 31,929 characters | identical, byte for byte |
  | Mapping prompt for one indicator at a time (`INDICATORS_SCOPE`) | not run | builds for each of the 61 |
  | Mapping prompt for all 61 together | not run | builds: 322,081 characters |

  An earlier rehearsal the same day, at commit `5bcbf49`, gave the same result (443 mapping tests then).

## What the repo's owner has to do with it

These are in the repo, not in the instrument, so they belong to the session working there.

1. **Update one pinned test.** `interface\tests\test_map_start.py` line 29 expects
   `{"A": 9, "B": 14, "C": 38}`. After the hand-off the counts are `{"A": 9, "B": 52, "C": 0}`. The
   rehearsal did not catch it because that test is skipped without the demo extraction output; it
   will fail in the working copy.
2. **Read `framework_name` in `stages\p3-map\src\p3map\rollup.py`.** Eleven more indicators are now
   `level: economy` (4.2, 4.5, 4.6, 4.1, 5.1, 5.4, 5.7, 8.1, 8.2, 11.1, 12.9). The roll-up knows the
   framework's name only for 7.1 and 7.2, so a run that includes any of the eleven leaves that cell
   "pending". Nothing crashes, and pillar 6–7 runs are not affected.
3. **Correct two texts.** `README.md` (Known Limitations) says the blocks outside pillars 6 and 7 are
   "host-criteria-only"; they are now full depth and not yet reviewed. In the interface, the "host
   criteria only" tag will show a count of 0.
4. **Refresh `docs\stages\p0-instrument\` if wanted.** It holds copies of this folder's documents as
   of 29 September. The current ones are `CHANGELOG.md`, `DECISIONS.md`, `HANDOFF.md`,
   `NOTICE_FOR_OTHER_STAGES.md`, `README.md`, `REPORT_2026-10-04_parity.md` and `evidence\*_2026-10-04.*`.

Section "Update of 4 October 2026" in `NOTICE_FOR_OTHER_STAGES.md` has the full list of contract
changes.

## Your decisions before it goes

Listed in `REPORT_2026-10-04_parity.md` section 4:
- whether any of the 52 manual indicators should be promoted to automated
- the five economy-level calls the drafters were unsure of
- who reviews the 52 Tier B blocks, which no person has read
- whether the submission repository should also receive it, given that its tag is what runs on
  15 October

## What goes where

| From this folder | To `rdtii_rocky_next` | How |
| :---- | :---- | :---- |
| `instrument\output\` | `stages\p0-instrument\output\` | Mirror |
| `instrument\output\` | `stages\p3-map\contracts\instrument\` | Mirror. This is the contract the mapping stage and the interface read |
| `code\scripts\` | `stages\p0-instrument\scripts\` | Mirror. The scripts find the stage folder in either layout |
| `code\scripts\indicator_ids.py` | `stages\p3-map\config\indicator_ids.py` | Copy the same file. A repo test compares the two byte for byte |
| `instrument\README.md` | `stages\p0-instrument\README.md` | Copy |
| Entries tagged **instrument** in `CHANGELOG.md` | `docs\CHANGELOG_FINALE.md` | Paste |

New since the first hand-off, all inside the folders above:
- `code\scripts\build_notes.py`, `report_flags.py`
- `code\scripts\data\label_flags.yaml`, `notes_table.yaml`, `coverage.yaml`
- `instrument\output\VALIDATION_2026-10-04.txt`

## What never leaves this folder

| Folder | Why |
| :---- | :---- |
| `sources\` | Host documents, ESCAP and KMITL material |
| `instrument\examples\`, `instrument\reference\`, `instrument\framework\` | Host workbooks and templates. The submission repository was built without them, so the instrument's builders and validator cannot run there; they run here |
| `drafting\` | Host workbook rows and Guide text |
| `code\tools\`, `code\README.md` | The tools read `sources\`; the README describes this workspace's layout |
| `notes\`, `evidence\`, `REPORT_*.md` | Working notes and proof. Quote from them, or copy them under `docs\stages\p0-instrument\` |

## Steps

Run these in PowerShell. For `robocopy`, exit codes 0 to 7 mean success and 8 or higher means failure.

1. **Check here first.**

   ```
   python C:\Users\woshi\Desktop\rdtii-finale-0-instrument\code\tools\validate.py --save
   ```

   It must end with `PASS` and `exit code: 0`. Before hand-off, its INFO line says the vendored copy
   is not re-vendored. That is expected. If the codebook changed, also run
   `python code\tools\audit_citations.py` from this folder and read the lines it lists.

2. **Agree the moment with the session working in the repo.** Run `git status` there first: it may
   have uncommitted work. The copy touches only the paths in the table above. Start a branch or commit
   there as that session prefers.

3. **Copy.**

   ```
   $WS   = "C:\Users\woshi\Desktop\rdtii-finale-0-instrument\instrument"
   $CODE = "C:\Users\woshi\Desktop\rdtii-finale-0-instrument\code\scripts"
   $RP   = "C:\Users\woshi\Desktop\rdtii_rocky_next\stages"
   robocopy "$WS\output" "$RP\p0-instrument\output" /MIR
   robocopy "$WS\output" "$RP\p3-map\contracts\instrument" /MIR
   robocopy "$CODE"      "$RP\p0-instrument\scripts" /MIR /XD __pycache__
   Copy-Item "$CODE\indicator_ids.py" "$RP\p3-map\config\indicator_ids.py"
   Copy-Item "$WS\README.md" "$RP\p0-instrument\README.md"
   ```

4. **Check.**

   From this folder, which has the host workbooks the validator needs:

   ```
   python C:\Users\woshi\Desktop\rdtii-finale-0-instrument\code\tools\validate.py --require-vendored
   ```

   It must say "vendored copy p3-map/contracts/instrument/ is identical" and pass.

   In the repo:

   ```
   cd C:\Users\woshi\Desktop\rdtii_rocky_next\stages\p3-map
   python -m pytest -q
   cd ..\..
   python -m pytest interface\tests -q
   ```

   Expect the one failure named in "What the repo's owner has to do with it", item 1, until that test
   is updated. To confirm the pillar 6–7 prompt is unchanged, render it before and after the copy with
   `drafting\2026-10-04\snapshots\render_prefix.py` (its docstring gives the command) and compare the
   two files.

5. **Review and record.**
   - Read `git status` and `git diff --stat` in the repo.
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
- The repo test `tests\test_indicator_ids.py` compares its two copies of `indicator_ids.py` byte for
  byte, so step 3 copies the same file to both places.

## The old worktree

`C:\Users\woshi\Desktop\rdtii-rocky-finale-w3`, on branch `w3-instrument-61`, holds the build of
13 September, uncommitted. This folder replaced it the same day.
- Everything in it is here. Later work was done here only.
- Don't edit it.

To remove it, once we agree:

```
git -C C:\Users\woshi\Desktop\rdtii-rocky-finale worktree remove --force C:\Users\woshi\Desktop\rdtii-rocky-finale-w3
git -C C:\Users\woshi\Desktop\rdtii-rocky-finale branch -D w3-instrument-61
```

`--force` is needed because its changes were never committed. They are all in this folder.
