import json
from openai import OpenAI
from openai import NOT_GIVEN
import redis

from django.conf import settings
from agent.constants import *
from django.urls import reverse

from core.utils import *


class OpenAIClientService:
    _client = None

    @classmethod
    def init_client(cls):
        """Initialize the OpenAI client."""
        if cls._client is None:
            try:
                cls._client = OpenAI()
                print("OpenAI client initialized.")
            except Exception as e:
                print(f"Failed to initialize OpenAI client: {e}")

    @classmethod
    def chat_completion(cls, model, system_content, chat_history, tools=NOT_GIVEN):
        """
        Get a completion from the OpenAI model using the system content and chat history
        """
        if cls._client is None:
            cls.init_client()

        messages = cls.compose_messages_with_history(system_content, chat_history)
        return cls._client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
        )

    @classmethod
    def get_chat_completion(cls, model, system_content, user_content):
        if cls._client is None:
            cls.init_client()

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ]
        completion = cls._client.chat.completions.create(model=model, messages=messages)
        model_used = completion.model
        total_tokens = completion.usage.total_tokens
        content = completion.choices[0].message.content
        return model_used, total_tokens, content

    @classmethod
    def compose_relevant_docs(cls, search_result):
        docs = ""
        for hits in search_result:
            for hit in hits:
                faq_url = reverse("faq_detail", kwargs={"pk": hit["id"]})
                docs += RELEVANT_DOCS_FORMAT.format(
                    id=hit["id"],
                    question=hit["entity"]["question"],
                    answer=hit["entity"]["answer"],
                    link=faq_url,
                )
        return SYSTEM_CONTENT_2 + docs

    @classmethod
    def compose_child_introduction(cls, children_data, is_found):
        profiles_list = []
        for child in children_data:
            child_url = reverse("sponsors:child_detail", kwargs={"pk": child.id})
            child_info = (
                f"Name: {child.name} (ID: {child.id})\n"
                f"Age: {child.age}\n"
                f"Date of Birth: {child.date_of_birth}\n"
                f"Gender: {child.gender}\n"
                f"Country: {child.country}\n"
                f"Profile Description: {child.profile_description}\n"
                f"Link: {child_url}"
            )
            profiles_list.append(child_info)
        profiles = "\n---\n".join(profiles_list)
        system_content = SYSTEM_CONTENT_3 if is_found else SYSTEM_CONTENT_4
        return system_content + profiles

    @classmethod
    def compose_messages(cls, system_content, user_content):
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ]

    @classmethod
    def compose_messages_with_history(cls, system_content, chat_history):
        return [
            {"role": "system", "content": system_content},
            *chat_history,
        ]


class RedisChatHistoryService:
    _redis = None

    @classmethod
    def init_redis(cls):
        if cls._redis is None:
            try:
                cls._redis = redis.Redis.from_url(
                    settings.REDIS_CHAT_HISTORY_URL, decode_responses=True
                )
                print("Redis client initialized.")
            except Exception as e:
                print(f"Failed to initialize Redis client: {e}")

    @classmethod
    def save_message(cls, session_id, sender, message, timestamp, ttl_sec=60 * 60):
        log_user_test(f"{sender} message: {message}")
        if cls._redis is None:
            cls.init_redis()

        key = f"chat:{session_id}"
        # Compose the message data
        message_data = {
            "sender": sender,
            "message": message,
            "timestamp": timestamp,
        }
        # Save the message to Redis
        cls._redis.rpush(key, json.dumps(message_data))
        # Set the expiration time for the key
        cls._redis.expire(key, ttl_sec)

    @classmethod
    def get_chat_history(cls, session_id):
        if cls._redis is None:
            cls.init_redis()

        key = f"chat:{session_id}"
        chats_json_list = cls._redis.lrange(key, 0, -1)
        chat_history = [json.loads(chat_json) for chat_json in chats_json_list]
        return cls.compose_messages(chat_history)

    @classmethod
    def compose_messages(cls, chat_history):
        messages = []
        for chat in chat_history:
            messages.append({"role": chat["sender"], "content": chat["message"]})
        return messages
