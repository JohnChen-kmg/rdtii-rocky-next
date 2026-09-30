# CN_manual_2026-09-20 — five administrative regulations, saved by hand

**Why these five.** The research of 2026-09-20 found that China's National Database of Laws and Regulations
answers 18 of the instrument's 61 indicators in full, and that most of the rest fail the same way: **the
regulation states the rule and delegates the number to a catalogue, list or standard published separately**.
Four of these five test that pattern; the fifth is a control that should disprove it.

| # | Instrument | Decree | What to check in the text | What the answer means |
| :---- | :---- | :---- | :---- | :---- |
| 1 | 电信条例 Telecommunications Regulations | 291 (2000, rev. 2016) | Search **附件** and **电信业务分类目录**; read 第七条–第十五条 | If the annexed catalogue is absent, indicator **5.5** cannot be answered from this tier |
| 2 | 外商投资电信企业管理规定 Foreign-Invested Telecom Enterprises | 534 → **752** (2022) | Search **49** and **50** (第六条); check the decree number shown | Present, but incomplete: a MIIT notice of October 2024 lifted the cap in four zones (**3.1, 5.2**) |
| 3 | 网络数据安全管理条例 Network Data Security Management | **790** (in force 2025-01-01) | Search **一千万** (第二十八条, 第三十条) | **The control.** If the ten-million threshold is here, a regulation *can* carry the number (**7.4**) |
| 4 | 非银行支付机构监督管理条例 Non-Bank Payment Institutions | **768** (in force 2024-05-01) | Search **限额** and **额度** | Expect none: the ceilings live in PBOC notices (**12.4.5**) |
| 5 | 两用物项出口管制条例 Dual-Use Items Export Control | **792** (in force 2024-12-01) | Search **管制清单** and **目录** | Expect "制定、调整并公布": the list is delegated to a MOFCOM announcement (**10.4**) |

## How to save them

1. Put each file in `raw/`, named `<number>_<pinyin-or-short-name>.<ext>` — for example
   `1_dianxin_tiaoli.html`. HTML, PDF or Word all work; record which.
2. Add one line per file to `provenance.tsv`, which already has its header. Every column matters:
   a hand-collected file is only evidence if it says where and when it came from.
3. Leave `raw/` out of git — `.gitignore` already excludes it. The provenance sheet is what is kept.

## What happens next

Tell me when the files are in, and I will read them and report: whether each document is the version its decree
number claims, whether the searched term is present, and what that means for the indicators in the table above.
I will not fetch anything from that site myself.
