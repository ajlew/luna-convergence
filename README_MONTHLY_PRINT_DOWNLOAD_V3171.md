# Luna v3.17.1 - Monthly print/download reliability hotfix

## Why

The monthly report already used a same-document browser print portal, but a browser print dialog is not a dependable delivery mechanism across mobile browsers and hosted app contexts.

## Change

- Keeps the existing `Print / Save PDF` browser control.
- Keeps JavaScript enabled explicitly for the monthly HTML renderer.
- Adds a native Streamlit `Download complete monthly PDF` control whenever the full report is authorised for printing.
- Uses the existing homepage-style monthly PDF generator.
- Falls back to the stable ReportLab PDF generator when a native HTML print engine is unavailable.
- Does not expose a PDF download on the free shortened monthly preview (`show_print=False` or `preview=True`).
- Preserves the canonical `YYYY-MM_Sign_Monthly.pdf` filename.

## Deployment

Replace `monthly_experience_v1.py` only. The accompanying regression test and README are optional for production but recommended for the repository.
