from __future__ import annotations

import argparse
from calendar import monthrange
from datetime import date
from itertools import combinations
import json
import math
from pathlib import Path
import re

from bs4 import BeautifulSoup

from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
from synthesis import period_report

SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


def _trigrams(html: str) -> set[tuple[str, str, str]]:
    text = " ".join(BeautifulSoup(html, "html.parser").get_text(" ").split())
    text = text.split("Why Luna sees this", 1)[0].lower()
    words = re.findall(r"[a-z']+", text)
    return set(zip(words, words[1:], words[2:]))


def audit(year: int, months: list[int]) -> dict:
    records = []
    grams = {}
    failures = []

    for month in months:
        for sign in SIGNS:
            start = date(year, month, 1)
            end = date(year, month, monthrange(year, month)[1])
            result = period_report(
                sign, start, end, "Australia/Sydney", start.strftime("%B %Y"),
                transition_count=9, nearest_city="Sydney", main_focus="General overview",
            )
            narrative = build_monthly_narrative(result)
            html = build_monthly_experience_html(narrative, result, show_print=True)
            arc = result.get("monthly_arc") or {}
            formula = arc.get("evidence_formula") or {}
            mappings = arc.get("mapping_audit") or []

            missing_mapping = [
                item.get("role") for item in mappings
                if item.get("role") != "relationship test"
                and (not item.get("evidence") or not item.get("scenario_key"))
            ]
            duplicate_evidence = len({item.evidence.casefold() for item in narrative.key_dates}) != len(narrative.key_dates)
            if missing_mapping:
                failures.append({"sign": sign, "month": month, "issue": "missing mapping", "roles": missing_mapping})
            if duplicate_evidence:
                failures.append({"sign": sign, "month": month, "issue": "duplicate calendar evidence"})

            record = {
                "sign": sign,
                "year": year,
                "month": month,
                "headline": narrative.hook_headline,
                "theme_axis": narrative.convergence_axis,
                "primary_house": arc.get("primary_house"),
                "secondary_house": arc.get("secondary_house"),
                "solar_source_house": formula.get("solar_source_house"),
                "solar_destination_house": formula.get("solar_destination_house"),
                "relationship_question": narrative.relationship_test[0] if narrative.relationship_test else "",
                "action_plan": list(narrative.action_plan),
                "mapping_audit": mappings,
            }
            records.append(record)
            grams[(sign, month)] = _trigrams(html)

    similarities = []
    for month in months:
        for first, second in combinations(SIGNS, 2):
            a, b = grams[(first, month)], grams[(second, month)]
            value = len(a & b) / max(1, len(a | b))
            similarities.append({"month": month, "first": first, "second": second, "similarity": round(value, 4)})
            if value >= 0.65:
                failures.append({"month": month, "issue": "cross-sign similarity", "first": first, "second": second, "similarity": value})

    headline_change = {
        sign: len({item["headline"] for item in records if item["sign"] == sign})
        for sign in SIGNS
    }
    # A connected sky pattern can legitimately persist across adjacent months.
    # The gate therefore rejects template lock-in, not every repeated phrase:
    # at least 80% of the selected months must produce distinct headlines.
    minimum_unique = max(1, math.ceil(len(months) * 0.80))
    for sign, count in headline_change.items():
        if count < minimum_unique:
            failures.append({
                "sign": sign,
                "issue": "insufficient monthly headline change",
                "unique": count,
                "minimum": minimum_unique,
            })

    return {
        "engine": "Luna Universal Monthly Evidence Engine v2.9.7",
        "year": year,
        "months": months,
        "report_count": len(records),
        "highest_cross_sign_similarity": max(similarities, key=lambda item: item["similarity"], default={}),
        "headline_change_by_sign": headline_change,
        "minimum_unique_headlines_per_sign": minimum_unique,
        "failures": failures,
        "status": "PASS" if not failures else "REVIEW REQUIRED",
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--months", nargs="+", type=int, default=[7, 8, 9])
    parser.add_argument("--json", default="Luna_v297_universal_monthly_audit.json")
    args = parser.parse_args()

    result = audit(args.year, args.months)
    Path(args.json).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Reports: {result['report_count']}")
    print(f"Highest cross-sign similarity: {result['highest_cross_sign_similarity']}")
    print(f"Failures: {len(result['failures'])}")
    print(f"OVERALL: {result['status']}")


if __name__ == "__main__":
    main()
