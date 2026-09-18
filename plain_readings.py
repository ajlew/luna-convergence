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
WORD_RANGES = {"daily": (65, 100), "weekly": (130, 180), "monthly": (280, 380), "studio_weekly": (85, 110), "studio_daily": (18, 30), "studio_meaning": (55, 90)}
PARAGRAPHS = {"daily": "one or two", "weekly": "three", "monthly": "four to six", "studio_weekly": "one or two", "studio_daily": "one", "studio_meaning": "one or two"}
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
    return errors


def prompt_for(packet: dict) -> str:
    product = packet["product"]
    low, high = WORD_RANGES[product]
    from reading_quality import grounded_brief
    brief = grounded_brief(packet)
    guidance = {
        "studio_weekly": "Give a complete collective weekly overview: opening mood, midweek shift, weekend resolution and one useful move. Name the key supporting and challenging aspects. This is also the master voiceover. ",
        "studio_meaning": "Explain this day’s collective meaning and energy. Name the main aspect and explain how active supporting aspects colour it. Distinguish slow background changes from brief emotional triggers. Offer a concrete response without personal houses or birth-chart claims. ",
        "daily": "Explain the strongest aspect, then how the supporting influences change the practical picture today. ",
        "weekly": "Trace the early-week, midweek and weekend progression. Connect support and pressure, rather than describing only the easiest aspects. ",
        "monthly": "Build a beginning, middle and end for the month. Explain the turning points, including supplied eclipses and seasonal gates. Group related events into human themes instead of reciting every transit. ",
    }.get(product, "Explain the collective pattern clearly for a spoken video. ")
    if product in ('weekly', 'studio_weekly'):
        guidance += ("Follow chronological_day_map in Monday-to-Sunday order. Never jump backwards. "
            "For Weekly, use three connected passages: Monday–Tuesday, Wednesday–Thursday, Friday–Sunday. "
            "For the Studio overview, summarise that same progression in spoken prose. "
            "Keep every named aspect on its supplied weekday, including supporting aspects. "
            "Do not move a Sunday event to Saturday or label a separating aspect as newly exact. "
            "Mention days only where useful; no need to recite all seven in a short overview. ")
    return (
        "You are Luna. Interpret this calculated brief as one connected human story. "
        "Python has already calculated the sky; do not recalculate or add events, dates, "
        "times, signs or houses. Use the actual supplied life areas. Distinguish slow "
        "background influences from brief triggers; separating does not mean becoming exact. "
        "Describe possibilities, not promised events.\n\n"
        "Open with a capitalised imperative sentence addressed to the reader. Write alive, intimate, imperative-led prose. Be incisive, humorous and affirming. "
        "Include a restrained tongue-in-cheek observation when it fits. Give concrete examples "
        "supported by the brief, connect pressure with support, and keep the reader's agency. "
        "For each important aspect you mention, explain its symbolic meaning in ordinary language, "
        "then connect it to the supplied life areas and a useful response. "
        "Name the main calculated aspect and the useful support aspect when the brief supplies them. "
        "If an event has a date, keep that event attached to that date; use exact date wording instead of loose phrases like a week later. "
        "Treat examples as choices, not predictions: no invented windfalls, meetings, investment gains or personal events. "
        "Use only the event_life_areas belonging to the event you are discussing. Never borrow a life area from a different event. "
        "For example, translate each supplied house meaning directly rather than guessing from its number. "
        "Keep house numbers and internal labels out of the finished prose; explain their supplied human meaning instead. "
        "Do not write first area, second area, seventh area or similar internal labels. "
        "When two slow or heavy aspects are supplied, keep their meanings separate before you blend them. "
        "Mention and explain every required_turning_point, even when this needs more words. "
        "Do not predict investment profits, double money, or recommend speculative action. "
        "Never turn a closest-approach label into an exact time, or imply a guaranteed effect. "
        + guidance +
        "No dreary advice template, generic flattery, cosmic filler, guarantees or magical promises. "
        "Do not repeat the calculation list.\n\n"
        f"Aim for roughly {low}-{high} words in {PARAGRAPHS[product]} short paragraphs. Prioritise a complete, useful reading over an exact count. "
        "No Markdown emphasis marks, JSON, headings, lists, citations or separate fields. Weave affirmation naturally "
        "into the prose. End with one clear imperative action sentence, ending in a full stop. "
        "Make that action specific to the supplied pattern: a concrete verb and task someone could do today. Avoid vague closings such as embrace the fluctuations, make space, trust the process, or notice what arises. "
        "Do not write the label Your move; the page adds it.\n\nCALCULATED BRIEF:\n"
        + json.dumps(brief, ensure_ascii=False, default=str, separators=(",", ":"))
    )


def make_reading(packet: dict, body: str) -> dict:
    from reading_quality import content_errors, writing_revision
    body = clean_prose(body)
    errors = text_errors(packet["product"], body) + content_errors(packet, body)
    if errors:
        raise ValueError("; ".join(errors))
    return {**{key: packet[key] for key in
               ("product", "period", "sign", "timezone", "calculation_header", "life_areas")},
            "facts_hash": packet_hash(packet), "voice_version": VOICE_VERSION,
            "writing_revision": writing_revision(packet["product"]),
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
    return {**value, "voice_body": clean_prose(value["voice_body"])}


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


def clean_prose(body: str) -> str:
    """Remove model emphasis delimiters without interpreting untrusted HTML."""
    return re.sub(r"\*{1,3}|_{2,3}|`+", "", body).strip()


def split_move(body: str) -> tuple[str, str]:
    """Extract the last sentence without losing paragraph breaks or duplicating it."""
    body = clean_prose(body)
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
    from luna_reading_style import STYLE
    html = (STYLE + f'<section class="luna-plain-reading"><div class="eyebrow">'
            f'{escape(packet["sign"])} · {escape(packet["period"])}</div>'
            f'<details class="luna-calculations"><summary>Key calculations</summary>'
            f'<p>Dates and times: {escape(packet["timezone"])}</p>'
            f'<ul>{header}</ul><p>{areas}</p></details>')
    if reading:
        body, move = split_move(reading["voice_body"])
        move = re.sub(r"[A-Za-z]", lambda m: m.group().upper(), move, count=1)
        paragraphs = "".join(f"<p>{escape(p)}</p>" for p in re.split(r"\n\s*\n", body) if p)
        html += (f'<h2>Luna’s reading</h2>{paragraphs}<div class="lean-daily-move">'
                 f'<div class="lean-daily-label">Your move</div><p>{escape(move)}</p></div>')
    # Missing prose is not replaced by invented interpretation or internal errors.
    return html + "</section>"


def generation_current(value, packet):
    """Refresh earlier writing once; keep the public storage format compatible."""
    from reading_quality import writing_revision, content_errors
    return (current_reading(value, packet) is not None
            and value.get('writing_revision') == writing_revision(packet['product'])
            and not content_errors(packet, value.get('voice_body')))
