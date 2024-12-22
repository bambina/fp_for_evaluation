from model_bakery import baker
from faqs.models import *


class TestFAQEntryModel:
    """Test cases for the FAQEntry model."""

    def test_creation(self):
        entry = baker.prepare(FAQEntry)
        assert isinstance(entry, FAQEntry)
        assert isinstance(entry.title, str)
        assert isinstance(entry.question, str)
        assert isinstance(entry.answer, str)

    def test_field_constraints(self):
        title_max_length = FAQEntry._meta.get_field("title").max_length
        assert title_max_length == 50
        question_max_length = FAQEntry._meta.get_field("question").max_length
        assert question_max_length == 255
        created_at_auto_now_add = FAQEntry._meta.get_field("created_at").auto_now_add
        assert created_at_auto_now_add is True
        updated_at_auto_now = FAQEntry._meta.get_field("updated_at").auto_now
        assert updated_at_auto_now is True

    def test_str_method(self):
        title = "FAQ Entry Title"
        entry = baker.prepare(FAQEntry, title=title)
        assert str(entry) == title
