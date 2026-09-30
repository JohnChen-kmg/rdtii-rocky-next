# China's legal sources

**Refocused 2026-09-22.** The national law database is the core of this corpus. Layer 2 is narrowed to the three
key areas the developer named — CAC, MIIT and Customs — and everything else is set aside in `_deferred/`,
**moved, not deleted**, with how to bring each part back.

## Why the focus changed

Two findings of 2026-09-21, in the developer's words: *"some policy papers are less important than the law
database"*, and the value of scraping everything is doubtful given the nature of the RDTII.

1. **Most of a general ministry's output is irrelevant to the index.** The share of each crawled section whose
   titles match the index's topics: **CAC 88%**, MOFCOM's 规章库 22%, SAMR's 法规司 18%. A regulator whose whole
   remit is digital is worth taking whole; a ministry that also regulates fuel, catering and meat reserves is not.
   PBOC's database — monetary policy, banking supervision, credit, long documents — would be worse.
2. **The State Council Gazette is not a proxy for the law in force.** It is authoritative for a rule's text *as
   issued*, but it is not consolidated (an amendment arrives years later as a separate 修改决定), carries no
   status (a repealed rule stays, unmarked), and may be incomplete (立法法 第九十七条 also allows a department's own
   gazette). It is a discovery log, not the text of record. **The national database is consolidated, current and
   carries status** — which is why it is the core.

## Layer 1 — the core

| Folder | Source | General link | What is in it |
| :---- | :---- | :---- | :---- |
| `manual/npc-database/` | 国家法律法规数据库 · National Database of Laws and Regulations | https://flk.npc.gov.cn/ | **945 documents** — 942 `.docx`, 3 `.doc` — in 11 bulk-download archives, downloaded by hand 2026-09-21 22:25–22:30 |

**Every file name carries its version date** — `中华人民共和国消防法_20210429.docx` — so the provenance rule
("record the date printed on the document, not the download date") is met by the database itself. One provenance
record for the whole export is enough. `robots.txt` forbids automated collection of this host, so it is downloaded
by hand and always will be.

## Layer 2 — the key areas

| Folder | Source | General link | Mode | Indicators served | State |
| :---- | :---- | :---- | :---- | ----: | :---- |
| `auto/cac/` | 国家互联网信息办公室 · CAC | https://www.cac.gov.cn/ | auto | **16** | **111 documents, done** — its whole 政策法规 index, 88% relevant |
| `manual/miit/` | 工业和信息化部 · MIIT | https://www.miit.gov.cn/ | **by hand** | **12** | 13 listed, and its rules sections to go through — see its README |
| `manual/customs/` | 海关总署 · Customs | https://www.customs.gov.cn/ | **by hand** | 1 | its 公告 section — see its README |
| `auto/govcn/` | 中国政府网 · gov.cn | https://www.gov.cn/ | auto | — | 6 documents, done: the permitted copies of key-area documents — MIIT's 令24, Customs' 1210/9610 notice, CAC's 个人信息出境认证办法 (the third cross-border route, pillar 6) |

MIIT and Customs are manual because their hosts refuse an honest client (403, and 412 with a certificate Chrome
rejects). Driving a browser to get past that is the circumvention the developer ruled out on 2026-09-21.

**For MIIT, take only the information and communications side.** Skip what layer 1 already holds — the laws and
administrative regulations MIIT administers are in the national database — and skip the industrial side. Keep
items touching 电信, 通信, 互联网, 网络, 无线电, 频率, 卫星, 域名, 数据, 个人信息, 软件, 集成电路, 进网, 码号,
工业互联网, 车联网 or 智能网联汽车. **Save attachments**: the telecom catalogue is a `.doc`, and the page is only a
wrapper around it.

**Save every file into that folder's `raw/`.** `.gitignore` excludes `outputs/**/raw/`; a file saved anywhere else
in this tree would be committed to git. Each manual folder has a `provenance.tsv` already filled in: add
`file_saved_as`, `fetched_on`, `version_date_on_document` and `notes` per row.

## Deferred — set aside, not deleted

`_deferred/` holds the other twelve sources, with their manual/auto split intact: PBOC and SAFE, NDRC, MPS, NHC and
the standards platform to collect by hand; SAMR, MOFCOM, OSCCA, MOF and the tariff commission, CNCA, the sectoral
publishers and the gazette index already partly collected. **What each holds, why it was set aside and how to bring
it back is in `_deferred/README.md`.** Every deferred source stays on the watch list, so every run of the tool
still says it is not being checked.

## The rule, for any source

| If the host… | then |
| :---- | :---- |
| forbids us in robots.txt | **manual** — `flk.npc.gov.cn`, `pbc.gov.cn`, `sousuo.www.gov.cn` |
| refuses its own robots.txt, or refuses an honest client | **manual** — permission cannot be established (MIIT, NDRC, Customs, NHC) |
| permits us, or publishes no robots.txt and serves us | **auto** |

Automatic requests go one at a time per host, **8 to 12 s apart**, under a User-Agent that says what we are. A
refusal is recorded and left alone — never retried with another client. The rule is enforced in code
(`countries/cn-china/tools/polite.py`), not only described here.

## To re-run or bring something back

```
python countries/cn-china/tools/collect.py --watchlist        # what the tool does not see, fetch nothing
python countries/cn-china/tools/collect.py cac                # re-read CAC's index; resumes
python countries/cn-china/tools/collect.py samr               # a deferred source: writes into _deferred/auto/samr
```

The collector finds each source where it now lives, so running a deferred source continues it in `_deferred/`
rather than recreating an empty folder here. To make one active again, move its folder back from `_deferred/`.

## What no folder here will hold

- **The blocking list (9.1)** — published in no instrument at any tier.
- **银支付〔2017〕209号** and the **full text of 工信部联通信〔2023〕59号** — real, operative, never published.
- **Most 重要数据目录** — drawn up region by region and department by department, largely unpublished.

Record these as *cited but unpublished*, never as absent. See `../CN_corpus_plan.md`, layer 3.
