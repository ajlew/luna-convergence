from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from datetime import date

from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
from synthesis import period_report


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", text.lower())).strip()


def _customer_blocks(narrative):
    """Return only copy rendered in the visible customer story.

    Collapsed timing and technical evidence are intentionally excluded.
    """
    blocks: list[tuple[str, str]] = []
    for index, paragraph in enumerate(narrative.luna_says[:2], start=1):
        blocks.append((f"Luna Says {index}", paragraph))
    for chapter in narrative.chapters:
        for index, paragraph in enumerate(chapter.paragraphs, start=1):
            blocks.append((f"{chapter.label} paragraph {index}", paragraph))
    blocks.append(("Romance active", narrative.romance_active))
    blocks.append(("Romance quiet", narrative.romance_quiet))
    for field_name, label in (
        ("love_story", "Love"),
        ("work_story", "Work"),
        ("money_story", "Money"),
    ):
        values = getattr(narrative, field_name)
        if values:
            blocks.append((label, values[0]))
    for index, item in enumerate(narrative.key_dates, start=1):
        blocks.append((f"Moments to notice {index}", item.response))
    for index, action in enumerate(narrative.action_plan, start=1):
        blocks.append((f"Your Move {index}", action))
    return blocks


def _duplicate_groups(narrative):
    groups: dict[str, list[str]] = defaultdict(list)
    text_by_key: dict[str, str] = {}
    for label, text in _customer_blocks(narrative):
        key = _normalise(text)
        if not key:
            continue
        groups[key].append(label)
        text_by_key.setdefault(key, text)
    return [
        (labels, text_by_key[key])
        for key, labels in groups.items()
        if len(labels) > 1
    ]


def _check(name: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"[{status}] {name}{suffix}")
    return condition


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate and sanity-check one Luna Monthly report."
    )
    parser.add_argument("--sign", default="Sagittarius")
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--month", type=int, default=8)
    parser.add_argument("--timezone", default="Australia/Sydney")
    parser.add_argument("--city", default="Sydney")
    parser.add_argument("--focus", default="General overview")
    args = parser.parse_args()

    start = date(args.year, args.month, 1)
    if args.month == 12:
        next_month = date(args.year + 1, 1, 1)
    else:
        next_month = date(args.year, args.month + 1, 1)
    end = date.fromordinal(next_month.toordinal() - 1)
    label = start.strftime("%B %Y")

    result = period_report(
        args.sign,
        start,
        end,
        args.timezone,
        label,
        transition_count=9,
        nearest_city=args.city,
        main_focus=args.focus,
    )
    narrative = build_monthly_narrative(result)
    html = build_monthly_experience_html(narrative, result, show_print=True)

    print(f"\nLuna Monthly sanity check: {args.sign} — {label}\n")
    checks: list[bool] = []

    checks.append(_check(
        "Four-act spine",
        [chapter.label for chapter in narrative.chapters]
        == ["Act I", "Act II", "Act III", "Act IV"],
    ))
    checks.append(_check(
        "Four unique act periods",
        len({chapter.date_range for chapter in narrative.chapters}) == 4,
    ))
    relationship_acts = [
        chapter for chapter in narrative.chapters
        if chapter.title == "Watch what happens next"
    ]
    checks.append(_check(
        "Relationship test integrated once",
        len(relationship_acts) == 1,
        relationship_acts[0].date_range if relationship_acts else "missing",
    ))
    checks.append(_check(
        "Four rendered story acts",
        html.count('class="luna-story-act"') == 4,
    ))
    checks.append(_check(
        "Four moments-to-notice cards",
        html.count('class="luna-story-date-card"') == 4,
    ))
    checks.append(_check(
        "Old three-act language removed",
        "The month in three acts" not in html and "Dates worth circling" not in html,
    ))
    checks.append(_check(
        "Detached relationship section removed",
        '<section class="luna-monthly-section luna-relationship-test">' not in html,
    ))

    duplicates = _duplicate_groups(narrative)
    checks.append(_check(
        "No verbatim customer-copy repetition",
        not duplicates,
        f"{len(duplicates)} repeated block group(s)" if duplicates else "",
    ))

    if duplicates:
        print("\nRepeated customer copy detected:")
        for labels, text in duplicates:
            preview = re.sub(r"\s+", " ", text).strip()
            if len(preview) > 180:
                preview = preview[:177] + "..."
            print(f"- {' / '.join(labels)}")
            print(f"  {preview}")

    print("\nManual customer read:")
    print("1. Read only the visible customer story; keep evidence collapsed.")
    print("2. Each act must add a new event, decision or consequence.")
    print("3. The relationship test must appear once, inside Act III.")
    print("4. Love, Work and Money must add different value, not retell the acts.")
    print("5. The final 'Your move' must be concrete enough to act on.")
    print("6. Open Print or Save Report and inspect page breaks on phone and desktop.")

    if all(checks):
        print("\nOVERALL: PASS — structurally clean and free of verbatim duplication.")
        return 0

    print("\nOVERALL: REVIEW REQUIRED — fix failed items before public sale.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
