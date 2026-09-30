# 中国人民银行 + 国家外汇管理局 · pbc.gov.cn, safe.gov.cn

> **Layer 2a, added 2026-09-21.** This ministry's departmental rules (令) are being indexed from the 国务院公报 on
> `www.gov.cn`, which publishes them officially under 立法法 第九十七条 and permits us. **Until the recall check
> confirms the gazette is complete, keep collecting as listed below.** Once it does, what is left here is
> PBOC's 银发 and SAFE's 汇发 normative documents, and their annexes — the payment caps are one. The check's result will be in `../../auto/gazette/recall.md`.

## Start here: the whole section, not only our list

**Collect every relevant instrument in these sections**, not only the documents listed further down. The
list below is what we already know is there; use it afterwards to check nothing was missed. A curated list
records what we already knew, and on CAC it missed 42 of 68 tier-2 documents.

| Section | Address | How the address is known |
| :---- | :---- | :---- |
| 人民银行 条法司 · 规章 (令) | https://www.pbc.gov.cn/tiaofasi/144941/144957/index.html | parent of verified documents |
| 人民银行 条法司 · 规范性文件 (银发) | https://www.pbc.gov.cn/tiaofasi/144941/3581332/index.html | parent of verified documents |
| 国家外汇管理局 · 政策法规 | https://www.safe.gov.cn/safe/zcfg/index.html | **verified 2026-09-21, HTTP 200** |

**What counts as relevant.** Anything touching data, cybersecurity, telecom, the internet, e-commerce,
payments, digital trade, foreign investment in those sectors, ICT goods, or standards for them. Skip what
plainly is not — energy pricing, agriculture, construction, internal administration. If unsure, take it:
a document collected and not needed costs a line in the sheet; a document needed and missed costs an
indicator. Add each one to `provenance.tsv` as a new row.

These hosts refuse our client, so none of these addresses could be opened by the tool. Where one has moved,
navigate from the site's 政策法规 or 政务公开 menu, and note the new address in `notes`.

**MANUAL — you download these, in a browser.**

Why not automatic:

- `www.pbc.gov.cn` — robots.txt: User-agent: * / Disallow: /
- `www.safe.gov.cn` — no robots.txt, but two documents do not justify a tool; kept with PBOC

## How to fill this folder

1. Open each link in `provenance.tsv`.
2. Save the file **into `raw/`** — never beside this README. `raw/` is kept out of git by `.gitignore`;
   anything saved elsewhere in this folder would be committed.
3. **If the page has an attachment (附件, `.doc`, `.pdf`), save the attachment too.** On these sites the
   law is often *in* the attachment and the page is only a wrapper — the MIIT telecom catalogue page carries
   572 characters; its `.doc` carries the whole classification.
4. Fill in four columns: `file_saved_as`, `fetched_on`, **`version_date_on_document`** (the 施行 or 修订 date
   printed on the document itself, not today's date), and `notes`.

## Documents to collect: 7

1. 条码支付业务规范（试行） — 银发〔2017〕296号  
   https://www.pbc.gov.cn/tiaofasi/144941/3581332/3589728/index.html
2. 非银行支付机构网络支付业务管理办法 — 人民银行公告〔2015〕第43号  
   https://www.pbc.gov.cn/tiaofasi/144941/3581332/3588090/index.html
3. 银行卡清算机构管理办法 — 人民银行+金融监管总局 令〔2025〕第2号  
   https://www.pbc.gov.cn/zhengwugongkai/4081330/4406346/4406348/2025092319185575978/index.html
4. 非银行支付机构监督管理条例实施细则 — 人民银行令〔2024〕第4号  
   https://www.pbc.gov.cn/tiaofasi/144941/144957/5414094/index.html
5. 支付机构外汇业务管理办法 — 外汇局 汇发〔2019〕13号  
   https://www.safe.gov.cn/safe/2019/0429/13114.html
6. 征信业务管理办法 — 人民银行令〔2021〕第4号  
   https://www.pbc.gov.cn/tiaofasi/144941/144957/4354378/index.html
7. 虚拟货币风险通知 — 八部门 银发〔2026〕42号  
   https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html
