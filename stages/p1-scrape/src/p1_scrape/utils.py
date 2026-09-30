"""Small shared helpers: timestamps, hashing, slugs."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone


def utc_now_iso() -> str:
    """ISO-8601 UTC with a trailing Z (manifest access_date format)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_stamp_compact() -> str:
    """Compact UTC stamp for filenames, e.g. 20260710T1032Z."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


#: How long a slug may be before it is capped. The slug becomes a folder name, so an
#: uncapped one overflows Windows' 260-character path limit: Timor-Leste's Portuguese
#: titles run past 250 characters and its first crawl lost 254 files to exactly this.
SLUG_MAX = 80


def _title_hash(name: str) -> str:
    """Eight hex characters of the title, so two capped or unrenderable titles cannot collide."""
    return hashlib.sha256(name.strip().encode("utf-8")).hexdigest()[:8]


def slugify(name: str) -> str:
    """Deterministic law slug: lowercase, alphanumerics + single underscores.

    Two guards, neither of which changes anything for a Latin title that fits:
    over SLUG_MAX characters the slug is capped and the title's hash appended; a
    title with no Latin alphanumerics at all — Lao, Chinese, Russian — falls back
    to that hash instead of the shared literal "unknown", which would otherwise
    put every law in such an economy in a single folder.
    """
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    if not s:
        return f"x_{_title_hash(name)}"
    if len(s) > SLUG_MAX:
        return s[: SLUG_MAX - 9].rstrip("_") + "_" + _title_hash(name)
    return s


def law_slug_compact(name: str) -> str:
    """Compact slug for the doc_id middle segment (no underscores, must match ^[a-z0-9]+$).

    Falls back to the title's hash rather than "unknown", for the same reason as
    slugify: one shared literal would make every law in a non-Latin script look
    like versions of one law.
    """
    s = re.sub(r"[^a-z0-9]+", "", name.strip().lower())
    return s or _title_hash(name)


def host_of(url: str) -> str:
    from urllib.parse import urlparse

    return (urlparse(url).hostname or "").lower()


_SLUG_STOP = {"of", "the", "and", "a", "an", "for", "to", "in", "on", "by", "with"}


def acronym_slug(law_name: str) -> str:
    """Deterministic doc_id slug from a law title, hyphen-free (doc_id middle segment).

    'Personal Data Protection Act 2012' -> 'pdpa2012'; 'Cybersecurity Act 2018' -> 'ca2018'.
    Drops parenthetical act numbers and stopwords; appends the last 4-digit year.

    A title with no Latin letters yields no acronym, so it falls back to the title's
    hash instead of the literal "law". Without that, every Lao law reduced to "law"
    and dedup treated 1,800 unrelated statutes as versions of one, disambiguated only
    by a four-character hash whose first collision was expected mid-crawl. An economy
    whose adapter sets Candidate.law_slug never reaches this path at all.
    """
    name = law_name.strip()
    years = re.findall(r"(?:19|20)\d{2}", name)
    year = years[-1] if years else ""
    core = re.sub(r"\(.*?\)", " ", name)              # drop "(Act 709)" etc.
    core = re.sub(r"(?:19|20)\d{2}", " ", core)       # drop years
    words = re.findall(r"[A-Za-z]+", core.lower())
    letters = "".join(w[0] for w in words if w not in _SLUG_STOP)
    slug = re.sub(r"[^a-z0-9]", "", (letters + year).lower())
    return slug or _title_hash(law_name)


def append_query(url: str, param_eq_value: str) -> str:
    """Append a `key=value` to a URL, choosing ? or & correctly."""
    sep = "&" if ("?" in url) else "?"
    return f"{url}{sep}{param_eq_value}"
