import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestFAQPage:
    @pytest.fixture
    def url(self):
        # Set the URL to the FAQ page
        return reverse("faq_list")

    def test_faq_page_status_code(self, client, url):
        """
        Test if the FAQ page returns a 200 status code
        """
        response = client.get(url)
        assert response.status_code == 200
        decoded_content = response.content.decode("utf-8")
        assert "Frequently Asked Questions" in decoded_content
