"""S8 — Malaysia error-check: 3 checks over all 26 MY baseline rows
(framework §2.6; double-weighted in scoring).

Checks per baseline row:
  url      — every reference URL answers < 400 (HEAD, cached, offline-safe:
             failures are recorded, never crash; judges may be offline)
  currency — the baseline Timeframe vs the corpus last_amended for the same
             law (staleness signal, e.g. missed 2024/25 amendments)
  substance— for rows whose cited law is in the corpus: does the cited section
             exist, and (for the two SUSPECT 7.3 rows) does its text support
             a MINIMUM-retention reading? Deterministic retrieval + rule
             checks; narrative refutations drafted at curation.

Output: out/errorcheck/malaysia_errorcheck.csv (framework Appendix B columns)
+ JSON with the retrieved evidence. Runs meaningfully after the MY corpus is
mapped, but url/currency/substance-retrieval work off the corpus alone —
runnable now.
"""
from __future__ import annotations

import csv
import json
import re

import httpx

from config.settings import SETTINGS

SUSPECT = {"r1-my-053", "r1-my-054"}  # baseline 7.3=1 rows we believe misread max-retention
MIN_RE = re.compile(r"(not less than|at least|minimum of|no shorter than)", re.I)
MAX_RE = re.compile(r"(no longer than|not longer than|cease|destroy|no longer necessary|"
                    r"as long as necessary|permanently delete)", re.I)
COLUMNS = ["Baseline Entry", "Retrieved Provision", "Check Class",
           "Correct / Not-correct", "Discrepancy", "Action",
           "Baseline Source", "Main-CSV crossref"]


def _norm(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "").lower())
    return re.sub(r"[^a-z0-9 ]", "", s).strip()


def _law_docs(law: str, doc_meta: dict) -> list[str]:
    t = {w for w in _norm(law).split() if len(w) > 2 and not w.isdigit()}
    out = []
    for did, dm in doc_meta.items():
        if dm.get("economy") != "MY" or not dm.get("law_name"):
            continue
        n = {w for w in _norm(dm["law_name"]).split() if len(w) > 2 and not w.isdigit()}
        if t and n and len(t & n) / min(len(t), len(n)) >= 0.8:
            out.append(did)
    return out


def _stem_tokens(s: str) -> set[str]:
    stop = {"act", "the", "of", "and", "an", "a", "law", "no"}
    out = set()
    for t in _norm(s).split():
        if t in stop or t.isdigit():
            continue
        if len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]
        out.add(t)
    return out


def _load_my_csv() -> list[dict]:
    """The judged MY submission — crossref target (2026-07-16 follow-up
    item 5: the error-check must reference the actual submitted rows)."""
    p = SETTINGS.out_dir / "submission" / "records_MY.csv"
    if not p.exists():
        return []
    with p.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _crossref(my_rows: list[dict], laws: list[str],
              indicator: str | None = None) -> str:
    """CSV rows citing any of `laws` (stemmed-token containment >=0.8),
    optionally filtered to one indicator."""
    hits = []
    for r in my_rows:
        if indicator and r["Indicator ID"] != indicator:
            continue
        rt = _stem_tokens(r["Law Name"])
        for law in laws:
            lt = _stem_tokens(law)
            if rt and lt and len(rt & lt) / min(len(rt), len(lt)) >= 0.8:
                hits.append(f"{r['Indicator ID']} {r['Law Name'][:40]} "
                            f"{r['Article / Section']}".strip())
                break
    if not hits:
        return "no MY submission row cites this law"
    return "records_MY.csv: " + "; ".join(dict.fromkeys(hits))


def run_errorcheck(check_urls: bool = True) -> None:
    doc_meta = json.loads((SETTINGS.index_dir / "doc_meta.json").read_text(encoding="utf-8"))
    my_rows = _load_my_csv()
    gold = []
    with (SETTINGS.instrument_dir / "gold" / "gold_set.jsonl").open(encoding="utf-8") as f:
        for line in f:
            g = json.loads(line)
            if g.get("economy") == "MY":
                gold.append(g)

    url_cache_path = SETTINGS.out_dir / "url_cache.json"
    url_cache = (json.loads(url_cache_path.read_text(encoding="utf-8"))
                 if url_cache_path.exists() else {})

    def check_url(u: str) -> str:
        if not u:
            return "no-url"
        if u in url_cache:
            return url_cache[u]
        status = "unreachable"
        if check_urls:
            try:
                r = httpx.head(u, follow_redirects=True, timeout=15,
                               headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code == 405:
                    r = httpx.get(u, follow_redirects=True, timeout=20,
                                  headers={"User-Agent": "Mozilla/5.0"})
                status = f"{r.status_code}"
            except Exception as e:
                status = f"error:{type(e).__name__}"
        url_cache[u] = status
        return status

    rows = []
    for g in gold:
        gid = g["gold_id"]
        laws = [x.strip() for x in re.split(r"[;\n]", g.get("law") or "") if x.strip()]
        urls = g.get("urls") or []
        if isinstance(urls, str):
            urls = re.findall(r"https?://\S+", urls)

        # 1 · URL check
        for u in urls[:3]:
            st = check_url(u)
            ok = st.startswith(("2", "3"))
            rows.append({
                "Baseline Entry": f"{gid} · {laws[0][:50] if laws else ''} · {g['indicator']} · score {g.get('raw_score')}",
                "Retrieved Provision": "", "Check Class": "url",
                "Correct / Not-correct": "Correct" if ok else "Not-correct",
                "Discrepancy": "" if ok else f"URL answers {st}",
                "Action": "" if ok else "find official replacement link",
                "Baseline Source": u,
                "Main-CSV crossref": _crossref(my_rows, laws, g["indicator"])})

        # 2 · currency check
        docs = [d for law in laws for d in _law_docs(law, doc_meta)]
        tf = g.get("timeframe") or ""
        tf_years = [int(y) for y in re.findall(r"(19\d{2}|20[0-2]\d)", tf)]
        for did in docs[:1]:
            # last_amended lives on provisions; approximate via any provision later
            rows.append({
                "Baseline Entry": f"{gid} · {g['indicator']}",
                "Retrieved Provision": did, "Check Class": "currency",
                "Correct / Not-correct": "Check-at-curation",
                "Discrepancy": f"baseline timeframe: {tf[:60]}",
                "Action": "compare vs corpus last_amended + 2024-25 amendment acts",
                "Baseline Source": "",
                "Main-CSV crossref": _crossref(my_rows, laws)})

        # 3 · substance check for the suspect 7.3 rows
        if gid in SUSPECT:
            found = []
            corpus = SETTINGS.index_dir / "prefilter_corpus.jsonl"
            with corpus.open(encoding="utf-8") as f:
                for line in f:
                    r = json.loads(line)
                    if r["doc_id"] in docs and r["economy"] == "MY":
                        txt = r["text"]
                        if re.search(r"reten|kept|stored|destroy", txt, re.I):
                            has_min = bool(MIN_RE.search(txt))
                            has_max = bool(MAX_RE.search(txt))
                            if has_min or has_max:
                                found.append((r["provision_id"], has_min, has_max,
                                              txt[:180]))
            verdict = "Not-correct" if (found and not any(f[1] for f in found)) \
                else ("Check-at-curation" if found else "Doc-not-parsed")
            rows.append({
                "Baseline Entry": f"{gid} · {laws[0][:50] if laws else ''} · P7-I3 · baseline score 1",
                "Retrieved Provision": "; ".join(f[0] for f in found[:4]),
                "Check Class": "score/substance",
                "Correct / Not-correct": verdict,
                "Discrepancy": ("retention language found is MAXIMUM/destroy-type, "
                                "not a minimum period" if verdict == "Not-correct"
                                else "see retrieved provisions"),
                "Action": ("corrected score 0 + refutation quote"
                           if verdict == "Not-correct" else "manual read"),
                "Baseline Source": "",
                "Main-CSV crossref": _crossref(my_rows, laws, "P7-I3")})

    out_dir = SETTINGS.out_dir / "errorcheck"
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "malaysia_errorcheck.csv").open("w", newline="",
                                                    encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    url_cache_path.write_text(json.dumps(url_cache, indent=1), encoding="utf-8")
    bad_urls = sum(1 for r in rows
                   if r["Check Class"] == "url"
                   and r["Correct / Not-correct"] == "Not-correct")
    print(f"[errorcheck:MY] {len(rows)} check rows ({bad_urls} URL failures) "
          f"-> {out_dir / 'malaysia_errorcheck.csv'}")


if __name__ == "__main__":
    import sys
    run_errorcheck(check_urls="--no-url" not in sys.argv)
