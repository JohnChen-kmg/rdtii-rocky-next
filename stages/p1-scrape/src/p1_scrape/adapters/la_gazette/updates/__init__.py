"""The update check for Lao PDR: what the Lao Official Gazette published, revised or superseded since the last
run.

The comparison is in `diff.py`, the delta list and `changes.md` in `delta.py`, the reading in `query.py`, the CLI
in `__main__.py`. `WORKFLOW.md` beside this file is the procedure.

This portal states a **status word on every row**, so this check can say `status_changed` where Timor-Leste's and
Australia's can only say "new". It is also the dearest check in the workshop, because the gazette pages ten rows
at a time and ignores `Document_pageSize`: a full check is about 190 requests, and `--pages` buys a shallow one
for about 25.
"""
from __future__ import annotations

from .baseline import Baseline, load as load_baseline, runs_under
from .delta import build_delta, changes_markdown, write_changes
from .diff import Change, Changes, compare
from .query import check

__all__ = ["Baseline", "Change", "Changes", "build_delta", "changes_markdown", "check", "compare",
           "load_baseline", "runs_under", "write_changes"]
