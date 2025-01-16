import ast

from openai import NOT_GIVEN

from sponsors.models import Child

from agent.constants import *
from agent.services import *
from semanticsearch.services import *


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
            if function_name == "search_vector_db":
                query = arguments.get("query")
                query_vectors = USEModelService.get_vector_representation([query])
                result = MilvusClientService.hybrid_search(query_vectors)
                print(f"\nQuery: {query}\n")
                print(f"\nSearch result: {result}\n")
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
                system_content = OpenAIClientService.compose_child_introduction(child)
                # Use ChatGPT to format the search result
                completion = OpenAIClientService.chat_completion(
                    USE_INEXPENSIVE_MODEL, system_content, chat_history, NOT_GIVEN
                )
            else:
                return f"OpenAI model wants to call a function not defined: {function_name}"
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
        if "country" in arguments and arguments["country"]:
            filters["country"] = arguments["country"]
        if "age" in arguments and arguments["age"]:
            filters["age"] = arguments["age"]
        if "profile_description" in arguments and arguments["profile_description"]:
            filters["profile_description__icontains"] = arguments["profile_description"]
        print(f"\nFilters: {filters}\n")
        return filters
