"""The settings contract: every location is an environment variable with a clean-clone default.

Names shared with the stages are reused (HANDOFF1_DIR, HANDOFF2_DIR, OUT_DIR, INDEX_DIR, INSTRUMENT_DIR,
BASELINE_PATH, BASELINE_R2_PATH) so the interface and the pipeline cannot drift apart. Relative paths
resolve against the repository root. See interface/DATA_PATHS.md for the reasoning.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

REPO = Path(__file__).resolve().parents[2]
INTERFACE_DIR = REPO / "interface"
STATIC_DIR = INTERFACE_DIR / "static"
FIXTURES_DIR = INTERFACE_DIR / "fixtures"

DEFAULTS: dict[str, str] = {
    "HANDOFF1_DIR": "demo_data/mini_raw",
    "HANDOFF2_DIR": "outputs/extract/demo",
    "OUT_DIR": "interface/fixtures",
    "RDTII_OUT_DIR_EXTRA": "",
    "INDEX_DIR": "outputs/index/demo",
    "INSTRUMENT_DIR": "stages/p0-instrument/output",
    "BASELINE_PATH": "",
    "BASELINE_R2_PATH": "",
    "RDTII_RUNS_ROOT": "outputs",
    "RDTII_SUBMISSION_DIR": "submission",
    "RDTII_INBOX_DIR": "inbox",
    "RDTII_PYTHON_P1": "",
    "RDTII_PYTHON_P2": "",
    "RDTII_PYTHON_P3": "",
    "RDTII_HOST": "127.0.0.1",
    "RDTII_PORT": "8765",
    "RDTII_REVIEWER": "",
}

# Folders a runs root must never sit inside: the code, the fixtures, the demo corpus, the filed rows.
PROTECTED = ("interface", "stages", "demo_data", "submission", "docs")


def _resolve(raw: str) -> Path:
    p = Path(raw)
    return p if p.is_absolute() else (REPO / p).resolve()


def _split_paths(raw: str) -> tuple[Path, ...]:
    return tuple(_resolve(x.strip()) for x in raw.split(",") if x.strip())


@dataclass(frozen=True)
class Settings:
    handoff1_dir: Path
    handoff2_dir: Path
    out_dir: Path
    out_dir_extra: tuple[Path, ...]
    index_dir: Path
    instrument_dir: Path
    baseline_path: str
    baseline_r2_path: str
    runs_root: Path
    submission_dir: Path
    inbox_dir: Path
    python_p1: str
    python_p2: str
    python_p3: str
    host: str
    port: int
    reviewer: str
    source: dict  # name -> "env" | "default", for the settings panel

    @property
    def stage_dirs(self) -> dict[str, Path]:
        return {"p1": REPO / "stages" / "p1-scrape",
                "p2": REPO / "stages" / "p2-extract",
                "p3": REPO / "stages" / "p3-map"}

    def python_for(self, stage: str) -> str:
        return {"p1": self.python_p1, "p2": self.python_p2, "p3": self.python_p3}[stage] or sys.executable


def load(env: Mapping[str, str] | None = None) -> Settings:
    env = os.environ if env is None else env
    vals: dict[str, str] = {}
    source: dict[str, str] = {}
    for name, default in DEFAULTS.items():
        raw = str(env.get(name, "")).strip()
        vals[name] = raw or default
        source[name] = "env" if raw else "default"
    reviewer = vals["RDTII_REVIEWER"]
    if not reviewer:
        try:
            reviewer = os.getlogin()
        except OSError:
            reviewer = "reviewer"
    return Settings(
        handoff1_dir=_resolve(vals["HANDOFF1_DIR"]),
        handoff2_dir=_resolve(vals["HANDOFF2_DIR"]),
        out_dir=_resolve(vals["OUT_DIR"]),
        out_dir_extra=_split_paths(vals["RDTII_OUT_DIR_EXTRA"]),
        index_dir=_resolve(vals["INDEX_DIR"]),
        instrument_dir=_resolve(vals["INSTRUMENT_DIR"]),
        baseline_path=vals["BASELINE_PATH"],
        baseline_r2_path=vals["BASELINE_R2_PATH"],
        runs_root=_resolve(vals["RDTII_RUNS_ROOT"]),
        submission_dir=_resolve(vals["RDTII_SUBMISSION_DIR"]),
        inbox_dir=_resolve(vals["RDTII_INBOX_DIR"]),
        python_p1=vals["RDTII_PYTHON_P1"],
        python_p2=vals["RDTII_PYTHON_P2"],
        python_p3=vals["RDTII_PYTHON_P3"],
        host=vals["RDTII_HOST"],
        port=int(vals["RDTII_PORT"]),
        reviewer=reviewer,
        source=source,
    )


def check_runs_root(s: Settings) -> None:
    """Refuse a runs root that would let Clear reach the code, the fixtures or the filed rows."""
    root = s.runs_root
    for name in PROTECTED:
        guard = (REPO / name).resolve()
        if root == guard or guard in root.parents:
            raise SystemExit(f"RDTII_RUNS_ROOT={root} sits inside {guard}; choose a folder outside the tree's "
                             f"code, fixtures, demo data and filed rows (default: outputs/)")


def arm_dirs(s: Settings) -> list[Path]:
    """The mapping output directories the interface displays as one run.

    OUT_DIR is the first arm. RDTII_OUT_DIR_EXTRA adds more. When OUT_DIR is a folder named `out`, any
    sibling `out_*` with a submission/ folder is picked up automatically, which is how Timor-Leste's
    second arm (`out_tl52`) travels beside the first.
    """
    arms = [s.out_dir]
    arms += [p for p in s.out_dir_extra if p not in arms]
    if s.out_dir.name == "out" and s.out_dir.parent.is_dir():
        for sib in sorted(s.out_dir.parent.glob("out_*")):
            if (sib / "submission").is_dir() and sib not in arms:
                arms.append(sib)
    return arms


def describe(s: Settings) -> list[dict]:
    rows = []
    shown = {
        "HANDOFF1_DIR": s.handoff1_dir, "HANDOFF2_DIR": s.handoff2_dir, "OUT_DIR": s.out_dir,
        "RDTII_OUT_DIR_EXTRA": ", ".join(str(p) for p in s.out_dir_extra) or "",
        "INDEX_DIR": s.index_dir, "INSTRUMENT_DIR": s.instrument_dir,
        "BASELINE_PATH": s.baseline_path, "BASELINE_R2_PATH": s.baseline_r2_path,
        "RDTII_RUNS_ROOT": s.runs_root, "RDTII_SUBMISSION_DIR": s.submission_dir, "RDTII_INBOX_DIR": s.inbox_dir,
    }
    for name, value in shown.items():
        exists = value.exists() if isinstance(value, Path) else (bool(value) and Path(value).exists())
        rows.append({"name": name, "value": str(value), "exists": exists, "source": s.source.get(name, "default")})
    return rows
