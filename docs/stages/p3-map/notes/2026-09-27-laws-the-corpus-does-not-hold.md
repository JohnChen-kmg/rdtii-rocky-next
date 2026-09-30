# Eleven laws the host's own gold rows cite and our corpus does not hold

Measured 2026-09-27 on the six-economy index (`run_2026-09-27`, 767,105 provisions), not inferred.
A finding for the scraping and extraction workstreams; mapping cannot fix any of it. The live
figures are `unresolvable_gold_rows` in `out/select/select_report.json`.

> **Corrected the same morning.** The first version of this note said nineteen laws, thirteen of
> them Chinese. That was the measurement's fault, not the corpus's: the recall gate could only
> compare English names, and for China and Lao the corpus's English name is a *translation* that
> the host words differently. Matching each law's own title — the host writes it inside 《》 — found
> six of the thirteen Chinese laws and two of the three Malaysian ones sitting in the corpus all
> along. The list below is what survives matching on the original script. The lesson is recorded
> in `config/lawnames.py`: for a non-Latin jurisdiction, an English name is a translation and only
> the original title is identity.

**23 gold rows, 11 distinct laws.**

## China — 7 laws, all one tier

| Law |
| :---- |
| Administrative Measures for Population Health Information (For Trial Implementation) 《人口健康信息的管理措施（试行）》 |
| Interim Measures for the Administration of Online Ride-Hailing Services 《网络预约出租汽车经营服务管理暂行办法》 |
| Interim Measures for the Administration of the Business Activities of Online Lending Information Intermediaries |
| Management Standards for the Entry and Removal of Digital Educational Resources on the National Smart Education Platform |
| Measures on the Administration of Accounting Records 《会计档案管理办法》 |
| Personal Financial Information Protection Technical Specification 《个人金融信息保护技术规范》 |
| Amendment to the Information Security Technology – Personal Information Security Specification (GB/T 35273) |

Every one is a **departmental rule, an administrative measure or a technical specification** — not
one is a law or an administrative regulation. That is the tier the coverage register says the
National Database of Laws and Regulations omits, and the register's China section is now measured
rather than argued: the gap is one horizontal slice of China's legal order, and the host's rows
live in that slice. The last two are GB/T standards, which are not law at all and which the M8/M9
notification sentence exists to disclose.

Recovered by the corrected matching, and therefore **not** missing: the Provisions on Promoting and
Regulating Cross-border Data Flow 《促进和规范数据跨境流动规定》 (the March 2024 easing rule, 14
provisions), the Regulation on Internet Information Services 《互联网信息服务管理办法》 (27), the Map
Management Regulations 《地图管理条例》 (58), the Provisions on Internet Post Comments Services (16),
the Administrative Regulations for Online Publishing Services (61) and the Industrial and Telecom
Data Protection Measures (42). Six documents, all present.

Where the seven that are missing live: the register's analysis says departmental rules are filed
with the State Council and published in the 国务院公报 and the 政策文件库 on gov.cn, which permits
crawling, and in the 国家规章库 on moj.gov.cn.

## Malaysia — 2 laws, one known family

| Law | State |
| :---- | :---- |
| Personal Data Protection Code of Practice For Banking Sector And Financial Institutions 2017 | **not crawled** |
| Personal Data Protection Code of Practice for Licensees Under the Communications and Multimedia Act | **not crawled** |

These are the two documents behind Round 1's hard-coded evaluator paragraph, which described them
as `parse_failed` shells. That was true of Round 1's July corpus and is **not** true of this one:
no Malaysian document in the September hand-off carries "practice" anywhere in its name or its
English name, so they were never fetched. 489 Malaysian documents do have zero corpus rows (384
skipped, 92 excluded, 13 `zero_provisions`) and neither Code is among them.

Between them the two Codes account for **nine** gold rows — 6.2, 6.4 twice, 7.1 twice, 7.3 twice
and 7.5 twice — which makes this pair the most valuable entry on the list, ahead of Lao's
cyber-crime law. A crawl request, not an extraction one.

The Services Tax Act (Act 807) 2018 and the Criminal Procedure Code (Act 593) 2018 are in the
corpus — 986 provisions for the Criminal Procedure Code — and appeared absent only because the
matcher was reading "Act 593" and "2018" as part of the name.

## Lao PDR — 1 law

**Law on Prevention and Combating Cyber Crime No.61/NA 2015**, cited by three gold rows (7.2, 7.3,
7.5). One document, three rows: the best single recovery on this list.

Lao's Law on Electronic Data Protection No.25/NA 2017 (55 provisions) and Law on Electronic
Transactions No.20/NA 2010 (74) **are** present; the law-number bug hid both.

## Australia — 1

"Privacy Impact Assessment 2020" is guidance rather than a statute, so it is arguably outside a
legal corpus altogether. It is the kind of row M8's notification sentence answers.

## What this costs

Not recall on what we hold: the gate reads 59 of 63 on the rows whose laws are in the corpus, and
the four it misses are threshold cases rather than coverage cases. It costs **coverage**, and
coverage is where the host's KNOWN rows come from — a baseline row we cannot reach is a row we
cannot reproduce, and reproducing the baseline is what the scoring rewards.

Cheapest recovery, in order:

1. **Malaysia's two PDP Codes of Practice** — two documents, nine gold rows between them.
2. **Lao's cyber-crime law** — one document, three gold rows.
3. The five Chinese departmental rules, from gov.cn or moj.gov.cn, which the register says permit
   crawling. Four of the ten Chinese misses are one document, the Interim Measures for Online
   Ride-Hailing Services, which answers 6.1, 6.2, 6.3 and 7.3. The two GB/T standards are not law
   and should be disclosed rather than chased.
