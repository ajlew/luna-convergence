# Luna Monthly Narrative v3.1

This update extends the August 2026 calibration set to all 12 zodiac signs and fixes monthly print identity metadata.

## Print identity fix

Every monthly report now embeds a compact report-details band inside the report itself. It is cloned into the print portal, so browser printing / Save as PDF retains:

- Star sign
- Report month
- Local generation date and time
- Timezone (short name + IANA timezone)

The generated timestamp is calculated in the report/browser-selected timezone, not the Streamlit server timezone.

## Full 12-sign August calibration

The scenario library is now calibrated against all 12 August 2026 sign reports. The calibration is used only to abstract scenario associations; no source prose is stored or reproduced.

The August event-led eclipse axis is regression-tested across all signs:

- Aries 5 → 12
- Taurus 4 → 11
- Gemini 3 → 10
- Cancer 2 → 9
- Leo 1 → 8
- Virgo 12 → 7
- Libra 11 → 6
- Scorpio 10 → 5
- Sagittarius 9 → 4
- Capricorn 8 → 3
- Aquarius 7 → 2
- Pisces 6 → 1

## Scenario database changes

The deterministic scenario library now contains 31 scenario families. The core house families were expanded with practical manifestations for property, communications, work/health, partnerships, outside money, travel/legal/study, career, networks and private/closure themes.

New higher-specificity families include:

- home/property expansion
- communication assignments
- work/client/staffing growth
- partnership formalisation
- shared-finance opportunity
- career breakthrough
- community/joint venture
- private preparation
- unexpected work/staffing disruption
- unexpected travel/legal complication
- romance/child/creative cost pressure
- health/treatment/recovery

Scenario selection remains deterministic. No random sampling is used.

## Ranking refinement

Broad multi-house scenario families now receive a specificity penalty unless the event evidence covers enough of their house signature. This prevents generic families such as paperwork or publishing from outranking a precise one-house story merely because they match many houses.

## Tests

- all 12 August event-led primary/secondary eclipse axes
- unique 12-sign headlines
- monthly QA checks
- monthly print metadata
- print portal cloning
- automatic expansion of evidence disclosures for print
- customer MVP flow
- admin monthly webpage flow
