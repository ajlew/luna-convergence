# Luna Convergence v2.9.7.3 - Download-Only Report Controls

The browser-print controls were removed because they were redundant and unreliable.

## Monthly

The `A4 portrait / Print or save report` block no longer renders. The remaining
`Download searchable A4 Monthly PDF` control is the sole customer output action and
uses Streamlit's primary button style, which is black under Luna's theme.

## Daily

The `Print Daily Reading` and `Print Full Daily + Evidence` controls no longer render.
The two searchable PDF downloads remain and both use the black primary style.

## Unchanged

- Daily and Monthly calculations
- Monthly narrative format
- PDF generation and canonical filenames
- A4 layout and searchable text
- Yearly hidden status
