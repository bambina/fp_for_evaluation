import pytest
from pytest_mock import mocker
from agent.orchestrators import *
from agent.constants import *
from conftest import *
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
        description = "loves playing football"
        mock_semantic_search.return_value = [child_with_profile.id], description
        arguments = {"profile_description": description}
        children, child_found, query_keyword = (
            await OpenAIInteractionOrchestrator.retrieve_children_by_attributes(
                arguments
            )
        )
        assert len(children) == 1
        assert child_found is True
        assert query_keyword == description
        assert children[0].id == child_with_profile.id

    @pytest.mark.asyncio
    @patch(
        "agent.orchestrators.OpenAIInteractionOrchestrator.fetch_children_by_profile_description"
    )
    async def test_fetch_children_with_structured_search(
        self, mock_semantic_search, child_with_structured_data
    ):
        """Ensure fetch_children returns correct child when using structured search."""
        mock_semantic_search.return_value = [], ""
        arguments = {"gender": "female", "country": "Bolivia"}
        children, child_found, query_keyword = (
            await OpenAIInteractionOrchestrator.retrieve_children_by_attributes(
                arguments
            )
        )
        assert len(children) == 1
        assert child_found is True
        assert query_keyword == ""
        assert children[0].id == child_with_structured_data.id

    @pytest.mark.asyncio
    @patch(
        "agent.orchestrators.OpenAIInteractionOrchestrator.fetch_children_by_profile_description"
    )
    async def test_fetch_children_with_both_searches(
        self, mock_semantic_search, children_for_search_tests
    ):
        """Ensure fetch_children correctly merges results from both structured and semantic searches."""
        description = "loves playing football"
        child1, child3 = (
            children_for_search_tests["child1"],
            children_for_search_tests["child3"],
        )
        mock_semantic_search.return_value = [child1.id, child3.id], description
        arguments = {
            "gender": "male",
            "profile_description": description,
        }
        children, child_found, query_keyword = (
            await OpenAIInteractionOrchestrator.retrieve_children_by_attributes(
                arguments
            )
        )
        assert len(children) == 2
        assert children == [child1, child3]
        assert child_found is True
        assert query_keyword == description

    @pytest.mark.asyncio
    @patch(
        "agent.orchestrators.OpenAIInteractionOrchestrator.fetch_children_by_profile_description"
    )
    async def test_fetch_children_falls_back_to_random_selection(
        self, mock_semantic_search, child_with_structured_data
    ):
        """Ensure fetch_children selects a random child when no search results are found."""
        mock_semantic_search.return_value = [], ""
        arguments = {"country": "Kenya"}
        children, child_found, query_keyword = (
            await OpenAIInteractionOrchestrator.retrieve_children_by_attributes(
                arguments
            )
        )
        assert len(children) == 1
        assert child_found is False
        assert query_keyword == ""

    @pytest.mark.asyncio
    async def test_generate_response_when_finish_reason_is_stop(
        self, mocker, mock_chat_history
    ):
        """Test that generate_response returns a normal reply when the finish_reason is 'stop'"""
        content = "Hello! How can I assist you today?"
        mock_completion = make_mock_chat_completion(
            finish_reason=FinishReason.STOP, content=content
        )
        mocker.patch(
            "agent.services.OpenAIClientService.chat_completion",
            return_value=mock_completion,
        )
        mocker.patch(
            "agent.services.RedisChatHistoryService.get_chat_history",
            return_value=mock_chat_history,
        )
        response = await OpenAIInteractionOrchestrator.generate_response(
            "test_session_id"
        )
        expected = {"model": "gpt-3.5-turbo", "total_tokens": 100, "content": content}
        assert response == expected

    @pytest.mark.asyncio
    async def run_generate_response_error_test(
        self,
        mocker,
        mock_chat_history,
        finish_reason: str,
        expected_exception: type[Exception],
    ):
        """Helper to test that generate_response raises the correct exception for a given finish_reason."""
        mock_completion = make_mock_chat_completion(finish_reason=finish_reason)
        mocker.patch(
            "agent.services.OpenAIClientService.chat_completion",
            return_value=mock_completion,
        )
        mocker.patch(
            "agent.services.RedisChatHistoryService.get_chat_history",
            return_value=mock_chat_history,
        )
        with pytest.raises(expected_exception):
            await OpenAIInteractionOrchestrator.generate_response("test_session_id")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "finish_reason,expected_exception",
        [
            (FinishReason.LENGTH, ChatResponseTooLongError),
            (FinishReason.CONTENT_FILTER, ChatContentFilteredError),
            ("unknown", ChatUnknownFinishReasonError),
            (FinishReason.TOOL_CALLS, ChatUndefinedToolCallError),
        ],
    )
    async def test_generate_response_error_cases(
        self, mocker, mock_chat_history, finish_reason, expected_exception
    ):
        await self.run_generate_response_error_test(
            mocker, mock_chat_history, finish_reason, expected_exception
        )
