# Luna v3.111 — Year Ahead natal activation label clarity

Apply `app.py` and `yearly_print_html.py` over the deployed v3.110 code. No other application files are changed.

- `app.py`: explicitly changes APP_VERSION to `v3.111` and the build label.
- `yearly_print_html.py`: groups closely spaced calculated natal targets, separates text labels and nearby plotted purple dots, adds subtle leader lines, keeps their original calculated longitude/angle and the complete report unchanged.

No natal/transit ephemeris changes, voice/prompt/provider changes, Paid Monthly changes, or narrative edits.

Verification: targeted synthetic collision tests pass; Python compilation passes; A4 WeasyPrint output for a deliberately crowded wheel was visually inspected. Live paid customer report PDF was not regenerated because no voice call was made.
