# 财政部 + 国务院关税税则委员会 · mof.gov.cn

**AUTOMATIC — the tool writes here. Do not put files in this folder by hand.**

Why automatic:

- `gss.mof.gov.cn` — no robots.txt
- `www.mof.gov.cn` — no robots.txt
- `gks.mof.gov.cn` — no robots.txt

## What the tool collects

**Verified links only** (tariff and e-commerce announcements are an unbounded stream)

Every run reads robots.txt for each host first and stops for any host that disallows us. A 403 or 412 is
recorded and left alone — never retried with a different client (`memory: browser-and-robots-rule`).

Verified links already known for this source: 5

1. 政府采购进口产品管理办法 — 财政部 财库〔2007〕119号
2. 跨境电子商务零售进口商品清单 调整公告 — 八部门公告 2022年第7号
3. 进境物品关税、增值税、消费税征收办法 — 税委会公告 2024年第11号
4. 关于一票货物免征关税额度的公告 — 财政部+海关总署公告 2024年第17号
5. 2026年关税调整方案 — 税委会公告 2025年第11号
