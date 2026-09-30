"""Shared config spine (contract §5): every knob comes from .env, nothing hardcoded.

Usage:  from config.settings import SETTINGS
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")


def _p(key: str, default: str) -> Path:
    raw = os.getenv(key, default)
    p = Path(raw)
    return p if p.is_absolute() else (REPO_ROOT / p).resolve()


@dataclass(frozen=True)
class Settings:
    # LLM backends (contract §5.1) — used from S4 on; S0–S3 are $0
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    llm_provider: str = os.getenv("LLM_PROVIDER", "anthropic")
    llm_model: str = os.getenv("LLM_MODEL", "claude-sonnet-5")
    verifier_model: str = os.getenv("VERIFIER_MODEL", "claude-haiku-4-5")
    escalation_model: str = os.getenv("ESCALATION_MODEL", "claude-opus-4-8")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    triage_model: str = os.getenv("TRIAGE_MODEL", "qwen2.5:14b")
    # Ollama's own default context is 2,048 tokens and it truncates from the FRONT of the
    # prompt, which is where the cached codebook prefix sits (~6.5k tokens on the Round 1
    # instrument, ~8k on the finale one). Measured 2026-09-27: left unset, a mapping call
    # read 2,050 of 6,792 tokens, returned schema-valid JSON, and fired three mutually
    # exclusive indicators on one provision.
    ollama_num_ctx: int = int(os.getenv("OLLAMA_NUM_CTX", "16384"))

    # prefilter
    embed_model: str = os.getenv("EMBED_MODEL", "BAAI/bge-m3")
    prefilter_sparse: str = os.getenv("PREFILTER_SPARSE", "bm25s")
    # How deep each leg stores its ranking, per indicator. It was 3 here and read nowhere, while
    # both legs hard-coded 50,000. It matters: measured 2026-09-27, the 50,000th cosine sits ABOVE
    # theta for 7.3 and 7.5, so at that depth the index decided those two cells and no threshold
    # could reach past it. At 150,000 the cut falls below every theta (7.3: 0.538 -> 0.503,
    # 7.5: 0.572 -> 0.527), which is the point: theta should decide, not the index. Costs 3.2%
    # more candidate pairs and 6 MB of arrays. A setting, so 15 October can go deeper without code.
    prefilter_topk: int = int(os.getenv("PREFILTER_TOPK", "150000"))
    # Gray-band floor on the RRF score, caps mode only. 0.0001 is what Round 1 ran (from its
    # .env); the 0.008 that stood here is 80x larger and, measured 2026-09-27 against the
    # reference arm, empties the gray band completely -- an RRF score is 1/(60+rank), so 0.008
    # cuts in around rank 65, inside every direct cap. At 0.0001 caps mode reproduces Round 1
    # exactly: direct 9,750, gray 29,250, all 27 cells, gold recall 37/37.
    prefilter_floor: float = float(os.getenv("PREFILTER_FLOOR", "0.0001"))
    # S2 candidate selection. "scores" is the measured threshold function in config/selection.py;
    # "caps" is Round 1's RRF-and-fixed-cap path, kept so a surprise is one variable from being
    # reverted. SELECTION_CONFIG points at an alternative parameter file, which is how a
    # threshold moves on 15 October without editing a tracked file.
    select_mode: str = os.getenv("SELECT_MODE", "scores")
    selection_config: str = os.getenv("SELECTION_CONFIG", "")
    embed_batch: int = int(os.getenv("EMBED_BATCH", "128"))
    embed_device: str = os.getenv("EMBED_DEVICE", "cuda")

    # seams
    handoff2_dir: Path = field(default_factory=lambda: _p("HANDOFF2_DIR", "../handoff2"))
    manifest_path: Path = field(default_factory=lambda: _p("MANIFEST_PATH", "../rdtii-p1-scrape/handoff1_v2/manifest.csv"))
    instrument_dir: Path = field(default_factory=lambda: _p("INSTRUMENT_DIR", "contracts/instrument"))
    baseline_path: str = os.getenv("BASELINE_PATH", "reference/Round1_Baseline_Database.xlsx")
    # The 2025 collection. AU/MY/SG have baseline rows only in the Round 1 book, CN/LA only in
    # this one, and Timor-Leste in neither. Both are read; a missing file is skipped with a line.
    baseline_r2_path: str = os.getenv(
        "BASELINE_R2_PATH",
        "reference/rdtii_official/ESCAP-RDTII-2.1_ Round 2 Database.xlsx")

    # output + guardrails
    out_dir: Path = field(default_factory=lambda: _p("OUT_DIR", "out"))
    index_dir: Path = field(default_factory=lambda: _p("INDEX_DIR", "data/index"))
    max_cost_usd_per_doc: float = float(os.getenv("MAX_COST_USD_PER_DOC", "0.25"))
    cost_hard_stop: float = float(os.getenv("COST_HARD_STOP", "400"))
    # The corpus the finale hands over is 0.3.0. ingest only checks startswith("0."), so a
    # stale value here never failed anything -- it just reported the wrong contract.
    contract_version: str = os.getenv("CONTRACT_VERSION", "0.3.0")
    # Contract gates at S0: a sampled record that fails provision.schema.json, an ungrounded
    # snippet, or a validator that will not load, each stop the run. INGEST_GATE=off reports
    # them and continues, which is a plumbing-test setting and not a run setting.
    ingest_gate: bool = os.getenv("INGEST_GATE", "on").strip().lower() not in ("off", "0", "false")
    # Law-name similarity that makes a fire KNOWN. The setting was dead and its default
    # disagreed with the 0.85 newknown.py actually ran in Round 1; 0.85 is kept so behaviour is
    # unchanged, and the knob is now live, because thresholds may move after the code freeze.
    newknown_sim: float = float(os.getenv("NEWKNOWN_SIM", "0.85"))
    exemplar_profile: str = os.getenv("EXEMPLAR_PROFILE", "production")
    # What reaches the CSV. These four were constants in output/submission.py, which makes them
    # unchangeable after the 30 September code freeze — and the live test is the run most likely to
    # need them moved. On 15 October the draw is one economy and two indicators, so NEW_CAP = 8 caps
    # the export at roughly 16–20 NEW rows however much the tool finds. Defaults are Round 1's
    # values exactly, so promoting them changes no behaviour.
    new_conf: float = float(os.getenv("NEW_CONF", "0.75"))
    new_cap: int = int(os.getenv("NEW_CAP", "8"))
    new_cap_tail: int = int(os.getenv("NEW_CAP_TAIL", "10"))          # the multi-row cells 7.3, 7.5
    sectoral_max: int = int(os.getenv("SECTORAL_MAX", "3"))           # framework §2.4
    # Thread counts for the three paid stages. Settings, not code, because the 15 October hour is
    # rate-limit-bound rather than compute-bound and this is the only dial that helps.
    triage_workers: int = int(os.getenv("TRIAGE_WORKERS", "12"))
    map_workers: int = int(os.getenv("MAP_WORKERS", "8"))
    verify_workers: int = int(os.getenv("VERIFY_WORKERS", "8"))
    # Optional run scope. Empty means "every economy the corpus holds" — see ECONOMIES below.
    economies: tuple[str, ...] = field(default_factory=lambda: tuple(
        x.strip().upper() for x in os.getenv("ECONOMIES", "").split(",") if x.strip()))


SETTINGS = Settings()

# Docs whose provision segmentation is known-thin: S0 adds source_text chunks
# so S1/S2 candidate discovery cannot miss content that exists only in raw text
# (framework doc §3.4d rule 1; verified by grep 2026-07-15).
SPECIAL_SOURCE_TEXT_DOCS = [
    "my-pdps2015-001",
    "my-pdpgcbpdt2025-001",
    "my-pdpgadpo2025-001",
    "my-pdpgdbn2025-001",
    "sg-agpcspd2024-001",
    "sg-ca2024-001",
    "au-scia2018-001",
]

# The indicators this stage maps, in host order, as decimal text ("6.1", never "P6-I1").
# Read from the vendored instrument rather than written here, so the 30 September instrument
# hand-off is a file swap and not a code change: config/instrument.py normalises either vintage.
# Scope is the automated set — decision M7, pillars 6 and 7.
from config.instrument import load as _load_instrument  # noqa: E402  (needs SETTINGS above)

# INDICATORS_SCOPE widens or narrows the set for one run, the way ECONOMIES does for economies.
# Empty means the instrument's automated set (pillars 6 and 7). It exists for two reasons: the
# 15 October draw may name an indicator outside those pillars, and Timor-Leste is being run against
# the full instrument. A name not in the instrument is refused rather than silently dropped.
_SCOPE = tuple(x.strip() for x in os.getenv("INDICATORS_SCOPE", "").split(",") if x.strip())
_AUTOMATED = _load_instrument().ids
if _SCOPE:
    from config.indicator_ids import normalize as _norm
    _all = set(_load_instrument().blocks)
    _asked = [_norm(x) for x in _SCOPE]
    _bad = [x for x in _asked if x not in _all]
    if _bad:
        raise ValueError(f"INDICATORS_SCOPE names indicators the instrument does not carry: {_bad}")
    INDICATORS: tuple[str, ...] = tuple(_asked)
else:
    INDICATORS: tuple[str, ...] = _AUTOMATED

# Economies are NOT a fixed list any more. The finale runs six and the live test may draw any of
# nine, so a run takes whatever the corpus contains; ECONOMIES restricts it when set, which is how
# the sealed 15 October task is scoped without touching code.
#   ECONOMIES=CN,LA,TL  ->  those three only
#   unset               ->  every economy present in the prefilter corpus
ECONOMIES: tuple[str, ...] = SETTINGS.economies
