# Luna v3.29.1 - Weekly duplication fix

## Writing correction

- Replaces the single repeated template per aspect with three deterministic
  variants per aspect.
- Adds pair-specific Luna copy for the active 17-23 August week.
- Prevents duplicate headlines, full explanations and actions inside one week.
- Adds a regression check for identical and near-duplicate daily scripts.

## Studio correction

- Removes the second large public-page hero from the owner workspace.
- Replaces seven repeated copy expanders with one day selector and one copy box.
- Makes the final odd card span the full grid and prevents day cards splitting
  across printed pages.

The public `/weekly-view` route and unlisted `/weekly-studio` route remain
unchanged.
