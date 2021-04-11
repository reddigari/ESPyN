import math
from datetime import datetime, timedelta


def current_season() -> int:
    """Get current NFL season

     After March, returns year of upcoming season.

    :return: current NFL season
    :rtype: int
    """
    now = datetime.now()
    month, year = now.month, now.year
    if month < 4:
        year -= 1
    return year


def _labor_day(year):
    """
    Returns first Monday in September of given year
    :param year: year
    :return: first Monday in September of year
    """
    day = datetime(year, 9, 1)
    delta = timedelta(days=1)
    while day.weekday() != 0:
        day += delta
    return day


def get_week_from_date(date) -> int:
    """Get NFL week (ESPN scoring period) from date

    The year of the given date determines the relevant NFL season.
    Assumes week 1 begins the week of Labor Day and ends the following
    Wednesday. Does not cap value, so may be below 1 or above 17.

    :param date: date for which to determine NFL week
    :rtype: datetime
    :return: NFL week (ESPN scoring period)
    :rtype: int
    """
    month, year = date.month, date.year
    if month < 4:
        year -= 1
    ld = _labor_day(year)
    wk1_wed = ld + timedelta(days=2)
    days_since = (date - wk1_wed).days
    weeks_since = days_since / 7.
    week = math.floor(weeks_since) + 1
    return int(week)


def current_week() -> int:
    """Get current NFL week (ESPN scoring period)

    :return: current NFL week (ESPN scoring period)
    :rtype: int
    """
    now = datetime.now()
    return get_week_from_date(now)
