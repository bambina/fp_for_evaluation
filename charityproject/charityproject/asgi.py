"""
ASGI config for charityproject project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "charityproject.settings")

application = get_asgi_application()

# Load the routing configuration after the Django app is loaded
from agent.routing import websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": application,
        "websocket": AllowedHostsOriginValidator(  # Confirm that incoming WebSocket connections are from an allowed host
            # Add an authentication layer to WebSocket connections
            AuthMiddlewareStack(
                # Define the routing configuration for WebSocket connections
                URLRouter(websocket_urlpatterns)
            )
        ),
    }
)
