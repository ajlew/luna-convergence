# Windows monthly report hotfix

## Windows crash

The monthly narrative used the Unix-only unpadded-day date directive.
Windows raises `ValueError: Invalid format string` for that directive.

Date labels now use:

```python
parsed = _parse_date(value)
return f"{parsed.strftime('%B')} {parsed.day}"
```

This produces `August 1` consistently on Windows, macOS and Linux.

## Admin preview

The admin Horoscope tab previously showed the raw deterministic
calculation. The customer PDF already used the customer-first Monthly
Narrative Engine, but the on-screen preview did not.

Monthly admin reports now show the actual customer-facing narrative
first. The raw calculation remains available in a collapsed section.

## Stability

PDF creation now has an error boundary. A future generation error appears
inside Streamlit rather than terminating the complete admin application.
