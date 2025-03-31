import ast, random
from typing import Optional

from openai import NOT_GIVEN, ChatCompletion

from agent.constants import *
from agent.services import *
from agent.exceptions import *
from core.utils import *
from semanticsearch.services import *
from sponsors.models import Child


class ChatOrchestrator:

    @staticmethod
    async def generate_response(room_name) -> dict:
        """
        Generates a response based on the chat history and model's output.
        """
        chat_history = RedisChatHistoryService.get_chat_history(room_name)
        # Generate an initial response from the API
        completion = OpenAIClientService.chat_completion(
            SELECTED_MODEL, SYSTEM_PROMPT_INITIAL_INSTRUCTION, chat_history, TOOLS
        )
        finish_reason = completion.choices[0].finish_reason
        # Handle tool calls if requested by the model
        if finish_reason == FinishReason.TOOL_CALLS:
            completion = await ChatOrchestrator.handle_tool_calls(
                completion, chat_history
            )
            return ChatOrchestrator.compose_response(completion)
        # Return the final response if the generation is complete
        elif finish_reason == FinishReason.STOP:
            return ChatOrchestrator.compose_response(completion)
        # Handle errors based on finish reason
        elif finish_reason == FinishReason.LENGTH:
            raise ChatResponseTooLongError(OpenAIAPIErrorMessages.RESPONSE_TOO_LONG)
        elif finish_reason == FinishReason.CONTENT_FILTER:
            raise ChatContentFilteredError(OpenAIAPIErrorMessages.CONTENT_FILTERED)
        else:
            raise ChatUnknownFinishReasonError(
                OpenAIAPIErrorMessages.UNKNOWN_FINISH_REASON.format(
                    finish_reason=finish_reason
                )
            )

    @staticmethod
    async def handle_tool_calls(
        completion: ChatCompletion, chat_history: list
    ) -> ChatCompletion:
        """
        Processes tool call requests and dispatches them to the appropriate handler.
        """
        tool_function = completion.choices[0].message.tool_calls[0].function
        function_name = tool_function.name
        arguments = ast.literal_eval(tool_function.arguments)
        if function_name == "search_relevant_faqs":
            return ChatOrchestrator.search_relevant_faqs(arguments, chat_history)
        elif function_name == "fetch_children":
            return await ChatOrchestrator.fetch_children(arguments, chat_history)
        else:
            raise ChatUndefinedToolCallError(
                OpenAIAPIErrorMessages.UNDEFINED_TOOL_CALL.format(
                    function_name=function_name
                )
            )

    @staticmethod
    def search_relevant_faqs(arguments: dict, chat_history: list) -> ChatCompletion:
        """
        Handles the 'search_relevant_faqs' tool call.

        Retrieves relevant FAQ documents using a semantic search and returns
        a follow-up completion generated with those results.
        """
        query = arguments.get("search_keywords")
        query_vectors = USEModelService.get_vector_representation(query)
        result = MilvusClientService.search_faq_hybrid(query_vectors)
        system_content = OpenAIClientService.compose_relevant_docs(result)
        return OpenAIClientService.chat_completion(
            SELECTED_MODEL, system_content, chat_history, NOT_GIVEN
        )

    @staticmethod
    async def fetch_children(arguments: dict, chat_history) -> ChatCompletion:
        """
        Handles the 'fetch_children' tool call.

        Retrieves children based on given arguments and returns
        a follow-up completion with a formatted introduction.
        """
        children, found, semantic_search_keyword = (
            await ChatOrchestrator.search_children(arguments)
        )
        system_content = OpenAIClientService.compose_child_introduction(
            children, found, semantic_search_keyword
        )
        return OpenAIClientService.chat_completion(
            SELECTED_MODEL, system_content, chat_history, NOT_GIVEN
        )

    @staticmethod
    def compose_response(completion: ChatCompletion) -> dict:
        """
        Compose a response dictionary from the OpenAI completion object.
        """
        return {
            "model": completion.model,
            "total_tokens": completion.usage.total_tokens,
            "content": completion.choices[0].message.content,
        }

    @staticmethod
    def build_structured_child_filters(arguments: dict) -> dict:
        """
        Build filters for fetching a child using structured data.
        """
        filters = {}
        if arguments.get("gender") and arguments["gender"].lower() != "all":
            filters["gender__name__iexact"] = arguments["gender"]
        if arguments.get("country") and arguments["country"].lower() != "all":
            filters["country__name__iexact"] = arguments["country"]
        if isinstance(arguments.get("min_age"), int):
            filters["age__gte"] = arguments["min_age"]
        if isinstance(arguments.get("max_age"), int):
            filters["age__lte"] = arguments["max_age"]
        if isinstance(arguments.get("birth_month"), int):
            filters["date_of_birth__month"] = arguments["birth_month"]
        if isinstance(arguments.get("birth_day"), int):
            filters["date_of_birth__day"] = arguments["birth_day"]
        return filters

    @staticmethod
    async def structured_search_for_children(arguments: dict) -> tuple[list[int], bool]:
        """
        Performs a structured search for children based on filterable attributes.

        Returns:
            child_ids (List[int]): List of matching child IDs.
            is_filter_missing (bool): True if no filters were provided.
        """
        # Build filters for structured child search
        filters = ChatOrchestrator.build_structured_child_filters(arguments)

        # Return empty result if no filters are provided
        if not filters:
            return [], True

        # Query children matching the filter conditions
        child_ids = [
            child.id
            async for child in Child.objects.filter(**filters).select_related(
                "country", "gender"
            )
        ]

        return child_ids, False

    @staticmethod
    async def semantic_search_for_children(arguments: dict) -> tuple[list[int], str]:
        """
        Performs a semantic search for children based on profile description.

        Returns:
            child_ids (List[int]): List of matching child IDs.
            query_keyword (str): The keyword used for semantic search.
        """
        child_ids = []
        query_keyword = ""
        # Perform semantic search if profile description is provided
        if arguments.get("profile_description"):
            query_keyword = arguments["profile_description"]
            query_vectors = USEModelService.get_vector_representation([query_keyword])
            result = MilvusClientService.search_child_profiles(query_vectors)
            for hits in result:
                for hit in hits:
                    child_ids.append(hit["entity"]["id"])
        return child_ids, query_keyword

    @staticmethod
    def intersect_children_ids(
        structured_match_ids: list[int], semantic_match_ids: list[int]
    ) -> list[int]:
        """
        Returns IDs that appear in both structured and semantic search results,
        preserving the original order of semantic search.
        """
        structured_set = set(structured_match_ids)
        return [id for id in semantic_match_ids if id in structured_set]

    @staticmethod
    async def search_children(arguments: dict) -> tuple[list, bool, str]:
        """
        Searches for children based on structured and semantic criteria.
        Falls back to a random child if no match is found.

        Returns:
            children (List[Child]): A list of children found through search or random selection.
            child_found (bool): True if children were found through search; False if fallback was used.
            semantic_keyword (str): The keyword used for semantic search (empty if not used).
        """
        # Perform structured and semantic search
        structured_match_ids, is_filter_missing = (
            await ChatOrchestrator.structured_search_for_children(arguments)
        )
        semantic_match_ids, semantic_keyword = (
            await ChatOrchestrator.semantic_search_for_children(arguments)
        )
        # Determine which IDs to use based on the available search results
        if is_filter_missing:
            child_ids = semantic_match_ids
        elif not semantic_keyword:
            child_ids = structured_match_ids
        else:
            child_ids = ChatOrchestrator.intersect_children_ids(
                structured_match_ids, semantic_match_ids
            )
        # Retrieve children by IDs or fall back to a random child
        if child_ids:
            children = await ChatOrchestrator.get_children_by_ids(child_ids)
        else:
            children = [await ChatOrchestrator.get_random_child()]
        return children, bool(child_ids), semantic_keyword

    @staticmethod
    async def get_children_by_ids(child_ids: list[int], limit: int = 3) -> list:
        """
        Retrieves Child objects by ID, preserving the order of the input list.

        Returns:
            list[Child]: Child objects in the same order as the provided IDs.
        """
        child_ids = child_ids[:limit]
        children_dict = {
            child.id: child
            async for child in Child.objects.filter(id__in=child_ids).select_related(
                "country", "gender"
            )
        }
        return [children_dict[id] for id in child_ids if id in children_dict]

    @staticmethod
    async def get_random_child() -> Optional[Child]:
        """
        Retrieve a random child from the database.
        """
        child_count = await Child.objects.acount()
        random_offset = random.randint(0, child_count - 1)

        return (
            await Child.objects.all()
            .select_related("country", "gender")
            .order_by("id")[random_offset : random_offset + 1]
            .afirst()
        )
