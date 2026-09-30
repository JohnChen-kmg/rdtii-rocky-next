# 3 · Mapping to the RDTII Index — Project 3 Plan

**Repo:** `rdtii-p3-map/` · **Pipeline stages:** P3 (prefilter) + P4 (map) + P5 (verify) + P9 (NEW/KNOWN + MY error-check) + P6 (final CSV/JSON) · **Owns:** the 40% Substantive-Accuracy block — Framework alignment ~10, **Discovery of NEW evidence 20**, Citation fidelity ~10 — plus the **15-pt Audit trail** and the P3 share of the measured cost-efficiency item. · **Contract:** obeys `00_contracts/` v`CONTRACT_VERSION` (`0.2.0` — the version every shipped Hand-off #2 record stamps); consumes **Hand-off #2** `handoff2/provisions.jsonl` (+ `handoff2/source_text/<doc_id>.txt`); emits `out/records.csv` + `out/records.json` + `out/cost_report.json`.

> This is the highest-leverage repo in the build: it converts a grounded provision into a *scored, cited, NEW-tagged* row. Every point it owns is either binary-visible to a non-technical judge (a working URL, a verbatim quote) or the single biggest differentiator (NEW). The plan is decision-forcing: where two designs were possible, one is chosen and the loser is named. It is also explicitly **staged** (§1.3, §11): a thin slice ships a *single* mapping agent + one verifier; the adversarial exclusive agent, proxy baseline, eval harness, and full edge-case matrix are deferred to post-slice polish so the protected single-row slice cannot be crowded out.

> **⚠️ Status — provisional (2026-07-09), by design.** Project 3 is the trickiest of the three, and its **final stage — provision-level NEW/KNOWN diff + the Malaysia error-check + the blind-verify / reconcile loop — is expected to get a dedicated, more detailed workflow when we reach it.** What is **fixed** is the boundary: it consumes Hand-off #2 and emits the frozen 13-column CSV/JSON (contract). What is **a working scaffold with deliberate room to change** is the internal design below — signature keys, thresholds, reconcile semantics, error-check classes, agent topology. Do not treat those as frozen. Build Projects 1 & 2 (whose goals/targets are clear) first; we sharpen this before building it.

---

## 1. Purpose, non-goals, and staging

### 1.1 Purpose (what this repo is accountable for)
Take one normalized Provision-Record per article, and:
1. **Prefilter** each provision to a short candidate-indicator list (recall-first) so the LLM never scores against all 9 blind.
2. **Map** each candidate (provision, indicator) pair → score (per-indicator-legal value set, §4.5) + ≤300-char rationale, using `indicators.yaml` scoring trees, guarding the P6-I4-vs-P6-I1, P7-I3, government-data, and P7-I1-polarity traps.
3. **Blind-verify** each mapping with an independent adversarial pass; disagreements are down-weighted, not silently dropped; the side-by-side view is retained as the audit artifact.
4. **Tag NEW/KNOWN** at *provision* level by diffing against the Round-1 baseline — with a graceful-degradation path because the baseline is not in hand as of 2026-07-09.
5. **Run the Malaysia error-check** (double-weighted): reconcile retrieved MY provisions against the baseline (or the `proxy:rdtii_public` interim target set) and emit Correct / Not-correct / Actions.
6. **Write** the final consolidated **13-column CSV + JSON** — every scored row carrying the audit trio (verbatim snippet + article/¶ locator + working URL); law-level "No provision found" rows carry the relaxed gate (§2.2).
7. **Instrument cost** — real measured per-document USD/tokens/wallclock for P3's own calls — and run a **baseline evaluator** when an answer key exists.

### 1.2 Non-goals (owned elsewhere — do not build here)
- **No crawling** (Project 1) and **no OCR / text cleaning / snippet production** (Project 2). P3 consumes `verbatim_snippet` + offsets; for grounding it re-reads **`handoff2/source_text/<doc_id>.txt`** (P2's normalized text) to re-confirm an offset — **never** re-reads or re-OCRs a raw PDF (`source_file_path` is carried only as provenance for the audit strip).
- **No feature-tag re-derivation.** `scope` / `data_type` / `obligation_type` from Hand-off #2 are *hints for the prefilter*, never the score. Per the contract boundary note, the P6-I4 trap is P3's responsibility, so P3 must be free to overrule `obligation_type=conditional`.
- **No schema authorship.** The 13 columns, the 9 indicator definitions, and `policies.yaml` are frozen in `00_contracts/`; P3 reads them, never redefines them. Any change there is a MAJOR bump (§8 of the contract) and is off-limits before 20 July. (The one additive item P3 relies on — the `source_text/<doc_id>.txt` sidecar and per-indicator score-value sets in `indicators.yaml` — are PATCH-level, backward-compatible clarifications; see §2.1 and §4.5.)

### 1.3 Staging (locked, mirrors §11)
| Phase | Ships | Deferred out |
|---|---|---|
| **Slice** (protected) | single mapping agent (inclusive-only prompt) + **one** blind verifier + reconciler + 13-col CSV/JSON + audit HTML + `--baseline NONE` + minimal edge cases (no-provision, bad-country) + P3 cost meter | — |
| **Breadth/polish** | the **exclusive** adversarial agent (dual-agent design §4), `--baseline proxy:rdtii_public` loader, full edge-case matrix, `eval` harness, `reconcile` on real baseline, MY error-check at scale | — |

This staging directly answers the realism risk (§12): the slice is buildable by a solo builder in the first days; the adversarial/eval machinery is real but additive and cannot block the single verifiable row.

---

## 2. Input contract (Hand-off #2) & final output schema

### 2.1 Input — `handoff2/provisions.jsonl` (+ `source_text/`)
One Provision-Record per line, grounded by P2's exit criteria. P3 **re-asserts** grounding on ingest as a defensive gate (a corrupted hand-off must fail loud, not silently mis-cite). Fields P3 relies on:

| Consumed field | Used for |
|---|---|
| `provision_id`, `doc_id`, `economy` | keys, grouping, per-economy runs |
| `law_name`, `law_number`, `last_amended` | CSV cols 2/3/4 |
| `article_section` | CSV col 6 (must already carry paragraph, e.g. `s.26(1)`) |
| `verbatim_snippet`, `snippet_char_start/end`, `raw_context_before/after` | CSV col 9 + LLM disambiguation + audit view; grounding re-assert |
| `location_reference`, `source_url` | CSV cols 8/11 |
| `scope`, `data_type`, `obligation_type` | **prefilter hints only** |
| `source_file_path`, `source_type`, `pdf_is_scanned`, `ocr_quality_cer`, `ocr_engine`, `retrieval_method`, `extraction_model`, `access_date` | JSON provenance extras + audit view (drives per-record `model_version`, §2.3/§9) |

**Grounding re-assert (layered — reads P2 text, never the raw PDF):**
- **Tier 1 (strong):** if `handoff2/source_text/<doc_id>.txt` is present, assert `source_text[snippet_char_start:snippet_char_end] == verbatim_snippet`. (`snippet_char_start/end` are Required fields in the frozen Hand-off #2 schema §3.2; the `source_text/<doc_id>.txt` sidecar is the file those offsets index — P2 writes it; formalize as a contract PATCH clarification, additive/backward-compatible per §8.)
- **Tier 2 (degraded):** if `source_text` is absent, assert `verbatim_snippet` occurs within `raw_context_before + verbatim_snippet + raw_context_after` and that the offsets are internally consistent (non-negative, `end>start`, `end-start == len(snippet)`). Set JSON `grounding = "context-checked"`.
- **Tier 3 (last resort):** if even context is missing/empty, trust P2's offsets and set JSON `grounding = "trusted-upstream"`.

**Ingest gate (hard):** validate each record against `00_contracts/schemas/provision.schema.json`; check `CONTRACT_VERSION` **major** compatibility (refuse on mismatch with the loud §8 error); run the layered grounding re-assert. A Tier-1 mismatch = hard fail (record dropped, logged); Tier-2/3 pass with the recorded `grounding` provenance.

### 2.2 Output — the exact 13 CSV columns (frozen order; judges validate programmatically)

| # | Column | Source in P3 | Required? | Rule |
|---|---|---|---|---|
| 1 | Economy | `economy` → full name (`SG`→`Singapore`) | ✅ | |
| 2 | Law Name | `law_name` | ✅ | |
| 3 | Law Number/Ref | `law_number` | ✅ (else `""`) | |
| 4 | Last Amended | `last_amended` | ✅ (else `""`) | |
| 5 | Indicator ID | mapping result | ✅ | one of `P6-I1..P6-I4, P7-I1..P7-I5` |
| 6 | Article/Section | `article_section` | ✅ (relaxed for no-provision rows) | **with paragraph**, RDTII style `s.26(1)` |
| 7 | Discovery Tag | NEW/KNOWN engine | ✅ | `NEW` \| `KNOWN` |
| 8 | Location Reference | `location_reference` | ⬜ | |
| 9 | Verbatim Snippet | `verbatim_snippet` | ✅ (relaxed for no-provision rows) | **exact, no paraphrase** |
| 10 | Mapping Rationale | mapping agent | ⬜ | **≤300 chars**, truncate-guard enforced |
| 11 | Source URL | `source_url` | ✅ | official portal, syntactically valid |
| 12 | Confidence | verifier consensus | ⬜ | 0–1 |
| 13 | Notes | edge-case engine | ⬜ | repealed / broken-url / cross-ref / candidate-NEW / verifier-split / MY-discrepancy etc. |

**Record types.** Every JSON record carries `record_type ∈ {scored, no_provision}`; `final_record.schema.json` and `validate()` select the gate by this flag.

**Audit-trio invariant — `record_type=scored` (the 15-pt gate).** Cols **6, 9, 11** must be present and non-empty, **and** col 11 must be a syntactically valid URL on an official portal host (from `sources_<cc>.yaml`). The **live** reachability check is a **Notes flag, not a rejection gate** (fix for the §7 contradiction / offline-judge risk):
- The URL check consults `out/url_cache.json` first; a cached `<400` (or no-network / timeout / cache-miss with network unavailable) is treated as **pass-with-warning** — the row is **never** dropped for a transient or unreachable URL.
- If a live check runs and returns `≥400` or times out, **keep the row**, set `Notes += "source URL unreachable at check time"`, and prefer the official replacement per §7 (the replacement, if found, becomes col 11 and is what the audit page links).
- Rejection happens only if col 11 is **absent or not a valid official-portal URL** — a structural, offline-decidable failure, not a network one.

**Audit-trio invariant — `record_type=no_provision` (relaxed gate).** For law-level "No provision found" rows (the mandatory never-blank edge case, §7): col 6 may be empty **or** carry the governing law's part/scope (e.g. `Part VI`); col 9 is the literal placeholder `"No provision found"` and is **exempt** from the verbatim-substring assert; col 11 must still be a valid official-portal URL (the governing law's page). `validate()` applies this relaxed gate when `record_type=no_provision`. This resolves the collision between the never-blank rule and the audit-trio hard gate.

### 2.3 Output — `records.json` extras (per the contract)
Top-level: `contract_version`, `run_timestamp`, `baseline_mode` (`NONE`|`proxy:rdtii_public`|`<path>`), `cost_report_ref`. Per record adds: `record_type`, `grounding` (§2.1), `source_file_path`, `ocr_quality_cer`, `ocr_engine`, `processing_time_seconds`, `pdf_is_scanned`, `retrieval_method`, `raw_context_before/after`, `snippet_char_start/end`, `score_value` (the 1/0.5/0), `verifier_verdict`, `prefilter_scores`, and **`model_version`** = `f"{LLM_MODEL}+{ocr_for_this_record}"` where `ocr_for_this_record` is derived **per record from that record's `ocr_engine` provenance** (fix #13), falling back to config `OCR_ENGINE` only when `ocr_engine` is null / the source is HTML. This keeps the pinned-model audit field faithful to the engine that actually processed each doc (P3 performs no OCR itself). `provisions[]` groups records per law (`by_law/<doc_id>.json`).

> Note: the CSV carries **Indicator ID** but not the numeric 1/0.5/0 — the frozen 13 columns include no score column. The value is preserved in JSON `score_value`. Do not invent a 14th CSV column (MAJOR-bump violation).

---

## 3. Prefilter (P3 stage) — indicator-as-statute-query, recall over precision

**Goal:** cut 9 indicators to a candidate set (typ. 1–3, capped ≤2 on the CPU path, §6-fix) so mapping is cheap and focused, **without dropping a true indicator** (a missed candidate = lost Framework-alignment *and* possibly lost NEW points — the most expensive error class). **Tune for recall; let mapping+verify supply precision.**

### 3.1 Method — hybrid sparse+dense, indicator-as-query
Each indicator is pre-encoded once as a **query document** from its `indicators.yaml` `question` + `scoring_tree` phrases + `disambiguation` keywords (we treat the indicator definition as the query and the short provision as the corpus).
- **Sparse:** BM25 (`bm25s` — MIT, NumPy-only, 100-500× faster than rank_bm25; see requirements.txt) over `verbatim_snippet` + `raw_context_before/after`. Catches terms of art ("transfer", "outside Singapore", "retain for a period of not less than").
- **Dense:** `BAAI/bge-m3` via `sentence-transformers`, CPU, cosine. Catches paraphrase ("shall not disclose … to a place beyond" ↔ cross-border transfer).
- **Fusion:** Reciprocal Rank Fusion (RRF) → keep indicators above a recall-biased threshold (default top-K by RRF **OR** any indicator whose sparse OR dense score exceeds a low floor). Config: `PREFILTER_TOPK` (default 3; **2** when `LLM_PROVIDER=ollama`), `PREFILTER_FLOOR`, `PREFILTER_SPARSE=bm25`, `EMBED_MODEL=BAAI/bge-m3`.

### 3.2 Hint fusion (cheap boost, never a filter)
`obligation_type` boosts the aligned indicator's RRF (`ban`→P6-I1, `storage`→P6-I2, `infrastructure`→P6-I3, `conditional`→P6-I4) but **cannot remove** an indicator the retrievers surfaced — preserving P3's authority to overrule the P6-I4 trap. `data_type=non-personal` down-weights (never removes) P7 indicators. `scope` informs P7-I1/I4 polarity but never gates.

### 3.3 Prefilter exit criteria
- **Slice (protected):** for s.26(1), P6-I4 appears in the top-K candidate set (P6-I1 may also appear — that is correct recall behavior; the trap is resolved downstream). No mini-set labeling required for the slice.
- **Post-slice:** on a hand-labeled SG mini-set (≈15 provisions) the prefilter reaches **recall ≥ 0.95** against the gold indicator set (evaluator §8.2). Gold labels for that mini-set are produced by the builder (John) by hand from the RDTII 2.1 methodology sheet and committed as `tests/gold/sg_miniset.yaml`; this is post-slice work, not on the critical path (fix #10).
- Every provision emits `prefilter_scores` (per-indicator RRF) into JSON. Runs CPU-only; BGE-M3 embeddings cached to disk keyed by `content_sha256` + `snippet_char_start`.

**Fallback:** if BGE-M3 is unavailable/too slow, `PREFILTER_DENSE=off` degrades to BM25-only (still recall-usable on term-of-art-heavy statute text) — the modular-backend story for the retrieval layer.

---

## 4. Mapping (P4) — inclusive agent for the slice; dual inclusive/exclusive at scale

**Goal:** for each (provision, candidate-indicator) pair, decide the score and write a rationale, correctly navigating the traps. A single prompt tends to over-fire (label everything a ban). The full design forces disagreement to surface; the slice ships the cheaper half and adds the adversary as polish (fix #12).

### 4.1 Staged agent design (chosen over single-agent + self-critique)
- **Slice default — inclusive agent only:** one LLM call per (provision, indicator) pair: "decide whether this provision fires indicator X; cite the scoring-tree branch and the exact snippet span; name any disqualifier you see." Emits Structured Output (§4.2). The reconciler + blind verifier (§5) supply the precision check for the slice.
- **Post-slice — add the exclusive agent (full dual-agent):** a second call, same model, adversarial prompt — "argue *against*; name the disqualifier (government data; wrong obligation class; trap conditions)." A deterministic **reconciler** (code, not LLM) combines: both-fire→high confidence; split→route to verifier; both-refuse→drop.
- **CPU/Ollama path (fix #6):** never run the exclusive agent; keep inclusive-only; cap candidates ≤2 (§3.1); the blind verifier fires **only** on split/low-confidence rows (§5.1). This bounds calls to ~1 per pair (≈≤2 per provision) so the keyless run is completable — expected wallclock documented in the README (§10.3).

*Loser design:* single agent scoring all candidates in one call — rejected: it blurs the traps and yields one shared rationale.

### 4.2 Structured Outputs contract (shared spine, §5 of the contract)
Every mapping call goes through `config.llm.get_llm(settings).complete(prompt, schema)` — never a raw SDK. Schema per call:
```
{ indicator_id, fires: bool, score: <allowed set for this indicator, §4.5>,
  tree_branch_id: str, trigger_span: {start,end}, disqualifier: str|null,
  rationale: str(<=300), self_conf: float }
```
`trigger_span` must be a sub-range of the provision's snippet — tying the score to grounded text (feeds the audit view). Model pinned via `LLM_MODEL`; `claude-sonnet-5` default, `claude-opus-4-8` for `--hard`, `ollama:llama3.1:8b` default / `qwen2.5:14b` opt-in when `ANTHROPIC_API_KEY` empty (auto-fallback, §5.2 of contract).

### 4.3 The encoded traps (each = a scoring-tree assertion + a verifier check)
- **P6-I4 vs P6-I1 (consent/adequacy trap):** transfer permitted *if* consent / adequacy / contract / approval → **P6-I4 conditional**, never P6-I1 ban. Encoded as a disqualifier ("if the text names a condition under which transfer is allowed, it is NOT an outright ban") + verifier rule. `obligation_type=conditional` aligns but does not decide.
- **P7-I3 (retention trap):** only a rule requiring data be kept **at least** N period scores P7-I3=1. "Do not keep longer than necessary" / storage-limitation → **not** P7-I3. Disqualifier keyed on "no longer than / not longer than necessary".
- **P6-I1..I4 government-data exception:** localization applied to **government** data is not scored. `data_type` + snippet inspection; the agent disqualifies government-held-data provisions.
- **P7-I1 inverted-polarity guard:** higher score = *less* protection (1=none, 0=comprehensive). The reconciler asserts polarity so an agent that "found a strong DP law" cannot mis-emit a high score.

### 4.4 The template-tab trap (systematic-error guard)
`indicators.yaml` is the **only** mapping authority. No code reads the `OUTPUT_TEMPLATE_31MAY.xlsx` "Indicator Reference" tab (GDPR taxonomy — WRONG). The `WARNING_DO_NOT_USE` string is surfaced in the audit page footer so a judge sees the guard was deliberate.

### 4.5 Per-indicator allowed score sets (fix #5)
The methodology makes three indicators **binary**. The allowed set is read from `indicators.yaml` `scoring.values` per indicator and enforced in both the reconciler and `final_record.schema.json`:

| Indicator | Allowed values |
|---|---|
| P6-I3 Infrastructure | `{1, 0}` |
| P7-I3 Minimum retention | `{1, 0}` |
| P7-I5 Government access | `{1, 0}` |
| P6-I1, P6-I2, P6-I4, P7-I1, P7-I2, P7-I4 | `{1, 0.5, 0}` |

A `0.5` emitted for a binary indicator is **rejected/clamped** by the reconciler with a logged correction (`"clamped 0.5→? on binary P7-I3; agent out-of-range"` — clamp direction: route to verifier tie-break, defaulting to the nearer of {1,0} by `self_conf`), and `final_record.schema.json` fails any surviving out-of-range value.

### 4.6 Mapping exit criteria
- Every fired pair carries a `tree_branch_id` matching a real branch in `indicators.yaml`.
- **Slice:** s.26(1) scored **P6-I4**, *not* P6-I1 (consent/adequacy trap held); rationale ≤300 chars names the tree branch.
- **Post-slice:** the three trap fixtures (conditional-transfer, storage-limitation, min-retention) scored correctly by ID; zero binary-indicator `0.5` survivors; zero rows where `fires=true` but `trigger_span` is empty.

---

## 5. Blind verifier + side-by-side audit view (earns the 15-pt audit trail)

### 5.1 Blind verifier
A **third, independent** LLM pass seeing only the verbatim snippet, the proposed `indicator_id`, and the scoring-tree branch — **not** the mapping rationales (blind = no anchoring). Returns `{agree, score, reason, span}`. On the **CPU/Ollama path it is conditional** — invoked only when the inclusive agent's `self_conf` is low or (post-slice) the dual agents split — to bound call volume (fix #6). Consensus rule:
- verifier agrees → `Confidence` high (≈0.9); write row.
- verifier disagrees on score → keep row, `Confidence` low (≤0.5), record both verdicts in JSON `verifier_verdict`, add `Notes += "verifier-split"`. Nothing silently dropped.
- verifier says indicator doesn't fire → drop the row **unless** the mapping agent(s) fired (then keep at low confidence, flagged). Bias: don't lose a true NEW find to one skeptical pass.

`Confidence` (col 12) = documented deterministic function of {agent fires, exclusive disqualifies (if run), verifier agrees, self_conf, prefilter rank}. Formula in README so the number is defensible, not magic.

### 5.2 Side-by-side audit view (the artifact that *shows* the 15 pts)
Beyond the CSV, P3 emits `out/audit/<provision_id>.html` + index `out/audit/index.html` rendering per row: the **verbatim snippet with the trigger span highlighted**, the matched scoring-tree branch, agent vs verifier verdicts side by side, the working deep `source_url` as a clickable link, `location_reference`, and the provenance strip (`source_type`, `ocr_quality_cer`, `ocr_engine`, `retrieval_method`, per-record `model_version`). One click from CSV row to highlighted source quote = "a non-technical judge can verify in seconds" made literal. Self-contained HTML (inline CSS), CPU-generated, zero external calls, produced by the runner with no manual steps — a ready screen-recording asset for Deliverable #4. It stays a **static view over `records.json`** (never runs the pipeline behind a button); a full interactive dashboard is **deferred to the Finale** (contract §9.2), where interface is heavily weighted — it earns nothing in Round 1 and must not compete with the scored pipeline.

### 5.3 Verifier exit criteria
- Every written row has a `verifier_verdict` in JSON.
- The audit index links every CSV row to a highlighted-snippet page whose `source_url` is a valid official-portal link (live-checked with cache; unreachable → Notes flag per §2.2, not a broken page).
- Live URL check cached in `out/url_cache.json` so re-runs and the judge's clone don't hammer portals.

---

## 6. NEW/KNOWN diff + graceful degradation + Malaysia error-check (the 20-pt lever)

### 6.1 Provision-level diff (not law-level)
NEW is judged at **provision** granularity: a new clause inside a baseline law still counts NEW. Diff key = normalized signature `(economy, indicator_id, canonicalized(article_section), semantic_fingerprint(verbatim_snippet))`. Match on economy+indicator+section AND a snippet fingerprint within threshold → `KNOWN`; else → `NEW`. Fingerprint = BGE-M3 cosine + a normalized-citation exact check (both from the already-loaded embedder). Threshold `NEWKNOWN_SIM` config-tunable; conservative default so we do not over-claim NEW.

### 6.2 Baseline modes (real baseline now in hand; degradation retained as fallback)
**The real Round 1 SG/AU/MY baseline is now available** — `Knowledge Portal/Database/ESCAP-RDTII-2.1_ Round 1 Database.xlsx` (per-country sheets). `--baseline <path>` to it is the **primary** mode for real output and the Malaysia error-check. The modes below are retained as documented fallbacks so P3 never *blocks* (offline runs, or before a refreshed baseline):
- `--baseline NONE` → every mapped provision tagged **`Discovery Tag = NEW`**, `Confidence` reduced, `Notes = "candidate-NEW — baseline unavailable at build; pending reconciliation"`. Nothing dropped. The 20-pt lever is live from day one, but these are **candidate-NEW**, not **verified-NEW** (the evaluator separates them, §8.2 / fix #9).
- `--baseline proxy:rdtii_public` (post-slice) → diff against the **public RDTII database** as a stand-in KNOWN/target set to avoid over-claiming; loader normalizes it into the signature schema.
- `--baseline <path>` → the real Round-1 SG/AU/MY DB (**now available**: `Knowledge Portal/Database/ESCAP-RDTII-2.1_ Round 1 Database.xlsx`) — the default for real output; a loader parses its per-country sheets into the signature schema.
- **`p3-map reconcile --baseline <path>`** → a pure post-process over `handoff2/` + existing `out/` that re-diffs at provision level and **rewrites cols 7, 12, and 13 only** (fix #7), without re-running P1/P2/mapping. Deterministic Notes edits allowed: strip the `candidate-NEW …` note on a NEW→KNOWN flip; add MY discrepancy flags (§6.3). This is the same code path MY error-check uses.

### 6.3 Malaysia error-check (double-weighted) — Correct / Not-correct / Actions
Malaysia is worth double (error-check of existing entries **plus** new collection), and it is **entirely blocked without a target set**. Since the Round-1 baseline is not in hand, the MY error-check runs against **`--baseline proxy:rdtii_public`** as the interim KNOWN/target set (fix #4), so the double-weighted item is demonstrable **before 20 July**; results are marked `"proxy-baseline; pending real-baseline reconciliation"` and re-run via `reconcile` when the real DB lands. Each retrieved MY provision is classed against the (proxy or real) target:
- **Correct** — agrees with target entry (same indicator + score + citation).
- **Not-correct** — contradicts target (different score, wrong indicator, dead/wrong URL, wrong section), with the specific discrepancy recorded.
- **Action** — the fix: corrected indicator/score, replacement official URL, corrected `article_section`, or "add — missing from target (NEW)".

Output: `out/malaysia_errorcheck.csv` with `Baseline Entry | Retrieved Provision | Correct/Not-correct | Discrepancy | Action | Baseline Source`, cross-referenced to main-CSV rows by `provision_id`; contradictions also flagged in the main row's col 13.

### 6.4 NEW/KNOWN exit criteria
- **Slice:** with `--baseline NONE`, the SG row is `NEW` + candidate-NEW note; run does not error.
- `reconcile` flips seeded KNOWN provisions to `KNOWN` when a baseline is supplied, editing only cols 7/12/13 (diff-tested: cols 1–6, 8–11 byte-identical before/after; col 13 changes limited to the deterministic strip/add edits above).
- **MY (post-slice):** run against `--baseline proxy:rdtii_public`, the MY error-check produces at least one **Correct** and one **Not-correct + Action** on the MY seed set. (This criterion is satisfiable pre-real-baseline because it targets the proxy.)

---

## 7. Edge-case rules (encoded from `policies.yaml`, enforced in P3)

| Edge case | P3 behavior |
|---|---|
| **No provision found** for an in-scope indicator in a governing law | Write a `record_type=no_provision` row (never blank): col 9 = `"No provision found"` (exempt from verbatim assert, §2.2), cols 2/3/5 cite the governing law + indicator, col 6 empty or governing part/scope, col 11 = the law's official URL, col 13 = reason. Emitted at *law* level after mapping finds no firing provision — P3's job, not P2's. **Slice includes this rule.** |
| **Repealed / superseded** law | Do not record the scored row, or set `Notes = "repealed/superseded"`. Detected from `last_amended` / P2 flags / a small `data/repealed.yaml`. *(Post-slice.)* |
| **Broken URL** at check time | Keep the row, `Notes = "source URL unreachable at check time; official replacement: <url>"`, prefer the official replacement; the audit-trio uses the replacement. Never a row rejection (§2.2). |
| **Same provision → 2 indicators** | Emit **two rows**, same snippet, different col 5, cross-noted. *(Post-slice.)* |
| **One indicator ← many laws** | Separate rows, cross-referenced in col 13. *(Post-slice.)* |
| **Sectoral AND horizontal** both apply | Record both rows; authority = who enacted it, not breadth. `scope` hint informs but P3 decides. *(Post-slice.)* |
| **Bad/misspelled country input** | CLI validates `--economy` against {Singapore,Australia,Malaysia + SG/AU/MY}; unknown → logged warning + graceful skip, **never crash**. **Slice includes this guard.** |

Each rule ships with a unit fixture so a regression is caught by `p3-map validate` / CI. Slice-scoped rules (no-provision, bad-country) are in the T8 exit; the rest are post-slice.

---

## 8. Cost instrumentation + baseline evaluator

### 8.1 Measured per-document cost (rubric: cost-efficiency, **measured not estimated**)
A `CostMeter` wraps every P3 `complete()` call, recording real token counts (from the provider response) × the pinned model's published price, plus wallclock. Aggregated into `out/cost_report.json`: `{per_doc: [{doc_id, llm_calls, input_tokens, output_tokens, usd, seconds}], totals, mean_usd_per_doc, model_version}`. `MAX_COST_USD_PER_DOC` (default 0.25) is a live guardrail — exceeding it warns and (config `COST_HARD_STOP`) can halt. For the Ollama fallback, USD=0 but wallclock is still recorded (the "no key, CPU-only, $0" story is itself a cost-efficiency claim).

**End-to-end consolidation (fix #8):** P1, P2, P3 are separate repos and Hand-off #2 carries only provisions — there is **no seam by which P3 reads P1/P2 cost reports**. Therefore P3's `cost_report.json` is scoped to **P3-only** calls, and **end-to-end per-doc consolidation is owned by the top-level `run_slice` runner** (§10.4 of the contract / this §10.5), which reads the P1 cost report (P1 shipped into `handoff1_v2/` — resolve every P1 path via `.env`, never hardcode `handoff1/`) + `handoff2/cost_report.json` + `out/cost_report.json` and writes `out/cost_report_e2e.json`. The seam is stated explicitly; nothing is unowned.

### 8.2 Baseline evaluator (precision / recall / new-count)
`p3-map eval --gold <answer_key>` computes, against a gold set: indicator **precision/recall/F1** (framework alignment), **citation-fidelity rate** (audit-trio present + snippet exact + URL valid), and **new-count**. The new-count **distinguishes** (fix #9):
- **verified-NEW** — provisions diffed against a *real or proxy* baseline and found absent. Only this figure is reported as the headline NEW-count and is the only one usable in the deck.
- **candidate-NEW** — provisions under `--baseline NONE` (baseline unavailable). Reported separately and clearly caveated in `eval_report.json` (`"candidate_new_count (NOT verified against a baseline — do not claim as discovered evidence)"`).

With no answer key (status: not obtained), `eval` runs **self-consistency mode**: agent/verifier agreement rate + grounding-assertion pass rate (should be 100%). Also reports **prefilter recall** (§3.3). Output `out/eval_report.json` feeds the pitch deck. *(Eval harness is post-slice.)*

---

## 9. Tool choices, swappable fallbacks, shared `.env`

All model-bearing choices are **config values, not code paths** (the 15-pt modular backend). P3 vendors the identical `config/` package from `00_contracts/config_template/` that P2 uses — the shared spine, not duplicated.

| Stage | Default | Fallback(s) | Config key |
|---|---|---|---|
| Mapping/verify LLM | `claude-sonnet-5-<pinned>` (anthropic SDK, Structured Outputs) | `claude-opus-4-8` (`--hard`) → `ollama:llama3.1:8b` default / `qwen2.5:14b` opt-in (open-weight, CPU, auto-selected if key empty) | `LLM_PROVIDER`, `LLM_MODEL`, `ANTHROPIC_API_KEY`, `OLLAMA_HOST` |
| Dense prefilter | `BAAI/bge-m3` (sentence-transformers, CPU) | any ST model; or `PREFILTER_DENSE=off` → BM25-only | `EMBED_MODEL` |
| Sparse prefilter | `bm25s` (bm25s + PyStemmer) | — | `PREFILTER_SPARSE` |
| Candidate cap | 3 (anthropic) / **2 (ollama)** | — | `PREFILTER_TOPK` |
| Cost guardrail | 0.25 USD/doc | — | `MAX_COST_USD_PER_DOC` |
| Contract pin | `0.2.0` | — | `CONTRACT_VERSION` |

**No-key guarantee:** empty `ANTHROPIC_API_KEY` → `config.llm.factory` auto-selects `ollama` (8b, capped candidates, conditional verifier) and logs it — the reviewer's clone runs end-to-end, CPU-only, $0, no manual edits. `model_version` per record = `f"{LLM_MODEL}+{record.ocr_engine or OCR_ENGINE}"` (fix #13).

**Pinned deps (no "latest"):** `requirements.txt` floors `anthropic`, `sentence-transformers`, `bm25s`, `pydantic`, `pyyaml`, `jsonschema`, `pandas`, `httpx`; exact pins land in `requirements.lock` (`pip freeze`) after first install, same as P2. Python 3.10+; Windows: setup installs into a venv and the README invokes `py -3`/resolved interpreter path (MS Store stub unreliable on PATH).

---

## 10. Repo scaffold + CLI + README

### 10.1 Folder layout
```
rdtii-p3-map/
  README.md                      # Quick Start: clone→venv→.env→run in <10 min
  requirements.txt               # pinned, exact versions
  .env.example                   # vendored from 00_contracts/config_template
  00_contracts/                  # pinned copy via `make sync-contracts` (copy at pinned SHA, NOT a git submodule — contract §8.1)
  config/                        # SHARED spine (identical to P2): settings.py, llm/, ocr/, embed/, factory
  src/p3map/
    ingest.py                    # load provisions.jsonl + source_text/, schema + version + layered grounding
    prefilter/                   # bm25.py, dense.py (bge-m3), fuse.py (RRF), hints.py
    mapping/                     # agent.py (inclusive), exclusive.py (post-slice), reconcile.py, score_sets.py, schema.py
    verify/                      # blind_verifier.py, confidence.py, audit_view.py (html)
    discovery/                   # signature.py, diff.py, reconcile_cmd.py, proxy_loader.py (post-slice), malaysia.py
    edgecases/                   # no_provision.py, bad_country.py (slice); repealed.py, dual_indicator.py, rules.py (post-slice)
    output/                      # csv_writer.py (13 cols), json_writer.py, url_check.py (cache + Notes flag)
    cost/                        # meter.py, report.py
    eval/                        # evaluator.py (precision/recall/new-count) — post-slice
    cli.py                       # argparse entrypoints
  data/
    baseline/                    # empty until Round-1 DB arrives; --baseline points here
    repealed.yaml
  tests/
    gold/sg_miniset.yaml         # hand-labeled recall gold (post-slice; author = builder)
    fixtures/                    # trap fixtures, edge-case fixtures, grounding, 13-col schema, binary-score fixtures
  out/                           # records.csv/json, cost_report.json, url_cache.json, eval_report.json, audit/
```

### 10.2 CLI signatures
```
p3-map run       --provisions handoff2/provisions.jsonl --out out/ [--baseline NONE|proxy:rdtii_public|<path>] [--hard]
python map.py    --economy Singapore --pillar 6            # == p3-map run filtered to SG/P6
p3-map validate  --csv out/records.csv                     # 13-col order + record_type-aware audit gate + version gate
p3-map reconcile --baseline <path>                         # re-diff NEW/KNOWN + MY error-check; rewrites cols 7/12/13 only
p3-map eval      --gold <answer_key>|--self                # precision/recall/new-count (verified vs candidate) or self-consistency
p3-map audit     --open                                    # rebuild + open out/audit/index.html
```
`run` always emits `out/cost_report.json` (measured, P3-only) and **streams a stage-by-stage narration to stdout + `logs/`** (contract §9.1 — prefilter candidates, mapping branch/disqualifier fired, verifier verdict, NEW/KNOWN, row written). Every `validate` is a **hard gate** in the top-level `run_slice` runner.

### 10.3 README (Quick Start, <10 min, Windows-aware)
Sections: prerequisites (Python 3.10+ via `py -3`; Ollama already installed for keyless fallback); `make sync-contracts` (or submodule init) to pin `00_contracts`; venv + `pip install -r requirements.txt` (pinned); copy `.env.example`→`.env` (key may be left empty → Ollama auto-fallback); `p3-map run --provisions handoff2/provisions.jsonl --baseline NONE --out out/`; open `out/audit/index.html`; interpret `records.csv`, `cost_report.json`, `eval_report.json`. A **"keyless CPU wallclock"** paragraph states the measured expected time per doc on the Ollama 8b path (from the slice benchmark) so the reviewer knows a full run is completable. An explicit **"swap the model"** paragraph (edit one `.env` line) = the modular-backend proof.

### 10.4 / 10.5 Runner seam
The top-level `run_slice` (contract §7) sequences the three CLIs and, after P3, runs the **end-to-end cost consolidation** (§8.1) reading the three per-stage `cost_report.json` files into `out/cost_report_e2e.json`. P3 does not reach into P1/P2 folders itself.

---

## 11. Singapore-first vertical-slice task list + exit criteria

Ordered by **scoring-weight × risk**; protects the slice, live-crawl dependency, NEW lever, and audit trail over breadth. Slice target row (contract §7): **SG · PDPA 2012 · Act 26/2012 · s.26(1) · P6-I4 · verbatim snippet · working SSO deep URL · rationale ≤300 chars · Discovery Tag=NEW (candidate).**

| # | Task | Exit criterion |
|---|---|---|
| T0 | Vendor `00_contracts/`, stub `config/` shared spine, pin `requirements.txt` | `p3-map --version` prints matching `CONTRACT_VERSION`; `import config.llm.factory` works |
| T1 | `ingest.py` — load `provisions.jsonl` + `source_text/`, schema + version + **layered grounding** (§2.1) | Given the contract's worked s.26 record, ingests 1 record; Tier-1 assert passes if `source_text/` present, else Tier-2 with `grounding=context-checked` |
| T2 | Prefilter (BM25 + BGE-M3 + RRF + hints), indicators-as-query | s.26(1) surfaces **P6-I4 in top-K** (P6-I1 may co-occur). *(recall≥0.95 mini-set gate is post-slice, §3.3 / fix #10)* |
| T3 | Mapping **inclusive agent** + Structured Outputs + reconciler; encode 3 traps + per-indicator score sets (§4.5) | s.26(1) scored **P6-I4**, *not* P6-I1 (consent/adequacy trap held); rationale ≤300 chars names the branch; no binary-indicator `0.5` survives |
| T4 | Blind verifier + confidence + **audit HTML view** | Row gets a verifier verdict; `out/audit/sg-pdpa2012-001#s.26(1).html` shows highlighted snippet + clickable SSO deep URL |
| T5 | 13-col CSV + JSON writer + **record_type-aware** audit gate + **URL-as-Notes-flag** (§2.2) | `out/records.csv` has exactly 13 cols in order; the SG row passes `validate`; an offline URL check keeps the row + Notes, never drops it |
| T6 | NEW/KNOWN with `--baseline NONE` (candidate-NEW) | SG row = `NEW` + candidate-NEW note; no crash |
| T7 | Cost meter + `cost_report.json`; keyless Ollama fallback path | Real measured USD (anthropic) or $0+seconds (ollama 8b) for the 1 doc; runs with empty key |
| T8 | Edge-case engine minimal: **no-provision-found** (relaxed gate) + **bad-country guard** | Misspelled `--economy` logs+skips (no crash); an indicator with no firing provision yields a `record_type=no_provision` row that passes the relaxed gate |
| **Slice gate** | Run via top-level `run_slice` P1→P2→P3 | **one correct verifiable cited row** in `out/records.csv`; audit page one click away; `cost_report.json` present |

**Then breadth/polish (locked order):** add the **exclusive adversarial agent** (full dual-agent §4) → Australia (HTML deep-anchor citation fidelity — the harder, higher-value differentiator) → Malaysia error-check via `--baseline proxy:rdtii_public` (`reconcile` + new collection, double-weighted) → `proxy:rdtii_public` loader + `eval` harness + full edge-case matrix → `reconcile` on the real baseline when it arrives → deck/video assets.

---

## 12. Dependencies & risks

| Risk | Impact | Mitigation (in this plan) |
|---|---|---|
| **Final-stage design churn** (NEW/KNOWN diff + MY error-check are provisional, §top) | The trickiest, still-evolving part; premature detail wasted | Real baseline **now in hand** (`Knowledge Portal/…Round 1 Database.xlsx`) → `--baseline <path>` primary; `NONE`/`proxy:rdtii_public` retained as offline fallbacks; `reconcile` rewrites cols 7/12/13 only; evaluator separates verified-NEW from candidate-NEW (fix #9). Treat this stage's internals as a scaffold; re-detail its workflow before building it. |
| **Hand-off #2 seam drift** across 3 repos (#1 risk) | Silent mis-cite / crash | Ingest gate: schema + `CONTRACT_VERSION` major check (loud refuse) + **layered grounding against `source_text/`** (fix #3/#11); vendored pinned contracts |
| **P6-I4 / P7-I3 / binary-score traps mis-scored** | Framework-alignment loss + false NEW | Inclusive (+ post-slice exclusive) agents + blind verifier + explicit disqualifiers from `indicators.yaml`; **per-indicator allowed-value enforcement** (fix #5); trap + binary-score fixtures in CI |
| **Offline / anti-bot `source_url` at judging** | Dropped rows / empty output if URL gated | **URL check is a Notes flag, not a rejection gate** (fix #1); official-replacement rule; `url_cache.json`; no-network = pass-with-warning |
| **"No provision found" vs audit gate collision** | Mandatory never-blank row rejected | `record_type=no_provision` relaxed gate: col 6 relaxed, col 9 exempt from verbatim assert (fix #2), documented in §2.2/§7 |
| **Template "Indicator Reference" tab WRONG** (GDPR taxonomy) | Systematic mis-mapping | `indicators.yaml` is the only source; `WARNING_DO_NOT_USE` surfaced in audit footer; no code reads the tab |
| **No API key on eval box / CPU-only latency** | End-to-end run too slow → loses no-manual-steps + modular pts | Keyless auto-fallback to Ollama **8b**, candidates capped ≤2, **conditional** verifier (fix #6); BGE-M3 CPU + BM25-only degrade; measured per-doc wallclock documented in README; everything pinned |
| **Cost-consolidation seam unowned** | End-to-end cost unowned across repos | P3 `cost_report.json` scoped to P3-only; **end-to-end consolidation owned by the top-level runner** reading the three stage reports (fix #8) |
| **Solo builder, 11 days, ~75% time; P3 is feature-dense** | Breadth crowds out the slice | **Explicit staging (§1.3/§11):** slice = single agent + one verifier + CSV/JSON + audit HTML + `--baseline NONE`; exclusive agent, proxy loader, eval, full edge-cases deferred (fix #12); task order = weight×risk |

**Upstream dependencies:** a valid `handoff2/provisions.jsonl` (+ `source_text/`) from Project 2 (blocks T1+; mitigated by using the contract's worked s.26 record as a fixture until P2 is ready) and the pinned `00_contracts/` instrument (`indicators.yaml` scoring trees + per-indicator score sets + `policies.yaml`). **Downstream:** none — P3 is the terminal stage producing Deliverable #2 (the consolidated CSV+JSON) and the audit assets for Deliverables #3 (deck) and #4 (video).
