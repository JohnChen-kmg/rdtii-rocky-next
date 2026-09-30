"""Deduplication + stable doc_id assignment (contract §5.3/§5.4).

- URL-level pre-dedup: normalize URLs so the same doc reached two ways is queued once.
- Content-level dedup: sha256 of bytes; a repeat within a run is dropped (no row).
- Stable doc_id via handoff1/.idmap.json keyed by (cc, lawslug) -> ordered version
  registry {content_sha256 -> seq}, so a re-crawl reuses the id and a genuine content
  change allocates the next seq without renumbering.
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .utils import acronym_slug, law_slug_compact, utc_now_iso

# Query params worth keeping when normalizing (meaningful to SSO / legislation.gov.au).
_KEEP_PARAMS = {"provids", "viewtype", "wholedoc"}


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    host = parts.netloc.lower()
    kept = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if k.lower() in _KEEP_PARAMS]
    query = urlencode(sorted(kept))
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), host, path, query, ""))


class Dedup:
    def __init__(self, handoff_dir: Path):
        self.idmap_path = Path(handoff_dir) / ".idmap.json"
        self.idmap: dict[str, dict] = {}
        if self.idmap_path.exists():
            try:
                self.idmap = json.loads(self.idmap_path.read_text(encoding="utf-8"))
            except Exception:
                self.idmap = {}
        self._seen_urls: set[str] = set()
        self._seen_sha: set[str] = set()
        # (key, seq) created during THIS run — so a 2nd form factor of the same law
        # in one run is not mislabelled as "superseding" the 1st.
        self._run_created: set[tuple[str, int]] = set()

    # --- URL-level ---------------------------------------------------------
    def url_is_new(self, url: str) -> bool:
        key = normalize_url(url)
        if key in self._seen_urls:
            return False
        self._seen_urls.add(key)
        return True

    # --- Content-level -----------------------------------------------------
    def content_is_new(self, sha: str) -> bool:
        if sha in self._seen_sha:
            return False
        self._seen_sha.add(sha)
        return True

    # --- Stable doc_id -----------------------------------------------------
    def _slug_key(self, economy: str, law_name: str, slug: str | None = None) -> tuple[str, str]:
        """(cc, slug) for the id map.

        When the adapter supplied a slug — Candidate.law_slug, which has existed since
        v0.2.0 and which nothing read until Lao PDR needed it — that is used, compacted,
        in place of an acronym built from the title. An acronym is the right key for a
        Latin title and the wrong one for a portal id: acronym_slug("la-2537") is "l".
        An economy whose adapter sets no slug takes the original path unchanged.
        """
        cc = economy.lower()
        slug = law_slug_compact(slug) if slug else acronym_slug(law_name)
        key = f"{cc}::{slug}"
        entry = self.idmap.get(key)
        # Collision guard: same slug, different law -> disambiguate with a short hash.
        if entry is not None and entry.get("law_name") not in (None, law_name):
            import hashlib
            h = hashlib.sha256(law_name.encode()).hexdigest()[:4]
            slug = f"{slug}{h}"
            key = f"{cc}::{slug}"
        return cc, slug

    def is_retrieved(self, economy: str, law_name: str, slug: str | None = None) -> bool:
        """True if this (economy, law) already has a stored version (for resumable crawls)."""
        cc, slug = self._slug_key(economy, law_name, slug)
        entry = self.idmap.get(f"{cc}::{slug}")
        return bool(entry and entry.get("versions"))

    def stable_id(self, economy: str, law_name: str, sha: str,
                  slug: str | None = None) -> tuple[str, str | None]:
        """Return (doc_id, supersedes_note). Reuse seq for a known sha; else next seq."""
        cc, slug = self._slug_key(economy, law_name, slug)
        key = f"{cc}::{slug}"
        entry = self.idmap.setdefault(
            key, {"law_name": law_name, "current_seq": 0, "versions": []}
        )
        for v in entry["versions"]:
            if v["content_sha256"] == sha:
                return f"{cc}-{slug}-{v['seq']:03d}", None
        seq = entry["current_seq"] + 1
        entry["current_seq"] = seq
        prior_current = [v for v in entry["versions"] if v.get("current")]
        for v in entry["versions"]:
            v["current"] = False
        entry["versions"].append({
            "seq": seq, "content_sha256": sha,
            "first_seen": utc_now_iso(), "current": True,
        })
        # Genuine supersession only if the prior current came from a PRIOR run
        # (not just a second form factor retrieved earlier in this same run).
        supersedes = None
        if prior_current:
            pc_seq = prior_current[-1]["seq"]
            if (key, pc_seq) not in self._run_created:
                supersedes = f"{cc}-{slug}-{pc_seq:03d}"
        self._run_created.add((key, seq))
        return f"{cc}-{slug}-{seq:03d}", supersedes

    def save(self) -> None:
        self.idmap_path.parent.mkdir(parents=True, exist_ok=True)
        self.idmap_path.write_text(
            json.dumps(self.idmap, ensure_ascii=False, indent=2), encoding="utf-8"
        )
