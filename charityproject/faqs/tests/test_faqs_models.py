import pytest
from datetime import datetime
from model_bakery import baker

from django.utils.timezone import now
from django.test import TestCase

from faqs.models import *


@pytest.mark.django_db
class FAQEntryModelTest(TestCase):
    """Test cases for the FAQEntry model."""

    def test_creation(self):
        """Test if an FAQEntry instance is created successfully."""
        entry = baker.make(FAQEntry)
        assert isinstance(entry, FAQEntry)
        assert isinstance(entry.question, str)
        assert isinstance(entry.answer, str)
        assert isinstance(entry.created_at, datetime)
        assert isinstance(entry.updated_at, datetime)
        assert entry.deleted_at is None

    def test_update(self):
        """Test if the updated_at field is updated when saving changes."""
        entry = baker.make(FAQEntry)
        assert entry.created_at is not None
        assert entry.updated_at is not None
        entry.answer = "Updated answer"
        entry.save()
        entry.refresh_from_db()
        assert entry.updated_at > entry.created_at

    def test_soft_delete(self):
        """Test if the deleted_at field can be set for soft deletion."""
        entry = baker.make(FAQEntry)
        current_time = now()
        entry.deleted_at = current_time
        entry.save()
        entry.refresh_from_db()
        assert entry.deleted_at == current_time

    def test_field_constraints(self):
        """Test constraints on model fields."""
        question_max_length = FAQEntry._meta.get_field("question").max_length
        assert question_max_length == 255
        created_at_auto_now_add = FAQEntry._meta.get_field("created_at").auto_now_add
        assert created_at_auto_now_add is True
        updated_at_auto_now = FAQEntry._meta.get_field("updated_at").auto_now
        assert updated_at_auto_now is True

    def test_meta_options(self):
        """Test the meta options."""
        verbose_name = FAQEntry._meta.verbose_name
        assert verbose_name == "FAQ Entry"
        verbose_name_plural = FAQEntry._meta.verbose_name_plural
        assert verbose_name_plural == "FAQ Entries"
        indexes = FAQEntry._meta.indexes
        assert len(indexes) == 1
        assert indexes[0].fields == ["question", "answer"]
        ordering = FAQEntry._meta.ordering
        assert ordering == ["created_at"]

    def test_str_method(self):
        """Test the string representation."""
        question = "FAQ Entry Question"
        entry = baker.prepare(FAQEntry, question=question)
        assert str(entry) == question
