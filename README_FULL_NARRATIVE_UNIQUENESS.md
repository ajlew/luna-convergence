# Full Sign-Specific Narrative and Purchase-Sign Synchronisation

## Public narrative correction

A shared aspect may correctly appear for all twelve signs, but the customer
language must reflect the different whole-sign houses activated for each sign.

The following visible fields are now generated from the sign's trigger house:

- headline;
- three-paragraph Today's Story;
- relationship paragraph;
- Hidden Opportunity;
- Watch Out;
- Action Today;
- three sign-specific reflection questions plus one aspect question.

Shared astronomical evidence remains shared where it should:

- active planets;
- aspect type;
- orb;
- applying, separating or exact status;
- emotional weather;
- strength score;
- aspect window.

## Purchase-sign correction

The Daily Horoscope purchase form previously reused one Streamlit widget key:

```text
daily-monthly-sign
```

Streamlit therefore preserved an earlier Sagittarius selection when Gemini,
Virgo or Pisces was subsequently generated.

The daily report panel now receives a sign-specific namespace:

```python
context=f"daily-{sign.lower()}"
```

This creates keys such as:

```text
daily-gemini-monthly-sign
daily-virgo-monthly-sign
daily-sagittarius-monthly-sign
daily-pisces-monthly-sign
```

The report form therefore opens with the sign belonging to the displayed
reading. The customer may still deliberately change it before checkout.

## Quality gate

The release test requires all twelve signs on July 29, 2026 to have unique:

- headlines;
- visible stories;
- relationship copy;
- opportunities;
- cautions;
- actions;
- four-question sets.

It simultaneously verifies that the four mutable signs retain the same real
Venus-square-Mars evidence and strength score.
