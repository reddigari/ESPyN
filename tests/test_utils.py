import datetime
from unittest import TestCase

from espyn.utils import (_labor_day, current_season,
                         get_week_from_date)


class UtilTests(TestCase):

    def test_labor_day(self):
        ld2020 = _labor_day(2020)
        actual = datetime.datetime(2020, 9, 7)
        self.assertEqual(ld2020, actual)

    def test_week_from_date(self):
        week1 = datetime.datetime(2020, 9, 9)
        self.assertEqual(get_week_from_date(week1), 1)
        week10 = datetime.datetime(2020, 11, 15)
        self.assertEqual(get_week_from_date(week10), 10)

    def test_current_season(self):
        today = datetime.date.today()
        year = today.year
        curr = current_season()
        self.assertTrue(year - 1 <= curr <= year)
