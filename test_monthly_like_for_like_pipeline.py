from __future__ import annotations

"""Regression contract: historical and ordinary monthly previews share one pipeline."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _calls_in(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            names.add(node.func.id)
    return names


def test_admin_uses_production_monthly_pipeline() -> None:
    calls = _calls_in(ROOT / "ephemeris_admin.py")
    assert "build_production_monthly_report" in calls
    assert "render_production_monthly_report" in calls


def test_monthly_preview_uses_production_monthly_pipeline() -> None:
    calls = _calls_in(ROOT / "app.py")
    assert "build_production_monthly_report" in calls
    assert "render_production_monthly_report" in calls


def test_production_renderer_cannot_use_short_preview_mode() -> None:
    source = (ROOT / "monthly_report_pipeline.py").read_text(encoding="utf-8")
    assert "preview=False" in source
    assert "preview=True" not in source
