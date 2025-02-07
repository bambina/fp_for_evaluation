import os
from typing import List

import numpy as np
import tensorflow_hub as hub
import tensorflow, tensorflow_text  # For loading the USE model
from pymilvus import MilvusClient, AnnSearchRequest, WeightedRanker

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
    def search_faq_hybrid(cls, query_vectors: np.ndarray, top_k: int = 3):
        if cls._client is None:
            cls.init_client()

        return cls._client.hybrid_search(
            collection_name=FAQ_COLLECTION_NAME,
            reqs=[
                AnnSearchRequest(
                    data=query_vectors,
                    anns_field="question_vector",
                    param={"metric_type": "IP", "params": {"nprobe": 10}},
                    limit=top_k,
                ),
                AnnSearchRequest(
                    data=query_vectors,
                    anns_field="answer_vector",
                    param={"metric_type": "IP", "params": {"nprobe": 10}},
                    limit=top_k,
                ),
            ],
            ranker=WeightedRanker(0.7, 0.3),
            output_fields=["question", "answer"],
            limit=top_k,
        )

    @classmethod
    def search_child_profiles(cls, query_vectors: np.ndarray, top_k: int = 3):
        if cls._client is None:
            cls.init_client()

        return cls._client.search(
            collection_name=CHILD_COLLECTION_NAME,
            data=query_vectors,
            anns_field="profile_description_vector",
            search_params={"metric_type": "IP"},
            output_fields=["id", "name", "profile_description"],
            limit=top_k,
        )
