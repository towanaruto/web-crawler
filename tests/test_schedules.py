from datetime import datetime, timezone

import pytest

from src.scheduler.schedules import compute_next_run_at, normalize_schedule_config


def test_interval_minutes_must_use_five_minute_steps():
    with pytest.raises(ValueError):
        normalize_schedule_config({"type": "interval", "value": 3, "unit": "minutes"})


def test_compute_interval_next_run_at():
    after = datetime(2026, 5, 30, 0, 0, tzinfo=timezone.utc)

    result = compute_next_run_at(
        {"type": "interval", "value": 2, "unit": "hours"},
        after=after,
    )

    assert result == datetime(2026, 5, 30, 2, 0, tzinfo=timezone.utc)


def test_compute_hourly_fixed_next_run_at_in_jst():
    after = datetime(2026, 5, 30, 0, 57, tzinfo=timezone.utc)

    result = compute_next_run_at(
        {"type": "fixed", "frequency": "hourly", "minute": 0},
        after=after,
        timezone_name="Asia/Tokyo",
    )

    assert result == datetime(2026, 5, 30, 1, 0, tzinfo=timezone.utc)


def test_compute_daily_fixed_next_run_at_in_jst():
    after = datetime(2026, 5, 30, 0, 0, tzinfo=timezone.utc)

    result = compute_next_run_at(
        {"type": "fixed", "frequency": "daily", "hour": 8, "minute": 30},
        after=after,
        timezone_name="Asia/Tokyo",
    )

    assert result == datetime(2026, 5, 30, 23, 30, tzinfo=timezone.utc)


def test_compute_month_end_fixed_next_run_at_in_jst():
    after = datetime(2026, 5, 30, 0, 0, tzinfo=timezone.utc)

    result = compute_next_run_at(
        {"type": "fixed", "frequency": "monthly", "day": "last", "hour": 10, "minute": 0},
        after=after,
        timezone_name="Asia/Tokyo",
    )

    assert result == datetime(2026, 5, 31, 1, 0, tzinfo=timezone.utc)
