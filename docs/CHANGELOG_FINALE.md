# Finale changelog

One entry per change, newest first. Three lines each: what, why, how it was verified.
The point is that anyone (including the author in three weeks) can reconstruct why the
code looks the way it does without reading git diffs.

Workstream codes refer to the finale build plan: W0 code understanding · W1 crawler ·
W2 provider layer and experiments · W3 twelve-pillar instrument.

---

## 2026-09-27

**W2 · The open-weights swap made real: `config/llm/factory.py` resolves the model from the provider it actually resolved and refuses an unknown provider; `config/llm/ollama_client.py` sets `num_ctx` from the new `OLLAMA_NUM_CTX` setting (default 16,384) and raises `ContextOverflow` rather than answering from a truncated prompt; `src/p3map/triage/local.py:100` gains the same `num_ctx`; `src/p3map/mapping/schema.py` closes `score_hint` and `coverage` to `Literal` enums.**
Why: measured on one real provision (SG PDPA s.26(1), the canonical ban-versus-conditional trap). `LLM_PROVIDER=ollama` alone built `OllamaClient(model='claude-sonnet-5')` and returned HTTP 404, because the role map was read from the Anthropic variables and `OLLAMA_MODEL` was consulted only in the empty-key fallback. With the model name corrected the call **ran, returned schema-valid JSON, and fired three mutually exclusive indicators** — a ban, a storage requirement and a conditional regime on one provision — having read 2,050 of 6,792 prompt tokens, since Ollama's default window is 2,048 and it truncates from the front where the codebook sits. It contradicted its own trap check, which said a conditional path existed, because the trap descriptions travel in the tool schema and are not truncated. Separately the model returned `score_hint: 'default'` and, on another run, a whole sentence: the field was free text while `rollup.py:91` does `float(score_hint)` and `submission.py:256`/`:261` count rows by `coverage == "Horizontal"`/`"Sectoral"`. `verify/blind.py:28` already constrained `score_hint` as an enum, so the mapper now matches its own verifier. The four enum values and three coverage values were taken from 16,717 Round 1 verdicts, so no real output is narrowed out.
Verified: `python -m pytest tests -q` gives 49 passed. Every factory path checked: the three Anthropic roles resolve their own variables, `role="triage"` still forces Ollama (decision #3), `LLM_PROVIDER=openai` now raises instead of silently becoming Ollama, and a stale `LLM_MODEL` is ignored with a printed notice. The same provision re-run through the real S4 path on `qwen2.5:14b` read 6,553 prompt tokens and reproduced Round 1's Sonnet verdict exactly — 6.1 false, 6.2 false, **6.4 applies, score 1, Horizontal**, 7.1/7.3/7.4 false, every quote grounded — in 27 s at $0. With `OLLAMA_NUM_CTX=2048` the same call raises `ContextOverflow` before spending.

## 2026-09-26

**W2 · `stages/p3-map/config/selection.json` and `config/selection.py` added, with `tests/test_selection.py`. S2 candidate selection becomes a score threshold with a floor and a ceiling, resolved per indicator, economy and language. Not yet wired into `src/p3map/select.py`.**
Why: the nine integers in `select.py:28-31` were not derived from anything — three were truncating filed evidence at the ceiling while 6.4 and 7.4 were three to fourteen times oversized — and being code they cannot be tuned after the 30 September freeze, when the live test names its economy on the morning of 15 October. A dense cosine is comparable across cells in a way rank is not: every Round 1 filed row scored at or above 0.540 while random provisions top out at 0.51. The floor keeps a null result evidenced; the flat ceiling holds because the depth needed does not scale with corpus size (Australia holds 3.85× Malaysia's provisions and needed the same depth for 7.3 and 7.5). Derivation: `rdtii-finale-3-mapping/notes/2026-09-26-selection-cap-function.md`.
Verified: `python -m pytest tests/test_selection.py -q` gives 21 passed and `tests/test_indicator_ids.py` still gives 28. Replayed against the Round 1 reference arm through the shipped module: **7,864 candidate pairs per economy against 13,627 for the caps, gold recall gate 37/37 unchanged, all 22 cells that held a verified fire keep their maximum score, 120 of 135 filed evidence rows and 91 of 105 NEW rows retained.** The BM25 top-up for 6.4 and 7.3 adds 269 pairs and 16 verified fires. A per-law cap was tried and rejected: it cuts the right provision inside the right law and drops retention to 43%.

## 2026-09-12 (later)

**Housekeeping · `interface/dashboard.py` `p3map_docs` default is now repo-relative, and the 13 per-step workflow documents were copied into `stages/p3-map/workflow/steps/` (68 KB).**
Why: the default was an absolute Desktop path into the standalone p3-map repo, which has been archived. Worse, the docs existed nowhere in the finale repo, so a reviewer's clean clone rendered an empty Workflow tab (C3b). They now ship with the code. `RDTII_P3MAP_DOCS` still overrides.
Verified: the file parses, the directory resolves, and 13 markdown files are present.

**Housekeeping · `interface/dashboard.py:58` `DEFAULT_REPO` is now `Path(__file__).resolve().parent.parent`.**
Why: it was an absolute Desktop path pointing at the *Round-1* repo, so a reviewer's clean clone drove the wrong checkout. This is the gap-list item "interface deploys from a clean clone" (C3a, C3b, C4a). Archiving the Round-1 repo forced the fix.
Verified: resolves to the finale repo root and `main.py` is present there; the file parses.

**Housekeeping · `stages/p1-scrape/tests/test_classifier.py` host-fixture path is now the `RDTII_SAMPLE_LEGISLATION` env var, defaulting to `1_Rules/Baselines/Sample legislations` in the planning folder.**
Why: it pointed into `Desktop/RDTII Plan`, which is being archived. The same host samples sit at a stable path in the planning folder. Skip-guarded either way, so a reviewer without the files sees skips, not failures.
Verified: `python -m pytest tests/test_classifier.py -q` gives 8 passed, so the real-sample tests ran rather than skipped.

## 2026-09-12

**W3A · `indicator_ids.py` added (canonical in `stages/p0-instrument/scripts/`, byte-identical copy in `stages/p3-map/config/`) with `stages/p3-map/tests/test_indicator_ids.py`.**
Why: the finale requires decimal-text indicator IDs (`6.1`, `4.01`, `12.4.1`); `P6-I1` cannot express three-level IDs, and float parsing collapses `4.01` into `4.1`. One helper owns parsing, pillar lookup, legacy translation and ordering so no module re-implements them.
Verified: `python -m pytest tests/test_indicator_ids.py -q` gives 28 passed, including the `4.01` vs `4.1` separation, three-level `12.4.1`, and agreement with the host template's Pillar-auto formula across all 62 indicators.

**W0 · `docs/CODE_MAP.md` added.**
Why: the developer wants to understand the logic, file structure and code far better than in Round 1; every build task starts from this map.
Verified: every `path:line` was taken from a grep of `def`/`class` lines or a direct read at commit `f0aef69`.

**W0 · `docs/CHANGELOG_FINALE.md` added (this file).**
Why: the walkthrough protocol requires a three-line record after every edit.
Verified: n/a.
