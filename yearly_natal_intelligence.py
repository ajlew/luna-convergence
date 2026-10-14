from __future__ import annotations

"""Read-only natal-to-year evidence links. No ephemeris recalculation, prose or LLM.

This module must not change the original snapshot or YearPacket. Only a transit's
explicit natal_target is considered a contact; names within a label are not proof.
"""
from typing import Any


def natal_year_links(snapshot: Any, packet: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    aspects = tuple(getattr(snapshot, 'aspects', ()) or ())
    games = tuple(row for row in (packet.get('games') or ()) if isinstance(row, dict))
    links: list[dict[str, Any]] = []
    for aspect in aspects:
        p1 = str(getattr(aspect, 'planet1', '') or '')
        p2 = str(getattr(aspect, 'planet2', '') or '')
        if not p1 or not p2 or p1 == p2:
            continue
        contacts = []
        for index, game in enumerate(games):
            transits = [game.get('primary_transit')] + list(game.get('supporting_transits') or ())
            for transit in transits:
                if not isinstance(transit, dict):
                    continue
                target = str(transit.get('natal_target') or '').strip()
                if target not in (p1, p2):
                    continue
                contacts.append({
                    'game_index': index,
                    'game_title': str(game.get('title') or ''),
                    'natal_target': target,
                    'transiting_planet': str(transit.get('transiting_planet') or ''),
                    'transit_aspect': str(transit.get('aspect') or ''),
                })
        if contacts:
            links.append({
                'natal_planets': (p1, p2),
                'natal_aspect': str(getattr(aspect, 'name', '') or ''),
                'natal_orb': float(getattr(aspect, 'orb', 0.0) or 0.0),
                'natal_strength': float(getattr(aspect, 'strength', 0.0) or 0.0),
                'contacts': tuple(contacts),
                'distinct_games': len({item['game_index'] for item in contacts}),
            })
    return tuple(sorted(links, key=lambda item: (-item['distinct_games'], -item['natal_strength'], item['natal_orb'], item['natal_planets'])))


def year_core_thread_evidence(snapshot: Any, packet: dict[str, Any]) -> str:
    """Minimal, evidence-only context. Never claims a natal aspect recurs as a transit."""
    links = natal_year_links(snapshot, packet)
    if not links:
        return ''
    selected = links[0]
    p1, p2 = selected['natal_planets']
    targets = sorted({row['natal_target'] for row in selected['contacts']})
    games = selected['distinct_games']
    return (
        f'Your natal {p1} {selected["natal_aspect"]} {p2} links to '
        f'{games} of the selected annual stories '
        f'through verified transit contacts to {" and ".join(targets)}. '
        'This connects an existing natal pattern to the year’s timing; '
        'it does not imply that the natal aspect itself repeats.'
    )
