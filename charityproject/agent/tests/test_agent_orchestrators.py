import pytest
from agent.orchestrators import *

from model_bakery import baker
from sponsors.models import *
from unittest.mock import patch


@pytest.mark.django_db(transaction=True)
class TestOpenAIInteractionOrchestrator:
    @pytest.fixture
    def child_with_profile(self):
        """Create a child with a profile description for semantic search testing."""
        return baker.make(Child, profile_description="loves playing football")

    @pytest.fixture
    def child_with_structured_data(self):
        """Create a child with structured data for structured search testing."""
        gender = baker.make(Gender, name="Female")
        country = baker.make(Country, name="Bolivia")
        return baker.make(Child, gender=gender, country=country)

    @pytest.fixture
    def children_for_search_tests(self):
        """Create 3 children for both structured and semantic search."""
        gender1 = baker.make(Gender, name="Male")
        gender2 = baker.make(Gender, name="Female")
        child1 = baker.make(
            Child,
            gender=gender1,
            profile_description="He loves playing football and dreams of becoming a professional player.",
        )
        child2 = baker.make(
            Child,
            gender=gender2,
            profile_description="She enjoys playing football with her friends after school.",
        )
        child3 = baker.make(
            Child,
            gender=gender1,
            profile_description="He likes trying different sports.",
        )
        return {"child1": child1, "child3": child3}

    def test_build_structured_child_filters(self):
        """
        Test if build_structured_child_filters correctly transforms input arguments into filter conditions.
        """
        arguments = {
            "gender": "female",
            "country": "Bolivia",
            "min_age": 5,
            "max_age": 10,
            "birth_month": 3,
            "birth_day": 15,
        }
        expected_filters = {
            "gender__name__iexact": "female",
            "country__name__iexact": "Bolivia",
            "age__gte": 5,
            "age__lte": 10,
            "date_of_birth__month": 3,
            "date_of_birth__day": 15,
        }

        filters = OpenAIInteractionOrchestrator.build_structured_child_filters(
            arguments
        )

        assert filters == expected_filters

    def test_build_structured_child_filters_empty_input(self):
        """
        Test if build_structured_child_filters returns an empty dictionary when given an empty input.
        """
        arguments = {}
        expected_filters = {}

        filters = OpenAIInteractionOrchestrator.build_structured_child_filters(
            arguments
        )

        assert filters == expected_filters

    def test_build_structured_child_filters_partial_input(self):
        """
        Test if build_structured_child_filters correctly handles partial input.
        """
        arguments = {"gender": "male", "birth_day": 25}
        expected_filters = {"gender__name__iexact": "male", "date_of_birth__day": 25}

        filters = OpenAIInteractionOrchestrator.build_structured_child_filters(
            arguments
        )

        assert filters == expected_filters

    @pytest.mark.asyncio
    @patch(
        "agent.orchestrators.OpenAIInteractionOrchestrator.fetch_children_by_profile_description"
    )
    async def test_fetch_children_with_semantic_search(
        self, mock_semantic_search, child_with_profile
    ):
        """Ensure fetch_children returns correct child when using semantic search."""
        mock_semantic_search.return_value = [child_with_profile.id], False
        arguments = {"profile_description": "loves playing football"}
        children, child_found = await OpenAIInteractionOrchestrator.fetch_children(
            arguments
        )
        assert len(children) == 1
        assert child_found is True
        assert children[0].id == child_with_profile.id

    @pytest.mark.asyncio
    @patch(
        "agent.orchestrators.OpenAIInteractionOrchestrator.fetch_children_by_profile_description"
    )
    async def test_fetch_children_with_structured_search(
        self, mock_semantic_search, child_with_structured_data
    ):
        """Ensure fetch_children returns correct child when using structured search."""
        mock_semantic_search.return_value = [], True
        arguments = {"gender": "female", "country": "Bolivia"}
        children, child_found = await OpenAIInteractionOrchestrator.fetch_children(
            arguments
        )
        assert len(children) == 1
        assert child_found is True
        assert children[0].id == child_with_structured_data.id

    @pytest.mark.asyncio
    @patch(
        "agent.orchestrators.OpenAIInteractionOrchestrator.fetch_children_by_profile_description"
    )
    async def test_fetch_children_with_both_searches(
        self, mock_semantic_search, children_for_search_tests
    ):
        """Ensure fetch_children correctly merges results from both structured and semantic searches."""
        child1, child3 = (
            children_for_search_tests["child1"],
            children_for_search_tests["child3"],
        )
        mock_semantic_search.return_value = [child1.id, child3.id], False
        arguments = {
            "gender": "male",
            "profile_description": "loves playing football",
        }
        children, child_found = await OpenAIInteractionOrchestrator.fetch_children(
            arguments
        )
        assert len(children) == 2
        assert children == [child1, child3]
        assert child_found is True

    @pytest.mark.asyncio
    @patch(
        "agent.orchestrators.OpenAIInteractionOrchestrator.fetch_children_by_profile_description"
    )
    async def test_fetch_children_falls_back_to_random_selection(
        self, mock_semantic_search, child_with_structured_data
    ):
        """Ensure fetch_children selects a random child when no search results are found."""
        mock_semantic_search.return_value = [], True
        arguments = {"country": "Kenya"}
        children, child_found = await OpenAIInteractionOrchestrator.fetch_children(
            arguments
        )
        assert len(children) == 1
        assert child_found is False
