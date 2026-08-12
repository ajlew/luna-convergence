from pathlib import Path
import ast

APP = Path(__file__).with_name('app.py').read_text(encoding='utf-8')
MONTHLY = Path(__file__).with_name('monthly_experience_v1.py').read_text(encoding='utf-8')


def _preview_hooks():
    tree = ast.parse(APP)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'AUGUST_2026_PREVIEW_HOOKS':
                    return ast.literal_eval(node.value)
    raise AssertionError('AUGUST_2026_PREVIEW_HOOKS not found')


def test_all_twelve_public_monthly_hooks_are_unique():
    hooks = _preview_hooks()
    assert len(hooks) == 12
    assert len(set(hooks.values())) == 12
    assert all('Pressure builds around' not in value for value in hooks.values())


def test_public_preview_uses_distinct_hook_without_touching_paid_narrative():
    assert '_august_preview_narrative(narrative)' in APP
    assert 'replace(narrative, hook_headline=hook)' in APP
    assert 'show_print=False,\n            preview=True' in APP


def test_public_monthly_hero_is_compact():
    assert "luna-monthly-preview' if preview else ''" in MONTHLY
    assert '.luna-monthly-preview .luna-monthly-hero h1' in MONTHLY
    assert 'font-size:clamp(1.8rem,4vw,2.8rem);' in MONTHLY
    assert 'padding:clamp(.8rem,1.8vw,1.15rem);' in MONTHLY


def test_read_another_sign_selector_is_visually_quieter():
    assert 'monthly-other-signs-label' in APP
    assert 'padding:.3rem .48rem;' in APP
    assert 'font-size:.61rem;' in APP
