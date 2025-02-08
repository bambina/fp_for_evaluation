from pymilvus import MilvusClient
from pymilvus import DataType, FieldSchema, CollectionSchema

from django.core.management.base import BaseCommand
from django.conf import settings
from semanticsearch.services import *

from faqs.models import *
from semanticsearch.constants import *
from core.constants import *


class Command(BaseCommand):
    # python manage.py sync_faq_vectors --help
    help = "Sync FAQ entries from the relational DB to the vector DB.\n\n"

    def handle(self, *args, **kwargs):
        # Init client
        client = MilvusClient(settings.VECTOR_DB_FILE)

        # Delete exisiting data
        if client.has_collection(collection_name=FAQ_COLLECTION_NAME):
            client.drop_collection(collection_name=FAQ_COLLECTION_NAME)

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
        schema = CollectionSchema(
            fields=fields,
            description="Collection for storing FAQ data including questions, answers, and their corresponding vectors",
        )

        client.create_collection(collection_name=FAQ_COLLECTION_NAME, schema=schema)

        # Prepare data
        faqs = FAQEntry.objects.all()
        total_count = faqs.count()
        batch_size = 10
        for i in range(0, total_count, batch_size):
            faqs_batch = faqs[i : i + batch_size]
            questions = [entry.question for entry in faqs_batch]
            answers = [entry.answer for entry in faqs_batch]
            question_vectors = USEModelService.get_vector_representation(
                questions
            ).tolist()
            answer_vectors = USEModelService.get_vector_representation(answers).tolist()
            data = [
                {
                    "id": faq.id,
                    "question": faq.question,
                    "answer": faq.answer,
                    "question_vector": questioin_vector,
                    "answer_vector": answer_vector,
                }
                for faq, questioin_vector, answer_vector in zip(
                    faqs_batch, question_vectors, answer_vectors
                )
            ]
            # Insert data to DB
            res = client.insert(collection_name=FAQ_COLLECTION_NAME, data=data)
            print(res)

        # Create index for vector fields
        # https://milvus.io/api-reference/pymilvus/v2.4.x/MilvusClient/Management/create_index.md
        index_params = client.prepare_index_params()
        for field_name in ["question_vector", "answer_vector"]:
            index_params.add_index(
                field_name=field_name,
                index_type="FLAT",
                metric_type="IP",
            )
        client.create_index(
            collection_name=FAQ_COLLECTION_NAME, index_params=index_params, sync=True
        )

        client.close()
