import pytest

from django.urls import reverse
from django.test import override_settings


@pytest.mark.django_db
class TestTopPage:
    @pytest.fixture
    def url(self):
        # Set the URL to the Top page
        return reverse("core:top")

    def test_top_page_contains_expected_content(self, client, url):
        """
        Ensure the Top page returns a 200 status code, contains expected text, and includes the footer element.
        """
        response = client.get(url)
        assert response.status_code == 200
        decoded_content = response.content.decode("utf-8")
        assert "The Virtual Charity" in decoded_content
        assert "Together, we can light the way." in decoded_content
        assert "<header" in decoded_content
        assert "<footer" in decoded_content


@pytest.mark.django_db
class Test404Page:
    @override_settings(DEBUG=False)
    def test_custom_404_page(self, client):
        """
        Test if the custom 404 page is shown for non-existent URLs
        """
        response = client.get("/non-existent-url/")
        assert response.status_code == 404
        decoded_content = response.content.decode("utf-8")
        assert "Requested resource not found." in decoded_content
        assert "<header" in decoded_content
        assert "<footer" in decoded_content
