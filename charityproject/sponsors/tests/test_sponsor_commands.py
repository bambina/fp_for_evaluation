from django.core.management import call_command
import pytest
from sponsors.models import *
from io import StringIO


@pytest.mark.django_db
def test_populate_data():
    out = StringIO()
    call_command("populate_sponsor_data", "--country", "test_countries.csv", stdout=out)

    assert Country.objects.count() == 1
    country = Country.objects.first()
    assert country.numeric_code == "231"
    assert country.code == "ET"
    assert country.name == "Valid Case Ethiopia"

    output = out.getvalue()
    assert "row 3: ['This field must contain exactly 3 numeric digits.']" in output
    assert (
        "row 4: ['This field must contain exactly 2 uppercase alphabetic characters.']"
        in output
    )
