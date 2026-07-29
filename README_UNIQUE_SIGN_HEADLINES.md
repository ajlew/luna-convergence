# Sign-Specific Daily Headlines

## Correction

A shared planetary aspect may affect all twelve signs, but it moves through
different whole-sign houses for each sign. The public headline must therefore
describe the sign-specific consequence rather than repeat one universal phrase.

The headline layer now uses:

```text
aspect meaning
× activated house pair
× aspect tone
= sign-specific headline
```

## July 29, 2026 example

The shared evidence is Venus square Mars. The four mutable signs now receive:

- Gemini: **A private feeling needs an honest response**
- Virgo: **What you want is changing who you are ready to be**
- Sagittarius: **What you want is changing how you are seen**
- Pisces: **The relationship needs a clearer answer**

The evidence remains consistent, while the public language reflects each
sign's activated houses.

## Automated quality gate

The new regression test generates all twelve signs for July 27–30, 2026 and
requires twelve unique headlines on every date. It also checks that the four
mutable signs do not share a headline and verifies the expected July 29 wording.
