"""Year Ahead strategy boards from deterministic selected Game data.

No invented planetary aspects, probabilities, optimal decisions or outcomes.
Groq never defines the board structure. These are reflective decision tools.
"""
from __future__ import annotations

from datetime import date
from html import escape
from typing import Any


def _safe(value: Any) -> str:
    return str(value or '').strip()


def _day(value: Any) -> str:
    raw = _safe(value)[:10]
    try:
        return date.fromisoformat(raw).strftime('%-d %B %Y')
    except ValueError:
        return ''


def _resource_profile(game: dict) -> dict[str, str]:
    """Symbolic policy map, never a claim about the reader's actual finances."""
    area = (_safe(game.get('human_life_area')) + ' ' + _safe(game.get('title'))).casefold()
    if any(term in area for term in ('career', 'reputation', 'authority', 'public', 'door', 'expansion')):
        return dict(resource='Time, operational capacity and reputation',
            opportunity='A bounded trial can preserve the option to accept a larger opportunity after its requirements are known.',
            protection='Request written scope, available support and a capacity limit before accepting an expanded role.')
    if any(term in area for term in ('relationship', 'partnership', 'money', 'value', 'agreement', 'attraction')):
        return dict(resource='Shared obligations, trust and potential financial exposure',
            opportunity='Clarifying terms may unlock cooperation without surrendering control of future commitments.',
            protection='Start with a reviewable agreement; define obligations, costs and exit terms before increasing exposure.')
    if any(term in area for term in ('identity', 'personal direction', 'shell', 'presentation')):
        return dict(resource='Time, emotional capacity and personal autonomy',
            opportunity='A small reversible commitment can reveal which role is worth expanding.',
            protection='Cap responsibilities and set a checkpoint before accepting permanent obligations.')
    return dict(resource='Time and attention; actual constraints must be supplied by the reader',
        opportunity='Test a small reversible option before committing additional resources.',
        protection='Define a maximum acceptable cost and a clear exit condition.')


def _adaptive_role(contact: dict) -> str:
    """Treat retrograde as a review cue, not as evidence of real-life loss."""
    phase = _safe(contact.get('stage')).casefold()
    if 'retrograde' in phase or 'return' in phase:
        return 'Review earlier choices, new information and unexpected costs; revise if the evidence calls for it'
    if 'final' in phase:
        return 'Compare trial results; decide whether to commit, adjust or withdraw'
    if 'initial' in phase or 'first' in phase:
        return 'Identify the choice, gather evidence and test a limited reversible step'
    return 'Review real conditions before adjusting resources'


def build_game_decision_boards(packet: dict) -> list[dict]:
    boards = []
    for number, game in enumerate(packet.get('games') or [], 1):
        if not isinstance(game, dict):
            continue
        primary = game.get('primary_transit') or {}
        support = game.get('supporting_transits') or []
        contacts = []
        seen = set()
        for tr in [primary, *support]:
            if not isinstance(tr, dict):
                continue
            label = _safe(tr.get('technical_label') or tr.get('label'))
            for passed in tr.get('passes') or []:
                if not isinstance(passed, dict):
                    continue
                day = _safe(passed.get('date'))[:10]
                try:
                    parsed = date.fromisoformat(day)
                except ValueError:
                    continue
                key = (day, label)
                if not label or key in seen:
                    continue
                seen.add(key)
                contacts.append({'date': day, 'label': label,
                                 'stage': _safe(passed.get('pass_label') or passed.get('stage'))})
        contacts.sort(key=lambda c: (c['date'], c['label']))
        objective = _safe(game.get('question') or game.get('strategic_frame'))
        proposed_move = _safe(game.get('move'))
        warning = _safe(game.get('dont'))
        upside = _safe(game.get('advantage'))
        downside = _safe(game.get('risk'))
        boards.append({
            'number': int(game.get('number') or number),
            'title': _safe(game.get('title') or f'Game {number}'),
            'area': _safe(game.get('human_life_area')),
            'objective': objective,
            'advantage': upside,
            'risk': downside,
            'move': proposed_move,
            'avoid': warning,
            'start': _safe(game.get('start_date')),
            'end': _safe(game.get('end_date')),
            'contacts': [{**c, 'decision_role': _adaptive_role(c)} for c in contacts],
            **_resource_profile(game),
        })
    return boards


def render_game_decision_board(board: dict) -> str:
    """Same source-defined decision structure for HTML/PDF and web screen."""
    esc = lambda v: escape(_safe(v), quote=True)
    cells = [
        ('Decision to clarify', board.get('objective')),
        ('Resource at stake', board.get('resource')),
        ('Potential advantage', board.get('advantage')),
        ('Asymmetric opportunity', board.get('opportunity')),
        ('Risk to protect against', board.get('risk')),
        ('Asymmetric downside protection', board.get('protection')),
        ('Proposed move', board.get('move')),
        ('Do not overlook', board.get('avoid')),
    ]
    rows = ''.join(f'<div class="game-decision-row"><strong>{esc(name)}</strong><span>{esc(value) if value else "Not specified in the calculated Game plan"}</span></div>' for name, value in cells)
    exact = ''.join('<li><strong>'+esc(_day(c['date']))+'</strong> · '+esc(c['label'])+ (' · '+esc(c['stage']) if c.get('stage') else '')+ '<span class="checkpoint-role">'+esc(c.get('decision_role'))+'</span></li>' for c in board.get('contacts') or [])
    checkpoint = ('<ul class="game-decision-dates">'+exact+'</ul>') if exact else '<p>No exact contacts fall within this selected Game window.</p>'
    return ('<div class="game-decision-board"><h3>Play this Game · '+esc(board.get('title'))+'</h3>'
            '<p class="game-decision-note">Use these as decision prompts, not predicted outcomes or calculated personal payoffs. '
            'A contact is a time to review your information—not an automatic instruction to act.</p>'
            + rows + '<h4>Calculated review checkpoints</h4>' + checkpoint +
            '<p class="game-decision-note"><strong>Decision rule:</strong> Compare your available resources and actual evidence against the advantage and risk. '
            'Protect against unacceptable downside while preserving affordable upside. Act only when real evidence, available resources and your priorities support it.</p>'
            '<p class="game-decision-note"><strong>What success means:</strong> Review your choice against the objective you set and the actual outcome, not the transit alone.</p></div>')


GAME_DECISION_CSS = '''
.game-decision-board{border-top:1px solid #b69b71;border-bottom:1px solid #ded4c6;padding:4mm 0;margin:6mm 0;font-size:9pt;break-inside:auto}
.game-decision-board h3{font-size:13pt;margin:1mm 0 2mm}
.game-decision-board h4{font-size:9pt;margin:3mm 0 1mm}
.game-decision-row{display:grid;grid-template-columns:40mm minmax(0,1fr);gap:4mm;border-top:1px solid #e8e2da;padding:1.6mm 0;break-inside:avoid}
.game-decision-row strong{font-weight:600}
.game-decision-board .game-decision-note{font-size:8pt;line-height:1.35;color:#54504b;margin:1.5mm 0}
.game-decision-dates{padding-left:5mm;margin:1mm 0;font-size:8pt}
.game-decision-dates li{padding:.7mm 0}.checkpoint-role{display:block;color:#666;font-size:7.4pt;margin-left:2mm}
@media(max-width:550px){.game-decision-row{grid-template-columns:1fr;gap:0}}
'''
