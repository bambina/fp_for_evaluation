import yaml

from pymilvus import MilvusClient
from pymilvus import DataType, FieldSchema, CollectionSchema

from django.core.management.base import BaseCommand
from django.conf import settings
from semanticsearch.services import USEModelService
from semanticsearch.constants import *


class Command(BaseCommand):
    # python manage.py populate_data --help
    help = "Populates the database with sample data.\n\n"

    def handle(self, *args, **kwargs):
        # Init client
        client = MilvusClient(settings.VECTOR_DB_FILE)
        # Delete exisiting data
        if client.has_collection(collection_name=COLLECTION_NAME):
            client.drop_collection(collection_name=COLLECTION_NAME)

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
                name="title",
                dtype=DataType.VARCHAR,
                max_length=MAX_TITLE_LEN,
                description="Title text",
            ),
            FieldSchema(
                name="description",
                dtype=DataType.VARCHAR,
                max_length=MAX_DESC_LEN,
                description="Description text",
            ),
            FieldSchema(
                name="title_vector",
                dtype=DataType.FLOAT_VECTOR,
                dim=NUM_DIM,
                description="Title vector",
            ),
            FieldSchema(
                name="description_vector",
                dtype=DataType.FLOAT_VECTOR,
                dim=NUM_DIM,
                description="Description vector",
            ),
        ]
        schema = CollectionSchema(
            fields=fields,
            description="Collection for storing donation methods with title and description vectors",
        )

        client.create_collection(collection_name=COLLECTION_NAME, schema=schema)

        # Create index for vector fields
        # https://milvus.io/api-reference/pymilvus/v2.4.x/MilvusClient/Management/create_index.md
        index_params = client.prepare_index_params()

        for field_name in ["title_vector", "description_vector"]:
            index_params.add_index(
                field_name=field_name,
                index_type="FLAT",
                metric_type="IP",
                params={"nlist": 128},
            )

        client.create_index(
            collection_name=COLLECTION_NAME, index_params=index_params, sync=True
        )

        # Prepare data
        titles, descriptions = self.read_data()
        title_vectors = USEModelService.get_vector_representation(titles).tolist()
        description_vectors = USEModelService.get_vector_representation(
            descriptions
        ).tolist()

        data = [
            {
                "id": i,
                "title": titles[i],
                "description": descriptions[i],
                "title_vector": title_vectors[i],
                "description_vector": description_vectors[i],
            }
            for i in range(len(titles))
        ]

        # Insert data to DB
        res = client.insert(collection_name=COLLECTION_NAME, data=data)
        print(res)

    def read_data(self):
        with open(settings.DATA_FILE, "r") as file:
            data = yaml.safe_load(file)

        titles = []
        descriptions = []
        for record in data:
            title = record.get("title")
            description = record.get("description")
            if len(title) > MAX_TITLE_LEN or len(description) > MAX_DESC_LEN:
                print(
                    f"Skipping record with title length {len(title)} and description length {len(description)}"
                )
                continue
            titles.append(title)
            descriptions.append(description)

        return titles, descriptions
