from __future__ import annotations

import calendar
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TIMEZONE = "Asia/Tokyo"
INTERVAL_UNITS = {"minutes", "hours", "days"}
FIXED_FREQUENCIES = {"hourly", "daily", "monthly"}


def normalize_schedule_config(config: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise ValueError("schedule_config must be an object")

    schedule_type = config.get("type")
    if schedule_type == "interval":
        value = _int_in_range(config.get("value"), "value", minimum=1, maximum=365)
        unit = config.get("unit")
        if unit not in INTERVAL_UNITS:
            raise ValueError("interval unit must be minutes, hours, or days")
        if unit == "minutes" and (value < 5 or value % 5 != 0):
            raise ValueError("minute intervals must be 5 minutes or longer in 5-minute steps")
        return {"type": "interval", "value": value, "unit": unit}

    if schedule_type == "fixed":
        frequency = config.get("frequency")
        if frequency not in FIXED_FREQUENCIES:
            raise ValueError("fixed frequency must be hourly, daily, or monthly")
        if frequency == "hourly":
            return {
                "type": "fixed",
                "frequency": "hourly",
                "minute": _int_in_range(config.get("minute"), "minute", minimum=0, maximum=55),
            }
        if frequency == "daily":
            return {
                "type": "fixed",
                "frequency": "daily",
                "hour": _int_in_range(config.get("hour"), "hour", minimum=0, maximum=23),
                "minute": _int_in_range(config.get("minute"), "minute", minimum=0, maximum=55),
            }
        day = config.get("day")
        if day != "last":
            day = _int_in_range(day, "day", minimum=1, maximum=28)
        return {
            "type": "fixed",
            "frequency": "monthly",
            "day": day,
            "hour": _int_in_range(config.get("hour"), "hour", minimum=0, maximum=23),
            "minute": _int_in_range(config.get("minute"), "minute", minimum=0, maximum=55),
        }

    raise ValueError("schedule type must be interval or fixed")


def compute_next_run_at(
    config: dict[str, Any],
    *,
    after: datetime,
    timezone_name: str = DEFAULT_TIMEZONE,
) -> datetime:
    normalized = normalize_schedule_config(config)
    after_utc = _as_utc(after)

    if normalized["type"] == "interval":
        delta = _interval_delta(normalized["value"], normalized["unit"])
        return after_utc + delta

    zone = _zone(timezone_name)
    local_after = after_utc.astimezone(zone)
    frequency = normalized["frequency"]
    if frequency == "hourly":
        candidate = local_after.replace(
            minute=normalized["minute"],
            second=0,
            microsecond=0,
        )
        if candidate <= local_after:
            candidate = candidate + timedelta(hours=1)
        return candidate.astimezone(timezone.utc)
    if frequency == "daily":
        candidate = local_after.replace(
            hour=normalized["hour"],
            minute=normalized["minute"],
            second=0,
            microsecond=0,
        )
        if candidate <= local_after:
            candidate = candidate + timedelta(days=1)
        return candidate.astimezone(timezone.utc)

    return _next_monthly_run(normalized, local_after).astimezone(timezone.utc)


def _interval_delta(value: int, unit: str) -> timedelta:
    if unit == "minutes":
        return timedelta(minutes=value)
    if unit == "hours":
        return timedelta(hours=value)
    return timedelta(days=value)


def _next_monthly_run(config: dict[str, Any], local_after: datetime) -> datetime:
    year = local_after.year
    month = local_after.month
    for _ in range(14):
        day = _monthly_day(year, month, config["day"])
        candidate = local_after.replace(
            year=year,
            month=month,
            day=day,
            hour=config["hour"],
            minute=config["minute"],
            second=0,
            microsecond=0,
        )
        if candidate > local_after:
            return candidate
        year, month = _next_month(year, month)
    raise ValueError("could not compute next monthly run")


def _monthly_day(year: int, month: int, day: int | str) -> int:
    if day == "last":
        return calendar.monthrange(year, month)[1]
    return int(day)


def _next_month(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    return year, month + 1


def _int_in_range(value: Any, field: str, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be an integer") from None
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{field} must be between {minimum} and {maximum}")
    if field == "minute" and parsed % 5 != 0:
        raise ValueError("minute must use 5-minute steps")
    return parsed


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _zone(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo(DEFAULT_TIMEZONE)
