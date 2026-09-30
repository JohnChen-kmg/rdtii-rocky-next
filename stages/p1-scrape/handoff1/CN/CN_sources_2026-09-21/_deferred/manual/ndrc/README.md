# 国家发展和改革委员会 · ndrc.gov.cn

> **Layer 2a, added 2026-09-21.** This ministry's departmental rules (令) are being indexed from the 国务院公报 on
> `www.gov.cn`, which publishes them officially under 立法法 第九十七条 and permits us. **Until the recall check
> confirms the gazette is complete, keep collecting as listed below.** Once it does, what is left here is
> the attachments: the negative-list and encouraged-list PDFs. The check's result will be in `../../auto/gazette/recall.md`.

## Start here: the whole section, not only our list

**Collect every relevant instrument in these sections**, not only the documents listed further down. The
list below is what we already know is there; use it afterwards to check nothing was missed. A curated list
records what we already knew, and on CAC it missed 42 of 68 tier-2 documents.

| Section | Address | How the address is known |
| :---- | :---- | :---- |
| 发展改革委令 — every 令, including the negative lists | https://www.ndrc.gov.cn/xxgk/zcfb/fzggwl/index.html | parent of verified documents |
| 政策发布 — all kinds | https://www.ndrc.gov.cn/xxgk/zcfb/index.html | parent of the section above |

**What counts as relevant.** Anything touching data, cybersecurity, telecom, the internet, e-commerce,
payments, digital trade, foreign investment in those sectors, ICT goods, or standards for them. Skip what
plainly is not — energy pricing, agriculture, construction, internal administration. If unsure, take it:
a document collected and not needed costs a line in the sheet; a document needed and missed costs an
indicator. Add each one to `provenance.tsv` as a new row.

These hosts refuse our client, so none of these addresses could be opened by the tool. Where one has moved,
navigate from the site's 政策法规 or 政务公开 menu, and note the new address in `notes`.

**MANUAL — you download these, in a browser.**

Why not automatic:

- `www.ndrc.gov.cn` — 403 from a WAF on robots.txt

## How to fill this folder

1. Open each link in `provenance.tsv`.
2. Save the file **into `raw/`** — never beside this README. `raw/` is kept out of git by `.gitignore`;
   anything saved elsewhere in this folder would be committed.
3. **If the page has an attachment (附件, `.doc`, `.pdf`), save the attachment too.** On these sites the
   law is often *in* the attachment and the page is only a wrapper — the MIIT telecom catalogue page carries
   572 characters; its `.doc` carries the whole classification.
4. Fill in four columns: `file_saved_as`, `fetched_on`, **`version_date_on_document`** (the 施行 or 修订 date
   printed on the document itself, not today's date), and `notes`.

## Documents to collect: 5

1. 外商投资准入特别管理措施（负面清单）（2024年版） — 发改委+商务部令 2024年第23号  
   https://www.ndrc.gov.cn/xxgk/zcfb/fzggwl/202409/t20240907_1392875.html
2. 自由贸易试验区外商投资准入负面清单（2021年版） — 发改委+商务部令 2021年第48号  
   https://www.ndrc.gov.cn/xxgk/zcfb/fzggwl/202112/t20211227_1310019.html
3. 鼓励外商投资产业目录（2025年版） — 发改委+商务部令 2025年第37号  
   https://www.ndrc.gov.cn/xxgk/zcfb/fzggwl/202512/t20251224_1402564.html
4. 外商投资安全审查办法 — 发改委+商务部令 2020年第37号  
   https://www.ndrc.gov.cn/xxgk/zcfb/fzggwl/202012/t20201219_1255025.html
5. 必须招标的工程项目规定 — 发改委令第16号  
   https://www.ndrc.gov.cn/xxgk/zcfb/fzggwl/201803/t20180330_960858_ext.html
