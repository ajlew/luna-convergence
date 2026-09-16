"""Free readings: calculated metadata plus one plain-text LLM response.

No provider imports here: this module is safe for read-only public pages.
"""
from __future__ import annotations

import hashlib
import json
import re
import tempfile
from pathlib import Path
from html import escape

ROOT = Path(__file__).parent / "generated" / "readings"
WORD_RANGES = {"daily": (65, 100), "weekly": (130, 180), "monthly": (280, 380), "studio_weekly": (85, 110), "studio_daily": (18, 30)}
PARAGRAPHS = {"daily": "one or two", "weekly": "two", "monthly": "four to six", "studio_weekly": "one or two", "studio_daily": "one"}
VOICE_VERSION = "plain-text-1"


def packet_hash(packet: dict) -> str:
    return hashlib.sha256(json.dumps(packet, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), default=str).encode()).hexdigest()


def reading_path(product: str, period: str, timezone: str, root=ROOT) -> Path:
    if product not in WORD_RANGES or not re.fullmatch(r"\d{4}-\d{2}(?:-\d{2})?", period):
        raise ValueError("Invalid product or period")
    zone = re.sub(r"[^A-Za-z0-9_-]", "-", timezone)
    return Path(root) / product / f"{period}_{zone}.json"


def text_errors(product: str, body: object) -> list[str]:
    if not isinstance(body, str) or not body.strip():
        return ["empty prose"]
    errors = []
    if body.lstrip().startswith(("{", "[", "```")):
        errors.append("plain prose required")
    if re.search(r"\b(will definitely|will certainly|destined to|fated to|automatic luck|"
                 r"manifestation is proven|the universe will deliver)\b", body, re.I):
        errors.append("unsupported certainty")
    for match in re.finditer(r"\bguarantee(?:d|s)?\b", body, re.I):
        prefix = re.split(r"[.!?\n]", body[:match.start()])[-1].lower().split()[-5:]
        if not set(prefix) & {"no", "not", "never", "nothing", "without", "cannot"}:
            errors.append("guarantee")
    return errors


def prompt_for(packet: dict) -> str:
    product = packet["product"]
    low, high = WORD_RANGES[product]
    brief = {k: v for k, v in packet.items() if k != "calculation_header"}
    guidance = {
        "daily": "Explain the strongest aspect, then how the supporting influences change the practical picture today. ",
        "weekly": "Trace the early-week, midweek and weekend progression. Connect support and pressure, rather than describing only the easiest aspects. ",
        "monthly": "Build a beginning, middle and end for the month. Explain the turning points, including supplied eclipses and seasonal gates. Group related events into human themes instead of reciting every transit. ",
    }.get(product, "Explain the collective pattern clearly for a spoken video. ")
    return (
        "You are Luna. Interpret this calculated brief as one connected human story. "
        "Python has already calculated the sky; do not recalculate or add events, dates, "
        "times, signs or houses. Use the actual supplied life areas. Distinguish slow "
        "background influences from brief triggers; separating does not mean becoming exact. "
        "Describe possibilities, not promised events.\n\n"
        "Write alive, intimate, imperative-led prose. Be incisive, humorous and affirming. "
        "Include a restrained tongue-in-cheek observation when it fits. Give concrete examples "
        "supported by the brief, connect pressure with support, and keep the reader's agency. "
        "For each important aspect you mention, explain its symbolic meaning in ordinary language, "
        "then connect it to the supplied life areas and a useful response. "
        "Treat examples as choices, not predictions: no invented windfalls, meetings, investment gains or personal events. "
        "Use a house number only when the brief explicitly associates that house with that event. "
        "Never turn a closest-approach label into an exact time, or imply a guaranteed effect. "
        + guidance +
        "No dreary advice template, generic flattery, cosmic filler, guarantees or magical promises. "
        "Do not repeat the calculation list.\n\n"
        f"Aim for roughly {low}-{high} words in {PARAGRAPHS[product]} short paragraphs. Prioritise a complete, useful reading over an exact count. "
        "No JSON, headings, lists, citations or separate fields. Weave affirmation naturally "
        "into the prose. End with one clear imperative action sentence, ending in a full stop. "
        "Do not write the label Your move; the page adds it.\n\nCALCULATED BRIEF:\n"
        + json.dumps(brief, ensure_ascii=False, default=str, separators=(",", ":"))
    )


def make_reading(packet: dict, body: str) -> dict:
    errors = text_errors(packet["product"], body)
    if errors:
        raise ValueError("; ".join(errors))
    return {**{key: packet[key] for key in
               ("product", "period", "sign", "timezone", "calculation_header", "life_areas")},
            "facts_hash": packet_hash(packet), "voice_version": VOICE_VERSION,
            "voice_body": body.strip(), "status": "published"}


def read_document(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def current_reading(value: object, packet: dict) -> dict | None:
    if not isinstance(value, dict):
        return None
    if any(value.get(key) != packet[key] for key in ("product", "period", "sign", "timezone")):
        return None
    if value.get("facts_hash") != packet_hash(packet) or value.get("status") != "published":
        return None
    if value.get("voice_version") != VOICE_VERSION or text_errors(packet["product"], value.get("voice_body")):
        return None
    return value


def load_reading(packet: dict, root=ROOT) -> dict | None:
    doc = read_document(reading_path(packet["product"], packet["period"], packet["timezone"], root))
    signs = doc.get("signs")
    return current_reading(signs.get(packet["sign"]), packet) if isinstance(signs, dict) else None


def write_document(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     suffix=".tmp", delete=False) as stream:
        json.dump(document, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        temporary = Path(stream.name)
    temporary.replace(path)


def split_move(body: str) -> tuple[str, str]:
    """Extract the last sentence without losing paragraph breaks or duplicating it."""
    body = re.sub(r"(?im)^\s*(?:\*\*)?your move(?:\*\*)?\s*[:—–-]\s*", "", body.strip())
    endings = list(re.finditer(r'[.!?][”"\u2019]?\s+(?=\S)', body))
    if not endings:
        return "", body
    boundary = endings[-1].end()
    move = re.sub(r"(?i)^(?:\*\*)?your move(?:\*\*)?\s*[:—–-]\s*", "", body[boundary:].strip())
    return body[:boundary].rstrip(), move


def reading_html(packet: dict, reading: dict | None) -> str:
    lines = list(dict.fromkeys(packet["calculation_header"]))
    if packet["product"] == "monthly":
        unique = {}
        for line in lines:
            key = str(line).casefold().replace("opposition", "opposite")
            unique.setdefault(key, line)
        lines = sorted(unique.values(), key=str)
    header = "".join(f"<li>{escape(str(line))}</li>" for line in lines)
    areas = escape(" · ".join(packet["life_areas"]))
    html = ('<style>.luna-plain-reading{max-width:820px;overflow-wrap:anywhere;}'
            '.luna-plain-reading p{line-height:1.65;}'
            '.luna-plain-reading h2{font-size:1.2rem!important;line-height:1.3!important;margin-top:1.6rem;}'
            '.luna-plain-reading li{line-height:1.5;margin-bottom:.45rem;}'
            '@media(max-width:600px){.luna-plain-reading{width:100%;}'
            '.luna-plain-reading ul{padding-left:1.25rem;}}</style>'
            f'<section class="luna-plain-reading"><div class="eyebrow">'
            f'{escape(packet["sign"])} · {escape(packet["period"])}</div>'
            f'<h2>Key calculations</h2><p>Dates and times: {escape(packet["timezone"])}</p>'
            f'<ul>{header}</ul><p>{areas}</p>')
    if reading:
        body, move = split_move(reading["voice_body"])
        paragraphs = "".join(f"<p>{escape(p)}</p>" for p in re.split(r"\n\s*\n", body) if p)
        html += (f'<h2>Luna’s reading</h2>{paragraphs}<div class="lean-daily-move">'
                 f'<div class="lean-daily-label">Your move</div><p>{escape(move)}</p></div>')
    # Missing prose is not replaced by invented interpretation or internal errors.
    return html + "</section>"
