import ast, random

from openai import NOT_GIVEN

from sponsors.models import Child

from agent.constants import *
from agent.services import *
from semanticsearch.services import *
from core.utils import *


class OpenAIInteractionOrchestrator:

    @staticmethod
    async def generate_response(room_name):
        chat_history = RedisChatHistoryService.get_chat_history(room_name)
        # Get a response from the OpenAI model
        completion = OpenAIClientService.chat_completion(
            SELECTED_MODEL, SYSTEM_CONTENT_1, chat_history, TOOLS
        )
        finish_reason = completion.choices[0].finish_reason
        # Check if the model intends to call an application function
        if finish_reason == "tool_calls":
            tool_function = completion.choices[0].message.tool_calls[0].function
            function_name = tool_function.name
            arguments = ast.literal_eval(tool_function.arguments)
            # Search for data relevant to the charity
            if function_name == "search_relevant_faqs":
                query = arguments.get("search_keywords")
                query_vectors = USEModelService.get_vector_representation(query)
                result = MilvusClientService.search_faq_hybrid(query_vectors)
                # print(f"\nQuery: {query}\n")
                # print(f"\nSearch result: {result}\n")
                log_user_test(f"Query: {query}\n")
                log_user_test(f"Search result: {result}\n")
                system_content = OpenAIClientService.compose_relevant_docs(result)
                # Get a completion from the OpenAI model using the retrieved data
                completion = OpenAIClientService.chat_completion(
                    SELECTED_MODEL, system_content, chat_history, NOT_GIVEN
                )
            # Search for a child in the Sponsor a Child program
            elif function_name == "fetch_children":
                children, found, semantic_search_keyword = (
                    await OpenAIInteractionOrchestrator.fetch_children(arguments)
                )
                system_content = OpenAIClientService.compose_child_introduction(
                    children, found, semantic_search_keyword
                )
                log_user_test(f"Children: {children}\n")
                # for child in children:
                #     print(f"Child found: {child}")

                # Use ChatGPT to format the search result
                completion = OpenAIClientService.chat_completion(
                    SELECTED_MODEL, system_content, chat_history, NOT_GIVEN
                )
            else:
                return f"OpenAI model wants to call a function not defined: {function_name}"
        else:
            # print(f"\nFinish reason: {finish_reason}\n")
            log_user_test(f"Finish reason: {finish_reason}\n")

        return {
            "model": completion.model,
            "total_tokens": completion.usage.total_tokens,
            "content": completion.choices[0].message.content,
        }

    @staticmethod
    def build_structured_child_filters(arguments):
        """
        Build filters for fetching a child using structured data.
        """
        filters = {}
        if arguments.get("gender") and arguments["country"].lower() != "all":
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
    async def fetch_children_by_filters(arguments):
        """
        Fetch children in the Sponsor a Child program based on structured attributes.
        """
        # Build filters for fetching children
        filters = OpenAIInteractionOrchestrator.build_structured_child_filters(
            arguments
        )

        # Fetch children based on attributes
        if not filters:
            return [], True
        return [
            child.id
            async for child in Child.objects.filter(**filters)
            .select_related("country", "gender")
            .all()
        ], False

    @staticmethod
    async def fetch_children_by_profile_description(arguments):
        """
        Fetch children in the Sponsor a Child program based on profile description.
        """
        child_ids = []
        query_keyword = ""
        if arguments.get("profile_description"):
            query_keyword = arguments["profile_description"]
            query_vectors = USEModelService.get_vector_representation([query_keyword])
            result = MilvusClientService.search_child_profiles(query_vectors, 5)
            for hits in result:
                for hit in hits:
                    child_ids.append(hit["entity"]["id"])
        return child_ids, query_keyword

    @staticmethod
    def merge_children_results(structured_match_ids, semantic_match_ids):
        """
        Merge results while preserving the ranking of semantic search.
        Returns IDs that appear in both structured and semantic search.
        """
        structured_set = set(structured_match_ids)
        return [id for id in semantic_match_ids if id in structured_set]

    @staticmethod
    async def fetch_children(arguments):
        """
        Fetch children in the Sponsor a Child program based on the given attributes.

        Returns:
            children (List[Child]): A list of children found through search or random selection.
            child_found (bool): True if children were found through search, False if a random selection was made.
        """
        print(f"\nArguments: {arguments}\n")
        log_user_test(f"Arguments: {arguments}\n")
        child_found = True

        # Perform structured and semantic search
        structured_match_ids, is_structured_filter_missing = (
            await OpenAIInteractionOrchestrator.fetch_children_by_filters(arguments)
        )
        semantic_match_ids, semantic_search_keyword = (
            await OpenAIInteractionOrchestrator.fetch_children_by_profile_description(
                arguments
            )
        )

        # Determine child IDs based on search results
        if is_structured_filter_missing:
            child_ids = semantic_match_ids
        elif semantic_search_keyword == "":
            child_ids = structured_match_ids
        else:
            child_ids = OpenAIInteractionOrchestrator.merge_children_results(
                structured_match_ids, semantic_match_ids
            )

        # Retrieve children based on the determined IDs
        if child_ids:
            children_dict = {
                child.id: child
                async for child in Child.objects.filter(
                    id__in=child_ids[:3]
                ).select_related("country", "gender")
            }
            children = [
                children_dict[id] for id in child_ids[:3] if id in children_dict
            ]
            # print(f"\nChildren: {children}\n")
        else:
            # If no children were found, select a random child
            child_found = False
            children = [await OpenAIInteractionOrchestrator.get_random_child()]
            # print(f"\nRandom child: {children}\n")

        return children, child_found, semantic_search_keyword

    @staticmethod
    async def get_random_child():
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
