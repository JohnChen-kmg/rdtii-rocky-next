# 国家卫生健康委员会 · nhc.gov.cn

> **Layer 2a, added 2026-09-21.** This ministry's departmental rules (令) are being indexed from the 国务院公报 on
> `www.gov.cn`, which publishes them officially under 立法法 第九十七条 and permits us. **Until the recall check
> confirms the gazette is complete, keep collecting as listed below.** Once it does, what is left here is
> its 国卫 notices. The check's result will be in `../../auto/gazette/recall.md`.

## Start here: the whole section, not only our list

**Collect every relevant instrument in these sections**, not only the documents listed further down. The
list below is what we already know is there; use it afterwards to check nothing was missed. A curated list
records what we already knew, and on CAC it missed 42 of 68 tier-2 documents.

| Section | Address | How the address is known |
| :---- | :---- | :---- |
| 卫生健康委 · 政策文件 | https://www.nhc.gov.cn/wjw/c100175/ | parent of a verified document |

**What counts as relevant.** Anything touching data, cybersecurity, telecom, the internet, e-commerce,
payments, digital trade, foreign investment in those sectors, ICT goods, or standards for them. Skip what
plainly is not — energy pricing, agriculture, construction, internal administration. If unsure, take it:
a document collected and not needed costs a line in the sheet; a document needed and missed costs an
indicator. Add each one to `provenance.tsv` as a new row.

These hosts refuse our client, so none of these addresses could be opened by the tool. Where one has moved,
navigate from the site's 政策法规 or 政务公开 menu, and note the new address in `notes`.

**MANUAL — you download these, in a browser.**

Why not automatic:

- `www.nhc.gov.cn` — 412 to plain clients

## How to fill this folder

1. Open each link in `provenance.tsv`.
2. Save the file **into `raw/`** — never beside this README. `raw/` is kept out of git by `.gitignore`;
   anything saved elsewhere in this folder would be committed.
3. **If the page has an attachment (附件, `.doc`, `.pdf`), save the attachment too.** On these sites the
   law is often *in* the attachment and the page is only a wrapper — the MIIT telecom catalogue page carries
   572 characters; its `.doc` carries the whole classification.
4. Fill in four columns: `file_saved_as`, `fetched_on`, **`version_date_on_document`** (the 施行 or 修订 date
   printed on the document itself, not today's date), and `notes`.

## Documents to collect: 2

1. 人口健康信息管理办法（试行） — 卫计委 国卫规划发〔2014〕24号  
   http://www.nhc.gov.cn/guihuaxxs/gongwen12/201405/783ec8adebc6422bbebdf79db3868d0b.shtml
2. 国家健康医疗大数据标准、安全和服务管理办法（试行） — 卫健委 国卫规划发〔2018〕23号  
   https://www.nhc.gov.cn/wjw/c100175/201809/a3223ef7768140a786b308c2064de14b.shtml
