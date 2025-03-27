import pytest
from datetime import datetime
from model_bakery import baker

from django.test import TestCase

from agent.constants import MessageSender
from agent.models import *


@pytest.mark.django_db
class ChatMessageModelTest(TestCase):
    """Test cases for the ChatMessage model."""

    def test_creation(self):
        """Test if a ChatMessage instance is created successfully"""
        message = baker.make(ChatMessage)
        assert isinstance(message, ChatMessage)
        assert isinstance(message.session_id, str)
        assert isinstance(message.sender_type, str)
        assert isinstance(message.content, str)
        assert isinstance(message.created_at, datetime)

    def test_custom_creation(self):
        """Test if a ChatMessage instance with specific values is created successfully"""
        session_id = "test_session"
        sender_type = MessageSender.USER
        content = "Test message content"

        message = baker.make(
            ChatMessage, session_id=session_id, sender_type=sender_type, content=content
        )
        assert message.session_id == session_id
        assert message.sender_type == sender_type
        assert message.content == content

    def test_field_constraints(self):
        """Test constraints on model fields"""
        session_id_max_length = ChatMessage._meta.get_field("session_id").max_length
        assert session_id_max_length == 50
        sender_type_max_length = ChatMessage._meta.get_field("sender_type").max_length
        assert sender_type_max_length == 10
        created_at_auto_now_add = ChatMessage._meta.get_field("created_at").auto_now_add
        assert created_at_auto_now_add is True
        sender_type_choices = ChatMessage._meta.get_field("sender_type").choices
        assert set(sender_type_choices) == set(MessageSender.CHOICES)

    def test_meta_options(self):
        """Test the meta options"""
        ordering = ChatMessage._meta.ordering
        assert ordering == ["created_at"]

    def test_str_method(self):
        """Test the string representation"""
        session_id = "test_session"
        sender_type = MessageSender.USER
        content = "This is a test message with more than 20 characters"
        message = baker.prepare(
            ChatMessage, session_id=session_id, sender_type=sender_type, content=content
        )
        expected_str = f"{session_id}({sender_type}) - {content[:20]}"
        assert str(message) == expected_str
