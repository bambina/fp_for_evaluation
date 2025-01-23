import pytest
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from unittest.mock import patch
from unittest.mock import MagicMock

from django.urls import path

from agent.consumers import *


def get_mock_chat_completion():
    """Return a mock chat completion object."""
    mocked_completion = MagicMock()
    mocked_completion.choices = [
        MagicMock(
            finish_reason="stop",
            message=MagicMock(
                content="Hello! How can I assist you today?",
            ),
        )
    ]
    mocked_completion.model = "gpt-3.5-turbo-0125"
    mocked_completion.usage = MagicMock(total_tokens=100)
    return mocked_completion


async def setup_communicator(room_name: str) -> WebsocketCommunicator:
    """Setup a WebSocket communicator for the chat room."""
    application = URLRouter(
        [
            path(
                "ws/chat/<room_name>/",
                ChatConsumer.as_asgi(),
            ),
        ]
    )
    url = f"ws/chat/{room_name}/"
    communicator = WebsocketCommunicator(application, url)
    return communicator


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_receive_welcome_message():
    """Test receiving the welcome message."""
    session_id = generate_session_id()
    communicator = await setup_communicator(session_id)
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection failed"
    response = await communicator.receive_json_from()
    assert response["type"] == MESSAGE_TYPE_ASSISTANT
    assert response["message"] == INITIAL_MSG
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_send_receive_message():
    """Test sending and receiving a message."""
    with patch(
        "agent.services.OpenAIClientService.chat_completion"
    ) as mock_chat_completion:
        mock_object = get_mock_chat_completion()
        mock_chat_completion.return_value = mock_object
        session_id = generate_session_id()
        communicator = await setup_communicator(session_id)
        await communicator.connect()
        await communicator.receive_json_from()
        await communicator.send_json_to({"message": "hello", "sender": "user"})
        response = await communicator.receive_json_from()
        assert response["type"] == MESSAGE_TYPE_ASSISTANT
        assert response["message"] == mock_object.choices[0].message.content
        await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_deny_connect_for_invalid_session_id():
    """Test that the consumer denies connection for an invalid session ID."""
    sessioin_id = "invalid_id"
    communicator = await setup_communicator(sessioin_id)
    await communicator.connect()
    response = await communicator.receive_output()
    assert response["type"] == MESSAGE_TYPE_CLOSE
    assert response["code"] == UNAUTHORIZED_ACCESS_CODE
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_receive_empty_message_data():
    """Test receiving an empty message."""
    session_id = generate_session_id()
    communicator = await setup_communicator(session_id)
    await communicator.connect()
    await communicator.receive_json_from()
    await communicator.send_json_to({})
    response = await communicator.receive_json_from()
    assert response["type"] == MESSAGE_TYPE_ERROR
    assert response["message"] == ERR_MSG_MISSING_FIELDS
    assert response["sender"] == SENDER_ASSISTANT
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_receive_invalid_json():
    """Test receiving invalid JSON data."""
    session_id = generate_session_id()
    communicator = await setup_communicator(session_id)
    await communicator.connect()
    await communicator.receive_json_from()
    await communicator.send_to(text_data="invalid_json")
    response = await communicator.receive_json_from()
    assert response["type"] == MESSAGE_TYPE_ERROR
    assert response["message"] == ERR_MSG_INVALID_JSON
    assert response["sender"] == SENDER_ASSISTANT
    await communicator.disconnect()
