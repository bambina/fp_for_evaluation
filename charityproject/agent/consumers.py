import json
import datetime
import logging
from typing import Dict

from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from agent.constants import *
from agent.utils import *
from agent.services import *
from semanticsearch.services import *
from agent.orchestrators import *
from core.utils import *

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Connection event handler provided by AsyncWebsocketConsumer."""
        print("Connected")
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        # Verify session ID
        if not verify_session_id(self.room_name):
            print(f"Invalid session ID attempted: {self.room_name}")
            await self.close(code=UNAUTHORIZED_ACCESS_CODE)
            return
        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        # Send a welcome message to the user
        await self.send_message_to_group(
            MESSAGE_TYPE_ASSISTANT, INITIAL_MSG, SENDER_ASSISTANT, timezone.now()
        )
        # Save assistant message to Redis
        RedisChatHistoryService.save_message(
            self.room_name, SENDER_ASSISTANT, INITIAL_MSG, timezone.now().isoformat()
        )

    async def disconnect(self, close_code):
        """Disconnection event handler provided by AsyncWebsocketConsumer."""
        print("Disconnected")
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """Message receive handler provided by AsyncWebsocketConsumer."""
        print("Received")
        try:
            data = json.loads(text_data)
            message = data.get("message")
            sender = data.get("sender")

            # Save user message to Redis
            RedisChatHistoryService.save_message(
                self.room_name, sender, message, timezone.now().isoformat()
            )
            log_search_and_child_functions(f"User message: {message}")
            # Load chat history from Redis
            chat_history = RedisChatHistoryService.get_chat_history(self.room_name)
            # Generate response using OpenAI API
            response = await OpenAIInteractionOrchestrator.generate_response(
                chat_history
            )
            res_message = response["content"]
            if res_message:
                await self.send_message_to_group(
                    MESSAGE_TYPE_ASSISTANT, res_message, SENDER_ASSISTANT, timezone.now()
                )
            # Save assistant message to Redis
            RedisChatHistoryService.save_message(
                self.room_name, SENDER_ASSISTANT, res_message, timezone.now().isoformat()
            )
            log_search_and_child_functions(f"Assistant message: {res_message}")
        except json.JSONDecodeError:
            logger.error(ERR_INVALID_JSON, exc_info=True)
        except Exception as e:
            logger.error(ERR_UNEXPECTED_LOG.format(error=str(e)), exc_info=True)
            await self.send_message_to_group(
                MESSAGE_TYPE_ERROR, ERR_MSG_UNEXPECTED, SENDER_ASSISTANT, timezone.now()
            )

    async def send_message_to_group(
        self, message_type: str, message: str, sender: str, timestamp: datetime
    ) -> None:
        """Send a message to the group channel."""
        print("Sending message to group")
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": message_type,
                "message": message,
                "sender": sender,
                "timestamp": timestamp.isoformat(),
            },
        )

    async def assistant_message(self, message_data: Dict[str, str]) -> None:
        """Send the response message to the client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": MESSAGE_TYPE_ASSISTANT,
                    "message": message_data["message"],
                    "sender": message_data["sender"],
                    "timestamp": message_data["timestamp"],
                }
            )
        )

    async def error_message(self, message_data: Dict[str, str]) -> None:
        """Send the error message to the client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": MESSAGE_TYPE_ERROR,
                    "message": message_data["message"],
                    "sender": message_data["sender"],
                    "timestamp": message_data["timestamp"],
                }
            )
        )
