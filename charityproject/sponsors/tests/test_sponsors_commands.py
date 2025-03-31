import pytest
from io import StringIO
from datetime import datetime

from django.core.management import call_command

from sponsors.models import *


@pytest.mark.django_db
def test_populate_sponsor_data():
    """
    Test the 'populate_sponsor_data' custom management command in test mode.
    """
    out = StringIO()
    call_command("populate_sponsor_data", "--test", stdout=out)

    # Test Country Table
    assert Country.objects.count() == 2
    country = Country.objects.get(name="Valid Case Ethiopia")
    assert country.numeric_code == "231"
    assert country.code == "ET"
    assert country.name == "Valid Case Ethiopia"

    # Test Gender Table
    assert Gender.objects.count() == 2
    male = Gender.objects.get(name="Male")
    assert male.name == "Male"

    # Test Child Table
    assert Child.objects.count() == 1
    child = Child.objects.first()
    assert child.name == "Liam"
    assert child.gender == Gender.objects.get(name="Male")
    assert child.country == Country.objects.get(name="Kenya")
    assert child.profile_description == "Valid case"
    assert child.date_of_birth == datetime(2021, 6, 12).date()

    output = out.getvalue()
    assert "row 4: ['This field must contain exactly 3 numeric digits.']" in output
    assert (
        "row 5: ['This field must contain exactly 2 uppercase alphabetic characters.']"
        in output
    )
    assert (
        "row 4: [\"Duplicate name detected: 'Duplicate names for name are invalid'\"]"
        in output
    )
    assert "row 5: ['Must be 50 characters or fewer']" in output
    assert "row 3: ['Must be 255 characters or fewer']" in output
    assert "row 4: Gender matching query does not exist." in output
    assert "row 5: Country matching query does not exist." in output
    assert (
        "row 6: [\"Invalid date format: ''. Expected format: YYYY-MM-DD.\"]" in output
    )
    assert (
        "row 7: [\"The date '1900-06-12' cannot be earlier than 2000-01-01.\"]"
        in output
    )
