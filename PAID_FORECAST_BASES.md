# Luna paid forecast calculation bases

## Purpose

Paid Monthly and Year Ahead should not ask the LLM to rediscover the entire forecast every time a customer opens a report.

The deterministic astrology engine owns the base. Luna Voice receives that base plus the customer's derived natal context and writes the interpretation.

## Monthly

The scheduled workflow builds one reusable file for each Sun sign before the month begins:

```text
generated/paid_forecast_bases/monthly/YYYY-MM/Australia-Sydney/
  aries.json
  taurus.json
  gemini.json
  cancer.json
  leo.json
  virgo.json
  libra.json
  scorpio.json
  sagittarius.json
  capricorn.json
  aquarius.json
  pisces.json
```

Each file contains the complete sign/month calculation board and a three-part story skeleton:

```text
shared sky
  -> all calculated events
  -> authoritative major-sky registry
  -> major transitions
  -> retrograde cycles
  -> convergences
  -> inherited context
  -> dominant life areas
  -> monthly arc / trajectory / decision
  -> key dates
  -> required structural anchors
  -> Opening / Middle / Closing story skeleton
```

At report time:

```text
stored sign/month base
        +
customer Natal Player
        +
personal monthly natal contacts
        +
reader focus/question
        ↓
Luna Voice contextualises
```

`Read the month` is deliberately generated in four bounded passes: one short lead plus Opening, Middle and Closing. A failed or truncated chapter is retried on its own; an incomplete LLM draft is never published as the whole month.

## Year Ahead

`paid_forecast_context.py` contains the equivalent `yearly_calculation_base()` and `contextualize_yearly()` contract. The generator supports `--product yearly --date YYYY-MM-DD` for a requested rolling start date. Year Ahead is not put on a fixed monthly schedule because the paid rolling year can begin on any date.

## Manual monthly build

```bash
python scripts/generate_paid_forecast_bases.py \
  --product monthly \
  --date 2026-10-01 \
  --timezone Australia/Sydney \
  --city Sydney
```

That creates all 12 October 2026 sign bases without using an LLM.

## GitHub Action

Upload `.github/workflows/generate-paid-forecast-bases.yml`. It runs on the 25th and prepares next month's twelve Monthly bases. It can also be run manually for any month, one sign, or a Year Ahead rolling start date.
