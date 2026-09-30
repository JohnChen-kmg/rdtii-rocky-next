"""The codebook file as text: a header, then one block per indicator in host order, grouped by pillar.

output/indicators.yaml holds every in-scope indicator in one `indicators:` list, ordered as in
output/indicator_order.yaml, with a comment banner above each pillar's first block. How deep a
block goes is the block's `tier` field (A, B or C); where the block sits says nothing about it.

split() cuts the file into its header, its pillar banners and the raw text of each block;
assemble() puts them back in host order. Blocks travel as text, so adding or moving one never
re-formats the others or drops their comments.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import yaml

BLOCK_START = re.compile(r"""^  - id: ["']?(\d[\d.]*)["']?\s*(?:#.*)?$""")
PILLAR_BANNER = re.compile(r"^# PILLAR (\d+)\b")
RULE = "# " + "-" * 76


@dataclass
class Codebook:
    header: str                                              # everything above `indicators:`
    banners: dict[int, str] = field(default_factory=dict)    # pillar -> banner comment lines
    blocks: dict[str, str] = field(default_factory=dict)     # indicator ID -> block text


def split(text: str) -> Codebook:
    lines = text.splitlines(keepends=True)
    try:
        start = next(i for i, ln in enumerate(lines) if ln.rstrip("\r\n") == "indicators:")
    except StopIteration:
        raise ValueError("codebook has no top-level 'indicators:' line") from None

    head, pending = lines[:start], []
    j = len(head)
    while j > 0 and (head[j - 1].startswith("#") or not head[j - 1].strip()):
        j -= 1
    if any(PILLAR_BANNER.match(ln) for ln in head[j:]):   # a pillar banner just above the list
        head, pending = head[:j], head[j:]
    cb = Codebook(header="".join(head).rstrip() + "\n\n")

    current: str | None = None
    buf: list[str] = []

    def close_block() -> None:
        if current is None:
            return
        if current in cb.blocks:
            raise ValueError(f"indicator {current} has two blocks")
        cb.blocks[current] = "".join(buf).rstrip() + "\n"

    def close_comments(group: list[str]) -> None:
        # Keep pillar banners. Any other column-0 comment group between blocks is dropped.
        hit = next((m for m in map(PILLAR_BANNER.match, group) if m), None)
        if hit:
            cb.banners[int(hit.group(1))] = "".join(group).strip() + "\n"

    for line in lines[start + 1:]:
        m = BLOCK_START.match(line.rstrip("\r\n"))
        if m:
            close_block()
            close_comments(pending)
            current, buf, pending = m.group(1), [line], []
        elif line.startswith("#"):
            pending.append(line)
        elif not line.strip():
            (pending if pending else buf).append(line)
        elif pending:
            raise ValueError(f"block {current}: content after a column-0 comment: {line!r}")
        else:
            buf.append(line)
    close_block()
    close_comments(pending)
    return cb


def default_banner(pillar: int, label: str) -> str:
    name = label.split(":", 1)[1].strip() if ":" in label else label
    return f"{RULE}\n# PILLAR {pillar} — {name.upper()}\n{RULE}\n"


def assemble(cb: Codebook, order: list[dict]) -> str:
    """Header, then for each pillar its banner and its blocks, all in host order.

    `order` is the `indicators` list of indicator_order.yaml. IDs without a block are skipped;
    a block whose ID is not in scope raises.
    """
    in_scope = {e["id"] for e in order if e["status"] == "in_scope"}
    stray = sorted(set(cb.blocks) - in_scope)
    if stray:
        raise ValueError(f"blocks for IDs that are not in scope: {stray}")
    out, pillar = [cb.header, "indicators:\n"], None
    for e in order:
        if e["id"] not in cb.blocks:
            continue
        if e["pillar"] != pillar:
            pillar = e["pillar"]
            out.append("\n" + (cb.banners.get(pillar) or default_banner(pillar, e["pillar_label"])))
        out.append("\n" + cb.blocks[e["id"]])
    return "".join(out)


def id_line(iid: str) -> str:
    """The first line of a block. IDs are always double-quoted, so none reads as a number."""
    return f'  - id: "{iid}"\n'


def render_block(block: dict) -> str:
    """A script-made block as list-item text in the codebook's layout (two-space indent)."""
    lines = yaml.safe_dump([block], allow_unicode=True, sort_keys=False, width=100).splitlines(keepends=True)
    if not lines[0].startswith("- id:"):
        raise ValueError(f"block must start with its id: {lines[0]!r}")
    return id_line(str(block["id"])) + "".join(("  " + ln if ln.strip() else ln) for ln in lines[1:])
