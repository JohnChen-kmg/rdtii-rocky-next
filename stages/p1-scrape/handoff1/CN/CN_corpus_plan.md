# What to collect to make a Chinese legal corpus that can be scored

> **Superseded in its layer 2 on 2026-09-21.** Layer 2 below is a hand-picked set of about twenty documents. Two
> things replaced that: taking whole rules sections from each ministry that permits it (on CAC, that found 42
> tier-2 documents the hand-picked list had missed), and the **国务院公报**, which publishes every ministry's rules
> under 立法法 第九十七条 from a host that permits us. Layer 2 is now four parts: **2a** the gazette, **2b** ministry
> indexes taken whole, **2c** verified links from announcement streams, **2d** ministry sites by hand, for notices
> and attachments only. The current structure and every source's general link are in
> `CN_sources_2026-09-21/README.md`. Layers 1 and 3 stand as written.
>
> **Refocused 2026-09-22.** The national database is the core — 945 documents downloaded by hand on 2026-09-21.
> Layer 2 is narrowed to CAC, MIIT and Customs; the rest is in `CN_sources_2026-09-21/_deferred/`, moved not
> deleted. The gazette was set aside with it: it gives a rule's text as issued, not the text in force. Deferring
> leaves 18 indicators on layer 1 alone, and only one of them, 7.5, is in pillars 6 and 7 — which layer 1 answers
> in full.

**Written 2026-09-20**, after reading five administrative regulations by hand
(`CN_manual_2026-09-20/FINDINGS.md`) and mapping the instrument's 61 indicators against what the National Database
of Laws and Regulations carries (`countries/_finale-survey/explore-2026-09-20/cn-china-coverage.md`).

**The principle:** the database gives an instrument's **articles**; an index measures its **attachments**. So the
corpus is the database *plus* the attachments, collected from the body that issues each one.

**Everything here is hand-collected.** `flk.npc.gov.cn` forbids automated collection; the ministry sites are a
separate question the developer decides (`POLICY.md` section 4 asks that any hand-picked set be disclosed).

---

## Layer 1 — the base: the National Database of Laws and Regulations

**About 25 instruments.** Laws and administrative regulations, plus judicial interpretations where the instrument
accepts them. This layer alone answers **18 of 61 indicators**, and pillar 7 in full.

| Pillar | Instruments |
| :---- | :---- |
| 1, 10 | 对外贸易法 (2025 rev., in force 2026-03-01) · 关税法 (2024-12-01) · 反倾销条例 / 反补贴条例 / 保障措施条例 · 货物进出口管理条例 · 技术进出口管理条例 · 出口管制法 · 两用物项出口管制条例 (第792号) |
| 2 | 政府采购法 · 政府采购法实施条例 (第658号) · 招标投标法 · 招标投标法实施条例 (第613号) |
| 3 | 外商投资法 · 外商投资法实施条例 (第723号) · **外商投资电信企业管理规定 (第333号)** · 公司法 (2023 rev.) |
| 4 | 专利法 · 著作权法 · 商标法 · 反不正当竞争法 (2025 rev.) · 专利法实施细则 · **信息网络传播权保护条例 (第468号)** |
| 5, 9 | **电信条例 (第291号)** · 互联网信息服务管理办法 (第292号) · 计算机信息网络国际联网管理暂行规定 (第195号) · 广告法 |
| 6, 7 | 网络安全法 (2025 amendment, in force 2026-01-01) · 数据安全法 · 个人信息保护法 · **网络数据安全管理条例 (第790号)** · 关键信息基础设施安全保护条例 (第745号) · 密码法 · 商用密码管理条例 (第760号) |
| 8 | 民法典 (arts. 1194–1197) · 电子商务法 |
| 11 | 标准化法 · 认证认可条例 (第390号) · 无线电管理条例 (第672号) |
| 12 | 电子商务法 · 消费者权益保护法 + **实施条例 (第778号)** · **非银行支付机构监督管理条例 (第768号)** · 反洗钱法 (2025-01-01) · 外汇管理条例 (第532号) |

The five in **bold** are already collected (`CN_manual_2026-09-20/`).

---

## Layer 2 — the attachments: about twenty documents, six publishers

This is what turns 18 answerable indicators into roughly 52.

### CAC 国家互联网信息办公室 · `www.cac.gov.cn`

| Document | Unblocks |
| :---- | :---- |
| 数据出境安全评估办法 (令11, 2022) | 6.2, 6.4 |
| 个人信息出境标准合同办法 (令13, 2023) | 6.4 |
| **促进和规范数据跨境流动规定 (2024-03-22)** — the thresholds and exemptions | 6.1, 6.2, 6.4 |
| 网络安全审查办法 (2022) | 2.2, 3.4 |
| 互联网信息服务算法推荐管理规定 (令9, 2022) | **4.9**, 8.4 |
| 互联网信息服务深度合成管理规定 (令12, 2023) · 生成式人工智能服务管理暂行办法 (2023) · 人工智能生成合成内容标识办法 (2025-09-01) | 4.9, 8.4 |
| 个人信息保护合规审计管理办法 (令18, 2025-05-01) | 7.4 |
| 互联网用户账号信息管理规定 (令10, 2022) | 8.3 |
| 网络信息内容生态治理规定 (令5, 2020) | 8.2, 9.1 |

### MIIT 工业和信息化部 · `www.miit.gov.cn`

| Document | Unblocks |
| :---- | :---- |
| **电信业务分类目录 (2015, as amended 2019)** — the annex missing from 电信条例 | **5.5**, 3.1 |
| 电信业务经营许可管理办法 (令42, 2017) | 5.5 |
| **增值电信业务扩大对外开放试点通告 (通信函〔2024〕107号)** — why 49%/50% is stale | 3.1, 5.2 |
| **互联网域名管理办法 (令43, 2017)** | **12.7** |
| 电信基础设施共建共享 notices (2008, 2023) | 5.1 |

### NDRC + MOFCOM · `www.ndrc.gov.cn`, `www.mofcom.gov.cn`

| Document | Unblocks |
| :---- | :---- |
| **外商投资准入特别管理措施（负面清单）2024年版** — every equity limit | **3.1**, 3.2, 12.01 |
| 外商投资安全审查办法 (令37, 2021) | 3.4 |
| **两用物项出口管制清单** (MOFCOM/GACC 公告) — the list 第792号 delegates | **10.4** |
| 禁止/限制进口货物目录 · 中国禁止出口限制出口技术目录 | 10.1, 10.2, 10.4 |
| Trade-defence 公告 (e.g. the 2025 analog-chip case) | 1.4 |

### MOF + Customs + Tariff Commission · `www.mof.gov.cn`, `www.customs.gov.cn`

| Document | Unblocks |
| :---- | :---- |
| **¥50 duty-free threshold 公告** | **12.5** |
| **财关税〔2018〕49号** — ¥5,000 / ¥26,000 e-commerce caps · 跨境电商零售进口商品清单 | 12.2, 12.5 |
| **国办发〔2025〕34号** 本国产品标准通知 (also on `www.gov.cn`) | **2.1, 10.3** |

### PBOC 中国人民银行 · `www.pbc.gov.cn`

| Document | Unblocks |
| :---- | :---- |
| **条码支付业务规范 银发〔2017〕296号** — the A/B/C/D daily caps | **12.4.5** |
| **网联迁移通知 银支付〔2017〕209号** ("断直连") | **12.4.6** |
| 非银行支付机构网络支付业务管理办法 (公告〔2015〕43号) — account tiers | 12.4.5 |
| 银行卡清算机构管理办法 | 12.4.4, 12.4.6 |

### SAMR + the standards platform · `www.samr.gov.cn`, `openstd.samr.gov.cn`

| Document | Unblocks |
| :---- | :---- |
| 互联网广告管理办法 (令72, 2023) | 9.3 |
| 网络交易监督管理办法 (令37, 2021) · 网络交易平台规则监督管理办法 (2026-02-01) | 12.3, 12.9 |
| 强制性产品认证目录 + CCC mode 公告 | 11.2, 11.3 |
| **GB/T 32918 (SM2), 32905 (SM3), 32907 (SM4), 38635 (SM9)** | **11.4** |

> **Note on standards:** GB and GB/T texts are free to read on the official platform, but redistribution is
> restricted. Cite and quote; do not republish the files. That is a licensing question, not a scraping one.

---

## Layer 3 — what no source will give you

| Indicator | Why |
| :---- | :---- |
| **9.1** blocking and filtering | The legal basis exists; **the blocklist is published in no instrument at any tier**. The honest record is "measure exists, list unpublished" |
| **5.3** state shareholding in telecom | No legal instrument of any kind. Only SASAC's central-enterprise catalogue and the three operators' own filings — a reconstruction, not a source |
| **重要数据目录** (feeds 6.x, 7.4) | Drawn up region by region and department by department; most are unpublished |

Mark these as structurally unobtainable in the methodology rather than scoring them as "no measure". Scoring
absence where the answer is merely unpublished is the one error this corpus cannot recover from.

---

## How to hold it

```
outputs/CN/CN_manual_<date>/
    raw/              the files, named <indicator>_<short-name>.<ext>
    provenance.tsv    one line each: source URL, when fetched, the 施行/修订 date printed on the page
    FINDINGS.md       what each document actually said
```

Three rules that make a hand-collected set usable as evidence:

1. **Record the version date printed on the document**, not the date you downloaded it. Chinese instruments are
   revised often and the database serves the consolidated text without always making the version obvious.
2. **Keep the Chinese original as the document of record.** Official English translations exist for some
   statutes and are not authoritative; a translation is working material, like Laos' English PDFs.
3. **One line per file, no exceptions.** A hand-collected set has no `discovery_log.jsonl`; the sheet is the only
   provenance it will ever have.

## What it costs

| Layer | Documents | Effort |
| :---- | ----: | :---- |
| 1, the base | ~25 | An afternoon, one site |
| 2, the attachments | ~20 | A day, six sites, and the searching is the slow part |
| 3 | — | A paragraph in the methodology |

**Coverage reached: roughly 52 of 61 indicators**, against 18 from the database alone. The remaining nine are the
partial cases in layer 3 and a few where only a sectoral rule would finish the answer.
