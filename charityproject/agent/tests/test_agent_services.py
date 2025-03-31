import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from agent.services import *
from conftest import *


class TestOpenAIClientService:
    @patch("agent.services.OpenAI")
    def test_get_chat_completion_with_mocked_response(self, mock_openai_class):
        """Test get_chat_completion using make_mock_chat_completion."""
        mock_client = MagicMock()
        mock_completion = make_mock_chat_completion(
            finish_reason="stop",
            content="Hello!",
            model="gpt-3.5-turbo",
            total_tokens=100,
        )
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai_class.return_value = mock_client

        OpenAIClientService._client = None
        model, total_tokens, content = OpenAIClientService.get_chat_completion(
            model="gpt-3.5-turbo", system_content="You are helpful.", user_content="Hi!"
        )

        assert model == "gpt-3.5-turbo"
        assert total_tokens == 100
        assert content == "Hello!"


class TestRedisChatHistoryService:
    session_id = "test_session"

    @pytest.fixture
    def mock_redis(self):
        with patch("agent.services.redis.Redis") as mock_redis_class:
            mock_redis_instance = MagicMock()
            mock_redis_class.from_url.return_value = mock_redis_instance
            yield mock_redis_instance

    def test_save_message_should_push_data_and_set_expiry(self, mock_redis):
        RedisChatHistoryService._redis = None
        sender = "user"
        message = "Hello"
        timestamp = datetime.now().isoformat()

        RedisChatHistoryService.save_message(
            self.session_id, sender, message, timestamp
        )

        key = f"chat:{self.session_id}"
        expected_data = json.dumps(
            {"sender": sender, "message": message, "timestamp": timestamp}
        )

        mock_redis.rpush.assert_called_once_with(key, expected_data)
        mock_redis.expire.assert_called_once_with(key, 60 * 60)

    def test_get_chat_history_returns_composed_messages(self, mock_redis):
        RedisChatHistoryService._redis = None
        key = f"chat:{self.session_id}"

        stored_messages = [
            json.dumps(
                {"sender": "user", "message": "Hi", "timestamp": "2025-01-01T00:00:00"}
            ),
            json.dumps(
                {
                    "sender": "assistant",
                    "message": "Hello!",
                    "timestamp": "2025-01-01T00:01:00",
                }
            ),
        ]
        mock_redis.lrange.return_value = stored_messages

        result = RedisChatHistoryService.get_chat_history(self.session_id)

        assert result == [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        mock_redis.lrange.assert_called_once_with(key, 0, -1)
