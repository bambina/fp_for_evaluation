import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestTopPage:
    @pytest.fixture
    def url(self):
        # Set the URL to the Top page
        return reverse("core:top")

    def test_top_page_status_code(self, client, url):
        """
        Test if the Top page returns a 200 status code
        """
        response = client.get(url)
        assert response.status_code == 200
        decoded_content = response.content.decode("utf-8")
        assert "The Virtual Charity" in decoded_content
        assert "Together, we can light the way." in decoded_content
