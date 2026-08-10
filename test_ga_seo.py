from pathlib import Path

root = Path(__file__).parent
app = (root / "app.py").read_text(encoding="utf-8")
config = (root / "site_config.py").read_text(encoding="utf-8")

assert "G-TE5HPKV94D" in app
assert "st.navigation" in app
assert 'url_path="august-2026-horoscopes"' in app
assert "monthly_report_click" in app
assert "daily_reading_generated" in app
assert 'MONTHLY_PRICE = "A$3.30"' in config
assert 'YEARLY_PRICE = "A$14.95"' in config

urls = (root / "SEARCH_CONSOLE_URLS.txt").read_text(encoding="utf-8").splitlines()
assert len(urls) == 20
assert "https://luna-convergence.streamlit.app/august-2026-sagittarius" in urls

print("GA4 and SEO route checks passed.")
