"""Brief (contracts/presentation-brief.schema.json) -> deck plan (contracts/deck-plan.schema.json).

Deterministic and fact-preserving: every slide text comes from the brief (topic, purpose, content
titles/facts) or from fixed localized UI labels. Missing evidence becomes an explicit
"pending input" item; the planner never invents numbers, customers, specs or outcomes.
Slide ids are content-keyed (not positional) so a revised brief keeps earlier layout choices."""
import hashlib, json, re
from dataclasses import dataclass, field
from pathlib import Path
from . import brand as B

UI = {
    "zh-TW": {"agenda": "簡報大綱", "agenda_k": "AGENDA · 大綱", "purpose": "簡報目的", "purpose_k": "PURPOSE · 目的",
              "summary": "重點回顧", "summary_k": "SUMMARY · 回顧", "next": "待確認事項與下一步", "next_k": "NEXT STEPS · 待補資料",
              "pending": "PENDING INPUT · 待補資料", "pending_cell": "待補", "deep_k": "DETAIL · 待補內容",
              "deep_body": "本頁內容需以提供的資料補充", "closing": "Turn Every Drill into Real",
              "company": "全球動力科技股份有限公司 · bigxreality.com", "audience": {"internal": "內部簡報", "external": "對外簡報",
              "government": "政府簡報", "partners": "合作夥伴簡報", "mixed": "簡報"}, "for": "對象", "step": "STEP"},
    "en": {"agenda": "Agenda", "agenda_k": "AGENDA", "purpose": "Purpose of this briefing", "purpose_k": "PURPOSE",
           "summary": "Key takeaways", "summary_k": "SUMMARY", "next": "Open items and next steps", "next_k": "NEXT STEPS · OPEN ITEMS",
           "pending": "PENDING INPUT", "pending_cell": "TBD", "deep_k": "DETAIL · CONTENT PENDING",
           "deep_body": "Content for this page must be supplied from verified material", "closing": "Turn Every Drill into Real",
           "company": "Big x Reality · bigxreality.com", "audience": {"internal": "Internal briefing", "external": "External briefing",
           "government": "Government briefing", "partners": "Partner briefing", "mixed": "Briefing"}, "for": "Audience", "step": "STEP"},
    "JP": {"agenda": "アジェンダ", "agenda_k": "AGENDA", "purpose": "本資料の目的", "purpose_k": "PURPOSE",
           "summary": "まとめ", "summary_k": "SUMMARY", "next": "確認事項と次のステップ", "next_k": "NEXT STEPS · 要確認",
           "pending": "PENDING INPUT · 要確認", "pending_cell": "要確認", "deep_k": "DETAIL · 内容要確認",
           "deep_body": "このページの内容は提供資料に基づき追記してください", "closing": "Turn Every Drill into Real",
           "company": "Big x Reality · bigxreality.com", "audience": {"internal": "社内説明", "external": "社外説明",
           "government": "官公庁向け説明", "partners": "パートナー向け説明", "mixed": "ご説明"}, "for": "対象", "step": "STEP"},
}

PROCESS_RE = re.compile(r"流程|步驟|程序|路徑|導入方式|workflow|process|steps|implementation|path|roadmap|手順|プロセス|フロー|導入", re.I)
COMPARE_RE = re.compile(r"比較|對照|選型|comparison|versus|\bvs\b|比較検討", re.I)
PENDING_RE = re.compile(r"為準|依專案評估|尚待|待填|TBD|to be confirmed|要確認|未定", re.I)
RULE_RE = re.compile(r"不編造|不得|不預設|不可|勿|rather than|do not|don't|avoid|しない|禁止", re.I)
NUM_FACT_RE = re.compile(r"^(?P<label>[^:：]{1,40})[:：]\s*(?P<val>-?\d+(?:\.\d+)?)\s*(?P<unit>[%A-Za-z一-鿿]*)\s*$")
OPTION_RE = re.compile(r"^(?P<name>[^:：]{1,24})[:：]\s*(?P<rest>.+)$")

ICON_KEYS = [("Police", r"police|警|警察"), ("Fire_Disaster", r"fire|消防|救災|救援|rescue|消防"),
             ("Military", r"defen[cs]e|army|military|國防|軍|陸軍|防衛"), ("UAV", r"uav|drone|無人機|ドローン"),
             ("XR", r"\bxr\b|\bvr\b|\bmr\b|虛擬|設備|headset|装置|機材"), ("Analytics", r"analytic|數據|成效|評估|成本|cost|data|評価|コスト"),
             ("Sensor_Radar", r"risk|風險|sensor|雷達|リスク"), ("Command", r"command|指揮|維護|maintain|運用|管理"),
             ("Communication", r"communicat|通訊|溝通|連絡"), ("AI", r"\bai\b|人工智慧"),
             ("Training", r"train|訓練|演練|演習|研修"), ("Simulation", r"simulat|模擬|情境|scenario|シナリオ")]


def pick_icon(text, used=()):
    for name, pat in ICON_KEYS:
        if re.search(pat, text, re.I) and name not in used:
            return name
    for name in ("Simulation", "Training", "Analytics", "Command"):
        if name not in used:
            return name
    return "Simulation"


def _short(s):
    cjk = sum(1 for c in s if ord(c) > 0x2E80)
    return (cjk and len(s) <= 10) or (not cjk and len(s.split()) <= 4)


@dataclass
class Slide:
    slide_id: str
    role: str
    layout: str                       # master layout name
    kind: str                         # composition used by builder
    title: str
    message: str
    content_refs: list
    editable: list
    evidence: str = "provided"
    kicker: str = ""
    data: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)


def classify(group):
    facts = group["facts"]
    title = group["title"]
    nums = [NUM_FACT_RE.match(f) for f in facts]
    if len(facts) >= 2 and all(nums):
        return "data"
    if COMPARE_RE.search(title) or (len(facts) >= 2 and sum(bool(OPTION_RE.match(f)) for f in facts) == len(facts) and len(facts) <= 4):
        return "comparison"
    if PROCESS_RE.search(title) and 3 <= len(facts) <= 6:
        return "process"
    if 2 <= len(facts) <= 4 and all(_short(f) for f in facts):
        return "cards"
    return "content"


# ---- content triggers for the aviation families (bxr_deck/layouts_aviation.py) -------------------
# Each rule needs the facts themselves to carry the structure (every fact must match), so ordinary
# groups keep their existing family. Output follows the shared render contract:
# (family, items:list, extra:dict). Nothing is inferred beyond what the facts say.
AV_ROLE = {"compare": "comparison", "timeline": "timeline", "map": "map", "team": "people",
           "product": "product", "gauge": "data", "quote": "content"}
YEAR_RE = re.compile(r"^\s*(?P<year>(?:19|20)\d{2}(?:\s*年)?|民國\s*\d{2,3}\s*年|1[0-2]\d\s*年)\s*[:：\-–—、]?\s*(?P<rest>.+)$")
CMP_TITLE_RE = re.compile(r"\bvs\.?(?=\s|$)|\bversus\b|對比|比較|相較|対比", re.I)
CMP_SPLIT_RE = re.compile(r"\s*(?:\bvs\.?(?=\s|$)|\bversus\b|對比|相較於|相較|與|和|及|と)\s*", re.I)
CMP_TAIL_RE = re.compile(r"(?:の|之)?(?:比較|對比|対比|comparison)\s*$", re.I)
VAL_SPLIT_RE = re.compile(r"\s*[｜|／]\s*|\s+vs\.?\s+", re.I)
GAUGE_RE = re.compile(r"^(?P<label>[^:：]{1,40})[:：]\s*(?P<val>\d+(?:\.\d+)?)\s*(?P<u1>[%A-Za-z一-鿿°]*)\s*"
                      r"(?:/|／|of|，?\s*上限|，?\s*max\.?|，?\s*満点)\s*(?P<max>\d+(?:\.\d+)?)\s*(?P<u2>[%A-Za-z一-鿿°]*)\s*$", re.I)
QUOTE_RE = re.compile(r"^\s*[「『“\"](?P<q>.+?)[」』”\"]\s*(?:[—–\-]{1,2}\s*(?P<who>.+))?$")
VISION_RE = re.compile(r"宣言|使命|願景|理念|\bmission\b|\bvision\b|manifesto|ミッション|ビジョン", re.I)
PRODUCT_RE = re.compile(r"^(?P<name>.+?)\s*(?:的|之|の)?\s*(?:產品特點|產品特色|功能特點|特點|特色|主要功能|key features|features|特長|特徴)\s*$", re.I)
ROLE_WORDS = re.compile(r"經理|主管|工程師|教官|指揮官|負責人|窗口|顧問|講師|技術支援|專員|組長|隊長|總監|執行長|"
                        r"\bPM\b|manager|engineer|\blead\b|instructor|director|officer|coordinator|specialist|"
                        r"担当|責任者|エンジニア|マネージャー|リーダー|講師", re.I)
REGIONS = ("台灣 臺灣 台湾 日本 美國 美国 米国 アメリカ 韓國 韓国 新加坡 シンガポール 越南 泰國 菲律賓 印尼 馬來西亞 印度 澳洲 "
           "德國 法國 英國 加拿大 中東 歐洲 欧州 亞洲 アジア 東南亞 東南アジア 東北亞 北美 北米 "
           "台北市 臺北市 新北市 桃園市 台中市 臺中市 台南市 臺南市 高雄市 基隆市 新竹市 新竹縣 苗栗縣 彰化縣 南投縣 雲林縣 "
           "嘉義市 嘉義縣 屏東縣 宜蘭縣 花蓮縣 台東縣 臺東縣 澎湖縣 金門縣 連江縣 北部 中部 南部 東部 離島 "
           "Taiwan Japan USA Korea Singapore Vietnam Thailand Philippines Indonesia Malaysia India Australia "
           "Germany France Canada Europe Asia").split() + ["United States", "United Kingdom", "Middle East",
                                                          "Southeast Asia", "North America"]
REGION_RE = re.compile(r"^(?:" + "|".join(map(re.escape, sorted(REGIONS, key=len, reverse=True))) +
                       r")(?:\s*(?:地區|地区|區域|一帶|市場|据点|據點|region|market))?$", re.I)


def _title_body(f):
    m = OPTION_RE.match(f)
    return (m["name"].strip(), m["rest"].strip()) if m else (f.strip(), None)


def aviation_family(title, facts):
    """Return (family, items, extra) when the facts carry one of the seven structures, else None."""
    n = len(facts)
    if not n:
        return None
    g = [GAUGE_RE.match(f) for f in facts]
    if n <= 4 and all(g):
        items = [{"label": m["label"].strip(), "value": float(m["val"]), "max": float(m["max"]),
                  "unit": (m["u1"] or m["u2"]).strip()} for m in g]
        if all(it["unit"] and 0 < it["max"] and it["value"] <= it["max"] for it in items):
            return "gauge", items, {"notes": []}
    y = [YEAR_RE.match(f) for f in facts]
    if 3 <= n <= 8 and all(y):
        items = []
        for m in y:
            t, b = _title_body(m["rest"])
            items.append({"year": re.sub(r"\s+", "", m["year"]), "title": t, "body": b})
        return "timeline", items, {}
    if CMP_TITLE_RE.search(title):
        cols = [p.strip() for p in CMP_SPLIT_RE.split(CMP_TAIL_RE.sub("", title).strip()) if p.strip()]
        rows = [OPTION_RE.match(f) for f in facts]
        if 2 <= len(cols) and 2 <= n <= 8 and all(rows):
            items = [{"label": m["name"].strip(), "values": VAL_SPLIT_RE.split(m["rest"].strip())} for m in rows]
            if all(len(it["values"]) == len(cols) for it in items):
                return "compare", items, {"columns": cols}
    q = [QUOTE_RE.match(f) for f in facts]
    if n <= 2 and (all(q) or VISION_RE.search(title)):
        who = next((m["who"].strip() for m in q if m and m["who"]), None)
        return "quote", [m["q"].strip() if m else f.strip() for m, f in zip(q, facts)], {"attribution": who}
    p = PRODUCT_RE.match(title)
    if p and 2 <= n <= 6:
        return "product", [dict(zip(("title", "body"), _title_body(f))) for f in facts], {"name": p["name"].strip()}
    tb = [_title_body(f) for f in facts]
    if 2 <= n <= 6 and all(len(t) <= 16 and ROLE_WORDS.search(t) for t, _ in tb):
        # names are never inferred: only the role is shown unless the brief states a name
        return "team", [{"role": t, "name": None, "body": b} for t, b in tb], {}
    if n <= 6 and all(REGION_RE.match(t) for t, _ in tb):
        return "map", [{"name": t, "body": b} for t, b in tb], {}
    return None


def split_facts(facts):
    """-> (presentable, pending, rules). Pending: 'needs data' statements; rules: presenter rules."""
    show, pend, rules = [], [], []
    for i, f in enumerate(facts):
        if RULE_RE.search(f): rules.append((i, f))
        elif PENDING_RE.search(f): pend.append((i, f))
        else: show.append((i, f))
    return show, pend, rules


LAYOUT_BG = {"BXR Cover": "cover", "BXR Closing": "cover", "BXR Section": "section"}


def plan(brief, previous=None):
    lang = brief["language"]; T = UI[lang]
    groups = brief["content"]; target = brief["slides"]
    slides, warnings, unverified = [], [], []
    acc = B.sector_accent(brief.get("sector"))

    def add(s): slides.append(s); return s

    # ---- core slides --------------------------------------------------------
    meta = f"{T['audience'].get(brief['audience'], '')}"
    cover = Slide("cover", "cover", "BXR Cover", "cover", brief["topic"], brief["topic"], ["brief.topic", "brief.purpose"],
                  ["title", "subtitle", "body"], data={"subtitle": brief["purpose"], "meta": meta})
    agenda = Slide("agenda", "agenda", "BXR Title Only", "agenda", T["agenda"], " / ".join(g["title"] for g in groups),
                   [f"content[{i}].title" for i in range(len(groups))], ["title", "body"], kicker=T["agenda_k"],
                   data={"items": [g["title"] for g in groups]})
    purpose = Slide("purpose", "content", "BXR Title Only", "statement", T["purpose"], brief["purpose"], ["brief.purpose", "brief.audience"],
                    ["title", "body"], kicker=T["purpose_k"],
                    data={"text": brief["purpose"], "sub": f"{T['for']}：{meta}" if lang != "en" else f"{T['for']}: {meta}"})

    body = []   # (section_slide, [content slides]) per group
    pending_all, deep_candidates = [], []
    for gi, g in enumerate(groups):
        show, pend, rules = split_facts(g["facts"])
        kind = classify({"title": g["title"], "facts": [f for _, f in show]}) if show else "content"
        if COMPARE_RE.search(g["title"]) and len(g["facts"]) >= 2 and all(OPTION_RE.match(f) for f in g["facts"]):
            kind = "comparison"; show, pend = [(i, f) for i, f in enumerate(g["facts"])], []
        refs = [f"content[{gi}].facts[{i}]" for i, _ in show]
        sec = Slide(f"section-c{gi}", "section", "BXR Section", "section", g["title"], g["title"], [f"content[{gi}].title"],
                    ["title", "body"], data={"number": f"{gi + 1:02d}", "label": ""})
        kicker = f"{gi + 1:02d} · {g['title']}"
        note = [f"Source: brief content[{gi}] “{g['title']}”" + (f"; refs: {', '.join(g.get('source_refs', []))}" if g.get("source_refs") else "")]
        note += [f"Presenter rule: {f}" for _, f in rules]
        evidence = "provided" if (g.get("source_refs") or brief.get("source_policy") == "provided-only") else "uncited"
        items = [f for _, f in show]
        pend_items = [f for _, f in pend]
        pending_all += [(gi, f) for f in pend_items]
        unverified += [f"content[{gi}]: {f}" for f in pend_items]
        sid = f"{kind}-c{gi}"
        role = {"data": "data", "comparison": "comparison", "process": "process", "cards": "content"}.get(kind, "content")
        av = aviation_family(g["title"], items) if items and not pend_items else None
        if av:
            fam, av_items, extra = av
            s = Slide(f"{fam}-c{gi}", AV_ROLE[fam], "BXR Title Only", "aviation", g["title"], g["title"], refs,
                      ["title", "diagram"], evidence, kicker, data={"family": fam, "items": av_items, "extra": extra})
        elif kind == "data":
            m = [NUM_FACT_RE.match(f) for f in g["facts"]]
            s = Slide(sid, role, "BXR Chart + Text", "chart", g["title"], g["title"], refs, ["title", "chart", "body"], evidence, kicker,
                      data={"categories": [x["label"].strip() for x in m], "values": [float(x["val"]) for x in m],
                            "unit": m[0]["unit"], "notes": [g.get("notes", "")] if g.get("notes") else []})
        elif kind == "comparison":
            opts = [OPTION_RE.match(f) for f in g["facts"]]
            names = [o["name"].strip() if o else f"#{i + 1}" for i, o in enumerate(opts)]
            factors = next((gg["facts"] for gg in groups if gg is not g and classify(gg) == "cards"), None)
            rows = [[fac] + [T["pending_cell"]] * len(names) for fac in (factors or [T["pending_cell"]])]
            s = Slide(sid, role, "BXR Title Only", "table", g["title"], g["title"], [f"content[{gi}].facts[{i}]" for i in range(len(g["facts"]))],
                      ["title", "table"], "provided", kicker,
                      data={"header": [""] + names, "rows": rows, "status": list(g["facts"])})
            unverified += [f"content[{gi}]: comparison values not supplied ({', '.join(names)})"]
        elif kind == "process":
            s = Slide(sid, role, "BXR Title Only", "process", g["title"], " → ".join(items), refs, ["title", "diagram"], evidence, kicker,
                      data={"steps": items, "pending": pend_items})
        elif kind == "cards":
            used = []
            cards = []
            for f in items:
                ic = pick_icon(f + " " + g["title"], used); used.append(ic); cards.append({"title": f, "icon": ic})
            s = Slide(sid, role, "BXR Title Only", "cards", g["title"], " / ".join(items), refs, ["title", "diagram"], evidence, kicker,
                      data={"cards": cards, "pending": pend_items})
            deep_candidates.append((gi, cards))
        elif not items and pend_items:
            hdr = {"zh-TW": ["評估項目", "目前狀態", "資料來源", "負責單位"], "en": ["Item", "Status", "Source", "Owner"],
                   "JP": ["評価項目", "現状", "情報源", "担当"]}[lang]
            s = Slide(f"assessment-c{gi}", "content", "BXR Title Only", "assessment", g["title"], g["title"],
                      [f"content[{gi}].facts[{i}]" for i, _ in pend], ["title", "table"], "uncited", kicker,
                      data={"header": hdr, "rows": [[f] + [T["pending_cell"]] * 3 for f in pend_items],
                            "rules": [f for _, f in rules]})
        else:
            s = Slide(sid, role, "BXR Title + Body" if not pend_items else "BXR Title Only",
                      "bullets" if not pend_items else "bullets_pending", g["title"], items[0] if items else g["title"], refs,
                      ["title", "body"], evidence if items else "uncited", kicker, data={"items": items, "pending": pend_items})
        s.notes = note
        body.append((sec, [s]))

    nxt = Slide("next-steps", "summary", "BXR Title Only", "next", T["next"], T["next"], [f"content[{gi}]" for gi, _ in pending_all] or ["brief"],
                ["title", "body"], "not-applicable", T["next_k"], data={"items": [f for _, f in pending_all]})
    summary = Slide("summary", "summary", "BXR Title Only", "agenda", T["summary"], " / ".join(g["title"] for g in groups),
                    [f"content[{i}].title" for i in range(len(groups))], ["title", "body"], kicker=T["summary_k"],
                    data={"items": [g["title"] for g in groups],
                          "details": [" · ".join(f for _, f in split_facts(g["facts"])[0][:4]) or T["pending_cell"] for g in groups]})
    closing = Slide("closing", "other", "BXR Closing", "closing", T["closing"], T["closing"], ["brand"], ["title", "body"],
                    "not-applicable", data={"text": T["company"]})

    # ---- fit to requested slide count without padding facts ------------------------
    opt = {"agenda": len(groups) >= 2, "purpose": True, "sections": len(groups) >= 2,
           "next": bool(pending_all), "summary": len(groups) >= 2}
    deep = []

    def assemble():
        out = [cover]
        if opt["agenda"]: out.append(agenda)
        if opt["purpose"]: out.append(purpose)
        for gi, (sec, ss) in enumerate(body):
            if opt["sections"]: out.append(sec)
            out += ss
            out += [d for d in deep if d.data["group"] == gi]
        if opt["next"]: out.append(nxt)
        if opt["summary"]: out.append(summary)
        out.append(closing)
        return out

    for key in ("sections", "agenda", "summary", "purpose", "next"):
        if len(assemble()) <= target: break
        opt[key] = False
    if len(assemble()) < target and not opt["next"] and deep_candidates:
        opt["next"] = True
    for gi, cards in deep_candidates:
        for k, c in enumerate(cards):
            if len(assemble()) >= target: break
            d = Slide(f"detail-c{gi}-i{k}", "content", "BXR Title Only", "detail", c["title"], c["title"],
                      [f"content[{gi}].facts[{k}]"], ["title", "body"], "uncited", f"{gi + 1:02d} · {UI[lang]['deep_k']}",
                      data={"group": gi, "icon": c["icon"], "text": UI[lang]["deep_body"]})
            d.notes = [f"Expansion slide for requested length; content pending from verified material ({c['title']})."]
            deep.append(d)
            unverified.append(f"content[{gi}] detail “{c['title']}”: no supporting facts supplied")
    nxt.data["items"] = [f for _, f in pending_all] + [f"{d.title} — {UI[lang]['deep_body']}" for d in deep]
    final = assemble()
    if len(final) != target:
        warnings.append(f"requested {target} slides; produced {len(final)} — brief has no further facts to fill slides without padding")

    # stable section numbering after optional removals
    n = 0
    for s in final:
        if s.kind == "section":
            n += 1; s.data["number"] = f"{n:02d}"
    # keep previous plan layout choices for unchanged ids (rework flow)
    if previous:
        prev = {p["slide_id"]: p for p in previous.get("slides", [])}
        for s in final:
            if s.slide_id in prev and prev[s.slide_id].get("role") == s.role:
                s.data["_kept_from_previous"] = True
                s.data["_prev_variant"] = prev[s.slide_id].get("layout_source", {}).get("variant")
    return final, warnings, unverified


def to_plan_json(brief, slides, unverified, status="ready-for-review", qa=None):
    rel = lambda p: str(Path(p).relative_to(B.REPO))
    out = []
    for s in slides:
        bg = LAYOUT_BG.get(s.layout, "content")
        entry = {"slide_id": s.slide_id, "role": s.role, "message": s.message, "content_refs": s.content_refs,
                 "layout_source": {"kind": "approved-background", "path": rel(B.BG[bg]),
                                   **({"variant": s.data["_variant"]} if s.data.get("_variant") else {})},
                 "editable_elements": sorted(set(s.editable + ["page-number"] * (bg == "content") + ["notes"])),
                 "evidence_status": s.evidence}
        if qa and s.slide_id in qa: entry["qa"] = qa[s.slide_id]
        out.append(entry)
    inv = hashlib.sha256(json.dumps(brief, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {"brief_id": brief["id"], "design_owner": "claude", "quality_status": status, "slides": out,
            "unverified_claims": unverified, "source_inventory_sha256": inv}
