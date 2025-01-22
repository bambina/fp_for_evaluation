import json
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
from core.constants import *

logger = logging.getLogger(PROJECT_LOGGER_NAME)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time chat functionality.
    """

    @property
    def current_time(self) -> str:
        """Return current time in ISO format."""
        return timezone.now().isoformat()

    async def connect(self):
        """Connection event handler provided by AsyncWebsocketConsumer."""
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        # Verify session ID and handle unauthorized access
        if not verify_session_id(self.room_name):
            logger.warning(
                f"Unauthorized connection attempt with session ID: {self.room_name}"
            )
            await self.close(code=UNAUTHORIZED_ACCESS_CODE)
            return
        # Add user to the chat room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        logger.info(f"New connection established in room: {self.room_name}")
        # Send a welcome message to the user
        await self.send_message_to_group(
            MESSAGE_TYPE_ASSISTANT, INITIAL_MSG, SENDER_ASSISTANT
        )
        # Save assistant message to Redis
        RedisChatHistoryService.save_message(
            self.room_name, SENDER_ASSISTANT, INITIAL_MSG, timezone.now().isoformat()
        )

    async def disconnect(self, close_code):
        """Disconnection event handler provided by AsyncWebsocketConsumer."""
        logger.info(
            f"Client disconnecting from room {self.room_name} with code: {close_code}"
        )
        # Remove user from the group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """Message receive handler provided by AsyncWebsocketConsumer."""
        logger.debug("Received WebSocket message")
        try:
            # Parse incoming message
            data = json.loads(text_data)
            message = data.get("message")
            sender = data.get("sender")
            # Save user message to chat history
            RedisChatHistoryService.save_message(
                self.room_name, sender, message, self.current_time
            )
            # Generate response using OpenAI API
            response = await OpenAIInteractionOrchestrator.generate_response(
                self.room_name
            )
            # response = {"content": "Hello, how can I help you?"}
            # Process and save AI response
            if bot_message := response["content"]:
                await self.send_message_to_group(
                    MESSAGE_TYPE_ASSISTANT,
                    bot_message,
                    SENDER_ASSISTANT,
                )
                # Save AI response to chat history
                RedisChatHistoryService.save_message(
                    self.room_name,
                    SENDER_ASSISTANT,
                    bot_message,
                    self.current_time,
                )
        except json.JSONDecodeError:
            logger.error(ERR_INVALID_JSON, exc_info=True)
        except Exception as e:
            logger.error(ERR_UNEXPECTED_LOG.format(error=str(e)), exc_info=True)
            await self.send_message_to_group(
                MESSAGE_TYPE_ERROR, ERR_MSG_UNEXPECTED, SENDER_ASSISTANT
            )

    async def send_message_to_group(
        self, message_type: str, message: str, sender: str
    ) -> None:
        """Send a message to the group channel."""
        print("Sending message to group")
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": message_type,
                "message": message,
                "sender": sender,
                "timestamp": self.current_time,
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
