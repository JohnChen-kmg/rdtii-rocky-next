# China: why the operative tier sits outside the National Database, what the methodology expects, and which databases the tool would need

| | |
| :---- | :---- |
| Recorded | 2026-09-20, at the developer's request, after reading the three files in `rdtii-finale-1-scraping\outputs\CN` |
| Status | Analysis. It feeds decision (d) of `2026-09-20_subordinate-tier-coverage.md` and adds two hand-backs to the scraping workshop |
| Owner of the decisions | Developer |

## What the three files establish

`CN_corpus_plan.md`, `CN_layer2_checklist.md` and `CN_layer2_links.md` set out a Chinese corpus in
three layers. Layer 1 is the National Database of Laws and Regulations, about 25 instruments, which
answers 18 of 61 indicators. Layer 2 is about 93 verified documents from nine publishers on some
thirty government hosts, which lifts that to roughly 52. Layer 3 is what no source publishes: the
blocklist behind 9.1, state shareholding for 5.3, most important-data catalogues. The five
administrative regulations read by hand in `CN_manual_2026-09-20\FINDINGS.md` confirm the mechanism
five times out of five: **the database reproduces an instrument's articles, not its attachments**,
and the index measures the attachment. The sharpest case is 电信条例 第八条, which says the services
catalogue is annexed to the regulation, while the database's copy has no annex.

The question the developer asked is why. The answer is in China's own law on legislation, and it is
a split of publication channels by tier, not a failure of publicity.

## Why: the structure of Chinese law puts the operative tier in the executive's channel

The 立法法 (Legislation Law, 2023 revision, text on gov.cn) draws the lines. Article numbers are from
that text.

| Rule | What it does to an index |
| :---- | :---- |
| **第九十一条.** A departmental rule (部门规章) may regulate only matters that implement a law or a State Council regulation, decision or order. Without such a basis it may not reduce rights or add obligations | The number, the list and the procedure are *meant* to sit in rules and below. The statute and the 条例 state the principle because the Legislation Law tells them to leave the detail to the executive |
| **第六十二条.** Laws are published in the NPC Standing Committee Gazette and on 中国人大网 | The legislature's channel |
| **第九十七条.** Administrative regulations and rules are published in the 国务院公报 or the department's gazette, and on 中国政府法制信息网, the Ministry of Justice's site | The executive's channel. Two channels, by statute |
| **第一百零九条.** Administrative regulations are filed with the NPC Standing Committee; departmental and local-government rules are filed with the State Council | The NPC's database holds what is made by or filed with the NPC Standing Committee: constitution, laws, administrative regulations, supervisory regulations, judicial interpretations, local regulations. Departmental rules are filed elsewhere, so they are not in it |

Below the rules sit two more things that are not legislation at all under the Legislation Law.
**Normative documents** (规范性文件: 通知, 公告, 函) are administrative acts governed by the State
Council's own regime for such documents; they are published on the issuer's site and in the State
Council's policy library. **Catalogues and lists** (目录, 清单, 负面清单) are an administrative
technique: the regulation creates the list and delegates its content and republication to a ministry,
as 电信条例 第八条 and 两用物项出口管制条例 第十一条 do in so many words, so the executive can adjust
the list without reopening the regulation. **Standards** (GB, GB/T) are technical documents under the
标准化法, published on the standards platform and never in a law database anywhere.

So China's peculiarity is not that the delegated tier is unpublished. It is that the legislature and
the executive run separate official databases, and the scraping survey looked at the legislature's.
Viet Nam, Russia and Kazakhstan put every tier in one database of normative legal acts, which is why
they look complete and China looks empty. The nearest analogue to China's split is India: Acts in the
India Code, rules and notifications in the Gazette, the FDI policy in a departmental circular.

## Why the methodology pulls these sources in

The RDTII Guide anticipates exactly this. Its section "Sources of regulatory measures" (printed p.12)
says: "fine-grain regulatory detail is not always available. To address this challenge, researchers
should dig deeper into the hierarchy of law: statutes, regulations, decrees, decisions and so on",
with the Republic of Korea as the worked example, Acts to Enforcement Decrees to Enforcement Rules,
"which are promulgated by administrative agencies, spell out in detail what Acts mandate". The Internal
Guide (p.8 and p.9) fixes the evidence rule: official sources "cover official laws, regulations,
guidelines, government decisions, case laws", secondary sources are excluded, and vertical coverage
"encompasses all levels of legal hierarchy, from overarching laws (Acts) to supplementary regulations
(decrees, decisions, etc.)". The methodology measures at the operative tier by design. In China the
operative tier is in the executive's channel, so the sources in `CN_layer2_links.md` are what the
methodology requires, not an extra.

The host's own coders did the same. The Round 2 database's 111 China rows, read from the gold set,
name as their first instrument:

| First-named instrument | Rows |
| :---- | ----: |
| Departmental rule (办法, 规定, 细则) | 40 |
| Statute (法) | 30 |
| Administrative regulation (条例) | 24 |
| Notice, announcement, catalogue or list | 11 |
| National standard | 2 |
| Other (practice, SOE fact) | 4 |

Their cited hosts: `gov.cn` 62 times, `flk.npc.gov.cn` 19, `cac.gov.cn` 17, then MOFCOM, Shanghai's
development commission, `npc.gov.cn`, the standards platform, `moj.gov.cn`, SAC, Beijing's government,
SAMR and a long tail of ministry sites. **The host went to the State Council's site three times as
often as to the NPC database.** The keyword classification is a heuristic on English titles, but the
direction is not in doubt: two thirds of the host's China evidence sits below the statute.

## Additional databases the tool would need for China

> **Corrected 2026-09-21.** The developer's observation that no single website can hold all of China's
> relevant law is right, and counting the host's own citations shows it holds for every economy, with China
> mid-pack rather than worst. The list below is therefore a first set, not a sufficient one: the host's
> Chinese evidence is spread over 34 official domains, and its busiest, `gov.cn`, carries 39 per cent.
> See `2026-09-21_source-dispersion.md`, which supersedes this section's framing.

In the order to try, with what the survey and the links file already know. Robots files for the first
two are unread; that check belongs to the scraping workshop.

| Source | What it holds | Status |
| :---- | :---- | :---- |
| **国务院公报 on `gov.cn`** (`gov.cn/gongbao`) | The official text of administrative regulations and of departmental rules issued by 令, named by 立法法 第九十七条 as a publication channel. `CN_layer2_links.md` already uses it as the mirror for every 令 | `www.gov.cn` robots permits crawling (survey of 2026-09-16). The host's coders cited gov.cn 62 times |
| **国务院政策文件库 on `gov.cn`** (`gov.cn/zhengce/zhengcewenjianku`, sections 国务院文件 and 国务院部门文件) | 国发 and 国办发 documents and departmental normative documents: the 通知, 公告 and 目录 tier, including 国办发〔2025〕34号 | Same host, same robots answer. One site covers most of layer 2's normative documents |
| **国家规章库 on 中国政府法制信息网** (`moj.gov.cn/pub/sfbgw/flfggz/`, 部门规章 and 地方政府规章) | Current departmental and local-government rules, sourced from ministry sites and the 国务院公报, published in step with gov.cn. The Ministry of Justice also runs the 国家行政法规库 with every historical text of each administrative regulation | The executive's twin of the NPC database, named in 立法法 第九十七条. Robots unread. The host's coders cited `moj.gov.cn` four times |
| **Issuer sites**, nine publishers | Rules, notices, catalogues and their PDF or `.doc` attachments, which the gazette copies sometimes omit | Verified one by one in `CN_layer2_links.md`. `www.miit.gov.cn` answers 403 to everything including robots, so MIIT is browser-only; customs and NHC 412; MPS 521 on the day |
| **全国标准信息公共服务平台** (`std.samr.gov.cn`, `openstd.samr.gov.cn`) | GB and GB/T texts, for 11.4, 7.2, 7.4 | Free to read, redistribution restricted. Cite and quote, do not republish |
| **国家法律法规数据库** (`flk.npc.gov.cn`) | Layer 1 | Robots forbids automated collection. Hand collection only, as in `CN_manual_2026-09-20` |

Two points for the instrument owner follow from 第九十七条. A 国务院公报 copy on gov.cn is an official
publication of the rule, not a mirror of convenience, so it satisfies the source hierarchy at least as
well as a ministry's news page. And an unpublished instrument, such as PBOC's 断直连 notice, is a
different fact from an absent one; the register's mark should say "cited but unpublished", never "no
provision found".

## What changes in our documents

- The coverage register's China block now says the gap is a channel split, names the two gov.cn
  libraries and the Ministry of Justice database, and points here.
- Decision (d) in the issue record gains a route that does not need the NPC's permission: gov.cn for
  administrative regulations, rules and normative documents, hand collection for the statutes.

## Hand-backs

| To | What |
| :---- | :---- |
| Scraping workshop | Read `robots.txt` for `www.moj.gov.cn` and for the `gov.cn/zhengce` and `gov.cn/gongbao` paths, one request each, and record the answer in `_finale-survey`. No crawl |
| Instrument workshop | Rule on whether a 国务院公报 copy on gov.cn counts as the official source for a 部门规章, and whether judicial interpretations count for 4.01, 4.2, 4.3 and 4.1 |
| Developer | Decision (d): whether a Chinese set is built at all before the freeze, and if so whether from gov.cn plus hand-collected statutes |
