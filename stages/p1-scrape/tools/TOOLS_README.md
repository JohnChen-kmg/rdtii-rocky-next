# tools/

Scripts that work on run folders after a crawl. They send no request to any portal, and they never write into a
run folder except to add the audit's two files. Both are part of the convention (`CONVENTIONS.md` steps 3 and 6,
decision 17) and apply to every country.

| Script | What it does | Writes |
| :---- | :---- | :---- |
| `audit_run.py <run>` | **Content check.** Opens every stored file in a run (the first 2 pages of a PDF, the head of an HTML page) and flags the files that are not, or may not be, the law's text: a repeal notice, another act's text, another language than recorded, a gazette notice, a scan with no text layer, a landing page. Lists the fetches that failed. Country rules live in `RULES` (Malaysia today); the generic flags apply everywhere | `audit.json`, `audit.md` in the run folder |
| `merge_corpus.py --outputs outputs/<CC> --out outputs/<CC>/<CC>_corpus_<date>` | **Corpus merge.** Builds one folder in the Hand-off #1 shape from every run of a country, newest first: the newest copy of each law wins, older copies are listed in `superseded.jsonl`, audit flags travel with the rows. Never merges into a run. `--exclude-flags repeal_notice,other_act_text` leaves flagged rows out; `--hardlink` links instead of copying | A new corpus folder: `manifest.csv`, `manifest.jsonl`, `raw/`, `links_used/`, `superseded.jsonl`, `corpus_meta.json`, `CORPUS_NOTE.md` |
| `test_tools.py` | 22 offline tests of both, on hand-made PDFs and run folders | |

## Running them

They import the engine (`p1_scrape.manifest`, `p1_scrape.models`), so they run from a stage root with the tools
copied into its `tools/` folder, like the repo's other tools:

```
STAGE=<stage root>                                  # the repo's stages/p1-scrape, or a sandbox copy
cp <ws>/tools/audit_run.py <ws>/tools/merge_corpus.py $STAGE/tools/
cp <ws>/tools/test_tools.py $STAGE/tests/test_tools.py
cd $STAGE
python -m pytest -q tests/test_tools.py                              # 22 passed
PYTHONPATH=src python tools/audit_run.py <ws>/outputs/MY/MY_ws_2026-09-14
PYTHONPATH=src python tools/merge_corpus.py --outputs <ws>/outputs/MY --out <ws>/outputs/MY/MY_corpus_$(date -u +%F)
```

`audit_run.py` needs `pypdfium2` (the engine's own PDF library). A missing file or an unreadable PDF is a finding
(`unreadable_file`), not a crash.

## What the audit flags mean

| Flag | Meaning | Wrong file? |
| :---- | :---- | :---- |
| `fetch_failed` | The crawl log records the fetch as failed and no row stored it (listed under "missing") | Missing |
| `store_failed` | The bytes arrived but the engine could not write them: a path over Windows' 260-character limit (a law name of about 140 characters or more), a full disk. Listed under "missing"; the portal is not the cause | Missing |
| `orphan_file` | A file under `raw/` that no manifest row names: written by a crawl stopped before its next checkpoint (the engine writes the manifest every 10 stored documents). Not part of the run; a resume fetches the document again | Not output |
| `no_text_layer` | The first pages have no usable text: a scan, OCR needed | Unreadable as is |
| `unreadable_file` | The file cannot be opened | Yes |
| | **On Windows, check the path before believing it.** A document whose folder name is long enough to push the path past 260 characters cannot be opened from the workshop path, and the audit calls it unreadable. Run the audit through a `subst` drive (`subst R: <ws>`, then `tools/audit_run.py R:/outputs/...`) and the flag goes away. Singapore's run of 2026-09-15 had exactly one such row | |
| `duplicate_content` | The same bytes under two doc_ids in one run | One of them |
| `short_principal` | A principal act of at most 4 pages: usually a repeal notice, sometimes a short act | Look |
| `one_page_principal` | A one-page principal-act file whose text does not say "repealed": a notice whose words the rules missed (OCR), or a scan | Look |
| `html_stored` (MY) | An HTML page where the portal serves documents (a landing page). Only where the rule set says HTML is a fault; on a portal where HTML is a form of the law nothing is flagged | Usually |
| `repeal_notice` (MY) | A short principal-act file whose text says the act is repealed or superseded | Yes: the notice, not the act |
| `other_act_text` (MY) | The first pages never give the row's act number but give another act's | Yes |
| `language_mismatch` (MY) | The text is in a language other than the one the link list recorded | Yes, for the language column |
| `gazette_notice` (MY) | A gazette notification stored as a principal act | Yes |
| `not_an_amending_act` (MY) | An amending-act file that is a gazette supplement never naming that act | Yes |
| `parent_not_named` (MY) | An amendment recorded as a P.U. order whose first pages never name the act it amends: often a bundle of notices, the right one further in | Look |
| `gazette_print` (MY) | An amending act stored as its gazette print: cover first, the act from page 2 | No |
| `subsidiary_amendment` (MY) | An "amending act" row that is a P.U. order, as the portal's amendment listing gives it | No |
| `empty_document` | A stored HTML file whose readable text is almost nothing: the markup is there, the words are not. This is how a landing page is caught in a country whose rules are not written yet | Yes |
| `title_not_in_text` (SG, AU) | Fewer than half the law title's distinctive words appear in the file | Yes, unless renamed |
| `other_act_text` (SG, AU) | The law numbers printed on the page do not include this row's | Yes |
| `repeal_notice` (SG) | A short principal-act file whose text says the act is repealed, where the act's own name does not say it is a repeal act | Yes |
| `short_act_as_printed` (SG) | A short act printed in full, with its title and either the statutes heading or its arrangement of sections: the Supply Acts, the Pensions (Expatriate Officers) Act | No |
| `gazette_print` (SG) | An amending act as published in the Acts Supplement to the gazette, which is the form the portal publishes it in | No |
| `act_as_passed` (SG) | A principal act stored as its Acts Supplement print rather than the consolidated text | Look |
| `as_made_short_act` (AU) | A short as-made Act that prints its own number: the whole Act, not a fragment | No |
| `renamed_since_enactment` (AU) | The file carries this Act's number under the title it was enacted with: the Act has been renamed (the Protection of Word "Anzac" Act 1920 prints as "War Precautions Act Repeal") | No |

**Singapore and Australia, calibrated 2026-09-16.** The title test came first: on Singapore's 739 documents 737
carry every distinctive word of their title and 2 carry four of five; on Australia's 1,277, 1,208 carry every word.
So "fewer than half" is the threshold, and it flags nothing in either corpus today. What the rules then found:

| Corpus | Flagged | What they are |
| :---- | ----: | :---- |
| `SG_corpus_2026-09-16` (738) | 27 | 22 amending acts in their gazette form, 5 short acts printed in full. **No wrong file** |
| `AU_corpus_2026-09-16` (1,277) | 91 | 88 as-made short Acts, 2 Acts renamed since enactment, 1 whose scan reads "No. 114 of ll73" and so cannot be matched |

Two drafts were discarded on the way, which is the point of calibrating against the corpus rather than a sample.
A `revised_edition` flag fired on 488 of Singapore's 739 documents: that is a property of the print, not a
finding, so it went. And Australia's number test first flagged two files as another Act's text because the first
number on the page belongs to the Act being amended; it now asks whether this Act's own number appears anywhere,
and reads the page twice, once with the spaces taken out, because the register's older scans print "No. 1 5 o f
1908".

Calibration, 2026-09-15, on the 1,311 files of `MY_ws_2026-09-14`: 132 rows flagged; 116 carry a wrong-file or
unreadable flag (76 repeal notices, 29 scans, 7 Malay files behind English links, 5 other acts' texts, 2 landing
pages, 1 gazette notice, 1 bundle: 121 flags on 116 rows, 4 rows carrying more than one); the rest are
informational. A row with no link row (5 in that run, all 17 in `MY_ws_2026-09-13`) gets its kind from the law
number. The first draft of the rules flagged 53 files as
another act's text; reading them showed "Revision of Laws Act **1968**" and gazette covers being read as act
numbers, which is why the rules now exclude years and treat gazette prints separately.

## Adding a country's rules

Add a key to `RULES` in `audit_run.py` with the act-number pattern, the repeal, gazette and language markers, then
a test in `test_tools.py` on a hand-made page for each flag. Without a rule set only the generic flags apply, which
is still worth running.

## Hand-back

Both scripts and the tests go to the repo as `stages/p1-scrape/tools/audit_run.py`, `tools/merge_corpus.py` and
`tests/test_tools.py` (`countries/README.md`, hand-back table). `pypdfium2` is already in `requirements.txt`.
