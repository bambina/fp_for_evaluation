"""
Custom exceptions for handling OpenAI API chat completion responses.
Some of these exceptions correspond to the possible values of 'finish_reason' as documented in
https://platform.openai.com/docs/api-reference/chat/object
"""


class ChatResponseTooLongError(Exception):
    """
    Raised when the OpenAI chat completion is terminated due to reaching the maximum token limit.
    Corresponds to finish_reason='length'.
    """

    pass


class ChatContentFilteredError(Exception):
    """
    Raised when the OpenAI chat completion is filtered by content moderation systems.
    Corresponds to finish_reason='content_filter'.
    """

    pass


class ChatUnknownFinishReasonError(Exception):
    """
    Raised when the OpenAI chat completion ends with an unexpected or undocumented finish_reason.
    Handles any finish_reason values not explicitly covered by other exceptions.
    """

    pass


class ChatUndefinedToolCallError(Exception):
    """
    Raised when there's an issue with tool calls in the OpenAI chat completion.
    Related to cases where finish_reason='tool_calls' but proper tool definitions are missing.
    """

    pass
