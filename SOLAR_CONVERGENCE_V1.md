# Solar Convergence v1

## Product equation

```text
Tropical Sun position
+ four solar gates
+ local daylight movement
+ activated whole-sign house
+ customer focus
= Solar Convergence
```

## Implemented

- `solar_cycle.py` calculates the tropical Sun, solar quarter, gate timing,
  hemisphere, local season, daylight, light direction, activated house and
  focus-specific strategy.
- The daily reading receives a compact Solar Position panel.
- The monthly PDF receives a full Solar Convergence page.
- The yearly report receives four solar chapters as its annual spine.
- The paid-order form receives an optional nearest-city field.
- City and location basis are included in the Stripe order reference,
  downloadable JSON and fulfilment email.
- `/solar-year` explains the method and its historical/factual boundary.

## Accuracy boundary

The Sun's tropical position is calculated with Swiss Ephemeris. Daylight is
estimated from the resolved city latitude using a solar-declination formula.
A supported customer-entered city is labelled `customer city`; blank or
unsupported values are labelled `timezone estimate`.
