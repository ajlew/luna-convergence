from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, (list, tuple, set)):
        return bool(value)
    return True


def assemble_report_bundle(
    report_type: str,
    *,
    main: Mapping[str, Any] | None,
    sections: Mapping[str, Any],
    required_sections: tuple[str, ...],
) -> dict[str, Any]:
    """Describe one publishable report without merging its calculated evidence.

    Provider requests may be divided into small paced calls.  The renderer uses
    this manifest as the single publication gate, so a successful lower section
    can never appear beneath a failed main story.
    """
    component_status = {"main": _present(main)}
    component_status.update({name: _present(value) for name, value in sections.items()})
    missing = tuple(
        name for name in ("main", *required_sections)
        if not component_status.get(name, False)
    )
    hashes = {
        "main": str((main or {}).get("facts_hash") or ""),
        **{
            name: str(value.get("facts_hash") or "")
            for name, value in sections.items()
            if isinstance(value, Mapping)
        },
    }
    identity_payload = json.dumps(
        {
            "report_type": report_type,
            "component_hashes": hashes,
            "required_sections": required_sections,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "report_type": report_type,
        "complete": not missing,
        "status": "complete" if not missing else "partial",
        "missing_sections": missing,
        "component_status": component_status,
        "component_hashes": hashes,
        "report_id": hashlib.sha256(identity_payload.encode("utf-8")).hexdigest(),
        "main": dict(main or {}),
        "sections": dict(sections),
    }

