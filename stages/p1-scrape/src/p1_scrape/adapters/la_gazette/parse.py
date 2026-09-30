"""Reading the Lao Official Gazette's listings and law pages.

The gazette is a PHP application. A listing is `/index.php?r=site/list&legaltype=<n>&old=<0|1>`, ten rows a page,
and a row carries more than any other portal we have met (`../NOTES.md` 1.2):

    ຫົວຂໍ້ (title) | ພາກສ່ວນຮັບຜິດຊອບ (body) | ວັນ-ເດືອນ-ປີ ນິຕິກໍາ (made) | ເຜີຍແຜ່ລົງຈົດໝາຍເຫດ (gazetted)
    | ປະເພດນິຕິກໍາ (kind) | ສະຖານະພາບ (status) | ເນື້ອໃນ (the law's page) | PDF ອັງກິດ | PDF ລາວ

Nine cells on every one of the 182 rows read on 2026-09-20, in that order: the **English** PDF column comes
before the **Lao** one.

**Two PDF columns.** The Lao text is the law; the English one, where it exists, is a translation the gazette
itself offers. Both are collected, and each is recorded with its own language.

**`old=0` and `old=1` are two halves of one body.** `old=0` lists only what the portal marks ປັດຈຸບັນ (current);
`old=1` lists ສະບັບເກົ່າ (old version) — the superseded texts **and the amending laws**, which appear nowhere
else. `CONVENTIONS.md` section 1 asks for every amending instrument the portal lists, so both are read
(`../NOTES.md` 1.2).

**The documents are scans**, so nothing here reads a document: everything comes from the listing.
"""
from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin

ROOT = "https://laoofficialgazette.gov.la"

_ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
_CELL_RE = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S | re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_HREF_RE = re.compile(r'href="([^"]+)"', re.I)
_ID_RE = re.compile(r"site/display&(?:amp;)?id=(\d+)")
_DATE_RE = re.compile(r"(\d{1,2})-(\d{1,2})-(\d{4})")
# "ສະແດງ 1-10 ຂອງ 182 ຜົນທີ່ໄດ້ຮັບ." — showing 1-10 of 182 results
_SUMMARY_RE = re.compile(r"<div class=\"summary\">(.*?)</div>", re.S)
_TOTAL_RE = re.compile(r"(\d+)\s*-\s*(\d+)\s+\S+\s+(\d+)")
#: what the portal prints instead of a table when a kind has nothing in it at all ("no data")
EMPTY_MARKER = "ບໍ່ມີຂໍ້ມູນ"
#: a row of a law's own page: `<div class="row"><strong>LABEL: </strong>value</div>`
_DETAIL_ROW_RE = re.compile(r'<div class="row">\s*<strong>(.*?)</strong>(.*?)</div>', re.S | re.I)

#: the kinds of instrument the portal lists, by its own `legaltype` number, with what each is in contract terms.
#: The Lao label is kept as the portal writes it, because that is what a reader will see on the page.
#:
#: `subset_of` records a listing contained in another. **legaltype 16 is contained in legaltype 6**: both were
#: read in full on 2026-09-20, and all 180 of 16's law ids are among 6's 182. The two that 6 has besides are the
#: Civil Code (id 1619) and the Penal Code (id 1402). So 6 is the whole body of laws and 16 is the same list
#: with the two codes left out. A listing with a `subset_of` is not read by default: it costs 18 requests and
#: adds nothing (`../NOTES.md` 1.2).
#:
#: **The order here is the order the listings are read**, and it is deliberate: the Civil Code and the Penal Code
#: come before the general Law listing, which also carries both. A law is kept under the first listing that
#: names it, so the two codes keep the specific kind the portal gives them rather than the general ກົດໝາຍ.
LEGAL_TYPES = {
    13: {"label": "ລັດຖະທໍາມະນູນ", "english": "Constitution", "kind": "principal_act"},
    1: {"label": "ປະມວນກົດໝາຍ ແພ່ງ", "english": "Civil Code", "kind": "principal_act"},
    10: {"label": "ປະມວນກົດໝາຍ ອາຍາ", "english": "Penal Code", "kind": "principal_act"},
    6: {"label": "ກົດໝາຍ", "english": "Law", "kind": "principal_act"},
    16: {"label": "ກົດໝາຍ", "english": "Law (second listing)", "kind": "principal_act", "subset_of": 6},
    9: {"label": "ລັດຖະບັນຍັດ", "english": "Presidential Ordinance", "kind": "principal_act"},
    4: {"label": "ລັດຖະດໍາລັດ", "english": "Presidential Decree", "kind": "subsidiary_legislation"},
    3: {"label": "ດໍາລັດ", "english": "Decree", "kind": "subsidiary_legislation"},
    8: {"label": "ຄໍາສັ່ງ", "english": "Order", "kind": "subsidiary_legislation"},
    2: {"label": "ຂໍ້ຕົກລົງ", "english": "Agreement", "kind": "subsidiary_legislation"},
    5: {"label": "ຄໍາແນະນໍາ", "english": "Instruction", "kind": "other"},
    12: {"label": "ມະຕິຕົກລົງ", "english": "Resolution", "kind": "other"},
}

#: what the portal's status column says, and what it means for `legal_status` (POLICY.md 3.5: read, never infer).
#: The contract's vocabulary has no `superseded`, and decision 17 settles superseded as repealed, so ສະບັບເກົ່າ
#: ("old version") reads as `repealed` with the portal's own word kept beside it in `status_word`.
STATUS = {
    "ປັດຈຸບັນ": "in_force",             # current
    "ສະບັບເກົ່າ": "repealed",            # old version: the text a revised version replaced
    "ຍົກເລີກ": "repealed",              # cancelled
    "ຖືກຍົກເລີກ": "repealed",
    "ຍັງບໍ່ມີຜົນບັງຄັບໃຊ້": "not_yet_in_force",
}

#: What an instrument **does**, read from its title. Three Lao words share a root and mean different things, and
#: getting them apart decides whether a document is evidence or linkage (`POLICY.md` 3.2, `CONTRACT.md` 3.3).
#:
#: - **ປັບປຸງ … ມາດຕາ** — "the amendment of article(s) N of …". This, and only this, is an amending instrument:
#:   an amendment always names the articles it changes. Measured on the 1,773 laws of 2026-09-20, requiring the
#:   article word takes the count from 41 to 26 and **finds 3 the looser pattern missed** (titles that open
#:   `ປັບປຸງ ມາດຕາ 19 ຂອງ…` with no `ການ` prefix).
#: - **ການປັບປຸງ alone** is the ordinary word for *improvement*, and matching it swept in 15 instruments that
#:   amend nothing: compensation prices for a ໂຄງການປັບປຸງທາງຫຼວງ (a highway improvement project), an Order on
#:   ການປັບປຸງຄຸນນະພາບ (improving quality), a Resolution on ການປັບປຸງການໃສ່ສີ (the colouring of the national
#:   emblem). Each had been stripped of its indicator tags and filed as linkage.
#: - **ລົບລ້າງ** is likewise ordinary ("to remove, to annul") — ຂໍລົບລ້າງ is applying to annul a judgment, and
#:   ລົບລ້າງສິ່ງກີດຂວາງ is clearing obstacles from a road. It marks a **repealing act** only when it names the
#:   instrument it repeals, as LA-1702 does: ການລົບລ້າງລັດຖະບັນຍັດ ເລກທີ 001.
#: - **ສະບັບປັບປຸງ** ("revised version") is a consolidated text, not an amendment — but the phrase also appears
#:   naming the *target* ("article 12 of the Law on Investment Promotion, revised version of 2016"), so it is
#:   tested **last**, after the amending and repealing tests, never before them.
_AMENDING_RE = re.compile(r"ປັບປຸງ[^,]{0,24}ມາດຕາ")
#: an instruction on *implementing*, or a resolution *adopting*, someone else's amendment is not itself one
_NOT_THE_INSTRUMENT_RE = re.compile(r"ການຈັດຕັ້ງປະຕິບັດ|ການຮັບຮອງເອົາ")
_REPEALING_RE = re.compile(r"ລົບລ້າງ[^,]{0,16}(?:ກົດໝາຍ|ລັດຖະບັນຍັດ|ດຳລັດ|ຂໍ້ຕົກລົງ|ຄຳສັ່ງ|ມະຕິ)")
_REVISED_RE = re.compile(r"ສະບັບປັບປຸງ")

#: The /am/ vowel is written two ways in one listing (21 titles use ຳ, 5 use ◌ໍ + າ), and ຫ+ນ, ຫ+ມ, ຫ+ລ are the
#: spelled-out forms of the ໝ, ໜ and ຫຼ ligatures. Tesseract writes the spelled-out forms too, which is why the
#: OCR pilot of 2026-09-20 had to normalise them before a title matched the portal's own (`../NOTES.md` 3).
_FOLD = (
    ("ໍາ", "ຳ"),         # ◌ໍ + າ  ->  ຳ
    ("ຫນ", "ໜ"),         # ຫ + ນ  ->  ໜ
    ("ຫມ", "ໝ"),         # ຫ + ມ  ->  ໝ
    ("ຫລ", "ຫຼ"),   # ຫ + ລ  ->  ຫ + ຼ
)


def fold(text: Optional[str]) -> str:
    """One spelling for matching: NFC, then the ligatures and the /am/ vowel written one way, spaces collapsed.

    NFC only — never NFKC, which rewrites all 182 of the Lao titles read on 2026-09-20 and is not a spelling
    normalisation at all. Lao has no case, so nothing here upper-cases: `TitleRule.normalise` calls `.upper()`,
    which leaves Lao untouched, and that is why the registry's patterns are plain Lao with no `\\b` boundaries —
    `\\b` needs ASCII word characters and never fires inside Lao script.
    """
    out = unicodedata.normalize("NFC", text or "")
    for src, dst in _FOLD:
        out = out.replace(src, dst)
    return re.sub(r"\s+", " ", out).strip()


def listing_path(legal_type: int, page: int = 1, old: int = 0) -> str:
    """One page of one kind's listing. The portal counts pages from 1 and serves ten rows.

    `Document_pageSize` is ignored by the server (asking for 50 still returns rows 11 to 20), so a listing of
    182 laws costs 19 requests and there is no way to ask for fewer.
    """
    path = f"/index.php?r=site/list&legaltype={legal_type}&old={old}"
    return path if page <= 1 else f"{path}&Document_page={page}"


def detail_path(law_id: str | int) -> str:
    return f"/index.php?r=site/display&id={law_id}"


def text_of(markup: str) -> str:
    """The readable text of a cell: tags out, entities resolved, whitespace collapsed.

    The parameter is not called `html`, because that is the module this file now uses to resolve the entities —
    naming it so shadowed the import and made `_unescape` unreachable from here.
    """
    out = _TAG_RE.sub(" ", markup or "")
    return re.sub(r"\s+", " ", html.unescape(out).replace("\xa0", " ")).strip()


def iso_date(text: str) -> Optional[str]:
    """`25-06-2025` -> `2025-06-25`. The portal writes day first."""
    m = _DATE_RE.search(text or "")
    if not m:
        return None
    day, month, year = (int(g) for g in m.groups())
    if not (1 <= day <= 31 and 1 <= month <= 12):
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def results_total(page: str) -> Optional[int]:
    """How many rows this listing claims, from its own summary line.

    `0` when the portal prints ບໍ່ມີຂໍ້ມູນ ("no data") instead of a table, which is a real answer and not a
    failure: `legaltype=4` (Presidential Decree) is empty, and so is `old=1` for three kinds. `None` means the
    page carried neither, which is the shape a caller should read as "the format may have changed".
    """
    m = _SUMMARY_RE.search(page)
    if m:
        hit = _TOTAL_RE.search(text_of(m.group(1)))
        if hit:
            return int(hit.group(3))
    return 0 if EMPTY_MARKER in page else None


@dataclass
class ListedLaw:
    """One row of one listing: a law, its dates, its status, and the files the portal offers for it."""

    legal_type: int
    law_id: str                       # the portal's own id, from the law page's address
    title: str                        # Lao, folded to one spelling
    agency: Optional[str]             # the body responsible, Lao
    made_on: Optional[str]            # ISO, the date of the instrument
    gazetted_on: Optional[str]        # ISO, the date it was published in the gazette
    kind_label: Optional[str]         # the portal's word for the kind
    status_label: Optional[str]       # the portal's word for the status
    legal_status: str                 # what that word means: in_force | repealed | not_yet_in_force | unknown
    pdf_lao: Optional[str] = None     # the Lao text: the law itself
    pdf_english: Optional[str] = None  # a translation the gazette offers, where it has one
    document_kind: str = "principal_act"
    old: int = 0                      # 0 the current listing, 1 the superseded one
    also_listed_under: tuple = ()     # the other legaltype numbers whose listing carries this same law id

    @property
    def code(self) -> str:
        return f"LA-{self.law_id}"

    @property
    def is_revised(self) -> bool:
        """This text is itself a consolidation of the amendments before it.

        ສະບັບປັບປຸງ in the title, **and** the instrument is not an amendment or a repeal — in an amending title
        the phrase names the law being amended, not this one.
        """
        return bool(_REVISED_RE.search(self.title)) and self.document_kind not in ("amending_act", "repealing_act")

    def url(self, which: str = "lao") -> Optional[str]:
        path = self.pdf_lao if which == "lao" else self.pdf_english
        return urljoin(ROOT, path) if path else None


def document_kind_of(row_kind: str, title: str) -> str:
    """The kind from the listing, narrowed by what the title says the instrument does.

    The portal's `legaltype` says what sort of instrument something is, never what it does. A title that names
    the articles it amends is an `amending_act` whichever listing it came from, and `POLICY.md` 3.2 and
    `CONTRACT.md` 3.3 both turn on that distinction: an amending instrument carries no indicator tags and P3
    re-cites the principal law.

    **The order of these tests is the whole point.** Testing ສະບັບປັບປຸງ first — as this did until 2026-09-21 —
    files an amendment as a principal act whenever the *target* law is a revised version, which is the common
    case: ການປັບປຸງມາດຕາ 12 ຂອງກົດໝາຍ … ສະບັບປັບປຸງ ປີ 2016 read as a principal act, and LA-2323, an in-force
    one-article amendment, would have been handed to mapping as the standing Law on State Investment.
    """
    folded = fold(title)
    if _AMENDING_RE.search(folded) and not _NOT_THE_INSTRUMENT_RE.search(folded):
        return "amending_act"
    if _REPEALING_RE.search(folded):
        return "repealing_act"
    return row_kind


def parse_listing(page: str, legal_type: int, old: int = 0) -> list[ListedLaw]:
    """Every law row on one listing page, in the order the portal lists them."""
    meta = LEGAL_TYPES.get(legal_type, {"kind": "other"})
    out: list[ListedLaw] = []
    for row in _ROW_RE.findall(page):
        if "site/display" not in row:
            continue                                   # the header, the filter row, the pager
        cells = _CELL_RE.findall(row)
        plain = [text_of(c) for c in cells]
        law_id = _ID_RE.search(row)
        if not law_id or not plain or not plain[0]:
            continue
        # The listing table is nine columns wide. The portal's own front page carries a narrower version of the
        # same table, and reading that one by fixed index put the text of the detail link — ເບິ່ງ, "view" —
        # into the status column on every row. A row that is not the listing's shape is not a listing row.
        detail_at = next((i for i, c in enumerate(cells) if "site/display" in c), -1)
        if detail_at != 6 or len(cells) != 9:
            continue
        english, lao = _pdf_columns(cells, detail_at)
        status_label = plain[5]
        title = fold(plain[0])
        out.append(ListedLaw(
            legal_type=legal_type, law_id=law_id.group(1), title=title,
            agency=fold(plain[1]) or None, made_on=iso_date(plain[2]), gazetted_on=iso_date(plain[3]),
            kind_label=fold(plain[4]) or None, status_label=fold(status_label) or None,
            legal_status=STATUS.get(fold(status_label), "unknown"),
            pdf_lao=lao, pdf_english=english,
            document_kind=document_kind_of(meta["kind"], title),
            old=old,
        ))
    return out


def _pdf_columns(cells: list[str], detail_at: int) -> tuple[Optional[str], Optional[str]]:
    """(English, Lao) — the two cells that follow the ເນື້ອໃນ column, which links the law's own page.

    Taken **relative to the detail cell**, not from the end of the row and not from fixed indices. The portal
    ships the same table in more than one width: the listings have nine columns, and its own front page has
    eight (no ສະຖານະພາບ). Counting from the end works for both; counting from the start does not, and hard-coding
    `>= 9` dropped the English file from every row of the narrower table.

    A row offering only one file keeps it as the Lao one: the Lao text is the document of record, and no row was
    ever seen with an English file and no Lao one (21 of 182 had both, 161 had Lao alone, none had English
    alone).
    """
    after = cells[detail_at + 1:detail_at + 3]
    links = [(m.group(1) if (m := _HREF_RE.search(c)) else None) for c in after]
    english, lao = (links + [None, None])[:2]
    if lao is None and english:
        english, lao = None, english
    return (_unescape(english) if english else None), (_unescape(lao) if lao else None)


def _unescape(url: str) -> str:
    """An address as the page means it, not as the markup spells it.

    `&amp;` was never the only entity in these hrefs. Four addresses in the list of 2026-09-20 carry `&#039;`
    for an apostrophe — `Women&#039;s_Union Law.pdf` — and requesting the literal entity asks for a path that
    does not exist. On this portal that does not 404: the server answers **HTTP 200 with its own HTML page**
    (`../NOTES.md` 1.1), so the crawl of 2026-09-21 recorded four documents as `failed` at status 200 rather
    than as missing. Every named and numeric entity is resolved, which is what `text_of` already did for the
    cells beside these links.
    """
    return html.unescape(url or "").strip()


@dataclass
class LawPage:
    """What a law's own page adds: the same metadata, confirmed, and nothing else. It carries no text."""

    law_id: str
    title: Optional[str] = None
    kind_label: Optional[str] = None
    issued_by: Optional[str] = None
    agency: Optional[str] = None
    made_on: Optional[str] = None
    gazetted_on: Optional[str] = None
    pdfs: tuple[str, ...] = ()


#: the labels a law's own page prints, each in its own `<div class="row"><strong>…</strong>` (read 2026-09-20
#: from id=2597). The match is on the label's leading words, because two of them carry trailing words of their
#: own ("ເຜີຍແຜ່ລົງ ຈົດໝາຍເຫດ ວັນທີ່ :").
_LABELS = (("title", "ຫົວຂໍ້"), ("kind_label", "ປະເພດ ນິຕິກໍາ"), ("issued_by", "ອອກໂດຍ"),
           ("agency", "ພາກສ່ວນຮັບຜິດຊອບ"), ("made_on", "ວັນທີ່ ນິຕິກໍາ"), ("gazetted_on", "ເຜີຍແຜ່ລົງ ຈົດໝາຍເຫດ"))


def parse_law_page(page: str, law_id: str) -> LawPage:
    """The law's own page. Metadata only: the portal keeps no text, only the scan.

    **Nothing in the crawl calls this.** The page carries no field the listing does not already carry, and it
    offers fewer files — id=2597 lists one download where its listing row gives two columns — so the detail page
    is not read (`../NOTES.md` 2.3). It is kept, and tested, because that claim is only worth making if the code
    that would read the page exists and agrees.
    """
    found: dict[str, Optional[str]] = {}
    for raw_label, raw_value in _DETAIL_ROW_RE.findall(page):
        label, value = fold(text_of(raw_label)).rstrip(": "), text_of(raw_value)
        for field, want in _LABELS:
            if field not in found and label.startswith(fold(want)):
                found[field] = iso_date(value) if field.endswith("_on") else (fold(value) or None)
                break
    return LawPage(law_id=law_id,
                   pdfs=tuple(_unescape(h) for h in _HREF_RE.findall(page) if h.lower().endswith(".pdf")),
                   **{k: found.get(k) for k, _ in _LABELS})
