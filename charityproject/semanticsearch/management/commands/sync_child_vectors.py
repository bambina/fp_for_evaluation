from pymilvus import MilvusClient

from django.core.management.base import BaseCommand
from django.conf import settings

from semanticsearch.services import *
from semanticsearch.constants import *
from semanticsearch.schemas import *
from sponsors.models import *
from core.constants import *


class Command(BaseCommand):
    # python manage.py sync_child_vectors --help
    help = "Sync child data from the relational DB to the vector DB.\n\n"

    def handle(self, *args, **kwargs):
        # Init client
        client = MilvusClient(settings.VECTOR_DB_FILE)

        # Delete exisiting data
        if client.has_collection(collection_name=CHILD_COLLECTION_NAME):
            client.drop_collection(collection_name=CHILD_COLLECTION_NAME)

        # Create collection
        schema = create_child_schema()
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
        base_index_params = client.prepare_index_params()
        index_params = create_child_index_params(base_index_params)
        client.create_index(
            collection_name=CHILD_COLLECTION_NAME, index_params=index_params, sync=True
        )

        client.close()
