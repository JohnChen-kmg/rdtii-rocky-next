"""The delta list: the documents to crawl for what changed, in the link-file format the crawl replays.

Rows are built by the same adapter code the full list uses (MyGazetteAdapter._principal_candidate,
_amendment_candidates, _subsidiary_candidates), with the same timeline and subsidiary policies applied to the
changed acts only, plus rows for new instruments taken from the P.U. listings. Every row carries
contract_meta.update: what changed, why, and the document the baseline stored for the same law.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ....models import Candidate
from ....sources import indicator_pillar, pillar_hint_for
from ..catalogue import _CANDIDATE_FIELDS, _law_rows, _scraper_hashes, candidate_from_row, cfg_fingerprint
from ..parse import _act_key, _law_number, _pu_key, pu_b_refs
from ..records import PrincipalAct
from .baseline import Baseline
from .diff import Change, Changes

_RANK = {"seed": 0, "relevant": 1, "all": 2}


def build_delta(adapter, client, changes: Changes, baseline: Optional[Baseline], since: Optional[str],
                pillars: list[int], subsidiary_meta: Optional[dict] = None,
                refetch: Optional[list[dict]] = None, list_rows: Optional[list[dict]] = None,
                list_meta: Optional[dict] = None) -> dict[str, Any]:
    """Read the changed acts' timelines (as lom.timeline asks), build one candidate per document to fetch, and
    return {documents, laws, meta, discovery_log} for scraper.catalogue.write. `refetch` rows (from --verify-stored)
    are baseline link-list rows whose stored file the portal reports changed; `list_rows` (from --list) are link-list
    rows no run stored (listcheck.py)."""
    cfg = adapter.cfg
    adapter.inventory = adapter._inventory_items()
    adapter._mark_relevance(adapter.inventory)
    adapter._terms = {it.law_number: ",".join(it.matched_terms) for it in adapter.inventory if it.matched_terms}
    relevant_numbers = {it.law_number for it in adapter.inventory if it.relevant}
    requests_before = len(client.log)

    seeds: list[tuple[dict, str, Any]] = []
    for law in cfg.get("seed_laws", []) or []:
        inds = law.get("indicators", []) or []
        if pillars and not any(indicator_pillar(i) in pillars for i in inds):
            continue
        seeds.append((law, *adapter._resolve_seed(law)))
    seed_principal = {obj.act_no: law for law, kind, obj in seeds if kind == "principal"}
    seed_amendment = {obj.a_number: law for law, kind, obj in seeds if kind == "amendment"}
    seed_pu = {_pu_key(law.get("law_number", "")): law for law, _k, _o in seeds
               if _pu_key(law.get("law_number", "")).startswith("PU(")}
    timeline_policy = adapter._timeline_policy()
    subsidiary_policy = adapter._subsidiary_policy()
    wanted_series = {_pu_key(s) for s in adapter._list_setting("subsidiary_series", ["P.U. (A)"])}

    def reads_timeline(p: PrincipalAct) -> bool:
        return (timeline_policy == "all" or (timeline_policy in ("seed", "rule") and p.act_no in seed_principal)
                or (timeline_policy == "rule" and adapter._rule_act(p)))

    def read_amendment_timeline(amd, principal: Optional[PrincipalAct]) -> bool:
        return timeline_policy != "none" and (
            timeline_policy == "all" or amd.a_number in seed_amendment
            or (principal is not None and reads_timeline(principal)))

    def wants_subsidiary(p: Optional[PrincipalAct]) -> bool:
        if p is None:
            return subsidiary_policy == "all"
        return ((subsidiary_policy == "seed" and p.act_no in seed_principal)
                or (subsidiary_policy == "core" and adapter._core_act(p))
                or (subsidiary_policy == "rule" and (p.act_no in seed_principal or adapter._rule_act(p)))
                or subsidiary_policy == "all")

    stored = baseline.stored if baseline else {}
    picked: dict[str, Candidate] = {}

    def add(cand: Optional[Candidate], change: str, reasons: list[str], found_by: Optional[str] = None,
            law_kind: Optional[str] = None) -> Optional[Candidate]:
        if cand is None or not cand.url or cand.url in picked:
            return None
        meta = cand.contract_meta
        meta["update"] = {
            "change": change, "reasons": list(reasons), "since": since,
            "baseline_run": baseline.name if baseline else None,
            "found_by": found_by or meta.get("discovery_path"),
            "previous": (baseline.previous(meta.get("portal_id"), law_kind or meta.get("document_kind"))
                         if baseline else None),
            "stored_before": cand.url in stored,
        }
        meta["discovery_path"] = "delta"
        picked[cand.url] = cand
        return cand

    # --- principal acts that changed: their new file, later amendments and (by policy) subsidiary legislation
    for ch in changes.principals:
        if not ch.crawl:
            continue
        p = adapter.principals.get(_act_key(ch.portal_id))
        if p is None:
            continue
        if reads_timeline(p):
            adapter._load_timeline(p, client)
        later = adapter._later_amendments(p)
        for amd in later:
            if read_amendment_timeline(amd, p):
                adapter._load_amendment_timeline(amd, client)
        law = seed_principal.get(p.act_no)
        cand = adapter._principal_candidate(p, law=law, indicators=(law or {}).get("indicators", []) or [])
        add(cand, ch.change, ch.reasons)
        if cand is None:
            ch.crawl, ch.note = False, "no document to fetch (none listed, or its file is already picked for another act)"
        for amd in later:
            for c in adapter._amendment_candidates(amd, p, client, law=seed_amendment.get(amd.a_number),
                                                   read_timeline=read_amendment_timeline(amd, p)):
                if c.url not in stored:
                    add(c, "amendment_of_changed_act", [f"listed after the as-at date of Act {p.act_no}"])
        listed = [e for e in adapter.timelines.get(p.act_no, [])
                  if e.log_type == "SUBSIDIARY_LEGISLATION" and e.file_url and e.pu_no]
        if listed and wants_subsidiary(p):
            for c in adapter._subsidiary_candidates(p, listed):
                if c.url not in stored:
                    add(c, "subsidiary_of_changed_act", [f"on the timeline of Act {p.act_no}"])

    # --- amending acts that are new or whose commencement changed
    for ch in changes.amendments:
        if not ch.crawl:
            continue
        amd = adapter.amendments.get(ch.portal_id.upper())
        if amd is None:
            continue
        principal = adapter._principal_for(amd)
        if principal is not None and reads_timeline(principal):
            adapter._load_timeline(principal, client)
            principal = adapter._principal_for(amd)            # the timeline's project id may settle the link
        rt = read_amendment_timeline(amd, principal)
        found = 0
        for c in adapter._amendment_candidates(amd, principal, client, law=seed_amendment.get(amd.a_number),
                                               read_timeline=rt):
            if c.url in stored and ch.change == "commencement_changed":
                continue                                        # the act's own file is unchanged
            earlier = picked.get(c.url)
            if earlier is not None:                             # already picked as a changed act's later amendment
                found += 1
                if earlier.contract_meta["update"]["change"] == "amendment_of_changed_act":
                    earlier.contract_meta["update"].update({"change": ch.change, "reasons": list(ch.reasons)})
                continue
            if add(c, ch.change, ch.reasons) is not None:
                found += 1
        if not found:
            ch.crawl, ch.note = False, "nothing new to fetch" + ("; its detail page was read" if rt else "")

    # --- new instruments from the P.U. listings
    cited: dict[str, list[str]] = {}
    for amd in adapter.amendments.values():
        for ref in pu_b_refs(amd):
            cited.setdefault(_pu_key(ref), []).append(f"Act {amd.a_number}")
    for ch in changes.subsidiary:
        parent = adapter.principals.get(_act_key(ch.now.get("act_no") or "")) if ch.now.get("act_no") else None
        key = _pu_key(ch.portal_id)
        commences = cited.get(key, [])
        seed_law = seed_pu.get(key)
        if ch.now.get("kind") == "pub" or key.startswith("PU(B)"):
            # As the full build: an order is fetched for an amending act whose detail page the policy reads.
            citing = [a for a in (adapter.amendments.get(c.split()[-1].upper()) for c in commences) if a is not None]
            in_policy = any(read_amendment_timeline(a, adapter._principal_for(a)) for a in citing)
            wanted = seed_law is not None or (bool(commences) and in_policy)
            kind = "commencement_instrument" if commences else "subsidiary_legislation"
            reason = ("a seed names it" if seed_law else
                      f"commencement order cited by {', '.join(commences)}" if in_policy else
                      (f"cited by {', '.join(commences)}, whose detail page lom.timeline={timeline_policy} does not read"
                       if commences else "a P.U. (B) notice no amending act cites"))
        else:
            in_series = any(key.startswith(w) for w in wanted_series)
            wanted = seed_law is not None or (in_series and wants_subsidiary(parent))
            kind = "subsidiary_legislation"
            reason = ("a seed names it" if seed_law else
                      f"P.U. (A) under {'a core act' if parent and adapter._core_act(parent) else 'Act ' + str(parent.act_no) if parent else 'no listed act'}"
                      if wanted else
                      (f"lom.subsidiary_acts={subsidiary_policy}: not under an act the policy covers"
                       if in_series else "series not in lom.subsidiary_series"))
        ch.crawl = wanted and bool(ch.url)
        ch.note = reason
        if not ch.crawl:
            continue
        cand = listing_candidate(ch, parent, kind, commences, seed_law)
        add(cand, ch.change, ch.reasons + [reason], found_by="subsidiary_list")

    # --- stored files the portal reports changed (--verify-stored)
    for row in refetch or []:
        cand = candidate_from_row(row)
        add(cand, "stored_file_changed", ["the stored URL answered 200 to a conditional request, not 304"],
            found_by=(row.get("contract_meta") or {}).get("discovery_path"))

    # --- documents the link list holds that no run stored (--list, listcheck.py)
    listed_by_url = {ch.url: ch for ch in changes.listed if ch.url}
    for row in list_rows or []:
        earlier = picked.get(row.get("url"))
        if earlier is not None:                     # the listing diff fetches it already (a not_stored act)
            ch = listed_by_url.get(row.get("url"))
            if ch is not None:
                ch.crawl, ch.note = False, f"fetched as {earlier.contract_meta['update']['change']} by the listing diff"
            continue
        cand = candidate_from_row(row)
        add(cand, "not_in_runs", [f"in the link list built {(list_meta or {}).get('generated_at') or 'undated'}, "
                                  f"stored by no run"],
            found_by=(row.get("contract_meta") or {}).get("discovery_path"))

    # --- order and scopes: seeds first, then acts the title rule selects, then the rest
    def scopes_of(c: Candidate) -> list[str]:
        meta = c.contract_meta
        number = meta.get("law_number") or c.law_number_guess or ""
        principal = meta.get("principal_law_number") or ""
        is_seed = (meta.get("update", {}).get("found_by") == "seed" or meta.get("seed_provenance") is not None
                   or number in {_law_number(a) for a in seed_principal} | {f"Act {a}" for a in seed_amendment})
        relevant = is_seed or number in relevant_numbers or principal in relevant_numbers
        return [s for s, on in (("seed", is_seed), ("relevant", relevant), ("all", True)) if on]

    rows = []
    for i, c in enumerate(picked.values()):
        scopes = scopes_of(c)
        rows.append((min(_RANK[s] for s in scopes), i, c, scopes))
    rows.sort(key=lambda t: (t[0], t[1]))
    documents = []
    for order, (_rank, _i, c, scopes) in enumerate(rows, start=1):
        row = {name: getattr(c, name) for name in _CANDIDATE_FIELDS}
        row.update({"order": order, "scopes": scopes, "contract_meta": c.contract_meta})
        documents.append(row)

    laws = _law_rows(adapter, documents)
    by_change = {(_act_key(ch.portal_id) if ch.kind == "principal" else ch.portal_id.upper()): ch
                 for ch in changes.principals + changes.amendments}
    state = baseline.state_run.name if baseline and baseline.state_run else None
    for law in laws:
        if law["not_crawled_reason"] and law["not_crawled_reason"].startswith("not selected"):
            key = _act_key(str(law["portal_id"])) if law["listing"] == "updated" else str(law["portal_id"]).upper()
            ch = by_change.get(key)
            if ch is None:
                law["not_crawled_reason"] = f"unchanged since {state}" if state else "no change found"
            else:
                law["not_crawled_reason"] = f"{ch.change}: {ch.note or ', '.join(ch.reasons)}; nothing fetched"
    counts = {scope: sum(1 for d in documents if scope in d["scopes"]) for scope in ("all", "seed", "relevant")}
    kinds: dict[str, int] = {}
    for d in documents:
        k = d["contract_meta"].get("document_kind") or "agency_or_other"
        kinds[k] = kinds.get(k, 0) + 1
    notes = list(adapter.notes)
    meta = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "economy": "MY", "pillars": pillars, "list_kind": "delta", "counts": counts, "document_kinds": kinds,
        "rule_id": adapter.title_rule.rule_id if adapter.title_rule else None,
        "settings": {**adapter.effective_settings(("timeline", "subsidiary_acts", "subsidiary_series",
                                                    "subsidiary_max_per_act", "document_languages", "root")),
                     "robots_5xx": adapter.lom_cfg.get("robots_5xx"),
                     "updates": {k: v for k, v in (cfg.get("updates") or {}).items()}},
        "cfg_sha256": cfg_fingerprint(cfg),
        "seed_keys": [[law.get("law_name"), law.get("law_number"), law.get("url")]
                      for law in cfg.get("seed_laws") or []],
        "requests": len(client.log), "requests_after_check": len(client.log) - requests_before,
        "robots_record": adapter.robots_record, "lom_error": adapter.lom_error,
        "listing_counts": adapter.listing_counts, "listing_floor": adapter.listing_floor,
        "timelines_read": len(adapter.timelines), "amendment_timelines_read": len(adapter.amendment_timelines),
        "subsidiary_listing": subsidiary_meta or {},
        "delta": {"since": since, "mode": changes.mode,
                  "baseline_runs": [r.name for r in baseline.runs] if baseline else [],
                  "baseline_state_run": state, "baseline_started_at": baseline.started_at if baseline else None,
                  "baseline_stored": len(stored), "changes": changes.summary(),
                  "link_list": list_meta},
        "notes": notes, "scraper_sha256": {**_scraper_hashes(), **_updates_hashes()},
    }
    return {"documents": documents, "laws": laws, "meta": meta, "discovery_log": list(client.log)}


def listing_candidate(ch: Change, parent: Optional[PrincipalAct], kind: str, commences: list[str],
                      seed_law: Optional[dict]) -> Candidate:
    """A row for an instrument the P.U. listing shows as new (the timeline path builds the others)."""
    now = ch.now
    act_no = parent.act_no if parent else now.get("act_no")
    inds = (seed_law or {}).get("indicators", []) or []
    cand = Candidate(
        url=ch.url, economy="MY",
        law_name_guess=(seed_law or {}).get("law_name") or
                       (f"{ch.portal_id} commencing {commences[0]}" if commences and kind == "commencement_instrument"
                        else f"{ch.portal_id} under Act {act_no}" if act_no else ch.portal_id),
        law_number_guess=ch.portal_id, publication_date=now.get("publication_date"),
        pillar_hint=(pillar_hint_for(inds) if inds else None), indicator_hints=(",".join(inds) or None),
        commencement_date=now.get("commencement"))
    cand.contract_meta = {
        "portal": "my-lom", "discovery_path": "seed" if seed_law else "subsidiary_list",
        "seed_provenance": (seed_law or {}).get("provenance"), "project_id": now.get("project_id"),
        "portal_id": ch.portal_id, "law_number": ch.portal_id, "document_kind": kind, "text_version": "as_enacted",
        "principal_law_number": _law_number(act_no) if act_no else None,
        "principal_link_source": "portal_listing" if act_no else None,
        "commences_law_number": commences[0] if commences and kind == "commencement_instrument" else None,
        "published_on": now.get("publication_date"), "commencement_note": now.get("commencement"),
        "instrument_status": now.get("status"), "law_name_portal": now.get("title"),
        "related_instrument": now.get("related"),
        "language": None, "language_source": None, "legal_status": "unknown", "status_source": None,
        "crawl_flags": [], "review_flags": ([] if act_no else ["principal_unlinked"])
                                          + (["seed_resolved_to_portal"] if seed_law else []),
    }
    return cand


def verify_stored(client, host: str, baseline: Baseline, limit: int) -> list[dict]:
    """One conditional HEAD per stored lom document (newest first, at most `limit`), never following a redirect:
    304 means unchanged; 200 with other validators means changed; 200 with the same validators means the server
    ignored the condition (recorded, not a change); anything else is recorded as it came."""
    if limit <= 0:
        return []
    docs = [d for d in baseline.stored.values() if d.url and host in d.url and (d.etag or d.last_modified)]
    docs.sort(key=lambda d: d.access_date or "", reverse=True)
    out = []
    for d in docs[:limit]:
        headers = {k: v for k, v in (("If-None-Match", d.etag), ("If-Modified-Since", d.last_modified)) if v}
        try:
            resp = client.request("HEAD", d.url, headers=headers, max_redirects=0)
            status, err = resp.status_code, None
            got = {k: (getattr(resp, "headers", None) or {}).get(k) for k in ("ETag", "Last-Modified", "Location")}
        except Exception as e:  # noqa: BLE001 — one failed check is recorded, not fatal
            status, err, got = None, f"{type(e).__name__}: {e}", {}
        same = (got.get("ETag") == d.etag if d.etag else True) and \
               (got.get("Last-Modified") == d.last_modified if d.last_modified else True)
        outcome = ("unchanged" if status == 304 else "changed" if status == 200 and not same
                   else "same_validators" if status == 200 else "redirect" if status in (301, 302, 303, 307, 308)
                   else "error" if err else "other")
        out.append({"url": d.url, "doc_id": d.doc_id, "run": d.run, "status": status, "error": err, "outcome": outcome,
                    "unchanged": outcome == "unchanged", "changed": outcome == "changed", "sent": headers, "got": got})
    return out


def write_changes(out_dir: str | Path, changes: Changes, verification: Optional[list[dict]] = None,
                  extra: Optional[dict] = None) -> dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    payload = {"generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), **(extra or {}),
               **changes.as_dict(), "verify_stored": verification or []}
    (out / "changes.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str),
                                      encoding="utf-8", newline="\n")
    (out / "changes.md").write_text(changes_markdown(changes, verification or [], extra or {}),
                                    encoding="utf-8", newline="\n")
    return {"changes.json": str(out / "changes.json"), "changes.md": str(out / "changes.md")}


def _cell(text: Optional[str]) -> str:
    """One Markdown table cell: no pipes, no line breaks."""
    return " ".join(str(text or "").split()).replace("|", "\\|")


def changes_markdown(changes: Changes, verification: list[dict], extra: dict) -> str:
    s = changes.summary()
    lines = [f"# Update check, {extra.get('generated_at') or datetime.now(timezone.utc).strftime('%Y-%m-%d')}", "",
             f"Since **{s['since']}** ({s['mode']} mode"
             + (f", baseline `{s['baseline_run']}`" if s["baseline_run"] else "") + "). "
             f"{s['total']} change(s): {s['to_crawl']} to fetch, {s['recorded_only']} recorded only.", ""]
    for title, items in (("Principal acts", changes.principals), ("Amending acts", changes.amendments),
                         ("Subsidiary legislation", changes.subsidiary),
                         ("Link list against the runs", changes.listed)):
        if title.startswith("Link list") and not items and not (extra.get("link_list")):
            continue                                    # no --list: no section
        lines += [f"## {title} ({len(items)})", ""]
        if title.startswith("Link list"):
            ll = extra.get("link_list") or {}
            lines += [f"`{ll.get('list')}` (built {ll.get('generated_at')}): {ll.get('rows')} rows, {ll.get('stored')} stored "
                      f"by a run, {ll.get('duplicates')} logged as duplicates, **{ll.get('not_in_runs')} stored by no run** "
                      f"(fetched), {ll.get('stored_elsewhere')} stored under another address (not fetched).", ""]
        if not items:
            lines += ["None.", ""]
            continue
        lines += ["| Law | Change | Why | Fetch |", "| :---- | :---- | :---- | :---- |"]
        for ch in items:
            why = "; ".join(ch.reasons) + (f". {ch.note}" if ch.note else "")
            lines.append(f"| {_cell(ch.law_number)}: {_cell((ch.law_name or '')[:70])} | {ch.change} | {_cell(why)} | "
                         f"{'yes' if ch.crawl else 'no'} |")
        lines.append("")
    if verification:
        n = len(verification)
        lines += [f"## Stored files checked ({n})", "",
                  f"{sum(1 for v in verification if v['unchanged'])} unchanged (304), "
                  f"{sum(1 for v in verification if v['changed'])} changed (200 with other validators), "
                  f"{sum(1 for v in verification if not v['unchanged'] and not v['changed'])} other "
                  f"(a 200 with the same validators, a redirect, an error).", ""]
        for v in verification:
            if not v["unchanged"]:
                lines.append(f"- {v['doc_id']} ({v['run']}): {v.get('outcome')}, HTTP {v['status']} "
                             f"{v['error'] or ''} {v['url']}")
        lines.append("")
    if changes.notes:
        lines += ["## Notes", ""] + [f"- {n}" for n in changes.notes] + [""]
    return "\n".join(lines)


def _updates_hashes() -> dict[str, str]:
    here = Path(__file__).parent
    return {f"updates/{p.name}": hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(here.glob("*.py"))}
