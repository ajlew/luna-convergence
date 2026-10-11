LUNA PAID TRANSIT CHAPTERS — FIRST IMPLEMENTATION
Replace these THREE files at project root:
- app.py
- paid_yearly_report.py
- monthly_transit_view.py (new)

Paid Year Ahead: 12 expandable rolling-month sections populated from existing Timing Map report stories; selected personal transits, slow-planet status and existing natal/activation wheel.
Paid Monthly: one expandable section with personal natal overlay, slow-planet contact listing and existing Monthly natal/activation wheel.
No changes to ephemeris or forecasting engine, provider-call architecture, checkout or PDF.

VERIFICATION: all modified Python files compile; shared view smoke tests pass.
NOTE: Full repository pytest is not green: test_reading_clarity.py fails importing missing text_errors from unmodified plain_readings.py. Integration must still be verified in Streamlit with actual report data. PDF unchanged.
