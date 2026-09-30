"""China's update check: what changed since the last collection, and what the tool cannot see.

    python countries/cn-china/tools/update.py [--fetch] [--npc-new DIR] [--base CN_sources_2026-09-21]

One part per kind of source, because each changes differently:

  layer 1   the national database. Never fetched — its robots.txt forbids automated collection. Given
            --npc-new, compares a newer hand-downloaded export with the baseline, offline: laws added, removed,
            and amended (the same title with a later version date in its file name).
  CAC       re-reads its whole 政策法规 index (six listing requests) and compares it with the baseline:
            documents new, gone, or retitled. A document that is gone may have been repealed or moved; the
            check says so and does not guess which. With --fetch, the new documents are fetched into the
            update folder, never into the baseline (CONVENTIONS rule 4).
  gov.cn    re-reads the documents held and compares their text with the stored copy: changed or unchanged.

Everything else — MIIT and Customs by hand, the deferred sources, publishers not yet collected — is on the
watch list, printed before this check runs and again when it finishes (CONVENTIONS rule 11).

Writes outputs/CN/<base>_to_<today>/ (with _2, _3 if run again the same day):

    changes.md          what changed, in words
    cac_changes.csv     new, gone and retitled CAC documents
    govcn_changes.csv   each gov.cn document, changed or not
    npc_changes.csv     with --npc-new: added, removed, amended laws and regulations
    run_log.jsonl       every request, with its status
    auto/cac/           with --fetch: the new CAC documents

Exit 0 when the check ran, 2 when a source refused us — so a scheduler can tell a quiet week from a broken one.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collect  # noqa: E402
import layer1  # noqa: E402
from polite import HostRefused, PoliteClient  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

CN_OUT = os.path.join(collect.REPO, "outputs", "CN")


def _norm_text(t: str) -> str:
    return re.sub(r"\s+", "", t or "")


def _sha(t: str) -> str:
    return hashlib.sha256(_norm_text(t).encode("utf-8")).hexdigest()[:16]


def update_dir(base: str) -> str:
    stem = os.path.join(CN_OUT, f"{base}_to_{datetime.now().strftime('%Y-%m-%d')}")
    d, n = stem, 1
    while os.path.exists(d):
        n += 1
        d = f"{stem}_{n}"
    os.makedirs(d)
    return d


def _read_csv(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def diff_listing(old: list[dict], new: list[dict]) -> dict:
    """Compare two listings of one index by address."""
    o = {r["url"]: r for r in old if r.get("url")}
    n = {r["url"]: r for r in new if r.get("url")}
    return {
        "new": [n[u] for u in n if u not in o],
        "gone": [o[u] for u in o if u not in n],
        "retitled": [{"url": u, "was": o[u]["title"], "now": n[u]["title"]}
                     for u in n if u in o and collect.clean_title(o[u]["title"]) != collect.clean_title(n[u]["title"])],
    }


def check_cac(client: PoliteClient, base_dir: str) -> tuple[dict, list[dict]]:
    baseline = _read_csv(os.path.join(base_dir, "list.csv"))
    fresh = collect.discover_cac(client)
    return diff_listing(baseline, fresh), fresh


def check_govcn(client: PoliteClient, base_dir: str) -> list[dict]:
    man = os.path.join(base_dir, "manifest.json")
    docs = json.load(open(man, encoding="utf-8"))["documents"] if os.path.exists(man) else []
    out = []
    for d in docs:
        stored = os.path.join(base_dir, "text", d["file"] + ".txt")
        old = open(stored, encoding="utf-8").read() if os.path.exists(stored) else ""
        row = {"title": d["title"], "url": d["url"], "status": "", "was": _sha(old), "now": ""}
        try:
            r = client.get(d["url"])
        except HostRefused as e:
            row["status"] = f"refused: {e}"
            out.append(row)
            continue
        if not r.ok:
            row["status"] = f"HTTP {r.status}"
        else:
            row["now"] = _sha(collect.body_text(r.text()))
            row["status"] = "unchanged" if row["now"] == row["was"] else "CHANGED"
        out.append(row)
        print(f"   {row['status']:<10} {d['title'][:50]}", flush=True)
    return out


def write_rows(path: str, rows: list[dict], fields: list[str]) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", default="CN_sources_2026-09-21", help="the collection this check compares against")
    ap.add_argument("--fetch", action="store_true", help="fetch the new CAC documents into the update folder")
    ap.add_argument("--npc-new", metavar="DIR", help="a newer hand-downloaded export of the national database")
    a = ap.parse_args()

    collect.watchlist_reminder("before this update check")
    base = os.path.join(CN_OUT, a.base)
    out = update_dir(a.base)
    client = PoliteClient()
    refused = False
    lines = [f"# China update check: {a.base} to {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]

    # ---- layer 1 ---------------------------------------------------------------------------
    print("\n[layer 1] national database", flush=True)
    base_raw = os.path.join(base, "manual", "npc-database", "raw")
    if a.npc_new:
        d = layer1.diff(layer1.index(base_raw), layer1.index(a.npc_new))
        rows = ([{"change": "added", "title": r["title"], "was": "", "now": r["version_date"]} for r in d["added"]]
                + [{"change": "removed", "title": r["title"], "was": r["version_date"], "now": ""} for r in d["removed"]]
                + [{"change": "amended", **r} for r in d["amended"]]
                + [{"change": "earlier date", **r} for r in d["earlier"]])
        write_rows(os.path.join(out, "npc_changes.csv"), rows, ["change", "title", "was", "now"])
        summary = ", ".join(f"{len(d[k])} {k}" for k in ("added", "removed", "amended"))
        print(f"   {summary}", flush=True)
        lines += ["## Layer 1 — the national database", "", f"Compared `{a.npc_new}` with the baseline: **{summary}**.",
                  "Details in `npc_changes.csv`.", ""]
    else:
        print("   not compared: download a fresh export by hand and pass it with --npc-new", flush=True)
        lines += ["## Layer 1 — the national database", "",
                  "**Not compared.** Its robots.txt forbids automated collection, so a fresh export has to be downloaded "
                  "by hand and passed with `--npc-new`. This is the most important part of any update.", ""]

    # ---- CAC -------------------------------------------------------------------------------
    print("\n[CAC] 政策法规 index", flush=True)
    cac_base = collect.folder_dir("cac")
    try:
        cd, fresh = check_cac(client, cac_base)
    except HostRefused as e:
        refused = True
        cd, fresh = {"new": [], "gone": [], "retitled": []}, []
        print(f"   REFUSED: {e}", flush=True)
        lines += ["## CAC", "", f"**Refused:** {e}", ""]
    else:
        rows = ([{"change": "new", **r} for r in cd["new"]] + [{"change": "gone", **r} for r in cd["gone"]]
                + [{"change": "retitled", "title": r["now"], "was_title": r["was"], "url": r["url"]} for r in cd["retitled"]])
        write_rows(os.path.join(out, "cac_changes.csv"), rows, ["change", "title", "was_title", "date", "section", "url"])
        print(f"   {len(fresh)} listed now; {len(cd['new'])} new, {len(cd['gone'])} gone, {len(cd['retitled'])} retitled", flush=True)
        lines += ["## CAC", "", f"{len(fresh)} documents listed now. **{len(cd['new'])} new, {len(cd['gone'])} gone, "
                  f"{len(cd['retitled'])} retitled.**", ""]
        lines += [f"- new: {r['date']} {r['title']}" for r in cd["new"]]
        lines += [f"- gone (repealed or moved; check which): {r.get('date', '')} {r['title']}" for r in cd["gone"]]
        lines += [""]
        if a.fetch and cd["new"]:
            res = collect.fetch_all(client, "cac", cd["new"], None, dest=os.path.join(out, "auto", "cac"))
            lines += [f"Fetched into `auto/cac/`: {res}", ""]

    # ---- gov.cn ----------------------------------------------------------------------------
    print("\n[gov.cn] documents held", flush=True)
    g = check_govcn(client, collect.folder_dir("govcn"))
    write_rows(os.path.join(out, "govcn_changes.csv"), g, ["status", "title", "was", "now", "url"])
    changed = [r for r in g if r["status"] == "CHANGED"]
    bad = [r for r in g if r["status"] not in ("CHANGED", "unchanged")]
    refused = refused or any(r["status"].startswith("refused") for r in g)
    lines += ["## gov.cn", "", f"{len(g)} documents re-read: **{len(changed)} changed**, {len(bad)} could not be read.", ""]
    lines += [f"- changed: {r['title']}" for r in changed] + [f"- not read ({r['status']}): {r['title']}" for r in bad] + [""]

    # ---- the rest --------------------------------------------------------------------------
    lines += ["## Not seen by this check", "",
              "MIIT and Customs (by hand), every deferred source, and the publishers not yet collected. They are on "
              "the watch list, printed before and after this check; `../CN_sources_2026-09-21/CHECK_BY_HAND.md` has "
              "it as a table. **This check is not a complete update until those have been looked at.**", ""]
    open(os.path.join(out, "changes.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    with open(os.path.join(out, "run_log.jsonl"), "w", encoding="utf-8") as f:
        for ev in client.log:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        for k, h in client.hosts.items():
            f.write(json.dumps({"event": "robots-verdict", "host": k, "verdict": h.verdict}, ensure_ascii=False) + "\n")

    print(f"\nwritten: {out}", flush=True)

    # Rule 13: the hand-collected sources cannot be checked by any tool, so say how many documents this
    # check did not cover, and rebuild the worklist that says where each of them lives.
    try:
        import manual_check

        path = os.path.join(manual_check.collection_dir(a.base), "MANUAL_UPDATE_CHECK.md")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(manual_check.build(a.base))
        n_docs = sum(len(manual_check.held(manual_check.read_provenance(p)))
                     for _, p in manual_check.manual_sources(a.base))
        print(f"\n!! {n_docs} documents in this collection were collected by hand and CANNOT be checked by this "
              f"tool.\n!! Their hosts refuse us, so only a person can see a change. The worklist, with the exact "
              f"address\n!! of every one of them, has been rebuilt at:\n!!   {path}", flush=True)
    except Exception as exc:  # a reporting extra must never fail an update check
        print(f"\n!! could not rebuild the by-hand worklist: {exc}", flush=True)

    collect.watchlist_reminder("after this update check")
    return 2 if refused else 0


if __name__ == "__main__":
    raise SystemExit(main())
