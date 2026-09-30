"""The update check for Timor-Leste: what the Jornal da República published since the last run.

Six requests — robots.txt and one page per category — because every category page carries its whole history. The
comparison is in `diff.py`, the delta list and `changes.md` in `delta.py`, the reading in `query.py`, the CLI in
`__main__.py`. `WORKFLOW.md` beside this file is the procedure.
"""
from __future__ import annotations

from .baseline import Baseline, load as load_baseline, runs_under
from .delta import build_delta, changes_markdown, write_changes
from .diff import Change, Changes, compare
from .query import check

__all__ = ["Baseline", "Change", "Changes", "build_delta", "changes_markdown", "check", "compare", "load_baseline",
           "runs_under", "write_changes"]
