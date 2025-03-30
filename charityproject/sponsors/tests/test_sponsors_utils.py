import pytest
from datetime import date
from unittest.mock import patch

from sponsors.utils import *


@pytest.fixture
def mock_today_2024_0330():
    with patch("sponsors.utils.date") as mock_date:
        mock_date.today.return_value = date(2024, 3, 30)
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
        yield


def test_calculate_age_standard(mock_today_2024_0330):
    """Should correctly calculate age for a past birthday."""
    birth_date = date(2000, 6, 1)
    assert calculate_age(birth_date) == 23


def test_calculate_age_birthday_today(mock_today_2024_0330):
    """Should return correct age when birthday is today."""
    birth_date = date(2000, 3, 30)
    assert calculate_age(birth_date) == 24


def test_calculate_age_birthday_tomorrow(mock_today_2024_0330):
    """Should subtract one year if birthday is tomorrow."""
    birth_date = date(2000, 3, 31)
    assert calculate_age(birth_date) == 23


def test_calculate_age_birthday_yesterday(mock_today_2024_0330):
    """Should not subtract a year if birthday was yesterday."""
    birth_date = date(2000, 3, 29)
    assert calculate_age(birth_date) == 24


def test_calculate_age_leap_year(mock_today_2024_0330):
    """Should correctly calculate age for Feb 29 birthdate in a leap year."""
    birth_date = date(2004, 2, 29)
    assert calculate_age(birth_date) == 20
