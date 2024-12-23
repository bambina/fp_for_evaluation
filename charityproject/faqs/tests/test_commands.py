from django.core.management import call_command
import pytest
from faqs.models import FAQEntry
from io import StringIO


@pytest.mark.django_db
def test_populate_data():
    out = StringIO()
    call_command("populate_data", "--faq", "test_faq.csv", stdout=out)

    assert FAQEntry.objects.count() == 1
    faq = FAQEntry.objects.first()
    assert faq.question == "Is this a normal case?"
    assert faq.answer == "Yes, this is."

    output = out.getvalue()
    assert "row 3: ['Question and answer cannot be empty']" in output
    assert "row 4: ['Question and answer cannot be empty']" in output
    assert "row 5: ['Must be 255 characters or fewer']" in output
