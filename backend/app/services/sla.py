"""Business-day SLA calculation service.

Calculates SLA due dates skipping weekends (Saturday & Sunday) and public holidays.
Holidays can be national (applicable across all regions) or regional.
Unit-tested edge cases: weekends, consecutive holidays, regional holidays.
"""

from datetime import UTC, date, datetime, time, timedelta

from app.models.entities import HolidayCalendar
from sqlalchemy.orm import Session


def get_holiday_dates(
    db: Session,
    start_date: date,
    end_date: date,
    region_id: int | None = None,
) -> set[date]:
    """Fetch all holiday dates between start and end date for region or national."""
    # Convert dates to range
    start_dt = datetime.combine(start_date, time.min, tzinfo=UTC)
    end_dt = datetime.combine(end_date, time.max, tzinfo=UTC)

    query = db.query(HolidayCalendar).filter(
        HolidayCalendar.date >= start_dt,
        HolidayCalendar.date <= end_dt,
    )

    if region_id is not None:
        # National holidays (region_id IS NULL) OR holidays for this specific region
        query = query.filter(
            (HolidayCalendar.region_id == None) | (HolidayCalendar.region_id == region_id)  # noqa: E711
        )
    else:
        query = query.filter(HolidayCalendar.region_id == None)  # noqa: E711

    holidays = query.all()
    return {h.date.date() for h in holidays}


def is_business_day(check_date: date, holiday_set: set[date]) -> bool:
    """Return True if Monday-Friday and not in holiday_set."""
    if check_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    if check_date in holiday_set:
        return False
    return True


def calculate_due_date(
    start_datetime: datetime,
    sla_business_days: int,
    db: Session | None = None,
    region_id: int | None = None,
    explicit_holidays: set[date] | None = None,
) -> datetime:
    """Calculate deadline given a start datetime and business days SLA.

    If sla_business_days <= 0, due_at is the start_datetime.
    Otherwise, counts forward strictly by business days.
    Preserves start_datetime time-of-day and timezone.
    """
    if sla_business_days <= 0:
        return start_datetime

    # Estimate safe window for fetching holidays
    max_calendar_days = sla_business_days * 3 + 30
    start_d = start_datetime.date()
    end_d = start_d + timedelta(days=max_calendar_days)

    holiday_set: set[date] = set()
    if explicit_holidays is not None:
        holiday_set = explicit_holidays
    elif db is not None:
        holiday_set = get_holiday_dates(db, start_d, end_d, region_id=region_id)

    curr_d = start_d
    added_days = 0

    while added_days < sla_business_days:
        curr_d += timedelta(days=1)
        if is_business_day(curr_d, holiday_set):
            added_days += 1

    return datetime.combine(
        curr_d,
        start_datetime.time(),
        tzinfo=start_datetime.tzinfo or UTC,
    )
