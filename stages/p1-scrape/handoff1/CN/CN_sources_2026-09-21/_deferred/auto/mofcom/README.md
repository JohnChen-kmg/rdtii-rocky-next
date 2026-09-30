# 商务部 · mofcom.gov.cn

**AUTOMATIC — the tool writes here. Do not put files in this folder by hand.**

Why automatic:

- `www.mofcom.gov.cn` — no robots.txt; serves an honest client
- `fms.mofcom.gov.cn` — MOFCOM subdomain
- `exportcontrol.mofcom.gov.cn` — MOFCOM subdomain
- `trb.mofcom.gov.cn` — MOFCOM subdomain
- `cacs.mofcom.gov.cn` — MOFCOM subdomain
- `policy.mofcom.gov.cn` — MOFCOM subdomain

## What the tool collects

**Whole 商务部规章 section**, same JPAAS API as SAMR; plus the verified links below

Every run reads robots.txt for each host first and stops for any host that disallows us. A 403 or 412 is
recorded and left alone — never retried with a different client (`memory: browser-and-robots-rule`).

Verified links already known for this source: 9

1. 中华人民共和国两用物项出口管制清单 — 商务部+工信部+海关总署+密码局公告 2024年第51号
2. 中国禁止出口限制出口技术目录 — 商务部+科技部公告 2025年第28号
3. 中国禁止进口限制进口技术目录 — 商务部公告 2021年第37号
4. 禁止进口货物目录（第九批） — 商务部+海关总署+生态环境部公告 2023年第63号
5. 进口许可证管理货物目录（2026年） — 商务部+海关总署公告 2025年第88号
6. 模拟芯片反倾销立案公告 — 商务部公告 2025年第27号
7. 机电产品国际招标投标实施办法（试行） — 商务部令 2014年第1号
8. 跨境电商 B2B 出口监管试点公告 (9710 / 9810) — 海关总署公告 2020年第75号
9. B2B 出口监管试点全国推广公告 — 海关总署公告 2021年第47号
