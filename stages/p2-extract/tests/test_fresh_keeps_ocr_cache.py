"""`--fresh` clears the outputs and must never clear the OCR page cache.

On 2026-09-23 `tools/run_economy.py --fresh` ran `shutil.rmtree(out)`, and `out/LA/ocr/`
lives inside `out`. That deleted 19,054 cached Lao pages - 20.8 minutes of 16-way parallel
OCR - and the run then re-read them one page at a time inside the single-threaded extraction
loop, which is roughly a fourteen-hour job. Nothing failed and nothing warned; the run simply
got slower by two orders of magnitude, and the only visible symptom was a document count that
crept instead of climbing.

Keeping the cache costs nothing in correctness: `ocr_cache.read` keys on the file's sha256,
the engine, the language and the DPI, so an entry that no longer matches is re-OCR'd by
itself. Only `cer_report.json` is a run artefact rather than cache, so only that is removed.

The test drives the real function from `tools/run_economy.py` rather than a copy of it.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

def _tools_dir() -> pathlib.Path:
    """`tools/` sits beside the stage in the repository and one level up in the workshop."""
    here = pathlib.Path(__file__).resolve()
    for parent in (here.parents[1], here.parents[2]):
        if (parent / "tools" / "run_economy.py").is_file():
            return parent / "tools"
    return here.parents[2] / "tools"


TOOLS = _tools_dir()


def _load_run_economy():
    spec = importlib.util.spec_from_file_location("run_economy", TOOLS / "run_economy.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_economy"] = module
    spec.loader.exec_module(module)
    return module


def _make_out(root: pathlib.Path) -> pathlib.Path:
    """An output folder shaped like a real one: results, and a populated page cache."""
    out = root / "LA"
    (out / "source_text").mkdir(parents=True)
    (out / "by_law").mkdir()
    (out / "source_text" / "la-1-001.txt").write_text("frozen", encoding="utf-8")
    (out / "provisions.jsonl").write_text('{"provision_id": "la-1-001#Art. 1"}\n',
                                          encoding="utf-8")
    for doc in ("la-1-001", "la-2-001"):
        cache = out / "ocr" / doc
        cache.mkdir(parents=True)
        (cache / "meta.json").write_text('{"doc_id": "%s"}' % doc, encoding="utf-8")
        (cache / "page_0001.txt").write_text("ມາດຕາ 1", encoding="utf-8")
        (cache / "cer_report.json").write_text("{}", encoding="utf-8")
    return out


def _fresh(out: pathlib.Path) -> str:
    """Run only the --fresh block, the way run_economy.main does."""
    module = _load_run_economy()
    source = (TOOLS / "run_economy.py").read_text(encoding="utf-8")
    start = source.index("    if args.fresh and out.exists():")
    end = source.index("    out.mkdir(parents=True, exist_ok=True)", start)
    block = "\n".join(line[4:] for line in source[start:end].splitlines())
    printed: list[str] = []
    namespace = {"args": type("A", (), {"fresh": True})(), "out": out,
                 "shutil": module.shutil, "print": lambda *a: printed.append(" ".join(map(str, a)))}
    exec(compile(block, "run_economy:fresh", "exec"), namespace)
    return "\n".join(printed)


def test_fresh_keeps_the_page_cache_and_clears_everything_else(tmp_path):
    out = _make_out(tmp_path)
    message = _fresh(out)

    # the expensive, content-addressed part survives
    assert (out / "ocr" / "la-1-001" / "meta.json").is_file()
    assert (out / "ocr" / "la-1-001" / "page_0001.txt").read_text(encoding="utf-8") == "ມາດຕາ 1"
    assert (out / "ocr" / "la-2-001" / "page_0001.txt").is_file()

    # the outputs do not
    assert not (out / "provisions.jsonl").exists()
    assert not (out / "source_text").exists()
    assert not (out / "by_law").exists()

    # a run artefact inside the cache folder is still a run artefact
    assert not (out / "ocr" / "la-1-001" / "cer_report.json").exists()

    assert "kept 2 cached OCR document(s)" in message


def test_fresh_on_an_output_folder_with_no_cache_says_nothing(tmp_path):
    out = tmp_path / "SG"
    out.mkdir()
    (out / "provisions.jsonl").write_text("{}\n", encoding="utf-8")
    message = _fresh(out)
    assert not (out / "provisions.jsonl").exists()
    assert message == ""


@pytest.mark.parametrize("name", ["logs", "cost_report.json", "doc_status.csv"])
def test_every_other_top_level_entry_is_removed(tmp_path, name):
    out = tmp_path / "TL"
    (out / "ocr").mkdir(parents=True)
    target = out / name
    if "." in name:
        target.write_text("x", encoding="utf-8")
    else:
        target.mkdir()
        (target / "run.jsonl").write_text("x", encoding="utf-8")
    _fresh(out)
    assert not target.exists()


def test_fresh_keeps_the_refresh_baseline(tmp_path):
    """`extracted_hashes.json` is state, not output.

    It is what `tools/refresh.py` compares an incoming batch against. Deleting it makes the
    next batch report every document as changed - on Lao that is 20 minutes of OCR and an hour
    of extraction, silently redone - which is exactly the trap the OCR cache was in.
    """
    out = _make_out(tmp_path)
    (out / "extracted_hashes.json").write_text('{"la-1-001": "abc"}', encoding="utf-8")
    _fresh(out)
    assert (out / "extracted_hashes.json").read_text(encoding="utf-8") == '{"la-1-001": "abc"}'
    assert not (out / "provisions.jsonl").exists()      # outputs still go
