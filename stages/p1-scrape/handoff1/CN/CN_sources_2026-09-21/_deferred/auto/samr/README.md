# 国家市场监督管理总局 · samr.gov.cn

**AUTOMATIC — the tool writes here. Do not put files in this folder by hand.**

Why automatic:

- `www.samr.gov.cn` — no robots.txt; serves an honest client

## What the tool collects

**Whole 法规司 section** — 233 items, read through the site's JPAAS listing API

Every run reads robots.txt for each host first and stops for any host that disallows us. A 403 or 412 is
recorded and left alone — never retried with a different client (`memory: browser-and-robots-rule`).

Verified links already known for this source: 6

1. 互联网广告管理办法 — 市场监管总局令第72号
2. 网络交易监督管理办法 — 市场监管总局令第37号, amended by 令101 (2025-03-18)
3. 网络交易平台规则监督管理办法 — 市场监管总局+网信办 令第116号
4. 网络购买商品七日无理由退货暂行办法 — 工商总局令第90号 (not 82), amended by 总局令31 (2020)
5. 强制性国家标准管理办法 — 市场监管总局令第25号
6. 国家标准管理办法 — 市场监管总局令第59号
