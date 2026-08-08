from __future__ import annotations

"""Durable ephemeris registry for Luna Convergence.

This module is intentionally isolated from the narrative/calculation engine.  Future
monthly-engine updates should import this module rather than re-implement upload or
storage logic.

Storage model
-------------
* Local repository: ``data/ephemerides/`` beside the application code.
* Durable cloud option: mirror the same files to the Luna GitHub repository using
  the GitHub Contents API when credentials are configured.

The uploaded Astrodienst PDF is a validation/reference artifact.  Luna continues to
calculate planetary positions with Swiss Ephemeris (pyswisseph); this avoids adding
PDF text-extraction or OCR errors to the astronomical calculation path.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable
import base64
import json
import os
import re
import tempfile

import requests
from pypdf import PdfReader


EPHEMERIS_FEATURE_VERSION = "1.0"
DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data" / "ephemerides"
REGISTRY_FILENAME = "registry.json"
SUPPORTED_FRAME = "geocentric"
SUPPORTED_ZODIAC = "tropical"


@dataclass(frozen=True)
class EphemerisMetadata:
    year: int | None
    frame: str
    zodiac: str
    source: str
    original_name: str
    sha256: str
    page_count: int
    usable_by_luna: bool
    validation_message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def ephemeris_data_dir() -> Path:
    override = os.environ.get("LUNA_EPHEMERIS_DIR", "").strip()
    return Path(override).expanduser().resolve() if override else DEFAULT_DATA_DIR


def _normalise_text(value: str) -> str:
    return " ".join((value or "").replace("\u00a0", " ").split())


def inspect_ephemeris_text(
    text: str,
    *,
    original_name: str = "uploaded.pdf",
    file_sha256: str = "",
    page_count: int = 0,
) -> EphemerisMetadata:
    """Inspect Astrodienst header text without trusting the filename."""
    normal = _normalise_text(text)
    lower = normal.lower()

    year_match = re.search(r"(?:for\s+the\s+year|ephemeris\s+for\s+the\s+year)\s+(19\d{2}|20\d{2}|21\d{2})", lower)
    if not year_match:
        year_match = re.search(r"\b(19\d{2}|20\d{2}|21\d{2})\b", normal)
    year = int(year_match.group(1)) if year_match else None

    if "heliocentric" in lower:
        frame = "heliocentric"
    elif "geocentric" in lower:
        frame = "geocentric"
    else:
        frame = "unknown"

    if "sidereal" in lower:
        zodiac = "sidereal"
    elif "tropical" in lower:
        zodiac = "tropical"
    else:
        zodiac = "unknown"

    if "astrodienst" in lower and "swiss ephemeris" in lower:
        source = "Astrodienst / Swiss Ephemeris"
    elif "swiss ephemeris" in lower:
        source = "Swiss Ephemeris"
    else:
        source = "Unknown"

    reasons: list[str] = []
    if year is None:
        reasons.append("year could not be identified")
    if zodiac != SUPPORTED_ZODIAC:
        reasons.append(f"expected {SUPPORTED_ZODIAC} zodiac, found {zodiac}")
    if frame != SUPPORTED_FRAME:
        reasons.append(f"expected {SUPPORTED_FRAME} positions, found {frame}")
    if "ephemeris" not in lower:
        reasons.append("document does not identify itself as an ephemeris")

    usable = not reasons
    message = (
        "Validated for Luna: tropical geocentric ephemeris."
        if usable
        else "Not eligible as a Luna calculation reference: " + "; ".join(reasons) + "."
    )

    return EphemerisMetadata(
        year=year,
        frame=frame,
        zodiac=zodiac,
        source=source,
        original_name=Path(original_name or "uploaded.pdf").name,
        sha256=file_sha256,
        page_count=int(page_count),
        usable_by_luna=usable,
        validation_message=message,
    )


def inspect_ephemeris_pdf(pdf_bytes: bytes, original_name: str) -> EphemerisMetadata:
    if not pdf_bytes.startswith(b"%PDF"):
        return EphemerisMetadata(
            year=None,
            frame="unknown",
            zodiac="unknown",
            source="Unknown",
            original_name=Path(original_name or "uploaded.pdf").name,
            sha256=sha256(pdf_bytes).hexdigest(),
            page_count=0,
            usable_by_luna=False,
            validation_message="Not eligible: uploaded file is not a readable PDF.",
        )

    reader = PdfReader(BytesIO(pdf_bytes))
    # Astrodienst declares year/frame/zodiac in the cover and first table page.
    text = "\n".join((page.extract_text() or "") for page in reader.pages[:2])
    return inspect_ephemeris_text(
        text,
        original_name=original_name,
        file_sha256=sha256(pdf_bytes).hexdigest(),
        page_count=len(reader.pages),
    )


def _registry_path(data_dir: Path | None = None) -> Path:
    root = data_dir or ephemeris_data_dir()
    return root / REGISTRY_FILENAME


def _load_registry_document(data_dir: Path | None = None) -> dict[str, Any]:
    path = _registry_path(data_dir)
    if not path.exists():
        return {
            "registry_version": EPHEMERIS_FEATURE_VERSION,
            "updated_at_utc": None,
            "ephemerides": {},
        }
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        doc = {}
    if not isinstance(doc, dict):
        doc = {}
    doc.setdefault("registry_version", EPHEMERIS_FEATURE_VERSION)
    doc.setdefault("updated_at_utc", None)
    doc.setdefault("ephemerides", {})
    return doc


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        tmp = Path(handle.name)
        handle.write(content)
    tmp.replace(path)


def _write_registry_document(doc: dict[str, Any], data_dir: Path | None = None) -> Path:
    path = _registry_path(data_dir)
    doc["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    payload = json.dumps(doc, indent=2, sort_keys=True).encode("utf-8")
    _atomic_write(path, payload)
    return path


def list_registered_ephemerides(data_dir: Path | None = None) -> list[dict[str, Any]]:
    doc = _load_registry_document(data_dir)
    entries = list((doc.get("ephemerides") or {}).values())
    entries.sort(key=lambda row: (int(row.get("year") or 0), row.get("original_name", "")))
    return entries


def registered_years(*, usable_only: bool = True, data_dir: Path | None = None) -> list[int]:
    years: set[int] = set()
    for entry in list_registered_ephemerides(data_dir):
        if usable_only and not bool(entry.get("usable_by_luna")):
            continue
        try:
            years.add(int(entry["year"]))
        except Exception:
            continue
    return sorted(years)


def is_year_registered(year: int, *, usable_only: bool = True, data_dir: Path | None = None) -> bool:
    return int(year) in registered_years(usable_only=usable_only, data_dir=data_dir)


def store_ephemeris_pdf(
    pdf_bytes: bytes,
    original_name: str,
    *,
    data_dir: Path | None = None,
    allow_reference_only: bool = False,
) -> tuple[EphemerisMetadata, Path | None]:
    """Validate and store an ephemeris without overwriting unrelated years.

    An incompatible document can optionally be stored as a reference, but it will
    never be marked as usable by Luna's historical test controls.
    """
    metadata = inspect_ephemeris_pdf(pdf_bytes, original_name)
    if metadata.year is None:
        return metadata, None
    if not metadata.usable_by_luna and not allow_reference_only:
        return metadata, None

    root = data_dir or ephemeris_data_dir()
    root.mkdir(parents=True, exist_ok=True)
    suffix = "" if metadata.usable_by_luna else "_reference_only"
    filename = f"{metadata.year}_{metadata.zodiac}_{metadata.frame}{suffix}.pdf"
    destination = root / filename
    _atomic_write(destination, pdf_bytes)

    doc = _load_registry_document(root)
    key = str(metadata.year) if metadata.usable_by_luna else f"{metadata.year}:reference:{metadata.sha256[:12]}"
    doc["ephemerides"][key] = {
        **metadata.to_dict(),
        "stored_name": filename,
        "stored_path": f"data/ephemerides/{filename}",
        "registered_at_utc": datetime.now(timezone.utc).isoformat(),
        "feature_version": EPHEMERIS_FEATURE_VERSION,
    }
    _write_registry_document(doc, root)
    return metadata, destination


def registry_bytes(data_dir: Path | None = None) -> bytes:
    path = _registry_path(data_dir)
    if path.exists():
        return path.read_bytes()
    return json.dumps(_load_registry_document(data_dir), indent=2).encode("utf-8")


def _github_get_sha(*, repo: str, branch: str, path: str, token: str) -> str | None:
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    response = requests.get(
        url,
        params={"ref": branch},
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        timeout=20,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    payload = response.json()
    return str(payload.get("sha") or "") or None


def _github_put_file(
    *,
    repo: str,
    branch: str,
    path: str,
    content: bytes,
    token: str,
    message: str,
) -> None:
    current_sha = _github_get_sha(repo=repo, branch=branch, path=path, token=token)
    body: dict[str, Any] = {
        "message": message,
        "content": base64.b64encode(content).decode("ascii"),
        "branch": branch,
    }
    if current_sha:
        body["sha"] = current_sha
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    response = requests.put(
        url,
        json=body,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        timeout=30,
    )
    response.raise_for_status()


def persist_ephemeris_to_github(
    *,
    metadata: EphemerisMetadata,
    local_path: Path,
    repo: str,
    branch: str,
    token: str,
    data_dir: Path | None = None,
) -> list[str]:
    """Mirror the ephemeris + registry into GitHub for Streamlit-cloud durability."""
    if not (repo.strip() and branch.strip() and token.strip()):
        raise ValueError("GitHub repository, branch and token are required.")
    remote_pdf = f"data/ephemerides/{local_path.name}"
    _github_put_file(
        repo=repo.strip(),
        branch=branch.strip(),
        path=remote_pdf,
        content=local_path.read_bytes(),
        token=token.strip(),
        message=f"Register Luna ephemeris {metadata.year}",
    )
    remote_registry = f"data/ephemerides/{REGISTRY_FILENAME}"
    _github_put_file(
        repo=repo.strip(),
        branch=branch.strip(),
        path=remote_registry,
        content=registry_bytes(data_dir),
        token=token.strip(),
        message=f"Update Luna ephemeris registry for {metadata.year}",
    )
    return [remote_pdf, remote_registry]


def registry_summary(entries: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "year": row.get("year"),
            "status": "usable" if row.get("usable_by_luna") else "reference only",
            "zodiac": row.get("zodiac"),
            "frame": row.get("frame"),
            "source": row.get("source"),
            "file": row.get("stored_name"),
        }
        for row in entries
    ]
