# Update by hand — the sources no tool can read

**Written 2026-09-22 by `countries/cn-china/tools/manual_check.py`, from each source's `provenance.tsv`.**
Rewritten on every run; nothing here is hand-edited.

`tools/update.py` covers CAC and gov.cn, which permit us. It cannot cover the **8 sources below, holding 25 documents**: their hosts refuse an honest client, so no tool will ever report that one of these rules was amended or repealed. **Until a person walks this list, an update check of China is not complete** (`CONVENTIONS.md` rule 11).

Work through each source, answer its three questions, then record the date:

```
python countries/my-malaysia/scraper/watchlist.py countries/cn-china/watchlist.tsv --checked <name>
```

Found something? **Do not edit a stored file.** Add a row to that source's `provenance.tsv`, download the new version beside the old one, and note the change — a superseded text is kept, not replaced (`CONVENTIONS.md` rule 6, flag and do not fix).

## customs

**Open these index pages first**, and compare what they list with the table below.

- [海关总署 · 公告](https://www.customs.gov.cn/customs/302249/302266/302267/index.html) — Cross-border e-commerce supervision (1210 / 9610 / 9710 / 9810); any new customs list
  · refuses our client: manual by decision, CONVENTIONS rule 14, not deferred: the tariff is not legislation and is read by a researcher at scoring time. Also 412 to an honest client, with a certificate Chrome rejects · last checked: **never checked**

**Three questions, in this order:**

1. Does the index list anything **new** that is not in the table below?
2. Is any document in the table shown with a **later version date** than the one we hold?
3. Is any document in the table marked **废止 / 失效** (repealed or lapsed)?

*Nothing downloaded from this source yet.*

## miit

**Open these index pages first**, and compare what they list with the table below.

- [工业和信息化部 · 政策文件](https://www.miit.gov.cn/zwgk/zcwj/) — New 令, 通告 and 公告; changes to 电信业务分类目录 and to the 进网许可 catalogue. Save attachments
  · refuses our client: 403 to any honest client, robots.txt included · last checked: **never checked**

**Three questions, in this order:**

1. Does the index list anything **new** that is not in the table below?
2. Is any document in the table shown with a **later version date** than the one we hold?
3. Is any document in the table marked **废止 / 失效** (repealed or lapsed)?

### Documents held — 25

| # | Document | Reference | Version we hold | Open | File |
| ---: | :---- | :---- | :---- | :---- | :---- |
| 1 | 电信业务分类目录（2015年版） | 工信部通告, 信管〔2015〕484号 | 2015-12-28 | [open](https://www.miit.gov.cn/zwgk/zcwj/wjfb/tg/art/2020/art_e98406cd89844f7e92ea1bcf3b5301e0.html) | 工业和信息化部关于发布《电信业务分类目录（2015年版）》的通告.… |
| 3 | 电信业务经营许可管理办法 | 工信部令第42号 | 2017-09-01 | [open](https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2020/art_ad4a7f072a5e4e2aab49b7817c49f5a6.html) | mirror_permitted/ |
| 4 | 增值电信业务扩大对外开放试点通告 | 工信部 通信函〔2024〕107号 | 2024-04-08 | [open](https://www.miit.gov.cn/zwgk/zcwj/wjfb/tg/art/2024/art_2326271e1b424e09b6e5924ad2948863.html) | mirror_permitted/ |
| 5 | 互联网域名管理办法 | 工信部令第43号 | 2017-11-01 | [open](https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2017/art_43ec3819b2d04a31ad2c1c81c3f6100b.html) | 互联网域名管理办法.pdf |
| 6 | 关于规范互联网信息服务使用域名的通知 | 工信部信管〔2017〕264号 | 2017-11-01 | [open](https://www.miit.gov.cn/jgsj/xgj/hlwgl/art/2020/art_f4e6b2b5bc6b400ea35b5d7294a960bd.html) | mirror_permitted/ |
| 13 | 工业和信息化领域数据安全管理办法（试行） | 工信部网安〔2022〕166号 | 2023-01-01 | [open](https://www.miit.gov.cn/zwgk/zcwj/wjfb/tz/art/2022/art_e0f06662e37140808d43d7735e9d9fd3.html) | mirror_permitted/ |
| 14 | 中华人民共和国无线电频率划分规定 | MIIT, 2018-04-18 | 2018-07-01 | [open](https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2020/art_ac0745b4d9cb4b298360f07024591279.html) | 6175308.doc |
| 17 | 通信网络安全防护管理办法 | MIIT | — | [open](https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2020/art_725c830e76424f8385f2e3eea00a294f.html) | 通信网络安全防护管理办法.html |
| 18 | 电话用户真实身份信息登记规定 | MIIT | — | [open](https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2020/art_07ad6d8e69cd4d5ba8b307b37c1aa093.html) | 《电话用户真实身份信息登记规定》.pdf |
| 19 | 国际通信出入口局管理办法 | MIIT | — | [open](https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2020/art_d2e6413bdee34101ae03be9dc67100be.html) | 国际通信出入口局管理办法.html |
| 20 | 公用电信网间互联管理规定 | MIIT | — | [open](https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2020/art_47a190d36aef4e82a1efd6082e05ea39.html) | 公用电信网间互联管理规定.html |
| 21 | 无线电频率使用许可管理办法 | MIIT | — | [open](https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2020/art_cf8ae59938a142c1bd64d6bc21f76a2e.html) | 无线电频率使用许可管理办法.html |
| 22 | 电子认证服务管理办法 | MIIT | — | [open](https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2020/art_79e49c1b615442f9b8ab31c604275d79.html) | 电子认证服务管理办法.html |
| 23 | 电信网码号资源管理办法 | MIIT | — | [open](https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2020/art_f18eb1797cd24fd0ac2aac76ff1704fd.html) | 电信网码号资源管理办法.pdf |
| 24 | 互联网IP地址备案管理办法 | MIIT | — | [open](https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2020/art_2a53e99c4b204e2988dede23bdd23b40.html) | 互联网IP地址备案管理办法.html |
| 25 | 互联网电子邮件服务管理办法 | MIIT | — | [open](https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2020/art_fcdb58d9dd4341be8bd8b829cf9a9159.html) | 互联网电子邮件服务管理办法.html |
| 26 | 通信短信息服务管理规定 | MIIT | — | [open](https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2020/art_77bc7219833c4a08b4563ba42ad23e1f.html) | mirror_permitted/ |
| 27 | 国际通信设施建设管理规定 | MIIT | — | [open](https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2020/art_ed10f9264b664c1b9a1e251dc3e27634.html) | 国际通信设施建设管理规定.html + 国际通信设施建设管理规定.… |
| 28 | 卫星移动通信系统终端地球站管理办法 | MIIT | — | [open](https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2020/art_f98db111ded147648638c62ff7beaa59.html) | 卫星移动通信系统终端地球站管理办法.html |
| 29 | 建立卫星通信网和设置使用地球站管理规定 | MIIT | — | [open](https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2020/art_1158ea23afd34c5bbb302912af8eb8e8.html) | 建立卫星通信网和设置使用地球站管理规定.html |
| 30 | 电信网间互联争议处理办法 | MIIT | — | [open](https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2020/art_d5c194d8878b4ef7a2dce5c0a7244ca4.html) | 电信网间互联争议处理办法.html |
| 31 | 电信用户申诉处理办法 | MIIT | — | [open](https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2020/art_b2e4b04d28f84f0d8c11e76c2b5c650a.html) | 电信用户申诉处理办法.html |
| 32 | 电信设备进网管理办法（2014 修订, 工信部令第28号） | 工信部令第28号 | 2014-09-29 | [open](https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2020/art_40167afc92c04d7d9782352e3edd4c12.html) | 电信设备进网管理办法.pdf |
| 33 | 中华人民共和国无线电频率划分规定（工信部令第62号, the text in force） | 工信部令第62号 | 2023-07-01 | **no address recorded** | 6175308.doc |
| 34 | 通信短信息服务管理规定（工信部令第74号, the text in force） | 工信部令第74号 | 2026-05-01 | **no address recorded** | mirror_permitted/ |

### Still to download — 3

- 关于清理规范互联网网络接入服务市场的通知 — [open](https://www.miit.gov.cn/zwgk/zcwj/wjfb/tz/art/2017/art_a940645e940946e1a62cd6c90a4e994e.html)
- 通信建设工程质量监督管理规定 (optional) — [open](https://www.miit.gov.cn/zc/wjxzfl/flfg/index.html)
- 工业和信息化部令第51号 (open to check) — [open](https://www.miit.gov.cn/zc/wjxzfl/flfg/index.html)

> **2 held documents have no address on the sheet.** They cannot be checked by hand until one is recorded — that is the whole cost of a missing `url`.

## npc-database

**Open these index pages first**, and compare what they list with the table below.

- [国家法律法规数据库 · layer 1](https://flk.npc.gov.cn/) — New and revised laws and administrative regulations. Re-download in bulk
  · refuses our client: robots.txt forbids automated collection · last checked: **never checked**

**Three questions, in this order:**

1. Does the index list anything **new** that is not in the table below?
2. Is any document in the table shown with a **later version date** than the one we hold?
3. Is any document in the table marked **废止 / 失效** (repealed or lapsed)?

*Nothing downloaded from this source yet.*

## mps  — deferred

*No index page on the watch list for this source — add one (`watchlist.tsv`), or this check has nothing to compare against.*

**Three questions, in this order:**

1. Does the index list anything **new** that is not in the table below?
2. Is any document in the table shown with a **later version date** than the one we hold?
3. Is any document in the table marked **废止 / 失效** (repealed or lapsed)?

*Nothing downloaded from this source yet.*

### Still to download — 2

- 信息安全等级保护管理办法 — [open](https://gat.xizang.gov.cn/bsfw_3269/bszn/wlaq/wlaqdjbh/201906/t20190611_170397.html)
- 公安机关互联网安全监督检查规定 — [open](https://www.mps.gov.cn/n6557558/c6263180/content.html)

## ndrc  — deferred

*No index page on the watch list for this source — add one (`watchlist.tsv`), or this check has nothing to compare against.*

**Three questions, in this order:**

1. Does the index list anything **new** that is not in the table below?
2. Is any document in the table shown with a **later version date** than the one we hold?
3. Is any document in the table marked **废止 / 失效** (repealed or lapsed)?

*Nothing downloaded from this source yet.*

### Still to download — 5

- 外商投资准入特别管理措施（负面清单）（2024年版） — [open](https://www.ndrc.gov.cn/xxgk/zcfb/fzggwl/202409/t20240907_1392875.html)
- 自由贸易试验区外商投资准入负面清单（2021年版） — [open](https://www.ndrc.gov.cn/xxgk/zcfb/fzggwl/202112/t20211227_1310019.html)
- 鼓励外商投资产业目录（2025年版） — [open](https://www.ndrc.gov.cn/xxgk/zcfb/fzggwl/202512/t20251224_1402564.html)
- 外商投资安全审查办法 — [open](https://www.ndrc.gov.cn/xxgk/zcfb/fzggwl/202012/t20201219_1255025.html)
- 必须招标的工程项目规定 — [open](https://www.ndrc.gov.cn/xxgk/zcfb/fzggwl/201803/t20180330_960858_ext.html)

## nhc  — deferred

*No index page on the watch list for this source — add one (`watchlist.tsv`), or this check has nothing to compare against.*

**Three questions, in this order:**

1. Does the index list anything **new** that is not in the table below?
2. Is any document in the table shown with a **later version date** than the one we hold?
3. Is any document in the table marked **废止 / 失效** (repealed or lapsed)?

*Nothing downloaded from this source yet.*

### Still to download — 2

- 人口健康信息管理办法（试行） — [open](http://www.nhc.gov.cn/guihuaxxs/gongwen12/201405/783ec8adebc6422bbebdf79db3868d0b.shtml)
- 国家健康医疗大数据标准、安全和服务管理办法（试行） — [open](https://www.nhc.gov.cn/wjw/c100175/201809/a3223ef7768140a786b308c2064de14b.shtml)

## pboc-safe  — deferred

*No index page on the watch list for this source — add one (`watchlist.tsv`), or this check has nothing to compare against.*

**Three questions, in this order:**

1. Does the index list anything **new** that is not in the table below?
2. Is any document in the table shown with a **later version date** than the one we hold?
3. Is any document in the table marked **废止 / 失效** (repealed or lapsed)?

*Nothing downloaded from this source yet.*

### Still to download — 7

- 条码支付业务规范（试行） — [open](https://www.pbc.gov.cn/tiaofasi/144941/3581332/3589728/index.html)
- 非银行支付机构网络支付业务管理办法 — [open](https://www.pbc.gov.cn/tiaofasi/144941/3581332/3588090/index.html)
- 银行卡清算机构管理办法 — [open](https://www.pbc.gov.cn/zhengwugongkai/4081330/4406346/4406348/2025092319185575978/index.html)
- 非银行支付机构监督管理条例实施细则 — [open](https://www.pbc.gov.cn/tiaofasi/144941/144957/5414094/index.html)
- 支付机构外汇业务管理办法 — [open](https://www.safe.gov.cn/safe/2019/0429/13114.html)
- 征信业务管理办法 — [open](https://www.pbc.gov.cn/tiaofasi/144941/144957/4354378/index.html)
- 虚拟货币风险通知 — [open](https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html)

## standards-idonly  — deferred

*No index page on the watch list for this source — add one (`watchlist.tsv`), or this check has nothing to compare against.*

**Three questions, in this order:**

1. Does the index list anything **new** that is not in the table below?
2. Is any document in the table shown with a **later version date** than the one we hold?
3. Is any document in the table marked **废止 / 失效** (repealed or lapsed)?

*Nothing downloaded from this source yet.*

### Still to download — 6

- GB/T 32918.1–.5 (SM2) — [open](https://openstd.samr.gov.cn/bzgk/gb/newGbInfo?hcno=3EE2FD47B962578070541ED468497C5B)
- GB/T 32905-2016 (SM3) — [open](https://openstd.samr.gov.cn/bzgk/gb/newGbInfo?hcno=45B1A67F20F3BF339211C391E9278F5E)
- GB/T 32907-2016 (SM4) — [open](https://openstd.samr.gov.cn/bzgk/gb/newGbInfo?hcno=7803DE42D3BC5E80B0C3E5D8E873D56A)
- GB/T 38635.1–.2 (SM9) — [open](https://openstd.samr.gov.cn/bzgk/gb/newGbInfo?hcno=B7A0D7DFF411CD0AAE76135ADE91886A)
- GB/T 22239-2019 等级保护基本要求 — [open](https://openstd.samr.gov.cn/bzgk/gb/newGbInfo?hcno=BAFB47E8874764186BDB7865E8344DAF)
- GB/T 35273-2020 个人信息安全规范 — [open](https://openstd.samr.gov.cn/bzgk/gb/newGbInfo?hcno=4568F276E0F8346EB0FBA097AA0CE05E)
