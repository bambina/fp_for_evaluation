from django.urls import reverse, resolve

from agent.views import start_chat


def test_agent_start_chat_url():
    """Test for start chat page URL configuration in agent app"""
    path = reverse("agent:start-chat")
    assert path == "/chat/start/"
    assert resolve(path).func == start_chat
