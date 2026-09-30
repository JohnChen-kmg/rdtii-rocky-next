# 中国政府网 · gov.cn (国务院文件, 国务院公报)

**AUTOMATIC — the tool writes here. Do not put files in this folder by hand.**

Why automatic:

- `www.gov.cn` — robots.txt permits; only legacy paths disallowed

## What the tool collects

**Verified links only**: 国务院 documents and the 国务院公报 copies of MIIT and MPS rules

Every run reads robots.txt for each host first and stops for any host that disallows us. A 403 or 412 is
recorded and left alone — never retried with a different client (`memory: browser-and-robots-rule`).

Verified links already known for this source: 6

1. 个人信息出境认证办法 (网信办 + 市场监管总局, in force 2026-01-01) — The third cross-border route, alongside the assessment and the standard contract. Without it, indicator 6.4 is described with two of its three mechanisms
2. 电信和互联网用户个人信息保护规定 — 工信部令第24号
3. 国办发〔2025〕34号 本国产品标准通知 — 国务院办公厅
4. 跨境电商零售进口税收政策通知 — 财政部+海关总署+税务总局 财关税〔2018〕49号
5. 跨境电商零售进出口监管公告 (1210 / 9610) — 海关总署公告 2018年第194号
6. 互联网安全保护技术措施规定 — 公安部令第82号
