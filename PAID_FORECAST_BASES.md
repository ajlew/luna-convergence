# Luna paid forecast calculation bases

## Purpose

Paid Monthly and Year Ahead should not ask the LLM to rediscover the forecast from scratch every time a customer opens a report.

The deterministic astrology engine owns the calculation base. Luna Voice receives that base plus the customer's derived natal context and writes the interpretation.

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

Each file contains the complete sign/month calculation board:

```text
shared sky
  -> all calculated events
  -> authoritative major-sky registry
  -> major transitions
  -> retrograde cycles
  -> convergences (evidence only)
  -> inherited context
  -> dominant life areas
  -> monthly arc / trajectory / decision
  -> key dates
  -> required structural anchors
  -> daily story ledger: one row per active date, every transit preserved
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

### Paid Monthly writing contract

`Read the month` no longer asks the LLM to interpret Opening / Middle / Closing groups.

The customer sees one long chronological report built from:

```text
whole-month lead
1 Oct -> every transit on 1 Oct
2 Oct -> every transit on 2 Oct
3 Oct -> every transit on 3 Oct
...
31 Oct -> every transit on 31 Oct
```

Only dates with a calculated event or personal natal activation receive a story entry. Each date is interpreted independently in Daily-style prose, then assembled in chronological order. Same-day transits are interpreted together because they are literally simultaneous; different dates are never collapsed into a phase or convergence group.

Voice requests are transported in small batches for reliability, but every JSON output remains one item per date. Missing events, changed dates or incomplete items fail validation. A bad batch is split until the failing day is isolated, so one weak completion cannot truncate the whole Monthly.

The target is a substantial paid narrative of roughly 2,000 words when the month's event density supports it. The target is editorial, not padding: every calculated transit must be accounted for, but the model is not asked to invent material to hit a word count.

`Key dates` is only a compact reference index. It does not repeat the longer interpretation.

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

`.github/workflows/generate-paid-forecast-bases.yml` runs on the 25th and prepares next month's twelve Monthly bases. It can also be run manually for any month, one sign, or a Year Ahead rolling start date.
