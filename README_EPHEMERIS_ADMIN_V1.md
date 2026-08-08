# Luna Ephemeris Admin v1 — durable source contract

This feature is deliberately isolated from the monthly narrator and convergence engine.

## Stable files

- `ephemeris_repository.py` — validation, registry and persistence contract.
- `ephemeris_admin.py` — hidden Streamlit admin page and historical test launcher.
- `data/ephemerides/` — uploaded reference PDFs and `registry.json`.
- `test_ephemeris_registry_contract.py` — regression test that protects the contract.

Future Luna monthly/yearly updates should **not replace or delete** `data/ephemerides/`.

## Why uploaded PDFs are references rather than calculation inputs

Astrodienst tables are excellent validation/reference documents, but extracting every table cell
from a PDF adds a second failure path. Luna continues to calculate with `pyswisseph` and uses the
uploaded yearly PDF as a durable source gate. This preserves astronomical precision while still
letting the admin register and test historic/future years explicitly.

## Streamlit Cloud durability

Runtime filesystem writes can disappear after a restart. To make Admin uploads survive deployment,
add these Streamlit Secrets:

```toml
LUNA_ADMIN_KEY = "choose-a-private-admin-key"
EPHEMERIS_GITHUB_REPO = "YOUR_GITHUB_USER/luna-convergence"
EPHEMERIS_GITHUB_BRANCH = "main"
EPHEMERIS_GITHUB_TOKEN = "YOUR_FINE_GRAINED_GITHUB_TOKEN"
```

The token should be fine-grained and limited to **Contents: Read and write** for this one repository.
Never place the token in source code.

When these are configured, the admin upload commits only:

- `data/ephemerides/<year>_tropical_geocentric.pdf`
- `data/ephemerides/registry.json`

A normal app update that replaces Python files will therefore not erase registered ephemerides.

## 2017 test

Upload the 2017 Astrodienst **tropical geocentric** PDF in Ephemeris Admin. It should validate.
Then choose:

- Year: 2017
- Sign: Sagittarius
- Month: September

and run **Generate historical monthly test**.

A heliocentric table is intentionally rejected as a Luna calculation reference.
