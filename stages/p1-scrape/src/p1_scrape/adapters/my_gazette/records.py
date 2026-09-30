"""Records parsed from Laws of Malaysia, and the errors that stop lom for a run."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

class LomUnavailable(RuntimeError):
    """lom cannot be crawled on this run: robots.txt, a listing failure, or a changed page format."""


class RobotsDisallowed(LomUnavailable):
    pass


class LomThrottled(LomUnavailable):
    pass


@dataclass
class LomDocument:
    url: str
    language: str            # eng | msa
    edition: str             # printed | online | unknown   (from the portal's download icon)
    name: str


@dataclass
class ListingVersion:
    """One title line of an updated-listing record. A record can list several versions, e.g. Act 26
    has a printed reprint as at 29-06-1947 and an online reprint ('*') as at 05-09-2022."""
    lang: str                                # BI | BM
    online: bool                             # the listing's "*": an online, not a printed, reprint
    title: Optional[str]
    as_at: Optional[str]                     # raw "01-07-2023"


@dataclass
class PrincipalAct:
    act_no: str                              # as the listing prints it: "709", "406 (Revised)"
    title_bi: Optional[str]
    title_bm: Optional[str]
    as_at_bi: Optional[str]                  # latest raw as-at date per language
    as_at_bm: Optional[str]
    online_marker: bool                      # any listed version carries "*"
    repealed_by: Optional[str]               # "Act 805" for "(Repealed by Act 805)", also a partial repeal
    documents: list[LomDocument]
    detail_links: dict[str, str]             # lang -> signed processFile link to the detail page
    versions: list[ListingVersion] = field(default_factory=list)
    status_kind: Optional[str] = None        # repealed | partially_repealed | superseded | not_yet_in_force
    status_marker: Optional[str] = None      # the marker as printed, English line preferred
    superseded_by: Optional[str] = None      # "Act 809" for "(Superseded by / Diganti oleh Akta 809)"
    raw: dict = field(repr=False, default_factory=dict)


@dataclass
class AmendingAct:
    a_number: str                            # "A1727"
    title_bi: Optional[str]
    title_bm: Optional[str]
    project_id: Optional[str]
    royal_assent: Optional[str]              # raw "09/10/2024"
    publication: Optional[str]
    commencement_date: Optional[str]
    commencement_remark: Optional[str]
    documents: list[LomDocument]
    detail_link: Optional[str]
    raw: dict = field(repr=False, default_factory=dict)


@dataclass
class TimelineEntry:
    date: Optional[str]                      # the entry's data-date, dd/mm/yyyy
    display_date: Optional[str]              # "17 Oct 2024"
    log_type: str                            # ORIGINAL | REPRINT | REPRINT ONLINE | AMENDMENTS | SUBSIDIARY_LEGISLATION ...
    project_id: Optional[str]
    file_url: Optional[str]
    publication_date: Optional[str] = None
    royal_assent_date: Optional[str] = None
    commencement_date: Optional[str] = None
    commencement_remark: Optional[str] = None
    pu_no: Optional[str] = None
