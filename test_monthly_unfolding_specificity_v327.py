from monthly_report_pipeline import build_production_monthly_report

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def _build(sign: str):
    return build_production_monthly_report(
        sign=sign,
        year=2026,
        month=8,
        timezone_name="Australia/Sydney",
        nearest_city="Sydney",
    )[0]


def _chapter_text(narrative):
    return " ".join(
        " ".join([chapter.hook, *chapter.paragraphs, chapter.action])
        for chapter in narrative.chapters
    )


def test_august_three_act_hooks_are_sign_specific_across_all_twelve_signs():
    narratives = {sign: _build(sign) for sign in SIGNS}
    for index in range(3):
        hooks = [narratives[sign].chapters[index].hook for sign in SIGNS]
        assert len(set(hooks)) == 12


def test_pisces_capricorn_sagittarius_tell_different_august_stories():
    pisces = _build("Pisces")
    capricorn = _build("Capricorn")
    sagittarius = _build("Sagittarius")

    assert [c.hook for c in pisces.chapters] == [
        "A workable routine begins to prove itself",
        "The routine stops being temporary",
        "The cost of the routine becomes personal",
    ]
    assert [c.hook for c in capricorn.chapters] == [
        "A financial or trust issue becomes easier to define",
        "The real price of the agreement becomes visible",
        "What was financial now forces a decision",
    ]
    assert [c.hook for c in sagittarius.chapters] == [
        "The wider road gets its first piece of proof",
        "The wider road demands a real commitment",
        "The wider road reaches your front door",
    ]


def test_customer_chronology_no_longer_exposes_score_language_or_old_template_hooks():
    forbidden = (
        "support clearly outweighs friction",
        "friction clearly outweighs support",
        "The first signal: movement arrives before the whole picture is settled",
        "The pattern concentrates: the main issue becomes harder to treat as a one-off",
        "The storm peaks: the original problem starts affecting the rest of the month",
        "Do what is necessary and preserve optionality while the pressure is still moving",
    )
    for sign in SIGNS:
        text = _chapter_text(_build(sign))
        for phrase in forbidden:
            assert phrase not in text


def test_august_newspaper_evidence_dates_remain_unchanged():
    narrative = _build("Sagittarius")
    assert [c.date_range for c in narrative.chapters] == [
        "1-10 August 2026",
        "11-20 August 2026",
        "21-31 August 2026",
    ]
    assert "Sun trine Saturn" in narrative.chapters[0].title
    assert "Eclipse" in narrative.chapters[1].title
    assert "Eclipse" in narrative.chapters[2].title


def test_sagittarius_secondary_relief_survives_narrative_specificity_upgrade():
    narrative = _build("Sagittarius")
    middle = " ".join(narrative.chapters[1].paragraphs)
    assert "romance, creativity and pleasure provide genuine relief" in middle
    assert "Mercury trine Neptune" in middle
