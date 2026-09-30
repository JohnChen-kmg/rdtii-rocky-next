"""Collect China's layer 2 from the publishers that permit it.

    python countries/cn-china/tools/collect.py <source> [--list-only] [--limit N]

    source   cac | samr | mofcom | oscca | links | all
             cac     CAC's 政策法规 index, six categories (JSON /cms/JsonList)
             samr    SAMR 法规司, whole section (JPAAS listing API), plus SAMR's verified links
             mofcom  MOFCOM 规章库 — 152 rules in force (JPAAS), plus MOFCOM's verified links
             oscca   OSCCA 法律法规 and 规范性文件 sections, plus OSCCA's verified links
             links   the verified links for cnca, mof-tariff, sectoral and govcn
             all     every one of the above, in that order

Writes into outputs/CN/CN_sources_2026-09-21/auto/<folder>/:

    raw/<stem>.html           the page as served          (kept out of git)
    raw/<stem>__<file>        each attachment it links    (kept out of git)
    text/<stem>.txt           the body text
    list.csv                  what discovery found
    provenance.tsv            one line per document fetched
    manifest.json             the same, plus refusals and the per-host robots verdicts
    run_log.jsonl             every request, with its status

Every request goes through polite.PoliteClient, which reads robots.txt first, refuses a host that forbids us
or refuses its own robots file, never retries a 403, and waits 8-12 s between requests to one host.
Re-running resumes: a document whose page is already in raw/ is not fetched again.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from polite import HostRefused, PoliteClient  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

def _data_root() -> str:
    """The directory that holds `CN/`, China's collection folders.

    A setting first: HANDOFF1_DIR, which `interface/DATA_PATHS.md` already defines as the
    crawler's corpus location, so a reviewer points this at their own copy without editing
    code. Failing that, the two layouts this module ships in — the development workshop,
    where the collection sits under `outputs/`, and the submission repository, where it
    sits under `handoff1/` beside the code.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    bases = []
    env = os.getenv("HANDOFF1_DIR")
    if env:
        bases += [env, os.path.abspath(os.path.join(env, os.pardir))]
    bases += [
        os.path.abspath(os.path.join(here, *[os.pardir] * 3)),   # workshop: countries/cn-china/tools/../../..
        os.path.abspath(os.path.join(here, *[os.pardir] * 4)),   # submission: src/p1_scrape/adapters/cn_npc/../../../..
    ]
    for base in bases:
        if os.path.isdir(os.path.join(base, "CN")):
            return base
        for sub in ("handoff1", "outputs"):
            if os.path.isdir(os.path.join(base, sub, "CN")):
                return os.path.join(base, sub)
    return os.path.join(bases[-1], "handoff1")


DATA = _data_root()
#: kept for callers that still expect it; DATA is what the paths below are built from
REPO = os.path.abspath(os.path.join(DATA, os.pardir))
OUT = os.path.join(DATA, "CN", "CN_sources_2026-09-21", "auto")
#: sources set aside on 2026-09-22 to focus on the national database and the key areas (CAC, MIIT, Customs)
DEFERRED = os.path.join(DATA, "CN", "CN_sources_2026-09-21", "_deferred", "auto")
LINKS_MD = os.path.join(DATA, "CN", "CN_layer2_links.md")


def folder_dir(folder: str) -> str:
    """Where a source's folder lives now: active under auto/, or set aside under _deferred/auto/.
    Running a deferred source writes into its deferred folder rather than recreating one under auto/."""
    active, deferred = os.path.join(OUT, folder), os.path.join(DEFERRED, folder)
    if os.path.isdir(active) or not os.path.isdir(deferred):
        return active
    return deferred

# ---- the sources ---------------------------------------------------------------------------

CAC_CHANNELS = [
    ("A09370301", "法律"), ("A09370302", "行政法规"), ("A09370303", "部门规章"),
    ("A09370304", "司法解释"), ("A09370305", "规范性文件"), ("A09370306", "政策文件"),
]

JPAAS = {
    "samr": {
        "root": "https://www.samr.gov.cn",
        "section": "法规司",
        "params": {
            "webId": "29e9522dc89d4e088a953d8cede72f4c",
            "pageId": "8395bc4a17d04d118c93e9904b258182",
            "tplSetId": "5c30fb89ae5e48b9aefe3cdf49853830",
            "tagId": "内容区域",
        },
    },
    "mofcom": {
        "root": "https://www.mofcom.gov.cn",
        "section": "规章库",
        "params": {
            "webId": "8f43c7ad3afc411fb56f281724b73708",
            "pageId": "8f9725e7377f44e3bf04b68cd18d21e5",
            "tplSetId": "52551ea0e2c14bca8c84792f7aa37ead",
            "tagId": "规章库列表",
        },
    },
}

OSCCA_SECTIONS = [
    ("法律法规", "https://www.oscca.gov.cn/sca/xxgk/zcfg/flfg.shtml"),
    ("规范性文件", "https://www.oscca.gov.cn/sca/xxgk/zcfg/gfxwj.shtml"),
]

#: first-link host -> auto folder (manual hosts are absent on purpose)
AUTO_HOSTS = {
    "www.cac.gov.cn": "cac",
    "www.samr.gov.cn": "samr", "www.cnca.gov.cn": "cnca",
    "www.mofcom.gov.cn": "mofcom", "fms.mofcom.gov.cn": "mofcom", "exportcontrol.mofcom.gov.cn": "mofcom",
    "trb.mofcom.gov.cn": "mofcom", "cacs.mofcom.gov.cn": "mofcom", "policy.mofcom.gov.cn": "mofcom",
    "www.oscca.gov.cn": "oscca",
    "gss.mof.gov.cn": "mof-tariff", "www.mof.gov.cn": "mof-tariff", "gks.mof.gov.cn": "mof-tariff",
    "www.nppa.gov.cn": "sectoral", "www.nrta.gov.cn": "sectoral", "zwgk.mct.gov.cn": "sectoral",
    "www.most.gov.cn": "sectoral", "www.sasac.gov.cn": "sectoral",
    "www.gov.cn": "govcn",
}

#: titles that name an administrative act of the ministry itself rather than a legal instrument.
#: Flagged, never dropped (flag, don't fix).
NOT_INSTRUMENT = re.compile(r"选聘|招聘|年度报告|工作报告|法治政府建设|政府信息公开工作|名单公示|征求意见|座谈|培训|会议")

ATTACH = re.compile(r"""href\s*=\s*["']?([^"'\s>]+\.(?:pdf|docx?|xlsx?|wps|ofd|zip|rar))""", re.I)
CONTENT_HINT = re.compile(
    r"""<(div|td|section|article)[^>]*(?:id|class)\s*=\s*["']?[^"'>]*(?:content|article|detail|TRS_Editor|zoom|pages_content|text|main-text|xxgk_content|con_con|mainText)[^"'>]*["']?[^>]*>""",
    re.I,
)


# ---- helpers -------------------------------------------------------------------------------

def host_of(u: str) -> str:
    return urllib.parse.urlparse(u).netloc


def absolute(base: str, href: str) -> str:
    href = href.strip()
    if href.startswith("//"):
        return "https:" + href
    return urllib.parse.urljoin(base, href)


def stem_for(title: str, url: str) -> str:
    s = re.sub(r"[^\w一-鿿]+", "-", title or "doc").strip("-")[:48]
    return f"{s or 'doc'}-{hashlib.sha256(url.encode()).hexdigest()[:8]}"


def strip_tags(html: str) -> str:
    h = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    h = re.sub(r"<br\s*/?>|</p\s*>|</div\s*>|</tr\s*>|</li\s*>|</h\d\s*>", "\n", h, flags=re.I)
    h = re.sub(r"<[^>]+>", "", h)
    for a, b in (("&nbsp;", " "), ("&#160;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                 ("&ldquo;", "“"), ("&rdquo;", "”"), ("&quot;", '"'), ("&middot;", "·")):
        h = h.replace(a, b)
    lines = [re.sub(r"[ \t　]+", " ", ln).strip() for ln in h.split("\n")]
    return "\n".join(ln for ln in lines if ln)


def body_text(html: str) -> str:
    """The article body: the content-looking block with the most Chinese text, else the whole page."""
    best, best_n = "", 0
    for m in CONTENT_HINT.finditer(html):
        chunk = html[m.start(): m.start() + 200_000]
        txt = strip_tags(chunk)
        n = len(re.findall(r"[一-鿿]", txt))
        if n > best_n:
            best, best_n = txt, n
    return best if best_n > 200 else strip_tags(html)


def clean_title(t: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t or "")).strip()


# ---- discovery -----------------------------------------------------------------------------

def discover_cac(client: PoliteClient) -> list[dict]:
    items = []
    for code, cat in CAC_CHANNELS:
        body = urllib.parse.urlencode({"channelCode": code, "perPage": "100", "pageno": "1",
                                       "condition": "0", "fuhao": "=", "value": ""}).encode()
        r = client.get("https://www.cac.gov.cn/cms/JsonList", data=body,
                       headers={"Content-Type": "application/x-www-form-urlencoded",
                                "Referer": "https://www.cac.gov.cn/wxzw/zcfg/A093703index_1.htm"})
        data = json.loads(r.text()) if r.ok else {}
        for it in data.get("list", []) or []:
            items.append({"title": clean_title(it.get("topic")), "url": absolute("https://www.cac.gov.cn/", it.get("infourl", "")),
                          "date": (it.get("pubtime") or "")[:10], "section": cat, "via": "index"})
        print(f"   {cat:<8} {len(data.get('list', []) or []):>4} of {data.get('totalRec', '?')}", flush=True)
    return items


#: the site's own page size. pageSize=100 returned 99 rows on both sites, so a larger page risks an
#: off-by-one gap at every page boundary; 20 is what the sites' own pagers ask for.
JPAAS_PAGE = 20
JPAAS_MAX_PAGES = 40


def discover_jpaas(client: PoliteClient, name: str) -> list[dict]:
    """SAMR lists rows as <li>, MOFCOM as <tr>; both put the document link on an art_<hash>.html address."""
    cfg = JPAAS[name]
    items, page = [], 1
    while page <= JPAAS_MAX_PAGES:
        q = dict(cfg["params"], parseType="bulidstatic", pageType="column",
                 paramJson=json.dumps({"pageNo": page, "pageSize": JPAAS_PAGE}))
        url = f"{cfg['root']}/api-gateway/jpaas-publish-server/front/page/build/unit?{urllib.parse.urlencode(q)}"
        r = client.get(url)
        if not r.ok:
            print(f"   page {page}: HTTP {r.status}", flush=True)
            break
        html = (json.loads(r.text()).get("data") or {}).get("html", "")
        found = 0
        for row in re.split(r"<(?:li|tr)\b", html, flags=re.I)[1:]:
            m = re.search(r"""<a[^>]+href\s*=\s*["']([^"']*art_[0-9a-f]{16,}\.html)["'][^>]*>(.*?)</a>""", row, flags=re.S | re.I)
            if not m:
                continue
            t = re.search(r"""title\s*=\s*["']([^"']+)["']""", m.group(0))
            title = clean_title(t.group(1) if t else m.group(2))
            if len(title) < 4:
                continue
            d = re.search(r"(20\d\d|19\d\d)[-./年](\d{1,2})[-./月](\d{1,2})", row)
            note = re.search(r"""class\s*=\s*["']zc_list_con["'][^>]*>(.*?)</span>""", row, flags=re.S | re.I)
            items.append({"title": title, "url": absolute(cfg["root"] + "/", m.group(1)),
                          "date": f"{d.group(1)}-{int(d.group(2)):02d}-{int(d.group(3)):02d}" if d else "",
                          "section": cfg["section"], "via": "index",
                          "reference": clean_title(note.group(1)).strip("()（）") if note else ""})
            found += 1
        print(f"   page {page}: {found} rows", flush=True)
        if found == 0:
            break
        page += 1
    # a listing can repeat a row across a page boundary
    seen, out = set(), []
    for it in items:
        if it["url"] not in seen:
            seen.add(it["url"])
            out.append(it)
    return out


def discover_oscca(client: PoliteClient) -> list[dict]:
    items = []
    for section, first in OSCCA_SECTIONS:
        url, pages = first, 0
        while url and pages < 20:
            r = client.get(url)
            pages += 1
            if not r.ok:
                print(f"   {section}: HTTP {r.status}", flush=True)
                break
            html = r.text()
            n = 0
            for m in re.finditer(r"""<a[^>]+href\s*=\s*["']([^"']*content_\d+\.shtml)["'][^>]*>(.*?)</a>""", html, re.S | re.I):
                t = re.search(r"""title\s*=\s*["']([^"']+)["']""", m.group(0))
                title = clean_title(t.group(1) if t else m.group(2))
                tail = html[m.end(): m.end() + 200]
                d = re.search(r"(20\d\d)-(\d\d)-(\d\d)", tail) or re.search(r"(20\d\d)-(\d\d)-(\d\d)", m.group(1))
                items.append({"title": title, "url": absolute(url, m.group(1)),
                              "date": "-".join(d.groups()) if d else "", "section": section, "via": "index"})
                n += 1
            print(f"   {section} page {pages}: {n} rows", flush=True)
            nxt = re.search(r"""<a[^>]+href\s*=\s*["']([^"']+)["'][^>]*>\s*下一页""", html)
            url = absolute(url, nxt.group(1)) if nxt and "javascript" not in nxt.group(1) else None
    seen, out = set(), []
    for it in items:
        if it["url"] not in seen and it["title"]:
            seen.add(it["url"])
            out.append(it)
    return out


# ---- the State Council Gazette: every ministry's rules, from a host that permits us ---------------
#
# 立法法 第九十七条 publishes departmental rules in the 国务院公报 (or the department's own gazette), so a gazette
# copy is an official publication of the rule, not a mirror. `www.gov.cn` permits us; `gbgl.json` lists every issue
# since 2000; each issue's contents are plain HTML. That gives MIIT's, NDRC's and PBOC's rules without touching
# their sites — robots.txt is per host, and the gazette is a different publisher doing what the law tells it to.
# Not usable: `sousuo.www.gov.cn`, the policy library's search, whose robots.txt is `Disallow: /`.

GAZETTE_INDEX = "https://www.gov.cn/gongbao/gbgl.json"
_CN_DIGIT = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
_CN_UNIT = {"十": 10, "百": 100, "千": 1000}

#: issuers whose rules the index can need; everything else is indexed and not fetched
RELEVANT_ISSUERS = re.compile(
    "工业和信息化部|信息产业部|发展和改革|发展改革|计划委员会|人民银行|商务部|对外贸易经济合作部|互联网信息|网信|"
    "市场监督管理|工商行政管理|质量监督检验检疫|认证认可|标准化管理|公安部|财政部|海关总署|关税税则|卫生健康|卫生和计划生育|"
    "密码管理|外汇管理|金融监督管理|银行保险监督|银行业监督|证券监督|数据局|知识产权|自然资源|新闻出版|广播电视|广播电影电视|"
    "文化和旅游|文化部|科学技术部|国有资产监督|国务院$|主席$"
)
RELEVANT_TOPICS = re.compile(
    "数据|网络|互联网|电信|通信|无线电|频率|卫星|域名|电子商务|电子签名|支付|清算|个人信息|隐私|密码|信息安全|计算机|软件|"
    "集成电路|人工智能|算法|跨境|外商投资|负面清单|进出口|出口管制|两用物项|关税|标准化|认证|知识产权|著作权|专利|商标|广告|"
    "消费者|网络交易|直播|征信|反洗钱|招标投标|政府采购"
)


def cn_number(s: str):
    """第五十六号 -> 56, 第82号 -> 82, 〔2025〕第2号 -> 2. Returns (year or None, number or None)."""
    year = re.search(r"(19|20)\d\d", s)
    tail = s[year.end():] if year else s
    m = re.search(r"(\d+)\s*号", tail)
    if m:
        return (int(year.group(0)) if year else None), int(m.group(1))
    m = re.search(r"第?([零〇一二两三四五六七八九十百千]+)号", tail)
    if not m:
        return (int(year.group(0)) if year else None), None
    total, cur = 0, 0
    for ch in m.group(1):
        if ch in _CN_DIGIT:
            cur = _CN_DIGIT[ch]
        else:
            total += (cur or 1) * _CN_UNIT[ch]
            cur = 0
    return (int(year.group(0)) if year else None), total + cur


def _gazette_issues(index_json: str) -> list[tuple[str, str, str]]:
    found = []

    def walk(o, path):
        if isinstance(o, dict):
            g = o.get("gname")
            if isinstance(g, str) and "/gongbao/" in g:
                found.append((path[-2] if len(path) >= 2 else "", path[-1] if path else "", g))
            for k, v in o.items():
                walk(v, path + [k])
        elif isinstance(o, list):
            for v in o:
                walk(v, path)

    walk(json.loads(index_json.lstrip("﻿")), [])
    return found


def parse_gazette_issue(html: str, issue_url: str, year: str, issue: str) -> list[dict]:
    rows = []
    for href, inner in re.findall(r"""<a[^>]+href=["']([^"']*content_\d+\.html?)["'][^>]*>(.*?)</a>""", html, re.S | re.I):
        parts = [re.sub(r"[\s　]+", " ", re.sub(r"<[^>]+>", "", p)).strip() for p in re.split(r"<br\s*/?>", inner, flags=re.I)]
        parts = [p for p in parts if p]
        raw = " | ".join(parts)
        if len(raw) < 6 or re.fullmatch(r"\d{4}年", raw) or raw.endswith("网站") or "公报增刊" in raw:
            continue
        joined = "".join(parts)
        m = re.match(r"^(.{2,80}?)令（(.+?)）(.*)$", joined)
        if m:
            issuer, order_no, title, kind = re.sub(r"中华人民共和国", "", m.group(1)).strip(), m.group(2), m.group(3).strip(), "order"
        else:
            mi = re.match(r"^(.{2,40}?)关于", joined)
            issuer, order_no, title, kind = (mi.group(1).strip() if mi else ""), "", joined, "document"
        oy, on = cn_number(order_no) if order_no else (None, None)
        rows.append({
            "year": year.rstrip("年"), "issue": issue, "kind": kind, "issuer": issuer, "order_no": order_no,
            "order_year": oy or "", "order_num": on if on is not None else "", "title": title, "raw": raw,
            "url": urllib.parse.urljoin(issue_url, href), "issue_url": issue_url,
            "relevant": "yes" if (RELEVANT_ISSUERS.search(issuer) or RELEVANT_TOPICS.search(title)) else "",
        })
    return rows


def discover_gazette(client: PoliteClient) -> tuple[list[dict], list[dict]]:
    """Every entry of every gazette issue since 2000. Issue pages are cached under raw/issues/, so an update
    fetches the index and only the issues it has not seen."""
    cache = os.path.join(folder_dir("gazette"), "raw", "issues")
    os.makedirs(cache, exist_ok=True)
    r = client.get(GAZETTE_INDEX)
    if not r.ok:
        print(f"   gbgl.json: HTTP {r.status}", flush=True)
        return [], []
    issues = _gazette_issues(r.text())
    print(f"   gbgl.json: {len(issues)} issues", flush=True)
    entries, failed = [], []
    for i, (year, issue, url) in enumerate(issues, 1):
        key = re.sub(r"[^\w]+", "_", url.split("/gongbao/", 1)[-1]).strip("_")
        p = os.path.join(cache, key + ".html")
        if os.path.exists(p) and os.path.getsize(p) > 2000:
            html = open(p, encoding="utf-8", errors="replace").read()
        else:
            try:
                rr = client.get(url)
            except HostRefused as e:
                failed.append({"url": url, "reason": str(e)})
                break
            if not rr.ok:
                failed.append({"url": url, "status": rr.status})
                print(f"   {i:4d}/{len(issues)} {year}{issue}: HTTP {rr.status}", flush=True)
                continue
            html = rr.text()
            open(p, "w", encoding="utf-8").write(html)
        got = parse_gazette_issue(html, url, year, issue)
        entries.extend(got)
        if i % 25 == 0 or i == len(issues):
            print(f"   {i:4d}/{len(issues)}  {year}{issue}  entries so far {len(entries)}", flush=True)
    return entries, failed


#: rules we already hold by hand: the gazette's recall test. (label, issuer pattern, number, year or None)
GAZETTE_RECALL = [
    ("MIIT 令24 电信和互联网用户个人信息保护规定", "工业和信息化部", 24, None),
    ("MIIT 令28 电信设备进网 amendment", "工业和信息化部", 28, None),
    ("MIIT 令42 电信业务经营许可管理办法", "工业和信息化部", 42, None),
    ("MIIT 令43 互联网域名管理办法", "工业和信息化部", 43, None),
    ("MIIT 令57 无线电发射设备管理规定", "工业和信息化部", 57, None),
    ("MIIT 令68 电信设备进网 amendment", "工业和信息化部", 68, None),
    ("MPS 令82 互联网安全保护技术措施规定", "公安部", 82, None),
    ("MPS 令151 公安机关互联网安全监督检查规定", "公安部", 151, None),
    ("NDRC+MOFCOM 令2024年第23号 负面清单", "发展和改革|发展改革", 23, 2024),
    ("NDRC+MOFCOM 令2021年第48号 自贸区负面清单", "发展和改革|发展改革", 48, 2021),
    ("NDRC+MOFCOM 令2025年第37号 鼓励目录", "发展和改革|发展改革", 37, 2025),
    ("NDRC+MOFCOM 令2020年第37号 安全审查办法", "发展和改革|发展改革", 37, 2020),
    ("NDRC 令16 必须招标的工程项目规定", "发展和改革|发展改革", 16, None),
    ("PBOC 令〔2025〕第2号 银行卡清算机构管理办法", "人民银行", 2, 2025),
    ("PBOC 令〔2024〕第4号 非银行支付实施细则", "人民银行", 4, 2024),
    ("PBOC 令〔2021〕第4号 征信业务管理办法", "人民银行", 4, 2021),
    ("MOFCOM 令2014年第1号 机电产品国际招标", "商务部", 1, 2014),
    ("CAC 令11 数据出境安全评估办法", "互联网信息", 11, None),
    ("CAC 令16 促进和规范数据跨境流动规定", "互联网信息", 16, None),
    ("SAMR 令72 互联网广告管理办法", "市场监督管理", 72, None),
    ("OSCCA 令3 商用密码应用安全性评估管理办法", "密码管理", 3, None),
]


def gazette_recall(entries: list[dict]) -> list[tuple[str, str]]:
    out = []
    for label, pat, num, yr in GAZETTE_RECALL:
        hit = next((e for e in entries if e["kind"] == "order" and re.search(pat, e["issuer"])
                    and e["order_num"] == num and (yr is None or e["order_year"] == yr)), None)
        out.append((label, f"{hit['year']}{hit['issue']}  {hit['url']}" if hit else ""))
    return out


def verified_links(folder: str) -> list[dict]:
    """Every link in CN_layer2_links.md that sits on a host assigned to this folder.

    **Every link in a row, not only the first.** A row sometimes bundles separate documents — OSCCA's
    认证目录 is three batches, 禁止出口限制出口技术目录 2025 is a delta on its 2023 base text, the tariff plan
    has a companion 税则 — and taking the first link alone silently dropped the rest (found 2026-09-21).
    A link that is only a mirror of another is fetched too: it costs one request and is a cross-check.
    Links on manual hosts are skipped here, and polite.py refuses them anyway.
    """
    md = open(LINKS_MD, encoding="utf-8").read().split("## What is not there")[0]
    out, seen = [], set()
    for line in md.splitlines():
        if not line.startswith("| ") or line.startswith(("| :", "| Document")):
            continue
        urls = re.findall(r"\((https?://[^)\s]+)\)", line)
        if not urls:
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        title = re.sub(r"\*\*|`", "", cells[0]).strip()
        ref = re.sub(r"\*\*|`", "", cells[1]).strip() if len(cells) > 1 else ""
        for k, u in enumerate(urls):
            if AUTO_HOSTS.get(host_of(u)) != folder or u in seen:
                continue
            seen.add(u)
            out.append({"title": title if k == 0 else f"{title} [link {k + 1}]", "reference": ref,
                        "url": u, "date": "", "section": "verified link",
                        "via": "CN_layer2_links.md" if k == 0 else "CN_layer2_links.md (further link in row)"})
    return out


# ---- fetching ------------------------------------------------------------------------------

def fetch_all(client: PoliteClient, folder: str, items: list[dict], limit: int | None, dest: str | None = None) -> dict:
    """`dest` sends the documents somewhere other than the source's own folder — the update check uses it so a
    delta lands in its own dated folder and the baseline is never written into (CONVENTIONS rule 4)."""
    d = dest or folder_dir(folder)
    for sub in ("raw", "text"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)

    done, refused, failed = [], [], []
    todo = items[:limit] if limit else items
    for i, it in enumerate(todo, 1):
        stem = stem_for(it["title"], it["url"])
        page_p = os.path.join(d, "raw", stem + ".html")
        flag = "not an instrument?" if NOT_INSTRUMENT.search(it["title"]) else ""

        if os.path.exists(page_p) and os.path.getsize(page_p) > 1024:
            html, status, fetched = open(page_p, encoding="utf-8", errors="replace").read(), 200, "(resumed)"
        else:
            try:
                r = client.get(it["url"])
            except HostRefused as e:
                refused.append({**it, "reason": str(e)})
                print(f"  {i:4d}/{len(todo)}  REFUSED  {e}", flush=True)
                continue
            if not r.ok:
                failed.append({**it, "status": r.status})
                print(f"  {i:4d}/{len(todo)}  HTTP {r.status:<4} {it['title'][:44]}", flush=True)
                continue
            html, status = r.text(), r.status
            open(page_p, "w", encoding="utf-8").write(html)
            fetched = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        text = body_text(html)
        open(os.path.join(d, "text", stem + ".txt"), "w", encoding="utf-8").write(text)

        attached = []
        for href in dict.fromkeys(ATTACH.findall(html)):
            a = absolute(it["url"], href)
            fn = re.sub(r"[^\w.\-一-鿿]+", "_", a.rsplit("/", 1)[-1])[:70]
            dest = os.path.join(d, "raw", f"{stem}__{fn}")
            if os.path.exists(dest):
                attached.append(fn)
                continue
            try:
                ar = client.get(a)
            except HostRefused:
                continue
            if ar.ok and len(ar.body) > 512:
                open(dest, "wb").write(ar.body)
                attached.append(fn)

        docno = re.search(r"(第\s*\d+\s*号|〔\d{4}〕\s*第?\s*\d+\s*号|\d{4}年第\d+号)", text[:600])
        eff = re.search(r"自\s*(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日)\s*起\s*(?:施行|实施)", text[:3000])
        done.append({
            "n": len(done) + 1, "title": it["title"], "reference": it.get("reference", ""),
            "section": it["section"], "listed_date": it["date"],
            "doc_number": re.sub(r"\s", "", docno.group(1)) if docno else "",
            "in_force_from": re.sub(r"\s", "", eff.group(1)) if eff else "",
            "chars": len(text), "has_articles": "第一条" in text, "attachments": " | ".join(attached),
            "flag": flag, "url": it["url"], "file": stem, "fetched": fetched, "via": it["via"],
        })
        mark = f"  +{len(attached)} file" if attached else ""
        print(f"  {i:4d}/{len(todo)}  {status}  {len(text):>6}c  {it['title'][:44]}{mark}{'  ['+flag+']' if flag else ''}", flush=True)

    # provenance + manifest
    with open(os.path.join(d, "provenance.tsv"), "w", encoding="utf-8-sig", newline="") as f:
        if done:
            w = csv.DictWriter(f, fieldnames=list(done[0].keys()), delimiter="\t")
            w.writeheader()
            w.writerows(done)
    robots = [{"host": k, "verdict": h.verdict} for k, h in client.hosts.items()]
    json.dump({"folder": folder, "documents": done, "refused": refused, "failed": failed, "robots": robots},
              open(os.path.join(d, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(d, "run_log.jsonl"), "a", encoding="utf-8") as f:
        for ev in client.log:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    client.log.clear()
    return {"fetched": len(done), "refused": len(refused), "failed": len(failed)}


def write_list(folder: str, items: list[dict]) -> None:
    d = folder_dir(folder)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "list.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["title", "reference", "date", "section", "via", "url"], extrasaction="ignore")
        w.writeheader()
        w.writerows(items)


def merged(*lists: list[dict]) -> list[dict]:
    seen, out = set(), []
    for lst in lists:
        for it in lst:
            if it["url"] not in seen:
                seen.add(it["url"])
                out.append(it)
    return out


# ---- the watch list: what this tool cannot see -----------------------------------------------
#
# The developer's rule of 2026-09-21: sources the tool cannot collect automatically — hosts that refuse us,
# announcement streams we do not take whole, publishers created after the source list was written — are
# not silently left out. Every run says so, at the start and at the end, and writes the list beside its
# output. A run of this tool is not a complete update until those sources have been checked by hand.

#: beside this module. In the development workshop it sat one level up, in
#: countries/cn-china/; here the tools and the list travel together.
WATCHLIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watchlist.tsv")
CHECK_FILE = os.path.join(os.path.dirname(OUT), "CHECK_BY_HAND.md")


def _read_watchlist() -> tuple[list[str], list[dict]]:
    if not os.path.exists(WATCHLIST):
        return [], []
    with open(WATCHLIST, encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t", restval="")
        # an empty trailing column can arrive as None; every field is text from here on
        return list(r.fieldnames or []), [{k: (v or "") for k, v in row.items() if k} for row in r]


def _age(row: dict) -> int | None:
    try:
        return (datetime.now().date() - datetime.strptime((row.get("last_checked") or "").strip(), "%Y-%m-%d").date()).days
    except ValueError:
        return None


def watchlist_reminder(when: str) -> None:
    fields, rows = _read_watchlist()
    if not rows:
        print(f"\n!! WATCH LIST MISSING: {WATCHLIST}\n!! This run cannot say what it leaves out.\n", flush=True)
        return
    rows.sort(key=lambda r: (-1 if _age(r) is None else -_age(r)))
    never = sum(1 for r in rows if _age(r) is None)
    stale = sum(1 for r in rows if (_age(r) or 0) > 90)
    bar = "=" * 78
    print(f"\n{bar}\n CHECK BY HAND — {len(rows)} sources this tool does not collect automatically ({when})")
    print(" A run of this tool is NOT a complete update until these have been checked.")
    print(f" {never} never checked, {stale} not checked in 90+ days.  Record a check with:  --checked <name>\n{bar}")
    for r in rows:
        a = _age(r)
        age = "never checked" if a is None else f"{a} days ago"
        print(f" {age:<14} {r['kind']:<13} {r['name'][:34]:<36} {r['url']}")
    print(bar + "\n", flush=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Check by hand",
        "",
        f"**Written by `countries/cn-china/tools/collect.py` at {now}.** Rewritten on every run.",
        "",
        f"**{len(rows)} sources are not collected automatically.** A run of the tool is not a complete update",
        "until each has been checked. After checking one, record it:",
        "",
        "```",
        'python countries/cn-china/tools/collect.py --checked "国家数据局"',
        "```",
        "",
        "| Last checked | Kind | Source | What to look for | Expect |",
        "| :---- | :---- | :---- | :---- | :---- |",
    ]
    for r in rows:
        a = _age(r)
        age = "**never**" if a is None else f"{r['last_checked']} ({a} d)"
        lines.append(f"| {age} | {r['kind']} | [{r['name']}]({r['url']}) | {r['what_to_look_for']} | {r['expect']} |")
    lines += [
        "",
        "**Kinds.** `manual-host`: the host refuses us or forbids us. `stream`: an announcement stream the tool",
        "takes only verified links from. `new-publisher`: a body not in the source list. `canary`: a cross-ministry",
        "index where a rule from an unfamiliar issuer is the sign the list itself is out of date.",
        "",
        f"The list lives in `countries/cn-china/watchlist.tsv`. Add a row when a new publisher is found.",
    ]
    os.makedirs(os.path.dirname(CHECK_FILE), exist_ok=True)
    open(CHECK_FILE, "w", encoding="utf-8").write("\n".join(lines) + "\n")


def mark_checked(needle: str) -> None:
    fields, rows = _read_watchlist()
    hit = [r for r in rows if needle in r["name"] or needle in r["url"]]
    if not hit:
        print(f"No watch-list row matches {needle!r}.")
        return
    today = datetime.now().strftime("%Y-%m-%d")
    for r in hit:
        r["last_checked"] = today
        print(f"  checked {today}  {r['name']}")
    with open(WATCHLIST, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


# ---- entry point ---------------------------------------------------------------------------

def run(source: str, list_only: bool, limit: int | None) -> dict:
    client = PoliteClient()
    plan = []
    if source == "cac":
        plan = [("cac", merged(discover_cac(client), verified_links("cac")))]
    elif source in ("samr", "mofcom"):
        plan = [(source, merged(discover_jpaas(client, source), verified_links(source)))]
    elif source == "oscca":
        plan = [("oscca", merged(discover_oscca(client), verified_links("oscca")))]
    elif source == "links":
        plan = [(f, verified_links(f)) for f in ("cnca", "mof-tariff", "sectoral", "govcn")]
    elif source == "gazette":
        entries, failed = discover_gazette(client)
        d = folder_dir("gazette")
        os.makedirs(d, exist_ok=True)
        if entries:
            with open(os.path.join(d, "index.csv"), "w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(entries[0].keys()))
                w.writeheader()
                w.writerows(entries)
        recall = gazette_recall(entries)
        found = sum(1 for _, where in recall if where)
        lines = [f"# Gazette recall check, {datetime.now().strftime('%Y-%m-%d %H:%M')}", "",
                 f"Rules we already hold by hand, looked for in the gazette index: **{found} of {len(recall)} found.**",
                 f"Index: {len(entries)} entries, {sum(1 for e in entries if e['kind'] == 'order')} orders, "
                 f"{sum(1 for e in entries if e['relevant'])} flagged relevant; {len(failed)} issues failed.", "",
                 "| Rule | Found in |", "| :---- | :---- |"]
        lines += [f"| {label} | {where or '**not found**'} |" for label, where in recall]
        open(os.path.join(d, "recall.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
        print(f"\n   RECALL: {found} of {len(recall)} hand-held rules found in the gazette index", flush=True)
        for label, where in recall:
            print(f"     {'ok ' if where else 'MISS'} {label}", flush=True)
        items = [{"title": e["title"] or e["raw"], "url": e["url"], "date": e["year"], "via": "gazette",
                  "section": f"{e['issuer']} {e['kind']}".strip(),
                  "reference": f"{e['issuer']}令（{e['order_no']}）" if e["order_no"] else ""}
                 for e in entries if e["relevant"]]
        plan = [("gazette", items)]

    result = {}
    for folder, items in plan:
        write_list(folder, items)
        print(f"\n[{folder}] {len(items)} documents listed", flush=True)
        if list_only:
            result[folder] = {"listed": len(items)}
            continue
        result[folder] = {"listed": len(items), **fetch_all(client, folder, items, limit)}
    for k, h in client.hosts.items():
        print(f"   robots  {k:<40} {h.verdict}")
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("source", nargs="?", choices=["cac", "samr", "mofcom", "oscca", "links", "gazette", "all"])
    ap.add_argument("--list-only", action="store_true", help="discover and write list.csv; fetch nothing")
    ap.add_argument("--limit", type=int, default=None, help="fetch at most N documents per folder")
    ap.add_argument("--watchlist", action="store_true", help="print the sources to check by hand, and stop")
    ap.add_argument("--checked", metavar="NAME", help="record that a watch-list source was checked today")
    a = ap.parse_args()

    if a.checked:
        mark_checked(a.checked)
        return
    if a.watchlist:
        watchlist_reminder("on request")
        return
    if not a.source:
        ap.error("give a source, or --watchlist, or --checked NAME")

    # said before the run as well as after it, so an interrupted run still delivered the reminder
    watchlist_reminder("before this run")
    started = time.time()
    sources = ["samr", "mofcom", "oscca", "links", "gazette", "cac"] if a.source == "all" else [a.source]
    summary = {}
    for s in sources:
        print(f"\n===== {s} =====", flush=True)
        summary.update(run(s, a.list_only, a.limit))
    print(f"\n===== summary ({(time.time() - started) / 60:.1f} min) =====")
    for folder, r in summary.items():
        print(f"  {folder:<12} " + "  ".join(f"{k} {v}" for k, v in r.items()))
    watchlist_reminder("after this run")


if __name__ == "__main__":
    main()
