# 海关总署 · customs.gov.cn

## Start here: the whole section, not only our list

**Collect every relevant instrument in these sections**, not only the documents listed further down. The
list below is what we already know is there; use it afterwards to check nothing was missed. A curated list
records what we already knew, and on CAC it missed 42 of 68 tier-2 documents.

| Section | Address | How the address is known |
| :---- | :---- | :---- |
| 海关总署公告 | https://www.customs.gov.cn/customs/302249/302266/302267/index.html | the index page named by the research agent |

**What counts as relevant.** Anything touching data, cybersecurity, telecom, the internet, e-commerce,
payments, digital trade, foreign investment in those sectors, ICT goods, or standards for them. Skip what
plainly is not — energy pricing, agriculture, construction, internal administration. If unsure, take it:
a document collected and not needed costs a line in the sheet; a document needed and missed costs an
indicator. Add each one to `provenance.tsv` as a new row.

These hosts refuse our client, so none of these addresses could be opened by the tool. Where one has moved,
navigate from the site's 政策法规 or 政务公开 menu, and note the new address in `notes`.

**MANUAL.** `www.customs.gov.cn` answers 412 to an honest client, and Chrome rejects its certificate chain
(`ERR_CERT_AUTHORITY_INVALID`), so the host itself is manual.

**What to take from the 公告 section:** customs lists and supervision rules for cross-border e-commerce
(1210, 9610, 9710, 9810), anything on ICT goods, and any import or export list. This is an announcement stream,
not a bounded rules library, so take the relevant ones rather than the whole stream.

**The three documents already on our list need no download here** — each has a permitted mirror the tool
fetches:

| Document | Fetched from |
| :---- | :---- |
| 海关总署公告 2018年第194号 (1210 / 9610 retail supervision) | `gov.cn` → `auto/govcn/` |
| 海关总署公告 2020年第75号 (9710 / 9810 B2B export pilot) | MOFCOM 全球法规库 → `auto/mofcom/` |
| 海关总署公告 2021年第47号 (nationwide roll-out) | `mofcom.gov.cn` → `auto/mofcom/` |

**Only use this folder if you want the customs.gov.cn originals** — for example, to confirm a mirror matches.
Save them into `raw/` and add a line to `provenance.tsv`.

Do not work around the certificate error. Disabling certificate validation is a security boundary, not a
politeness setting.
