"""Deterministic downstream chain (2026-07-16 audit item 3).

Runs S5 -> S7 -> S6 -> S9 -> S10, then the two review surfaces, in order for one economy, so no
stage ever consumes a sibling's stale artifact. Use this instead of invoking the stages by hand once
mapping (S4) is complete.

    python -m src.p3map.chain SG
    python -m src.p3map.chain TL --extra-dirs ../run/out_tl52   # an economy mapped in two arms
    python -m src.p3map.chain CN --gloss                        # + machine English (costs money)

Two flags exist because of two things that used to go wrong silently.

`--gloss` runs S9b before the workbook and the audit page. Both surfaces have a machine-English
column, and without the gloss those columns are simply blank -- which looks like "this economy needs
no translation" rather than "the step was not run". It is OPT-IN rather than default because it calls
a paid model, and a chain that spends money without being asked is worse than one that leaves a
column empty. English-source economies need it no more than they need a translator: the glosser
writes nothing for them.

`--extra-dirs` passes further run directories to the workbook and audit page, for an economy mapped
in more than one arm. Timor-Leste is that case, and without it a re-run produces a workbook covering
one arm that looks entirely normal and is missing 52 indicators.

What this chain does NOT do, because both are whole-run steps rather than per-economy ones:

    python -m src.p3map.output.template  --template <host xlsx> --out <x> --records <csv>...
    python -m src.p3map.output.package   --out submission --arm <E>=<dir> ... --template <host xlsx>

S9c fills the host's Output Data sheet from every economy's records at once (it has to choose 101
rows out of all of them), and S9d assembles the submission folder. Run them after the last economy.
`python -m src.p3map.output.urlcheck` checks every filed Source URL and is also whole-run.
"""
from __future__ import annotations

import argparse


def run_chain(economy: str, skip_verify: bool = False, gloss: bool = False,
              extra_dirs=()) -> None:      # noqa: ANN001
    if not skip_verify:
        from src.p3map.verify.blind import run_verify
        run_verify(economy)                       # S5 (resumes/no-ops if done)
    from src.p3map.discovery.newknown import run_newknown
    run_newknown(economy)                         # S7
    from src.p3map.rollup import run_rollup
    run_rollup(economy)                           # S6 (reads verified directly)
    from src.p3map.output.submission import run_submission
    run_submission(economy)                       # S9
    from src.p3map.eval.evaluator import run_eval
    run_eval(economy)                             # S10
    if gloss:
        # before the two surfaces that render it, or their English columns stay blank
        from src.p3map.output.gloss import run_gloss, run_section_gloss
        run_gloss(economy)                        # S9b, the quote
        run_section_gloss(economy)                # S9b, the whole provision
    from src.p3map.output.excel_export import export
    export(economy, extra_dirs=extra_dirs)        # review workbook
    from src.p3map.verify.audit_view import render
    render(economy, extra_dirs=extra_dirs)        # audit page


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="S5->S10 plus the review surfaces, for one economy")
    ap.add_argument("economy", nargs="?", default="SG")
    ap.add_argument("--skip-verify", action="store_true",
                    help="S5 already done and you do not want it re-checked")
    ap.add_argument("--gloss", action="store_true",
                    help="also run S9b machine English before the workbook and audit page. "
                         "Costs money; without it those columns are blank rather than absent")
    ap.add_argument("--extra-dirs", nargs="*", default=[],
                    help="further run directories for an economy mapped in more than one arm")
    a = ap.parse_args()
    run_chain(a.economy, skip_verify=a.skip_verify, gloss=a.gloss, extra_dirs=a.extra_dirs)
