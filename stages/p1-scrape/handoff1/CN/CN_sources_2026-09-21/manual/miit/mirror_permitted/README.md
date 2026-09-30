# MIIT documents, fetched from hosts that permit us — 2026-09-22

**Why this folder exists.** `www.miit.gov.cn` answers 403 to any honest client, so MIIT is collected by hand into
`../raw/`. Six of those documents are also published by hosts that **do** serve us — the State Council Gazette and
CAC — so they were fetched with `tools/collect.py` through the polite client instead of being printed in a browser.
Each is a machine-readable copy of a document the hand-collected folder holds as a picture or not at all.

Six documents, in `raw/` (as served) and `text/` (extracted). Provenance in `provenance.tsv`, every request in
`run_log.jsonl`.

| Document | From | Note |
| :---- | :---- | :---- |
| 电信业务经营许可管理办法 (令42) | gov.cn 公报 2017年第32号 | same version as the hand copy |
| 增值电信业务扩大对外开放试点通告 | gov.cn 政策库 | **plus its 附件**, the 试点方案 itself, saved in `raw/` as `…__P020240410661560824373.pdf` |
| 工业和信息化领域数据安全管理办法（试行） | gov.cn 政策库 | same version as the hand copy |
| 关于规范互联网信息服务使用域名的通知 | CAC | same version as the hand copy |
| **中华人民共和国无线电频率划分规定** | gov.cn 公报 2023年第23号 | **工信部令第62号, in force 2023-07-01 — newer than the 2018 令46 held by hand** |
| **通信短信息服务管理规定** | gov.cn 公报 2026年第15号 | **工信部令第74号, in force 2026-05-01 — newer than the 2015 text held by hand** |

**The caveat that matters.** The gazette gives a rule's text **as issued**, not the consolidated text in force. For
a rule never amended since, the two are the same. For one amended later, this copy is the version its 令 number
names and nothing more. The 令 number and date are on each document; use them, not the fetch date.

**How the last two were found.** Not from MIIT — its 法律法规 list stops at 2022-01-29 and cannot show either
amendment. They came from searching the 180 already-cached gazette issues offline against the documents held.
That is the gazette earning its keep as a canary, and it is written up in `../../../../countries/cn-china/SOURCES.md`.
