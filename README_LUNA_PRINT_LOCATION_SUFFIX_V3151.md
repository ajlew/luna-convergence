# Luna v3.15.1 - Print location suffix

Small print-only refinement. No forecast, solar, trajectory, payment, admin, or narrative logic is changed.

The browser print/save-PDF title now appends the resolved local-light city when available:

- `2026-09_Sagittarius_Monthly_London.pdf`
- `2026-09_Sagittarius_Monthly_Sydney.pdf`
- `2026-09_Sagittarius_Monthly_New_York.pdf`

If no resolved city is available, Luna preserves the previous filename format:

- `2026-09_Sagittarius_Monthly.pdf`

The report page itself continues to show the full timezone such as `Europe/London`.
