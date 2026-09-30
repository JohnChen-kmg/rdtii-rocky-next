"""Triage a list copied from a site the tool may not fetch — offline, sending no request.

    python countries/cn-china/tools/triage.py <pasted.txt> [<more.txt> ...] [--out triage.md]

Give every page of one list together: an old version on page 7 is only known to be superseded if the newer one on
page 1 is in the same run.

For the hosts collected by hand (MIIT, Customs): the developer copies a listing page's text from a browser into a
file, one item per line, a title followed by its date (`电信业务经营许可管理办法2017-07-13`). This sorts every item into

    already held    in layer 1 (the national database export) or in the CAC set — skip
    superseded      an older version of something newer on the same list, or of a renamed successor — skip
    relevant        not held, on the information and communications side — download
    borderline      needs a person's judgement, with the reason
    skip            industrial or procedural

Relevance is a declared keyword rule, written in advance from the instrument's topics, not from known answers. It is
crude on purpose and says so: read the borderline group, and glance at what it skips.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collect  # noqa: E402

RELEVANT = re.compile("电信|通信|互联网|网络|无线电|频率|卫星|域名|数据|信息保护|个人信息|进网|码号|电子认证|电子签名|短信息|"
                      "电子邮件|IP地址|地球站|电话用户|网约|跨境电子商务|跨境电商|电子商务|密码|软件|集成电路|人工智能|算法")
INDUSTRIAL = re.compile("烟草|食盐|盐业|汽车|乘用车|摩托车|民用爆炸|化学品|化学物质|核|武器|军|国防|农药|农业|钢铁|水泥|节能|能源|"
                        "乳品|食品|气象|放射|环境|循环经济|清洁生产|航天|空间物体|废弃电器|安全生产|生产安全|动植物|检疫|药品")
PROCEDURAL = re.compile("行政许可实施|行政复议|听证规则|行政处罚|行政审批|关于废止|关于修改|修改部分|修改和废止|制定程序|无证无照|"
                        "公益广告|公共资源交易|无障碍")
#: judged in advance, with the reason — a person's call the keywords cannot make
BORDERLINE = {"网络借贷信息中介机构业务活动管理暂行办法": "online lending: fintech, not a payments measure",
              "电器电子产品有害物质限制使用管理办法": "China RoHS: a product rule on ICT goods, possibly 11.x",
              "通信工程建设项目招标投标管理办法": "telecom construction bidding: pillar 2, not automated",
              "电子招标投标办法": "e-procurement procedure: pillar 2, not automated",
              "关于境内企业承接服务外包业务信息保护的若干规定": "information protection for outsourcing firms: 7.x, from 2009"}
#: an old title -> the title that replaced it
SUCCESSOR = {"中国互联网络域名管理办法": "互联网域名管理办法", "电信用户申诉处理暂行办法": "电信用户申诉处理办法",
             "通信工程质量监督管理规定": "通信建设工程质量监督管理规定"}


def core(t: str) -> str:
    t = re.sub(r"（\d{4}年[^）]*）", "", t)
    t = re.sub(r"^中华人民共和国", "", t)
    return re.sub(r"[《》\s]", "", t)


def held() -> tuple[dict, dict]:
    idx = os.path.join(collect.REPO, "outputs", "CN", "CN_sources_2026-09-21", "manual", "npc-database", "index.csv")
    l1 = {core(r["title"]): r["title"] + " (" + r["version_date"] + ")"
          for r in csv.DictReader(open(idx, encoding="utf-8-sig"))} if os.path.exists(idx) else {}
    cac_csv = os.path.join(collect.folder_dir("cac"), "list.csv")
    cac = {core(r["title"]): r["title"] for r in csv.DictReader(open(cac_csv, encoding="utf-8-sig"))} \
        if os.path.exists(cac_csv) else {}
    return l1, cac


def parse(text: str) -> list[tuple[str, str]]:
    items = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or re.fullmatch(r"(法律法规|上一页.*|下一页.*|\d+)", ln):
            continue
        m = re.match(r"^(.*?)(\d{4}-\d{2}-\d{2})?\s*$", ln)
        if m and len(m.group(1)) >= 4:
            items.append((m.group(1).strip(), m.group(2) or ""))
    return items


def triage(items: list[tuple[str, str]]) -> dict:
    l1, cac = held()
    newest = {}
    for t, d in items:
        newest[core(t)] = max(newest.get(core(t), ""), d)
    listed = {core(t) for t, _ in items}
    out = {k: [] for k in ("relevant", "borderline", "held", "superseded", "skip")}
    for t, d in dict.fromkeys(items):
        c = core(t)
        if SUCCESSOR.get(c) in listed:
            out["superseded"].append((t, d, f"replaced by {SUCCESSOR[c]}"))
        elif newest[c] > d:
            out["superseded"].append((t, d, f"a newer entry, {newest[c]}, is on the list"))
        elif c in l1:
            out["held"].append((t, d, "layer 1: " + l1[c]))
        elif c in cac:
            out["held"].append((t, d, "CAC set"))
        elif c in {core(k) for k in BORDERLINE}:
            out["borderline"].append((t, d, next(v for k, v in BORDERLINE.items() if core(k) == c)))
        elif PROCEDURAL.search(t):
            out["skip"].append((t, d, "procedural"))
        elif INDUSTRIAL.search(t) and not RELEVANT.search(t):
            out["skip"].append((t, d, "industrial"))
        elif RELEVANT.search(t):
            out["relevant"].append((t, d, ""))
        else:
            out["borderline"].append((t, d, "no topic keyword either way — read it"))
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("pasted", nargs="+", help="one or more files of pasted list text; give every page of a list together")
    ap.add_argument("--out")
    a = ap.parse_args()
    items = [it for f in a.pasted for it in parse(open(f, encoding="utf-8").read())]
    res = triage(items)
    lines = [f"# Triage of {', '.join('`' + os.path.basename(f) + '`' for f in a.pasted)}", "",
             f"{len(items)} items: **{len(res['relevant'])} to download**, {len(res['borderline'])} borderline, "
             f"{len(res['held'])} already held, {len(res['superseded'])} superseded, {len(res['skip'])} skipped.", ""]
    for g, title in (("relevant", "Download"), ("borderline", "Borderline — read these"), ("held", "Already held"),
                     ("superseded", "Superseded"), ("skip", "Skipped")):
        lines += [f"## {title} ({len(res[g])})", ""] + [f"- {d} {t}" + (f" — {w}" if w else "") for t, d, w in res[g]] + [""]
    text = "\n".join(lines)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
