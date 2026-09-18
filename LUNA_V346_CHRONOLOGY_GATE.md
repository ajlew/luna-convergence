# Luna v3.46 - Chronology Gate

## Decision

Chronology is the only hard editorial validation rule.

The generator still receives guidance about aspect coverage, human life-area wording,
Luna's voice, certainty, and concrete actions. Those preferences can improve a retry,
but they no longer discard otherwise usable copy.

## What can reject generated copy

- Empty output.
- JSON or fenced-code output instead of plain prose.
- Weekly or Studio Weekly weekdays written out of Monday-to-Sunday order.
- A named aspect attached to the wrong supplied weekday.

## What remains prompt guidance

- Naming main and supporting aspects.
- Explaining seasonal gates, lunations, and eclipses.
- Translating internal house labels into human language.
- Using exact dates instead of loose timing phrases.
- Ending with a specific practical action.
- Avoiding guarantees and unsupported certainty.
- Keeping Luna's imperative, dry, alive voice.

This keeps calculated chronology protected without turning editorial preferences into
failure conditions that leave readings unpublished.
