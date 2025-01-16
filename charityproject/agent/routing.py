from django.urls import path

from agent import consumers

# Routing for websocket consumers
# Prefix the URL pattern with "ws" to indicate that this is a websocket URL
websocket_urlpatterns = [
    path(
        "ws/chat/<room_name>/",
        consumers.ChatConsumer.as_asgi(),
    ),
]
