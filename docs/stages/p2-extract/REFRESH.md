# Taking a new batch from collection

**Written 2026-09-24.** Collection publishes each batch as
`outputs/<CC>/<CC>_corpus_<YYYY-MM-DD>/`. A new batch is mostly the old one — a few new
instruments, a few re-fetched, the rest byte-identical — so the job is to extract what changed
and leave the rest alone. Nothing about the output format changes: same four artefacts, same
fields, same contract version.

## The whole procedure

```
python tools/import_corpora.py            # pull the newest batch in, hash it
python tools/refresh.py                   # what changed? reads only, writes nothing
python tools/refresh.py --run             # extract the new and changed documents
python tools/render_law_titles.py --all   # fill law_name_en for any new titles
```

Then verify, per economy:

```
python -m rdtii_p2.cli validate --provisions out/<CC>/provisions.jsonl \
    --source-text out/<CC>/source_text --laws out/<CC>/laws.jsonl
```

## What each step will and will not do

### `import_corpora.py` — finds the batch, never guesses its name

The corpus folder is **discovered**, not written down. Collection dates every batch, so a
hardcoded `LA_corpus_2026-09-21` would silently import nothing the moment a new one lands, and
report success over a stale corpus. `latest_batch()` picks the newest by the date **in the
folder name** — not by mtime, because a re-import or a file touch changes mtime and would
promote an older batch.

Where collection's workshop is, in order: `--scrape`, then `$RDTII_SCRAPE_DIR`, then a sibling
directory named `rdtii-finale-1-scraping`. No absolute path is compiled in.

`--verify` re-hashes without copying and prints `DRIFT` for any metadata file whose bytes no
longer match what was imported. Run it before trusting an old corpus.

`raw/` is a directory junction, not a copy — 9.2 GB that must stay byte-identical to what
collection stored, so there is one copy of it.

### `refresh.py` — decides by content hash, not by date

| Class | Meaning | Action |
| :---- | :---- | :---- |
| `new` | in the manifest, never extracted | extract |
| `changed` | extracted before, `content_sha256` differs | extract, replacing its rows |
| `unchanged` | same bytes, already has a `doc_status` row | skip |
| `withdrawn` | extracted before, gone from the manifest | **reported, not deleted** |

**Why the hash.** A re-crawl rewrites `access_date` on every row, so comparing dates marks the
entire corpus changed. `content_sha256` is what collection computed over the bytes and is the
only field that answers "is this the same document".

**Withdrawn documents are never removed automatically.** A document vanishing can mean
collection dropped it, or that a crawl failed and the batch is short. Those are opposite
situations and the difference is not visible from here. `--prune` acts once someone has looked.

**`--baseline`** records the current manifest hashes as already extracted. Run it once on output
produced before this tool existed, otherwise the first refresh calls everything changed.

### Why a partial run is safe

None of this is new machinery; it is what the stage already does:

* `emit._merge_jsonl` replaces rows for the `doc_id`s this run processed and keeps every other
  row, so extracting one document does not truncate the corpus. **Verified**: re-extracting a
  single Singapore document left 110,661 provisions, 717 documents, 738 law rows and 738
  doc_status rows exactly as they were, with 0 duplicate ids.
* the OCR page cache is keyed on the file's own sha256, the engine, the language and the DPI, so
  a re-fetched scan re-OCRs itself and an untouched one costs nothing.
* `out/_title_cache.json` is keyed on (title, model), so only genuinely new titles are rendered.
* a row annotated `superseded by` is dropped at ingest, and `refresh` applies the same rule, so
  it is not reported as permanently new.

**Do not use `--fresh` for a refresh.** It clears the outputs — correct for a clean rebuild,
wasteful here. It does keep the OCR cache.

## If the batch brings something genuinely new

| What arrives | What to do |
| :---- | :---- |
| A new economy | add it to `corpus/economies.json` (language, segmenter, OCR pack) and to `ECONOMIES` in `import_corpora.py`. `run_economy.py` reads the registry, so nothing else changes |
| A new language | add the Tesseract pack to `config/ocr/langmap.py`, a segmenter profile to `segment_civil.PROFILES`, and a tagging model to `config/llm/tagmap.py`. Each fails loudly rather than defaulting to English |
| A new portal (HTML) | register its host in `parse_html.PORTAL_PARSERS`. Matching is on the host with the most specific registered host winning, so registration order does not matter |
| A new file type | add it to `router.LANE_BY_TYPE` and give it a reader. Lanes today: A html, B pdf_native, C pdf_scanned, D docx |
| Scanned documents | run `p2-extract ocr` first — the parallel pre-pass, ~16 pages/s at 16 workers. In the run loop it is one page at a time |

## What stays the same, whatever arrives

The output contract. `provisions.jsonl`, `laws.jsonl`, `doc_status.jsonl` and
`source_text/<doc_id>.txt`, at contract **0.3.0**, with the same fields for every economy. A new
batch cannot change the shape of what stage 3 reads — only the rows in it.

The grounding rule holds regardless: `verbatim_snippet` is a character-exact substring of the
frozen text at the recorded offsets, re-verified before the record is written, and a provision
that cannot be grounded is not emitted.
