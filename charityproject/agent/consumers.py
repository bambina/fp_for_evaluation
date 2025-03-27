import json, logging
from typing import Dict

from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from core.utils import *
from core.constants import *
from agent.constants import *
from agent.utils import *
from agent.services import *
from agent.orchestrators import *
from semanticsearch.services import *
from agent.models import *

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
        # Accept connection
        await self.accept()
        # Verify session ID and handle unauthorized access
        if not verify_session_id(self.room_name):
            logger.warning(
                f"Unauthorized connection attempt with session ID: {self.room_name}"
            )
            await self.close(code=UNAUTHORIZED_ACCESS_CODE)
            return
        # Add user to the chat room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        logger.info(f"New connection established in room: {self.room_name}")
        # Send a welcome message to the user
        await self.send_message_to_group(
            MESSAGE_TYPE_ASSISTANT, INITIAL_MSG, MessageSender.ASSISTANT
        )
        # Save assistant message to Redis
        RedisChatHistoryService.save_message(
            self.room_name,
            MessageSender.ASSISTANT,
            INITIAL_MSG,
            timezone.now().isoformat(),
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

            # Check if required fields are present
            if not sender or not message:
                logger.error(ERR_MISSING_FIELDS)
                await self.send_message_to_group(
                    MESSAGE_TYPE_ERROR, ERR_MSG_MISSING_FIELDS, MessageSender.ASSISTANT
                )
                return

            # Save user message to chat history
            RedisChatHistoryService.save_message(
                self.room_name, sender, message, self.current_time
            )
            await self.save_message_to_db(sender, message)
            # Generate response using OpenAI API
            response = await OpenAIInteractionOrchestrator.generate_response(
                self.room_name
            )
            # Process and save AI response
            if bot_message := response["content"]:
                await self.send_message_to_group(
                    MESSAGE_TYPE_ASSISTANT,
                    bot_message,
                    MessageSender.ASSISTANT,
                )
                # Save AI response to chat history
                RedisChatHistoryService.save_message(
                    self.room_name,
                    MessageSender.ASSISTANT,
                    bot_message,
                    self.current_time,
                )
                await self.save_message_to_db(MessageSender.ASSISTANT, bot_message)
        except json.JSONDecodeError:
            logger.error(ERR_INVALID_JSON)
            await self.send_message_to_group(
                MESSAGE_TYPE_ERROR, ERR_MSG_INVALID_JSON, MessageSender.ASSISTANT
            )
        except Exception as e:
            logger.error(ERR_UNEXPECTED_LOG.format(error=str(e)))
            await self.send_message_to_group(
                MESSAGE_TYPE_ERROR, ERR_MSG_UNEXPECTED, MessageSender.ASSISTANT
            )

    async def send_message_to_group(
        self, message_type: str, message: str, sender: str
    ) -> None:
        """Send a message to the group channel."""
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

    @database_sync_to_async
    def save_message_to_db(self, sender: str, message: str) -> None:
        ChatMessage.objects.create(
            session_id=self.room_name, sender_type=sender, content=message
        )
