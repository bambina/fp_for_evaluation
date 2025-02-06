import ast
from datetime import datetime

from openai import NOT_GIVEN

from sponsors.models import Child
from django.db.models import Q

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
                query = arguments.get("query")
                query_vectors = USEModelService.get_vector_representation([query])
                result = MilvusClientService.hybrid_search(query_vectors)
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
                children, found = await OpenAIInteractionOrchestrator.fetch_children(
                    arguments
                )
                system_content = OpenAIClientService.compose_child_introduction(
                    children, found
                )
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
    def build_child_filters(arguments):
        """
        Build filters for fetching a child in the Sponsor a Child program.
        """
        filters = {}
        if "gender" in arguments and arguments["gender"]:
            filters["gender__name__iexact"] = arguments["gender"]
        if "country" in arguments and arguments["country"]:
            filters["country__name__iexact"] = arguments["country"]
        if "min_age" in arguments and arguments["min_age"] is not None:
            filters["age__gte"] = arguments["min_age"]
        if "max_age" in arguments and arguments["max_age"] is not None:
            filters["age__lte"] = arguments["max_age"]
        if "birth_month" in arguments and arguments["birth_month"] is not None:
            filters["date_of_birth__month"] = arguments["birth_month"]
        if "birth_day" in arguments and arguments["birth_day"] is not None:
            filters["date_of_birth__day"] = arguments["birth_day"]
        return filters

    @staticmethod
    async def fetch_children(arguments):
        """
        Fetch children in the Sponsor a Child program based on the given attributes.
        """
        # Build filters for fetching children
        filters = OpenAIInteractionOrchestrator.build_child_filters(arguments)
        print(f"\nArguments: {arguments}\n")
        print(f"\nFilters: {filters}\n")
        # log_user_test(f"filters: {filters}\n")
        # Fetch children based on attributes
        children = []
        child_found = True
        async for child in (
            Child.objects.filter(**filters)
            .select_related("country", "gender")
            .all()[:MAX_CHILDREN_RESULTS]
        ):
            children.append(child)

        if not children:
            child_found = False
            random_birth_month = (datetime.now().second % 12) + 1
            child = (
                await Child.objects.filter(date_of_birth__month=random_birth_month)
                .select_related("country", "gender")
                .afirst()
            )
            children.append(child)

        print(f"\nchildren: {children}\n")
        # log_user_test(f"children: {children}\n")
        return children, child_found
