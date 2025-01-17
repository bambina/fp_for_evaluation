import ast
from datetime import datetime

from openai import NOT_GIVEN

from sponsors.models import Child

from agent.constants import *
from agent.services import *
from semanticsearch.services import *
from core.utils import log_search_and_child_functions


class OpenAIInteractionOrchestrator:

    @staticmethod
    async def generate_response(chat_history):
        # Get a response from the OpenAI model
        completion = OpenAIClientService.chat_completion(
            USE_INEXPENSIVE_MODEL, SYSTEM_CONTENT_1, chat_history, TOOLS
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
                log_search_and_child_functions(f"\nQuery: {query}\n")
                log_search_and_child_functions(f"\nSearch result: {result}\n")
                system_content = OpenAIClientService.compose_relevant_docs(result)
                # Get a completion from the OpenAI model using the retrieved data
                completion = OpenAIClientService.chat_completion(
                    USE_INEXPENSIVE_MODEL, system_content, chat_history, NOT_GIVEN
                )
            # Search for a child in the Sponsor a Child program
            elif function_name == "fetch_child":
                # Build filters for fetching a child
                filters = OpenAIInteractionOrchestrator.build_child_filters(arguments)
                # Fetch child based on attributes
                child = (
                    await Child.objects.filter(**filters)
                    .select_related("country", "gender")
                    .afirst()
                )
                # print(f"\nfilters: {filters}\n")
                # print(f"\nChild: {child}\n")
                log_search_and_child_functions(f"\nfilters: {filters}\n")
                log_search_and_child_functions(f"\nChild: {child}\n")
                child_found = True
                if not child:
                    child_found = False
                    random_birth_month = (datetime.now().second % 12) + 1
                    child = (
                        await Child.objects.filter(
                            date_of_birth__month=random_birth_month
                        )
                        .select_related("country", "gender")
                        .afirst()
                    )

                system_content = OpenAIClientService.compose_child_introduction(
                    child, child_found
                )
                # print(f"\nSystem content: {system_content}\n")
                # Use ChatGPT to format the search result
                completion = OpenAIClientService.chat_completion(
                    USE_INEXPENSIVE_MODEL, system_content, chat_history, NOT_GIVEN
                )
            else:
                return f"OpenAI model wants to call a function not defined: {function_name}"
        else:
            # print(f"\nFinish reason: {finish_reason}\n")
            log_search_and_child_functions(f"\nFinish reason: {finish_reason}\n")

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
            filters["country"] = arguments["country"]
        if "min_age" in arguments and arguments["min_age"] is not None:
            filters["age__gte"] = arguments["min_age"]
        if "max_age" in arguments and arguments["max_age"] is not None:
            filters["age__lte"] = arguments["max_age"]
        if "birth_month" in arguments and arguments["birth_month"] is not None:
            filters["date_of_birth__month"] = arguments["birth_month"]
        if "birth_day" in arguments and arguments["birth_day"] is not None:
            filters["date_of_birth__day"] = arguments["birth_day"]
        if "profile_description" in arguments and arguments["profile_description"]:
            filters["profile_description__icontains"] = arguments["profile_description"]
        print(f"\nFilters: {filters}\n")
        return filters
