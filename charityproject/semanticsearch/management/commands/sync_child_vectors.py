from pymilvus import MilvusClient
from pymilvus import DataType, FieldSchema, CollectionSchema

from django.core.management.base import BaseCommand
from django.conf import settings
from semanticsearch.services import *

from sponsors.models import *
from semanticsearch.constants import *
from core.constants import *


class Command(BaseCommand):
    # python manage.py sync_child_vectors --help
    help = "Populates the vector database with Child data.\n\n"

    def handle(self, *args, **kwargs):
        # Init client
        client = MilvusClient(settings.VECTOR_DB_FILE)

        # Delete exisiting data
        if client.has_collection(collection_name=CHILD_COLLECTION_NAME):
            client.drop_collection(collection_name=CHILD_COLLECTION_NAME)

        # Define the schema fields
        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=False,
                description="ID synchronized with relational DB primary key",
            ),
            FieldSchema(
                name="name",
                dtype=DataType.VARCHAR,
                max_length=MAX_CHILD_NAME_LEN,
                description="Child name",
            ),
            FieldSchema(
                name="profile_description",
                dtype=DataType.VARCHAR,
                max_length=MAX_CHILD_PROFILE_LEN,
                description="Child profile description",
            ),
            FieldSchema(
                name="profile_description_vector",
                dtype=DataType.FLOAT_VECTOR,
                dim=NUM_DIM,
                description="Vector representation of the child profile description",
            ),
        ]
        schema = CollectionSchema(
            fields=fields,
            description="Collection for storing child profile embeddings and associated metadata.",
        )
        client.create_collection(collection_name=CHILD_COLLECTION_NAME, schema=schema)

        # Prepare data
        children = Child.objects.all()
        total_count = children.count()
        batch_size = 10
        for i in range(0, total_count, batch_size):
            children_batch = children[i : i + batch_size]
            profiles = [child.profile_description for child in children_batch]
            profile_vectors = USEModelService.get_vector_representation(
                profiles
            ).tolist()
            data = [
                {
                    "id": child.id,
                    "name": child.name,
                    "profile_description": child.profile_description,
                    "profile_description_vector": profile_vector,
                }
                for child, profile_vector in zip(children_batch, profile_vectors)
            ]
            # Insert data to DB
            res = client.insert(collection_name=CHILD_COLLECTION_NAME, data=data)
            print(res)

        # Create index for vector field
        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="profile_description_vector",
            index_type="FLAT",
            metric_type="IP",
        )
        client.create_index(
            collection_name=CHILD_COLLECTION_NAME, index_params=index_params, sync=True
        )

        client.close()
