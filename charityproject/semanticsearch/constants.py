# Milvus
FAQ_COLLECTION_NAME = "faq_vectors"
CHILD_COLLECTION_NAME = "child_profiles"
NUM_DIM = 512  # The vectors Google USE creates has 512 dimensions
MAX_QUESTION_LEN = 255
MAX_ANSWER_LEN = 2048


# OpenAI API - prompt templates
# https://platform.openai.com/docs/models/models-overview
USE_INEXPENSIVE_MODEL = "gpt-3.5-turbo"
AVAILABLE_MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
RELEVANT_DOCS_FORMAT = "Title:{title}\nDescription:{description}\n\n"
SYSTEM_CONTENT_0 = """Hi, I'm Nico, your assistant for this charity!
I'm here to support you by answering questions about our mission, activities, and donation methods.
If you're interested in sponsoring a child, I can help you find the perfect match.

For example, try asking me:
- What is your mission?
- Are there any young girls I can sponsor?

Thank you for visiting this charity's website—your support means the world to us. Feel free to ask me anything!
"""
SYSTEM_CONTENT_1 = """
You are an assistant for an NPO website. Determine if the user's query requires using a specific function to provide relevant information.
- If the query is general or conversational (e.g., greetings), respond directly without using any function.
- If the query is informational and relevant to the NPO's services (e.g., donation methods, activities), use the "search_vector_db" function to retrieve information from the documents.
- If the query is related to finding a specific child to support based on attributes (e.g., "I want to sponsor a child from Kenya" or "Who loves football?"), use the "fetch_child" function to find matching children.
"""
SYSTEM_CONTENT_2 = """You are an assistant for an NPO website, providing answers strictly based on the information provided.
Answer ONLY using the provided information.
If the information does not contain enough details to answer the question, respond with "I'm sorry, but I don't have enough information on that topic."
DO NOT add any information or make inferences beyond what is in the provided information.
Avoid generating any additional details that are not explicitly stated in the provided information.
Here is the list of relevant documents:
"""
SYSTEM_CONTENT_3 = """You are an assistant for an NPO website, responsible for introducing children to potential sponsors based on the provided information.
Using the details of the child retrieved from the database, create a warm and engaging introduction that highlights the child's name, age, country, and any specific preferences or hobbies they have.

Your response should:
- Be friendly and encouraging to help the sponsor feel connected to the child.
- Strictly use the information provided about the child.
- Avoid adding any additional details or making inferences beyond what is provided.
- Conclude your response with a sentence providing a clickable HTML link to learn more about the child and how to support them.
- Do not use Markdown formatting (e.g., brackets or parentheses) or plain text for the link. Instead, use an HTML `<a>` tag. For example: 'To learn more about [child's name] and how you can support them, please visit this link: <a href="[child's link]">[child's link]</a>'.



- Do not include any follow-up questions such as "Would you like to learn more about sponsoring [child's name]?" or similar phrases.

Here is the information about the child:

"""
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_vector_db",
            "description": "Search the vector database for related documents based on the query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to use.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_child",
            "description": "Fetch a child's details based on specific attributes like gender, age, country, and preference.",
            "parameters": {
                "type": "object",
                "properties": {
                    "gender": {
                        "type": "string",
                        "description": "The preferred gender of the child (e.g., 'male', 'female'). Leave blank if not specified.",
                    },
                    "age": {
                        "type": "integer",
                        "description": "The preferred age of the child. Leave blank if not specified.",
                    },
                    "country": {
                        "type": "string",
                        "description": "The country the child is from. Leave blank if not specified.",
                    },
                    "profile_description": {
                        "type": "string",
                        "description": "Keywords or interests to match in the child's profile description. Leave blank if not specified.",
                    },
                },
                "required": [],
            },
        },
    },
]
