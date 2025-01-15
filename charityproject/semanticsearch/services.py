import os, json
from typing import List

import numpy as np
import tensorflow_hub as hub
import tensorflow, tensorflow_text  # For loading the USE model
from pymilvus import MilvusClient, AnnSearchRequest, WeightedRanker
from openai import OpenAI
from openai import NOT_GIVEN
import redis

from django.conf import settings
from semanticsearch.constants import *


class USEModelService:
    _model = None

    @classmethod
    def load_model(cls):
        """
        Load the USE model from the directory specified in the settings.
        """
        if cls._model is None:
            if os.path.exists(settings.USE_MODEL_DIR):
                # Load the USE model
                print("Loading the USE model...")
                cls._model = hub.load(settings.USE_MODEL_DIR)
                print("USE model loaded successfully!")
            else:
                print(f"USE model directory not found: {settings.USE_MODEL_DIR}")

    @classmethod
    def get_vector_representation(cls, query_list: List[str]) -> np.ndarray:
        """
        Get the vector representation of a list of query strings using the USE model.
        """
        if cls._model is None:
            cls.load_model()

        return cls._model(query_list).numpy()


class MilvusClientService:
    _client = None

    @classmethod
    def init_client(cls):
        if cls._client is None:
            try:
                cls._client = MilvusClient(settings.VECTOR_DB_FILE)
                print("Milvus client initialized.")
            except Exception as e:
                print(f"Failed to initialize Milvus client: {e}")

    @classmethod
    def hybrid_search(cls, query_vectors: np.ndarray, top_k: int = 3):
        if cls._client is None:
            cls.init_client()

        return cls._client.hybrid_search(
            collection_name=FAQ_COLLECTION_NAME,
            reqs=[
                AnnSearchRequest(
                    data=query_vectors,
                    anns_field="title_vector",
                    param={"metric_type": "IP", "params": {"nprobe": 10}},
                    limit=top_k,
                ),
                AnnSearchRequest(
                    data=query_vectors,
                    anns_field="description_vector",
                    param={"metric_type": "IP", "params": {"nprobe": 10}},
                    limit=top_k,
                ),
            ],
            ranker=WeightedRanker(0.7, 0.3),
            output_fields=["title", "description"],
            limit=top_k,
        )


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
                docs += RELEVANT_DOCS_FORMAT.format(
                    title=hit["entity"]["title"],
                    description=hit["entity"]["description"],
                )
        return SYSTEM_CONTENT_2 + docs

    @classmethod
    def compose_child_introduction(cls, child_data):
        child_info = (
            f"Name: {child_data.name}\n"
            f"Age: {child_data.age}\n"
            f"Country: {child_data.country}\n"
            f"Profile Description: {child_data.profile_description}\n"
            f"Date of Birth: {child_data.date_of_birth}\n"
            f"Link: https://example.com/children/{child_data.id}"
        )
        return SYSTEM_CONTENT_3 + child_info

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
    def save_message(cls, session_id, sender, message, timestamp, ttl_sec=60 * 10):
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
