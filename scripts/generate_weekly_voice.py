from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from luna_voice_provider import generate_openai_compatible_json  # noqa: E402
from weekly_view import build_weekly_view, monday_for  # noqa: E402
from weekly_voice_composer import (  # noqa: E402
    build_weekly_voice_packet,
    build_weekly_voice_prompt,
    candidate_path,
    make_candidate_document,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate one validated Luna weekly voice candidate outside Streamlit."
    )
    parser.add_argument("--week", required=True, help="Any date in the production week (YYYY-MM-DD).")
    parser.add_argument("--timezone", default="Australia/Sydney")
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--response-file",
        type=Path,
        help="Validate a previously generated JSON copy instead of calling a provider.",
    )
    parser.add_argument(
        "--packet-only",
        action="store_true",
        help="Print the closed evidence packet and make no provider call.",
    )
    return parser.parse_args()


def _write_json_atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
    ) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def main() -> int:
    args = _parse_args()
    selected = date.fromisoformat(args.week)
    monday = monday_for(selected)
    days = build_weekly_view(monday, args.timezone)
    packet = build_weekly_voice_packet(days, monday, args.timezone)
    if args.packet_only:
        print(json.dumps(packet, ensure_ascii=False, indent=2))
        return 0

    if args.response_file:
        copy = json.loads(args.response_file.read_text(encoding="utf-8"))
        provider = "response-file"
        model = args.response_file.name
    else:
        copy = generate_openai_compatible_json(build_weekly_voice_prompt(packet))
        provider = os.getenv("LUNA_VOICE_PROVIDER", "openai-compatible")
        model = os.getenv("LUNA_VOICE_MODEL", "")

    document = make_candidate_document(
        copy,
        packet,
        provider=provider,
        model=model,
    )
    output = args.output or candidate_path(monday, args.timezone)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    _write_json_atomic(output, document)
    print(f"Validated Luna voice candidate written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

