"""Deterministic paid Year Ahead preflight. Never reads or edits LLM prose."""
from __future__ import annotations
from datetime import date, timedelta


def verify_yearly_material(material: dict) -> None:
    period = material.get('period') or {}
    start = date.fromisoformat(str(period.get('start') or period.get('start_date'))[:10])
    end = date.fromisoformat(str(period.get('end') or period.get('end_date'))[:10])
    if end != start + timedelta(days=364):
        raise ValueError('Year Ahead requires exactly 365 inclusive days')
    rounds = material.get('monthly_rounds') or []
    if len(rounds) != 12:
        raise ValueError('Year Ahead must contain exactly twelve monthly rounds')
    last = start - timedelta(days=1)
    for expected, row in enumerate(rounds, 1):
        a = date.fromisoformat(str(row['start'])[:10])
        b = date.fromisoformat(str(row['end'])[:10])
        if int(row['number']) != expected or a != last + timedelta(days=1) or b < a or b > end:
            raise ValueError(f'Year Ahead month {expected} has a gap, overlap or invalid date')
        key = str(row.get('strongest_date') or '')
        if key and not (a <= date.fromisoformat(key[:10]) <= b):
            raise ValueError(f'Year Ahead month {expected} strongest date outside its period')
        last = b
    if last != end:
        raise ValueError('Year Ahead monthly rounds do not reach report end')
    games = material.get('major_issues') or []
    ids = {int(game['number']) for game in games}
    if len(ids) != len(games):
        raise ValueError('Year Ahead Game numbers are not unique')
    for row in rounds:
        number = row.get('dominant_game_number')
        if number is not None and int(number) not in ids:
            raise ValueError(f"Year Ahead month {row['number']} refers to absent Game")
    for game in games:
        a, b = str(game.get('start') or '')[:10], str(game.get('end') or '')[:10]
        if a and b and date.fromisoformat(a) > date.fromisoformat(b):
            raise ValueError(f"Year Ahead Game {game['number']} has inverted window")


def decision_stage(month: dict, preceding: list[dict]) -> str:
    """Predetermined editorial progression within a Game, no inferred predictions."""
    gid = month.get('dominant_game_number')
    previous = sum(item.get('dominant_game_number') == gid for item in preceding)
    stage = ('Identify the constraint and competing options.',
             'Compare evidence and costs against the earlier options.',
             'Choose a reversible test and define a checkpoint.',
             'Review what changed; keep, renegotiate, or withdraw resources.')
    return stage[min(previous, 3)]
