# Hand-off: sending the instrument to the repo

The instrument is built, checked and edited in this folder. The pipeline runs in the repo. At hand-off,
the finished instrument is copied into the repo so the mapping stage and the interface can use it.
Until then, `instrument\` (the files) and `code\scripts\` (the code) in this folder are the only
working copy. Decisions D9 and D12 in `DECISIONS.md` record why.

## Which repo

There are four copies of the tool on this machine. Only one is the hand-off target.

| Folder on the Desktop | What it is | Hand off here? |
| :---- | :---- | :---- |
| `rdtii_rocky_next` | **The working copy**, where the mapping stage and the interface are developed since 3 October. On the evening of 4 October it was on branch `feature/desktop-workspace-triage` at commit `421e7f5`, tree clean, and other sessions were committing to it that day | **Yes** |
| `rdtii_rocky_finale_9.30` | The submission repository, public. Its `ASSEMBLY.md` says its release tag is what runs on 15 October | Only if the developer decides the submission itself should change |
| `rdtii-rocky-finale` | The development history, at tag `finale-submission-2026-09-30`. The first hand-off landed here | No |
| `rdtii-rocky-finale-w3` | The worktree of the 13 September build, retired | No |

The contract is `instrument\output\`. The mapping stage reads its own copy at
`stages\p3-map\contracts\instrument\`, and the interface reads that same copy.

## Where things stand

- **First hand-off: done on 29 September 2026** (commit `bf2bb3e` in `rdtii-rocky-finale`, carried into
  the submission repository and `rdtii_rocky_next`).
- **Second hand-off: done on 4 October 2026** (commit `bafe873` in `rdtii_rocky_next`), by the session
  working in that repo, following this file. It carried every indicator at pillar 6–7 depth (D15) and
  the coverage marks (D16). That session also updated the pinned tier counts in
  `interface\tests\test_map_start.py`, corrected the repo `README.md`, and refreshed
  `docs\stages\p0-instrument\`. The mapping stage now reads scales, `level` and `framework_name` from
  the blocks (commits `bbcd27a`, `421e7f5`).
- **Third hand-off: pending.** It carries the two roll-up fields of D17: `absence_score` with
  `absence_basis` on every block, and `count_rule` on 15 blocks. Files that differ from the repo's
  copy: `indicators.yaml`, `README.md`, `INSTRUMENT_NOTES.md` and `VALIDATION_2026-10-04.txt` in
  `output\`; `validate_instrument.py`, `build_rollup_fields.py`, `report_rollup_fields.py` and
  `data\rollup_fields.yaml` in the scripts; and `instrument\README.md`.
- **This workshop's session cannot make the copy.** Its permission system refuses writes into the
  shared repo. Run step 3 yourself, or have the session working in the repo run it, as for the second
  hand-off.
- **Rehearsed on 4 October** in an exported copy of `rdtii_rocky_next` at commit `421e7f5`, with the new
  files copied in as the steps below describe. The repo itself was not touched.

  | Check | Before the copy | After |
  | :---- | :---- | :---- |
  | Mapping stage tests (`stages\p3-map`) | 478 passed, 9 skipped | 478 passed, 9 skipped |
  | Interface tests (`interface\tests`) | 233 ran, OK | 233 ran, OK |
  | Pillar 6–7 mapping prompt, built by the mapping stage's code | 31,929 characters | identical, same SHA-256 |
  | Mapping prompt for all 61 together and for each of the 61 alone | built from the repo's instrument | identical, character for character, in all 62 scopes |

  The working copy reports 479 passed and 8 skipped in the mapping suite: one test needs run data
  that an export does not have.

## What the repo's owner has to do with it

These are in the repo, not in the instrument, so they belong to the session working there.

1. **Declare the two fields in `INTERFACE_CONTRACT.md` section 4.** The copies under
   `stages\p2-extract` and `stages\p3-map` are the same file; `stages\p1-scrape` has its own version.
   Add this after the per-indicator schema in section 4.1:

   ```
   Two fields added for the finale roll-up (instrument decision D17, 4 October 2026). Neither is
   rendered into the mapping prompt. Their values are kept in
   stages/p0-instrument/scripts/data/rollup_fields.yaml and written by build_rollup_fields.py.

       absence_score: 0            # on every block. The score of a cell when the corpus was
                                   # searched and no qualifying provision was found: one of the
                                   # block's scoring.values, or null = leave the cell unscored.
       absence_basis: "..."        # why, with the host source
       count_rule:                 # only on blocks that score by how many measures an economy has
         unit: measure             # what the host criterion counts: measure | sector | company |
                                   # product | procedure
         counts: "..."             # the same, in words
         counted_as: law           # what stands in for the unit today: distinct laws
         method: threshold         # threshold | sum
         counted_scores: [0.5]     # a law counts when its highest verified score is one of these
         thresholds:               # method threshold: the highest threshold met gives a score
           - {at_least: 2, score: 1}
         cap: 1                    # method sum only: add the laws' scores and stop here
         otherwise: highest_verified_score
         needs: []                 # facts a verdict would have to carry to count the unit exactly:
                                   # a list of {fact, why}
         basis: "..."              # the host rule, cited

   How a rule is applied: for one economy and one indicator, take each law's highest verified
   score. With method threshold, count the laws whose score is one of counted_scores; the cell
   takes the higher of the threshold's score and the highest single verified score. With method
   sum, add the laws' scores and stop at cap. A rule never lowers a cell.
   ```

2. **Read the two fields in the mapping stage.** `rollup.py` `measure_score()` applies `count_rule` in
   place of `ESCALATION_IDS`; `submission.py` and `measure_score()` write `absence_score` on a
   no-provision row and an empty cell, with null meaning unscored. For 6.1 and 6.2 the declared rule is
   the one in the code today, and the validator pins it.
3. **Take the six `needs` back to mapping.** 3.1 (`sector`), 5.2 (`measure_key`), 5.3 (`company`),
   10.1 and 10.3 (`products`), 10.2 (`procedure`): until a verdict records the fact, distinct laws
   stand in for the unit. `evidence\rollup_fields_2026-10-04.md` has the table.
4. **Refresh `docs\stages\p0-instrument\` if wanted.** The current documents are `CHANGELOG.md`,
   `DECISIONS.md` (D17), `HANDOFF.md`, `NOTICE_FOR_OTHER_STAGES.md`, `README.md` and
   `evidence\rollup_fields_2026-10-04.md`.

`NOTICE_FOR_OTHER_STAGES.md` has the full list of contract changes, newest first.

## Your decisions before it goes

- whether the 3.4 count rule stays: the request named fourteen blocks, and 3.4 was added because its
  block counts mechanisms
- whether 1.4, 5.3, 9.1, 11.4 and 12.6 should stay unscored on an absence, or score 0 as before
- still open from `REPORT_2026-10-04_parity.md` section 4: promotion of any of the 52 to automated,
  the five uncertain economy-level calls, who reviews the 52 Tier B blocks, and whether the submission
  repository also receives the instrument

## What goes where

| From this folder | To `rdtii_rocky_next` | How |
| :---- | :---- | :---- |
| `instrument\output\` | `stages\p0-instrument\output\` | Mirror |
| `instrument\output\` | `stages\p3-map\contracts\instrument\` | Mirror. This is the contract the mapping stage and the interface read |
| `code\scripts\` | `stages\p0-instrument\scripts\` | Mirror. The scripts find the stage folder in either layout |
| `code\scripts\indicator_ids.py` | `stages\p3-map\config\indicator_ids.py` | Copy the same file. A repo test compares the two byte for byte |
| `instrument\README.md` | `stages\p0-instrument\README.md` | Copy |
| Entries tagged **instrument** in `CHANGELOG.md` | `docs\CHANGELOG_FINALE.md` | Paste |

New since the second hand-off, all inside the folders above:
- `code\scripts\build_rollup_fields.py`, `report_rollup_fields.py`
- `code\scripts\data\rollup_fields.yaml`

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

   Expect the counts in "Where things stand". The mapping test `tests\test_second_handoff.py` pins the
   pillar 6–7 prompt at 31,929 characters, so a passing suite also shows that prompt is unchanged.

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
