# Luna Narrator + Forecast Inventory v2.8

## Product principle

Luna is the narrative voice of the product.

- **Daily Luna** is a sharp observer: one hook, one consequence and one move.
- **Monthly Luna** is a storyteller: carryover, opening, complication,
  relationship test, climax and resolution.
- **Yearly Luna** is a strategist and game narrator: players, board,
  dominant games, rule changes, twelve rounds and final position.

The personality remains consistent. Only the narrative distance changes.

## Calculation stack

```text
Ephemeris
→ astronomical events
→ whole-sign astrological structure
→ convergence scoring
→ ranked scenario families
→ narrative role assignment
→ Luna narration
→ customer focus, city and local light
→ Daily / Monthly / Yearly product
```

## Daily equation

```text
Strongest immediate trigger
+ activated house pair
+ emotional or relationship consequence
+ customer focus
+ local Solar Convergence
= one useful daily move
```

Daily output stays brief. Evidence remains behind disclosures.

## Monthly equation

```text
Carryover
+ ranked convergences
+ scenario pathway
+ tension curve
+ independent relationship test
+ climax and resolution
= monthly arc
```

The engine avoids assigning the same dense event cluster to several repetitive
narrative roles.

### Sagittarius, August 2026

The revised sequence is:

1. **28–30 July:** late-July breakthrough enters August with momentum.
2. **7 August:** friends, audiences or organisations help structure the plan.
3. **11–15 August:** the opportunity grows and reveals cost, distance,
   shared risk, trust, ownership or paperwork.
4. **17–21 August:** Venus and Saturn create an independent relationship test:
   *Are they here for you—or just for the fun of it?*
5. **24–28 August:** the public result meets home, location, family and
   emotional security.
6. **28 August:** the outcome must fit both ambition and private life.

## Yearly equation

```text
Inherited regime
+ planetary players
+ dominant strategic games
+ rule changes
+ twelve monthly rounds
+ path dependence
= yearly game
```

The reader remains the protagonist.

- Planets are the players.
- The sign ruler is the lead strategist.
- Houses are the board.
- Aspects are alliances, conflict and information exchange.
- Eclipses, stations and major ingresses change the rules.
- Months are rounds, not independent players.
- Each round changes the options available in the next.

The yearly engine first builds a top-down game map, then validates it against
all twelve Monthly Arc calculations. The customer report contains three
dominant games, three-to-five annual acts and twelve concise monthly moves—not
twelve full monthly reports joined together.

## Forecast inventory

The editorial route is:

```text
/forecast-library
```

It is visible only while `EDITOR_PREVIEW_ENABLED = True`.

The library can precompute:

- a Daily batch of up to 32 days;
- selected Monthly reports for one or more signs;
- Year-ahead game maps for selected signs.

Each record stores:

- report type and period;
- sign;
- timezone and representative city;
- focus;
- editorial status;
- calculation, arc and voice versions;
- calculation hash;
- complete structured payload.

Supported editorial states are:

```text
draft
calculated
narrative generated
editorially reviewed
approved
published
archived
```

The common forecast can therefore be calculated, refined and approved before
sale. At purchase, Luna adds the customer's city, local-light phase, focus and
optional question.

## Release rule

`EDITOR_PREVIEW_ENABLED = True` exposes the editorial generator and bypasses
checkout for testing. Set it to `False` before the public paid launch.
