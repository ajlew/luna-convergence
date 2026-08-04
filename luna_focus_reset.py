from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path


FOCUS_RESET_LABEL = "Luna's signature Focus Reset"
FOCUS_RESET_METHOD = "Uttarabodhi mudra + box breath"
FOCUS_RESET_CUE = "Bring thought, intention and action into one line."
FOCUS_RESET_DURATION = "Optional / 1-2 minutes"
FOCUS_RESET_ASSET = Path(__file__).parent / "assets" / "luna_focus_reset_mudra.png"


@lru_cache(maxsize=1)
def focus_reset_data_uri() -> str:
    """Return the approved circular mudra artwork as an embedded PNG URI."""
    if not FOCUS_RESET_ASSET.exists():
        return ""
    encoded = base64.b64encode(FOCUS_RESET_ASSET.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def focus_reset_web_html(*, class_name: str = "luna-focus-reset") -> str:
    """Build the compact, non-instructional Luna ritual card used by web reports."""
    image_uri = focus_reset_data_uri()
    image_html = (
        f'<img src="{image_uri}" alt="Uttarabodhi mudra circular illustration" />'
        if image_uri
        else '<div class="luna-focus-reset-fallback" aria-hidden="true">◇</div>'
    )
    return f"""
<section class="{class_name}" aria-label="{FOCUS_RESET_LABEL}">
  {image_html}
  <div class="luna-focus-reset-copy">
    <span>{FOCUS_RESET_LABEL}</span>
    <strong>{FOCUS_RESET_METHOD}</strong>
    <p>{FOCUS_RESET_CUE}</p>
  </div>
  <small>{FOCUS_RESET_DURATION}</small>
</section>
"""
