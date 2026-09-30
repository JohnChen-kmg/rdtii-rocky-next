# S1 — Prefilter (two legs) · $0 · no generative LLM

**What we're doing:** turning each of the 9 indicators into a search query and
scoring every provision against it, two independent ways, so we can shortlist
candidates instead of sending 412k provisions to an LLM.

**In → Out**
- In: `prefilter_corpus.jsonl` + the indicator **signature** files.
- Out: `bm25_top.npz`, `dense_top.npz` — top-50k ranked provisions per indicator.

**How the instrument becomes the query** (`prefilter/queries.py`)
Each indicator query = its signature's `name` + `definition_text` + `keywords` +
2 real exemplar snippets. Example — P6-I4 "Conditional flow regimes":
> "Cross-border data transfer is permitted only if conditions are satisfied:
> consent, adequacy…, contractual safeguards…, or government approval. …often a
> default prohibition with exceptions — that pattern is a conditional flow regime,
> not a ban, because a compliant transfer path exists." + keywords `unless`,
> `adequacy`, `standard contractual clauses`, `whitelist`, …

**Two legs**
- Sparse: BM25 (keyword).
- Dense: BGE-M3 embeddings, cosine (semantic; catches paraphrase and cross-lingual).

**Note:** the traps (`negative_signals`) are deliberately **left out** of the
query — retrieval optimizes recall; precision is the mapper's job.
