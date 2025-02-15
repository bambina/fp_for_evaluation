"""
Common test fixtures for the project.
This file contains fixtures that can be automatically used across all test files:
- Milvus client setup
- Collection creation and cleanup
"""

import pytest
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
