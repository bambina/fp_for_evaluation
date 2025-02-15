from semanticsearch.constants import *


def test_faq_vector_insertion(setup_milvus_faq_collection):
    """Test vector insertion for FAQ data."""
    # Setup FAQ collection client
    client = setup_milvus_faq_collection
    test_data = {
        "id": 1,
        "question": "Test question?",
        "answer": "Test answer",
        "question_vector": [0.1] * NUM_DIM,
        "answer_vector": [0.2] * NUM_DIM,
    }
    # Insert FAQ entry
    insert_result = client.insert(collection_name=FAQ_COLLECTION_NAME, data=test_data)
    # Check FAQ insertion success
    assert insert_result["insert_count"] == 1
    assert insert_result["ids"][0] == test_data["id"]

    # Query and verify FAQ entry
    query_results = client.query(
        collection_name=FAQ_COLLECTION_NAME, filter=f"id == {test_data['id']}"
    )
    # Verify FAQ query results
    assert len(query_results) == 1
    assert query_results[0]["question"] == test_data["question"]


def test_child_vector_insertion(setup_milvus_child_collection):
    """Test vector insertion for child data."""
    # Setup child collection client
    client = setup_milvus_child_collection
    test_data = {
        "id": 1,
        "name": "Test child",
        "profile_description": "Test profile description",
        "profile_description_vector": [0.1] * NUM_DIM,
    }
    # Insert child entry
    insert_result = client.insert(collection_name=CHILD_COLLECTION_NAME, data=test_data)
    # Check child insertion success
    assert insert_result["insert_count"] == 1
    assert insert_result["ids"][0] == test_data["id"]

    # Query and verify child entry
    query_results = client.query(
        collection_name=CHILD_COLLECTION_NAME, filter=f"id == {test_data['id']}"
    )
    # Verify child query results
    assert len(query_results) == 1
    assert query_results[0]["name"] == test_data["name"]
