# Full Report Print Portal v2.5

## Observed failure

Browser printing from the Streamlit Reports page produced a one-page PDF
containing only a lower section of the report. A full-page screen capture
produced three pages and preserved the whole customer reading.

This indicates that the browser was paginating Streamlit's constrained
application container rather than the complete report flow.

## Correction

Before printing, Luna now:

1. clones the complete monthly or yearly report;
2. appends the clone directly to the document body;
3. removes the print controls from the clone;
4. opens every evidence disclosure in the clone;
5. applies the selected A4/A3 and portrait/landscape page settings;
6. hides the Streamlit application only for the print operation;
7. prints the top-level clone with unrestricted height and visible overflow;
8. removes the temporary clone after printing.

This avoids clipping by Streamlit containers and preserves selectable text,
web fonts, page breaks and the full evidence appendix.

## Screen capture

Screen capture remains useful for editorial review because it records the
complete scrolling page. It is not the preferred customer delivery method:
it can include website controls, usually rasterises the page and produces
lower-quality text than native browser printing.

## Products

The print portal is used by both:

- Monthly customer reports
- Year-ahead customer reports
