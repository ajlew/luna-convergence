from pathlib import Path


def main() -> None:
    root = Path(__file__).parent
    app = (root / "app.py").read_text(encoding="utf-8")
    admin = (root / "admin_console.py").read_text(encoding="utf-8")
    monthly = (root / "monthly_narrative_v1.py").read_text(encoding="utf-8")

    assert '"Nearest city (optional)"' in app
    assert "daily_solar_convergence" in app
    assert "SOLAR_YEAR_PAGE_REF" in app
    assert 'url_path="solar-year"' in app
    assert "nearest_city=nearest_city" in app
    assert '"Nearest city"' in admin
    assert "nearest_city=nearest_city" in admin
    assert "# Your Solar Convergence" in monthly

    print("Solar Convergence app integration checks passed.")


if __name__ == "__main__":
    main()
