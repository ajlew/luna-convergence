from datetime import date
from studio_readings import weekly_sky_cards
from epic_sky import load_approved, prompt_from_cards, to_script

def test_epic_sample_matches_calculated_week():
    cards = weekly_sky_cards(date(2026,10,12), 'Australia/Sydney')
    sample = load_approved(date(2026,10,12), cards)
    assert sample and len(sample['days']) == 7
    script = to_script(sample)
    assert script.count('Your move:') == 7
    assert 'Moon square Pluto' in script and 'Venus square Pluto' in script
    assert 'Moon square Pluto' in prompt_from_cards(cards)

def test_mismatched_sky_is_not_displayed():
    cards = weekly_sky_cards(date(2026,10,12), 'Australia/Sydney')
    cards[0]['event'] = 'Mismatch'
    assert load_approved(date(2026,10,12), cards) is None
