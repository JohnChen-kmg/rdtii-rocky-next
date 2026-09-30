# Check by hand

**Written by `countries/cn-china/tools/collect.py` at 2026-09-22 00:54.** Rewritten on every run.

**33 sources are not collected automatically.** A run of the tool is not a complete update
until each has been checked. After checking one, record it:

```
python countries/cn-china/tools/collect.py --checked "国家数据局"
```

| Last checked | Kind | Source | What to look for | Expect |
| :---- | :---- | :---- | :---- | :---- |
| **never** | layer-1 | [国家法律法规数据库 · layer 1](https://flk.npc.gov.cn/) | New and revised laws and administrative regulations. Re-download in bulk | continuous |
| **never** | manual-host | [工业和信息化部 · 政策文件](https://www.miit.gov.cn/zwgk/zcwj/) | New 令, 通告 and 公告; changes to 电信业务分类目录 and to the 进网许可 catalogue. Save attachments | irregular |
| **never** | manual-host | [国家发展和改革委员会 · 发展改革委令 [deferred]](https://www.ndrc.gov.cn/xxgk/zcfb/fzggwl/) | A new 外商投资准入负面清单 or 自贸区负面清单; a new 鼓励外商投资产业目录 | negative list revised 2019, 2020, 2021, 2024; encouraged list 2022, 2025 |
| **never** | manual-host | [中国人民银行 · 条法司 规范性文件 [deferred]](https://www.pbc.gov.cn/tiaofasi/144941/3581332/index.html) | Payment rules, caps and account tiers; anything replacing 银发〔2017〕296号 | irregular |
| **never** | manual-host | [中国人民银行 · 条法司 规章 [deferred]](https://www.pbc.gov.cn/tiaofasi/144941/144957/index.html) | New PBOC 令 — the 银行卡清算 rule was replaced in 2025 and the crypto notice in 2026 | irregular |
| **never** | manual-host | [国家外汇管理局 [deferred]](https://www.safe.gov.cn/) | Cross-border payment and FX rules for payment institutions | irregular |
| **never** | manual-host | [海关总署 · 公告](https://www.customs.gov.cn/customs/302249/302266/302267/index.html) | Cross-border e-commerce supervision (1210 / 9610 / 9710 / 9810); any new customs list | irregular |
| **never** | manual-host | [公安部 [deferred]](https://www.mps.gov.cn/n6557558/index.html) | New 公安部令 on network security; the 网络安全等级保护条例 if it is ever finalised | irregular |
| **never** | manual-host | [国家卫生健康委员会 [deferred]](https://www.nhc.gov.cn/) | Health-data rules | irregular |
| **never** | manual-host | [司法部 · 国家规章库](https://www.moj.gov.cn/pub/sfbgw/flfggz/) | The cross-ministry index of current 部门规章 — the best single place to spot a rule from a publisher we do not watch | continuous |
| **never** | standards | [国家标准 GB/T [deferred]](https://openstd.samr.gov.cn/bzgk/gb/) | New editions of SM2, SM3, SM4, SM9, GB/T 22239, GB/T 35273 | irregular |
| **never** | stream | [财政部关税司 · 政策发布 [deferred]](https://gss.mof.gov.cn/gzdt/zhengcefabu/) | The annual 关税调整方案; any change to the ¥50 免征额 or to the cross-border e-commerce caps and list | tariff plan every late December |
| **never** | stream | [商务部 · 政策发布 [deferred]](https://www.mofcom.gov.cn/zwgk/zcfb/) | 进口许可证管理货物目录 (every December); 禁止进口货物目录 batches; export-control and technology catalogues | import licence catalogue every late December |
| **never** | stream | [商务部 · 出口管制 [deferred]](http://exportcontrol.mofcom.gov.cn/) | A new 两用物项出口管制清单; the annual 两用物项和技术进出口许可证管理目录 | licence catalogue every late December |
| **never** | stream | [商务部 · 服贸司 技术进出口 [deferred]](https://fms.mofcom.gov.cn/zcfg/jsjckzcfg/) | Adjustments to 禁止出口限制出口技术目录 and 禁止进口限制进口技术目录 | irregular: 2020, 2023, 2025 |
| **never** | stream | [商务部 · 贸易救济调查局 [deferred]](https://trb.mofcom.gov.cn/) | New investigations, determinations and sunset reviews on ICT goods | continuous |
| **never** | stream | [国家认证认可监督管理委员会 · 公告 [deferred]](https://www.cnca.gov.cn/zwxx/gg/) | Changes to the 强制性产品认证目录 and CCC implementing rules | several a year |
| **never** | stream | [国家密码管理局 · 新闻动态 [deferred]](https://www.oscca.gov.cn/sca/xwdt/) | A fourth batch of the 商用密码产品认证目录; changes to the import and export lists | batches 2020, 2022, 2025 |
| **never** | canary | [中国政府网 · 国务院政策文件库](https://www.gov.cn/zhengce/zhengceku/) | 国务院部门文件 — notices from any ministry, including ones not on this list. A notice from an unfamiliar issuer means the list is out of date | continuous |
| **never** | new-publisher | [国家数据局](https://www.nda.gov.cn/) | Data rules — cross-border data, data property, public data. Pillar 6 and 7 territory | continuous |
| **never** | new-publisher | [国家金融监督管理总局](https://www.nfra.gov.cn/) | Financial-sector data and record-retention rules | irregular |
| **never** | new-publisher | [国家知识产权局](https://www.cnipa.gov.cn/) | Patent examination rules touching software and algorithms | irregular |
| **never** | new-publisher | [国家统计局](https://www.stats.gov.cn/) | Statistical-data rules, if any bear on data flows | irregular |
| **never** | new-publisher | [自然资源部 · Ministry of Natural Resources](https://www.mnr.gov.cn/) | Map and geographic-information rules: restrictions on exporting or hosting geographic data | irregular |
| **never** | regulator | [国家市场监督管理总局 · 法规司 [deferred]](https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/fgs/) | Rules on online trading, advertising, standards, product certification | irregular |
| **never** | regulator | [商务部 · 规章库 [deferred]](https://www.mofcom.gov.cn/zfxxgk/zc/gz/) | Rules on trade, investment and e-commerce among its 152 in force | irregular |
| **never** | regulator | [国家密码管理局 · 政策法规 [deferred]](https://www.oscca.gov.cn/sca/xxgk/zcfg/flfg.shtml) | Commercial-cryptography rules | irregular |
| **never** | regulator | [国家新闻出版署 · NPPA [deferred]](https://www.nppa.gov.cn/) | Online-publishing rules, including the server-location rule | irregular |
| **never** | regulator | [国家广播电视总局 · NRTA [deferred]](https://www.nrta.gov.cn/) | Online audiovisual rules | irregular |
| **never** | regulator | [文化和旅游部 · MCT [deferred]](https://www.mct.gov.cn/) | Internet-culture rules | irregular |
| **never** | regulator | [科学技术部 · MOST [deferred]](https://www.most.gov.cn/) | Human-genetic-resources data rules | irregular |
| **never** | regulator | [国务院国资委 · SASAC [deferred]](http://www.sasac.gov.cn/) | The central-enterprise directory: state ownership of telecom operators | rolling |
| **never** | canary | [国务院公报 · gazette index [deferred]](https://www.gov.cn/gongbao/) | Rules issued or amended by any ministry, including ones not on this list | about 36 issues a year |

**Kinds.** `manual-host`: the host refuses us or forbids us. `stream`: an announcement stream the tool
takes only verified links from. `new-publisher`: a body not in the source list. `canary`: a cross-ministry
index where a rule from an unfamiliar issuer is the sign the list itself is out of date.

The list lives in `countries/cn-china/watchlist.tsv`. Add a row when a new publisher is found.
