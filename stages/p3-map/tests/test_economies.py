"""The economy table, and the rule that decides which retrieval legs a run needs.

Round 1 kept a three-economy tuple in four places. Three were fixed; the fourth was `main.py` at
the repo root, which is the entry point a reviewer and the live test actually use, and which no
test reached. These tests cover the shared table and close that gap.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from config.economies import (ALIASES, ECON_NAME, PRIMARY_LANGUAGE, economies_needing_dense,
                              language, official_name, resolve, sparse_leg_adequate)

STAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = STAGE_ROOT.parents[1]
MAIN_PY = REPO_ROOT / "main.py"

# The six economies a corpus was built for on 27 September, and whether the sparse leg reads them.
MEASURED = {"AU": True, "SG": True, "MY": True, "CN": False, "LA": False, "TL": False}


def test_every_name_is_a_coverage_matrix_string():
    """Column A is counted by COUNTIFS against these exact strings, so none may drift."""
    assert ECON_NAME["LA"] == "Lao PDR", "the matrix row, not the UN prose form"
    assert ECON_NAME["VN"] == "Viet Nam", "two words, as the matrix writes it"
    assert ECON_NAME["RU"] == "Russian Federation"
    for code, name in ECON_NAME.items():
        assert re.fullmatch(r"[A-Z]{2}", code), code
        assert name == name.strip() and name, code


@pytest.mark.parametrize("raw,want", [
    ("China", "CN"), ("CN", "CN"), ("cn", "CN"), ("  china  ", "CN"), ("PRC", "CN"),
    ("Lao PDR", "LA"), ("Laos", "LA"), ("LA", "LA"), ("lao", "LA"),
    ("Timor-Leste", "TL"), ("East Timor", "TL"), ("TL", "TL"),
    ("Viet Nam", "VN"), ("Vietnam", "VN"),
    ("Russia", "RU"), ("Russian Federation", "RU"),
    ("Singapore", "SG"), ("sgp", "SG"),
])
def test_resolve_accepts_the_spellings_people_use(raw, want):
    assert resolve(raw) == want


@pytest.mark.parametrize("raw", ["", None, "Narnia", "XX", "Republic of Nowhere"])
def test_resolve_never_guesses(raw):
    """A wrong code files rows under the wrong economy, so an unknown one must come back None."""
    assert resolve(raw) is None


def test_official_name_passes_an_unknown_code_through():
    assert official_name("China") == "China"
    assert official_name("cn") == "China"
    assert official_name("ZZ") == "ZZ", "never invent a name for a code we do not know"


def test_no_alias_points_at_an_economy_we_cannot_name():
    """An alias resolving to a code with no Coverage Matrix string would file an uncounted row."""
    for alias, code in ALIASES.items():
        assert code in ECON_NAME, f"{alias!r} -> {code!r}, which has no name"
        assert alias == alias.lower(), f"{alias!r} would never match a lowercased lookup"


def test_every_economy_has_a_language():
    assert set(PRIMARY_LANGUAGE) == set(ECON_NAME), "a run must be able to say what it is reading"
    for code, lang in PRIMARY_LANGUAGE.items():
        assert re.fullmatch(r"[a-z]{3}", lang), code


@pytest.mark.parametrize("econ,adequate", sorted(MEASURED.items()))
def test_sparse_leg_matches_what_was_measured(econ, adequate):
    """Measured on the 27 September index: zero rows for CN and LA, 4.4% for TL.

    Timor-Leste is the one that stops this being a script test: Portuguese is Latin-script and the
    sparse leg still could not read it, because the queries are English.
    """
    assert sparse_leg_adequate(econ) is adequate


def test_an_unknown_economy_is_not_assumed_to_be_easy():
    """False, not True: a run that cannot name its language must not take the shortcut."""
    assert sparse_leg_adequate("Narnia") is False
    assert sparse_leg_adequate(None) is False
    assert language("Narnia") is None


def test_economies_needing_dense_preserves_order_and_finds_the_blind_ones():
    assert economies_needing_dense(["AU", "SG", "MY"]) == []
    assert economies_needing_dense(["AU", "CN", "SG", "LA"]) == ["CN", "LA"]
    assert economies_needing_dense([]) == []


# --------------------------------------------------------------- the wrapper --

def test_the_wrapper_does_not_keep_its_own_economy_table():
    """`main.py` held the last copy: `--economy China` exited 2 while the stage was ready for it."""
    src = MAIN_PY.read_text(encoding="utf-8")
    assert "from config.economies import" in src, "the wrapper must read the shared table"
    assert not re.search(r'ECON_NAMES\s*=\s*\{', src), "a local economy dict is back in main.py"
    assert not re.search(r'ECON_ALIASES\s*=\s*\{', src), "a local alias dict is back in main.py"


def test_the_wrapper_has_no_legacy_indicator_list():
    """It stubbed the dense leg with "P6-I1_idx" keys while bm25_top.npz keys "6.1_idx"."""
    src = MAIN_PY.read_text(encoding="utf-8")
    assert not re.search(r'INDICATORS\s*=\s*\[\s*"P6-I1"', src), "legacy indicator list in main.py"


def test_the_wrapper_never_stubs_the_dense_leg_for_a_blind_economy():
    """The stub is reachable only where the sparse leg actually retrieves something.

    This is the failure the guard exists to prevent: with the economy table widened and the stub
    left unconditional, a Chinese law handed to `--docs` would retrieve nothing and report success.
    """
    src = MAIN_PY.read_text(encoding="utf-8")
    assert "economies_needing_dense" in src, "the leg decision must consult the shared rule"
    fn = src[src.index("def _retrieval_legs"):]
    guard = fn.index("if not blind:")
    stub = fn.index("_stub_dense_leg(index_dir)")
    both = fn.index('"--leg", "both"')
    assert guard < stub < both, (
        "_stub_dense_leg must sit inside the `if not blind` branch, above the both-legs path")


def _load_main():
    """Import the repo-root wrapper. It only defines names and extends sys.path."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("_rdtii_main", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_stub_mirrors_the_sparse_legs_own_keys(tmp_path):
    """A stub keyed differently from the leg it pairs with is a zero contribution for the wrong
    reason. bm25_top.npz keys "6.1_idx" today and "P6-I1_idx" on a Round 1 index; the stub must
    follow whichever it finds instead of carrying its own list.
    """
    np = pytest.importorskip("numpy")
    main = _load_main()
    keys = {"6.1_idx": np.array([3, 1], dtype=np.int32),
            "6.1_score": np.array([0.9, 0.8], dtype=np.float32),
            "12.4.1_idx": np.array([7], dtype=np.int32),
            "12.4.1_score": np.array([0.5], dtype=np.float32)}
    np.savez_compressed(tmp_path / "bm25_top.npz", **keys)

    main._stub_dense_leg(tmp_path)

    with np.load(tmp_path / "dense_top.npz") as dense:
        assert set(dense.keys()) == set(keys), "the stub must mirror the sparse leg's keys exactly"
        for key in keys:
            assert len(dense[key]) == 0, f"{key} must be empty, not merely present"
        assert dense["6.1_idx"].dtype == np.int32
        assert dense["6.1_score"].dtype == np.float32


def test_the_stub_refuses_when_there_is_no_sparse_leg_to_mirror(tmp_path):
    """Writing a stub with no keys at all would make every indicator silently unretrievable."""
    pytest.importorskip("numpy")
    main = _load_main()
    with pytest.raises(RuntimeError, match="does not exist"):
        main._stub_dense_leg(tmp_path)


# ------------------------------------------------------------ the paid stages --

@pytest.mark.parametrize("rel", ["src/p3map/triage/local.py", "src/p3map/triage/haiku.py"])
def test_triage_honours_the_economy_scope(rel):
    """Both passes read the whole gray band and ignored ECONOMIES until 27 September.

    Measured: a run scoped to CN, LA and TL judged all 42,263 pairs instead of the 21,175 in scope,
    half of them for economies whose rows are reused from Round 1. On 15 October the draw is ONE
    economy, so an unscoped triage spends the hour on five nobody asked about.
    """
    src = (STAGE_ROOT / rel).read_text(encoding="utf-8")
    assert "SETTINGS.economies" in src, f"{rel} does not consult the run scope"
    scope = src.index("SETTINGS.economies")
    load = src.index('"gray_pairs.jsonl"')
    assert scope < load, f"{rel} must know its scope before it reads the gray band"


def test_the_paid_triage_can_be_priced_before_it_is_run():
    """kappa = 0.213 was measured on three English economies, so it is a projection elsewhere.

    Measured with this flag: China keeps 68% of its gray band against kappa's 21.3%, Lao 24% and
    Timor-Leste 23%. That cost $0.98 to learn and it resized the run.
    """
    src = (STAGE_ROOT / "src/p3map/triage/haiku.py").read_text(encoding="utf-8")
    assert "def run_haiku_triage(limit: int = 0)" in src, "S3b must accept a limit"
    assert "--limit" in src, "S3b must expose the limit on the command line"
