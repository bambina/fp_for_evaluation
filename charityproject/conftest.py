"""
Common test fixtures for the project.
"""

import pytest
import json
from typing import Optional
from unittest.mock import MagicMock
from pymilvus import MilvusClient

from django.conf import settings

from semanticsearch.schemas import *
from semanticsearch.constants import *


@pytest.fixture
def milvus_client():
    """Return a Milvus client for testing."""
    client = MilvusClient(settings.VECTOR_DB_FILE_TEST)
    yield client


@pytest.fixture
def setup_milvus_faq_collection(milvus_client):
    """Setup and cleanup FAQ collection for testing.

    - Creates a new collection with FAQ schema and index.
    - Drops the collection after test completion.
    """
    # Setup
    if milvus_client.has_collection(collection_name=FAQ_COLLECTION_NAME):
        milvus_client.drop_collection(collection_name=FAQ_COLLECTION_NAME)

    schema = create_faq_schema()
    milvus_client.create_collection(collection_name=FAQ_COLLECTION_NAME, schema=schema)

    base_index_params = milvus_client.prepare_index_params()
    index_params = create_faq_index_params(base_index_params)
    milvus_client.create_index(
        collection_name=FAQ_COLLECTION_NAME, index_params=index_params, sync=True
    )

    yield milvus_client

    # Cleanup
    if milvus_client.has_collection(collection_name=FAQ_COLLECTION_NAME):
        milvus_client.drop_collection(collection_name=FAQ_COLLECTION_NAME)


@pytest.fixture
def setup_milvus_child_collection(milvus_client):
    """Setup and cleanup child collection for testing.

    - Creates a new collection with child schema and index.
    - Drops the collection after test completion.
    """
    # Setup
    if milvus_client.has_collection(collection_name=CHILD_COLLECTION_NAME):
        milvus_client.drop_collection(collection_name=CHILD_COLLECTION_NAME)

    schema = create_child_schema()
    milvus_client.create_collection(
        collection_name=CHILD_COLLECTION_NAME, schema=schema
    )

    base_index_params = milvus_client.prepare_index_params()
    index_params = create_child_index_params(base_index_params)
    milvus_client.create_index(
        collection_name=CHILD_COLLECTION_NAME, index_params=index_params, sync=True
    )

    yield milvus_client

    # Cleanup
    if milvus_client.has_collection(collection_name=CHILD_COLLECTION_NAME):
        milvus_client.drop_collection(collection_name=CHILD_COLLECTION_NAME)


def make_mock_chat_completion(
    finish_reason: str,
    content: str = "",
    function_name: Optional[str] = None,
    model: str = "gpt-3.5-turbo",
    total_tokens: int = 100,
):
    """Return a mock chat completion object with the given finish_reason and content."""
    function_mock = MagicMock()
    function_mock.name = function_name
    function_mock.arguments = json.dumps({})
    mocked_tool_call = MagicMock()
    mocked_tool_call.function = function_mock

    mocked_completion = MagicMock()
    mocked_completion.choices = [
        MagicMock(
            finish_reason=finish_reason,
            message=MagicMock(content=content, tool_calls=[mocked_tool_call]),
        )
    ]
    mocked_completion.model = model
    mocked_completion.usage = MagicMock(total_tokens=total_tokens)
    return mocked_completion


@pytest.fixture
def mock_chat_history():
    """Return a mock chat history."""
    return [
        {
            "role": "assistant",
            "content": "Hi, I'm Nico, your assistant for The Virtual Charity!",
        },
        {"role": "user", "content": "Hello, how are you?"},
    ]
