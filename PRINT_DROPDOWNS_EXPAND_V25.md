# Print dropdown expansion

The customer screen remains sparse: reference and evidence disclosures
stay closed until the reader opens them.

During printing, Luna clones the complete report and opens every
`<details>` element in that temporary print copy. This includes:

- Why Luna sees this
- Solar Convergence
- Key dates and planetary timing
- Full technical evidence
- any nested disclosures added later

Expansion runs twice: once when the clone is created and again on the
next animation frame. This prevents nested or browser-restored disclosure
state from remaining closed during pagination.

The behaviour applies to both Monthly and Year-ahead reports, whether
printing starts from Luna's button or from the browser's Print command.
After printing, the temporary copy is removed and the on-screen sections
remain collapsed.
