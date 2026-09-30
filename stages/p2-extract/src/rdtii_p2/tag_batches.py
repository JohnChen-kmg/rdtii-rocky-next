"""Anthropic Batches API tagging lane (the corpus-scale path, decision 2026-07-12).

Two-phase flow:
  1. `p2-extract run --skip-tags`   -> untagged records + tag_inputs.jsonl
  2. `p2-extract tag-corpus`        -> pack ~TAG_BATCH_SIZE provisions per
     request, submit one (or more) message batches, poll until ended, map the
     tool_use results back by provision id, rewrite provisions.jsonl/by_law.

Grounding is untouched: tags are the only fields this module writes, and it
reuses the exact prompt bytes of the interactive path (extract_fields), so the
sync path, the local path, and the batch path stay semantically identical.
Requests that error/expire are retried synchronously via the plain client -
worst case degrades to the proven one-provision path, never to silence.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config.settings import Settings
from rdtii_p2 import emit, extract_fields
from rdtii_p2.segment import Span

log = logging.getLogger("rdtii_p2.tag_batches")

MAX_REQUESTS_PER_BATCH = 90_000  # API cap is 100k; headroom for safety
MAX_TOKENS_PER_REQUEST = 2048
BATCH_DISCOUNT = 0.5

STATE_FILE = "tag_batch_state.json"
TAG_INPUTS_FILE = "tag_inputs.jsonl"


# ------------------------------------------------------------- pack phase ----

@dataclass
class Chunk:
    custom_id: str
    doc_id: str
    law_name: str | None
    rows: list[dict[str, Any]]  # tag_inputs rows, prompt order

    @property
    def ids(self) -> list[str]:
        return [row["article_section"] for row in self.rows]


def _row_to_item(row: dict[str, Any]) -> extract_fields.TagItem:
    span = Span(
        article_section=row["article_section"],
        unit="provision",
        char_start=0,
        char_end=0,
        heading=row.get("heading"),
        hierarchy=tuple(row.get("hierarchy") or ()),
    )
    return (span, row["snippet"], row.get("context_before") or "")


def load_tag_inputs(out_dir: Path) -> list[dict[str, Any]]:
    path = out_dir / TAG_INPUTS_FILE
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} missing - run `p2-extract run --skip-tags` first")
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def make_chunks(rows: list[dict[str, Any]], batch_size: int) -> list[Chunk]:
    """Group rows per doc (one statute per prompt), then chunk within the doc."""
    size = max(1, batch_size)
    by_doc: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_doc.setdefault(row["doc_id"], []).append(row)
    chunks: list[Chunk] = []
    for doc_id, doc_rows in by_doc.items():
        for start in range(0, len(doc_rows), size):
            part = doc_rows[start:start + size]
            chunks.append(Chunk(
                custom_id=f"c{len(chunks):06d}",
                doc_id=doc_id,
                law_name=part[0].get("law_name"),
                rows=part,
            ))
    return chunks


def chunk_params(chunk: Chunk, model: str) -> dict[str, Any]:
    """Messages-create params for one chunk - same forced-tool shape as the
    sync AnthropicClient so batch results parse identically."""
    items = [_row_to_item(row) for row in chunk.rows]
    if len(items) == 1:
        span, snippet, before = items[0]
        prompt = extract_fields._tag_prompt(chunk.law_name, span, snippet, before)
        schema = extract_fields.TAG_SCHEMA
    else:
        prompt = extract_fields._batch_tag_prompt(chunk.law_name, items)
        schema = extract_fields._batch_schema(chunk.ids)
    return {
        "model": model,
        "max_tokens": MAX_TOKENS_PER_REQUEST,
        "tools": [{
            "name": "emit_result",
            "description": "Return the structured extraction result.",
            "input_schema": schema,
        }],
        "tool_choice": {"type": "tool", "name": "emit_result"},
        "messages": [{"role": "user", "content": prompt}],
    }


# ----------------------------------------------------------- submit / poll ----

def submit(client, chunks: list[Chunk], model: str) -> list[str]:
    batch_ids: list[str] = []
    for start in range(0, len(chunks), MAX_REQUESTS_PER_BATCH):
        part = chunks[start:start + MAX_REQUESTS_PER_BATCH]
        batch = client.messages.batches.create(requests=[
            {"custom_id": chunk.custom_id, "params": chunk_params(chunk, model)}
            for chunk in part
        ])
        log.info("submitted batch %s: %d requests", batch.id, len(part))
        batch_ids.append(batch.id)
    return batch_ids


def save_state(out_dir: Path, state: dict[str, Any]) -> None:
    (out_dir / STATE_FILE).write_text(
        json.dumps(state, indent=2), encoding="utf-8")


def load_state(out_dir: Path) -> dict[str, Any]:
    path = out_dir / STATE_FILE
    if not path.is_file():
        raise FileNotFoundError(f"{path} missing - nothing submitted yet?")
    return json.loads(path.read_text(encoding="utf-8"))


def poll_until_ended(client, batch_ids: list[str], interval_seconds: int) -> None:
    pending = list(batch_ids)
    while pending:
        for batch_id in list(pending):
            batch = client.messages.batches.retrieve(batch_id)
            counts = batch.request_counts
            log.info("%s: %s (ok=%d err=%d processing=%d)",
                     batch_id, batch.processing_status,
                     counts.succeeded, counts.errored, counts.processing)
            if batch.processing_status == "ended":
                pending.remove(batch_id)
        if pending:
            time.sleep(interval_seconds)


# ------------------------------------------------------------ apply phase ----

def _tool_input(entry) -> dict[str, Any] | None:
    if entry.result.type != "succeeded":
        return None
    for block in entry.result.message.content:
        if block.type == "tool_use":
            return dict(block.input)
    return None


def collect_tags(client, batch_ids: list[str], chunks: list[Chunk]
                 ) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Returns (tags by provision_id, leftover tag_input rows, token usage)."""
    by_custom_id = {chunk.custom_id: chunk for chunk in chunks}
    tags: dict[str, dict[str, Any]] = {}
    leftovers: list[dict[str, Any]] = []
    usage = {"input_tokens": 0, "output_tokens": 0}
    for batch_id in batch_ids:
        for entry in client.messages.batches.results(batch_id):
            chunk = by_custom_id.get(entry.custom_id)
            if chunk is None:
                log.warning("unknown custom_id %s in batch results", entry.custom_id)
                continue
            matched = None
            try:
                payload = _tool_input(entry)
                if entry.result.type == "succeeded":
                    usage["input_tokens"] += entry.result.message.usage.input_tokens
                    usage["output_tokens"] += entry.result.message.usage.output_tokens
                if payload is not None:
                    entries = payload["provisions"] if "provisions" in payload else [
                        {**payload, "id": chunk.ids[0]}]
                    # models occasionally emit the array (or an element) as a
                    # JSON string despite the schema - coerce, never crash
                    if isinstance(entries, str):
                        entries = json.loads(entries)
                    entries = [json.loads(e) if isinstance(e, str) else e
                               for e in entries]
                    matched = extract_fields.match_batch_entries(chunk.ids, entries)
            except Exception as exc:
                log.warning("%s (%s): result parse failed (%s) - queued for sync retry",
                            entry.custom_id, chunk.doc_id, exc)
            if matched is None:
                log.warning("%s (%s): unusable result (%s) - queued for sync retry",
                            entry.custom_id, chunk.doc_id, entry.result.type)
                leftovers.extend(chunk.rows)
                continue
            for row, tag in zip(chunk.rows, matched):
                tags[row["provision_id"]] = tag
    return tags, leftovers, usage


def retry_sync(llm, leftovers: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """One-provision sync calls for rows whose batch request failed."""
    tags: dict[str, dict[str, Any]] = {}
    for row in leftovers:
        span, snippet, before = _row_to_item(row)
        tags[row["provision_id"]] = extract_fields.llm_tags(
            llm, row.get("law_name"), span, snippet, before)
    return tags


def apply_tags(out_dir: Path, tags: dict[str, dict[str, Any]], model: str) -> tuple[int, int]:
    """Rewrite provisions.jsonl + by_law with tags; stamp the tagging model.
    Returns (updated, missing) counts."""
    provisions_path = out_dir / "provisions.jsonl"
    with open(provisions_path, encoding="utf-8") as fh:
        records = [json.loads(line) for line in fh if line.strip()]
    updated = 0
    for record in records:
        tag = tags.get(record["provision_id"])
        if tag is None:
            # A provision this lane did not tag keeps its untagged state - null tags and
            # no model. It must never inherit the model name from a record beside it.
            continue
        for key in ("scope", "data_type", "obligation_type", "extraction_confidence"):
            record[key] = tag[key]
        extract_fields.stamp_tagging_model(record, model, tag["extraction_confidence"])
        updated += 1
    emit.write_provisions(out_dir, records, {record["doc_id"] for record in records})
    return updated, len(tags) - updated


def update_cost_report(out_dir: Path, settings: Settings, model: str,
                       usage: dict[str, int], wallclock_seconds: float,
                       n_provisions: int) -> dict[str, Any]:
    from rdtii_p2.cli import _API_PRICES_PER_MTOK

    prices = _API_PRICES_PER_MTOK.get(model)
    usd = None
    if prices:
        usd = round((usage["input_tokens"] / 1e6 * prices[0]
                     + usage["output_tokens"] / 1e6 * prices[1]) * BATCH_DISCOUNT, 4)
    report_path = out_dir / "cost_report.json"
    report = (json.loads(report_path.read_text(encoding="utf-8"))
              if report_path.is_file() else {})
    entry = {
        "llm_model": model,
        "provisions_tagged": n_provisions,
        "llm_tokens": usage,
        "wallclock_seconds": round(wallclock_seconds, 2),
        "estimated_usd_with_batch_discount": usd,
    }
    # cumulative history - every batch is judge-facing cost evidence, so a
    # later batch must never overwrite an earlier one's measured numbers
    history = report.get("tagging_batches")
    if isinstance(history, dict):
        history = [history]
    history = (history or []) + [entry]
    report["tagging_batches"] = history
    report["tagging_total_usd"] = round(
        sum(e["estimated_usd_with_batch_discount"] or 0 for e in history), 4)
    emit.write_cost_report(out_dir, report)
    return entry
