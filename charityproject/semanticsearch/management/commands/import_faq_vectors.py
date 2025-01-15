from pymilvus import MilvusClient
from pymilvus import DataType, FieldSchema, CollectionSchema

from django.core.management.base import BaseCommand
from django.conf import settings
from semanticsearch.services import USEModelService
from semanticsearch.constants import *
from django.core.exceptions import ValidationError
from pathlib import Path
from core.validators import *
import csv
from core.utils import *


class Command(BaseCommand):
    # python manage.py import_faq_vectors --help
    help = "Populates the vector database with FAQ data.\n\n"

    def add_arguments(self, parser):
        # Add an optional argument to specify the CSV file to load data from
        parser.add_argument(
            "--faq",
            type=str,
            default="faqs.csv",
            help="The CSV file to load data from (default: faqs.csv).",
        )

    def handle(self, *args, **kwargs):
        file_paths = {
            "faq": Path(settings.DATA_DIR) / kwargs["faq"],
        }
        for file_path in file_paths.values():
            if not file_path.exists():
                raise FileNotFoundError(f"File {file_path} not found")

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

        # Create index for vector fields
        # https://milvus.io/api-reference/pymilvus/v2.4.x/MilvusClient/Management/create_index.md
        index_params = client.prepare_index_params()

        for field_name in ["question_vector", "answer_vector"]:
            index_params.add_index(
                field_name=field_name,
                index_type="FLAT",
                metric_type="IP",
                params={"nlist": 128},
            )

        client.create_index(
            collection_name=FAQ_COLLECTION_NAME, index_params=index_params, sync=True
        )

        # Prepare data
        questions, answers = self.read_faq_data(file_paths["faq"])
        question_vectors = USEModelService.get_vector_representation(questions).tolist()
        answer_vectors = USEModelService.get_vector_representation(answers).tolist()
        data = [
            {
                "id": i,
                "question": questions[i],
                "answer": answers[i],
                "question_vector": question_vectors[i],
                "answer_vector": answer_vectors[i],
            }
            for i in range(len(questions))
        ]

        # Insert data to DB
        res = client.insert(collection_name=FAQ_COLLECTION_NAME, data=data)
        print(res)

    def read_faq_data(self, file_path):
        questions = []
        answers = []
        with open(file_path, mode="r", encoding="utf-8") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            csv_reader.__next__()
            for row in csv_reader:
                try:
                    # Assign the row data to variables
                    question = row[0].strip()
                    answer = row[1].strip()
                    if not question or not answer:
                        raise ValidationError("Question and answer cannot be empty")
                    # Validate the question length
                    max_length_255_validator(question)
                    max_length_2048_validator(answer)
                    questions.append(question)
                    answers.append(answer)
                except ValidationError as e:
                    write_error(
                        self.stdout,
                        self.style,
                        f"Validation error in row {csv_reader.line_num}: {e}",
                    )
                    continue
        return questions, answers
