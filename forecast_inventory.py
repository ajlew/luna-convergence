from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from typing import Iterable, Sequence

from luna_voice import VOICE_VERSION


INVENTORY_VERSION = "Forecast Inventory v1.0"
EDITORIAL_STATUSES = (
    "draft",
    "calculated",
    "narrative generated",
    "editorially reviewed",
    "approved",
    "published",
    "archived",
)


@dataclass(frozen=True)
class ForecastRecord:
    key: str
    report_type: str
    sign: str
    start_date: str
    end_date: str
    timezone_basis: str
    city_basis: str
    main_focus: str
    status: str
    calculation_version: str
    arc_version: str
    voice_version: str
    generated_at: str
    calculation_hash: str
    payload: dict

    def to_dict(self) -> dict:
        return asdict(self)


def _jsonable(value: object) -> object:
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _hash_payload(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _record(
    *,
    report_type: str,
    sign: str,
    start: date,
    end: date,
    timezone_name: str,
    city: str,
    main_focus: str,
    status: str,
    payload: dict,
) -> ForecastRecord:
    if status not in EDITORIAL_STATUSES:
        raise ValueError(f"Unsupported editorial status: {status}")
    calculation_hash = _hash_payload(payload)
    key = f"{report_type}:{sign.lower()}:{start.isoformat()}:{end.isoformat()}:{calculation_hash}"
    arc_version = "daily trigger v3" if report_type == "daily" else (
        "monthly arc v2.8" if report_type == "monthly" else "yearly game map v1.0"
    )
    return ForecastRecord(
        key=key,
        report_type=report_type,
        sign=sign,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        timezone_basis=timezone_name,
        city_basis=city,
        main_focus=main_focus,
        status=status,
        calculation_version="Swiss Ephemeris / whole-sign v1",
        arc_version=arc_version,
        voice_version=VOICE_VERSION,
        generated_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        calculation_hash=calculation_hash,
        payload=payload,
    )


def build_daily_core(
    sign: str,
    reading_date: date,
    timezone_name: str,
    city: str = "",
    status: str = "calculated",
) -> ForecastRecord:
    from customer_experience import HOUSE_VOICE, free_daily_reading
    from daily_narrative_v3 import build_daily_narrative

    reading = free_daily_reading(sign, reading_date, timezone_name)
    narrative = build_daily_narrative(
        reading,
        sign=sign,
        reading_date=reading_date,
        timezone_name=timezone_name,
        house_voice=HOUSE_VOICE,
    )
    payload = {
        "reading": _jsonable(reading),
        "narrative": _jsonable(narrative),
    }
    return _record(
        report_type="daily",
        sign=sign,
        start=reading_date,
        end=reading_date,
        timezone_name=timezone_name,
        city=city,
        main_focus="Daily overview",
        status=status,
        payload=payload,
    )


def build_monthly_core(
    sign: str,
    year: int,
    month: int,
    timezone_name: str,
    city: str = "",
    main_focus: str = "General overview",
    status: str = "calculated",
) -> ForecastRecord:
    from calendar import monthrange
    from monthly_narrative_v1 import build_monthly_narrative
    from synthesis import period_report

    start = date(year, month, 1)
    end = date(year, month, monthrange(year, month)[1])
    result = period_report(
        sign,
        start,
        end,
        timezone_name,
        start.strftime("%B %Y"),
        transition_count=12,
        nearest_city=city,
        main_focus=main_focus,
    )
    narrative = build_monthly_narrative(result, main_focus=main_focus)
    payload = {
        "result": _jsonable(result),
        "narrative": _jsonable(narrative),
    }
    return _record(
        report_type="monthly",
        sign=sign,
        start=start,
        end=end,
        timezone_name=timezone_name,
        city=city,
        main_focus=main_focus,
        status=status,
        payload=payload,
    )


def build_yearly_core(
    sign: str,
    year: int,
    timezone_name: str,
    city: str = "",
    main_focus: str = "General year ahead",
    status: str = "calculated",
) -> ForecastRecord:
    from synthesis import period_report

    start = date(year, 1, 1)
    end = date(year, 12, 31)
    result = period_report(
        sign,
        start,
        end,
        timezone_name,
        str(year),
        transition_count=12,
        nearest_city=city,
        main_focus=main_focus,
    )
    payload = {"result": _jsonable(result)}
    return _record(
        report_type="yearly",
        sign=sign,
        start=start,
        end=end,
        timezone_name=timezone_name,
        city=city,
        main_focus=main_focus,
        status=status,
        payload=payload,
    )


def build_inventory(
    report_type: str,
    signs: Sequence[str],
    *,
    year: int,
    timezone_name: str,
    city: str = "",
    months: Sequence[int] = (),
    start_date: date | None = None,
    end_date: date | None = None,
    main_focus: str = "General overview",
    status: str = "calculated",
) -> tuple[ForecastRecord, ...]:
    records: list[ForecastRecord] = []
    if report_type == "daily":
        if start_date is None or end_date is None:
            raise ValueError("Daily inventory requires a start and end date")
        if end_date < start_date:
            raise ValueError("End date must not precede start date")
        if (end_date - start_date).days > 31:
            raise ValueError("Daily batches are limited to 32 days per generation")
        current = start_date
        while current <= end_date:
            for sign in signs:
                records.append(build_daily_core(sign, current, timezone_name, city, status))
            current += timedelta(days=1)
    elif report_type == "monthly":
        selected_months = tuple(months) or tuple(range(1, 13))
        for sign in signs:
            for month in selected_months:
                records.append(
                    build_monthly_core(
                        sign,
                        year,
                        int(month),
                        timezone_name,
                        city,
                        main_focus,
                        status,
                    )
                )
    elif report_type == "yearly":
        for sign in signs:
            records.append(
                build_yearly_core(
                    sign,
                    year,
                    timezone_name,
                    city,
                    main_focus if main_focus != "General overview" else "General year ahead",
                    status,
                )
            )
    else:
        raise ValueError(f"Unsupported report type: {report_type}")
    return tuple(records)


def inventory_document(records: Iterable[ForecastRecord]) -> dict:
    items = [record.to_dict() for record in records]
    return {
        "inventory_version": INVENTORY_VERSION,
        "record_count": len(items),
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "records": items,
    }


def inventory_json(records: Iterable[ForecastRecord]) -> str:
    return json.dumps(inventory_document(records), ensure_ascii=False, indent=2)


def save_inventory(records: Iterable[ForecastRecord], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(inventory_json(records), encoding="utf-8")
    return output
