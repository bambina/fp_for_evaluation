from pymilvus import FieldSchema, CollectionSchema, DataType
from semanticsearch.constants import *
from core.constants import *


def create_faq_schema():
    # Define the schema fields
    fields = [
        FieldSchema(
            name="id",
            dtype=DataType.INT64,
            is_primary=True,
            auto_id=False,
            description="Auto-incrementing document ID",
        ),
        FieldSchema(
            name="question",
            dtype=DataType.VARCHAR,
            max_length=MAX_QUESTION_LEN,
            description="Question text",
        ),
        FieldSchema(
            name="answer",
            dtype=DataType.VARCHAR,
            max_length=MAX_ANSWER_LEN,
            description="Answer text",
        ),
        FieldSchema(
            name="question_vector",
            dtype=DataType.FLOAT_VECTOR,
            dim=NUM_DIM,
            description="Question vector",
        ),
        FieldSchema(
            name="answer_vector",
            dtype=DataType.FLOAT_VECTOR,
            dim=NUM_DIM,
            description="Answer vector",
        ),
    ]
    return CollectionSchema(
        fields=fields,
        description="Collection for storing FAQ data including questions, answers, and their corresponding vectors",
    )


def create_faq_index_params(index_params):
    """Create index parameters for the FAQ collection."""
    # https://milvus.io/api-reference/pymilvus/v2.4.x/MilvusClient/Management/create_index.md
    for field_name in ["question_vector", "answer_vector"]:
        index_params.add_index(
            field_name=field_name,
            index_type="FLAT",
            metric_type="IP",
        )
    return index_params
