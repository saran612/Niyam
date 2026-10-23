"""Tests for Business-Day SLA calculation edge cases."""

from datetime import UTC, date, datetime

from app.services.sla import calculate_due_date, is_business_day


def test_business_day_detection():
    # 2026-10-23 is Friday
    fri = date(2026, 10, 23)
    sat = date(2026, 10, 24)
    sun = date(2026, 10, 25)
    mon = date(2026, 10, 26)

    assert is_business_day(fri, set()) is True
    assert is_business_day(sat, set()) is False
    assert is_business_day(sun, set()) is False
    assert is_business_day(mon, set()) is True

    # Holiday on Monday
    assert is_business_day(mon, {mon}) is False


def test_calculate_due_date_across_weekend():
    # Start on Friday 10:00 UTC, 1 business day -> should land on Monday 10:00 UTC
    start = datetime(2026, 10, 23, 10, 0, tzinfo=UTC)
    due = calculate_due_date(start, sla_business_days=1, explicit_holidays=set())
    assert due.date() == date(2026, 10, 26)
    assert due.time() == start.time()


def test_calculate_due_date_across_holiday():
    # Start on Thursday 10:00, 2 business days, Friday is a holiday
    # Friday 2026-10-23 is holiday -> Sat/Sun skip -> Due on Tuesday 2026-10-27
    start = datetime(2026, 10, 22, 10, 0, tzinfo=UTC)
    holiday = date(2026, 10, 23)
    due = calculate_due_date(start, sla_business_days=2, explicit_holidays={holiday})
    assert due.date() == date(2026, 10, 27)


def test_calculate_due_date_zero_or_negative():
    start = datetime(2026, 10, 22, 10, 0, tzinfo=UTC)
    assert calculate_due_date(start, 0) == start
    assert calculate_due_date(start, -5) == start
