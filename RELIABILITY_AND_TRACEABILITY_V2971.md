# Luna Convergence v2.9.7.1

## Daily and Monthly Reliability + Evidence Traceability

This patch stabilises the existing v2.9.7 product without replacing the Universal Monthly Evidence Engine or changing Luna's customer-facing visual structure.

## Reliability changes

### Daily

- Editorial hook validation now tries the preferred approved hook, alternate tone families and a safe house-specific fallback.
- The former Capricorn false positive has been replaced with **The family meeting has entered the chat**.
- A failed editorial hook can no longer surface as a public Streamlit exception.
- Same-house aspects now use concentration grammar:
  - `both influences concentrate in relationships`;
  - not `relationships connect with relationships`.
- The renderer hard-limits the public reading to one reflection question.

### Printing and PDF

- Daily print buttons create isolated A4 documents rather than printing the visible Streamlit page.
- Daily offers:
  - customer reading only;
  - full Daily plus technical evidence.
- Monthly print opens a isolated document, opens every `<details>` element, and closes the window after printing.
- Legacy print portals are removed before every Monthly print.
- Searchable A4 PDF downloads are generated server-side with ReportLab or the existing controlled Monthly PDF pipeline.
- Canonical filenames are used:
  - `2026-08-03_Aries_Daily.pdf`;
  - `2026-08_Aries_Monthly.pdf`.

## Evidence traceability

The Monthly **Why Luna sees this** section now includes a table mapping:

| Narrative role | House | Scenario family | Supporting events |
|---|---:|---|---|
| Opening | 5 | Creative or romantic development | Sun sextile Uranus; Sun conjunction Jupiter; Full Moon in Aquarius |

The calculation remains underneath Luna's editorial layer. The table exposes the chain without changing the main reading format.

## Validation

The release test checks:

- 4,380 Daily sign/date combinations for 2026;
- zero hook exceptions;
- exactly one Daily reflection question;
- correct same-house language for all 12 signs on 3 August 2026;
- isolated A4 Daily print documents;
- searchable Daily PDFs;
- 12 Monthly reports with visible evidence-to-scenario mapping;
- isolated Monthly print-window code;
- searchable one-sign Monthly PDF output;
- canonical filenames.
