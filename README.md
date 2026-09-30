# [Tool Name] — AI Tool for Digital Trade Regulatory Analysis

UN Global Hackathon on AI for Digital Trade Regulatory Analysis
Team: [Team Name] | Round: **Final**
Last updated: [YYYY-MM-DD]

> **Final round requirement.** Every section below is mandatory, as flagged in the Round 1 version of this
> template. This README is part of your 30 September submission and is read during the desk review — it is
> where a reviewer looks first, and it is the front door to criterion **C4a, Technical Handover (8 points)**.

---

## What This Tool Does

This tool automates two tasks required by the ESCAP Regional Digital Trade Integration Index (RDTII 2.1):

**Task 1 — Automated Evidence Discovery**
Given an economy and a pillar, the tool crawls official government legal portals, retrieves the relevant
legislation (including scanned and image-based PDFs), and extracts clean, structured text — with no manual steps.

**Task 2 — Intelligent Mapping and Categorisation**
The extracted text is mapped to RDTII indicator IDs. Each provision is recorded with an article-level citation,
a verbatim snippet, and a Discovery Tag marking whether it was found independently (NEW) or matched a known
example (KNOWN).

**Mandatory pillars:** 6 (Cross-border data policies) and 7 (Domestic data protection and privacy).
**Also in scope:** all twelve RDTII 2.1 pillars. The sealed live test on 15 October may fall in any of them.
**Economies covered:** [list them]
**Ready for the live test:** the nine economies whose 2025 RDTII database you hold — Thailand, Viet Nam,
Indonesia, China, India, Kazakhstan, Lao PDR, Mongolia, the Russian Federation. State honestly which of these
your tool has actually been run against.

---

## Quick Start

⚠ **A competent programmer must reach a working system from this section alone, on a clean machine, in under
30 minutes — with no help from your team.** That threshold is criterion C4a and it will be tested literally.

### 1. Clone the repository

    git clone https://github.com/[your-org]/[repo-name].git
    cd [repo-name]

### 2. Set up the environment

    # Python 3.10+ required
    python -m venv venv
    source venv/bin/activate        # Windows: venv\Scripts\activate
    pip install -r requirements.txt

### 3. Configure

    cp .env.example .env

Open `.env` and set your two declared engines and your OCR engine. See **Your Two Declared Engines** below.

### 4. Start the interface

    [the single command that starts your interface]

Then open [http://localhost:PORT]. **Everything else happens in the interface** — starting a run, reviewing,
correcting, switching engines, exporting. A reviewer should not need the command line again after this step.

### 5. Verify

Run [economy] on pillar [n] from the interface. Expected: [n] provisions in roughly [n] minutes, exported to
`outputs/`. If you see [known first-run symptom], [fix].

---

## Your Interface

Criteria **C3a (10)** and **C3b (5)** are marked on your interface during the desk review, by someone who did
not build it. Describe how to reach each of the following, with the screen name and the control:

| What a reviewer needs to do | Where it is |
| :---- | :---- |
| Start a run and watch progress in plain words | [screen / control] |
| Open the audit view: a result beside the source text it came from | [screen / control] |
| Follow a row to its official source at the cited article | [screen / control] |
| Accept, reject or correct a row | [screen / control] |
| Switch the AI engine | [screen / control] |
| Export to the RDTII schema | [screen / control] |

**Walkthrough recording:** [link or filename]. Three to four minutes, submitted with your Word document.

---

## Your Two Declared Engines

Required by criterion **C4b (No Vendor Lock-in, 7 points)** and tested again live as **C5b (4 points)**.
Both engines are declared in Section 5 of your Word submission on 30 September and **cannot change afterwards**.

| | Engine A — commercial hosted | Engine B — open weights |
| :---- | :---- | :---- |
| Provider and model | [ ] | [ ] |
| Version / checkpoint | [ ] | [ ] |
| Local or hosted API | [ ] | [ ] |
| Config value | `LLM_PROVIDER=[ ]` `LLM_MODEL=[ ]` | `LLM_PROVIDER=[ ]` `LLM_MODEL=[ ]` |

### Switching between them

The switch must be made **inside the interface**, with no file edited and no command typed. A steward watches
this happen on 15 October; a switch that needs code or configuration scores zero on C5b.

In the interface: [screen name] → [control name] → select the engine.
The underlying abstraction lives in `[src/llm/client.py]`; adding a provider means [one line on how].

### Re-running without fetching

A second pass must read documents already downloaded and fetch nothing new — its document list must be empty.

In the interface: [screen name] → [control name].
Where downloaded documents are cached: `[path]`.

---

## Crawling Politely

Built in and **on by default** — a ministry running this tool should not have to configure it to avoid being
blocked, and on 15 October five tools will be reading the same government sites in the same hour.

| Setting | Value | Where it is set |
| :---- | :---- | :---- |
| Max requests per second per host | 1 | `[file:line]` |
| Parallel requests per host | 1 | `[file:line]` |
| robots.txt respected | yes | `[file:line]` |

---

## Architecture Overview

[Keep your Round 1 diagram, updated. Make the boundary between fetching and reading explicit — the second
pass depends on those being separable.]

### Key modules

| Module | File | Description |
| :---- | :---- | :---- |
| Portal Crawler | `[ ]` | Navigates portals, retrieves source URLs |
| Document Processor | `[ ]` | Download, OCR, structural parsing |
| Retrieval | `[ ]` | Chunking, embedding, search, reranking |
| Mapper | `[ ]` | Maps a provision to an RDTII indicator |
| Interface | `[ ]` | Run control, audit view, review, export |
| Output Writer | `[ ]` | Writes the RDTII schema |

---

## Swapping the OCR Engine

| Engine | Config value | Notes |
| :---- | :---- | :---- |
| [ ] | `[ ]` | [ ] |

Note which of these are proprietary services. Your Section 3 declaration says the core pipeline can run with
no proprietary API — that has to hold for OCR and translation as well as for the language model.

---

## Supported Economies and Portals

| Economy | Official portal | Language | Run end to end? | Notes |
| :---- | :---- | :---- | :---- | :---- |
| [ ] | [ ] | [ ] | [ ] | [ ] |

---

## Output Format

Columns are in this exact order — the same schema as Round 1, plus Language of Source. Do not rename or
reorder; the secretariat validates programmatically.

| # | Column | Required | Description |
| :---- | :---- | :---- | :---- |
| 1 | economy | Required | Official UN country name |
| 2 | law_name | Required | Full official statute name and year |
| 3 | law_number_ref | Optional | Official act or law number (e.g. Act 709, B.E. 2562) |
| 4 | last_amended | Optional | Year of most recent amendment |
| 5 | indicator_id | Required | **RDTII 2.1 code as text: `6.1`, `7.3`, `12.9`. Not "P6-I1".** |
| 6 | article | Required | Exact article and paragraph (e.g. Art. 26(2), s. 16(1)) |
| 7 | discovery_tag | Required | NEW = independent find; KNOWN = in the baseline you hold |
| 8 | location_reference | Optional | PDF page number, or HTML anchor / section path |
| 9 | verbatim_snippet | Required | Exact quoted text — no paraphrasing |
| 10 | mapping_rationale | Optional | Max 300 characters: why this provision maps to this indicator |
| 11 | source_url | Required | Direct URL on the official government portal |
| 12 | confidence | Optional | Model certainty (0.00–1.00) |
| 13 | notes | Optional | OCR issues, bilingual sources, cross-references |
| 14 | language_of_source | Required | Original language of the document — drives C1c |

> **Write indicator IDs as text.** Entered as a number, `12.10` collapses to `12.1` and `4.01` to `4.1` —
> and those are different indicators.

---

## Measured Cost

**Measured costs from real runs — not estimates. Show your working.** Cost is also recorded per run and per
engine during the live hour, so make sure your logging produces it without manual arithmetic.

| Component | Engine used | Measured cost |
| :---- | :---- | :---- |
| OCR | [ ] | $[ ] |
| Embedding | [ ] | $[ ] |
| Mapping — Engine A | [ ] | $[ ] |
| Mapping — Engine B | [ ] | $[ ] |
| Crawling | [ ] | $[ ] |
| **Total, Engine A** | | **$[ ] per document** |
| **Total, Engine B** | | **$[ ] per document** |

**Measured on:** [date] **Benchmark document:** [law, economy, pages]
**Wall-clock:** [ ] seconds per document

The secretariat verifies cost claims against your code. Unexplained discrepancies are flagged.

---

## Known Limitations

Be honest. A tool that flags text it could not read is better built than one that presents everything with
equal confidence, and saying plainly what does not work is marked up, not down.

- **[Limitation]:** [what it means in practice, and which economies or documents it affects]
- **Confidence calibration:** [are your scores calibrated probabilities, or relative? Below what score should
  a human check?]

---

## Running the Test Suite

    pytest tests/

| Test file | What it tests |
| :---- | :---- |
| `[ ]` | [ ] |

---

## Reproducing Your Submitted Evidence

    [command]

Lets a reviewer regenerate the rows in your submitted workbook and compare them against what you filed.

---

## Team

| Role | Name | Responsibility |
| :---- | :---- | :---- |
| Technical Lead | [ ] | AI architecture, OCR, pipeline |
| Substantive Lead | [ ] | Legal and policy analysis, output QA |

---

## Licence

Released under the **Apache License 2.0**, as required. See [LICENSE](LICENSE) for the full text.

---


The release tag you record is the version that runs on 15 October. Settings may change on the day; code may not.

---

## Acknowledgements

Built for the UN Global Hackathon on AI for Digital Trade Regulatory Analysis, organised by ESCAP and KMITL.

