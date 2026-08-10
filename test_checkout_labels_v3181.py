from pathlib import Path


def test_legacy_checkout_feature_chips_remain_non_button_css_if_reused():
    source = Path('app.py').read_text(encoding='utf-8')
    css = source[source.index('.pill {'):source.index('.trust-strip {')]
    assert 'border:0;' in css
    assert 'background:transparent;' in css
    assert 'padding:0;' in css
    assert '.pill + .pill::before' in css
    assert 'content:"·";' in css
    assert 'border:1px solid var(--black);' not in css


def test_checkout_marketing_cards_are_removed_v3182():
    source = Path('app.py').read_text(encoding='utf-8')
    for text in (
        'Choose and personalise your report',
        '<div class="eyebrow">Monthly strategic report</div>',
        '<div class="eyebrow">Year-ahead strategic report</div>',
        '<span class="pill">One star sign</span>',
        '<span class="pill">Personalised PDF</span>',
    ):
        assert text not in source
