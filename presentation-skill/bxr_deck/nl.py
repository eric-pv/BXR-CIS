"""Natural-language outline -> brief (offline, deterministic; no API key needed).

Accepted text (any of zh-TW / en / JP):
    第一行：主題
    目的：…            (Purpose: … / 目的：…)
    12頁               (12 slides / 12枚)  — optional
    # 章節標題          (or '## …' / '1. …' heading lines)
    - 事實              (bullet facts, copied verbatim)
Language is detected from the script (kana -> JP, CJK -> zh-TW, otherwise en).
An LLM front-end can replace this function as long as it emits the same schema."""
import re

KANA = re.compile(r"[぀-ヿ]")
CJK = re.compile(r"[一-鿿]")


def detect_language(text):
    if KANA.search(text): return "JP"
    if CJK.search(text): return "zh-TW"
    return "en"


def brief_from_text(text, brief_id, audience="internal", slides=None):
    lines = [l.rstrip() for l in text.splitlines() if l.strip()]
    if not lines: raise ValueError("empty outline")
    lang = detect_language(text)
    topic = lines[0].lstrip("# ").strip()
    purpose, content, cur = None, [], None
    for l in lines[1:]:
        s = l.strip()
        m = re.match(r"^(目的|purpose)\s*[:：]\s*(.+)$", s, re.I)
        if m: purpose = m.group(2).strip(); continue
        m = re.match(r"^(\d{1,2})\s*(頁|页|slides?|枚)$", s, re.I)
        if m: slides = slides or int(m.group(1)); continue
        if re.match(r"^(#{1,3}\s+|\d+[.、]\s*)", s):
            cur = {"title": re.sub(r"^(#{1,3}\s+|\d+[.、]\s*)", "", s), "facts": []}; content.append(cur); continue
        if re.match(r"^[-*•・]\s*", s):
            if cur is None: cur = {"title": topic, "facts": []}; content.append(cur)
            cur["facts"].append(re.sub(r"^[-*•・]\s*", "", s)); continue
        if cur is None: cur = {"title": topic, "facts": []}; content.append(cur)
        cur["facts"].append(s)
    return {"id": brief_id, "topic": topic, "language": lang, "audience": audience,
            "purpose": purpose or topic, "slides": max(3, min(60, slides or 10)),
            "series": "military-tech", "source_policy": "provided-only", "content": content or [{"title": topic, "facts": []}],
            "output": {"pptx": True, "pdf": False}}
