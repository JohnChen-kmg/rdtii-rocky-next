"""A line the person writes at Start and the run carries with it.

It is kept in the run's own folder as `run_note.txt`, one line per run (a second pass into the same folder
adds a line), so it travels with the folder: Output shows it, and so does the next stage's Input when that
folder is chosen there. The stages never read it.

Standard library only.
"""
from __future__ import annotations

import time
from pathlib import Path

NOTE_FILE = "run_note.txt"
MAX_CHARS = 300


def clean(raw) -> str:
    """One line, trimmed, at most MAX_CHARS characters; anything else typed is folded into spaces."""
    return " ".join(str(raw or "").split())[:MAX_CHARS].strip()


def write(folder: Path, note: str) -> bool:
    """Add the note to the folder's file. False when there is nothing to write or no folder to write into."""
    note = clean(note)
    if not note or not folder.is_dir():
        return False
    stamp = time.strftime("%Y-%m-%d %H:%M")
    with (folder / NOTE_FILE).open("a", encoding="utf-8", newline="\n") as f:
        f.write(f"{stamp}\t{note}\n")
    return True


def read(folder: Path) -> dict:
    """The latest note of a run folder: {"note": text, "noted": when}. Both empty when there is none."""
    f = folder / NOTE_FILE
    try:
        lines = [x for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]
    except OSError:
        return {"note": "", "noted": ""}
    if not lines:
        return {"note": "", "noted": ""}
    when, sep, text = lines[-1].partition("\t")
    return {"note": clean(text if sep else when), "noted": when if sep else ""}


def carry(steps: list, folder: Path, note: str) -> None:
    """Have the run write its note into its folder as soon as the folder exists.

    A stage creates its own output folder, sometimes only part of the way through, and a run can be stopped
    before its last step. So every step's finish tries once; the first that finds the folder writes the line.
    """
    note = clean(note)
    if not note:
        return
    state = {"written": False}

    def after(previous):
        def hook(job, rc):
            if previous is not None:
                previous(job, rc)
            if not state["written"] and write(folder, note):
                state["written"] = True
        return hook

    for step in steps:
        step.on_done = after(step.on_done)
