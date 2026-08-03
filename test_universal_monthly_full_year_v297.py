from __future__ import annotations

from sanity_check_universal_monthly import audit


def main() -> None:
    result = audit(2026, list(range(1, 13)))
    assert result["report_count"] == 144
    assert result["status"] == "PASS", result["failures"]
    assert result["highest_cross_sign_similarity"]["similarity"] < 0.65
    assert min(result["headline_change_by_sign"].values()) >= result["minimum_unique_headlines_per_sign"]
    print("Universal Monthly full-year validation passed: 144 reports.")


if __name__ == "__main__":
    main()
