import json
from openai import OpenAI
from openai import NOT_GIVEN
import redis

from django.conf import settings
from agent.constants import *
from django.urls import reverse

from core.utils import *


class OpenAIClientService:
    """Service class for interacting with the OpenAI chat completion API."""

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
        """Compose formatted content from search results, selecting most relevant FAQs."""
        processed_faq_ids = set()
        unique_faqs = []
        formatted_content = ""
        max_faqs = 5
        # Collect unique FAQs from all search results
        for result_group in search_result:
            for faq in result_group:
                if faq["id"] not in processed_faq_ids:
                    processed_faq_ids.add(faq["id"])
                    unique_faqs.append(faq)
        # Sort FAQs by distance
        sorted_faqs = sorted(unique_faqs, key=lambda x: x["distance"], reverse=True)
        # Format top N FAQs with their details and URLs
        for faq in sorted_faqs[:max_faqs]:
            faq_url = reverse("faqs:faq_detail", kwargs={"pk": faq["id"]})
            formatted_content += RELEVANT_DOCS_FORMAT.format(
                id=faq["id"],
                question=faq["entity"]["question"],
                answer=faq["entity"]["answer"],
                link=faq_url,
            )
        return SYSTEM_CONTENT_2 + formatted_content

    @classmethod
    def compose_child_introduction(
        cls, children_data, is_found, semantic_search_keyword
    ):
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
        if is_found:
            note = (
                SEMANTIC_SEARCH_NOTE.format(keyword=semantic_search_keyword)
                if semantic_search_keyword
                else FILTERED_SEARCH_NOTE
            )
            system_content = SYSTEM_CONTENT_3.format(
                num_children=len(profiles_list), note=note
            )
        else:
            system_content = SYSTEM_CONTENT_4
        print(f"System content: {system_content + profiles}")
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
    """Service class for storing and retrieving chat history."""

    _redis = None

    @classmethod
    def init_redis(cls):
        """Initialize the Redis client."""
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
        """
        Save a chat message to Redis.
        """
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
        """
        Retrieve the chat history for a given session.
        """
        if cls._redis is None:
            cls.init_redis()

        key = f"chat:{session_id}"
        chats_json_list = cls._redis.lrange(key, 0, -1)
        chat_history = [json.loads(chat_json) for chat_json in chats_json_list]
        return cls.compose_messages(chat_history)

    @classmethod
    def compose_messages(cls, chat_history):
        """
        Convert chat history to a format compatible with chat completion models.
        """
        messages = []
        for chat in chat_history:
            messages.append({"role": chat["sender"], "content": chat["message"]})
        return messages
