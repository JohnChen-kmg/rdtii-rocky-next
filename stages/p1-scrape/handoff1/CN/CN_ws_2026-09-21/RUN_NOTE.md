# Run note: CN_ws_2026-09-21 — CAC's 政策法规 index

## Read this first

This is **China's first crawled run**. Every earlier Chinese document in `outputs/CN/` was collected by hand,
because `flk.npc.gov.cn` forbids automated collection. That prohibition is specific to that host. **CAC publishes a
robots.txt that permits us**, so its own index of policy and regulations was crawled instead of hand-picked.

The result is the reason to do it: **42 of the 68 tier-2 documents here were not on our hand-built checklist**,
even after four research agents had verified that checklist document by document. A curated list records what we
already knew; the index records what CAC published.

## At a glance

| | |
| :---- | :---- |
| Portal | `www.cac.gov.cn`, section 政策法规 (`/wxzw/zcfg/`) |
| Documents | **111 of 111, no failures** |
| Size | 3.3 MB raw HTML, 1.5 MB extracted text |
| Listing requests | 6 (one per category, `perPage=100`) |
| Document requests | 111 |
| Pace | 6 s + jitter, one request at a time |
| Identity | `RDTII-Rocky-Crawler/0.1 (+polite public-law retrieval)` — no disguise |
| Wall clock | about 12 minutes |

### By category

| Category | Documents | Tier |
| :---- | ----: | :---- |
| 部门规章 | 38 | **Layer 2 — absent from the NPC database** |
| 规范性文件 | 30 | **Layer 2 — absent from the NPC database** |
| 政策文件 | 15 | Policy; context, not instruments |
| 行政法规 | 14 | Layer 1 (also in the NPC database) |
| 法律 | 8 | Layer 1 |
| 司法解释 | 6 | Layer 1 |

政策解读 (346 items) was **not** collected: commentary on instruments, not instruments.

## How it was run

`robots.txt`, read 2026-09-21, disallows only `/zfz/`, `/wxb_zfz/`, `/wxzf/` and one video path. Our paths
(`/wxzw/`, `/cms/`) are permitted and no `Crawl-delay` is stated, so 6 s + jitter was our own conservative choice.

Paging is a POST to `/cms/JsonList` with `{channelCode, perPage, pageno, condition, fuhao, value}`, returning JSON
with `totalRec` and a `list` of `{topic, infourl, pubtime}`. `perPage=100` is honoured, so each category came back
in one request.

Scripts are in the session scratchpad (`cac_list.py`, `cac_fetch.py`). **No country package was written for CN** —
this was a direct crawl, not an adapter run, so there is no `countries/cn-china/` and no engine manifest.

## What is in this folder

```
raw/           111 files   the page as served
text/          111 files   body text, 纠错 bar to footer
manifest.csv               one row per document
manifest.json              the same, plus failures (none)
LINKS.md                   every document with a direct link, grouped by tier
```

`manifest.csv` carries, per document: category, title, published date, **document number and effective date read
out of the text**, character count, whether 第一条 is present, attachments, URL, filename.

## What is stored

**The full legal text, inline in HTML.** No PDF, no attachment, no OCR, no viewer. This is the cleanest source
China has offered so far — cleaner than the NPC database itself, which serves articles without annexes.

One document carries attachments: 互联网信息内容管理行政执法程序规定 links three `.doc` forms. They were recorded
in the manifest but **not downloaded** — forms, not law.

## What is missing

- **政策解读 (346)** — deliberately not collected.
- **Annexes**, if any exist beyond the one noted above. The extractor records attachment links; it does not
  follow them.
- CAC's index does not carry documents issued by other bodies, even where CAC co-signed. The MIIT, NDRC, MOF,
  Customs, SAMR, MPS and OSCCA documents on the layer-2 list are elsewhere.

## Issues encountered

1. **The parser found nothing on the first attempt.** CAC writes `href` **unquoted** (`href=//www.cac.gov.cn/...
   target=_blank`), so `href="([^"]+)"` matches zero rows. The listing also sits in a div named `loadingInfoPage`,
   which looks client-rendered but is server-rendered for page 1.
2. **21 documents flagged "short / no 第一条".** This is a false positive in our own check, not a defect in the
   data: 政策文件 are 意见 and 方案, which have no articles. One genuine short page: 国务院关于授权国家互联网信息办公室
   负责互联网信息内容管理工作的通知 (195 characters) — that is the whole document.
3. `index_2.htm` returns **404**. Paging is the JSON endpoint only; do not assume sequential static pages.

## What this changes

The layer-2 checklist listed **19** CAC documents. The index holds **68** in the two tiers the NPC database omits.
Among the 42 we had not listed, these bear directly on indicators we score:

| Document | Number | In force |
| :---- | :---- | :---- |
| 人脸识别技术应用安全管理办法 | 令第19号 | 2025-06-01 |
| 关键信息基础设施商用密码使用管理规定 | 令第5号 | 2025-08-01 |
| 网络数据安全风险评估办法 | 令第24号 | 2026-08-20 |
| 小型个人信息处理者个人信息保护简化措施规定 | 令第25号 | 2026-09-01 |
| 直播电商监督管理办法 | 令第117号 | 2026-02-01 |
| 金融产品网络营销管理办法 | 〔2026〕第9号 | 2026-09-30 |
| 常见类型移动互联网应用程序必要个人信息范围规定 | 〔2021〕14号 | 2021 |
| 移动互联网应用程序信息服务管理规定 | — | 2022 |
| 关于实施个人信息保护认证的公告 | — | 2022-11-18 |

And one correction to `CN_layer2_links.md`: **人工智能拟人化互动服务管理暂行办法 is not a draft.** It was issued
2026-04-10 as a departmental rule. Our file still describes it as out for comment.

## Decisions still open

1. **Do the other publishers get the same treatment?** PBOC must not — its robots.txt is `Disallow: /` for
   everyone but Baiduspider. SAMR, MOFCOM and OSCCA publish no robots.txt at all. That is a policy call, recorded
   in `../CN_layer2_2026-09-21/RUN_NOTE.md`.
2. **Should `CN_layer2_links.md` be rebuilt from indexes rather than maintained by hand?** On tonight's evidence a
   hand-built list of this kind runs about 60% incomplete.
3. Nothing here is committed yet.
