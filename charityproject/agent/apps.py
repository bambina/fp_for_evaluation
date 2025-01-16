from django.apps import AppConfig

import os, sys
from agent.services import *


class AgentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agent"

    def ready(self):
        """
        This method is called when the app is ready.
        """
        allowed_commands = {"runserver"}
        if len(sys.argv) > 1 and sys.argv[1] in allowed_commands:
            if sys.argv[1] == "runserver" and os.environ.get("RUN_MAIN") != "true":
                return
            # Load the USE model when the app is ready
            if os.environ.get("RUN_MAIN") == "true":
                print("agent app ready method called")
                OpenAIClientService.init_client()
                RedisChatHistoryService.init_redis()
