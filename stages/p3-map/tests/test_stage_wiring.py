"""Migration guards: every module imports, and every indicator-keyed table is decimal.

Run from stages/p3-map:
    python -m pytest tests/test_stage_wiring.py -q

Round 1's nine indicator IDs were written into eleven files by hand. After the decimal
migration a stale key does not raise: `select.py` would cap a cell it cannot find, triage would
screen with no definition and default to KEEP, `submission.py` would file a no-provision row
with a vaguer reason. These tests are cheap and catch exactly that class of silence.
"""
from __future__ import annotations

import importlib
import pathlib
import re

import pytest

from config.settings import INDICATORS

LEGACY = re.compile(r"P[67]-I[0-9]")
STAGE_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _modules() -> list[str]:
    out = []
    for p in sorted((STAGE_ROOT / "src" / "p3map").rglob("*.py")) + \
             sorted((STAGE_ROOT / "config").rglob("*.py")):
        if "__pycache__" in p.parts or p.name == "__init__.py":
            continue
        rel = str(p.relative_to(STAGE_ROOT).with_suffix(""))
        out.append(rel.replace("\\", ".").replace("/", "."))
    return out


@pytest.mark.parametrize("mod", _modules())
def test_module_imports(mod):
    """A stage module must import with no API key, no network and no run directory."""
    importlib.import_module(mod)


def test_indicators_are_decimal_text():
    assert INDICATORS
    for iid in INDICATORS:
        assert not LEGACY.match(iid), iid
        assert re.match(r"^\d{1,2}\.\d{1,2}(?:\.\d{1,2})?$", iid), iid


def test_per_cell_caps_cover_every_indicator():
    """A missing cap is a KeyError mid-run, after the expensive legs have finished."""
    from src.p3map.select import CAPS
    assert set(CAPS) == set(INDICATORS)


def test_the_scored_selection_config_covers_every_indicator():
    """Guards the block-E swap: selection.json must be complete before it replaces CAPS."""
    from config.selection import indicators
    assert set(indicators()) >= set(INDICATORS)


def test_no_provision_reasons_are_keyed_decimally():
    from src.p3map.output.submission import _NP_REASON
    assert set(_NP_REASON) <= set(INDICATORS)
    assert set(_NP_REASON), "every filed no-provision row carries a reason"


def test_economy_level_rollup_prompt_is_keyed_decimally():
    from src.p3map.rollup import WHAT
    assert set(WHAT) <= set(INDICATORS)
    from config.instrument import load
    ins = load()
    assert set(WHAT) == {i for i in INDICATORS if ins.level(i) == "economy"}


def test_excel_mechanism_notes_are_keyed_decimally():
    from src.p3map.output.excel_export import _MECHANISM
    assert set(_MECHANISM) <= set(INDICATORS)


def test_fire_columns_match_the_excel_fire_row():
    """The empty-workbook column list must stay in step with the dict the exporter builds."""
    from src.p3map.output.excel_export import FIRE_COLUMNS
    src = (STAGE_ROOT / "src" / "p3map" / "output" / "excel_export.py").read_text(encoding="utf-8")
    # anchored on the closing brace at its own indentation: the body itself contains "})"
    # inside `(vv.get("verifier") or {}).get(...)`
    body = re.search(r"fires\.append\(\{(.*?)^\s*\}\)", src, re.S | re.M).group(1)
    keys = re.findall(r'"([A-Z][^"]*)":', body)
    assert keys == FIRE_COLUMNS


def test_submission_columns_are_the_host_sheet_order():
    from src.p3map.output.submission import COLUMNS
    assert COLUMNS[0] == "Economy" and COLUMNS[4] == "Indicator ID"
    assert len(COLUMNS) == len(set(COLUMNS))


def test_economies_are_not_hard_coded():
    """A fixed economy tuple is how a China or Lao run reports success having read nothing."""
    for rel in ("src/p3map/select.py", "src/p3map/output/urlcheck.py"):
        src = (STAGE_ROOT / rel).read_text(encoding="utf-8")
        assert not re.search(r'=\s*\(\s*"SG"\s*,\s*"MY"\s*,\s*"AU"\s*\)', src), rel


def test_the_emit_caps_are_settings_at_round_one_values():
    """Promoting a constant must not move it.

    NEW_CONF, NEW_CAP, NEW_CAP_TAIL and SECTORAL_MAX were constants in submission.py, on the wrong
    side of the code freeze: the live test is the run most likely to need them moved. They are
    settings now, and their defaults are Round 1's values exactly.
    """
    from config.settings import SETTINGS
    from src.p3map.output import submission

    assert (SETTINGS.new_conf, SETTINGS.new_cap, SETTINGS.new_cap_tail, SETTINGS.sectoral_max) == (
        0.75, 8, 10, 3), "a default moved; Round 1 behaviour is no longer reproducible"
    assert submission.NEW_CONF == SETTINGS.new_conf
    assert submission.NEW_CAP == SETTINGS.new_cap
    assert submission.NEW_CAP_TAIL == SETTINGS.new_cap_tail
    assert submission.SECTORAL_MAX == SETTINGS.sectoral_max


def test_the_paid_stages_read_their_worker_counts_from_settings():
    """The live hour is rate-limit-bound, so these must be settable without touching code."""
    from config.settings import SETTINGS
    from src.p3map.mapping import runner
    from src.p3map.triage import haiku
    from src.p3map.verify import blind

    assert haiku.WORKERS == SETTINGS.triage_workers == 12
    assert runner.WORKERS == SETTINGS.map_workers == 8
    assert blind.WORKERS == SETTINGS.verify_workers == 8


def test_every_setting_the_code_reads_is_documented():
    """A knob nobody documents is a knob nobody sets on 15 October.

    .env.example is the only description of this stage's settings, and after the code freeze a
    setting is the only thing that can still change.
    """
    example = (STAGE_ROOT / ".env.example").read_text(encoding="utf-8")
    declared = set(re.findall(r"^([A-Z][A-Z_0-9]+)=", example, re.M))
    read = set()
    files = (sorted((STAGE_ROOT / "config").rglob("*.py"))
             + sorted((STAGE_ROOT / "src").rglob("*.py")))
    for p in files:
        src = p.read_text(encoding="utf-8")
        read |= set(re.findall(r'os\.getenv\(\s*"([A-Z][A-Z_0-9]+)"', src))
        read |= set(re.findall(r'os\.environ\.get\(\s*"([A-Z][A-Z_0-9]+)"', src))
        read |= set(re.findall(r'_p\(\s*"([A-Z][A-Z_0-9]+)"', src))
        # a module constant that names a variable counts as reading it, e.g.
        # ENGINE_ENV = "RDTII_ENGINE" in config/llm/engines.py
        read |= set(re.findall(r'_ENV\s*=\s*"([A-Z][A-Z_0-9]+)"', src))
    undocumented, unread = sorted(read - declared), sorted(declared - read)
    assert not undocumented, f"read by the code, absent from .env.example: {undocumented}"
    assert not unread, f"documented but read nowhere: {unread}"


# ------------------------------------------------------------------ re-runnability


ENTRY_POINTS = [
    "src.p3map.chain",
    "src.p3map.output.excel_export",
    "src.p3map.output.gloss",
    "src.p3map.output.package",
    "src.p3map.output.submission",
    "src.p3map.output.template",
    "src.p3map.output.urlcheck",
    "src.p3map.verify.audit_view",
    "src.p3map.verify.blind",
    "src.p3map.rollup",
    "src.p3map.discovery.newknown",
    "src.p3map.mapping.runner",
    "src.p3map.mapping.batch_runner",
    "src.p3map.cli",
]


@pytest.mark.parametrize("mod", ENTRY_POINTS)
def test_every_entry_point_has_a_main_block(mod):
    """A stage nobody can invoke is a stage nobody re-runs. Every module the runbook names must be
    executable as `python -m`, which means having an `if __name__ == "__main__"` block."""
    path = STAGE_ROOT / (mod.replace(".", "/") + ".py")
    assert path.exists(), path
    assert '__name__ == "__main__"' in path.read_text(encoding="utf-8"), (
        f"{mod} is in the runbook but cannot be run as a module")


def test_the_chain_can_pass_the_multi_arm_flag_through():
    """Timor-Leste is mapped in two arms. A chain that cannot forward that produces a workbook
    covering one arm which looks entirely normal and is missing 52 indicators."""
    import inspect
    from src.p3map.chain import run_chain
    from src.p3map.output.excel_export import export
    from src.p3map.verify.audit_view import render
    for fn in (run_chain, export, render):
        assert "extra_dirs" in inspect.signature(fn).parameters, fn.__name__


def test_the_chain_offers_the_gloss_and_does_not_force_it():
    """Both review surfaces render machine English. Without S9b those columns are blank, which reads
    as "nothing to translate" rather than "not run" -- so the chain must offer it. It must stay
    opt-in, because it calls a paid model and a chain that spends unasked is worse than a blank
    column."""
    import inspect
    from src.p3map.chain import run_chain
    p = inspect.signature(run_chain).parameters
    assert "gloss" in p
    assert p["gloss"].default is False, "paid work must be opt-in"


def test_the_chain_says_which_steps_it_does_not_run():
    """S9c and S9d are whole-run, not per-economy: they choose across every economy at once. A
    reader who follows the chain and stops has no submission folder, so the chain has to say so."""
    doc = (STAGE_ROOT / "src/p3map/chain.py").read_text(encoding="utf-8")
    for name in ("output.template", "output.package", "output.urlcheck"):
        assert name in doc, f"chain.py should name {name} as a step it does not run"


@pytest.mark.parametrize("mod", ENTRY_POINTS)
def test_every_entry_point_prints_usage(mod):
    """`--help` must print usage, not raise.

    Three of these parsed sys.argv positionally, so `--help` was read as an economy name or a verb
    and produced a traceback -- the first thing someone who was not here types, answered with a
    stack trace. A fourth then failed because a literal `%` in an argparse help string is a format
    specifier, which is the kind of thing only running it finds.
    """
    import subprocess
    import sys as _sys
    r = subprocess.run([_sys.executable, "-X", "utf8", "-m", mod, "--help"],
                       capture_output=True, text=True, cwd=STAGE_ROOT, timeout=120)
    assert r.returncode == 0, f"{mod} --help exited {r.returncode}: {r.stderr[-400:]}"
    assert "usage" in (r.stdout + r.stderr).lower(), f"{mod} --help printed no usage"
