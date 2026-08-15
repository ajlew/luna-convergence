# Luna v3.28.1 — Monthly Sky Map Render Fix

## Why this patch exists
The v3.28 free Monthly page generated the correct SVG wheel, but the live Streamlit `st.html` rendering layer sanitised the inline `<svg>` markup. The section title, introduction and metadata remained visible while the circular wheel disappeared.

## Fix
- Keep the existing `monthly_sky_map.py` calculation and SVG generator unchanged.
- Base64-encode the generated SVG and render it through a normal `<img src="data:image/svg+xml;base64,...">` element inside the same Monthly section.
- Add responsive `.luna-sky-wheel-image` CSS.
- Preserve the exact free Monthly order: Where the sky is gathering → Monthly sky snapshot → How August unfolds.
- No paid Monthly, Natal, Daily, Solar Year, checkout, fulfilment, PDF, or astronomy logic removed.

## QA
119/119 tests pass.
