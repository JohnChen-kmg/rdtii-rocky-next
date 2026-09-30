"""Shared configuration for RDTII Project 1 (crawler-relevant keys only).

Every model-/engine-bearing choice is a config VALUE, not a code change (the
modular-backend rubric item). P1 uses only the crawler subset of the shared
config layer; LLM/OCR keys live in Projects 2 & 3.

No third-party dependency for .env loading — a tiny parser keeps the crawler
free of an extra pin.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent

# Browser-compatible AND identifiable: a real Chromium UA with our crawler token +
# contact appended, so an administrator can trace/contact rather than block, while
# still clearing naive user-agent gates.
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 "
    "RDTII-Rocky-Crawler/0.1 (+polite public-law retrieval; contact: jiaxiangchen.kmg@gmail.com)"
)


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader. Real environment variables always win (never overridden)."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def _get(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _get_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, str(default)))
    except (TypeError, ValueError):
        return default


def _get_bool(key: str, default: bool) -> bool:
    val = os.environ.get(key)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _read_contract_version() -> str:
    env = os.environ.get("CONTRACT_VERSION")
    if env:
        return env.strip()
    f = _REPO_ROOT / "CONTRACT_VERSION"
    if f.exists():
        return f.read_text(encoding="utf-8").strip()
    return "0.1.0"


@dataclass(frozen=True)
class Settings:
    contract_version: str
    crawl_engine: str
    scan_char_threshold: int
    request_delay_ms: int
    max_concurrency_per_host: int
    max_candidates_per_economy: int
    crawl_depth_max: int
    respect_robots_for_discovery: bool
    robots_hard_block: bool
    user_agent: str
    fetch_timeout_ms: int
    fetch_retries: int

    @property
    def request_delay_seconds(self) -> float:
        return self.request_delay_ms / 1000.0

    @property
    def fetch_timeout_seconds(self) -> float:
        return self.fetch_timeout_ms / 1000.0


def load_settings(env_path: Path | None = None) -> Settings:
    _load_dotenv(env_path or (_REPO_ROOT / ".env"))
    return Settings(
        contract_version=_read_contract_version(),
        crawl_engine=_get("CRAWL_ENGINE", "playwright"),
        scan_char_threshold=_get_int("SCAN_CHAR_THRESHOLD", 100),
        request_delay_ms=_get_int("REQUEST_DELAY_MS", 3000),
        max_concurrency_per_host=_get_int("MAX_CONCURRENCY_PER_HOST", 1),
        max_candidates_per_economy=_get_int("MAX_CANDIDATES_PER_ECONOMY", 60),
        crawl_depth_max=_get_int("CRAWL_DEPTH_MAX", 2),
        respect_robots_for_discovery=_get_bool("RESPECT_ROBOTS_FOR_DISCOVERY", True),
        robots_hard_block=_get_bool("ROBOTS_HARD_BLOCK", False),
        user_agent=_get("USER_AGENT", DEFAULT_USER_AGENT),
        fetch_timeout_ms=_get_int("FETCH_TIMEOUT_MS", 45000),
        fetch_retries=_get_int("FETCH_RETRIES", 3),
    )
