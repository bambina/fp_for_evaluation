import pytest

from model_bakery import baker

from django.urls import reverse
from faqs.models import *


@pytest.mark.django_db
class TestFAQListPage:
    @pytest.fixture
    def url(self):
        # FAQ List page URL
        return reverse("faq_list")

    def test_faq_page_contains_expected_content(self, client, url):
        """
        Test if the FAQ List page returns a 200 status code,
        contains expected text, and includes the header and footer elements.
        """
        response = client.get(url)
        assert response.status_code == 200
        decoded_content = response.content.decode("utf-8")
        assert "Frequently Asked Questions" in decoded_content
        assert "<header" in decoded_content
        assert "<footer" in decoded_content


@pytest.mark.django_db
class TestFAQDetailPage:
    @pytest.fixture
    def faq(self):
        # Create a test FAQ instance using baker
        return baker.make(
            FAQEntry,
            question="What is this project about?",
            answer="This is a test FAQ entry.",
        )

    @pytest.fixture
    def url(self, faq):
        # Generate the URL for the FAQ detail page
        return reverse("faq_detail", kwargs={"pk": faq.pk})

    def test_faq_detail_page_contains_expected_content(self, client, url, faq):
        """
        Ensure the FAQ detail page returns 200, shows the question and answer,
        and includes the header and footer elements.
        """
        response = client.get(url)
        assert response.status_code == 200

        decoded_content = response.content.decode("utf-8")
        assert faq.question in decoded_content
        assert faq.answer in decoded_content
        assert "<header" in decoded_content
        assert "<footer" in decoded_content
