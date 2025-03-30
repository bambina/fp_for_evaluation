import pytest
from model_bakery import baker
from datetime import datetime, date

from django.test import TestCase

from sponsors.models import *


@pytest.mark.django_db
class CountryModelTest(TestCase):
    """Test cases for the Country model."""

    def test_creation(self):
        """Test if a Country instance is created successfully."""
        country = baker.make(Country)
        assert isinstance(country, Country)
        assert isinstance(country.name, str)
        assert isinstance(country.code, str)
        assert isinstance(country.numeric_code, str)

    def test_unique_constraints(self):
        """Test unique constraints on numeric_code, code, and name."""
        baker.make(Country, numeric_code="840", code="US", name="United States")
        with pytest.raises(Exception):
            baker.make(Country, numeric_code="840")
        with pytest.raises(Exception):
            baker.make(Country, code="US")
        with pytest.raises(Exception):
            baker.make(Country, name="United States")

    def test_field_constraints(self):
        """Test constraints on model fields."""
        numeric_code_field = Country._meta.get_field("numeric_code")
        assert numeric_code_field.max_length == 3
        assert numeric_code_field.unique is True
        code_field = Country._meta.get_field("code")
        assert code_field.max_length == 2
        assert code_field.unique is True
        name_field = Country._meta.get_field("name")
        assert name_field.max_length == 255
        assert name_field.unique is True
        assert name_field.verbose_name == "Country Name"

    def test_meta_options(self):
        """Test the meta options."""
        verbose_name = Country._meta.verbose_name
        assert verbose_name == "Country"
        verbose_name_plural = Country._meta.verbose_name_plural
        assert verbose_name_plural == "Countries"
        ordering = Country._meta.ordering
        assert ordering == ["name"]
        indexes = Country._meta.indexes
        assert any(index.fields == ["name"] for index in indexes)

    def test_str_method(self):
        """Test the string representation."""
        country = baker.prepare(Country, name="Canada")
        assert str(country) == "Canada"


@pytest.mark.django_db
class GenderModelTest(TestCase):
    """Test cases for the Gender model."""

    def test_creation(self):
        """Test if a Gender instance is created successfully."""
        gender = baker.make(Gender)
        assert isinstance(gender, Gender)
        assert isinstance(gender.name, str)

    def test_unique_constraint(self):
        """Test that the name field must be unique."""
        name = "Male"
        baker.make(Gender, name=name)
        with pytest.raises(Exception):
            baker.make(Gender, name=name)

    def test_field_constraints(self):
        """Test constraints on model fields."""
        name_max_length = Gender._meta.get_field("name").max_length
        assert name_max_length == 50
        unique = Gender._meta.get_field("name").unique
        assert unique is True

    def test_meta_options(self):
        """Test the meta options."""
        ordering = Gender._meta.ordering
        assert ordering == ["name"]

    def test_str_method(self):
        """Test the string representation."""
        gender = baker.prepare(Gender, name="Female")
        assert str(gender) == "Female"


@pytest.mark.django_db
class ChildModelTest(TestCase):
    """Test cases for the Child model."""

    def test_creation(self):
        """Test if a Child instance is created successfully."""
        child = baker.make(Child)
        assert isinstance(child, Child)
        assert isinstance(child.name, str)
        assert isinstance(child.age, int)
        assert isinstance(child.gender, Gender)
        assert isinstance(child.country, Country)
        assert isinstance(child.profile_description, str)
        assert isinstance(child.date_of_birth, date)
        assert isinstance(child.created_at, datetime)
        assert isinstance(child.updated_at, datetime)
        assert child.deleted_at is None

    def test_update(self):
        """Test if the updated_at field is updated when saving changes."""
        child = baker.make(Child)
        child.profile_description = "Updated description"
        child.save()
        child.refresh_from_db()
        assert child.updated_at > child.created_at

    def test_field_constraints(self):
        """Test constraints on model fields."""
        name_max_length = Child._meta.get_field("name").max_length
        assert name_max_length == MAX_CHILD_NAME_LEN
        profile_description_field = Child._meta.get_field("profile_description")
        assert profile_description_field.max_length == MAX_CHILD_PROFILE_LEN
        assert profile_description_field.blank is True
        image_field = Child._meta.get_field("image")
        assert image_field.blank is True
        assert image_field.null is True

    def test_meta_options(self):
        """Test the meta options."""
        ordering = Child._meta.ordering
        assert ordering == ["name"]
        verbose_name = Child._meta.verbose_name
        assert verbose_name == "Child"
        verbose_name_plural = Child._meta.verbose_name_plural
        assert verbose_name_plural == "Children"
        index_fields = [tuple(index.fields) for index in Child._meta.indexes]
        assert ("name",) in index_fields
        assert ("country",) in index_fields

    def test_str_method(self):
        """Test the string representation."""
        child = baker.prepare(
            Child,
            name="Maria",
            age=7,
            country=baker.make(Country, name="Kenya"),
            date_of_birth=date(2017, 5, 20),
        )
        assert str(child) == "Maria (7), Kenya, 2017-05-20"
