"""Which local model tags a provision, chosen by the document's own language.

The tag prompt asks a model to read a `verbatim_snippet` **in its source language** and decide
scope, data_type and obligation_type. So the question is not "which model is best" but "which
model reads this script", and the answer is not the same for Lao as for English. Round 1 used a
single global `LLM_MODEL` for every economy, the same shape of mistake that had every Lao page
read as English until `config/ocr/langmap.py` made the OCR language a per-document fact.

**What was actually measured** (`evidence/2026-09-23_translation_comparison.md`):

  * **Lao is the only language with a scored winner.** Against the gazette's own published
    English, `gemma3:12b` reached chrF 0.658 and `qwen2.5:14b` 0.561 - 82% against 70% of the
    0.807 ceiling that a same-meaning re-translation scores. gemma3 also fixed both of qwen's
    substantive errors: qwen rendered "ປອດພາສີ" (duty-free) as "free", losing that the article
    is about customs at all, and hardened "promotes" into "shall promote", which turns a policy
    statement into a binding obligation - exactly the distinction `obligation_type` encodes.
  * **Portuguese and Chinese have NO measured winner.** What was measured there is the two
    models' *agreement with each other* - 0.846 and 0.836 - which says they say the same thing,
    not which is right. Picking gemma3 for those would be inventing a result.

**Two honest limits on all of this.** It measures *translation*, and tagging is a different task;
treating one as a proxy for the other is an inference, not a measurement. And `qwen2.5:14b` is
Apache-2.0 where Gemma carries its own terms, which matters for a submission that declares its
engines local and open. So gemma3 is used where it was measured to be better, and nowhere else.
"""

from __future__ import annotations

import logging

log = logging.getLogger("config.llm.tagmap")

DEFAULT_TAGGER = "qwen2.5:14b"

# ISO 639-3 (what the crawler writes) -> the Ollama model that reads it.
# `why` is carried so a reviewer can tell a measured choice from an inherited default.
LANGUAGE_TO_TAGGER: dict[str, tuple[str, str]] = {
    "lao": ("gemma3:12b", "measured: chrF 0.658 vs qwen2.5:14b 0.561 on 12 Lao articles"),
    "por": (DEFAULT_TAGGER, "default: the two models agree at 0.846, neither measured better"),
    "zho": (DEFAULT_TAGGER, "default: the two models agree at 0.836, neither measured better"),
    "eng": (DEFAULT_TAGGER, "default: incumbent, Apache-2.0, no script barrier"),
    "msa": (DEFAULT_TAGGER, "default: incumbent; Malaysia's texts are read in English"),
}


def tagger_for(language: str | None) -> str:
    """The model that should tag a provision in `language`."""
    return model_and_reason(language)[0]


def model_and_reason(language: str | None) -> tuple[str, str]:
    """(model, why) - the reason travels into the run note, so the choice is auditable."""
    if not language:
        return DEFAULT_TAGGER, "default: no language declared for this document"
    entry = LANGUAGE_TO_TAGGER.get(language)
    if entry is None:
        log.warning("no tagging model mapped for language %r - falling back to %r. Add it to "
                    "LANGUAGE_TO_TAGGER rather than letting a script be judged by a model that "
                    "may not read it.", language, DEFAULT_TAGGER)
        return DEFAULT_TAGGER, f"default: {language!r} is not in LANGUAGE_TO_TAGGER"
    return entry


def models_in_use(languages) -> dict[str, str]:
    """{model: the languages it will tag} - for the preflight line and the run note."""
    grouped: dict[str, list[str]] = {}
    for language in sorted({lang for lang in languages if lang}):
        grouped.setdefault(tagger_for(language), []).append(language)
    return {model: ", ".join(langs) for model, langs in sorted(grouped.items())}
