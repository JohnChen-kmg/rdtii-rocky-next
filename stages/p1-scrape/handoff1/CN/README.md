# outputs/CN/

**`flk.npc.gov.cn` is never crawled.** Its robots.txt forbids automated collection in as many words —
"禁止使用任何自动化工具、脚本、爬虫程序采集或复制网站数据" — followed by `Disallow: /`
(`countries/_finale-survey/cn-china.md`). **Nothing in this folder came from that host by tool, and nothing ever
will.** The national database is downloaded by hand.

**That prohibition is specific to that host, and on 2026-09-21 the distinction started to matter.** China's
operative tier — 部门规章 and 规范性文件 — is not in the national database at all, and the ministries that issue
it publish their own indexes. Each was checked before anything was fetched:

| Host | robots.txt, read 2026-09-21 | What we do |
| :---- | :---- | :---- |
| `flk.npc.gov.cn` | forbids automated collection | **Hand only** |
| `www.pbc.gov.cn` | `User-agent: *` / `Disallow: /` (Baiduspider only) | **Hand only** |
| `www.cac.gov.cn` | permits: only `/zfz/`, `/wxb_zfz/`, `/wxzf/` and one video path disallowed | **Crawled** |
| `www.gov.cn` | permits: legacy paths only | Crawlable |
| `www.miit.gov.cn`, `www.ndrc.gov.cn` | 403 to any client, robots.txt included | **Hand** — permission cannot be established |
| `www.customs.gov.cn` | 412, and a certificate Chrome rejects | **Hand**, via mirrors |
| SAMR, MOFCOM, OSCCA, MOF, CNCA, NHC, MOST | none published | Nothing disallowed; open question |

| Folder | Date | What it is |
| :---- | :---- | :---- |
| `CN_manual_2026-09-20` | 2026-09-20 | Five administrative regulations, saved by hand to test whether that tier answers the index's indicators or only states the rule and delegates the number |
| **`CN_ws_2026-09-21`** | 2026-09-21 | **The first Chinese crawl.** CAC's 政策法规 index, 111 of 111 documents, no failures, 12 minutes at 6 s. **42 of its 68 tier-2 documents were absent from our hand-built checklist** |
| `CN_layer2_2026-09-21` | 2026-09-21 | A six-document browser probe of MIIT, NDRC and Customs, run before the rule above was settled. It retrieved the 电信业务分类目录 `.doc` and two PDFs. **Under the rule now in force these five should be re-collected by hand**; they are kept as the record of a method that was tested and set aside |
| **`CN_sources_2026-09-21`** | 2026-09-21 | **The corpus, one folder per source.** Layer 1: the national database, **945 documents** downloaded by hand. Layer 2: CAC (111, automatic), MIIT and Customs (by hand), gov.cn (6). Twelve more sources set aside in `_deferred/`, moved not deleted. **Start with its `README.md`** |
| `CN_sources_2026-09-21_to_2026-09-22` | 2026-09-22 | **The first update check** (`countries/cn-china/tools/update.py`): 12 requests, all 200. CAC 0 new, 0 gone; gov.cn 0 changed. Layer 1 not compared — no fresh export was passed |

**Why each source is in or out** — the source-selection record — is `countries/cn-china/SOURCES.md`. **How to run
the collector, the updater and the offline tools** is `countries/cn-china/WORKFLOW.md`.

The reasoning for what to collect and why is in `CN_corpus_plan.md`; the verified links, with their corrections,
in `CN_layer2_links.md`.

**What China's database can and cannot answer**, against the instrument's 61 indicators:
`countries/_finale-survey/explore-2026-09-20/cn-china-coverage.md`.
