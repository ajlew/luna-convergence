from pathlib import Path

ROOT = Path(__file__).resolve().parent
app = (ROOT / "app.py").read_text(encoding="utf-8")
config = (ROOT / "site_config.py").read_text(encoding="utf-8")

assert 'MONTHLY_PRICE = "A$3.30"' in config
assert 'Choose and personalise your report' not in app
assert 'Select the star sign, report period, timezone and personal focus **before payment**.' not in app
assert '<div class="delivery-notice"><strong>Instant delivery</strong>' not in app
assert '<div class="eyebrow">Monthly strategic report</div>' not in app
assert '<div class="eyebrow">Year-ahead strategic report</div>' not in app
assert 'Monthly report — {MONTHLY_PRICE}' in app
assert 'Prepare monthly checkout — {MONTHLY_PRICE}' in app
