import pytest

from django.urls import reverse


@pytest.mark.django_db
class TestChatPage:
    @pytest.fixture
    def url(self):
        # Set the URL to the chat page
        return reverse("agent:start-chat")

    def test_chat_page_renders_without_footer(self, client, url):
        """
        Ensure the Chat page returns a 200 status code,
        contains expected content, and does not include the footer element.
        """
        response = client.get(url)
        assert response.status_code == 200
        decoded_content = response.content.decode("utf-8")
        assert "Nico, powered by OpenAI" in decoded_content
        assert "<header" in decoded_content
        assert "<footer" not in decoded_content
