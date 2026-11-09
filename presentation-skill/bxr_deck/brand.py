"""Brand constants resolved from the repository (CIS v3.2). Never hard-code assets elsewhere."""
import json
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]          # presentation-skill/
REPO = SKILL.parent
COLORS_JSON = REPO / "02_Color" / "BXR_Colors_v3.2.json"
LOGO = REPO / "01_Logo" / "PNG"
ICONS = REPO / "04_Graphics" / "Icons"
BACKGROUNDS = SKILL / "approved-layouts" / "military-tech"
BG = {"cover": BACKGROUNDS / "BXR_Military_Cover_16x9.png",
      "section": BACKGROUNDS / "BXR_Military_Section_16x9.png",
      "content": BACKGROUNDS / "BXR_Military_Content_White_16x9.png"}
TEMPLATE_DIR = SKILL / "templates"
MASTER_PPTX = TEMPLATE_DIR / "BXR_Military_Master_v0.1.pptx"

_c = json.loads(COLORS_JSON.read_text(encoding="utf-8"))
def _hex(node): return node["hex"].lstrip("#").upper()

RED = _hex(_c["brand"]["core"]["BxR Red"])            # D02753 — the only corporate red
BLACK = _hex(_c["brand"]["core"]["Command Black"])    # 0B0F14
GRAPHITE = _hex(_c["brand"]["core"]["Graphite"])      # 1E252D
PAPER = _hex(_c["brand"]["core"]["Paper"])            # F2F4F6
WHITE = "FFFFFF"
TEXT_RED = _hex(_c["brand"]["text"]["Text Red"])      # A51C40 numerals on light only
SLATE = _hex(_c["neutral"]["Slate"]); ASH = _hex(_c["neutral"]["Ash"])
MIST = _hex(_c["neutral"]["Mist"]); LINE = _hex(_c["neutral"]["Line"])
SIM_CYAN = _hex(_c["functional"]["Sim Cyan"])        # XR lines on dark
SIGNAL_TEAL = _hex(_c["functional"]["Signal Teal"])  # XR data on light

# sector accents: 'deep' = on white, 'light' = on dark, 'tint' = light block. Accent level only.
SECTOR = {k.lower(): {"deep": _hex(v["deep"]), "light": _hex(v["light"]), "tint": _hex(v["tint"])}
          for k, v in _c["sector"].items()}
SECTOR_ALIAS = {"army": "army", "navy": "navy", "air": "air", "police": "police", "fire": "fire"}

def sector_accent(sector):
    """Return sector colors or None (cross-sector / corporate use neutral functional colors)."""
    key = SECTOR_ALIAS.get(sector or "")
    return SECTOR.get(key) if key else None

FONT = "Noto Sans TC"        # primary (CIS ~90%)
FONT_JP = "Noto Sans JP"     # East-Asian face for JP decks (same Noto family)
MONO = "B612 Mono"           # technical accent (CIS <=10%), plain zero
