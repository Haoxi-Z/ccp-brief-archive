#!/usr/bin/env python3
"""Turn the CCP daily brief data in index.html into Obsidian news cards.

Reads the JSON between /*DATA-START*/ and /*DATA-END*/ in index.html and writes
one Markdown card per item to cards/<id>.md, plus cards/index.txt
(one "id<TAB>filename" line per card) for the Mac sync script.
Existing cards are rewritten from the data each run, so the output always
matches index.html. Your own edits happen in the vault copy, never here.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "index.html"
OUT = ROOT / "cards"

SECTION = {"reg": "监管", "fmi": "同业", "assoc": "行业"}

# Brief topic labels -> vault topic notes (10-Work/14-专题)
TOPIC = {
    "第三国认可/等效": ["第三国CCP认可"],
    "EMIR 3.0": ["EMIR 3.0"],
    "美债清算": ["美国国债集中清算"],
    "保证金/压力测试": ["保证金透明度", "CCP韧性与压力测试"],
    "恢复与处置": ["CCP恢复与处置"],
}

# Institution -> jurisdiction (matches the vault's jurisdiction values)
JUR = {
    "欧盟": ["ESMA", "ECB", "欧央行", "欧洲央行", "EC", "欧盟委员会", "EBA", "EIOPA",
           "Eurex", "Eurex Clearing", "Nasdaq Clearing", "EACH", "AFME", "Euroclear", "Clearstream"],
    "英国": ["BoE", "BOE", "英格兰银行", "FCA", "HMT", "HM Treasury", "PRA", "LCH", "ICE Clear Europe", "LME Clear"],
    "美国": ["CFTC", "SEC", "Fed", "美联储", "Federal Reserve", "OCC", "DTCC", "FICC", "NSCC",
           "CME", "CME Clearing", "ICE Clear Credit", "ICE Clear US", "SIFMA", "Treasury", "美国财政部"],
    "日本": ["JSCC", "JFSA", "日本金融厅", "BOJ", "日本央行"],
    "中国香港": ["HKMA", "香港金管局", "SFC", "香港证监会", "HKEX", "港交所", "OTC Clear", "场外结算公司"],
    "新加坡": ["MAS", "SGX"],
    "澳大利亚": ["ASX", "ASIC", "RBA"],
    "韩国": ["KRX"],
    "中国": ["上海清算所", "中国人民银行", "人民银行", "证监会", "中国证监会", "金融监管总局",
           "中央结算", "中央国债登记结算", "中国结算", "外汇交易中心"],
    "国际": ["CPMI", "IOSCO", "CPMI-IOSCO", "FSB", "BIS", "ISDA", "FIA", "CCP12", "WFE", "ICMA", "IMF"],
}
ORG2JUR = {org.lower(): j for j, orgs in JUR.items() for org in orgs}


def yq(s):
    """Quote a scalar for YAML."""
    return json.dumps(str(s), ensure_ascii=False)


def safe_name(s, limit=70):
    s = re.sub(r'[\\/:*?"<>|#^\[\]\n\r\t]', " ", s)
    s = re.sub(r"\s+", " ", s).strip(" .")
    return s[:limit].rstrip(" .")


def card(brief, it):
    org = (it.get("org") or "").strip()
    pub = it.get("pubDate") or brief["date"]
    title = (it.get("title") or "").strip()
    labels = it.get("topics") or []
    topics = []
    for lab in labels:
        for t in TOPIC.get(lab, []):
            if t not in topics:
                topics.append(t)
    jur = ORG2JUR.get(org.lower())
    tags = ["CCP日报"] + [re.sub(r"[\s/]+", "-", lab) for lab in labels]

    fm = [
        "---",
        f"title: {yq(title)}",
        f"source: {yq(it.get('url', ''))}",
        f"published: {pub}",
        f"created: {brief['date']}",
        f"institution: {yq(org)}" if org else "institution:",
        "jurisdiction:" + (f"\n  - {jur}" if jur else " []"),
        "type:",
        f"section: {SECTION.get(it.get('group'), '')}",
        "topic:" + ("".join(f'\n  - "[[{t}]]"' for t in topics) if topics else " []"),
        "status: 原始",
        "weekly:",
        "follow_up:",
        "tags:" + "".join(f"\n  - {yq(t)}" for t in tags),
        "---",
    ]
    body = [
        f"# {title}",
        "",
        "## 一句话",
        "",
        "",
        "## 要点（日报自动生成）",
        (it.get("summary") or "").strip(),
        "",
    ]
    if (it.get("focus") or "").strip():
        body += ["## 关注点", it["focus"].strip(), ""]
    body += [
        "## 我的理解",
        "",
        "",
        "## 原文",
        f"- {org}，{pub}：{it.get('url', '')}",
        "",
    ]
    return "\n".join(fm) + "\n" + "\n".join(body)


def main():
    html = SRC.read_text(encoding="utf-8")
    m = re.search(r"/\*DATA-START\*/(.*?)/\*DATA-END\*/", html, re.S)
    if not m:
        sys.exit("DATA block not found in index.html")
    briefs = json.loads(m.group(1).replace("<\\/", "</"))

    OUT.mkdir(exist_ok=True)
    index, used = [], set()
    for brief in sorted(briefs, key=lambda b: b["date"]):
        for it in brief.get("items") or []:
            key = it.get("url") or (brief["date"] + it.get("title", ""))
            cid = hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
            if cid in {i for i, _ in index}:
                continue  # same item repeated on a later day: keep the first
            pub = it.get("pubDate") or brief["date"]
            org, title = (it.get("org") or "").strip(), (it.get("title") or "").strip()
            label = title if title.startswith(org) else f"{org} {title}"
            base = safe_name(f"{pub} {label}")
            name, n = base, 2
            while name in used:
                name, n = f"{base} ({n})", n + 1
            used.add(name)
            (OUT / f"{cid}.md").write_text(card(brief, it), encoding="utf-8")
            index.append((cid, name + ".md"))

    keep = {f"{cid}.md" for cid, _ in index}
    for f in OUT.glob("*.md"):
        if f.name not in keep:
            f.unlink()
    (OUT / "index.txt").write_text(
        "".join(f"{cid}\t{name}\n" for cid, name in index), encoding="utf-8")
    print(f"{len(index)} cards")


if __name__ == "__main__":
    main()
