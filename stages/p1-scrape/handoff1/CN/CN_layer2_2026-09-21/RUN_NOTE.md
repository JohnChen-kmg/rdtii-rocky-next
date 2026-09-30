# Run note: CN_layer2_2026-09-21 — a six-document browser probe

## Read this first

Three publishers on the layer-2 list refuse an ordinary HTTP client: **MIIT answers 403 across its whole site,
NDRC answers 403 from a WAF, Customs answers 412.** On 2026-09-21 the developer decided that driving a real
browser is acceptable **for hosts that publish no prohibition**, and then cut the scope to a handful: *"just try a
few, so we don't violate protocol, only touch the thing that is public."* This folder is that handful.

**What was not touched, and why:**

| Host | Reason |
| :---- | :---- |
| `www.pbc.gov.cn` | robots.txt says `User-agent: *` / `Disallow: /`. A published refusal — the same ground that keeps us off `flk.npc.gov.cn`. Its 7 documents stay hand-collected |
| `flk.npc.gov.cn` | robots.txt forbids automated collection. Never contacted |
| `openstd.samr.gov.cn` | GB/T texts are free to read but restricted for redistribution. Record identifiers, do not download |
| `www.cac.gov.cn` | already collected the same night through its own index (`../CN_ws_2026-09-21/`) |

## At a glance

| | |
| :---- | :---- |
| Attempted | 6 |
| Succeeded | **5** |
| Failed | 1 (Customs — TLS, see below) |
| Attachments retrieved | **3** (1 `.doc`, 2 PDF, 660 KB) |
| Method | Playwright driving installed Chrome, headless, one page at a time, 6 s + jitter |
| Wall clock | about 50 seconds |

## Results

| # | Document | Host | HTTP | Page text | Attachment |
| ----: | :---- | :---- | ----: | ----: | :---- |
| 1 | 电信业务分类目录（2015年版） | miit | 200 | 572 c | **`4564599.doc`, 273 KB** |
| 2 | 电信业务分类目录 2019年修订公告 | miit | 200 | 733 c | — |
| 3 | 增值电信业务扩大对外开放试点通告 | miit | 200 | 1,251 c | 2 PDF, 174 KB |
| 4 | 互联网域名管理办法 | miit | 200 | 8,234 c | — |
| 5 | 外商投资准入负面清单（2024年版） | ndrc | 200 | 971 c | **PDF, 237 KB** |
| 6 | 跨境电商B2B出口监管试点公告 | customs | **FAIL** | — | — |

## The finding

**Look at the page-text column.** Four of the five pages carry between 572 and 1,251 characters — a title, a
document number, a sentence of transmittal. The law is in the attachment.

This is the same pattern we proved by hand on five administrative regulations in `CN_manual_2026-09-20/`, now
observed from the other side: the NPC database drops the annex, and the issuing ministry publishes a page that is
*only* a wrapper around it. An index that reads either one alone reads nothing.

**What the three attachments actually contain**, checked after download:

- `4564599.doc` — the real **电信业务分类目录**: the full classification tree, A11 固定通信业务 through A23, and
  B11 IDC / B12 CDN / B13 ISP / B14 在线数据处理. This is the annex 电信条例 第八条 calls "本条例所附" and the
  national database does not carry. **Indicator 5.5 is answerable for the first time.**
- The pilot-scheme PDF — names IDC, CDN, ISP, 在线数据处理与交易处理 and 信息服务 as the services whose foreign
  equity cap is lifted. This is what makes the 49%/50% figure in 国务院令第333号 incomplete (3.1, 5.2).
- The negative-list PDF — the actual 负面清单 with its 股权要求 and 高管要求 (3.1, 3.2, 12.01).

All three are text-layer, not scans. **No OCR is needed anywhere in the Chinese corpus.**

## Issues encountered

**Customs failed on TLS, not on a block.** `www.customs.gov.cn` returned `net::ERR_CERT_AUTHORITY_INVALID` — Chrome
rejects its certificate chain. This was **not** worked around: disabling certificate validation is a security
boundary, not a politeness setting, and it is a different thing from choosing a client. Use the `gov.cn` and
MOFCOM mirrors already recorded in `../CN_layer2_links.md` for the three GACC announcements.

## What is in this folder

```
raw/     5 files    the page as Chrome rendered it
text/    5 files    visible text
files/   3 files    the attachments, which are the actual law
manifest.csv/.json  one row each: title, reference, host, HTTP, chars, attachments, URL
```

## What this does not settle

- **Five documents is not a sample.** It shows the method works and that the wrapper pattern is real on MIIT and
  NDRC. It does not measure how often attachments carry the substance.
- **The remaining ~90 layer-2 URLs were not fetched.** Scope was deliberately cut.
- **Whether to crawl SAMR, MOFCOM and OSCCA at all** is open. None publishes a robots.txt, so nothing is
  disallowed, but "no robots.txt" is not the same as "invited". That is a `POLICY.md` question, not a technical
  one.
- Nothing here is committed yet.
