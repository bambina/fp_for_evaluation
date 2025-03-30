from agent.routing import websocket_urlpatterns


def test_chat_consumer_url():
    """Test for Chat WebSocket URL configuration"""
    assert len(websocket_urlpatterns) == 1
    url_pattern = websocket_urlpatterns[0]
    assert url_pattern.pattern._route == "ws/chat/<room_name>/"
    assert url_pattern.callback.__name__ == "ChatConsumer"
