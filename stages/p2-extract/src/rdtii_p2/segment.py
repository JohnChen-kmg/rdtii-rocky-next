"""Hierarchy-aware article-boundary detection (PLAN.md section 2.5, kickoff #4).

Deterministic layers only - regex heading detection with structural cues; the
LLM tie-break (PLAN 2.5 layer 5) is deferred until a real ambiguous corpus case
demands it. Naive flat chunkers lose 30-42% of statute sections (NitiBench), so
every span carries its hierarchy path (Act > Part > Division > Section >
Subsection) plus exact char offsets into the frozen source_text.

TOC suppression: statutes open with a table of contents whose lines mirror body
section headings. Candidates are grouped into monotonically non-decreasing runs
of section numbers; the run covering the largest char span is the body - the
TOC run is dense and short and is discarded.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

log = logging.getLogger("rdtii_p2.segment")

# --- heading patterns (country-tunable; defaults cover SG/MY/AU text shapes) ---

_PART = re.compile(r"^PART\s+(\d+[A-Z]?|[IVXLC]+[A-Z]?)\b\s*[—–\-�]?\s*(.*)$", re.M)
_DIVISION = re.compile(r"^Division\s+(\d+[A-Z]?)\s*[—–\-�]?\s*(.*)$", re.M)

# SSO style "26.—(1)" (em-dash may extract as -, --, – or U+FFFD)
_SECTION_WITH_SUB = re.compile(
    r"^(\d{1,3}[A-Z]{0,2})\.\s*[—–�-]{1,2}\s*\((\d+[A-Z]?)\)", re.M
)
# Generic "2. Text..." / MY "2. (1) Text..." - guarded by a following capital or (
_SECTION_PLAIN = re.compile(r"^(\d{1,3}[A-Z]{0,2})\.\s+(?=[(\"'A-Z])", re.M)

# AU OPC compilations head sections WITHOUT a dot, heading on the same line:
# "5B Extra-territorial operation of Act". Fallback only (see segment()) so
# SG/MY corpora never see this looser pattern.
_SECTION_AU = re.compile(r"^(\d{1,3}[A-Z]{0,2}) {1,2}(?=[A-Z(\"'])", re.M)
# "6 June 2026" at line start is a date, never a section heading
_AU_MONTH_HEADING = re.compile(
    r"^(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\b")

# Subsection marker at line start inside a section body ((2AA)-style markers
# carry up to two trailing capitals)
_SUBSECTION = re.compile(r"^\((\d+[A-Z]{0,2})\)\s", re.M)
# regulator notice/guideline decimal paragraphs ("2.1 For the purpose of..."),
# used ONLY by the zero-candidate fallback in segment()
_DECIMAL_PARA = re.compile(r"^(\d{1,2}\.\d{1,2})\s+\S", re.M)

# Schedules end the sectioned body: "FIRST SCHEDULE", "SCHEDULE 2", "THE SCHEDULE"
_SCHEDULE = re.compile(r"^(?:(?:[A-Z]+|THE)\s+)?SCHEDULES?\b(?:\s+\d+)?\s*$", re.M)
# AU OPC style: "Schedule 1—Australian Privacy Principles" (mixed case)
_SCHEDULE_AU = re.compile(r"^Schedule\s+\d+[A-Z]?\s*[—–-]", re.M)

_HEADING_LINE = re.compile(r"^[A-Z][^\n]{2,110}[^.\s]$")


@dataclass
class Span:
    article_section: str          # normalized citation, e.g. "s.26(1)"
    unit: str                     # "section" | "subsection"
    char_start: int
    char_end: int
    heading: str | None = None
    hierarchy: tuple[str, ...] = ()


@dataclass
class _Candidate:
    number: str                   # "26", "15A"
    sub: str | None               # "1" when matched as "26.—(1)"
    start: int
    match_end: int
    # AU no-dot style: the heading shares the number line, so the section's
    # quotable content starts on the NEXT line
    content_start: int | None = None
    heading_inline: str | None = None

    @property
    def numeric(self) -> int:
        digits = re.match(r"\d+", self.number)
        return int(digits.group()) if digits else 0


@dataclass
class SegmentResult:
    spans: list[Span] = field(default_factory=list)
    n_sections: int = 0
    dropped_toc_candidates: int = 0

    def find(self, article_section: str) -> Span | None:
        for span in self.spans:
            if span.article_section == article_section:
                return span
        return None


def _collect_candidates(text: str) -> list[_Candidate]:
    candidates: dict[int, _Candidate] = {}
    for match in _SECTION_WITH_SUB.finditer(text):
        candidates[match.start()] = _Candidate(
            number=match.group(1), sub=match.group(2),
            start=match.start(), match_end=match.end(),
        )
    for match in _SECTION_PLAIN.finditer(text):
        if match.start() not in candidates:
            candidates[match.start()] = _Candidate(
                number=match.group(1), sub=None,
                start=match.start(), match_end=match.end(),
            )
    return [candidates[key] for key in sorted(candidates)]


_AU_ENDNOTES = re.compile(r"(?m)^Endnotes?\b")


def _titles_agree(a: str | None, b: str | None) -> bool:
    """Case/whitespace-folded prefix agreement; permissive when either side
    is missing or too short to be discriminating."""
    if not a or not b:
        return True
    fold_a = re.sub(r"\s+", " ", a).strip().casefold()
    fold_b = re.sub(r"\s+", " ", b).strip().casefold()
    length = min(len(fold_a), len(fold_b), 25)
    if length < 6:
        return True
    return fold_a[:length] == fold_b[:length]


def _collect_candidates_au(text: str) -> list[_Candidate]:
    """Number+heading lines, split into TOC rows (dot leaders within two lines)
    and body candidates. The TOC rows become a per-document index: a body
    candidate whose number+title is not in the contents is a numbered TABLE
    ROW inside a provision, not a section - the Privacy Act's agency table
    would otherwise shadow real sections."""
    # the endnotes SECTION (last match - earlier matches are its own TOC row)
    matches = list(_AU_ENDNOTES.finditer(text))
    cutoff = matches[-1].start() if matches else len(text)
    toc_index: dict[str, list[str]] = {}
    body: list[_Candidate] = []
    for match in _SECTION_AU.finditer(text, 0, cutoff):
        line_end = text.find("\n", match.end())
        if line_end == -1:
            line_end = len(text)
        raw_line = text[match.end():line_end]
        # TOC rows carry dot leaders to a page number - on this line or, when
        # the title wraps, on one of the next two lines
        window_end = line_end
        for _ in range(2):
            next_nl = text.find("\n", window_end + 1)
            window_end = next_nl if next_nl != -1 else len(text)
        if "...." in text[match.end():window_end]:
            title = raw_line.split("....", 1)[0].strip(" .")
            toc_index.setdefault(match.group(1), []).append(title)
            continue
        heading = raw_line.strip()
        if _AU_MONTH_HEADING.match(heading):
            continue
        body.append(_Candidate(
            number=match.group(1), sub=None,
            start=match.start(), match_end=match.end(),
            content_start=min(line_end + 1, len(text)),
            heading_inline=heading or None,
        ))
    if len(toc_index) >= 3:
        body = [
            candidate for candidate in body
            if candidate.number in toc_index
            and any(_titles_agree(candidate.heading_inline, title)
                    for title in toc_index[candidate.number])
        ]
    return body


def _pick_body_au(candidates: list[_Candidate]) -> tuple[list[_Candidate], int]:
    """Contiguous-run picking like _pick_body_run, then stitching: a short
    numbered-table digression inside a section splits the body into runs
    (…1..6][table rows][7..114…) - merge a later run onto the body when its
    head continues the body's tail, and prepend earlier runs the same way.
    Repeated numerals keep their first occurrence."""
    runs: list[list[_Candidate]] = []
    for candidate in candidates:
        if runs and candidate.numeric >= runs[-1][-1].numeric:
            runs[-1].append(candidate)
        else:
            runs.append([candidate])
    if not runs:
        return [], 0

    def coverage(run: list[_Candidate]) -> int:
        return run[-1].start - run[0].start

    body_index = max(range(len(runs)), key=lambda i: coverage(runs[i]))
    body = list(runs[body_index])
    # stitch forward: later runs whose head numeral continues the body tail
    for run in runs[body_index + 1:]:
        if run[0].numeric >= body[-1].numeric:
            body.extend(run)
    # stitch backward: earlier runs whose tail numeral the body head continues
    for run in reversed(runs[:body_index]):
        if run[-1].numeric <= body[0].numeric:
            body = list(run) + body
    seen: set[str] = set()
    body = [candidate for candidate in body
            if not (candidate.number in seen or seen.add(candidate.number))]
    return body, len(candidates) - len(body)


def _pick_body_run(candidates: list[_Candidate]) -> tuple[list[_Candidate], int]:
    """Split candidates into non-decreasing runs; the widest char span is the body."""
    if not candidates:
        return [], 0
    runs: list[list[_Candidate]] = [[candidates[0]]]
    for candidate in candidates[1:]:
        # allow equal (subsection re-match) and forward jumps; break on decrease
        if candidate.numeric >= runs[-1][-1].numeric:
            runs[-1].append(candidate)
        else:
            runs.append([candidate])
    def coverage(run: list[_Candidate]) -> int:
        return run[-1].start - run[0].start
    body = max(runs, key=coverage)
    dropped = sum(len(r) for r in runs) - len(body)
    return body, dropped


def _heading_before(text: str, start: int) -> tuple[str, int] | None:
    """The bold-style heading line immediately above a section-number line,
    plus the offset where that heading line begins. The heading belongs to the
    FOLLOWING section, so the previous span must end before it."""
    if start == 0 or text[start - 1] != "\n":
        return None
    prev_end = start - 1                       # the newline ending the heading line
    prev_start = text.rfind("\n", 0, prev_end) + 1
    line = text[prev_start:prev_end].strip()
    if line and _HEADING_LINE.match(line) and not _SECTION_PLAIN.match(line + " X"):
        return line, prev_start
    return None


# schedule CLAUSE styles: decimal ("8.1 Before an APP entity...", APP/CIRMP
# style) and plain-numbered ("1 Heading" / "1. Text") within a schedule region
_SCHED_CLAUSE_DECIMAL = re.compile(r"^(\d{1,3}[A-Z]?\.\d{1,2}[A-Z]?)\s+\S", re.M)
_ORDINAL_SCHEDULES = {
    "FIRST": "1", "SECOND": "2", "THIRD": "3", "FOURTH": "4", "FIFTH": "5",
    "SIXTH": "6", "SEVENTH": "7", "EIGHTH": "8", "NINTH": "9", "TENTH": "10",
    "THE": "1",
}


def _schedule_regions(text: str, cutoff: int) -> list[tuple[str, str, int, int]]:
    """(number, title, start, end) per schedule BODY. Statutes print each
    schedule heading twice (contents + body) - the LAST occurrence of a given
    schedule number before the endnotes is the body (same trick the endnotes
    cutoff uses)."""
    heads: dict[str, tuple[int, str]] = {}
    for match in _SCHEDULE_AU.finditer(text, 0, cutoff):
        line_end = text.find("\n", match.start())
        line = text[match.start():line_end if line_end != -1 else cutoff]
        number_match = re.match(r"Schedule\s+(\d+[A-Z]?)", line)
        if number_match is None:
            continue
        title = re.sub(r"^Schedule\s+\d+[A-Z]?\s*[—–-]\s*", "", line).strip()
        heads[number_match.group(1)] = (match.start(), title)
    for match in _SCHEDULE.finditer(text, 0, cutoff):
        line = match.group(0).strip()
        digits = re.search(r"(\d+)", line)
        word = line.split()[0] if line.split() else ""
        number = digits.group(1) if digits else _ORDINAL_SCHEDULES.get(word)
        if number:
            heads.setdefault(number, (match.start(), line))
    regions = sorted((start, number, title) for number, (start, title) in heads.items())
    out: list[tuple[str, str, int, int]] = []
    for index, (start, number, title) in enumerate(regions):
        end = regions[index + 1][0] if index + 1 < len(regions) else cutoff
        out.append((number, title, start, end))
    return out


def _schedule_spans(text: str, cutoff: int) -> list[Span]:
    """Segment schedule CONTENT (previously schedules only TERMINATED spans, so
    schedule text - incl. the Privacy Act APPs - could never yield provisions).
    Clause ids: "sch.1 cl.8.1", or "sch.1 APP 8.1" when the schedule titles
    itself Australian Privacy Principles. Engages per region only with >=3
    clause markers, so stub/amendment schedules stay unsegmented (disclosed)."""
    spans: list[Span] = []
    for number, title, start, end in _schedule_regions(text, cutoff):
        if end - start < 2000:
            continue
        region = text[start:end]
        label = f"Schedule {number}" + (f" — {title}" if title else "")
        is_app = "australian privacy principle" in title.lower()
        clauses = list(_SCHED_CLAUSE_DECIMAL.finditer(region))
        style = "decimal"
        if len(clauses) < 3:
            clauses = [m for m in _SECTION_PLAIN.finditer(region)]
            style = "plain"
        if len(clauses) < 3:
            clauses = [m for m in _SECTION_AU.finditer(region)
                       if not _AU_MONTH_HEADING.match(
                           region[m.end():m.end() + 20])]
            style = "au"
        if len(clauses) < 3:
            continue
        seen: set[str] = set()
        for index, match in enumerate(clauses):
            clause_no = match.group(1)
            citation = (f"sch.{number} APP {clause_no}" if is_app
                        else f"sch.{number} cl.{clause_no}")
            if citation in seen:
                continue
            seen.add(citation)
            clause_end = (clauses[index + 1].start()
                          if index + 1 < len(clauses) else len(region))
            spans.append(Span(
                article_section=citation, unit="section",
                char_start=start + match.start(),
                char_end=start + clause_end,
                heading=None,
                hierarchy=(label, citation),
            ))
        log.info("schedule %s: %d clause spans (%s style)%s",
                 number, len(seen), style, " [APP]" if is_app else "")
    return spans


def _structure_markers(text: str) -> list[tuple[int, str, str]]:
    """(offset, kind, label) for PART / Division headings, in document order."""
    markers: list[tuple[int, str, str]] = []
    for match in _PART.finditer(text):
        title = match.group(2).strip()
        # all-caps title often sits on the following line
        if not title:
            following = text[match.end():match.end() + 120].lstrip("\n")
            first_line = following.split("\n", 1)[0].strip()
            if first_line.isupper():
                title = first_line
        label = f"Part {match.group(1)}" + (f" — {title}" if title else "")
        markers.append((match.start(), "part", label))
    for match in _DIVISION.finditer(text):
        label = f"Division {match.group(1)}"
        if match.group(2).strip():
            label += f" — {match.group(2).strip()}"
        markers.append((match.start(), "division", label))
    markers.sort()
    return markers


def _hierarchy_at(markers: list[tuple[int, str, str]], offset: int) -> tuple[str, ...]:
    part = division = None
    for marker_offset, kind, label in markers:
        if marker_offset > offset:
            break
        if kind == "part":
            part, division = label, None
        else:
            division = label
    return tuple(x for x in (part, division) if x)


def segment(text: str) -> SegmentResult:
    """Frozen source_text -> section + subsection spans with hierarchy paths."""
    result = SegmentResult()
    candidates = _collect_candidates(text)
    body, dropped = _pick_body_run(candidates)
    # Fallback for AU OPC no-dot headings: engaged only when the dot pattern
    # finds (nearly) nothing, so a well-segmented SG/MY doc never switches.
    if len(body) < 5:
        au_body, au_dropped = _pick_body_au(_collect_candidates_au(text))
        if len(au_body) > len(body):
            log.info("AU-style no-dot headings: %d sections (dot pattern found %d)",
                     len(au_body), len(body))
            body, dropped = au_body, au_dropped
    result.dropped_toc_candidates = dropped
    if not body:
        # Regulator notices/guidelines (MAS notices, some PDPC/APRA guidance)
        # number paragraphs decimally ("2.1", "4.6") under unnumbered part
        # headings - no statute pass matches. Engaged ONLY when every other
        # pass found zero candidates, so no statute doc can switch shapes.
        decimal_markers = list(_DECIMAL_PARA.finditer(text))
        if len(decimal_markers) >= 5:
            log.info("decimal-paragraph fallback: %d markers "
                     "(regulator notice/guideline shape)", len(decimal_markers))
            seen: set[str] = set()
            for index, match in enumerate(decimal_markers):
                citation = f"para {match.group(1)}"
                if citation in seen:
                    continue  # repeated marker (e.g. a contents row) - keep first
                seen.add(citation)
                end = (decimal_markers[index + 1].start()
                       if index + 1 < len(decimal_markers) else len(text))
                result.spans.append(Span(
                    article_section=citation, unit="section",
                    char_start=match.start(), char_end=end,
                    heading=None, hierarchy=(citation,),
                ))
                result.n_sections += 1
            _append_schedule_spans(result, text)
            log.info("segmented: %d sections, %d spans total, %d TOC/front-matter "
                     "candidates dropped", result.n_sections, len(result.spans),
                     result.dropped_toc_candidates)
            return result
        _append_schedule_spans(result, text)
        if not result.spans:
            log.warning("segmentation found no section candidates")
        return result

    markers = _structure_markers(text)
    # Part AND Division headings close the preceding section; Schedule blocks
    # end the sectioned body entirely (their front matter is not provision text)
    endnote_matches = list(_AU_ENDNOTES.finditer(text))
    closer_offsets = sorted(
        [offset for offset, _kind, _label in markers]
        + [match.start() for match in _SCHEDULE.finditer(text)]
        + [match.start() for match in _SCHEDULE_AU.finditer(text)]
        # the endnotes SECTION (last match) ends the final provision's span
        + ([endnote_matches[-1].start()] if endnote_matches else [])
    )

    heads = [_heading_before(text, candidate.start) for candidate in body]
    # a section span ends where the NEXT section visually begins - at its
    # bold heading line when it has one, not at its number line
    visual_starts = [
        head[1] if head else candidate.start
        for head, candidate in zip(heads, body)
    ]

    for index, candidate in enumerate(body):
        section_end = visual_starts[index + 1] if index + 1 < len(body) else len(text)
        for closer in closer_offsets:
            if candidate.start < closer < section_end:
                section_end = closer
                break
        head = heads[index]
        heading = candidate.heading_inline or (head[0] if head else None)
        hierarchy = _hierarchy_at(markers, candidate.start)
        section_citation = f"s.{candidate.number}"

        result.spans.append(Span(
            article_section=section_citation,
            unit="section",
            char_start=(candidate.content_start
                        if candidate.content_start is not None else candidate.start),
            char_end=section_end,
            heading=heading,
            hierarchy=hierarchy + (section_citation,),
        ))
        result.n_sections += 1

        # --- subsections within the section body ---
        section_text = text[candidate.start:section_end]
        sub_matches = list(_SUBSECTION.finditer(section_text))
        subs: list[tuple[str, int]] = []
        if candidate.sub is not None:
            # inline first subsection: "26.—(1)" - span starts at the section start
            subs.append((candidate.sub, 0))
        for match in sub_matches:
            offset = match.start()
            if candidate.sub is not None and offset == 0:
                continue
            subs.append((match.group(1), offset))
        for sub_index, (sub_number, sub_offset) in enumerate(subs):
            sub_start = candidate.start + sub_offset
            sub_end = (
                candidate.start + subs[sub_index + 1][1]
                if sub_index + 1 < len(subs) else section_end
            )
            citation = f"s.{candidate.number}({sub_number})"
            result.spans.append(Span(
                article_section=citation,
                unit="subsection",
                char_start=sub_start,
                char_end=sub_end,
                heading=heading,
                hierarchy=hierarchy + (section_citation, f"({sub_number})"),
            ))

    _append_schedule_spans(result, text)
    log.info(
        "segmented: %d sections, %d spans total, %d TOC/front-matter candidates dropped",
        result.n_sections, len(result.spans), result.dropped_toc_candidates,
    )
    return result


def _append_schedule_spans(result: SegmentResult, text: str) -> None:
    endnote_matches = list(_AU_ENDNOTES.finditer(text))
    cutoff = endnote_matches[-1].start() if endnote_matches else len(text)
    schedule_spans = _schedule_spans(text, cutoff)
    result.spans.extend(schedule_spans)
    result.n_sections += len(schedule_spans)
