# 工业和信息化部 · miit.gov.cn

> **A key area, 2026-09-22.** Collect MIIT here, by hand — its rules as well as its notices. An earlier note said
> the 国务院公报 might replace the hand collection of MIIT's 令. It will not: the gazette gives a rule's text as
> issued, not the consolidated text in force, and it has been deferred. **Take only the information and
> communications side**, skip laws and administrative regulations (they are in layer 1), and **save attachments**.

## Where this folder stands, 2026-09-22

The 法律法规 section was walked in full by the developer — **all seven pages, 165 items** — and triaged offline
against layer 1 and the CAC set (`triage_flfg_2026-09-22.md`, `triage_flfg_pages2-7_2026-09-22.md`).
**18 were worth taking, 11%.** All 18 are in `raw/`, with their source URLs and page dates recorded in
`provenance.tsv`. Four items on that list were the superseded version of something already held, and are
recorded as such rather than taken as the text in force.

**Closed 2026-09-22.** 15 documents were saved again as HTML and now carry their text; 21 text-less prints were
deleted once a readable replacement existed; 6 were fetched from gov.cn and CAC into `mirror_permitted/`, two of
them **newer versions than MIIT's own list can show**; and the 电信业务分类目录 attachment (`4564599.doc`, 50,194
characters) is in hand. What remains open is on the sheet: 电信网码号资源管理办法 (held only as a text-less print),
the 2024 令68 进网管理办法, and four documents declined by the developer — among them the only source for 5.1.

**The larger point, for whoever picks this up: 法律法规 is the least MIIT-specific category on the site.** It holds
the laws MIIT did *not* write, which is why 147 of its 165 items were tobacco, defence, vehicles or already in layer 1. Of the 13 MIIT documents
verified by link in this folder, **only 2 appear on it** (令42 and 令43). The list also stops at 2022-01-29,
so nothing since — the 2022 data-security measures, 令68 of 2024, the 2024 opening pilot — can be found
there at all. **The rule tier lives in the sibling categories, 部门规章 and 规范性文件**, in the same
文件性质分类 menu. Those are not yet walked, and they are where the yield should be.

## Start here: the whole section, not only our list

**Collect every relevant instrument in these sections**, not only the documents listed further down. The
list below is what we already know is there; use it afterwards to check nothing was missed. A curated list
records what we already knew, and on CAC it missed 42 of 68 tier-2 documents.

| Section | Address | How the address is known |
| :---- | :---- | :---- |
| **政策 · 文件性质分类 · 法律法规** — MIIT's documents classified by type; the best entry point. Its sibling categories in the same menu (部门规章, 规范性文件) are where MIIT's own instruments sit | https://www.miit.gov.cn/zc/wjxzfl/flfg/index.html | **found by the developer in a browser, 2026-09-22** |
| 政策文件 · 法律法规 — MIIT's 令 (令42 and 令43 sit here) | https://www.miit.gov.cn/zwgk/zcwj/flfg/index.html | parent of verified documents |
| 政策法规 · 信息通信类 (the 2024 consolidated 令68 sits here) | https://www.miit.gov.cn/zcfg/xxtxl/index.html | parent of a verified document |
| 文件发布 · 通告 (the telecom catalogue and the 2024 opening pilot) | https://www.miit.gov.cn/zwgk/zcwj/wjfb/tg/index.html | parent of verified documents |
| 文件发布 · 通知 | https://www.miit.gov.cn/zwgk/zcwj/wjfb/tz/index.html | parent of verified documents |

**What counts as relevant.** Anything touching data, cybersecurity, telecom, the internet, e-commerce,
payments, digital trade, foreign investment in those sectors, ICT goods, or standards for them. Skip what
plainly is not — energy pricing, agriculture, construction, internal administration. If unsure, take it:
a document collected and not needed costs a line in the sheet; a document needed and missed costs an
indicator. Add each one to `provenance.tsv` as a new row.

These hosts refuse our client, so none of these addresses could be opened by the tool. Where one has moved,
navigate from the site's 政策法规 or 政务公开 menu, and note the new address in `notes`.

**MANUAL — you download these, in a browser.**

Why not automatic:

- `www.miit.gov.cn` — 403 to any honest client, robots.txt included
- `domain.miit.gov.cn` — MIIT subdomain
- `jwxk.miit.gov.cn` — MIIT subdomain
- `gdca.miit.gov.cn` — MIIT subdomain
- `shca.miit.gov.cn` — MIIT subdomain
- `hca.miit.gov.cn` — MIIT subdomain

## How to fill this folder

> **Save the page the right way, or the file is useless to stage 2.** In the browser's print dialog, set the
> destination to the browser's own **"Save as PDF" / 另存为 PDF**, *not* to the **"Microsoft Print to PDF"**
> printer. Microsoft's printer converts every Chinese glyph to a vector outline: the file looks perfect and
> contains no text at all — no fonts, no text blocks, about a thousand drawn curves a page. Nothing can read
> it but a human eye. Saving the page instead with Ctrl+S as **Webpage, Single File (.mhtml)** also keeps the
> text, and matches how CAC's documents are stored. **Check one file before doing a batch**; the first 18
> saved here on 2026-09-22 all had to be redone, and 21 of them were later deleted as unreadable.

1. Open each link in `provenance.tsv`.
2. Save the file **into `raw/`** — never beside this README. `raw/` is kept out of git by `.gitignore`;
   anything saved elsewhere in this folder would be committed.
3. **If the page has an attachment (附件, `.doc`, `.pdf`), save the attachment too.** On these sites the
   law is often *in* the attachment and the page is only a wrapper — the MIIT telecom catalogue page carries
   572 characters; its `.doc` carries the whole classification. Proved again on 2026-09-22: 无线电频率划分规定
   is a 2-page wrapper whose `.doc` attachment runs to 230 pages and 144,302 words.
4. Fill in four columns: `file_saved_as`, `fetched_on`, **`version_date_on_document`** (the 施行 or 修订 date
   printed on the document itself, not today's date), and `notes`.

## Documents to collect: 13

1. 电信业务分类目录（2015年版） — 工信部通告, 信管〔2015〕484号  
   https://www.miit.gov.cn/zwgk/zcwj/wjfb/tg/art/2020/art_e98406cd89844f7e92ea1bcf3b5301e0.html
2. 电信业务分类目录 修订公告 — 工信部, no number printed  
   https://www.miit.gov.cn/zwgk/zcwj/wjfb/tg/art/2020/art_b6a54a60f9c6471cb3a996106fc09cd5.html
3. 电信业务经营许可管理办法 — 工信部令第42号  
   https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2020/art_ad4a7f072a5e4e2aab49b7817c49f5a6.html
4. 增值电信业务扩大对外开放试点通告 — 工信部 通信函〔2024〕107号  
   https://www.miit.gov.cn/zwgk/zcwj/wjfb/tg/art/2024/art_2326271e1b424e09b6e5924ad2948863.html
5. 互联网域名管理办法 — 工信部令第43号  
   https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2017/art_43ec3819b2d04a31ad2c1c81c3f6100b.html
6. 关于规范互联网信息服务使用域名的通知 — 工信部信管〔2017〕264号  
   https://www.miit.gov.cn/jgsj/xgj/hlwgl/art/2020/art_f4e6b2b5bc6b400ea35b5d7294a960bd.html
7. 电信设备进网管理办法 — 信息产业部令第11号, 修订 工信部令第28号 (2014) 及 第68号 (2024-01-18)  
   https://www.miit.gov.cn/zcfg/xxtxl/art/2024/art_773927399a0a4864b47dfab2ba120302.html
8. 实行进网许可制度的电信设备目录 — 工信部, no standing 公告 number  
   https://jwxk.miit.gov.cn/networkGuide/DeviceDirectory
9. 无线电发射设备管理规定 — 工信部令第57号  
   https://www.miit.gov.cn/jgsj/wgj/bmgz/art/2023/art_c504af4beeb944fba57e618140959213.html
10. 深化电信基础设施共建共享 促进双千兆网络高质量发展实施意见 — 十四部门, 工信部联通信〔2023〕59号  
   https://www.miit.gov.cn/jgsj/txs/gzdt/art/2023/art_cd5706ee0fd8417492e42305337c0f6a.html
11. 关于推进电信基础设施共建共享的紧急通知 — 工信部+国资委 工信部联通〔2008〕235号  
   https://shca.miit.gov.cn/zwgk/zcwj/wjfb/art/2022/art_513b35989fc946b1bc99491ce63d8a33.html
12. 关于清理规范互联网网络接入服务市场的通知 — 工信部信管函〔2017〕32号  
   https://www.miit.gov.cn/zwgk/zcwj/wjfb/tz/art/2017/art_a940645e940946e1a62cd6c90a4e994e.html
13. 工业和信息化领域数据安全管理办法（试行） — 工信部网安〔2022〕166号  
   https://www.miit.gov.cn/zwgk/zcwj/wjfb/tz/art/2022/art_e0f06662e37140808d43d7735e9d9fd3.html
