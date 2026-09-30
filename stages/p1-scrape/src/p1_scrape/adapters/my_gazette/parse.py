"""Pure parsers and helpers for Laws of Malaysia pages and listing replies (unit-tested offline)."""
from __future__ import annotations

import base64
import html as _html
import json
import re
from typing import Any, Optional
from urllib.parse import parse_qs, quote, unquote, urlparse

from .records import AmendingAct, ListingVersion, LomDocument, LomUnavailable, PrincipalAct, TimelineEntry

_LOM = "https://lom.agc.gov.my"


_LISTINGS = {
    "updated": ("principal.php?type=updated", "json-updated-2024.php"),
    "amendment": ("principal.php?type=amendment", "json-amendment-2024.php"),
}


# Characters kept literally in a document path; everything else (spaces, non-ASCII, %) is encoded.
_PATH_SAFE = "/-_.~()!*',;=+:@$&"


# A status marker closes a title line: "(Repealed by Act 805)", "(Repealed by Act P.U. (A) 146/1969)",
# "(Diganti oleh Akta 809)". One level of nested parentheses is allowed inside it.
_STATUS_MARKER = re.compile(
    r"\s*\((Repealed by|Dimansuhkan oleh|Superseded by|Diganti oleh)\s+((?:[^()]|\([^()]*\))*)\)\s*$", re.I)


_NYIF_MARKER = re.compile(r"\s*-?\s*\((NOT YET IN FORCE|BELUM BERKUAT KUASA)\)\s*$", re.I)


_PARTIAL_REPEAL = re.compile(r"\s+(in respect of its application to|berkenaan dengan pemakaiannya)\b.*$", re.I)


_NOT_YET_IN_FORCE = re.compile(r"not\s+yet\s+(in\s+force|enforced?)|belum\s+berkuat\s+kuasa", re.I)


_EXCEPT = re.compile(r"\b(except|kecuali)\b", re.I)


_PU_B_REF = re.compile(r"P\.?\s*U\.?\s*\(\s*B\s*\)\s*(\d+)\s*/\s*(\d{4})", re.I)


_TEXT_VERSION = {"ORIGINAL": "as_enacted", "REPRINT": "reprint", "REPRINT ONLINE": "reprint"}


_MONTHS = {
    "january": 1, "februari": 2, "february": 2, "march": 3, "mac": 3, "april": 4, "may": 5, "mei": 5,
    "june": 6, "jun": 6, "july": 7, "julai": 7, "august": 8, "ogos": 8, "september": 9, "october": 10,
    "oktober": 10, "november": 11, "december": 12, "disember": 12, "januari": 1,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "okt": 10,
    "nov": 11, "dec": 12, "dis": 12,
}


_DATE_ISO = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")


_DATE_DMY = re.compile(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b")


_DATE_NAMED = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(" + "|".join(sorted(_MONTHS, key=len, reverse=True)) + r")\.?,?\s+(\d{4})\b",
    re.I)


def extract_response_key(page_html: str) -> str:
    m = re.search(r"SEARCH_RESPONSE_KEY\s*=\s*['\"]([0-9a-fA-F]{64})['\"]", page_html or "")
    if not m:
        raise LomUnavailable("lom listing page carries no SEARCH_RESPONSE_KEY; the page format changed")
    return m.group(1)


def datatables_form(draw: int, start: int, length: int) -> dict:
    """The form fields the listing page's DataTables sends (serverSide, language=BI)."""
    return {"draw": str(draw), "start": str(start), "length": str(length),
            "search[value]": "", "search[regex]": "false",
            "order[0][column]": "0", "order[0][dir]": "desc",
            "searchValue": "", "language": "BI"}


def decrypt_listing(payload: Any, key_hex: str) -> dict:
    """Decrypt a lom DataTables reply: base64( IV[12] | TAG[16] | CIPHERTEXT ), AES-256-GCM.

    `payload` is either {"encrypted": true, "data": "<base64>"} or the bare base64 string,
    matching the two cases in the portal's js/responseCrypto.js.
    """
    if isinstance(payload, dict):
        if payload.get("encrypted") is True:
            payload = payload.get("data")
        elif "records" in payload:
            return payload            # an unencrypted reply, should the portal ever send one
        elif payload.get("error"):
            raise LomUnavailable(f"lom listing error: {payload.get('message') or payload}")
    if not isinstance(payload, str) or not payload:
        raise LomUnavailable("lom listing reply is empty or in an unknown format")
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError as e:  # pragma: no cover - environment problem, not logic
        raise LomUnavailable("the 'cryptography' package is required to read lom listings") from e
    raw = base64.b64decode(payload)
    if len(raw) < 28:
        raise LomUnavailable("lom listing reply too short to be AES-GCM")
    iv, tag, ct = raw[:12], raw[12:28], raw[28:]
    return json.loads(AESGCM(bytes.fromhex(key_hex)).decrypt(iv, ct + tag, None))


def parse_principal(rec: dict, root: str = _LOM) -> Optional[PrincipalAct]:
    act_no = re.sub(r"\s+", " ", str(rec.get("lgt_act_no") or "")).strip()
    if not act_no:
        return None
    versions: list[ListingVersion] = []
    markers: dict[str, tuple[str, str, str]] = {}      # lang -> (kind, target, raw marker text)
    # Each title line is <a href="act-detail.php?…lang=XX…">TITLE</a> followed, up to the next <br>,
    # by an optional status marker and an optional "As At / Sebagaimana Pada <date>". A marker can
    # also sit inside the anchor: "... 2016 (BELUM BERKUAT KUASA)".
    for line in re.split(r"<br\s*/?>", rec.get("title") or "", flags=re.I):
        a = re.search(r'<a href="act-detail\.php\?([^"]+)">(.*?)</a>(.*)$', line, re.S)
        if not a:
            continue
        lang = (parse_qs(_html.unescape(a.group(1))).get("lang") or [""])[0].upper()
        title = _clean(a.group(2))
        tail = _clean(re.sub(r"(As At|Sebagaimana Pada).*$", "", a.group(3), flags=re.S))
        date = re.search(r"(?:As At|Sebagaimana Pada)\s*(?:<[^>]+>\s*)*([\d-]+)", a.group(3))
        online = title.startswith("*")
        title = title.lstrip("*").strip()
        for text in (tail, title):
            m = _STATUS_MARKER.search(text)
            if m:
                verb, target = m.group(1).lower(), _clean(m.group(2))
                kind = "superseded" if verb in ("superseded by", "diganti oleh") else (
                    "partially_repealed" if _PARTIAL_REPEAL.search(" " + target) else "repealed")
                markers.setdefault(lang, (kind, target, f"{m.group(1)} {target}"))
                title = _STATUS_MARKER.sub("", title).strip()
            n = _NYIF_MARKER.search(text)
            if n:
                markers.setdefault(lang, ("not_yet_in_force", "", n.group(1)))
                title = _NYIF_MARKER.sub("", title).strip()
        if lang:
            versions.append(ListingVersion(lang=lang, online=online, title=title or None,
                                           as_at=(date.group(1) if date else None)))

    def latest(lang: str) -> Optional[ListingVersion]:
        vs = [v for v in versions if v.lang == lang]
        return max(vs, key=lambda v: iso_date(v.as_at) or "") if vs else None

    cleaned = {lang: (latest(lang).title if latest(lang) else None) for lang in ("BI", "BM")}
    marker = markers.get("BI") or markers.get("BM")
    kind, target, raw_marker = marker if marker else (None, "", None)
    number = _marker_number(_PARTIAL_REPEAL.sub("", target)) if target else None
    links: dict[str, str] = {}
    for href in re.findall(r'href="(processFile\.php\?isDirect=1&(?:amp;)?token=[^"]+)"',
                           rec.get("title_link") or ""):
        href = _html.unescape(href)
        target_url = decode_token_target(href)
        lang = (parse_qs(urlparse(target_url).query).get("lang") or [""])[0].upper() if target_url else ""
        if lang and lang not in links:
            links[lang] = href
    return PrincipalAct(
        act_no=act_no, title_bi=cleaned.get("BI"), title_bm=cleaned.get("BM"),
        as_at_bi=(latest("BI").as_at if latest("BI") else None),
        as_at_bm=(latest("BM").as_at if latest("BM") else None),
        online_marker=any(v.online for v in versions),
        repealed_by=number if kind in ("repealed", "partially_repealed") else None,
        documents=_documents(rec.get("doc2downloadgeneratepdf"), root), detail_links=links,
        versions=versions, status_kind=kind, status_marker=raw_marker,
        superseded_by=number if kind == "superseded" else None, raw=rec)


def principal_status(p: PrincipalAct) -> tuple[str, Optional[str]]:
    """(legal_status, status_source) from the listing's own marker. "Superseded by" counts as repealed
    (decision 10): the superseding revised edition replaces the old text."""
    return {
        "repealed": ("repealed", "portal_listing"),
        "superseded": ("repealed", "portal_listing"),
        "partially_repealed": ("partially_in_force", "portal_listing"),
        "not_yet_in_force": ("not_yet_in_force", "portal_listing"),
    }.get(p.status_kind or "", ("unknown", None))


def parse_amendment(rec: dict, root: str = _LOM) -> Optional[AmendingAct]:
    number = str(rec.get("ACTNO_LEGISLATION") or "").strip()
    if not number and rec.get("nombor"):
        number = "A" + str(rec["nombor"]).strip()
    if not number:
        return None
    docs = _documents(rec.get("DOC2DOWNLOADBIgeneratepdf"), root) + _documents(rec.get("DOC2DOWNLOADBMgeneratepdf"), root)
    link = re.search(r'href="(processFile\.php\?isDirect=1&(?:amp;)?token=[^"]+)"', rec.get("LEGISLATIONTITLEBI_LINK") or "")
    return AmendingAct(
        a_number=number.upper(),
        title_bi=_anchor_text(rec.get("LEGISLATIONTITLEBI")), title_bm=_anchor_text(rec.get("LEGISLATIONTITLEBM")),
        project_id=(str(rec.get("ILP_PROJECT_ID")).strip() or None) if rec.get("ILP_PROJECT_ID") else None,
        royal_assent=_blank(rec.get("ROYALASSENTDATE")), publication=_blank(rec.get("PUBLICATIONDATE")),
        commencement_date=_blank(rec.get("COMMENCEMENTDATEBI")),
        commencement_remark=_blank(rec.get("COMMENCEMENTREMARKBI")),
        documents=docs, detail_link=(_html.unescape(link.group(1)) if link else None), raw=rec)


def amendment_status(a: AmendingAct, today: str) -> tuple[str, Optional[str]]:
    """(legal_status, status_source) as the amendment listing states it.

    "NOT YET IN FORCE" alone is not_yet_in_force. "Not Yet In Force except …", or a remark that also
    dates some parts, is partially_in_force. A commencement date field later than today is
    not_yet_in_force. Anything else is unknown: a past date says when parts began, not that all did."""
    remark = a.commencement_remark or ""
    if _NOT_YET_IN_FORCE.search(remark):
        if _EXCEPT.search(remark) or all_dates(remark):
            return "partially_in_force", "portal_remark"
        return "not_yet_in_force", "portal_remark"
    if _NOT_YET_IN_FORCE.search(a.commencement_date or ""):
        return "not_yet_in_force", "portal_listing"
    field_date = iso_date(a.commencement_date)
    if field_date and field_date > today:
        return "not_yet_in_force", "portal_listing"
    return "unknown", None


def pu_b_refs(a: AmendingAct) -> list[str]:
    """P.U. (B) references in an amendment's commencement field and remark, normalised, in order."""
    out: list[str] = []
    for text in (a.commencement_date, a.commencement_remark):
        for m in _PU_B_REF.finditer(text or ""):
            ref = f"P.U. (B) {int(m.group(1))}/{m.group(2)}"
            if ref not in out:
                out.append(ref)
    return out


def parse_timeline(detail_html: str, root: str = _LOM) -> list[TimelineEntry]:
    """Timeline entries of an act-detail page, in portal order."""
    if not detail_html or "cd-horizontal-timeline" not in detail_html:
        return []
    nav = re.findall(r'<a href="#0"\s+data-date="([^"]*)"\s+data-project-id="([^"]*)"\s+'
                     r'data-log-type="([^"]*)"[^>]*>(.*?)</a>', detail_html, re.S)
    contents = re.findall(r'<li\s+(?:class="selected"\s+)?data-date="([^"]*)">(.*?)</li>',
                          detail_html.split('class="events-content"', 1)[-1], re.S)
    entries: list[TimelineEntry] = []
    for i, (date_, pid, log_type, _label) in enumerate(nav):
        body = contents[i][1] if i < len(contents) and contents[i][0] == date_ else ""
        p_text = re.search(r"<p[^>]*>(.*?)</p>", body, re.S)
        lines = [_clean(x) for x in re.split(r"<br\s*/?>", p_text.group(1))] if p_text else []
        lines = [x for x in lines if x]
        fields: dict[str, str] = {}
        for line in lines[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                fields[k.strip().lower()] = v.strip()
        src = re.search(r'data-src="pdfjs/web/viewer\.html\?file=([^"&]+)', body)
        entries.append(TimelineEntry(
            date=date_ or None, display_date=(lines[0] if lines else None), log_type=log_type.strip().upper(),
            project_id=(pid or None), file_url=(portal_file_url(_html.unescape(src.group(1)), root) if src else None),
            publication_date=_blank(fields.get("publication date")),
            royal_assent_date=_blank(fields.get("royal assent date")),
            commencement_date=_blank(fields.get("commencement date")),
            commencement_remark=_dash_blank(fields.get("commencement remark")),
            pu_no=_blank(fields.get("p.u. no."))))
    return entries


def portal_file_url(path: str, root: str = _LOM) -> str:
    """'../../../ilims/upload/…' or '/upload/portal/…' → an absolute, percent-encoded lom URL."""
    p = unquote(path).replace("../../../", "/")
    if p.startswith("/upload/"):
        p = "/ilims" + p
    if not p.startswith("/"):
        p = "/" + p
    return root.rstrip("/") + quote(p, safe=_PATH_SAFE)


def decode_token_target(href: str) -> Optional[str]:
    """processFile.php?token=base64('<target url>|<signature>') → the target URL (read-only)."""
    m = re.search(r"token=([^&\"]+)", href)
    if not m:
        return None
    try:
        return base64.b64decode(unquote(m.group(1))).decode("utf-8", "replace").split("|", 1)[0]
    except (ValueError, UnicodeError):
        return None


def choose_document(docs: list[LomDocument], languages: list[str]) -> Optional[LomDocument]:
    """First preferred language that has a document; printed before online within a language.
    For a principal act use choose_principal_document, which decides by as-at date."""
    order = {"printed": 0, "unknown": 1, "online": 2}
    for lang in languages:
        same = sorted((d for d in docs if d.language == lang), key=lambda d: order.get(d.edition, 1))
        if same:
            return same[0]
    return docs[0] if docs else None


def document_as_at(p: PrincipalAct, doc: LomDocument) -> Optional[str]:
    """Raw as-at date of the listing version a document belongs to: same language, and online ('*')
    for an online download, printed otherwise. None when that edition has no dated version: a date is
    never borrowed from another edition (Act 26/1947's 1947 original is not "as at 2022")."""
    lang = {"eng": "BI", "msa": "BM"}.get(doc.language, "")
    exact = [v for v in p.versions if v.lang == lang and v.online == (doc.edition == "online")]
    dated = [v for v in exact if iso_date(v.as_at)]
    return max(dated, key=lambda v: iso_date(v.as_at)).as_at if dated else None


def choose_principal_document(p: PrincipalAct, languages: list[str],
                              exclude: frozenset[str] = frozenset()) -> Optional[LomDocument]:
    """The document with the LATEST as-at date in the first preferred language that has one
    (POLICY.md §3.1: choose a version by its date, never by upload order or edition).
    A document whose own edition is dated beats an undated one; on equal dates the printed reprint wins.
    URLs in `exclude` (already stored for another act) are passed over while the act has another document
    in the same language; the language choice itself never changes because of them."""
    for lang in languages:
        same = [d for d in p.documents if d.language == lang]
        if same:
            free = [d for d in same if d.url not in exclude] or same
            return max(free, key=lambda d: (document_as_at(p, d) is not None,
                                            iso_date(document_as_at(p, d)) or "", d.edition == "printed"))
    return p.documents[0] if p.documents else None


def _normalise_title(title: Optional[str]) -> str:
    text = (title or "").upper().replace("’", "'").replace("‘", "'").replace("`", "'")
    return re.sub(r"\s+", " ", text).strip()


def amending_base_title(title: Optional[str]) -> Optional[str]:
    """'PERSONAL DATA PROTECTION (AMENDMENT) ACT 2024' → 'PERSONAL DATA PROTECTION'."""
    if not title:
        return None
    m = re.match(r"^(.*?)\s*\((?:AMENDMENTS?)\)\s*(?:\(NO\.?\s*\d+\)\s*)?(?:ACT\s+)?\d{4}$", _normalise_title(title))
    return m.group(1).strip() if m else None


def principal_title_key(title: Optional[str]) -> Optional[str]:
    """'IMMIGRATION ACT 1959/63' and 'IMMIGRATION ACT' → 'IMMIGRATION'; the key an amending base title
    is looked up by."""
    text = _normalise_title(title)
    if not text:
        return None
    text = re.sub(r" \d{4}(?:/\d{2,4})?$", "", text)
    return re.sub(r" ACT$", "", text) or None


def title_matches_base(principal_title: Optional[str], base: str) -> bool:
    key = principal_title_key(principal_title)
    return key is not None and key == principal_title_key(base)


def all_dates(raw: Optional[str]) -> list[str]:
    """Every date in a lom text, as ISO, in the order written: day-first numbers ('1-3-2017', '17/10/2024'),
    ISO ('2018-04-27') and month names in English or Malay ('1 July 2025', '1 JANUARI 2025', '17 Oct 2024')."""
    if not raw:
        return []
    found: list[tuple[int, str]] = []
    for rx, order in ((_DATE_ISO, "ymd"), (_DATE_DMY, "dmy"), (_DATE_NAMED, "named")):
        for m in rx.finditer(raw):
            if order == "ymd":
                y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            elif order == "dmy":
                d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            else:
                d, mo, y = int(m.group(1)), _MONTHS[m.group(2).lower()], int(m.group(3))
            if 1 <= mo <= 12 and 1 <= d <= 31:
                found.append((m.start(), f"{y:04d}-{mo:02d}-{d:02d}"))
    return [iso for _pos, iso in sorted(found)]


def iso_date(raw: Optional[str]) -> Optional[str]:
    """The first date in a lom text, as ISO ('01-07-2023' → '2023-07-01'); None when there is none."""
    dates = all_dates(raw)
    return dates[0] if dates else None


def amendment_effective_date(a: AmendingAct) -> Optional[str]:
    """The earliest date the amendment listing gives for the amendment taking effect, else its
    publication date. Staleness checks use every date (MyGazetteAdapter._amendment_dates)."""
    dates = all_dates(a.commencement_date) + all_dates(a.commencement_remark)
    return min(dates) if dates else iso_date(a.publication)


def _documents(raw: Any, root: str = _LOM) -> list[LomDocument]:
    if not raw:
        return []
    try:
        items = json.loads(raw) if isinstance(raw, str) else raw
    except ValueError:
        return []
    if isinstance(items, dict):
        items = [items]
    out = []
    for it in items or []:
        path, name, icon = it.get("path") or "", it.get("docName") or "", it.get("icon") or ""
        if not name:
            continue
        lang = "eng" if "-en" in icon else ("msa" if "-ms" in icon else "unknown")
        edition = "printed" if "printed" in icon else ("online" if "online" in icon else "unknown")
        out.append(LomDocument(url=portal_file_url(path + name, root), language=lang, edition=edition, name=name))
    return out


def _timeline_entry_for(doc: LomDocument, entries: list[TimelineEntry]) -> Optional[TimelineEntry]:
    return next((e for e in entries if e.file_url and unquote(e.file_url) == unquote(doc.url)), None)


def _timeline_entry_date(e: TimelineEntry) -> Optional[str]:
    return iso_date(e.publication_date) or iso_date(e.display_date) or iso_date(e.date)


def _title_year(title: Optional[str]) -> Optional[int]:
    m = re.search(r"\b(\d{4})(?:/\d{2,4})?\s*$", _normalise_title(title))
    return int(m.group(1)) if m else None


def _marker_number(target: str) -> Optional[str]:
    """'Akta 811' → 'Act 811'; 'Act P.U. (A) 146/1969' → 'P.U. (A) 146/1969'."""
    text = _clean(target)
    text = re.sub(r"^Akta\s+", "Act ", text, flags=re.I)
    text = re.sub(r"^Act\s+(?=P\.?\s*U)", "", text, flags=re.I)
    return text or None


def _portal_label(meta: dict) -> str:
    pid = meta.get("portal_id")
    return f"Act {pid}" if pid and re.match(r"^A?\d", str(pid)) else str(pid)


def _positive_int(value: Any) -> Optional[int]:
    try:
        n = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _json_or_text(resp) -> Any:
    try:
        return resp.json()
    except ValueError:
        return (resp.text or "").strip().strip('"')


def _clean(s: Optional[str]) -> str:
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def _anchor_text(s: Optional[str]) -> Optional[str]:
    m = re.search(r">(.*?)</a>", s or "", re.S)
    return (_clean(m.group(1)) or None) if m else (_clean(s) or None)


def _blank(v: Any) -> Optional[str]:
    s = str(v).strip() if v is not None else ""
    return s or None


def _dash_blank(v: Any) -> Optional[str]:
    s = _blank(v)
    return None if s in (None, "-") else s


def _pu_key(ref: str) -> str:
    """'P.U. (A) 221/2024', 'P.U.(A) 221/2024' and 'PU(A) 221/2024' compare equal."""
    return re.sub(r"[\s.]", "", ref or "").upper()


def _act_key(act_no: str) -> str:
    return re.sub(r"\s+", " ", act_no).strip().upper()


def _law_number(act_no: str) -> str:
    return f"Act {act_no}" if re.match(r"^A?\d", act_no.strip()) else act_no.strip()


def _a_number_int(a_number: str) -> int:
    m = re.search(r"\d+", a_number or "")
    return int(m.group(0)) if m else 0


def _act_number(law_number: str) -> Optional[str]:
    """Extract a lom act number ONLY from a real act reference ('Act 709', 'Act A1727').
    Guideline/regulation refs like 'GP 3/2025' or 'P.U.(A) 2024' must NOT resolve via
    lom-by-number — their digits are not act numbers (GP 3 would fetch lom Act 3)."""
    m = re.search(r"\bAct\s+(A?\d+)\b", law_number or "", re.IGNORECASE)
    return m.group(1) if m else None
