# Monthly Homepage PDF v3

The monthly PDF now uses the Luna Convergence homepage as its design source rather than a traditional report-document template.

## Shared visual system

- Bodoni Moda heading stack;
- Josefin Sans body copy;
- IBM Plex Mono labels and evidence;
- black, white, soft grey and thin rules;
- homepage brand row and navigation strip;
- two-column editorial hero;
- black reading card with geometric outline;
- trust strips, form-style metadata fields and unrounded bordered cards.

## Rendering method

Chrome or Microsoft Edge prints an A4 HTML report using the same CSS font import as the public Streamlit app. On Windows, Luna searches automatically for Chrome and Edge. The browser receives a seven-second font-loading budget before printing.

If a supported browser is unavailable or printing fails, Luna falls back to the stable ReportLab Editorial v2 PDF rather than failing the customer order.

No additional Python package is required.
